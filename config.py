try:
    from config_quest import settings
except Exception:
    from .config_quest import settings

__all__ = ["settings"]
