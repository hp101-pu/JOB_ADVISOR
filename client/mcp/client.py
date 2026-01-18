from langchain_mcp_adapters.client import MultiServerMCPClient
from client.mcp.server import SERVERS

_mcp_client: MultiServerMCPClient | None = None


async def get_mcp_client() -> MultiServerMCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MultiServerMCPClient(SERVERS)
    return _mcp_client

async def close_mcp_client():
    """Reset the singleton on shutdown."""
    global _client
    _client = None