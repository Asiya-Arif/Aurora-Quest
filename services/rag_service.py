"""Minimal RAG service shim for local development.

Provides a `RAGService` class with an `async get_response` method that returns
simple deterministic responses so other modules can call it without the
original langchain dependency.
"""

from typing import Optional


class RAGService:
	async def get_response(self, query: str, session_id: Optional[int] = None) -> str:
		# Simple echo-style response for development.
		return f"(RAG mock) Answer to: {query}"

	async def generate_quiz(self, session_id: int, num_questions: int = 5):
		# Return a list of simple quiz question dicts matching the shape used by quiz.py
		questions = []
		for i in range(1, num_questions + 1):
			questions.append({
				"question": f"Sample question {i} for session {session_id}",
				"option_a": "Option A",
				"option_b": "Option B",
				"option_c": "Option C",
				"option_d": "Option D",
				"correct": "Option A",
			})
		return questions


__all__ = ["RAGService"]
