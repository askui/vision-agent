import pytest


@pytest.fixture(autouse=True)
def set_env_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASKUI_WORKSPACE_ID", "test_workspace_id")
