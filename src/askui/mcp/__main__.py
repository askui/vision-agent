from fastmcp import FastMCP

# @dataclass
# class AppContext:
#     vision_agent: VisionAgent


# @asynccontextmanager
# async def mcp_lifespan(server: FastMCP[Any]) -> AsyncIterator[AppContext]:  # noqa: ARG001
#     with VisionAgent() as vision_agent:
#         yield AppContext(vision_agent=vision_agent)


# mcp = FastMCP("Vision Agent MCP App", lifespan=mcp_lifespan)
mcp = FastMCP("Vision Agent MCP App")


@mcp.tool
def get_the_name_of_the_app_to_test() -> str:
    return "com.google.android.apps.maps"


if __name__ == "__main__":
    mcp.run(transport="sse")
