import hashlib
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("brandpulse.cache")


class MemoryCache:
    """
    Lightweight, high-performance in-memory cache with TTL expiration.
    Eliminates redundant external LLM and translation API calls to strictly control costs.
    """
    def __init__(self, default_ttl: int = 3600, max_size: int = 5000):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v.get("expires_at", 0)]
        for k in expired:
            self._store.pop(k, None)

    def get(self, key: str) -> Optional[Any]:
        hashed = self._hash_key(key)
        item = self._store.get(hashed)
        if not item:
            return None
        if time.time() > item["expires_at"]:
            self._store.pop(hashed, None)
            return None
        return item["val"]

    def set(self, key: str, val: Any, ttl: Optional[int] = None) -> None:
        if len(self._store) >= self.max_size:
            self._cleanup_expired()
            if len(self._store) >= self.max_size:
                # Evict oldest 20% of entries based on expiration time
                sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k]["expires_at"])
                for k in sorted_keys[:max(1, len(sorted_keys) // 5)]:
                    self._store.pop(k, None)
        hashed = self._hash_key(key)
        expires_at = time.time() + (ttl or self.default_ttl)
        self._store[hashed] = {"val": val, "expires_at": expires_at}

    def clear(self) -> None:
        self._store.clear()


# Global cache singletons
llm_cache = MemoryCache(default_ttl=7200) # 2 hours TTL for LLM responses
translation_cache = MemoryCache(default_ttl=86400) # 24 hours TTL for translations


def get_cached_translation(text: str, target_lang: str) -> Optional[str]:
    """Retrieves cached translation if available."""
    cache_key = f"trans:{target_lang}:{text.strip()}"
    return translation_cache.get(cache_key)


def set_cached_translation(text: str, target_lang: str, translated_text: str) -> None:
    """Caches translation result."""
    cache_key = f"trans:{target_lang}:{text.strip()}"
    translation_cache.set(cache_key, translated_text)


def get_cached_llm_response(prompt: str, context_hash: str = "") -> Optional[str]:
    """Retrieves cached LLM response for identical prompt & context."""
    cache_key = f"llm:{context_hash}:{prompt.strip()}"
    return llm_cache.get(cache_key)


def set_cached_llm_response(prompt: str, response: str, context_hash: str = "") -> None:
    """Caches LLM response to save tokens and inference costs."""
    cache_key = f"llm:{context_hash}:{prompt.strip()}"
    llm_cache.set(cache_key, response)
