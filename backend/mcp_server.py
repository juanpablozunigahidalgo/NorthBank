"""MCP stdio entry: `python mcp_server.py`."""

from northmill.mcp.server import build_mcp, main

if __name__ == "__main__":
    main()

__all__ = ["build_mcp", "main"]
