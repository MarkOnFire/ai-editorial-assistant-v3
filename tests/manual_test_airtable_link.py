#!/usr/bin/env python3
"""
Manual test script for Airtable auto-linking on job creation.

This script demonstrates the auto-linking functionality by simulating
job creation with various scenarios.

Run with: python tests/manual_test_airtable_link.py
"""

import asyncio
import os
from api.services.utils import extract_media_id
from api.services.airtable import AirtableClient


async def test_media_id_extraction():
    """Test media ID extraction from various filenames."""
    print("\n=== Testing Media ID Extraction ===")

    test_cases = [
        "2WLI1209HD_ForClaude.txt",
        "9UNP2005HD.srt",
        "2BUC0000HDWEB02_REV20251202.srt",
        "2WLI1209HD_ForClaude_REV20251202.txt",
        "Some_Project_Name.txt",
    ]

    for filename in test_cases:
        media_id = extract_media_id(filename)
        print(f"  {filename:45} -> {media_id}")


async def test_airtable_lookup():
    """Test Airtable lookup with real API (if configured)."""
    print("\n=== Testing Airtable Lookup ===")

    # Check if Airtable API key is configured
    if not os.getenv("AIRTABLE_API_KEY"):
        print("  ⚠️  AIRTABLE_API_KEY not set - skipping live API test")
        print("     Set AIRTABLE_API_KEY in .env to test real lookups")
        return

    try:
        client = AirtableClient()
        print("  ✓ AirtableClient initialized")

        # Test with a known Media ID (adjust as needed)
        test_media_id = "2WLI1209HD"  # Replace with actual Media ID from your SST
        print(f"\n  Looking up Media ID: {test_media_id}")

        record = await client.search_sst_by_media_id(test_media_id)

        if record:
            print(f"  ✓ Found SST record!")
            print(f"    Record ID: {record['id']}")
            print(f"    URL: {client.get_sst_url(record['id'])}")
            if 'fields' in record:
                print(f"    Fields: {list(record['fields'].keys())}")
        else:
            print(f"  ℹ️  No SST record found for Media ID: {test_media_id}")

    except ValueError as e:
        print(f"  ⚠️  Configuration error: {e}")
    except Exception as e:
        print(f"  ❌ Airtable API error: {e}")


async def test_graceful_failure():
    """Test graceful handling of various failure scenarios."""
    print("\n=== Testing Graceful Failure Handling ===")

    # Test 1: Missing API key
    print("\n  Test 1: Missing API key")
    try:
        original_key = os.getenv("AIRTABLE_API_KEY")
        if "AIRTABLE_API_KEY" in os.environ:
            del os.environ["AIRTABLE_API_KEY"]

        client = AirtableClient()
        print("  ❌ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    finally:
        if original_key:
            os.environ["AIRTABLE_API_KEY"] = original_key

    # Test 2: Invalid Media ID
    if os.getenv("AIRTABLE_API_KEY"):
        print("\n  Test 2: Invalid Media ID")
        try:
            client = AirtableClient()
            record = await client.search_sst_by_media_id("INVALID_MEDIA_ID_12345")
            if record is None:
                print("  ✓ Correctly returned None for invalid Media ID")
            else:
                print("  ⚠️  Unexpectedly found a record")
        except Exception as e:
            print(f"  ✓ Gracefully handled error: {e}")


async def main():
    """Run all manual tests."""
    print("=" * 60)
    print("Airtable Auto-Linking Manual Test Suite")
    print("=" * 60)

    await test_media_id_extraction()
    await test_airtable_lookup()
    await test_graceful_failure()

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start the API server: uvicorn api.main:app --reload")
    print("  2. Test job creation: POST /api/queue with a transcript file")
    print("  3. Check job record for airtable_record_id, airtable_url, media_id")


if __name__ == "__main__":
    asyncio.run(main())
