from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    LyzrAuthenticationError,
    LyzrRateLimitError,
    LyzrResponseError,
    LyzrUnavailableError,
)

logger = logging.getLogger(__name__)

# Never log this header key's value
_REDACTED = "<redacted>"


def normalize_lyzr_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Parse the Lyzr API response into a plain dict regardless of encoding.

    Supports:
      - raw already contains structured fields (no 'response' wrapper)
      - raw['response'] is a dict
      - raw['response'] is a JSON string
      - raw['response'] is a markdown-fenced JSON string
    """
    if "response" not in raw:
        # Root-level structured response
        if isinstance(raw, dict) and ("success" in raw or "requirements" in raw or "operation" in raw):
            return raw
        raise LyzrResponseError("Lyzr response missing 'response' field")

    payload = raw["response"]

    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str):
        text = payload.strip()
        # Strip markdown fences: ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text.strip())
        text = text.strip()
        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LyzrResponseError(
                f"Lyzr response could not be parsed as JSON: {exc}"
            ) from exc
        if not isinstance(result, dict):
            raise LyzrResponseError("Lyzr parsed response is not a dictionary")
        return result

    raise LyzrResponseError(
        f"Lyzr response field has unexpected type: {type(payload).__name__}"
    )


class LyzrService:
    """Async client for Lyzr Studio Agent inference."""

    async def chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ) -> dict[str, Any]:
        """Send a message to the Lyzr agent and return the normalized response dict.

        Raises:
            LyzrUnavailableError   – timeout, network error, 429, 5xx
            LyzrAuthenticationError – 401 / 403
            LyzrResponseError      – malformed / unparseable response
        """
        if not settings.LYZR_ENABLED:
            raise LyzrUnavailableError("Lyzr integration is disabled (LYZR_ENABLED=false)")

        if not settings.LYZR_API_KEY:
            raise LyzrAuthenticationError(
                "LYZR_API_KEY is not configured — set it in backend/.env"
            )

        url = settings.lyzr_chat_url
        body = {
            "user_id": user_id,
            "agent_id": settings.LYZR_AGENT_ID,
            "session_id": session_id,
            "message": message,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": settings.LYZR_API_KEY,
        }

        logger.info(
            "Lyzr request | session=%s user=%s agent=%s",
            session_id,
            user_id,
            settings.LYZR_AGENT_ID,
        )

        try:
            async with httpx.AsyncClient(timeout=settings.LYZR_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise LyzrUnavailableError(
                f"Lyzr request timed out after {settings.LYZR_TIMEOUT_SECONDS}s"
            ) from exc
        except httpx.ConnectError as exc:
            raise LyzrUnavailableError(
                "Could not connect to Lyzr service"
            ) from exc
        except httpx.RequestError as exc:
            raise LyzrUnavailableError(
                f"Lyzr network error: {type(exc).__name__}"
            ) from exc

        if response.status_code in (401, 403):
            raise LyzrAuthenticationError(
                f"Lyzr returned HTTP {response.status_code} — verify LYZR_API_KEY"
            )
        if response.status_code == 429:
            raise LyzrRateLimitError("Lyzr rate limit exceeded (HTTP 429)")
        if response.status_code >= 500:
            raise LyzrUnavailableError(
                f"Lyzr server error HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise LyzrResponseError(
                f"Lyzr returned HTTP {response.status_code}"
            )

        try:
            raw = response.json()
        except Exception as exc:
            raise LyzrResponseError(
                "Lyzr response body is not valid JSON"
            ) from exc

        result = normalize_lyzr_response(raw)
        logger.info(
            "Lyzr response | session=%s success=%s operation=%s",
            session_id,
            result.get("success"),
            result.get("operation"),
        )
        return result


# Module-level singleton
lyzr_service = LyzrService()
