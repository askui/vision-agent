"""Integration tests for the MCP configs API endpoints."""

from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient
from fastmcp.mcp_config import StdioMCPServer
from sqlalchemy.orm import Session

from askui.chat.api.mcp_configs.models import McpConfig
from askui.chat.api.mcp_configs.orms import McpConfigOrm
from askui.chat.api.mcp_configs.service import McpConfigService


class TestMcpConfigsAPI:
    """Test suite for the MCP configs API endpoints."""

    def test_list_mcp_configs_with_configs(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test listing MCP configs when configs exist."""
        from datetime import datetime, timezone

        # Create a mock MCP config in the database
        workspace_id = UUID(test_headers["askui-workspace"])
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Test MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="test_command"),
            workspace_id=workspace_id,
        )
        mcp_config_orm = McpConfigOrm.from_model(mock_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test listing MCP configs with pagination parameters."""
        from datetime import datetime, timezone

        # Create multiple mock MCP configs in the database
        workspace_id = UUID(test_headers["askui-workspace"])
        for i in range(5):
            mock_config = McpConfig(
                id=f"mcpcnf_test{i}",
                object="mcp_config",
                created_at=datetime.fromtimestamp(1234567890 + i, timezone.utc),
                name=f"Test MCP Config {i}",
                mcp_server=StdioMCPServer(type="stdio", command=f"test_command_{i}"),
                workspace_id=workspace_id,
            )
            mcp_config_orm = McpConfigOrm.from_model(mock_config)
            test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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

    def test_create_mcp_config(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test creating a new MCP config."""
        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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

    def test_create_mcp_config_minimal(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test creating an MCP config with minimal data."""
        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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

    def test_retrieve_mcp_config(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving an existing MCP config."""
        from datetime import datetime, timezone

        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Test MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="test_command"),
            workspace_id=None,
        )
        mcp_config_orm = McpConfigOrm.from_model(mock_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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

    def test_modify_mcp_config(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test modifying an existing MCP config."""
        from datetime import datetime, timezone

        workspace_id = UUID(test_headers["askui-workspace"])
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Original Name",
            mcp_server=StdioMCPServer(type="stdio", command="original_command"),
            workspace_id=workspace_id,
        )
        mcp_config_orm = McpConfigOrm.from_model(mock_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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

    def test_modify_mcp_config_partial(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test modifying an MCP config with partial data."""
        from datetime import datetime, timezone

        workspace_id = UUID(test_headers["askui-workspace"])
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Original Name",
            mcp_server=StdioMCPServer(type="stdio", command="original_command"),
            workspace_id=workspace_id,
        )
        mcp_config_orm = McpConfigOrm.from_model(mock_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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

    def test_delete_mcp_config(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test deleting an existing MCP config."""
        from datetime import datetime, timezone

        workspace_id = UUID(test_headers["askui-workspace"])
        mock_config = McpConfig(
            id="mcpcnf_test123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Test MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="test_command"),
            workspace_id=workspace_id,
        )
        mcp_config_orm = McpConfigOrm.from_model(mock_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test that modifying a default MCP configuration returns 403 Forbidden."""
        from datetime import datetime, timezone

        # Create a default MCP config (no workspace_id) in the database
        default_config = McpConfig(
            id="mcpcnf_default123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Default MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="default_command"),
            workspace_id=None,  # No workspace_id = default
        )
        mcp_config_orm = McpConfigOrm.from_model(default_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test that deleting a default MCP configuration returns 403 Forbidden."""
        from datetime import datetime, timezone

        # Create a default MCP config (no workspace_id) in the database
        default_config = McpConfig(
            id="mcpcnf_default456",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Default MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="default_command"),
            workspace_id=None,  # No workspace_id = default
        )
        mcp_config_orm = McpConfigOrm.from_model(default_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test that listing MCP configs includes both default and workspace-scoped
        ones."""
        from datetime import datetime, timezone

        # Create a default MCP config (no workspace_id) in the database
        default_config = McpConfig(
            id="mcpcnf_default789",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Default MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="default_command"),
            workspace_id=None,  # No workspace_id = default
        )
        mcp_config_orm = McpConfigOrm.from_model(default_config)
        test_db_session.add(mcp_config_orm)

        # Create a workspace-scoped MCP config
        workspace_id = UUID(test_headers["askui-workspace"])
        workspace_config = McpConfig(
            id="mcpcnf_workspace123",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Workspace MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="workspace_command"),
            workspace_id=workspace_id,
        )
        workspace_config_orm = McpConfigOrm.from_model(workspace_config)
        test_db_session.add(workspace_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
                assert workspace_config_data["workspace_id"] == str(workspace_id)
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_default_mcp_config_success(
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test that retrieving a default MCP configuration works."""
        from datetime import datetime, timezone

        # Create a default MCP config (no workspace_id) in the database
        default_config = McpConfig(
            id="mcpcnf_defaultretrieve",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Default MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="default_command"),
            workspace_id=None,  # No workspace_id = default
        )
        mcp_config_orm = McpConfigOrm.from_model(default_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
        self, test_db_session: Session, test_headers: dict[str, str]
    ) -> None:
        """Test that workspace-scoped MCP configs can be modified and deleted."""
        from datetime import datetime, timezone

        workspace_id = UUID(test_headers["askui-workspace"])
        workspace_config = McpConfig(
            id="mcpcnf_workspaceops",
            object="mcp_config",
            created_at=datetime.fromtimestamp(1234567890, timezone.utc),
            name="Workspace MCP Config",
            mcp_server=StdioMCPServer(type="stdio", command="workspace_command"),
            workspace_id=workspace_id,
        )
        mcp_config_orm = McpConfigOrm.from_model(workspace_config)
        test_db_session.add(mcp_config_orm)
        test_db_session.commit()

        from askui.chat.api.app import app
        from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service

        def override_mcp_config_service() -> McpConfigService:
            return McpConfigService(test_db_session, seeds=[])

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
                assert data["workspace_id"] == str(workspace_id)

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
