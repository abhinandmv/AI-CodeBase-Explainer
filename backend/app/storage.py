import json
from typing import Any, Dict, Optional
from redis import Redis
from .config import settings
from .utils import safe_mkdir


class Store:
    """
    Redis-backed store:
      - analysis:<id> -> JSON {status, progress, result, error, cached}
      - cache:<repo_hash> -> analysis_id (TTL)
    """

    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        safe_mkdir(settings.OUTPUT_DIR)
        safe_mkdir(settings.CLONE_DIR)

    def set_analysis_state(self, analysis_id: str, state: Dict[str, Any], ttl: int | None = None) -> None:
        key = f"analysis:{analysis_id}"
        self.redis.set(key, json.dumps(state), ex=ttl or settings.ANALYSIS_TTL_SECONDS)

    def get_analysis_state(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        key = f"analysis:{analysis_id}"
        raw = self.redis.get(key)
        return json.loads(raw) if raw else None

    def update(
        self,
        analysis_id: str,
        *,
        status: str,
        progress: int,
        result: Any = None,
        error: Optional[str] = None,
        cached: bool = False,
        ttl: int | None = None,
    ) -> None:
        state = self.get_analysis_state(analysis_id) or {}
        state.update(
            {
                "status": status,
                "progress": int(progress),
                "result": result,
                "error": error,
                "cached": bool(cached),
            }
        )
        self.set_analysis_state(analysis_id, state, ttl=ttl)

    def cache_set(self, repo_hash: str, analysis_id: str, ttl: int | None = None) -> None:
        self.redis.set(f"cache:{repo_hash}", analysis_id, ex=ttl or settings.CACHE_TTL_SECONDS)

    def cache_get(self, repo_hash: str) -> Optional[str]:
        return self.redis.get(f"cache:{repo_hash}")


store = Store()