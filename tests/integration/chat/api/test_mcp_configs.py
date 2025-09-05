"""Integration tests for the MCP configs API endpoints."""

import tempfile
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

from askui.chat.api.mcp_configs.models import McpConfig
from askui.chat.api.mcp_configs.service import McpConfigService


class TestMcpConfigsAPI:
    """Test suite for the MCP configs API endpoints."""

    def test_list_mcp_configs_with_configs(self, test_headers: dict[str, str]) -> None:
        """Test listing MCP configs when configs exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock MCP config
        workspace_id = test_headers["askui-workspace"]
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Test MCP Config",
            mcp_server={"type": "stdio", "command": "test_command"},
            workspace_id=workspace_id,
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
        workspace_id = test_headers["askui-workspace"]
        for i in range(5):
            mock_config = McpConfig(
                id=f"mcpcnf_test{i}",
                object="mcp_config",
                created_at=1234567890 + i,
                name=f"Test MCP Config {i}",
                mcp_server={"type": "stdio", "command": f"test_command_{i}"},
                workspace_id=workspace_id,
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

        workspace_id = test_headers["askui-workspace"]
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Original Name",
            mcp_server={"type": "stdio", "command": "original_command"},
            workspace_id=workspace_id,
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

        workspace_id = test_headers["askui-workspace"]
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Original Name",
            mcp_server={"type": "stdio", "command": "original_command"},
            workspace_id=workspace_id,
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

        workspace_id = test_headers["askui-workspace"]
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=1234567890,
            name="Test MCP Config",
            mcp_server={"type": "stdio", "command": "test_command"},
            workspace_id=workspace_id,
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

    def test_modify_default_mcp_config_forbidden(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that modifying a default MCP configuration returns 403 Forbidden."""
        # Create a default MCP config (no workspace_id)
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        default_config = McpConfig(
            id="mcpcnf_default123",
            object="mcp_config",
            created_at=1234567890,
            name="Default MCP Config",
            mcp_server={"type": "stdio", "command": "default_command"},
            workspace_id=None,  # No workspace_id = default
        )
        (mcp_configs_dir / "mcpcnf_default123.json").write_text(
            default_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                # Try to modify the default MCP config
                response = client.post(
                    "/v1/mcp-configs/mcpcnf_default123",
                    headers=test_headers,
                    json={"name": "Modified Name"},
                )
                assert response.status_code == 403
                assert "cannot be modified" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_default_mcp_config_forbidden(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that deleting a default MCP configuration returns 403 Forbidden."""
        # Create a default MCP config (no workspace_id)
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        default_config = McpConfig(
            id="mcpcnf_default456",
            object="mcp_config",
            created_at=1234567890,
            name="Default MCP Config",
            mcp_server={"type": "stdio", "command": "default_command"},
            workspace_id=None,  # No workspace_id = default
        )
        (mcp_configs_dir / "mcpcnf_default456.json").write_text(
            default_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                # Try to delete the default MCP config
                response = client.delete(
                    "/v1/mcp-configs/mcpcnf_default456",
                    headers=test_headers,
                )
                assert response.status_code == 403
                assert "cannot be deleted" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_list_mcp_configs_includes_default_and_workspace(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that listing MCP configs includes both default and workspace-scoped
        ones."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        # Create a default MCP config (no workspace_id)
        default_config = McpConfig(
            id="mcpcnf_default789",
            object="mcp_config",
            created_at=1234567890,
            name="Default MCP Config",
            mcp_server={"type": "stdio", "command": "default_command"},
            workspace_id=None,  # No workspace_id = default
        )
        (mcp_configs_dir / "mcpcnf_default789.json").write_text(
            default_config.model_dump_json()
        )

        # Create a workspace-scoped MCP config
        workspace_id = test_headers["askui-workspace"]
        workspace_config = McpConfig(
            id="mcpcnf_workspace123",
            object="mcp_config",
            created_at=1234567890,
            name="Workspace MCP Config",
            mcp_server={"type": "stdio", "command": "workspace_command"},
            workspace_id=workspace_id,
        )
        (mcp_configs_dir / "mcpcnf_workspace123.json").write_text(
            workspace_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                # List MCP configs - should include both
                response = client.get("/v1/mcp-configs", headers=test_headers)
                assert response.status_code == 200

                data = response.json()
                config_ids = [config["id"] for config in data["data"]]

                # Should include both default and workspace configs
                assert "mcpcnf_default789" in config_ids
                assert "mcpcnf_workspace123" in config_ids

                # Verify workspace_id fields
                default_config_data = next(
                    c for c in data["data"] if c["id"] == "mcpcnf_default789"
                )
                workspace_config_data = next(
                    c for c in data["data"] if c["id"] == "mcpcnf_workspace123"
                )

                # Default config should not have workspace_id field (excluded when None)
                assert "workspace_id" not in default_config_data
                assert workspace_config_data["workspace_id"] == workspace_id
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_default_mcp_config_success(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that retrieving a default MCP configuration works."""
        # Create a default MCP config (no workspace_id)
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        default_config = McpConfig(
            id="mcpcnf_defaultretrieve",
            object="mcp_config",
            created_at=1234567890,
            name="Default MCP Config",
            mcp_server={"type": "stdio", "command": "default_command"},
            workspace_id=None,  # No workspace_id = default
        )
        (mcp_configs_dir / "mcpcnf_defaultretrieve.json").write_text(
            default_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                # Retrieve the default MCP config
                response = client.get(
                    "/v1/mcp-configs/mcpcnf_defaultretrieve",
                    headers=test_headers,
                )
                assert response.status_code == 200

                data = response.json()
                assert data["id"] == "mcpcnf_defaultretrieve"
                # Default config should not have workspace_id field (excluded when None)
                assert "workspace_id" not in data
        finally:
            app.dependency_overrides.clear()

    def test_workspace_scoped_mcp_config_operations_success(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test that workspace-scoped MCP configs can be modified and deleted."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        mcp_configs_dir = workspace_path / "mcp_configs"
        mcp_configs_dir.mkdir(parents=True, exist_ok=True)

        workspace_id = test_headers["askui-workspace"]
        workspace_config = McpConfig(
            id="mcpcnf_workspaceops",
            object="mcp_config",
            created_at=1234567890,
            name="Workspace MCP Config",
            mcp_server={"type": "stdio", "command": "workspace_command"},
            workspace_id=workspace_id,
        )
        (mcp_configs_dir / "mcpcnf_workspaceops.json").write_text(
            workspace_config.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(workspace_path)

        app.dependency_overrides[get_mcp_config_service] = override_mcp_config_service

        try:
            with TestClient(app) as client:
                # Modify the workspace MCP config
                response = client.post(
                    "/v1/mcp-configs/mcpcnf_workspaceops",
                    headers=test_headers,
                    json={"name": "Modified Workspace MCP Config"},
                )
                assert response.status_code == 200

                data = response.json()
                assert data["name"] == "Modified Workspace MCP Config"
                assert data["workspace_id"] == workspace_id

                # Delete the workspace MCP config
                response = client.delete(
                    "/v1/mcp-configs/mcpcnf_workspaceops",
                    headers=test_headers,
                )
                assert response.status_code == 204

                # Verify it's deleted
                response = client.get(
                    "/v1/mcp-configs/mcpcnf_workspaceops",
                    headers=test_headers,
                )
                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
