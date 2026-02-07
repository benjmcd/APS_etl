from __future__ import annotations

import json
from typing import Any

import vcr

from aps_etl.canonical import canon_json_bytes


def normalized_body_matcher(request1: Any, request2: Any) -> bool:
    body1 = _normalize_body(request1.body)
    body2 = _normalize_body(request2.body)
    return body1 == body2


def _normalize_body(body: Any) -> bytes:
    if body is None:
        return b""
    if isinstance(body, bytes):
        raw = body
    elif isinstance(body, str):
        raw = body.encode("utf-8")
    elif hasattr(body, "__iter__"):
        raw = b"".join(body)
    else:
        raw = str(body).encode("utf-8")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return raw
    return canon_json_bytes(parsed)


def build_vcr(record_mode: str) -> vcr.VCR:
    recorder = vcr.VCR(
        record_mode=record_mode,
        filter_headers=["Ocp-Apim-Subscription-Key"],
        match_on=["method", "uri", "normalized_body"],
    )
    recorder.register_matcher("normalized_body", normalized_body_matcher)
    return recorder
