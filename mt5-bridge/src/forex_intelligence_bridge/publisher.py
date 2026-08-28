"""HTTP publisher for replaying durable MT5 envelopes to the backend."""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .spool import EnvelopeSpool


class PublishDisposition(str, Enum):
    ACK = "ACK"
    RETRY = "RETRY"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"


@dataclass(frozen=True)
class PublishResult:
    disposition: PublishDisposition
    status_code: int | None = None
    detail: str = ""


class BackendPublisher:
    """Publish one envelope and classify the downstream response."""

    def __init__(self, url: str, api_key: str, timeout_seconds: float = 5.0) -> None:
        if not url.startswith(("http://", "https://")):
            raise ValueError("backend URL must use http or https")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if len(api_key.encode("utf-8")) < 32:
            raise ValueError("backend API key must be at least 32 bytes")
        self._url = url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def publish(self, envelope: dict[str, Any]) -> PublishResult:
        body = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        request = urllib.request.Request(
            self._url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "X-Bridge-Api-Key": self._api_key},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                status = int(response.status)
                if 200 <= status < 300:
                    return PublishResult(PublishDisposition.ACK, status)
                if status == 429 or 500 <= status < 600:
                    return PublishResult(PublishDisposition.RETRY, status)
                return PublishResult(PublishDisposition.PERMANENT_FAILURE, status)
        except urllib.error.HTTPError as error:
            status = int(error.code)
            if status == 429 or 500 <= status < 600:
                return PublishResult(PublishDisposition.RETRY, status, str(error.reason))
            return PublishResult(PublishDisposition.PERMANENT_FAILURE, status, str(error.reason))
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            return PublishResult(PublishDisposition.RETRY, None, str(error))


class SpoolReplayer:
    """Replay the oldest pending envelope using ACK-driven removal semantics."""

    def __init__(
        self,
        spool: EnvelopeSpool,
        publisher: BackendPublisher,
        *,
        max_attempts: int = 5,
        base_delay_seconds: float = 0.25,
        max_delay_seconds: float = 5.0,
        sleep: Callable[[float], None] = time.sleep,
        random_value: Callable[[], float] = random.random,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if base_delay_seconds < 0 or max_delay_seconds < base_delay_seconds:
            raise ValueError("invalid retry delay configuration")
        self._spool = spool
        self._publisher = publisher
        self._max_attempts = max_attempts
        self._base_delay_seconds = base_delay_seconds
        self._max_delay_seconds = max_delay_seconds
        self._sleep = sleep
        self._random_value = random_value

    def replay_one(self) -> PublishResult | None:
        pending = self._spool.peek()
        if pending is None:
            return None
        path, envelope = pending

        for attempt in range(self._max_attempts):
            result = self._publisher.publish(envelope)
            if result.disposition is PublishDisposition.ACK:
                self._spool.acknowledge(path)
                return result
            if result.disposition is PublishDisposition.PERMANENT_FAILURE:
                detail = f"HTTP {result.status_code}: {result.detail}" if result.status_code else result.detail
                self._spool.quarantine(path, "permanent_backend_rejection", detail)
                return result
            if attempt + 1 < self._max_attempts:
                self._sleep(self._retry_delay(attempt))
        return result

    def _retry_delay(self, attempt: int) -> float:
        exponential = min(self._max_delay_seconds, self._base_delay_seconds * (2**attempt))
        # Full jitter keeps simultaneous bridge instances from retrying in lockstep.
        return exponential * self._random_value()
