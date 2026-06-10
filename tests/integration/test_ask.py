import pytest

pytestmark = pytest.mark.integration


class TestAskEndpoint:
    async def test_ask_returns_200_with_valid_key(self, async_client, test_api_key):
        raw_key, _ = test_api_key

        response = await async_client.post(
            "/api/v1/ask",
            json={"question": "What is in the document?"},
            headers={"x-api-key": raw_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "This is a mocked agent response."

    async def test_ask_returns_403_without_key(self, async_client):
        response = await async_client.post(
            "/api/v1/ask",
            json={"question": "Anything"},
        )

        assert response.status_code == 422  # missing required header

    async def test_ask_returns_403_with_invalid_key(self, async_client):
        response = await async_client.post(
            "/api/v1/ask",
            json={"question": "Anything"},
            headers={"x-api-key": "totally-bogus-key"},
        )

        assert response.status_code == 403

    async def test_ask_returns_422_without_body(self, async_client, test_api_key):
        raw_key, _ = test_api_key

        response = await async_client.post(
            "/api/v1/ask",
            headers={"x-api-key": raw_key},
        )

        assert response.status_code == 422
