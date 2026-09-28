"""Drive the MCP server over real stdio JSON-RPC, independent of client SDK versions."""
import json
import subprocess
import sys

import pytest

pytest.importorskip("mcp")
from codecard import render  # noqa: E402


def _rpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    if "id" not in msg:
        return None
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout: " + proc.stderr.read())
        reply = json.loads(line)
        if reply.get("id") == msg["id"]:
            return reply


@pytest.fixture
def server(tmp_path):
    proc = subprocess.Popen([sys.executable, "-m", "codecard.mcp_server"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            env={**__import__("os").environ, "CODECARD_OUT": str(tmp_path)})
    init = _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}})
    assert "result" in init, init
    _rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    yield proc
    proc.kill()
    proc.communicate()


def test_lists_four_tools(server):
    tools = _rpc(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
    assert {t["name"] for t in tools} == {"render_code", "render_terminal", "render_diff", "render_transcript"}


def _chrome():
    try:
        return render.find_chrome()
    except FileNotFoundError:
        return None


@pytest.mark.skipif(_chrome() is None, reason="no Chrome available")
def test_render_terminal_returns_path_and_image(server, tmp_path):
    r = _rpc(server, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "render_terminal", "arguments": {"text": "$ export API_KEY=supersecret123\nok"}}})
    content = r["result"]["content"]
    kinds = [c["type"] for c in content]
    assert kinds == ["text", "image"], r
    path = content[0]["text"].removeprefix("Wrote ").strip()
    assert path.startswith(str(tmp_path)) and path.endswith(".png")
    assert content[1]["mimeType"] == "image/png"


def test_rejects_non_image_out(server):
    r = _rpc(server, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
        "name": "render_terminal", "arguments": {"text": "$ ls", "out": "/tmp/evil.sh"}}})
    assert r["result"].get("isError") is True
