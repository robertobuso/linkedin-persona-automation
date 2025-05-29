"""
API v1 router for LinkedIn Presence Automation Application.

Main router that includes all API endpoint modules and provides
centralized route configuration.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    content,
    drafts,
    engagement,
    analytics,
    preferences
)

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    content.router,
    prefix="/content",
    tags=["Content Management"]
)

api_router.include_router(
    drafts.router,
    prefix="/drafts",
    tags=["Draft Management"]
)

api_router.include_router(
    engagement.router,
    prefix="/engagement",
    tags=["Engagement"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

# --- ADD THIS SECTION ---
api_router.include_router(
    preferences.router,  # <--- Use the imported module
    prefix="/preferences", # <--- The prefix the frontend is expecting
    tags=["Preferences Management"] # <--- A descriptive tag for your API docs
)
# ------------------------