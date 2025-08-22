"""Integration tests for the health API endpoint."""

from fastapi import status
from fastapi.testclient import TestClient


class TestHealthAPI:
    """Test suite for the health API endpoint."""

    def test_health_check(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test the health check endpoint."""
        response = test_client.get("/v1/health", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "OK"

    def test_health_check_without_headers(self, test_client: TestClient) -> None:
        """Test the health check endpoint without workspace headers."""
        response = test_client.get("/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "OK"

    def test_health_check_response_structure(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test that the health check response has the correct structure."""
        response = test_client.get("/v1/health", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check that only the expected fields are present
        assert set(data.keys()) == {"status"}
        assert isinstance(data["status"], str)
        assert data["status"] == "OK"

    def test_health_check_content_type(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test that the health check response has the correct content type."""
        response = test_client.get("/v1/health", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
