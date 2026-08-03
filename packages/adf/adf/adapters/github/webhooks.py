"""GitHub webhook signature verification (HMAC SHA-256)."""

from __future__ import annotations

import hashlib
import hmac


class GitHubWebhookVerifier:
    """Verifies the ``X-Hub-Signature-256`` header against the shared secret."""

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def verify(self, payload: bytes, signature: str | None) -> bool:
        if not signature:
            return False
        if not signature.startswith("sha256="):
            return False
        expected = (
            "sha256="
            + hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        )
        # Constant-time comparison to avoid timing attacks.
        return hmac.compare_digest(expected, signature)

    def sign(self, payload: bytes) -> str:
        """Helper used by tests to produce a valid signature."""
        return "sha256=" + hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
