"""MCP server entrypoint — exposes Meta Marketing tools over stdio (default)
or SSE (HTTP) transport.

Usage:
    meta-ads-mcp                  # stdio transport (default, for Claude Desktop)
    meta-ads-mcp --sse            # SSE transport on 0.0.0.0:8765
    meta-ads-mcp --sse --port 9000
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import MetaAdsClient, MetaAPIError
from .tools import ALL_TOOLS

logger = logging.getLogger("meta-ads-mcp")


def _python_type_to_json_schema(annotation: Any) -> dict:
    """Map Python typing annotations to a minimal JSON schema."""
    if annotation is str or annotation == "str":
        return {"type": "string"}
    if annotation is int or annotation == "int":
        return {"type": "integer"}
    if annotation is float or annotation == "float":
        return {"type": "number"}
    if annotation is bool or annotation == "bool":
        return {"type": "boolean"}
    if annotation is list or getattr(annotation, "__origin__", None) is list:
        return {"type": "array", "items": {}}
    if annotation is dict or getattr(annotation, "__origin__", None) is dict:
        return {"type": "object"}
    # Optional[X] or X | None → unwrap
    args = getattr(annotation, "__args__", None)
    if args:
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json_schema(non_none[0])
    return {"type": "string"}


def _function_to_tool(fn) -> Tool:
    """Build an MCP Tool from a Python function (introspect signature)."""
    sig = inspect.signature(fn)
    properties: dict[str, dict] = {}
    required: list[str] = []
    for pname, param in sig.parameters.items():
        if pname == "client":
            continue
        schema = _python_type_to_json_schema(param.annotation)
        if param.default is inspect.Parameter.empty:
            required.append(pname)
        else:
            schema["default"] = param.default if param.default is not None else None
        properties[pname] = schema

    description = (fn.__doc__ or "").strip().split("\n")[0]
    return Tool(
        name=fn.__name__,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required,
        },
    )


def build_server() -> Server:
    server: Server = Server("meta-ads-mcp")
    tool_index = {fn.__name__: fn for fn in ALL_TOOLS}

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [_function_to_tool(fn) for fn in ALL_TOOLS]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict | None) -> list[TextContent]:
        fn = tool_index.get(name)
        if fn is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        client = MetaAdsClient()
        args = arguments or {}
        try:
            result = await fn(client, **args)
        except MetaAPIError as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": e.message, "status": e.status, "details": e.payload},
                                indent=2, ensure_ascii=False),
            )]
        except TypeError as e:
            return [TextContent(type="text", text=f"Bad arguments: {e}")]
        except Exception as e:
            logger.exception("tool %s failed", name)
            return [TextContent(type="text", text=f"Internal error: {e}")]

        if isinstance(result, str):
            return [TextContent(type="text", text=result)]
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False, default=str),
        )]

    return server


async def _serve_stdio():
    server = build_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


async def _serve_sse(host: str, port: int):
    """Lightweight HTTP/SSE server for remote Claude Desktop connection."""
    try:
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        import uvicorn
    except ImportError:
        sys.exit("SSE mode needs 'starlette' and 'uvicorn'. pip install starlette uvicorn")

    server = build_server()
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ])
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    await uvicorn.Server(config).serve()


def main():
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Meta Ads MCP server")
    parser.add_argument("--sse", action="store_true", help="Run as HTTP/SSE server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", 8765)))
    args = parser.parse_args()

    if args.sse:
        logger.info("Starting Meta Ads MCP (SSE) on %s:%d", args.host, args.port)
        asyncio.run(_serve_sse(args.host, args.port))
    else:
        logger.info("Starting Meta Ads MCP (stdio)")
        asyncio.run(_serve_stdio())


if __name__ == "__main__":
    main()
