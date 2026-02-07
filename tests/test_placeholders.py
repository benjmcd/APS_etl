import pytest


@pytest.mark.integration
def test_integration_placeholder() -> None:
    pytest.skip("Integration tests not implemented yet.")


@pytest.mark.smoke_offline
def test_smoke_offline_placeholder() -> None:
    pytest.skip("Offline smoke tests not implemented yet.")


@pytest.mark.smoke_live
def test_smoke_live_placeholder() -> None:
    pytest.skip("Live smoke tests not implemented yet.")
