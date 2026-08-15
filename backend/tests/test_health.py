from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.database.database import get_db
from app.main import app


async def _override_get_db():
    session = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = 1
    session.execute.return_value = result
    yield session


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["db"] == "ok"
