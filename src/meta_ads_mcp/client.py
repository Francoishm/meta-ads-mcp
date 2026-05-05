"""Thin async wrapper around the Meta Marketing Graph API."""

from __future__ import annotations

import os
from typing import Any

import httpx


class MetaAPIError(RuntimeError):
    """Raised when Meta returns an error payload."""

    def __init__(self, status: int, message: str, payload: dict | None = None):
        super().__init__(f"Meta API {status}: {message}")
        self.status = status
        self.message = message
        self.payload = payload or {}


class MetaAdsClient:
    """Async client for Meta Marketing API.

    Reads credentials from env at instantiation time.
    Methods return parsed JSON dicts (raise MetaAPIError on non-2xx).
    """

    def __init__(
        self,
        access_token: str | None = None,
        ad_account_id: str | None = None,
        api_version: str | None = None,
        timeout: float = 30.0,
    ):
        self.access_token = access_token or os.environ.get("META_ACCESS_TOKEN")
        if not self.access_token:
            raise RuntimeError("META_ACCESS_TOKEN is required (env var or constructor arg)")
        self.ad_account_id = ad_account_id or os.environ.get("META_AD_ACCOUNT_ID", "")
        self.api_version = api_version or os.environ.get("META_API_VERSION", "v19.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.timeout = timeout
        self.read_only = os.environ.get("META_READ_ONLY", "false").lower() in ("1", "true", "yes")

    # ------------------------------------------------------------------
    # Low-level
    # ------------------------------------------------------------------

    async def _request(
        self, method: str, path: str, *, params: dict | None = None, data: dict | None = None
    ) -> dict[str, Any]:
        if method.upper() != "GET" and self.read_only:
            raise MetaAPIError(403, "Server is in read-only mode (META_READ_ONLY=true)")

        url = f"{self.base_url}/{path.lstrip('/')}"
        params = {**(params or {}), "access_token": self.access_token}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.request(method, url, params=params, data=data)

        if resp.status_code >= 400:
            try:
                payload = resp.json()
                error = payload.get("error", {})
                msg = error.get("message", resp.text[:200])
                raise MetaAPIError(resp.status_code, msg, error)
            except (ValueError, KeyError):
                raise MetaAPIError(resp.status_code, resp.text[:200])

        return resp.json()

    async def get(self, path: str, **params) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, **data) -> dict:
        return await self._request("POST", path, data=data)

    async def delete(self, path: str, **params) -> dict:
        return await self._request("DELETE", path, params=params)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _account(self, account_id: str | None = None) -> str:
        """Resolve ad_account_id from arg or env. Ensures 'act_' prefix."""
        acct = account_id or self.ad_account_id
        if not acct:
            raise RuntimeError("ad_account_id required (arg or META_AD_ACCOUNT_ID env)")
        return acct if acct.startswith("act_") else f"act_{acct}"

    async def paginated(self, path: str, **params) -> list[dict]:
        """Walk a paginated edge until exhausted."""
        items: list[dict] = []
        next_url = None
        first = True
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while True:
                if first:
                    p = {**params, "access_token": self.access_token, "limit": params.get("limit", 100)}
                    resp = await client.get(f"{self.base_url}/{path.lstrip('/')}", params=p)
                    first = False
                else:
                    if not next_url:
                        break
                    resp = await client.get(next_url)

                if resp.status_code >= 400:
                    try:
                        payload = resp.json()
                        msg = payload.get("error", {}).get("message", resp.text[:200])
                        raise MetaAPIError(resp.status_code, msg, payload.get("error"))
                    except ValueError:
                        raise MetaAPIError(resp.status_code, resp.text[:200])

                body = resp.json()
                items.extend(body.get("data", []))
                next_url = body.get("paging", {}).get("next")
                if not next_url:
                    break
        return items
