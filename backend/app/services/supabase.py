from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
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
        self._in_memory_field_sources: Dict[str, List[Dict[str, Any]]] = {}
        self._in_memory_notice_edits: Dict[str, List[Dict[str, Any]]] = {}
        self._in_memory_relationships: Dict[int, Dict[str, Any]] = {}
        self._in_memory_relationship_seq: int = 0
        self._in_memory_processing_events: Dict[str, List[Dict[str, Any]]] = {}
        self._in_memory_error_reports: Dict[int, Dict[str, Any]] = {}
        self._in_memory_error_report_seq: int = 0

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

    @staticmethod
    def _parse_content_range_total(content_range: Optional[str], fallback: int) -> int:
        if not content_range or "/" not in content_range:
            return fallback
        total_part = content_range.split("/", 1)[1].strip()
        if total_part.isdigit():
            return int(total_part)
        return fallback

    async def get_notice(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single notice row by ID (async)."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notices?id=eq.{notice_id}&select=*"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        logger.error(
                            "Supabase PostgREST error fetching notice %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to fetch notice record.",
                        )
                    results = resp.json()
                    return results[0] if isinstance(results, list) and results else None
            except httpx.RequestError as exc:
                logger.error("Database connection failed fetching notice %s: %s", notice_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        notice = self._in_memory_notices.get(notice_id)
        return dict(notice) if notice is not None else None

    async def list_review_queue(
        self, *, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List notices that are held or failed processing for uploader review."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/notices"
                "?or=(publication_status.eq.held,processing_status.eq.failed)"
                "&publication_status=neq.withdrawn"
                "&order=updated_at.desc"
                f"&limit={limit}&offset={offset}&select=*"
            )
            headers = self._rest_headers(prefer="count=exact")
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=headers)
                    if resp.status_code not in (200, 206):
                        logger.error(
                            "Supabase PostgREST error listing review queue (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to load review queue.",
                        )
                    items = resp.json() if isinstance(resp.json(), list) else []
                    total = self._parse_content_range_total(
                        resp.headers.get("content-range"), len(items)
                    )
                    return items, total
            except httpx.RequestError as exc:
                logger.error("Database connection failed listing review queue: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        eligible = [
            dict(notice)
            for notice in self._in_memory_notices.values()
            if notice.get("publication_status") != "withdrawn"
            and (
                notice.get("publication_status") == "held"
                or notice.get("processing_status") == "failed"
            )
        ]
        eligible.sort(
            key=lambda n: str(n.get("updated_at") or n.get("created_at") or ""),
            reverse=True,
        )
        total = len(eligible)
        return eligible[offset : offset + limit], total

    async def get_notice_pages(self, notice_id: str) -> List[Dict[str, Any]]:
        """Retrieve ordered page records for a notice."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/notice_pages"
                f"?notice_id=eq.{notice_id}&order=page_number.asc&select=*"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        logger.error(
                            "Supabase PostgREST error fetching notice_pages (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to fetch notice pages.",
                        )
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError as exc:
                logger.error("Database connection failed fetching notice_pages: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        pages = list(self._in_memory_notice_pages.get(notice_id, []))
        pages.sort(key=lambda p: int(p.get("page_number", 0)))
        return [dict(p) for p in pages]

    async def get_field_sources(self, notice_id: str) -> List[Dict[str, Any]]:
        """Retrieve field source provenance records for a notice."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/field_sources"
                f"?notice_id=eq.{notice_id}&order=id.asc&select=*"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        logger.error(
                            "Supabase PostgREST error fetching field_sources (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to fetch field evidence.",
                        )
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError as exc:
                logger.error("Database connection failed fetching field_sources: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        return [dict(row) for row in self._in_memory_field_sources.get(notice_id, [])]

    def replace_ai_field_sources_sync(
        self, notice_id: str, sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Replace AI-extracted field_sources rows for a notice (sync)."""
        rows = [
            {
                "notice_id": notice_id,
                "field_name": src["field_name"],
                "value_text": src.get("value_text"),
                "source_page": src.get("source_page"),
                "source_quote": src.get("source_quote"),
                "extraction_method": src.get("extraction_method", "ai"),
                "confidence": src.get("confidence"),
                "verified": bool(src.get("verified", False)),
                "human_edited": bool(src.get("human_edited", False)),
            }
            for src in sources
        ]
        if self._use_live_supabase:
            delete_url = (
                f"{self.url}/rest/v1/field_sources"
                f"?notice_id=eq.{notice_id}&extraction_method=eq.ai"
            )
            insert_url = f"{self.url}/rest/v1/field_sources"
            try:
                with httpx.Client(timeout=15.0) as client:
                    client.delete(delete_url, headers=self._rest_headers())
                    if not rows:
                        return []
                    resp = client.post(insert_url, json=rows, headers=self._rest_headers())
                    if resp.status_code not in (200, 201):
                        logger.warning(
                            "Failed to store field_sources for %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
                        return rows
                    result = resp.json()
                    return result if isinstance(result, list) else rows
            except httpx.RequestError as exc:
                logger.warning("Database error storing field_sources for %s: %s", notice_id, exc)
                return rows

        existing = [
            row
            for row in self._in_memory_field_sources.get(notice_id, [])
            if row.get("extraction_method") != "ai"
        ]
        self._in_memory_field_sources[notice_id] = existing + rows
        return rows

    async def replace_ai_field_sources(
        self, notice_id: str, sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Replace AI-extracted field_sources rows for a notice (async)."""
        rows = [
            {
                "notice_id": notice_id,
                "field_name": src["field_name"],
                "value_text": src.get("value_text"),
                "source_page": src.get("source_page"),
                "source_quote": src.get("source_quote"),
                "extraction_method": src.get("extraction_method", "ai"),
                "confidence": src.get("confidence"),
                "verified": bool(src.get("verified", False)),
                "human_edited": bool(src.get("human_edited", False)),
            }
            for src in sources
        ]
        if self._use_live_supabase:
            delete_url = (
                f"{self.url}/rest/v1/field_sources"
                f"?notice_id=eq.{notice_id}&extraction_method=eq.ai"
            )
            insert_url = f"{self.url}/rest/v1/field_sources"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    await client.delete(delete_url, headers=self._rest_headers())
                    if not rows:
                        return []
                    resp = await client.post(insert_url, json=rows, headers=self._rest_headers())
                    if resp.status_code not in (200, 201):
                        logger.warning(
                            "Failed to store field_sources for %s (%s): %s",
                            notice_id,
                            resp.status_code,
                            resp.text,
                        )
                        return rows
                    result = resp.json()
                    return result if isinstance(result, list) else rows
            except httpx.RequestError as exc:
                logger.warning("Database error storing field_sources for %s: %s", notice_id, exc)
                return rows

        existing = [
            row
            for row in self._in_memory_field_sources.get(notice_id, [])
            if row.get("extraction_method") != "ai"
        ]
        self._in_memory_field_sources[notice_id] = existing + rows
        return rows

    async def mark_fields_human_edited(
        self,
        notice_id: str,
        field_values: Dict[str, Optional[str]],
    ) -> None:
        """Mark corrected fields as human-edited in field_sources."""
        if not field_values:
            return
        if self._use_live_supabase:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    for field_name, val in field_values.items():
                        del_url = (
                            f"{self.url}/rest/v1/field_sources"
                            f"?notice_id=eq.{notice_id}&field_name=eq.{field_name}"
                        )
                        await client.delete(del_url, headers=self._rest_headers())
                        row = {
                            "notice_id": notice_id,
                            "field_name": field_name,
                            "value_text": val,
                            "extraction_method": "human",
                            "verified": True,
                            "human_edited": True,
                        }
                        await client.post(
                            f"{self.url}/rest/v1/field_sources",
                            json=row,
                            headers=self._rest_headers(),
                        )
            except httpx.RequestError as exc:
                logger.error("Failed updating field_sources for %s: %s", notice_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )
            return

        current = self._in_memory_field_sources.get(notice_id, [])
        filtered = [row for row in current if row.get("field_name") not in field_values]
        for field_name, val in field_values.items():
            filtered.append(
                {
                    "notice_id": notice_id,
                    "field_name": field_name,
                    "value_text": val,
                    "source_page": None,
                    "source_quote": None,
                    "extraction_method": "human",
                    "confidence": None,
                    "verified": True,
                    "human_edited": True,
                }
            )
        self._in_memory_field_sources[notice_id] = filtered

    async def insert_notice_edits(self, edits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert audit log entries into notice_edits."""
        if not edits:
            return []
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notice_edits"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=edits, headers=self._rest_headers())
                    if resp.status_code not in (200, 201):
                        logger.error(
                            "Supabase PostgREST error inserting notice_edits (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to record edit audit log.",
                        )
                    results = resp.json()
                    return results if isinstance(results, list) else edits
            except httpx.RequestError as exc:
                logger.error("Database connection failed inserting notice_edits: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        stored: List[Dict[str, Any]] = []
        for entry in edits:
            notice_id = str(entry["notice_id"])
            row = {"edited_at": now_iso, **entry}
            self._in_memory_notice_edits.setdefault(notice_id, []).append(row)
            stored.append(dict(row))
        return stored

    async def get_notice_edits(self, notice_id: str) -> List[Dict[str, Any]]:
        """Retrieve human edit history for a notice."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/notice_edits"
                f"?notice_id=eq.{notice_id}&order=edited_at.desc&select=*"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        return []
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError:
                return []

        edits = list(self._in_memory_notice_edits.get(notice_id, []))
        edits.sort(key=lambda e: str(e.get("edited_at") or ""), reverse=True)
        return [dict(e) for e in edits]

    async def get_notice_relationships(self, notice_id: str) -> List[Dict[str, Any]]:
        """Retrieve relationships involving a notice (as earlier or later)."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/notice_relationships"
                f"?or=(earlier_id.eq.{notice_id},later_id.eq.{notice_id})&order=id.asc&select=*"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        logger.error(
                            "Supabase PostgREST error fetching relationships (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to fetch notice relationships.",
                        )
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError as exc:
                logger.error("Database connection failed fetching relationships: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        return [
            dict(rel)
            for rel in self._in_memory_relationships.values()
            if rel.get("earlier_id") == notice_id or rel.get("later_id") == notice_id
        ]

    async def get_relationship_by_id(self, relation_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single notice_relationships record by ID."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notice_relationships?id=eq.{relation_id}&select=*"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to fetch notice relationship.",
                        )
                    rows = resp.json()
                    return rows[0] if isinstance(rows, list) and rows else None
            except httpx.RequestError as exc:
                logger.error("Database connection failed fetching relationship %s: %s", relation_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        rel = self._in_memory_relationships.get(relation_id)
        return dict(rel) if rel is not None else None

    async def update_relationship(
        self, relation_id: int, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a notice_relationships record."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notice_relationships?id=eq.{relation_id}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.patch(
                        endpoint, json=update_data, headers=self._rest_headers()
                    )
                    if resp.status_code not in (200, 204):
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to update notice relationship.",
                        )
                    if resp.status_code == 200 and resp.content:
                        rows = resp.json()
                        if isinstance(rows, list) and rows:
                            return rows[0]
                    return {"id": relation_id, **update_data}
            except httpx.RequestError as exc:
                logger.error("Database error updating relationship %s: %s", relation_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        rel = self._in_memory_relationships.get(relation_id)
        if rel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found.")
        rel.update(update_data)
        return dict(rel)

    async def delete_relationship(self, relation_id: int) -> None:
        """Delete an unconfirmed notice_relationships record."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/notice_relationships?id=eq.{relation_id}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.delete(endpoint, headers=self._rest_headers())
                    if resp.status_code not in (200, 204):
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to remove rejected relationship.",
                        )
                    return
            except httpx.RequestError as exc:
                logger.error("Database error deleting relationship %s: %s", relation_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        self._in_memory_relationships.pop(relation_id, None)

    async def insert_processing_event(
        self,
        notice_id: str,
        step: str,
        outcome: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a processing/review lifecycle event for a notice."""
        payload = {
            "notice_id": notice_id,
            "step": step,
            "outcome": outcome,
            "message": message,
        }
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/processing_events"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=payload, headers=self._rest_headers())
                    if resp.status_code in (200, 201) and resp.content:
                        rows = resp.json()
                        if isinstance(rows, list) and rows:
                            return rows[0]
                    return payload
            except httpx.RequestError as exc:
                logger.warning("Failed recording processing event for %s: %s", notice_id, exc)
                return payload

        event = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        self._in_memory_processing_events.setdefault(notice_id, []).append(event)
        return dict(event)

    async def get_processing_events(self, notice_id: str) -> List[Dict[str, Any]]:
        """Retrieve processing/review history events for a notice."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/processing_events"
                f"?notice_id=eq.{notice_id}&order=created_at.asc&select=*"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        return []
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError:
                return []

        return [dict(e) for e in self._in_memory_processing_events.get(notice_id, [])]

    async def create_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = 900,
    ) -> Optional[str]:
        """Generate a short-lived signed download URL for a private storage object."""
        if not path:
            return None
        if self._use_live_supabase:
            endpoint = f"{self.url}/storage/v1/object/sign/{bucket}/{path}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        endpoint,
                        json={"expiresIn": expires_in},
                        headers=self._rest_headers(),
                    )
                    if resp.status_code != 200:
                        logger.warning(
                            "Failed generating signed URL for %s/%s (%s)",
                            bucket,
                            path,
                            resp.status_code,
                        )
                        return None
                    data = resp.json()
                    signed_path = data.get("signedURL") or data.get("signedUrl")
                    if not signed_path:
                        return None
                    if signed_path.startswith("http"):
                        return signed_path
                    return f"{self.url}/storage/v1{signed_path}"
            except httpx.RequestError as exc:
                logger.warning("Storage signed URL error: %s", exc)
                return None

        return None

    async def list_published_notices(self) -> List[Dict[str, Any]]:
        """Retrieve all notices with publication_status='published'."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/notices"
                "?publication_status=eq.published"
                "&order=published_at.desc"
                "&select=id,title,notice_date,deadline_date,audience,category,summary,"
                "storage_path,publication_status,relationship_status,published_at,created_at,updated_at"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        logger.error(
                            "Supabase PostgREST error listing published notices (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to load published notices.",
                        )
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError as exc:
                logger.error("Database connection failed listing published notices: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        return [
            dict(notice)
            for notice in self._in_memory_notices.values()
            if notice.get("publication_status") == "published"
        ]

    async def list_confirmed_relationships(self) -> List[Dict[str, Any]]:
        """Retrieve all confirmed notice relationships."""
        if self._use_live_supabase:
            endpoint = (
                f"{self.url}/rest/v1/notice_relationships"
                "?confirmed=eq.true&order=created_at.desc&select=*"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        return []
                    rows = resp.json()
                    return rows if isinstance(rows, list) else []
            except httpx.RequestError:
                return []

        return [
            dict(rel)
            for rel in self._in_memory_relationships.values()
            if rel.get("confirmed") is True
        ]

    async def list_all_notices_for_management(
        self,
        *,
        publication_status: Optional[str] = None,
        processing_status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List notices for staff management regardless of publication status."""
        if self._use_live_supabase:
            params: List[str] = [
                "order=created_at.desc",
                f"limit={limit}",
                f"offset={offset}",
                "select=*",
            ]
            if publication_status:
                params.append(f"publication_status=eq.{publication_status}")
            if processing_status:
                params.append(f"processing_status=eq.{processing_status}")
            endpoint = f"{self.url}/rest/v1/notices?{'&'.join(params)}"
            headers = self._rest_headers(prefer="count=exact")
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=headers)
                    if resp.status_code not in (200, 206):
                        logger.error(
                            "Supabase PostgREST error listing management notices (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to list notices.",
                        )
                    items = resp.json() if isinstance(resp.json(), list) else []
                    total = self._parse_content_range_total(
                        resp.headers.get("content-range"), len(items)
                    )
                    return items, total
            except httpx.RequestError as exc:
                logger.error("Database error listing management notices: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        rows = [dict(n) for n in self._in_memory_notices.values()]
        if publication_status:
            rows = [r for r in rows if r.get("publication_status") == publication_status]
        if processing_status:
            rows = [r for r in rows if r.get("processing_status") == processing_status]
        rows.sort(
            key=lambda n: str(n.get("created_at") or n.get("updated_at") or ""),
            reverse=True,
        )
        total = len(rows)
        return rows[offset : offset + limit], total

    async def insert_error_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a public error report into error_reports."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/error_reports"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        endpoint, json=report_data, headers=self._rest_headers()
                    )
                    if resp.status_code not in (200, 201):
                        logger.error(
                            "Supabase PostgREST error inserting error_report (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to submit error report.",
                        )
                    rows = resp.json()
                    return rows[0] if isinstance(rows, list) and rows else report_data
            except httpx.RequestError as exc:
                logger.error("Database error inserting error_report: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        self._in_memory_error_report_seq += 1
        rid = self._in_memory_error_report_seq
        row = {
            "id": rid,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": None,
            "resolved_at": None,
            "resolution_note": None,
            **report_data,
        }
        self._in_memory_error_reports[rid] = row
        return dict(row)

    async def list_error_reports(
        self,
        *,
        report_status: Optional[str] = "open",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List error reports filtered by status for uploader review."""
        if self._use_live_supabase:
            params: List[str] = [
                "order=created_at.desc",
                f"limit={limit}",
                f"offset={offset}",
                "select=*,notices(title)",
            ]
            if report_status:
                params.append(f"status=eq.{report_status}")
            endpoint = f"{self.url}/rest/v1/error_reports?{'&'.join(params)}"
            headers = self._rest_headers(prefer="count=exact")
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=headers)
                    if resp.status_code not in (200, 206):
                        logger.error(
                            "Supabase PostgREST error listing error_reports (%s): %s",
                            resp.status_code,
                            resp.text,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to load error reports.",
                        )
                    items = resp.json() if isinstance(resp.json(), list) else []
                    total = self._parse_content_range_total(
                        resp.headers.get("content-range"), len(items)
                    )
                    return items, total
            except httpx.RequestError as exc:
                logger.error("Database error listing error_reports: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        rows = []
        for report in self._in_memory_error_reports.values():
            if report_status and report.get("status") != report_status:
                continue
            item = dict(report)
            notice = self._in_memory_notices.get(str(report["notice_id"]))
            item["notice_title"] = notice.get("title") if notice else None
            rows.append(item)
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        total = len(rows)
        return rows[offset : offset + limit], total

    async def get_error_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single error report by ID."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/error_reports?id=eq.{report_id}&select=*"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(endpoint, headers=self._rest_headers())
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to fetch error report.",
                        )
                    rows = resp.json()
                    return rows[0] if isinstance(rows, list) and rows else None
            except httpx.RequestError as exc:
                logger.error("Database error fetching error_report %s: %s", report_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        row = self._in_memory_error_reports.get(report_id)
        return dict(row) if row is not None else None

    async def update_error_report(
        self, report_id: int, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an error report record."""
        if self._use_live_supabase:
            endpoint = f"{self.url}/rest/v1/error_reports?id=eq.{report_id}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.patch(
                        endpoint, json=update_data, headers=self._rest_headers()
                    )
                    if resp.status_code not in (200, 204):
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Failed to update error report.",
                        )
                    if resp.status_code == 200 and resp.content:
                        rows = resp.json()
                        if isinstance(rows, list) and rows:
                            return rows[0]
                    return {"id": report_id, **update_data}
            except httpx.RequestError as exc:
                logger.error("Database error updating error_report %s: %s", report_id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Database service unavailable.",
                )

        row = self._in_memory_error_reports.get(report_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error report not found.")
        row.update(update_data)
        return dict(row)


_supabase_service_instance: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    global _supabase_service_instance
    if _supabase_service_instance is None:
        _supabase_service_instance = SupabaseService()
    return _supabase_service_instance
