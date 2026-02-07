"""APS client placeholder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class APSClient:
    """Client for APS API access.

    This is a placeholder implementation to be extended with real HTTP calls.
    """

    base_url: str
    api_key: str | None = None

    def fetch(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Fetch data from APS.

        Args:
            endpoint: Endpoint path.
            params: Query parameters.

        Raises:
            NotImplementedError: Until APS API integration is defined.
        """

        raise NotImplementedError("APS client integration is not implemented yet.")
