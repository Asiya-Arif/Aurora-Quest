import os
import time
import secrets
import hashlib
from typing import Dict, Any

class AgoraService:
    """
    Minimal Agora helper used by the language/chat routes.

    - generate_channel_name(user_id, language): returns a deterministic channel name for a user+language
    - generate_token(channel_name, uid): returns a dict with a token placeholder and app_id

    NOTE:
    - Replace the token generation below with the official Agora RTC token
      generation logic when you integrate with the real Agora SDK and set
      AGORA_APP_ID / AGORA_APP_CERTIFICATE environment variables.
    - Keep your Agora credentials on the server (do not expose them to the frontend).
    """

    def __init__(self) -> None:
        # Read env variables (optional). Use these in your real token creation.
        self.app_id = os.getenv("AGORA_APP_ID", "your-agora-app-id")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE", "")
        # Fallback key for dev-only placeholder tokens
        self._dev_key = os.getenv("AGORA_DEV_KEY", "dev-placeholder-key")

    def generate_channel_name(self, user_id: int | str, language: str) -> str:
        """
        Create a deterministic channel name for a given user and language.
        Example: "aurora_user-42_lang-en_20251114"
        """
        sanitized_lang = (language or "global").lower().replace(" ", "-")
        uid_part = str(user_id or "anon")
        date_part = time.strftime("%Y%m%d")
        channel = f"aurora_user-{uid_part}_lang-{sanitized_lang}_{date_part}"
        # Keep channel length reasonable
        return channel[:80]

    def generate_token(self, channel_name: str, uid: int | str) -> Dict[str, Any]:
        """
        Generate a simple placeholder token + metadata for the frontend.

        Replace this with the official Agora token generation (using
        AGORA_APP_ID and AGORA_APP_CERTIFICATE) in production.

        Returns:
            { "token": "<token-string>", "app_id": "<app_id>", "uid": "<uid>" }
        """
        # Simple HMAC-ish placeholder (NOT SECURE) so token looks unique each call
        seed = f"{self._dev_key}|{channel_name}|{uid}|{time.time()}"
        token = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return {"token": token, "app_id": self.app_id, "uid": uid}