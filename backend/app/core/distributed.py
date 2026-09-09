"""Small infrastructure adapters used by the distributed LearnSync features.

All adapters degrade to process-local behavior when Redis is not configured.  This
keeps local development and the existing unit-test suite usable, while production
deployments can point every API/worker process at the same Redis instance.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class DistributedInfrastructure:
    def __init__(self) -> None:
        self._redis = None
        self._memory_cache: dict[str, tuple[float, Any]] = {}
        self._memory_locks: dict[str, threading.Lock] = {}
        self._memory_rate: dict[str, tuple[float, float]] = {}
        self._guard = threading.Lock()

    @property
    def redis(self):
        if self._redis is None and settings.REDIS_URL:
            try:
                import redis

                client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception as exc:
                logger.warning("Redis unavailable; using local fallback: %s", exc)
                self._redis = False
        return self._redis if self._redis is not False else None

    @staticmethod
    def cache_key(namespace: str, *parts: Any) -> str:
        raw = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{settings.REDIS_KEY_PREFIX}:{namespace}:{digest}"

    def cache_get(self, key: str) -> Optional[Any]:
        client = self.redis
        if client:
            value = client.get(key)
            return json.loads(value) if value else None
        with self._guard:
            item = self._memory_cache.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at <= time.monotonic():
                self._memory_cache.pop(key, None)
                return None
            return value

    def cache_set(self, key: str, value: Any, ttl_seconds: int) -> None:
        client = self.redis
        encoded = json.dumps(value, default=str)
        if client:
            client.setex(key, ttl_seconds, encoded)
            return
        with self._guard:
            self._memory_cache[key] = (time.monotonic() + ttl_seconds, json.loads(encoded))

    @contextmanager
    def lock(self, name: str, timeout_seconds: Optional[int] = None) -> Iterator[bool]:
        """Acquire a Redis lock with an ownership token, or a local lock offline."""
        client = self.redis
        timeout = timeout_seconds if timeout_seconds is not None else settings.DISTRIBUTED_LOCK_TIMEOUT_SECONDS
        key = f"{settings.REDIS_KEY_PREFIX}:lock:{name}"
        token = str(uuid.uuid4())
        acquired = False
        if client:
            acquired = bool(client.set(key, token, nx=True, ex=timeout))
        else:
            with self._guard:
                lock = self._memory_locks.setdefault(key, threading.Lock())
            acquired = lock.acquire(timeout=timeout)

        try:
            yield acquired
        finally:
            if not acquired:
                return
            if client:
                release = (
                    "if redis.call('get', KEYS[1]) == ARGV[1] then "
                    "return redis.call('del', KEYS[1]) else return 0 end"
                )
                client.eval(release, 1, key, token)
            else:
                self._memory_locks[key].release()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        """Fixed-window distributed limiter; returns False when the quota is spent."""
        client = self.redis
        redis_key = f"{settings.REDIS_KEY_PREFIX}:rate:{key}"
        if client:
            count = client.incr(redis_key)
            if count == 1:
                client.expire(redis_key, window_seconds)
            return count <= limit

        now = time.monotonic()
        with self._guard:
            started, count = self._memory_rate.get(key, (now, 0.0))
            if now - started >= window_seconds:
                started, count = now, 0.0
            count += 1
            self._memory_rate[key] = (started, count)
            return count <= limit

    check_rate_limit = allow


distributed = DistributedInfrastructure()
