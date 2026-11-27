from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.api.v1 import notices, uploader

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(notices.router, tags=["Notices"])
api_router.include_router(uploader.router, tags=["Uploader"])

