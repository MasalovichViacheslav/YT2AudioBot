import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.main import health


@pytest.fixture
async def client():
    app = web.Application()
    app.router.add_get("/health", health)
    async with TestClient(TestServer(app)) as c:
        yield c


async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status == 200


async def test_health_returns_ok(client):
    response = await client.get("/health")
    text = await response.text()
    assert text == "OK"
