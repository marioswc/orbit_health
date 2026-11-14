import pytest
from fastapi.testclient import TestClient

from app import config, main


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "api.db"))
    with TestClient(main.app, raise_server_exceptions=True) as c:
        yield c
