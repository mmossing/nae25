"""
Strava authentication helper for NAE25 data scripts.

Reads/writes the shared token file at ~/.strava_mcp_token.json (same file used
by the Strava MCP server), automatically refreshing the access token when it
expires. STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be in the environment
or a .env file; no STRAVA_REFRESH_TOKEN is needed.

Usage:
    from scripts.strava_auth import strava_get

    async def main():
        athlete = await strava_get("/athlete")
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TOKEN_FILE    = Path(os.getenv("STRAVA_TOKEN_FILE", "~/.strava_mcp_token.json")).expanduser()

STRAVA_BASE = "https://www.strava.com/api/v3"
TOKEN_URL   = "https://www.strava.com/oauth/token"


def load_token() -> dict:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return {}


def save_token(token: dict) -> None:
    TOKEN_FILE.write_text(json.dumps(token, indent=2))
    TOKEN_FILE.chmod(0o600)


async def get_access_token() -> str:
    """Return a valid access token, refreshing via the shared token file if needed."""
    token = load_token()
    if not token:
        raise RuntimeError(
            f"No token found at {TOKEN_FILE}.\n"
            "Run the Strava MCP server's OAuth flow first:\n"
            "  cd ~/projects/experiments/strava_routes\n"
            "  python server.py --auth"
        )
    if token.get("expires_at", 0) < time.time() + 60:
        if not CLIENT_ID or not CLIENT_SECRET:
            raise RuntimeError(
                "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env to refresh the token."
            )
        async with httpx.AsyncClient() as client:
            r = await client.post(TOKEN_URL, data={
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type":    "refresh_token",
                "refresh_token": token["refresh_token"],
            })
            r.raise_for_status()
            token.update(r.json())
            save_token(token)
    return token["access_token"]


async def strava_get(path: str, params: dict | None = None) -> Any:
    """Make an authenticated GET request to the Strava API."""
    access_token = await get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{STRAVA_BASE}{path}",
            headers=headers,
            params=params or {},
        )
        r.raise_for_status()
        return r.json()


def strava_get_sync(path: str, params: dict | None = None) -> Any:
    """Synchronous wrapper around strava_get for use in non-async scripts."""
    return asyncio.run(strava_get(path, params))
