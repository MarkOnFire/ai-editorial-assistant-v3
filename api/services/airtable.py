"""
Airtable API Service - READ-ONLY

Provides read-only access to the PBS Wisconsin SST (Single Source of Truth) table.

CRITICAL: This service is intentionally READ-ONLY. No write operations are permitted.
"""

import os
from typing import Optional
import httpx
from datetime import datetime


class AirtableClient:
    """
    READ-ONLY Airtable client for SST lookups.

    This client only provides read operations against the Airtable API.
    No create, update, or delete operations are implemented.
    """

    BASE_ID = "appZ2HGwhiifQToB6"
    TABLE_ID = "tblTKFOwTvK7xw1H5"
    TABLE_NAME = "✔️Single Source of Truth"
    MEDIA_ID_FIELD = "Media ID"
    MEDIA_ID_FIELD_ID = "fld8k42kJeWMHA963"
    API_BASE_URL = "https://api.airtable.com/v0"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Airtable client.

        Args:
            api_key: Airtable API key. If not provided, uses AIRTABLE_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Airtable API key required. Provide via constructor or AIRTABLE_API_KEY env var."
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search_sst_by_media_id(self, media_id: str) -> Optional[dict]:
        """
        Search SST table by Media ID field.

        Args:
            media_id: The Media ID to search for (e.g., "3092977804")

        Returns:
            Record dict if found, None if not found or on error.
            Record format: {"id": "rec...", "fields": {...}, "createdTime": "..."}

        Raises:
            httpx.HTTPError: On network or API errors (except 404/empty results)
        """
        url = f"{self.API_BASE_URL}/{self.BASE_ID}/{self.TABLE_ID}"

        # Use filterByFormula to search by Media ID field
        # Airtable formula: {Media ID} = 'value'
        formula = f"{{{self.MEDIA_ID_FIELD}}} = '{media_id}'"

        params = {
            "filterByFormula": formula,
            "maxRecords": 1,  # We only expect one match
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                records = data.get("records", [])

                if records:
                    return records[0]
                return None

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise
            except httpx.HTTPError:
                raise

    async def get_sst_record(self, record_id: str) -> Optional[dict]:
        """
        Fetch a specific SST record by Airtable record ID.

        Args:
            record_id: Airtable record ID (e.g., "recXXXXXXXXXXXXXX")

        Returns:
            Record dict if found, None if not found.
            Record format: {"id": "rec...", "fields": {...}, "createdTime": "..."}

        Raises:
            httpx.HTTPError: On network or API errors (except 404)
        """
        url = f"{self.API_BASE_URL}/{self.BASE_ID}/{self.TABLE_ID}/{record_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise
            except httpx.HTTPError:
                raise

    def get_sst_url(self, record_id: str) -> str:
        """
        Generate Airtable web interface URL for a record.

        Args:
            record_id: Airtable record ID (e.g., "recXXXXXXXXXXXXXX")

        Returns:
            Full Airtable URL to the record
        """
        return f"https://airtable.com/{self.BASE_ID}/{self.TABLE_ID}/{record_id}"


# Factory function for dependency injection
def get_airtable_client() -> AirtableClient:
    """
    Create AirtableClient instance.

    Returns:
        Configured AirtableClient instance

    Raises:
        ValueError: If AIRTABLE_API_KEY env var is not set
    """
    return AirtableClient()
