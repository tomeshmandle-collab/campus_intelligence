import logging
from typing import Any, Dict, Optional
import httpx
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service wrapping Supabase Storage and PostgREST database operations."""

    def __init__(
        self,
        url: Optional[str] = None,
        service_role_key: Optional[str] = None,
        is_mock: bool = False,
    ):
        self.is_mock = is_mock
        self.url = (url if url is not None else settings.SUPABASE_URL or "").rstrip("/")
        self.service_role_key = (
            service_role_key
            if service_role_key is not None
            else (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY or "")
        )
        # In-memory storage for test/development environments without live credentials
        self._in_memory_storage: Dict[str, bytes] = {}
        self._in_memory_notices: Dict[str, Dict[str, Any]] = {}

    async def upload_file(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> bool:
        """Upload raw file bytes to Supabase Storage private bucket."""
        if not self.is_mock and self.url and self.service_role_key:
            endpoint = f"{self.url}/storage/v1/object/{bucket}/{path}"
            headers = {
                "Authorization": f"Bearer {self.service_role_key}",
                "apikey": self.service_role_key,
                "Content-Type": content_type,
                "x-upsert": "true",
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(endpoint, content=content, headers=headers)
                    if resp.status_code not in (200, 201):
                        logger.error(f"Supabase Storage error ({resp.status_code}): {resp.text}")
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to store uploaded file in private storage.",
                        )
                return True
            except httpx.RequestError as exc:
                logger.error(f"Storage connection failed: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Private storage service unavailable.",
                )
        else:
            # Fallback for dev / mock mode
            key = f"{bucket}/{path}"
            self._in_memory_storage[key] = content
            logger.info(f"Saved file to in-memory storage: {key} ({len(content)} bytes)")
            return True

    async def insert_notice(self, notice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert initial notice row into notices table."""
        if not self.is_mock and self.url and self.service_role_key:
            endpoint = f"{self.url}/rest/v1/notices"
            headers = {
                "Authorization": f"Bearer {self.service_role_key}",
                "apikey": self.service_role_key,
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=notice_data, headers=headers)
                    if resp.status_code not in (200, 201):
                        logger.error(f"Supabase PostgREST error ({resp.status_code}): {resp.text}")
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to record notice in database.",
                        )
                    results = resp.json()
                    return results[0] if isinstance(results, list) and results else notice_data
            except httpx.RequestError as exc:
                logger.error(f"Database connection failed: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )
        else:
            # Fallback for dev / mock mode
            notice_id = str(notice_data.get("id"))
            self._in_memory_notices[notice_id] = notice_data
            logger.info(f"Saved notice to in-memory database: {notice_id}")
            return notice_data


_supabase_service_instance: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    global _supabase_service_instance
    if _supabase_service_instance is None:
        _supabase_service_instance = SupabaseService()
    return _supabase_service_instance
