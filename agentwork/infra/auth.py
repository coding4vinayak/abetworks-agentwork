"""Token-based authentication system using HMAC signatures."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
from typing import Any, Dict, Optional, Set

from agentwork.core.exceptions import AgentError

VALID_ROLES = {"admin", "agent", "readonly"}


class InvalidTokenError(AgentError):
    """Raised when a token is invalid, expired, or revoked."""

    def __init__(self, message: str = "Invalid token", details: Optional[Any] = None) -> None:
        super().__init__(message, details)


class TokenAuth:
    """Token-based authentication using HMAC+SHA256 signatures.

    Token format: base64(json_payload) + "." + hmac_signature

    Args:
        secret_key: Secret key used for signing tokens.
    """

    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key.encode("utf-8")
        self._revoked: Set[str] = set()
        self._lock = threading.Lock()

    def _sign(self, payload_b64: str) -> str:
        """Create HMAC-SHA256 signature for a base64 payload."""
        signature = hmac.new(
            self._secret_key,
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def generate_token(
        self,
        subject: str,
        role: str = "agent",
        expires_in: int = 3600,
        claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a signed token.

        Args:
            subject: The subject (user/agent ID) the token is for.
            role: Role for the token (admin, agent, readonly).
            expires_in: Token lifetime in seconds.
            claims: Additional custom claims to include.

        Returns:
            Signed token string.

        Raises:
            InvalidTokenError: If role is not valid.
        """
        if role not in VALID_ROLES:
            raise InvalidTokenError(f"Invalid role: {role}. Must be one of {VALID_ROLES}")

        payload = {
            "sub": subject,
            "role": role,
            "iat": time.time(),
            "exp": time.time() + expires_in,
        }

        if claims:
            payload["claims"] = claims

        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")
        signature = self._sign(payload_b64)

        return f"{payload_b64}.{signature}"

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a token and return its payload.

        Args:
            token: The token string to validate.

        Returns:
            Dict with subject, role, claims, and timing info.

        Raises:
            InvalidTokenError: If token is invalid, expired, or revoked.
        """
        if not token or "." not in token:
            raise InvalidTokenError("Malformed token")

        parts = token.split(".", 1)
        if len(parts) != 2:
            raise InvalidTokenError("Malformed token")

        payload_b64, signature = parts

        # Verify signature
        expected_signature = self._sign(payload_b64)
        if not hmac.compare_digest(signature, expected_signature):
            raise InvalidTokenError("Invalid signature")

        # Check revocation
        if self.is_revoked(token):
            raise InvalidTokenError("Token has been revoked")

        # Decode payload
        try:
            payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
            payload = json.loads(payload_json)
        except (ValueError, json.JSONDecodeError) as e:
            raise InvalidTokenError(f"Failed to decode token payload: {e}")

        # Check expiration
        if time.time() > payload.get("exp", 0):
            raise InvalidTokenError("Token has expired")

        return {
            "subject": payload["sub"],
            "role": payload["role"],
            "claims": payload.get("claims", {}),
            "issued_at": payload["iat"],
            "expires_at": payload["exp"],
        }

    def revoke_token(self, token: str) -> None:
        """Add a token to the revocation set.

        Args:
            token: The token to revoke.
        """
        with self._lock:
            self._revoked.add(token)

    def is_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.

        Args:
            token: The token to check.

        Returns:
            True if the token is revoked.
        """
        with self._lock:
            return token in self._revoked
