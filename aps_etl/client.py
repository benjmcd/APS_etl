"""APS API client for search requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from aps_etl.serialization import serialize_query


class APSClientError(RuntimeError):
    """APS client error."""


class APSUnauthorizedError(APSClientError):
    """Raised when APS returns 401/403."""


@dataclass
class APSClient:
    """Client for APS API access."""

    base_url: str
    api_key: str
    timeout_s: float
    retry_max_attempts: int
    retry_min_wait_s: float
    retry_max_wait_s: float

    def _headers(self) -> dict[str, str]:
        return {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise APSUnauthorizedError("APS API authentication failed.")
        if response.status_code in {429} or response.status_code >= 500:
            response.raise_for_status()
        if response.status_code >= 400:
            raise APSClientError(f"APS request failed with status {response.status_code}.")

    def _request(self, method: str, url: str, json: dict[str, Any]) -> httpx.Response:
        with httpx.Client(timeout=self.timeout_s, headers=self._headers()) as client:
            response = client.request(method, url, json=json)
        self._raise_for_status(response)
        return response

    def search(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a search request to APS."""

        url = f"{self.base_url}/aps/api/search"
        retrying = Retrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            stop=stop_after_attempt(self.retry_max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_min_wait_s,
                max=self.retry_max_wait_s,
            ),
            reraise=True,
        )
        for attempt in retrying:
            with attempt:
                response = self._request("POST", url, json=payload)
                return response.json()
        raise APSClientError("Retry loop failed unexpectedly.")

    def probe_wire_format(self, query: Any) -> str:
        """Probe APS to determine wire-format support for the query."""

        payload_a = serialize_query(query, wire_format="A", skip=0)
        try:
            self.search(payload_a)
            return "A"
        except APSClientError:
            payload_b = serialize_query(query, wire_format="B", skip=0)
            self.search(payload_b)
            return "B"
