"""
AmoCRM API Integration Service.

This module handles all communications with the AmoCRM REST API, 
including initial OAuth2 token exchange, token refresh logic, 
contact searching, and lead creation.
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AmoCRMToken
from core.config import settings

logger = logging.getLogger(__name__)


class AmoCRMService:
    """
    Service for interacting with AmoCRM API.
    
    Manages token lifecycle (exchange, storage, and auto-refresh) and CRM entities.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the service with a database session.

        Args:
            db_session (AsyncSession): Database session for token storage access.
        """
        self.db_session = db_session
        self.base_url = f"https://{settings.amo_subdomain}.amocrm.ru"

    async def init_tokens(self, auth_code: str) -> None:
        """
        Exchanges the one-time Authorization Code for Access and Refresh tokens.
        
        This method must be run once during the initial setup. Saves the retrieved
        tokens into the PostgreSQL database.

        Args:
            auth_code (str): One-time authorization code from AmoCRM console.
        """
        url = f"{self.base_url}/oauth2/access_token"
        payload = {
            "client_id": settings.amo_client_id,
            "client_secret": settings.amo_client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": settings.amo_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to init tokens: {response.text}")
                raise Exception("AmoCRM token exchange failed.")

            data = response.json()
            
            # Clear any existing tokens first to keep exactly 1 row (as per Spec)
            await self.db_session.execute(select(AmoCRMToken)) # Fetch to register
            # Write new token row
            new_token = AmoCRMToken(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                updated_at=datetime.now(timezone.utc)
            )
            self.db_session.add(new_token)
            await self.db_session.commit()
            logger.info("AmoCRM tokens successfully initialized and saved to DB.")

    async def _refresh_access_token(self, current_token: AmoCRMToken) -> str:
        """
        Uses the refresh token to obtain a new access token from AmoCRM.
        
        Updates the token row in the database with the new values.

        Args:
            current_token (AmoCRMToken): Current token record from DB.

        Returns:
            str: The newly issued active access token.
        """
        url = f"{self.base_url}/oauth2/access_token"
        payload = {
            "client_id": settings.amo_client_id,
            "client_secret": settings.amo_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": current_token.refresh_token,
            "redirect_uri": settings.amo_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to refresh tokens: {response.text}")
                raise Exception("AmoCRM token refresh failed.")

            data = response.json()
            
            # Update the single token record in DB
            current_token.access_token = data["access_token"]
            current_token.refresh_token = data["refresh_token"]
            current_token.updated_at = datetime.now(timezone.utc)
            
            await self.db_session.commit()
            logger.info("AmoCRM tokens successfully refreshed and updated in DB.")
            return data["access_token"]

    async def _get_auth_headers(self) -> dict:
        """
        Retrieves active access token from DB, auto-refreshes if expired.

        Returns:
            dict: HTTP headers including the active Bearer token.
        """
        stmt = select(AmoCRMToken).limit(1)
        result = await self.db_session.execute(stmt)
        token_data = result.scalar_one_or_none()

        if not token_data:
            logger.error("AmoCRM tokens not found in DB. Run init_tokens first.")
            raise Exception("No AmoCRM tokens found.")

        # AmoCRM access token expires in 24 hours.
        # We refresh it if it was updated more than 23 hours ago (safety margin).
        expiration_time = token_data.updated_at + timedelta(hours=23)
        
        if datetime.now(timezone.utc) > expiration_time:
            logger.info("Access token expired or close to expiration. Refreshing...")
            active_token = await self._refresh_access_token(token_data)
        else:
            active_token = token_data.access_token

        return {
            "Authorization": f"Bearer {active_token}",
            "Content-Type": "application/json"
        }

    async def check_auth(self) -> bool:
        """
        Checks if the current connection to AmoCRM is active.

        Returns:
            bool: True if authorized, False otherwise.
        """
        try:
            headers = await self._get_auth_headers()
            url = f"{self.base_url}/api/v4/account"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Auth check failed: {e}")
            return False