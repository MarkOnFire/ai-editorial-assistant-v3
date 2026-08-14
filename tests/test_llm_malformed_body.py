"""Tests for transient malformed-body handling on the LLM call path.

Regression cover for prod job #39, which died on::

    Phase formatter failed: Chunk 0 failed: Expecting value: line 323 column 1 (char 1771)

OpenRouter answered HTTP 200, held the connection open with whitespace padding
for ~66s, then ended the body without ever sending the JSON payload. The bare
``json.JSONDecodeError`` from ``response.json()`` propagated all the way up and
hard-failed a five-phase job. Retrying the identical request succeeded.

Two behaviours are specified here:

1. A 200 whose body will not parse raises ``MalformedResponseError`` carrying
   enough of the body to diagnose it (nothing logged the body before, which is
   why the original body is unknown).
2. ``chat()`` retries that transient failure a bounded number of times, and
   does not burn retries on errors that carry their own recovery semantics.

Attempt counts assert on the ``_post_openrouter`` seam, not on
``httpx.AsyncClient.post``. Patching the httpx class counts *every* POST in the
process — on the success path Langfuse tracing adds one, so the count depended
on whether ``LANGFUSE_*`` was set (it is in CI, and was not locally).
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.llm import (
    CostCapExceededError,
    CreditExhaustedError,
    LLMClient,
    MalformedResponseError,
    get_run_tracker,
    start_run_tracking,
)


@pytest.fixture
def llm_client(tmp_path):
    """LLMClient on a minimal OpenRouter config (no shared fixture exists in tests/)."""
    config = {
        "primary_backend": "openrouter",
        "backends": {
            "openrouter": {
                "type": "openrouter",
                "endpoint": "https://openrouter.ai/api/v1/chat/completions",
                "api_key_env": "OPENROUTER_API_KEY",
                "model": "anthropic/claude-sonnet-4.6",
            },
        },
        "safety": {"run_cost_cap": 10.0, "max_cost_per_1k_tokens": 1.0, "model_allowlist": []},
    }
    config_path = tmp_path / "llm_config.json"
    config_path.write_text(json.dumps(config))
    return LLMClient(config_path=str(config_path))


def _malformed_response():
    """A 200 whose body is whitespace padding only — the job #39 shape."""
    resp = MagicMock()
    resp.status_code = 200
    # 322 padding lines then EOF, exactly what the error offsets implied.
    resp.text = "    \n" * 322
    resp.json.side_effect = json.JSONDecodeError("Expecting value", resp.text, 1771)
    return resp


def _ok_response(content="Recovered response"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "choices": [{"message": {"content": content}}],
        "model": "anthropic/claude-sonnet-4.6",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
    return resp


@pytest.fixture
def _no_backoff(monkeypatch):
    """Collapse retry backoff so tests do not actually sleep."""

    async def _instant(_seconds):
        return None

    monkeypatch.setattr("asyncio.sleep", _instant)


@pytest.mark.asyncio
async def test_malformed_body_error_reports_body_length_and_prefix(llm_client, monkeypatch, _no_backoff):
    """A 200 that will not parse must surface the body, not a bare JSONDecodeError.

    The original failure was undiagnosable because nothing captured the body.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    start_run_tracking(job_id=901)

    monkeypatch.setattr(llm_client, "_post_openrouter", AsyncMock(return_value=_malformed_response()))

    with patch("api.services.llm.log_event"):
        with pytest.raises(MalformedResponseError) as excinfo:
            await llm_client.chat(messages=[{"role": "user", "content": "Hello"}], backend="openrouter")

    message = str(excinfo.value)
    assert "1610" in message, f"body length missing from diagnostics: {message}"
    # repr'd so whitespace padding is visible rather than collapsing into blanks.
    assert "\\n" in message, f"body prefix not repr'd, padding invisible: {message}"


@pytest.mark.asyncio
async def test_chat_retries_malformed_body_and_recovers(llm_client, monkeypatch, _no_backoff):
    """The job #39 case: first attempt returns padding, retry returns real JSON."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    start_run_tracking(job_id=902)

    post = AsyncMock(side_effect=[_malformed_response(), _ok_response()])
    monkeypatch.setattr(llm_client, "_post_openrouter", post)

    with patch("api.services.llm.log_event"):
        response = await llm_client.chat(messages=[{"role": "user", "content": "Hello"}], backend="openrouter")

    assert response.content == "Recovered response"
    assert post.call_count == 2


@pytest.mark.asyncio
async def test_chat_gives_up_after_bounded_attempts(llm_client, monkeypatch, _no_backoff):
    """Retry is bounded — a persistently broken backend must not loop forever."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    start_run_tracking(job_id=903)

    post = AsyncMock(side_effect=lambda *a, **k: _malformed_response())
    monkeypatch.setattr(llm_client, "_post_openrouter", post)

    with patch("api.services.llm.log_event"):
        with pytest.raises(MalformedResponseError):
            await llm_client.chat(messages=[{"role": "user", "content": "Hello"}], backend="openrouter")

    assert post.call_count == 3, f"expected 3 bounded attempts, got {post.call_count}"


@pytest.mark.asyncio
async def test_credit_exhaustion_is_not_retried(llm_client, monkeypatch, _no_backoff):
    """Credit exhaustion pauses the job; retrying it just burns attempts."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    start_run_tracking(job_id=904)

    resp = MagicMock()
    resp.status_code = 402
    resp.text = '{"error":{"message":"Insufficient credits"}}'
    resp.json.return_value = {"error": {"message": "Insufficient credits"}}

    post = AsyncMock(return_value=resp)
    monkeypatch.setattr(llm_client, "_post_openrouter", post)

    with patch("api.services.llm.log_event"):
        with pytest.raises(CreditExhaustedError):
            await llm_client.chat(messages=[{"role": "user", "content": "Hello"}], backend="openrouter")

    assert post.call_count == 1, f"credit exhaustion retried {post.call_count} times"


@pytest.mark.asyncio
async def test_retry_rechecks_cost_cap_between_attempts(llm_client, monkeypatch, _no_backoff):
    """The run cost cap is re-checked before each retry, not only once up front.

    A malformed body carries no usage data, so a discarded attempt's spend cannot
    be added to the tracker — but the cap must still stop the loop from spending
    more once the run has already breached it (e.g. via concurrent calls).
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    start_run_tracking(job_id=905)
    llm_client.run_cost_cap = 1.0

    def _breach_cap_then_fail(*args, **kwargs):
        # Simulate the run crossing its cap while this attempt was in flight.
        get_run_tracker().total_cost = 5.0
        return _malformed_response()

    post = AsyncMock(side_effect=_breach_cap_then_fail)
    monkeypatch.setattr(llm_client, "_post_openrouter", post)

    with patch("api.services.llm.log_event"):
        with pytest.raises(CostCapExceededError):
            await llm_client.chat(messages=[{"role": "user", "content": "Hello"}], backend="openrouter")

    assert post.call_count == 1, f"kept spending past the cap: {post.call_count} attempts"


@pytest.mark.asyncio
async def test_retry_warning_carries_structured_fields(llm_client, monkeypatch, _no_backoff, caplog):
    """job_id/phase ride in ``extra``, not interpolated into the message.

    These lines exist to be read while diagnosing a job, so they must be
    filterable the same way every other worker log line is.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    start_run_tracking(job_id=906)

    post = AsyncMock(side_effect=[_malformed_response(), _ok_response()])
    monkeypatch.setattr(llm_client, "_post_openrouter", post)

    with patch("api.services.llm.log_event"):
        with caplog.at_level("WARNING", logger="api.services.llm"):
            await llm_client.chat(
                messages=[{"role": "user", "content": "Hello"}],
                backend="openrouter",
                job_id=906,
                phase="formatter",
            )

    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert warnings, "no retry warning emitted"
    record = warnings[0]
    assert getattr(record, "job_id", None) == 906
    assert getattr(record, "phase", None) == "formatter"
