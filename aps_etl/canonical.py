"""Canonical JSON and hashing utilities for APS ETL."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canon_json_bytes(payload: Any) -> bytes:
    """Return canonical JSON bytes for deterministic hashing."""

    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return normalized.encode("utf-8")


def sha256_hex(payload: Any) -> str:
    """Return the SHA256 hex digest for canonical JSON payloads."""

    return hashlib.sha256(canon_json_bytes(payload)).hexdigest()


def request_fingerprint(method: str, url: str, wire_format: str, body: Any) -> str:
    """Compute the request fingerprint for APS search requests."""

    fingerprint_payload = {
        "method": method,
        "url": url,
        "wire_format": wire_format,
        "body": body,
    }
    return sha256_hex(fingerprint_payload)
