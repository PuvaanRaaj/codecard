"""One entry point for every card kind, shared by the CLI and the MCP server."""
import tempfile
from pathlib import Path

from . import lexers, render, transcript
from .redact import redact

KINDS = ("code", "term", "diff", "transcript")


def _auto_cols(rows, lo=40, hi=100) -> int:
    longest = max((sum(len(t) for _, t in toks) for _, toks in rows), default=lo)
    return max(lo, min(hi, longest + 1))


def render_card(
    kind: str,
    out: Path,
    *,
    text: str | None = None,
    name: str | None = None,
    lang: str | None = None,
    session: str | None = None,
    cwd: str | None = None,
    turns: int = 1,
    max_rows: int = 40,
    result_lines: int = 3,
    title: str | None = None,
    bg: str = "razer",
    cols: int | None = None,
    gif: bool = False,
    scale: int | None = None,
    redact_on: bool = True,
) -> Path:
    """Render one card to `out` (.png, or .gif when `gif` or the suffix says so)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    scrub = redact if redact_on else (lambda s: s)

    if kind == "transcript":
        path = transcript.find_session(session, cwd)
        events = transcript.last_turns(transcript.load_events(path), turns)
        cols = cols or 90
        rows = transcript.cap_rows(transcript.to_rows(events, cols, result_lines, scrub), max_rows)
        title = title or "Claude Code"
    else:
        if text is None:
            raise ValueError(f"{kind} needs text")
        text = scrub(text)
        rows = {"code": lambda: lexers.code(text, lang, name), "term": lambda: lexers.term(text),
                "diff": lambda: lexers.diff(text)}[kind]()
        cols = cols or _auto_cols(rows)
        rows = lexers.wrap(rows, cols)
        if title is None:
            title = name or {"term": "Terminal", "diff": "diff", "code": ""}[kind]

    as_gif = gif or out.suffix.lower() == ".gif"
    scale = scale or (1 if as_gif else 2)
    doc, w, h = render.to_html(rows, title, cols, bg)
    if as_gif:
        with tempfile.TemporaryDirectory() as tmp:
            png = render.screenshot(doc, w, h, Path(tmp) / "full.png", scale)
            render.gif(png, rows, cols, out, scale)
    else:
        render.screenshot(doc, w, h, out, scale, transparent=bg == "none")
    return out.resolve()
