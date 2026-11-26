from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Schema for successful notice upload response."""

    notice_id: str = Field(description="Unique identifier for the created notice record")
    status: str = Field(default="pending", description="Initial processing status")
