import logging
from typing import Any, Dict, List, Optional
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
        self._in_memory_notice_pages: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def _use_live_supabase(self) -> bool:
        return not self.is_mock and bool(self.url and self.service_role_key)

    def _rest_headers(self, prefer: str = "return=representation") -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.service_role_key}",
            "apikey": self.service_role_key,
            "Content-Type": "application/json",
            "Prefer": prefer,
        }

    @staticmethod
    def _prepare_notice_page_rows(
        notice_id: str, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize notice_pages payloads to match the database schema."""
        return [
            {
                "notice_id": notice_id,
                "page_number": int(page["page_number"]),
                "extracted_text": page.get("extracted_text", ""),
                "is_scanned": bool(page.get("is_scanned", False)),
            }
            for page in pages
        ]

    def _save_notice_pages_in_memory(
        self, notice_id: str, rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        self._in_memory_notice_pages[notice_id] = rows
        logger.info("Saved %d page(s) to in-memory notice_pages for %s", len(rows), notice_id)
        return rows

    async def upload_file(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> bool:
        """Upload raw file bytes to Supabase Storage private bucket."""
        if self._use_live_supabase:
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
                        logger.error("Supabase Storage error (%s): %s", resp.status_code, resp.text)
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to store uploaded file in private storage.",
                        )
                return True
            except httpx.RequestError as exc:
                logger.error("Storage connection failed: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Private storage service unavailable.",
                )
        key = f"{bucket}/{path}"
        self._in_memory_storage[key] = content
        logger.info("Saved file to in-memory storage: %s (%d bytes)", key, len(content))
        return True

    async def insert_notice(self, notice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert initial notice row into notices table."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notices"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        endpoint, json=notice_data, headers=self._rest_headers()
                    )
                    if resp.status_code not in (200, 201):
                        logger.error("Supabase PostgREST error (%s): %s", resp.status_code, resp.text)
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to record notice in database.",
                        )
                    results = resp.json()
                    return results[0] if isinstance(results, list) and results else notice_data
            except httpx.RequestError as exc:
                logger.error("Database connection failed: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )
        notice_id = str(notice_data.get("id"))
        self._in_memory_notices[notice_id] = notice_data
        logger.info("Saved notice to in-memory database: %s", notice_id)
        return notice_data

    async def insert_notice_pages(
        self, notice_id: str, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist extracted page rows into the notice_pages table (async)."""
        rows = self._prepare_notice_page_rows(notice_id, pages)
        if not rows:
            return []
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notice_pages?on_conflict=notice_id,page_number"
            headers = self._rest_headers(prefer="resolution=merge-duplicates,return=representation")
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=rows, headers=headers)
                    if resp.status_code not in (200, 201):
                        logger.error(
                            "Supabase PostgREST error saving notice_pages (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to store extracted notice pages in database.",
                        )
                    results = resp.json()
                    return results if isinstance(results, list) else rows
            except httpx.RequestError as exc:
                logger.error("Database connection failed saving notice_pages: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )
        return self._save_notice_pages_in_memory(notice_id, rows)

    def insert_notice_pages_sync(
        self, notice_id: str, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist extracted page rows into the notice_pages table (sync)."""
        rows = self._prepare_notice_page_rows(notice_id, pages)
        if not rows:
            return []
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notice_pages?on_conflict=notice_id,page_number"
            headers = self._rest_headers(prefer="resolution=merge-duplicates,return=representation")
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(endpoint, json=rows, headers=headers)
                    if resp.status_code not in (200, 201):
                        logger.error(
                            "Supabase PostgREST error saving notice_pages (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise RuntimeError(f"Failed to save notice_pages: HTTP {resp.status_code}")
                    results = resp.json()
                    return results if isinstance(results, list) else rows
            except httpx.RequestError as exc:
                logger.error("Database connection failed saving notice_pages: %s", exc)
                raise RuntimeError("Database service unavailable while saving notice_pages.") from exc
        return self._save_notice_pages_in_memory(notice_id, rows)

    def update_notice_review_reasons_sync(
        self, notice_id: str, review_reasons: List[str]
    ) -> None:
        """Record review reasons on a held notice (sync)."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notices?id=eq.{notice_id}"
            payload = {"publication_status": "held", "review_reasons": review_reasons}
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.patch(endpoint, json=payload, headers=self._rest_headers())
                    if resp.status_code not in (200, 204):
                        logger.warning(
                            "Failed to update review_reasons for notice %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
            except httpx.RequestError as exc:
                logger.warning("Failed to update review_reasons for notice %s: %s", notice_id, exc)
            return

        if notice_id in self._in_memory_notices:
            self._in_memory_notices[notice_id]["publication_status"] = "held"
            self._in_memory_notices[notice_id]["review_reasons"] = review_reasons

    def update_notice_sync(
        self, notice_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing notice row in the notices table (sync)."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notices?id=eq.{notice_id}"
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.patch(
                        endpoint, json=update_data, headers=self._rest_headers()
                    )
                    if resp.status_code not in (200, 204):
                        logger.error(
                            "Supabase PostgREST error updating notice %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
                        raise RuntimeError(f"Failed to update notice: HTTP {resp.status_code}")
                    if resp.status_code == 200 and resp.content:
                        results = resp.json()
                        if isinstance(results, list) and results:
                            return results[0]
                    return {"id": notice_id, **update_data}
            except httpx.RequestError as exc:
                logger.error("Database connection failed updating notice %s: %s", notice_id, exc)
                raise RuntimeError("Database service unavailable while updating notice.") from exc

        existing = self._in_memory_notices.setdefault(notice_id, {"id": notice_id})
        existing.update(update_data)
        logger.info("Updated notice in in-memory database: %s", notice_id)
        return dict(existing)

    async def update_notice(
        self, notice_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing notice row in the notices table (async)."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notices?id=eq.{notice_id}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.patch(
                        endpoint, json=update_data, headers=self._rest_headers()
                    )
                    if resp.status_code not in (200, 204):
                        logger.error(
                            "Supabase PostgREST error updating notice %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to update notice record in database.",
                        )
                    if resp.status_code == 200 and resp.content:
                        results = resp.json()
                        if isinstance(results, list) and results:
                            return results[0]
                    return {"id": notice_id, **update_data}
            except httpx.RequestError as exc:
                logger.error("Database connection failed updating notice %s: %s", notice_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        existing = self._in_memory_notices.setdefault(notice_id, {"id": notice_id})
        existing.update(update_data)
        logger.info("Updated notice in in-memory database: %s", notice_id)
        return dict(existing)

    def get_notice_sync(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single notice row by ID (sync)."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notices?id=eq.{notice_id}&select=*"
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        logger.error(
                            "Supabase PostgREST error fetching notice %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
                        return None
                    results = resp.json()
                    return results[0] if isinstance(results, list) and results else None
            except httpx.RequestError as exc:
                logger.error("Database connection failed fetching notice %s: %s", notice_id, exc)
                return None

        notice = self._in_memory_notices.get(notice_id)
        return dict(notice) if notice is not None else None


_supabase_service_instance: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    global _supabase_service_instance
    if _supabase_service_instance is None:
        _supabase_service_instance = SupabaseService()
    return _supabase_service_instance
