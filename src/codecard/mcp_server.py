"""codecard as an MCP server (stdio). Install with the `mcp` extra.

Every tool always redacts — there is deliberately no way for an agent to turn
it off. Each tool returns the written file path, plus the PNG itself so the
model can look at what it made.
"""
import os
import tempfile
import time
from pathlib import Path

from mcp.server.mcpserver import Image, MCPServer

from .card import render_card

server = MCPServer(
    "codecard",
    instructions=(
        "Render carbon-style images locally (nothing is uploaded). Use render_code for source, "
        "render_terminal for $ commands + output, render_diff for unified diffs, render_transcript "
        "for the last turns of a Claude Code session. Keep cards short (<= ~30 rows). Always look at "
        "the returned image before telling the user it is done. Output is redacted automatically, but "
        "check transcripts for internal hostnames or customer data before the user shares them."
    ),
)


def _out(kind: str, out: str | None, gif: bool) -> Path:
    if out:
        p = Path(out).expanduser()
        if p.suffix.lower() not in (".png", ".gif"):
            raise ValueError("out must end in .png or .gif")
        return p
    base = Path(os.environ.get("CODECARD_OUT") or Path(tempfile.gettempdir()) / "codecard")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{kind}-{time.strftime('%Y%m%d-%H%M%S')}.{'gif' if gif else 'png'}"


def _result(path: Path):
    if path.suffix.lower() == ".png":
        return [f"Wrote {path}", Image(path=path)]
    return [f"Wrote {path} (animated GIF)"]


@server.tool()
def render_code(code: str, language: str | None = None, filename: str | None = None,
                title: str | None = None, out: str | None = None, gif: bool = False,
                bg: str = "razer", cols: int | None = None):
    """Syntax-highlighted source code card. `language` or `filename` picks the highlighter; otherwise it is guessed."""
    return _result(render_card("code", _out("code", out, gif), text=code, lang=language, name=filename,
                               title=title, gif=gif, bg=bg, cols=cols))


@server.tool()
def render_terminal(text: str, title: str | None = None, out: str | None = None, gif: bool = False,
                    bg: str = "razer", cols: int | None = None):
    """Terminal card. Lines starting '$ ' or '> ' are commands, '  # ' starts a comment, other lines are output."""
    return _result(render_card("term", _out("term", out, gif), text=text, title=title, gif=gif, bg=bg, cols=cols))


@server.tool()
def render_diff(diff: str, title: str | None = None, out: str | None = None, gif: bool = False,
                bg: str = "razer", cols: int | None = None):
    """Unified diff card (e.g. output of `git diff`) with +/- line colouring."""
    return _result(render_card("diff", _out("diff", out, gif), text=diff, title=title, gif=gif, bg=bg, cols=cols))


@server.tool()
def render_transcript(session: str | None = None, cwd: str | None = None, turns: int = 1, max_rows: int = 30,
                      title: str | None = None, out: str | None = None, gif: bool = False, bg: str = "razer"):
    """Card of the last `turns` prompts of a Claude Code session, in the Claude Code UI style.

    `session` is a session id or .jsonl path; omitted means the newest session for `cwd`
    (default: the server's working directory). Thinking and subagent traffic are never shown.
    """
    return _result(render_card("transcript", _out("transcript", out, gif), session=session, cwd=cwd,
                               turns=turns, max_rows=max_rows, title=title, gif=gif, bg=bg))


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
