"""Small gamification shim used for awarding XP in development.

Keeps the production interface but is intentionally simple.
"""

from typing import Any


class GamificationService:
	def award_xp(self, db: Any, user_id: Any, xp_amount: Any, action_type: str = "") -> int:
		# In development just return the requested xp_amount (or a default).
		# Accept `user_id` as Any because SQLAlchemy model attributes may be
		# Column objects at static analysis time.
		try:
			return int(xp_amount) if xp_amount else 5
		except Exception:
			return 5


__all__ = ["GamificationService"]
