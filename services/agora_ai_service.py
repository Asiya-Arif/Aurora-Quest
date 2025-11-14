"""Minimal, mocked Agora AI adapter used for local development and tests.

This module exposes an `agora_ai_service` instance with async methods the
application expects: `chat`, `start_language_session`,
`generate_language_exercise`, and `get_pronunciation_feedback`.

The implementations are intentionally simple and deterministic so the app
can run without real Agora credentials during development.
"""

from typing import Optional, Dict, Any


class AgoraAIService:
    async def chat(self, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        # Return a simple echoed reply so chat endpoints can function.
        return {
            "status": "success",
            "reply": f"(Agora mock) Echo: {query}",
            "session_id": session_id or "anon",
        }

    async def start_language_session(self, language: str, user_id: str, proficiency_level: str = "beginner") -> Dict[str, Any]:
        return {
            "status": "success",
            "ai_tutor_name": "Ava",
            "initial_prompt": f"Hello! Let's practice {language} together.",
            "voice_enabled": False,
            "real_time_feedback": False,
        }

    async def generate_language_exercise(self, language: str, proficiency_level: str, topic: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "exercise": {
                "question": f"Translate to {language}: 'Good morning' (topic={topic})",
                "expected_answer": "(example) Buen día",
            },
        }

    async def get_pronunciation_feedback(self, user_audio_url: str, phrase: str, language: str, session_id: str) -> Dict[str, Any]:
        # Simple deterministic feedback for development.
        return {
            "status": "success",
            "score": 0.8,
            "comments": "Clear pronunciation with minor vowel differences.",
        }


# Module-level singleton used by the rest of the app: `from services.agora_ai_service import agora_ai_service`
agora_ai_service = AgoraAIService()