"""
Pydantic schemas for LinkedIn integration.

Defines data models for LinkedIn feed posts, interactions, and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class LinkedInAuthor(BaseModel):
    """LinkedIn post author information."""
    id: Optional[str] = None
    name: str
    profile_url: Optional[str] = None
    profile_image: Optional[str] = None

class LinkedInSocialCounts(BaseModel):
    """LinkedIn post engagement counts."""
    numLikes: Optional[int] = 0
    numComments: Optional[int] = 0
    numShares: Optional[int] = 0
    numViews: Optional[int] = 0

class LinkedInFeedPost(BaseModel):
    """LinkedIn feed post model."""
    id: str
    urn: str
    author: LinkedInAuthor
    content: str
    created_time: Optional[int] = None
    social_counts: Optional[LinkedInSocialCounts] = None
    type: str = "feed_post"
    platform: str = "linkedin"
    
    class Config:
        extra = "allow"

class LinkedInInteractionRequest(BaseModel):
    """Request model for LinkedIn interactions."""
    post_urn: str = Field(..., description="LinkedIn post URN")
    comment_text: Optional[str] = Field(None, description="Comment text for comment interactions")
    
    class Config:
        schema_extra = {
            "example": {
                "post_urn": "urn:li:activity:123456789",
                "comment_text": "Great insights! Thanks for sharing."
            }
        }

class LinkedInInteractionResponse(BaseModel):
    """Response model for LinkedIn interactions."""
    success: bool
    message: str
    interaction_type: str  # "like", "comment", "share"
    post_urn: str
    comment_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Post liked successfully",
                "interaction_type": "like",
                "post_urn": "urn:li:activity:123456789",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class LinkedInPostDetails(BaseModel):
    """Detailed LinkedIn post information."""
    id: str
    urn: str
    author: LinkedInAuthor
    content: str
    created_time: Optional[int] = None
    last_modified: Optional[int] = None
    social_counts: Optional[LinkedInSocialCounts] = None
    comments: Optional[List[Dict[str, Any]]] = []
    media: Optional[List[Dict[str, Any]]] = []
    tags: Optional[List[str]] = []
    
    class Config:
        extra = "allow"

class LinkedInFeedResponse(BaseModel):
    """Response model for LinkedIn feed requests."""
    posts: List[LinkedInFeedPost]
    total_count: int
    has_more: bool = False
    next_cursor: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "posts": [],
                "total_count": 10,
                "has_more": False
            }
        }

class LinkedInConnectionStatus(BaseModel):
    """LinkedIn connection status model."""
    connected: bool
    has_token: bool
    token_expires_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
