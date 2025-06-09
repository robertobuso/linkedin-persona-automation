"""
Enhanced schemas for draft management with tone selection.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field

class ToneStyle(str, Enum):
    """Available tone styles for draft generation."""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    STORYTELLING = "storytelling"
    HUMOROUS = "humorous"
    PROFESSIONAL_THOUGHT_LEADER = "professional_thought_leader"
    EDUCATIONAL = "educational"
    ENGAGEMENT_OPTIMIZED = "engagement_optimized"



class DraftRegenerateRequest(BaseModel):
    """Request model for draft regeneration."""
    tone_style: ToneStyle = Field(..., description="Tone style for regeneration")
    preserve_hashtags: bool = Field(False, description="Whether to preserve existing hashtags")
    
    class Config:
        schema_extra = {
            "example": {
                "tone_style": "storytelling",
                "preserve_hashtags": False
            }
        }

class DraftWithContent(BaseModel):
    """Draft model with full content details."""
    id: UUID
    user_id: UUID
    content: str
    hashtags: List[str]
    title: Optional[str] = None
    status: str
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    linkedin_post_id: Optional[str] = None
    linkedin_post_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Generation metadata
    generation_metadata: Optional[dict] = None
    ai_model_used: Optional[str] = None
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "content": "Excited to share insights about AI in business...",
                "hashtags": ["#AI", "#Business", "#Innovation"],
                "status": "ready",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

class DraftRegenerateResponse(BaseModel):
    """Response model for draft regeneration."""
    draft: DraftWithContent
    tone_style: ToneStyle
    regenerated_at: datetime
    success: bool = True
    message: str = "Draft regenerated successfully"
    
    class Config:
        schema_extra = {
            "example": {
                "draft": {},  # DraftWithContent example
                "tone_style": "storytelling",
                "regenerated_at": "2024-01-15T10:35:00Z",
                "success": True,
                "message": "Draft regenerated successfully"
            }
        }

class ContentItemWithDraftStatus(BaseModel):
    """Content item model with draft generation status."""
    id: UUID
    title: str
    content: str
    url: str
    source_name: str
    published_at: Optional[datetime]
    relevance_score: Optional[int]
    draft_generated: bool = False
    tags: List[str] = []
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "The Future of AI in Business",
                "content": "Article content here...",
                "url": "https://example.com/article",
                "source_name": "Tech News",
                "draft_generated": False,
                "relevance_score": 85
            }
        }
