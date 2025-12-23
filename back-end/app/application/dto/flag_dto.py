"""
DTOs para Flag Submission.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class FlagSubmitDTO(BaseModel):
    """DTO para enviar una flag."""
    
    flag: str = Field(..., min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "flag": "flag{example_flag_123}"
            }
        }


class FlagSubmitResponseDTO(BaseModel):
    """DTO para respuesta de submit de flag."""
    
    success: bool
    message: str
    points: Optional[int] = None
    already_solved: bool = False


class SubmissionHistoryDTO(BaseModel):
    """DTO para historial de submissions."""
    
    id: UUID
    ctf_id: UUID
    is_correct: bool
    submitted_at: datetime
    
    class Config:
        from_attributes = True
