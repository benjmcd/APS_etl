from aps_etl.canonical import canon_json_bytes, request_fingerprint, sha256_hex


def test_canon_json_bytes_is_deterministic() -> None:
    payload = {"b": 2, "a": 1}

    assert canon_json_bytes(payload) == b'{"a":1,"b":2}'


def test_sha256_hex_matches_canonical_payload() -> None:
    payload = {"a": 1}

    assert sha256_hex(payload) == (
        "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )


def test_request_fingerprint_is_stable() -> None:
    fingerprint = request_fingerprint(
        method="POST",
        url="https://adams-api.nrc.gov/aps/api/search",
        wire_format="A",
        body={"q": "test", "skip": 0},
    )

    assert fingerprint == ("4be5848693d3dfc379a92a0b88919c91a4fb5d25e47668d08cecf90caa875ffa")
