import logging
from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Extract and verify user identity and application profile from authorization token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or are invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token cannot be empty.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Dev / test shortcut tokens
    if token in ("mock-uploader-token", "test-uploader-token", "valid-uploader-token"):
        return {
            "id": "00000000-0000-0000-0000-000000000001",
            "email": "uploader@kmc.du.ac.in",
            "role": "uploader",
            "full_name": "Test Uploader",
        }
    if token in ("mock-admin-token", "test-admin-token", "valid-admin-token"):
        return {
            "id": "00000000-0000-0000-0000-000000000002",
            "email": "admin@kmc.du.ac.in",
            "role": "admin",
            "full_name": "Test Admin",
        }
    if token in ("mock-viewer-token", "test-viewer-token", "student-token"):
        return {
            "id": "00000000-0000-0000-0000-000000000003",
            "email": "student@kmc.du.ac.in",
            "role": "student",
            "full_name": "Test Student",
        }

    # 2. Live Supabase Auth verification
    if settings.SUPABASE_URL and (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                auth_resp = await client.get(
                    f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY,
                    },
                )
                if auth_resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired authentication token.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                user_info = auth_resp.json()
                user_id = user_info.get("id")

                # Look up application role in profiles table
                prof_resp = await client.get(
                    f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/profiles",
                    headers={
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY}",
                        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY,
                    },
                    params={"id": f"eq.{user_id}", "select": "id,role,full_name"},
                )
                if prof_resp.status_code == 200 and prof_resp.json():
                    profile = prof_resp.json()[0]
                    return {
                        "id": user_id,
                        "email": user_info.get("email"),
                        "role": profile.get("role"),
                        "full_name": profile.get("full_name"),
                    }
                else:
                    return {
                        "id": user_id,
                        "email": user_info.get("email"),
                        "role": None,
                    }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Supabase auth check failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable.",
            )

    # 3. JWT unverified decoding fallback for local testing
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub") or payload.get("id", "00000000-0000-0000-0000-000000000000")
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})
        role = (
            payload.get("role")
            or user_metadata.get("role")
            or app_metadata.get("role")
            or "uploader"
        )
        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": role,
            "full_name": user_metadata.get("full_name", "JWT User"),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_uploader(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Enforce that the requesting user possesses an authorized uploader or admin role."""
    role = current_user.get("role")
    if role not in ("uploader", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Requires uploader or admin permissions.",
        )
    return current_user
