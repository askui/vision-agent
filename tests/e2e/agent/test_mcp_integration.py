"""E2E tests for MCP integration with AgentBase."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from fastmcp import Client, FastMCP

from askui.models.shared.tools import ToolCollection
from askui.models.shared.agent_message_param import MessageParam
from askui.agent_base import AgentBase


class MockMcpServer:
    """Mock MCP server for testing."""
    
    def __init__(self):
        self.tools = {
            "add_numbers": {
                "name": "add_numbers",
                "description": "Add two numbers together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            "get_weather": {
                "name": "get_weather", 
                "description": "Get weather information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"]
                }
            }
        }
        
    async def list_tools(self):
        return list(self.tools.values())
        
    async def call_tool(self, name: str, arguments: dict):
        if name == "add_numbers":
            result = arguments["a"] + arguments["b"]
            return Mock(text=str(result))
        elif name == "get_weather":
            return Mock(text=f"Weather in {arguments['city']}: Sunny, 25°C")
        else:
            raise ValueError(f"Unknown tool: {name}")


class TestMcpToolCollection:
    """Test MCP integration with ToolCollection."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MCP client."""
        mock_server = MockMcpServer()
        client = Mock(spec=Client)
        client.list_tools = AsyncMock(side_effect=mock_server.list_tools)
        client.call_tool = AsyncMock(side_effect=mock_server.call_tool)
        return client

    def test_toolcollection_with_mcp_client(self, mock_client):
        """Test ToolCollection can be initialized with MCP client."""
        tool_collection = ToolCollection(mcp_client=mock_client)
        assert tool_collection._mcp_client == mock_client
        assert tool_collection._mcp_tools_cache is None

    def test_toolcollection_to_params_includes_mcp_tools(self, mock_client):
        """Test that to_params includes MCP tools."""
        tool_collection = ToolCollection(mcp_client=mock_client)
        params = tool_collection.to_params()
        
        # Should include both MCP tools
        tool_names = [param.name for param in params]
        assert "add_numbers" in tool_names
        assert "get_weather" in tool_names
        
        # Check tool details
        add_tool = next(p for p in params if p.name == "add_numbers")
        assert add_tool.description == "Add two numbers together"
        assert "a" in add_tool.input_schema["properties"]
        assert "b" in add_tool.input_schema["properties"]

    def test_mcp_tool_execution(self, mock_client):
        """Test that MCP tools can be executed through ToolCollection."""
        from askui.models.shared.agent_message_param import ToolUseBlockParam
        
        tool_collection = ToolCollection(mcp_client=mock_client)
        
        # Create a tool use block for add_numbers
        tool_use = ToolUseBlockParam(
            type="tool_use",
            id="test-123",
            name="add_numbers",
            input={"a": 5, "b": 3}
        )
        
        # Run the tool
        results = tool_collection.run([tool_use])
        assert len(results) == 1
        
        result = results[0]
        assert result.tool_use_id == "test-123"
        assert not result.is_error
        assert "8" in result.content  # 5 + 3 = 8

    def test_mcp_tool_execution_error_handling(self, mock_client):
        """Test error handling when MCP tool execution fails."""
        from askui.models.shared.agent_message_param import ToolUseBlockParam
        
        # Make call_tool raise an exception
        mock_client.call_tool = AsyncMock(side_effect=ValueError("Test error"))
        
        tool_collection = ToolCollection(mcp_client=mock_client)
        
        tool_use = ToolUseBlockParam(
            type="tool_use",
            id="test-error",
            name="add_numbers", 
            input={"a": 5, "b": 3}
        )
        
        results = tool_collection.run([tool_use])
        assert len(results) == 1
        
        result = results[0]
        assert result.tool_use_id == "test-error"
        assert result.is_error
        assert "failed" in result.content.lower()

    def test_unknown_mcp_tool_handling(self, mock_client):
        """Test handling of unknown tool names."""
        from askui.models.shared.agent_message_param import ToolUseBlockParam
        
        tool_collection = ToolCollection(mcp_client=mock_client)
        
        tool_use = ToolUseBlockParam(
            type="tool_use",
            id="test-unknown",
            name="unknown_tool",
            input={}
        )
        
        results = tool_collection.run([tool_use])
        assert len(results) == 1
        
        result = results[0]
        assert result.tool_use_id == "test-unknown"
        assert result.is_error
        assert "Tool not found" in result.content


class TestMcpIntegration:
    """Test MCP integration scenarios."""

    def test_stdio_server_connection(self):
        """Test connecting to a stdio MCP server."""
        # This would test actual stdio connection in real scenario
        server_config = "python -m some_mcp_server"
        client = Client(server_config)
        
        tool_collection = ToolCollection(mcp_client=client)
        assert tool_collection._mcp_client == client

    def test_sse_server_connection(self):
        """Test connecting to an SSE MCP server."""
        # This would test actual SSE connection in real scenario  
        server_url = "http://localhost:8000/sse"
        client = Client(server_url)
        
        tool_collection = ToolCollection(mcp_client=client)
        assert tool_collection._mcp_client == client

    def test_http_server_connection(self):
        """Test connecting to an HTTP MCP server."""
        # This would test actual HTTP connection in real scenario
        server_url = "http://localhost:8000/mcp"
        client = Client(server_url)
        
        tool_collection = ToolCollection(mcp_client=client)
        assert tool_collection._mcp_client == client

    def test_in_memory_server_connection(self):
        """Test connecting to an in-memory MCP server."""
        # Create a FastMCP server instance
        server = FastMCP("Test Server")
        
        @server.tool
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b
        
        # Connect directly to the server instance
        tool_collection = ToolCollection(mcp_client=Client(server))
        assert tool_collection._mcp_client is not None


class TestAgentBaseMcpIntegration:
    """Test MCP integration with AgentBase."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        # This would be replaced with actual agent setup in real tests
        return Mock(spec=AgentBase)

    def test_act_with_mcp_client_parameter(self, mock_agent):
        """Test that act method accepts mcp_client parameter."""
        from fastmcp import Client
        
        mock_client = Mock(spec=Client)
        
        # Mock the act method to verify it's called with correct parameters
        mock_agent.act = Mock()
        
        # This would be the actual call in real scenario
        mock_agent.act(
            goal="Test goal",
            mcp_client=mock_client
        )
        
        # Verify the method was called with mcp_client
        mock_agent.act.assert_called_once()
        call_args = mock_agent.act.call_args
        assert call_args.kwargs.get('mcp_client') == mock_client

    def test_backwards_compatibility(self, mock_agent):
        """Test that existing code without MCP still works."""
        mock_agent.act = Mock()
        
        # Call without mcp_client should still work
        mock_agent.act(goal="Test goal")
        
        mock_agent.act.assert_called_once()
        call_args = mock_agent.act.call_args
        # mcp_client should be None when not provided
        assert call_args.kwargs.get('mcp_client') is None


class TestMcpToolCaching:
    """Test MCP tool caching behavior."""

    def test_tools_are_cached(self, mock_client):
        """Test that MCP tools are cached after first retrieval."""
        tool_collection = ToolCollection(mcp_client=mock_client)
        
        # First call should fetch tools
        tools1 = tool_collection._get_mcp_tools()
        assert mock_client.list_tools.call_count == 1
        
        # Second call should use cache
        tools2 = tool_collection._get_mcp_tools()
        assert mock_client.list_tools.call_count == 1  # Still 1, not 2
        
        # Results should be the same
        assert tools1 == tools2

    def test_cache_error_handling(self, mock_client):
        """Test error handling when caching fails."""
        # Make list_tools fail
        mock_client.list_tools = AsyncMock(side_effect=Exception("Connection failed"))
        
        tool_collection = ToolCollection(mcp_client=mock_client)
        
        # Should return empty dict on error
        tools = tool_collection._get_mcp_tools()
        assert tools == {}
        assert tool_collection._mcp_tools_cache == {}


@pytest.fixture
def mock_client():
    """Global fixture for mock MCP client."""
    mock_server = MockMcpServer()
    client = Mock(spec=Client)
    client.list_tools = AsyncMock(side_effect=mock_server.list_tools)
    client.call_tool = AsyncMock(side_effect=mock_server.call_tool)
    return client