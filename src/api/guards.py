"""Abuse/cost controls (docs/11 s1). In-memory only; client ids are salted hashes, never stored or logged raw."""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Callable


def client_key(ip: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}|{ip}".encode()).hexdigest()[:16]


@dataclass
class RateLimiter:
    per_minute: int = 10
    per_day: int = 100
    clock: Callable[[], float] = time.monotonic
    _bucket: dict[str, tuple[float, float]] = field(default_factory=dict)   # key -> (tokens, last_ts)
    _day: dict[str, tuple[float, int]] = field(default_factory=dict)        # key -> (window_start, count)

    def allow(self, key: str) -> bool:
        now = self.clock()
        start, n = self._day.get(key, (now, 0))
        if now - start >= 86400:
            start, n = now, 0
        if n >= self.per_day:
            return False
        tokens, last = self._bucket.get(key, (float(self.per_minute), now))
        tokens = min(float(self.per_minute), tokens + (now - last) * self.per_minute / 60.0)
        if tokens < 1.0:
            self._bucket[key] = (tokens, now)
            return False
        self._bucket[key] = (tokens - 1.0, now)
        self._day[key] = (start, n + 1)
        return True


@dataclass
class Budget:
    daily_usd: float
    usd_per_mtok_in: float = 1.0
    usd_per_mtok_out: float = 5.0
    spent: float = 0.0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.spent += input_tokens * self.usd_per_mtok_in / 1e6 + output_tokens * self.usd_per_mtok_out / 1e6

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.daily_usd

    @property
    def fraction(self) -> float:
        return self.spent / self.daily_usd if self.daily_usd else 1.0


@dataclass
class Settings:
    enabled: bool = True
    max_question_chars: int = 500
    max_k: int = 10
    per_minute: int = 10
    per_day: int = 100
    daily_budget_usd: float = 1.0
    salt: str = "dev-salt-change-me"

    @classmethod
    def from_env(cls) -> "Settings":
        e = os.environ.get
        return cls(enabled=e("DEMO_ENABLED", "true").lower() != "false", per_minute=int(e("RATE_PER_MIN", 10)),
                   per_day=int(e("RATE_PER_DAY", 100)), daily_budget_usd=float(e("DEMO_DAILY_BUDGET_USD", 1.0)),
                   salt=e("CLIENT_SALT", cls.salt))
