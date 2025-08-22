"""Integration tests for the MCP configs API endpoints."""

import tempfile
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

from askui.chat.api.mcp_configs.models import McpConfig
from askui.chat.api.mcp_configs.service import McpConfigService


class TestMcpConfigsAPI:
    """Test suite for the MCP configs API endpoints."""

    def test_list_mcp_configs_empty(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test listing MCP configs when no configs exist."""
        response = test_client.get("/v1/mcp-configs", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["has_more"] is False

    def test_list_mcp_configs_with_configs(self, test_headers: dict[str, str]) -> None:
        """Test listing MCP configs when configs exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock MCP config
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Test MCP Config",
            mcp_server={"type": "stdio", "command": "test_command"},
        )
        (mcp_configs_dir / "mcpcnf_test123.json").write_text(
            mock_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/mcp-configs", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "mcpcnf_test123"
                assert data["data"][0]["name"] == "Test MCP Config"
                assert data["data"][0]["mcp_server"]["type"] == "stdio"
        finally:
            app.dependency_overrides.clear()

    def test_list_mcp_configs_with_pagination(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test listing MCP configs with pagination parameters."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple mock MCP configs
        for i in range(5):
            mock_config = McpConfig(
                id=f"mcpcnf_test{i}",
                object="mcp_config",
                created_at=1234567890 + i,
                name=f"Test MCP Config {i}",
                mcp_server={"type": "stdio", "command": f"test_command_{i}"},
            )
            (mcp_configs_dir / f"mcpcnf_test{i}.json").write_text(
                mock_config.model_dump_json()
            )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/mcp-configs?limit=3", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 3
                assert data["has_more"] is True
        finally:
            app.dependency_overrides.clear()

    def test_create_mcp_config(self, test_headers: dict[str, str]) -> None:
        """Test creating a new MCP config."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                config_data = {
                    "name": "New MCP Config",
                    "mcp_server": {"type": "stdio", "command": "new_command"},
                }
                response = client.post(
                    "/v1/mcp-configs", json=config_data, headers=test_headers
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["name"] == "New MCP Config"
                assert data["mcp_server"]["type"] == "stdio"
                assert data["mcp_server"]["command"] == "new_command"
        finally:
            app.dependency_overrides.clear()

    def test_create_mcp_config_minimal(self, test_headers: dict[str, str]) -> None:
        """Test creating an MCP config with minimal data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/v1/mcp-configs",
                    json={
                        "name": "Minimal Config",
                        "mcp_server": {"type": "stdio", "command": "minimal"},
                    },
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "mcp_config"
                assert data["name"] == "Minimal Config"
                assert data["mcp_server"]["type"] == "stdio"
                assert data["mcp_server"]["command"] == "minimal"
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_mcp_config(self, test_headers: dict[str, str]) -> None:
        """Test retrieving an existing MCP config."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Test MCP Config",
            mcp_server={"type": "stdio", "command": "test_command"},
        )
        (mcp_configs_dir / "mcpcnf_test123.json").write_text(
            mock_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/mcp-configs/mcpcnf_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "mcpcnf_test123"
                assert data["name"] == "Test MCP Config"
                assert data["mcp_server"]["type"] == "stdio"
                assert data["mcp_server"]["command"] == "test_command"
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_mcp_config_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent MCP config."""
        response = test_client.get(
            "/v1/mcp-configs/mcpcnf_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_modify_mcp_config(self, test_headers: dict[str, str]) -> None:
        """Test modifying an existing MCP config."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Original Name",
            mcp_server={"type": "stdio", "command": "original_command"},
        )
        (mcp_configs_dir / "mcpcnf_test123.json").write_text(
            mock_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                modify_data = {
                    "name": "Modified Name",
                    "mcp_server": {"type": "stdio", "command": "modified_command"},
                }
                response = client.post(
                    "/v1/mcp-configs/mcpcnf_test123",
                    json=modify_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Modified Name"
                assert data["mcp_server"]["type"] == "stdio"
                assert data["mcp_server"]["command"] == "modified_command"
        finally:
            app.dependency_overrides.clear()

    def test_modify_mcp_config_partial(self, test_headers: dict[str, str]) -> None:
        """Test modifying an MCP config with partial data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Original Name",
            mcp_server={"type": "stdio", "command": "original_command"},
        )
        (mcp_configs_dir / "mcpcnf_test123.json").write_text(
            mock_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                modify_data = {"name": "Only Name Modified"}
                response = client.post(
                    "/v1/mcp-configs/mcpcnf_test123",
                    json=modify_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Only Name Modified"

        finally:
            app.dependency_overrides.clear()

    def test_modify_mcp_config_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test modifying a non-existent MCP config."""
        modify_data = {"name": "Modified Name"}
        response = test_client.post(
            "/v1/mcp-configs/mcpcnf_nonexistent123",
            json=modify_data,
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_mcp_config(self, test_headers: dict[str, str]) -> None:
        """Test deleting an existing MCP config."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Test MCP Config",
            mcp_server={"type": "stdio", "command": "test_command"},
        )
        (mcp_configs_dir / "mcpcnf_test123.json").write_text(
            mock_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/v1/mcp-configs/mcpcnf_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_204_NO_CONTENT
                assert response.content == b""
        finally:
            app.dependency_overrides.clear()

    def test_delete_mcp_config_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent MCP config."""
        response = test_client.delete(
            "/v1/mcp-configs/mcpcnf_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
