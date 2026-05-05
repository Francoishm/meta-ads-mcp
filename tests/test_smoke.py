"""Smoke tests — verify imports + tool registry without hitting the network."""

from meta_ads_mcp.server import build_server, _function_to_tool
from meta_ads_mcp.tools import ALL_TOOLS


def test_29_tools_registered():
    assert len(ALL_TOOLS) == 29


def test_all_tools_have_docstrings():
    for fn in ALL_TOOLS:
        assert fn.__doc__ and fn.__doc__.strip(), f"{fn.__name__} missing docstring"


def test_each_tool_builds_a_valid_mcp_tool():
    for fn in ALL_TOOLS:
        tool = _function_to_tool(fn)
        assert tool.name == fn.__name__
        assert tool.description
        assert tool.inputSchema["type"] == "object"


def test_server_initialises():
    server = build_server()
    assert server is not None
