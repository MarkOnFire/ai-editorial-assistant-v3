"""Job processing worker for Editorial Assistant v3.0.

Polls the queue for pending jobs and processes them through agent phases.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from api.models.job import JobStatus, JobPhase, PhaseStatus
from api.services.database import (
    claim_next_job,
    update_job_status,
    update_job_phase,
    update_job_heartbeat,
    log_event,
)
from api.services.llm import (
    get_llm_client,
    start_run_tracking,
    end_run_tracking,
    LLMResponse,
)
from api.services.utils import calculate_transcript_metrics
from api.models.events import EventType, EventCreate, EventData
from api.services.logging import setup_logging, get_logger
from api.services.airtable import get_airtable_client


# Initialize logging for worker
setup_logging(log_file="worker.log")
logger = get_logger(__name__)

# Default paths
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "OUTPUT"))
TRANSCRIPTS_DIR = Path(os.getenv("TRANSCRIPTS_DIR", "transcripts"))
TRANSCRIPTS_ARCHIVE_DIR = TRANSCRIPTS_DIR / "archive"
AGENTS_DIR = Path(".claude/agents")


class WorkerConfig:
    """Configuration for the job worker."""

    def __init__(
        self,
        poll_interval: int = 30,
        heartbeat_interval: int = 60,
        max_retries: int = 3,
        max_concurrent_jobs: int = 1,
        worker_id: Optional[str] = None,
    ):
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.max_retries = max_retries
        self.max_concurrent_jobs = max_concurrent_jobs
        # Generate worker_id if not provided
        self.worker_id = worker_id or f"worker-{os.getpid()}"


class JobWorker:
    """Processes jobs from the queue through agent phases.

    Note: copy_editor is intentionally excluded from automatic processing.
    It's designed to be run interactively via Claude Desktop/MCP for
    human-in-the-loop editing workflow.

    The manager phase runs last as QA review of all outputs.
    """

    PHASES = ["analyst", "formatter", "seo", "manager"]

    # Manager always runs on big-brain tier for quality oversight
    FORCE_BIG_BRAIN_PHASES = ["manager"]

    def __init__(self, config: Optional[WorkerConfig] = None):
        self.config = config or WorkerConfig()
        self.llm = get_llm_client()
        self.running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._current_job_id: Optional[int] = None

    async def start(self):
        """Start the worker polling loop with concurrent job processing."""
        self.running = True
        worker_id = self.config.worker_id
        max_concurrent = self.config.max_concurrent_jobs

        logger.info(
            "Worker starting",
            extra={
                "worker_id": worker_id,
                "poll_interval": self.config.poll_interval,
                "max_concurrent": max_concurrent,
            }
        )

        # Track active job tasks
        active_tasks: set = set()

        while self.running:
            try:
                # Clean up completed tasks
                done_tasks = {t for t in active_tasks if t.done()}
                for task in done_tasks:
                    # Check for exceptions
                    try:
                        task.result()
                    except Exception as e:
                        logger.error(
                            "Task error",
                            extra={"worker_id": worker_id, "error": str(e)},
                            exc_info=True,
                        )
                active_tasks -= done_tasks

                # Claim more jobs if we have capacity
                while len(active_tasks) < max_concurrent:
                    job = await claim_next_job(worker_id=worker_id)
                    if job:
                        # Convert Job model to dict for processing
                        job_dict = job.model_dump() if hasattr(job, 'model_dump') else dict(job)
                        # Start processing as a task
                        task = asyncio.create_task(self.process_job(job_dict))
                        active_tasks.add(task)
                        logger.info(
                            "Job claimed",
                            extra={
                                "worker_id": worker_id,
                                "job_id": job.id,
                                "active_jobs": len(active_tasks),
                                "max_concurrent": max_concurrent,
                            }
                        )
                    else:
                        # No more pending jobs
                        break

                # Wait before next poll
                await asyncio.sleep(self.config.poll_interval)

            except Exception as e:
                logger.error(
                    "Error in polling loop",
                    extra={"worker_id": worker_id, "error": str(e)},
                    exc_info=True,
                )
                await asyncio.sleep(self.config.poll_interval)

        # Wait for active tasks on shutdown
        if active_tasks:
            logger.info(
                "Waiting for active jobs to complete on shutdown",
                extra={"worker_id": worker_id, "active_jobs": len(active_tasks)}
            )
            await asyncio.gather(*active_tasks, return_exceptions=True)

    async def stop(self):
        """Stop the worker."""
        self.running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

    async def process_job(self, job: Dict[str, Any]):
        """Process a single job through all phases."""
        job_id = job["id"]
        self._current_job_id = job_id
        project_name = job.get("project_name", "Unknown")

        logger.info(
            "Processing job",
            extra={"job_id": job_id, "project_name": project_name}
        )

        # Start cost tracking for this run
        tracker = start_run_tracking(job_id)

        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(job_id))

        try:
            # Status already set to in_progress by claim_next_job()

            # Log job started event
            await log_event(EventCreate(
                job_id=job_id,
                event_type=EventType.job_started,
                data=EventData(extra={"project_name": job.get("project_name")}),
            ))

            # Set up project directory
            project_path = self._setup_project_dir(job)
            await update_job_status(job_id, JobStatus.in_progress, project_path=str(project_path))

            # Check if all phases are already complete (recovery case)
            phases = job.get("phases") or []
            if isinstance(phases, str):
                phases = json.loads(phases)

            if self._all_phases_complete(phases, project_path):
                logger.info(
                    "All phases already complete, marking job done",
                    extra={"job_id": job_id, "project_name": project_name}
                )
                await update_job_status(
                    job_id,
                    JobStatus.completed,
                    actual_cost=job.get("actual_cost", 0),
                )
                return

            # Load transcript
            transcript_content = self._load_transcript(job)

            # Calculate transcript metrics for routing decisions
            routing_config = self.llm.config.get("routing", {})
            threshold_minutes = routing_config.get("long_form_threshold_minutes", 15)
            transcript_metrics = calculate_transcript_metrics(
                transcript_content,
                long_form_threshold_minutes=threshold_minutes
            )
            logger.info(
                "Transcript metrics calculated",
                extra={
                    "job_id": job_id,
                    "word_count": transcript_metrics["word_count"],
                    "estimated_duration_minutes": transcript_metrics["estimated_duration_minutes"],
                    "is_long_form": transcript_metrics["is_long_form"],
                }
            )

            # Fetch SST context if linked (Task 6.2.1)
            sst_context = await self._fetch_sst_context(job)
            if sst_context:
                logger.info(
                    "SST context loaded",
                    extra={"job_id": job_id, "sst_title": sst_context.get("title", "Unknown")}
                )

            # Get existing phases or initialize
            phases = job.get("phases") or []
            if isinstance(phases, str):
                phases = json.loads(phases)

            # Process each phase
            context = {
                "transcript": transcript_content,
                "project_path": project_path,
                "transcript_metrics": transcript_metrics,
                "sst_context": sst_context,  # Add SST context to processing context
            }

            for phase_name in self.PHASES:
                # Check if phase already completed
                existing_phase = next((p for p in phases if p["name"] == phase_name), None)
                if existing_phase and existing_phase.get("status") == "completed":
                    logger.debug(
                        "Skipping completed phase",
                        extra={"job_id": job_id, "phase": phase_name}
                    )
                    # Load previous output for context
                    output_file = project_path / f"{phase_name}_output.md"
                    if output_file.exists():
                        context[f"{phase_name}_output"] = output_file.read_text()
                    continue

                # Update current phase
                await update_job_status(job_id, JobStatus.in_progress, current_phase=phase_name)

                # Process phase
                logger.info(
                    "Running phase",
                    extra={"job_id": job_id, "phase": phase_name}
                )
                phase_result = await self._run_phase(job_id, phase_name, context, project_path)

                # Update phases list with model/tier info
                phase_data = {
                    "name": phase_name,
                    "status": "completed" if phase_result["success"] else "failed",
                    "cost": phase_result.get("cost", 0),
                    "tokens": phase_result.get("tokens", 0),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "model": phase_result.get("model"),
                    "tier": phase_result.get("tier"),
                    "tier_label": phase_result.get("tier_label"),
                    "tier_reason": phase_result.get("tier_reason"),
                    "attempts": phase_result.get("attempts", 1),
                }

                # Update or add phase
                phase_updated = False
                for i, p in enumerate(phases):
                    if p["name"] == phase_name:
                        phases[i] = phase_data
                        phase_updated = True
                        break
                if not phase_updated:
                    phases.append(phase_data)

                await update_job_phase(job_id, phases)

                if not phase_result["success"]:
                    raise Exception(f"Phase {phase_name} failed: {phase_result.get('error')}")

                # Add output to context for next phase
                context[f"{phase_name}_output"] = phase_result.get("output", "")

            # Create manifest
            await self._create_manifest(job, project_path, phases, tracker)

            # Mark job completed
            run_summary = await end_run_tracking()
            await update_job_status(
                job_id,
                JobStatus.completed,
                actual_cost=run_summary["total_cost"] if run_summary else 0,
            )

            # Archive the transcript file (non-fatal if this fails)
            try:
                self._archive_transcript(job)
            except Exception as archive_err:
                logger.warning(
                    "Failed to archive transcript (non-fatal)",
                    extra={"job_id": job_id, "error": str(archive_err)}
                )

            logger.info(
                "Job completed successfully",
                extra={
                    "job_id": job_id,
                    "project_name": project_name,
                    "total_cost": run_summary["total_cost"] if run_summary else 0,
                }
            )

        except Exception as e:
            logger.error(
                "Job failed",
                extra={"job_id": job_id, "project_name": project_name, "error": str(e)},
                exc_info=True,
            )

            # End tracking for this attempt
            run_summary = await end_run_tracking()
            current_cost = run_summary["total_cost"] if run_summary else 0

            # Set status to investigating while manager analyzes the failure
            await update_job_status(
                job_id,
                JobStatus.investigating,
                error_message=str(e),
            )

            # Run manager to analyze and decide on recovery action
            recovery_result = await self._analyze_and_recover(
                job=job,
                project_path=project_path,
                phases=phases,
                context=context,
                error=str(e),
                current_cost=current_cost,
            )

            # If recovery was successful, job status already updated
            if recovery_result.get("recovered"):
                logger.info(
                    "Job recovered by manager",
                    extra={
                        "job_id": job_id,
                        "action": recovery_result.get("action"),
                        "total_cost": recovery_result.get("total_cost", 0),
                    }
                )
                return

            # Recovery failed - mark job as failed
            await update_job_status(
                job_id,
                JobStatus.failed,
                error_message=str(e),
                actual_cost=current_cost + recovery_result.get("cost", 0),
            )

            # Log error event with investigation summary
            await log_event(EventCreate(
                job_id=job_id,
                event_type=EventType.job_failed,
                data=EventData(extra={
                    "error": str(e),
                    "recovery_attempted": recovery_result.get("action", "none"),
                    "recovery_reason": recovery_result.get("reason", "Unknown"),
                }),
            ))

        finally:
            # Stop heartbeat
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None
            self._current_job_id = None

    async def _fetch_sst_context(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch SST metadata from Airtable if job has linked record.

        Args:
            job: Job dict with potential airtable_record_id field

        Returns:
            Dict with SST fields if found, None if no SST link or error
        """
        airtable_record_id = job.get("airtable_record_id")
        if not airtable_record_id:
            return None

        try:
            client = get_airtable_client()
            record = await client.get_sst_record(airtable_record_id)

            if not record:
                logger.warning(
                    "SST record not found",
                    extra={"job_id": job.get("id"), "record_id": airtable_record_id}
                )
                return None

            # Extract relevant fields for agent context
            fields = record.get("fields", {})
            sst_context = {
                "title": fields.get("Title"),
                "short_description": fields.get("Short Description"),
                "long_description": fields.get("Long Description"),
                "keywords": fields.get("Keywords"),
                "tags": fields.get("Tags"),
                "host": fields.get("Host"),
                "presenter": fields.get("Presenter"),
                "program": fields.get("Program"),
                "media_id": fields.get("Media ID"),
            }

            # Remove None values
            sst_context = {k: v for k, v in sst_context.items() if v is not None}

            return sst_context if sst_context else None

        except Exception as e:
            logger.warning(
                "Failed to fetch SST context (non-fatal)",
                extra={"job_id": job.get("id"), "error": str(e)}
            )
            return None

    async def _heartbeat_loop(self, job_id: int):
        """Send periodic heartbeats while processing."""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                await update_job_heartbeat(job_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "Heartbeat error",
                    extra={"job_id": job_id, "error": str(e)}
                )

    def _all_phases_complete(self, phases: List[Dict[str, Any]], project_path: Path) -> bool:
        """Check if all required phases are complete and output files exist.

        This is a recovery mechanism for jobs that failed after all phases
        completed (e.g., due to archiving errors). Verifies both phase status
        and actual output file existence.
        """
        if not phases:
            return False

        # Check all required phases are in the list and completed
        completed_phases = set()
        for phase in phases:
            if phase.get("status") == "completed":
                completed_phases.add(phase.get("name"))

        required_phases = set(self.PHASES)  # analyst, formatter, seo
        if not required_phases.issubset(completed_phases):
            return False

        # Verify output files actually exist
        for phase_name in required_phases:
            output_file = project_path / f"{phase_name}_output.md"
            if not output_file.exists():
                return False

        return True

    def _setup_project_dir(self, job: Dict[str, Any]) -> Path:
        """Create and return the project output directory."""
        project_name = job.get("project_name", f"job_{job['id']}")
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)

        project_path = OUTPUT_DIR / safe_name
        project_path.mkdir(parents=True, exist_ok=True)

        return project_path

    def _load_transcript(self, job: Dict[str, Any]) -> str:
        """Load the transcript file content.

        Handles various encodings (UTF-8, ISO-8859, etc.) gracefully.
        Also checks the archive folder as a fallback for re-processed jobs.
        """
        transcript_file = job.get("transcript_file", "")

        # Try various paths, including archive folder as fallback
        paths_to_try = [
            Path(transcript_file),
            TRANSCRIPTS_DIR / transcript_file,
            TRANSCRIPTS_DIR / Path(transcript_file).name,
            # Archive folder fallback for re-processed jobs
            TRANSCRIPTS_ARCHIVE_DIR / transcript_file,
            TRANSCRIPTS_ARCHIVE_DIR / Path(transcript_file).name,
        ]

        for path in paths_to_try:
            if path.exists():
                # Log if we're using archive fallback
                if TRANSCRIPTS_ARCHIVE_DIR in path.parents or path.parent == TRANSCRIPTS_ARCHIVE_DIR:
                    logger.info(
                        "Using archived transcript (re-processing)",
                        extra={"job_id": job.get("id"), "source": str(path)}
                    )
                # Try different encodings
                for encoding in ['utf-8', 'iso-8859-1', 'cp1252', 'latin-1']:
                    try:
                        return path.read_text(encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                # Last resort: read with errors='replace'
                return path.read_text(encoding='utf-8', errors='replace')

        raise FileNotFoundError(f"Transcript not found: {transcript_file}")

    def _archive_transcript(self, job: Dict[str, Any]) -> None:
        """Move completed transcript to archive folder.

        Archives the original transcript file to transcripts/archive/ after
        successful job completion. This keeps the main transcripts folder
        clean and shows only unprocessed files.
        """
        transcript_file = job.get("transcript_file", "")
        if not transcript_file:
            return

        # Find the source file
        source_paths = [
            Path(transcript_file),
            TRANSCRIPTS_DIR / transcript_file,
            TRANSCRIPTS_DIR / Path(transcript_file).name,
        ]

        source = None
        for path in source_paths:
            if path.exists():
                source = path
                break

        if not source:
            logger.warning(
                "Transcript not found for archiving",
                extra={"source_file": transcript_file}
            )
            return

        # Create archive directory if needed
        TRANSCRIPTS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Move to archive
        dest = TRANSCRIPTS_ARCHIVE_DIR / source.name
        try:
            import shutil
            shutil.move(str(source), str(dest))
            logger.info(
                "Archived transcript",
                extra={"source_file": source.name, "destination": str(dest)}
            )
        except Exception as e:
            logger.error(
                "Failed to archive transcript",
                extra={"source_file": source.name, "error": str(e)},
                exc_info=True,
            )

    async def _run_phase(
        self,
        job_id: int,
        phase_name: str,
        context: Dict[str, Any],
        project_path: Path,
    ) -> Dict[str, Any]:
        """Run a single agent phase with tiered escalation on failure.

        Attempts to run with the initial tier based on transcript duration.
        On failure or timeout, escalates to the next tier and retries.
        """
        # Get escalation config
        escalation_config = self.llm.get_escalation_config()
        escalation_enabled = escalation_config.get("enabled", True)
        escalate_on_failure = escalation_config.get("on_failure", True)
        escalate_on_timeout = escalation_config.get("on_timeout", True)
        timeout_seconds = escalation_config.get("timeout_seconds", 120)
        max_retries = escalation_config.get("max_retries_per_tier", 1)

        # Check if tier is being forced (e.g., by manager escalation)
        forced_tier = context.get("_force_tier")

        # Force big-brain tier for QA phases (manager)
        if phase_name in self.FORCE_BIG_BRAIN_PHASES:
            initial_tier = 2  # big-brain tier
            initial_tier_reason = f"{phase_name} phase always uses big-brain tier for quality oversight"
        elif forced_tier is not None:
            initial_tier = forced_tier
            initial_tier_reason = f"Forced tier {forced_tier} by manager escalation"
        else:
            # Get initial tier based on context (duration thresholds)
            initial_tier, initial_tier_reason = self.llm.get_tier_for_phase_with_reason(phase_name, context)

        current_tier = initial_tier
        tier_reason = initial_tier_reason
        routing_config = self.llm.config.get("routing", {})
        tier_labels = routing_config.get("tier_labels", ["cheapskate", "default", "big-brain"])

        # Load prompts once (don't reload on each retry)
        system_prompt = self._load_agent_prompt(phase_name)
        user_message = self._build_phase_prompt(phase_name, context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        total_cost = 0.0
        total_tokens = 0
        last_error = None
        attempts = 0

        while True:
            # Get backend for current tier
            backend = self.llm.get_backend_for_phase(phase_name, context, tier_override=current_tier)
            tier_label = tier_labels[current_tier] if current_tier < len(tier_labels) else f"tier-{current_tier}"
            logger.info(
                "Phase attempting with tier",
                extra={
                    "job_id": job_id,
                    "phase": phase_name,
                    "tier": current_tier,
                    "tier_label": tier_label,
                    "backend": backend,
                }
            )

            # Log phase started/retry
            await log_event(EventCreate(
                job_id=job_id,
                event_type=EventType.phase_started,
                data=EventData(
                    phase=phase_name,
                    backend=backend,
                    extra={"tier": current_tier, "tier_label": tier_label, "attempt": attempts + 1}
                ),
            ))

            try:
                # Call LLM with timeout
                response: LLMResponse = await asyncio.wait_for(
                    self.llm.chat(
                        messages=messages,
                        backend=backend,
                        job_id=job_id,
                    ),
                    timeout=timeout_seconds
                )

                # Track costs across retries
                total_cost += response.cost
                total_tokens += response.total_tokens

                # Save output
                output_file = project_path / f"{phase_name}_output.md"
                output_file.write_text(response.content)

                # Log phase completed
                await log_event(EventCreate(
                    job_id=job_id,
                    event_type=EventType.phase_completed,
                    data=EventData(
                        phase=phase_name,
                        cost=response.cost,
                        tokens=response.total_tokens,
                        model=response.model,
                        extra={"tier": current_tier, "tier_label": tier_label, "total_attempts": attempts + 1}
                    ),
                ))

                return {
                    "success": True,
                    "output": response.content,
                    "cost": total_cost,
                    "tokens": total_tokens,
                    "model": response.model,
                    "tier": current_tier,
                    "tier_label": tier_label,
                    "tier_reason": tier_reason,
                    "attempts": attempts + 1,
                }

            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout_seconds}s"
                logger.warning(
                    "Phase timed out",
                    extra={
                        "job_id": job_id,
                        "phase": phase_name,
                        "tier_label": tier_label,
                        "timeout_seconds": timeout_seconds,
                    }
                )

                # Check if we should escalate on timeout
                if not escalation_enabled or not escalate_on_timeout:
                    break

            except Exception as e:
                last_error = str(e)
                logger.error(
                    "Phase failed",
                    extra={
                        "job_id": job_id,
                        "phase": phase_name,
                        "tier_label": tier_label,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Check if we should escalate on failure
                if not escalation_enabled or not escalate_on_failure:
                    break

            attempts += 1

            # Try to escalate to next tier
            next_tier = self.llm.get_next_tier(current_tier)
            if next_tier is None:
                logger.warning(
                    "Phase failed at max tier, no more escalation possible",
                    extra={
                        "job_id": job_id,
                        "phase": phase_name,
                        "final_tier": current_tier,
                    }
                )
                break

            # Log escalation
            next_label = tier_labels[next_tier] if next_tier < len(tier_labels) else f"tier-{next_tier}"
            logger.info(
                "Escalating phase to next tier",
                extra={
                    "job_id": job_id,
                    "phase": phase_name,
                    "from_tier": tier_label,
                    "to_tier": next_label,
                    "reason": last_error,
                }
            )

            # Update tier reason to reflect escalation
            tier_reason = f"escalated from {tier_label}: {last_error}"

            await log_event(EventCreate(
                job_id=job_id,
                event_type=EventType.phase_started,
                data=EventData(
                    phase=phase_name,
                    extra={
                        "escalation": True,
                        "from_tier": current_tier,
                        "to_tier": next_tier,
                        "reason": last_error
                    }
                ),
            ))

            current_tier = next_tier

        # All attempts failed
        await log_event(EventCreate(
            job_id=job_id,
            event_type=EventType.phase_failed,
            data=EventData(
                phase=phase_name,
                extra={"error": last_error, "attempts": attempts, "final_tier": current_tier}
            ),
        ))
        return {"success": False, "error": last_error, "attempts": attempts, "cost": total_cost}

    async def _analyze_and_recover(
        self,
        job: Dict[str, Any],
        project_path: Path,
        phases: List[Dict[str, Any]],
        context: Dict[str, Any],
        error: str,
        current_cost: float,
    ) -> Dict[str, Any]:
        """Run manager agent to analyze failure and attempt recovery.

        The manager decides on an action:
        - RETRY: Re-run the failed phase at the same tier
        - ESCALATE: Re-run with a higher tier model
        - FIX: Apply corrections and continue
        - FAIL: Mark as failed (truly unrecoverable)

        Returns:
            Dict with recovery results including whether job was recovered
        """
        job_id = job.get("id")
        project_name = job.get("project_name", "Unknown")

        logger.info(
            "Manager analyzing failure",
            extra={"job_id": job_id, "error": error[:100]}
        )

        try:
            # Find the failed phase
            failed_phase = None
            failed_phase_idx = -1
            for i, phase in enumerate(phases):
                if phase.get("status") == "failed":
                    failed_phase = phase
                    failed_phase_idx = i
                    break

            # Build context summary
            phases_summary = []
            for phase in phases:
                status = phase.get("status", "unknown")
                phase_name = phase.get("name", "unknown")
                phase_error = phase.get("error_message", "")
                tier_label = phase.get("tier_label", "unknown")
                tier = phase.get("tier", 0)
                phases_summary.append(
                    f"- {phase_name}: {status} (tier {tier}: {tier_label})"
                    f"{f' - Error: {phase_error}' if phase_error else ''}"
                )

            # Get partial outputs for context
            partial_outputs = []
            for phase_name in ["analyst", "formatter", "seo"]:
                output = context.get(f"{phase_name}_output", "")
                if output:
                    partial_outputs.append(f"## {phase_name.title()} Output:\n{output[:800]}...")

            # Build decision prompt
            decision_prompt = f"""## Failure Recovery Analysis

**Job ID:** {job_id}
**Project:** {project_name}
**Error:** {error}
**Failed Phase:** {failed_phase.get('name', 'unknown') if failed_phase else 'unknown'}
**Failed at Tier:** {failed_phase.get('tier', 0) if failed_phase else 0} ({failed_phase.get('tier_label', 'unknown') if failed_phase else 'unknown'})

## Phase Status:
{chr(10).join(phases_summary)}

## Available Outputs:
{chr(10).join(partial_outputs) if partial_outputs else "No outputs available yet"}

## Your Task:
Analyze this failure and decide on the BEST recovery action. You MUST respond with exactly ONE of these actions on the FIRST LINE of your response:

**ACTION: RETRY** - The failure is transient (API timeout, rate limit, temporary issue). Re-run at the same tier.

**ACTION: ESCALATE** - The task is too complex for the current tier. Re-run with a more capable model (tier {min((failed_phase.get('tier', 0) if failed_phase else 0) + 1, 2)}).

**ACTION: FIX** - The output has minor issues you can correct. Provide the corrected output after your analysis.

**ACTION: FAIL** - The failure is unrecoverable (missing transcript, invalid input, fundamental issue).

## Response Format:
ACTION: [RETRY|ESCALATE|FIX|FAIL]
REASON: [Brief explanation - 1-2 sentences]

[If ACTION is FIX, provide the corrected output below]
"""

            # Load manager system prompt
            system_prompt = self._load_agent_prompt("manager")

            # Use big-brain tier for recovery decisions
            routing_config = self.llm.config.get("routing", {})
            tier_backends = routing_config.get("tiers", ["openrouter-cheapskate", "openrouter", "openrouter-big-brain"])
            backend_name = tier_backends[2] if len(tier_backends) > 2 else tier_backends[-1]

            logger.info(
                "Running recovery analysis",
                extra={"job_id": job_id, "backend": backend_name}
            )

            # Run the analysis
            response = await self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=decision_prompt,
                backend=backend_name,
                timeout=120
            )

            # Parse the decision - search full content for action pattern
            content = response.content.strip()
            # Normalize content for pattern matching (handles **ACTION:** markdown format)
            content_upper = content.upper().replace("**", "")

            action = "FAIL"  # Default to fail if we can't parse
            if "ACTION: RETRY" in content_upper or "ACTION:RETRY" in content_upper:
                action = "RETRY"
            elif "ACTION: ESCALATE" in content_upper or "ACTION:ESCALATE" in content_upper:
                action = "ESCALATE"
            elif "ACTION: FIX" in content_upper or "ACTION:FIX" in content_upper:
                action = "FIX"
            elif "ACTION: FAIL" in content_upper or "ACTION:FAIL" in content_upper:
                action = "FAIL"

            # Extract reason - check multiple formats
            reason = "No reason provided"
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_upper = line.upper().strip()
                # Check for "REASON:" format
                if line_upper.startswith("REASON:"):
                    reason = line[line.find(":") + 1:].strip()
                    break
                # Check for "### Rationale" section (manager prompt format)
                elif "RATIONALE" in line_upper and line_upper.startswith("#"):
                    # Get the next non-empty line as the reason
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith("#"):
                            reason = next_line
                            break
                    break

            logger.info(
                "Manager decision",
                extra={
                    "job_id": job_id,
                    "action": action,
                    "reason": reason[:100],
                    "analysis_cost": response.cost,
                }
            )

            # Save the analysis report
            report_file = project_path / "recovery_analysis.md"
            report_file.write_text(f"""# Recovery Analysis Report
**Job ID:** {job_id}
**Project:** {project_name}
**Error:** {error}
**Analysis Time:** {datetime.now(timezone.utc).isoformat()}

## Decision
**Action:** {action}
**Reason:** {reason}

## Full Analysis
{response.content}

---
**Analysis Cost:** ${response.cost:.4f}
**Model:** {response.model}
""")

            total_cost = current_cost + response.cost

            # Execute the recovery action
            if action == "FAIL":
                return {
                    "recovered": False,
                    "action": action,
                    "reason": reason,
                    "cost": response.cost,
                }

            elif action == "RETRY":
                # Re-run the failed phase at the same tier
                if failed_phase and failed_phase_idx >= 0:
                    logger.info(
                        "Retrying failed phase",
                        extra={"job_id": job_id, "phase": failed_phase.get("name")}
                    )

                    # Reset phase status
                    phases[failed_phase_idx]["status"] = "pending"
                    phases[failed_phase_idx]["error_message"] = None
                    await update_job_phase(job_id, phases)

                    # Re-run the phase
                    retry_result = await self._run_phase(
                        job_id=job_id,
                        phase_name=failed_phase.get("name"),
                        context=context,
                        project_path=project_path,
                    )

                    if retry_result["success"]:
                        # Continue with remaining phases
                        context[f"{failed_phase.get('name')}_output"] = retry_result.get("output", "")
                        return await self._complete_remaining_phases(
                            job=job,
                            phases=phases,
                            context=context,
                            project_path=project_path,
                            start_from=failed_phase_idx + 1,
                            total_cost=total_cost + retry_result.get("cost", 0),
                        )

                return {"recovered": False, "action": action, "reason": "Retry failed", "cost": response.cost}

            elif action == "ESCALATE":
                # Re-run with a higher tier
                if failed_phase and failed_phase_idx >= 0:
                    current_tier = failed_phase.get("tier", 0)
                    next_tier = min(current_tier + 1, 2)

                    if next_tier > current_tier:
                        logger.info(
                            "Escalating to higher tier",
                            extra={
                                "job_id": job_id,
                                "phase": failed_phase.get("name"),
                                "from_tier": current_tier,
                                "to_tier": next_tier,
                            }
                        )

                        # Reset phase and force higher tier
                        phases[failed_phase_idx]["status"] = "pending"
                        phases[failed_phase_idx]["error_message"] = None
                        phases[failed_phase_idx]["tier"] = next_tier  # Force escalation
                        await update_job_phase(job_id, phases)

                        # Re-run with escalated tier
                        # Temporarily modify context to force tier
                        context["_force_tier"] = next_tier

                        retry_result = await self._run_phase(
                            job_id=job_id,
                            phase_name=failed_phase.get("name"),
                            context=context,
                            project_path=project_path,
                        )

                        # Clean up
                        context.pop("_force_tier", None)

                        if retry_result["success"]:
                            context[f"{failed_phase.get('name')}_output"] = retry_result.get("output", "")
                            return await self._complete_remaining_phases(
                                job=job,
                                phases=phases,
                                context=context,
                                project_path=project_path,
                                start_from=failed_phase_idx + 1,
                                total_cost=total_cost + retry_result.get("cost", 0),
                            )

                return {"recovered": False, "action": action, "reason": "Escalation failed", "cost": response.cost}

            elif action == "FIX":
                # Manager provided a fix - extract and save it
                if failed_phase and failed_phase_idx >= 0:
                    phase_name = failed_phase.get("name")

                    # The fix content is everything after the REASON line
                    fix_content = ""
                    found_reason = False
                    for line in content.split('\n'):
                        if found_reason:
                            fix_content += line + "\n"
                        elif line.upper().startswith("REASON:"):
                            found_reason = True

                    fix_content = fix_content.strip()

                    if fix_content:
                        logger.info(
                            "Applying manager fix",
                            extra={"job_id": job_id, "phase": phase_name, "fix_length": len(fix_content)}
                        )

                        # Save the fixed output
                        output_file = project_path / f"{phase_name}_output.md"
                        output_file.write_text(fix_content)

                        # Mark phase as completed
                        phases[failed_phase_idx]["status"] = "completed"
                        phases[failed_phase_idx]["error_message"] = None
                        phases[failed_phase_idx]["completed_at"] = datetime.now(timezone.utc).isoformat()
                        await update_job_phase(job_id, phases)

                        # Add to context and continue
                        context[f"{phase_name}_output"] = fix_content

                        return await self._complete_remaining_phases(
                            job=job,
                            phases=phases,
                            context=context,
                            project_path=project_path,
                            start_from=failed_phase_idx + 1,
                            total_cost=total_cost,
                        )

                return {"recovered": False, "action": action, "reason": "Fix could not be applied", "cost": response.cost}

            return {"recovered": False, "action": action, "reason": reason, "cost": response.cost}

        except Exception as recovery_err:
            logger.warning(
                "Recovery analysis failed",
                extra={"job_id": job_id, "error": str(recovery_err)}
            )
            return {
                "recovered": False,
                "action": "FAIL",
                "reason": f"Recovery analysis failed: {str(recovery_err)[:100]}",
                "cost": 0,
            }

    async def _complete_remaining_phases(
        self,
        job: Dict[str, Any],
        phases: List[Dict[str, Any]],
        context: Dict[str, Any],
        project_path: Path,
        start_from: int,
        total_cost: float,
    ) -> Dict[str, Any]:
        """Complete remaining phases after recovery.

        Returns:
            Dict indicating if job was fully recovered
        """
        job_id = job.get("id")

        try:
            # Run remaining phases
            for i in range(start_from, len(phases)):
                phase = phases[i]
                phase_name = phase.get("name")

                if phase.get("status") == "completed":
                    continue

                # Update phase status
                phase["status"] = "in_progress"
                phase["started_at"] = datetime.now(timezone.utc).isoformat()
                await update_job_phase(job_id, phases)

                # Run the phase
                result = await self._run_phase(
                    job_id=job_id,
                    phase_name=phase_name,
                    context=context,
                    project_path=project_path,
                )

                if not result["success"]:
                    # Another failure - don't recurse infinitely
                    return {
                        "recovered": False,
                        "action": "FAIL",
                        "reason": f"Phase {phase_name} failed after recovery",
                        "cost": total_cost,
                    }

                # Update phase as completed
                phase["status"] = "completed"
                phase["completed_at"] = datetime.now(timezone.utc).isoformat()
                phase["cost"] = result.get("cost", 0)
                phase["tokens"] = result.get("tokens", 0)
                phase["model"] = result.get("model")
                phase["tier"] = result.get("tier")
                phase["tier_label"] = result.get("tier_label")
                await update_job_phase(job_id, phases)

                total_cost += result.get("cost", 0)
                context[f"{phase_name}_output"] = result.get("output", "")

            # All phases complete - create manifest and mark done
            from api.services.tracking import CostTracker
            tracker = CostTracker()
            tracker.total_cost = total_cost

            await self._create_manifest(job, project_path, phases, tracker)

            await update_job_status(
                job_id,
                JobStatus.completed,
                actual_cost=total_cost,
            )

            # Archive transcript
            try:
                self._archive_transcript(job)
            except Exception:
                pass  # Non-fatal

            return {
                "recovered": True,
                "action": "COMPLETED",
                "total_cost": total_cost,
            }

        except Exception as e:
            return {
                "recovered": False,
                "action": "FAIL",
                "reason": str(e),
                "cost": total_cost,
            }

    def _load_agent_prompt(self, phase_name: str) -> str:
        """Load the system prompt for an agent phase."""
        prompt_file = AGENTS_DIR / f"{phase_name}.md"

        if prompt_file.exists():
            return prompt_file.read_text()

        # Fallback prompts if files don't exist
        fallback_prompts = {
            "analyst": """You are a transcript analyst for PBS Wisconsin. Your role is to analyze raw video transcripts and identify:

1. Key topics and themes discussed
2. Speaker identification and roles
3. Important quotes and timestamps
4. Structural elements (segments, transitions)
5. Items that may need human review (unclear audio, names to verify)

Output a detailed analysis document in markdown format that will guide the formatting and SEO agents.""",

            "formatter": """You are a transcript formatter for PBS Wisconsin. Your role is to transform raw transcripts into clean, readable markdown documents.

Guidelines:
- Use proper speaker attribution (SPEAKER NAME:)
- Create logical paragraph breaks
- Preserve important timestamps
- Fix obvious transcription errors
- Maintain the original meaning and voice

Output a clean, well-formatted markdown transcript.""",

            "seo": """You are an SEO specialist for PBS Wisconsin streaming content. Your role is to generate search-optimized metadata for video content.

Generate:
1. Title (compelling, keyword-rich, under 60 chars)
2. Short description (1-2 sentences, 150 chars)
3. Long description (2-3 paragraphs, engaging)
4. Tags (10-15 relevant keywords)
5. Categories

Output as JSON with keys: title, short_description, long_description, tags, categories""",

            "copy_editor": """You are a copy editor for PBS Wisconsin. Your role is to review and refine formatted transcripts for broadcast quality.

Focus on:
- Grammar and punctuation
- Clarity and readability
- PBS style guidelines
- Consistency in formatting
- Preserving speaker voice while improving prose

Output the polished transcript with any notes on changes made.""",

            "manager": """You are the QA Manager for PBS Wisconsin Editorial Assistant. Review all pipeline outputs for quality.

Check:
1. Formatter: Speaker labels use first+last name only (no titles like Dr./Mr./Ms.), review notes only at top
2. SEO: Title <60 chars, descriptions are engaging, tags relevant
3. Analyst: Speakers identified, topics captured

Output a QA report with:
- Overall Status: APPROVED or NEEDS_REVISION
- Checklist of passes/fails
- Issues found (CRITICAL/MAJOR/MINOR)
- Recommendation""",
        }

        return fallback_prompts.get(phase_name, f"You are the {phase_name} agent. Process the input and provide appropriate output.")

    def _build_phase_prompt(self, phase_name: str, context: Dict[str, Any]) -> str:
        """Build the user prompt for a phase with relevant context."""
        transcript = context.get("transcript", "")
        sst_context = context.get("sst_context")

        # Build SST context section if available
        sst_section = ""
        if sst_context:
            sst_section = "\n## Single Source of Truth (SST) Context\n\n"
            sst_section += "The following metadata exists in the PBS Wisconsin Airtable SST for this project:\n\n"

            if sst_context.get("title"):
                sst_section += f"**Title:** {sst_context['title']}\n"
            if sst_context.get("program"):
                sst_section += f"**Program:** {sst_context['program']}\n"
            if sst_context.get("short_description"):
                sst_section += f"**Short Description:** {sst_context['short_description']}\n"
            if sst_context.get("long_description"):
                sst_section += f"**Long Description:** {sst_context['long_description']}\n"
            if sst_context.get("host"):
                sst_section += f"**Host:** {sst_context['host']}\n"
            if sst_context.get("presenter"):
                sst_section += f"**Presenter:** {sst_context['presenter']}\n"
            if sst_context.get("keywords"):
                sst_section += f"**Keywords:** {sst_context['keywords']}\n"
            if sst_context.get("tags"):
                sst_section += f"**Tags:** {sst_context['tags']}\n"

            sst_section += "\n*Use this context to align your analysis with existing metadata.*\n\n"

        if phase_name == "analyst":
            prompt = f"""Please analyze the following transcript:
"""
            if sst_section:
                prompt += sst_section
            prompt += f"""---
{transcript}
---

Provide a detailed analysis document."""
            return prompt

        elif phase_name == "formatter":
            analysis = context.get("analyst_output", "")
            prompt = "Using the following analysis as guidance:\n\n"
            if sst_section:
                prompt += sst_section
            prompt += f"""---
{analysis}
---

Please format this transcript:

---
{transcript}
---"""
            return prompt

        elif phase_name == "seo":
            analysis = context.get("analyst_output", "")
            formatted = context.get("formatter_output", "")
            prompt = "Based on this analysis:\n\n"
            if sst_section:
                prompt += sst_section
            prompt += f"""---
{analysis}
---

And this formatted transcript:

---
{formatted[:2000]}...
---

Generate SEO metadata as a markdown report."""
            return prompt

        elif phase_name == "copy_editor":
            formatted = context.get("formatter_output", "")
            return f"""Please review and polish this formatted transcript:

---
{formatted}
---

Apply PBS style guidelines and improve readability while preserving speaker voice."""

        elif phase_name == "manager":
            analysis = context.get("analyst_output", "")
            formatted = context.get("formatter_output", "")
            seo = context.get("seo_output", "")
            prompt = "Please perform a QA review of the following pipeline outputs.\n\n"
            if sst_section:
                prompt += sst_section
            prompt += f"""## Original Transcript (for reference):
---
{transcript[:3000]}{"..." if len(transcript) > 3000 else ""}
---

## Analyst Output:
---
{analysis}
---

## Formatted Transcript:
---
{formatted}
---

## SEO Metadata:
---
{seo}
---

Review all outputs against PBS Wisconsin quality standards and provide your QA report."""
            return prompt

        return f"Process the following:\n\n{transcript}"

    async def _create_manifest(
        self,
        job: Dict[str, Any],
        project_path: Path,
        phases: List[Dict[str, Any]],
        tracker,
    ):
        """Create a manifest file for the completed project."""
        manifest = {
            "job_id": job["id"],
            "project_name": job.get("project_name"),
            "transcript_file": job.get("transcript_file"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "phases": phases,
            "total_cost": tracker.total_cost if tracker else 0,
            "total_tokens": tracker.total_tokens if tracker else 0,
            "outputs": {
                "analysis": "analyst_output.md",
                "formatted_transcript": "formatter_output.md",
                "seo_metadata": "seo_output.md",
                "qa_review": "manager_output.md",
                "copy_edited": "copy_editor_output.md",
            },
        }

        manifest_file = project_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2))


# CLI entry point
async def run_worker():
    """Run the worker as a standalone process."""
    worker = JobWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
