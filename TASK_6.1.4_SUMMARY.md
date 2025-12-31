# Task 6.1.4: Auto-link SST on Job Creation - Implementation Summary

## Overview
Implemented automatic linking of Airtable SST (Single Source of Truth) records when jobs are created through the queue API endpoint.

## Changes Made

### Modified Files

#### `/Users/mriechers/Developer/ai-editorial-assistant-v3/api/routers/queue.py`
- Added imports for `AirtableClient`, `extract_media_id`, `JobUpdate`, and `logging`
- Modified `add_to_queue()` endpoint to automatically:
  1. Extract Media ID from transcript filename using `extract_media_id()`
  2. Lookup SST record in Airtable using `AirtableClient.search_sst_by_media_id()`
  3. Store Airtable record ID, URL, and Media ID on job if found
  4. Handle all error cases gracefully (API key missing, record not found, API errors)

### New Files

#### `/Users/mriechers/Developer/ai-editorial-assistant-v3/tests/api/test_queue_router.py`
Comprehensive test suite covering:
- Successful Airtable lookup and linking
- SST record not found scenario
- Missing API key handling
- Airtable API error handling
- Media ID extraction from various filename formats

#### `/Users/mriechers/Developer/ai-editorial-assistant-v3/tests/manual_test_airtable_link.py`
Manual test script for validating the integration with live Airtable API (when configured).

## Implementation Details

### Auto-linking Logic Flow

```python
1. Job is created with status=pending
2. Extract media_id from transcript_file:
   - "2WLI1209HD_ForClaude.txt" -> "2WLI1209HD"
   - "9UNP2005HD.srt" -> "9UNP2005HD"
   - "2BUC0000HDWEB02_REV20251202.srt" -> "2BUC0000HDWEB02"

3. Try to create AirtableClient:
   - If AIRTABLE_API_KEY not set -> ValueError -> catch and log warning
   - If set -> proceed to lookup

4. Search for SST record by Media ID:
   - If found -> update job with airtable_record_id, airtable_url, media_id
   - If not found -> update job with media_id only, log warning

5. Any errors -> catch, log warning, continue (job creation never fails)
```

### Error Handling

The implementation includes graceful handling for:

1. **Missing API Key**: ValueError caught, logged, job creation continues
2. **SST Record Not Found**: Updates job with media_id only, logs warning
3. **Airtable API Errors**: Generic Exception caught, logged, job creation continues
4. **Always**: Job creation succeeds regardless of Airtable status

### Logging

Added comprehensive logging:
- `logger.info()` - Successful SST linkage
- `logger.warning()` - SST not found, API key missing, or API errors

## Exit Criteria Verification

All exit criteria met:

- [x] Queue POST extracts Media ID from transcript filename
  - Uses `extract_media_id()` from `api.services.utils`
  - Handles PBS Wisconsin naming conventions (_ForClaude, _REV suffixes)

- [x] Looks up SST record via Airtable service
  - Uses `AirtableClient.search_sst_by_media_id()`
  - Proper async/await handling

- [x] Stores record ID, URL, and media_id on job
  - Updates job with `airtable_record_id`, `airtable_url`, `media_id`
  - Uses `JobUpdate` model and `database.update_job()`

- [x] Graceful handling when SST not found or Airtable unavailable
  - Try/except blocks for ValueError (API key) and Exception (API errors)
  - Logs warnings but continues
  - Stores media_id even when lookup fails

- [x] Job creation never fails due to Airtable issues
  - All Airtable operations in try/except block
  - Job created first, then Airtable lookup attempted
  - Any errors logged but not raised

## Test Results

All tests passing:

```
tests/api/test_queue_router.py::test_add_to_queue_with_successful_airtable_lookup PASSED
tests/api/test_queue_router.py::test_add_to_queue_airtable_not_found PASSED
tests/api/test_queue_router.py::test_add_to_queue_airtable_api_key_missing PASSED
tests/api/test_queue_router.py::test_add_to_queue_airtable_api_error PASSED
tests/api/test_queue_router.py::test_media_id_extraction PASSED

5 passed, 3 warnings in 0.28s
```

## Usage Example

### API Request
```bash
POST /api/queue
{
  "project_name": "Wisconsin Life 1209",
  "transcript_file": "2WLI1209HD_ForClaude.txt",
  "priority": 0
}
```

### Response (Success with Airtable Link)
```json
{
  "id": 1,
  "project_path": "/path/to/OUTPUT/Wisconsin_Life_1209",
  "transcript_file": "2WLI1209HD_ForClaude.txt",
  "status": "pending",
  "media_id": "2WLI1209HD",
  "airtable_record_id": "recXXXXXXXXXXXXXX",
  "airtable_url": "https://airtable.com/appZ2HGwhiifQToB6/tblTKFOwTvK7xw1H5/recXXXXXXXXXXXXXX",
  ...
}
```

### Response (SST Not Found)
```json
{
  "id": 2,
  "project_path": "/path/to/OUTPUT/Unknown_Project",
  "transcript_file": "UNKNOWN_MEDIA_ID.txt",
  "status": "pending",
  "media_id": "UNKNOWN_MEDIA_ID",
  "airtable_record_id": null,
  "airtable_url": null,
  ...
}
```

## Dependencies Used

- `api.services.airtable.AirtableClient` - SST record lookup
- `api.services.utils.extract_media_id()` - Media ID extraction
- `api.models.job.JobUpdate` - Job update schema
- `api.services.database.update_job()` - Job persistence

## Next Steps

1. Test with live Airtable API:
   - Set `AIRTABLE_API_KEY` in `.env`
   - Create test job with real Media ID
   - Verify SST record linkage

2. Monitor logs for warnings about:
   - Missing SST records
   - API key configuration issues
   - Airtable API errors

3. Consider adding metrics/monitoring for:
   - SST linkage success rate
   - Airtable API response times
   - Failed lookup reasons
