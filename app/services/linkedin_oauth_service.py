"""
LinkedIn OAuth service for authentication and token management (2025 OpenID Connect).
"""
import os
import logging
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class LinkedInOAuthService:
    """Service for LinkedIn OAuth 2.0 with OpenID Connect authentication flow."""
    
    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")
        
        # Updated scope for 2025 - LinkedIn now uses OpenID Connect
        self.scope = os.getenv("LINKEDIN_SCOPE", "openid,profile,w_member_social")
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("LinkedIn OAuth credentials not configured")
        
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base = "https://api.linkedin.com/v2"
        # New OpenID Connect userinfo endpoint
        self.userinfo_url = "https://api.linkedin.com/v2/userinfo"

    def get_authorization_url(self, state: str) -> str:
        """Generate LinkedIn OAuth authorization URL with OpenID Connect."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": self.scope
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens and ID token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn token exchange failed: {response.text}")
                response.raise_for_status()
            
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh LinkedIn access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn token refresh failed: {response.text}")
                response.raise_for_status()
            
            return response.json()

    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Get LinkedIn user profile information using OpenID Connect userinfo endpoint.
        This is the new 2025 way to get user profile data.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn userinfo fetch failed: {response.text}")
                response.raise_for_status()
            
            return response.json()

    def decode_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Decode LinkedIn ID token (JWT) to extract user information.
        Note: This is a basic decode without signature verification.
        For production, you should verify the JWT signature.
        """
        try:
            # Split the JWT token
            header, payload, signature = id_token.split('.')
            
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            
            # Decode the payload
            decoded_payload = base64.urlsafe_b64decode(payload)
            user_info = json.loads(decoded_payload)
            
            return user_info
        except Exception as e:
            logger.error(f"Failed to decode ID token: {e}")
            return {}

    def calculate_token_expiry(self, expires_in: int) -> datetime:
        """Calculate token expiration datetime."""
        return datetime.utcnow() + timedelta(seconds=expires_in)

    async def get_user_urn_from_profile(self, access_token: str) -> str:
        """
        Get LinkedIn user URN from the /v2/people/~ endpoint.
        This is still needed for posting APIs.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/people/~",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn people API failed: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            return f"urn:li:person:{result['id']}"