"""Utility functions for Editorial Assistant v3.0 API.

Provides timezone-aware datetime handling and common utilities.
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime.

    This function should be used instead of the deprecated datetime.utcnow(),
    which returns naive datetime objects.

    Returns:
        Timezone-aware datetime representing the current UTC time

    Examples:
        >>> now = utc_now()
        >>> now.tzinfo is not None
        True
        >>> now.tzinfo == timezone.utc
        True
    """
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 formatted string.

    Returns:
        ISO 8601 string representation of current UTC time with timezone info

    Examples:
        >>> timestamp = utc_now_iso()
        >>> timestamp.endswith('+00:00') or timestamp.endswith('Z')
        True
    """
    return datetime.now(timezone.utc).isoformat()


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert naive datetime to UTC-aware datetime.

    If the datetime is already timezone-aware, returns it unchanged.
    If the datetime is naive (no timezone), assumes it represents UTC
    and adds UTC timezone information.

    Args:
        dt: Datetime to convert (can be None)

    Returns:
        Timezone-aware datetime or None if input is None

    Examples:
        >>> from datetime import datetime
        >>> naive_dt = datetime(2024, 1, 15, 12, 30, 0)
        >>> aware_dt = ensure_utc(naive_dt)
        >>> aware_dt.tzinfo == timezone.utc
        True

        >>> already_aware = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        >>> ensure_utc(already_aware) == already_aware
        True

        >>> ensure_utc(None) is None
        True
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - assume UTC and add timezone info
        return dt.replace(tzinfo=timezone.utc)

    # Already timezone-aware - return unchanged
    return dt


def parse_iso_datetime(s: str) -> datetime:
    """Parse ISO 8601 datetime string to UTC-aware datetime.

    Handles various ISO 8601 formats and ensures the result is always
    in UTC with timezone information.

    Args:
        s: ISO 8601 formatted datetime string

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        ValueError: If string cannot be parsed as ISO datetime

    Examples:
        >>> dt = parse_iso_datetime("2024-01-15T12:30:00+00:00")
        >>> dt.tzinfo == timezone.utc
        True

        >>> dt = parse_iso_datetime("2024-01-15T12:30:00Z")
        >>> dt.tzinfo == timezone.utc
        True

        >>> dt = parse_iso_datetime("2024-01-15T12:30:00")
        >>> dt.tzinfo == timezone.utc
        True
    """
    try:
        # Try parsing with fromisoformat (handles most ISO formats)
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError(f"Invalid ISO datetime string: {s}") from e

    # Ensure result is UTC-aware
    return ensure_utc(dt)


def calculate_transcript_metrics(
    transcript_content: str,
    words_per_minute: int = 150,
    long_form_threshold_minutes: int = 15
) -> dict:
    """Calculate metrics from transcript content for routing decisions.

    Args:
        transcript_content: Raw transcript text
        words_per_minute: Speaking rate estimate (default 150 wpm)
        long_form_threshold_minutes: Minutes threshold for long-form classification

    Returns:
        Dict with word_count, estimated_duration_minutes, is_long_form

    Examples:
        >>> metrics = calculate_transcript_metrics("Hello world " * 1000)
        >>> metrics["word_count"]
        2000
        >>> metrics["estimated_duration_minutes"]  # 2000 / 150 = 13.33
        13.33
        >>> metrics["is_long_form"]
        False

        >>> metrics = calculate_transcript_metrics("Hello world " * 2500)
        >>> metrics["is_long_form"]  # 5000 words / 150 wpm = 33.33 min
        True
    """
    # Count words (simple split on whitespace)
    words = transcript_content.split()
    word_count = len(words)

    # Estimate duration based on speaking rate
    estimated_duration_minutes = round(word_count / words_per_minute, 2)

    # Classify as long-form if exceeds threshold
    is_long_form = estimated_duration_minutes > long_form_threshold_minutes

    return {
        "word_count": word_count,
        "estimated_duration_minutes": estimated_duration_minutes,
        "is_long_form": is_long_form,
    }


def extract_media_id(filename: str) -> str:
    """Extract Media ID from transcript filename.

    Removes common suffixes and extensions to extract the core media identifier.
    Handles PBS Wisconsin naming conventions including _ForClaude suffix,
    revision date suffixes (_REV\d+), and standard file extensions.

    Args:
        filename: Transcript filename (with or without extension)

    Returns:
        Extracted media ID (base filename without suffixes/extensions)

    Examples:
        >>> extract_media_id("2WLI1209HD_ForClaude.txt")
        '2WLI1209HD'
        >>> extract_media_id("9UNP2005HD.srt")
        '9UNP2005HD'
        >>> extract_media_id("2BUC0000HDWEB02_REV20251202.srt")
        '2BUC0000HDWEB02'
        >>> extract_media_id("Some_Project_Name.txt")
        'Some_Project_Name'
        >>> extract_media_id("2WLI1209HD_ForClaude_REV20251202.txt")
        '2WLI1209HD'
    """
    # Get filename without path
    base_name = Path(filename).name

    # Remove extension
    stem = Path(base_name).stem

    # Remove all known suffixes (can appear in any combination)
    # Pattern matches: _ForClaude, _REV followed by digits, or both
    stem = re.sub(r'(_ForClaude)?(_REV\d+)?$', '', stem, flags=re.IGNORECASE)

    return stem
