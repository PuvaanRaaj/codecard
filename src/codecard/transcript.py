"""Read a Claude Code session (.jsonl) and turn its last turns into rows.

Rendered in the Claude Code TUI idiom: `>` prompts, `●` assistant text and
tool calls, `⎿` tool results. Thinking blocks, subagent sidechains, meta lines
and injected <system-reminder> text are never rendered.
"""
import glob
import json
import os
import re
import textwrap
from pathlib import Path

from .lexers import Row

_TAGGED = re.compile(r"<(system-reminder|command-[a-z-]+|local-command-[a-z-]+)>[\s\S]*?</\1>")
_SUMMARY_KEYS = ("command", "file_path", "path", "pattern", "url", "query", "prompt", "description")


def config_dirs() -> list[Path]:
    dirs = []
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        dirs.append(Path(os.environ["CLAUDE_CONFIG_DIR"]).expanduser())
    dirs += [Path.home() / ".claude"] + [Path(p) for p in glob.glob(str(Path.home() / ".claude-*"))]
    seen, out = set(), []
    for d in dirs:
        r = d.resolve()
        if r not in seen and (d / "projects").is_dir():
            seen.add(r)
            out.append(d)
    return out


def find_session(ref: str | None, cwd: str | None = None) -> Path:
    """Path to a session jsonl: explicit path, a session id, or the newest for `cwd`."""
    if ref and Path(ref).expanduser().is_file():
        return Path(ref).expanduser()
    cands: list[Path] = []
    for d in config_dirs():
        if ref:
            cands += [Path(p) for p in glob.glob(str(d / "projects" / "*" / f"{ref}*.jsonl"))]
        else:
            slug = re.sub(r"[^A-Za-z0-9]", "-", cwd or os.getcwd())
            cands += [Path(p) for p in glob.glob(str(d / "projects" / slug / "*.jsonl"))]
    if not cands:
        where = f"session '{ref}'" if ref else f"any session for {cwd or os.getcwd()}"
        raise FileNotFoundError(f"could not find {where} under {[str(d) for d in config_dirs()]}")
    return max(cands, key=lambda p: p.stat().st_mtime)


def _clean(text: str) -> str:
    return _TAGGED.sub("", text).strip()


def _prompt_text(content) -> str | None:
    """Text of a real user prompt, or None if this user line is a tool result / injected."""
    if isinstance(content, str):
        t = _clean(content)
        return t or None
    if isinstance(content, list):
        if any(b.get("type") == "tool_result" for b in content):
            return None
        parts = []
        for b in content:
            if b.get("type") == "text":
                parts.append(_clean(b.get("text", "")))
            elif b.get("type") == "image":
                parts.append("[image]")
        t = "\n".join(p for p in parts if p)
        return t or None
    return None


def _summary(inp: dict) -> str:
    for k in _SUMMARY_KEYS:
        v = inp.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().splitlines()[0]
    for v in inp.values():
        if isinstance(v, str) and v.strip():
            return v.strip().splitlines()[0]
    return ""


def _result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if b.get("type") == "text")
    return ""


def load_events(path: Path) -> list[dict]:
    """Flatten a session into ordered events: prompt / text / tool / result."""
    events: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("isSidechain") or d.get("isMeta") or d.get("type") not in ("user", "assistant"):
                continue
            content = (d.get("message") or {}).get("content")
            if d["type"] == "user":
                t = _prompt_text(content)
                if t:
                    events.append({"kind": "prompt", "text": t})
                elif isinstance(content, list):
                    for b in content:
                        if b.get("type") == "tool_result":
                            events.append({"kind": "result", "text": _result_text(b.get("content")),
                                           "error": bool(b.get("is_error"))})
            else:
                for b in content or []:
                    if b.get("type") == "text" and b.get("text", "").strip():
                        events.append({"kind": "text", "text": b["text"].strip()})
                    elif b.get("type") == "tool_use":
                        events.append({"kind": "tool", "name": b.get("name", "?"),
                                       "arg": _summary(b.get("input") or {})})
    return events


def last_turns(events: list[dict], turns: int) -> list[dict]:
    starts = [i for i, e in enumerate(events) if e["kind"] == "prompt"]
    if not starts:
        return events
    return events[starts[-turns] if turns <= len(starts) else 0:]


def to_rows(events: list[dict], cols: int, result_lines: int = 3, redact=lambda s: s) -> list[Row]:
    from .lexers import wrap

    rows: list[Row] = []

    def block(first: list[tuple[str, str]], text: str, cls: str, indent: int, rcls: str = ""):
        # prose: wrap at word boundaries; wrap() below still hard-breaks anything longer
        lines = [w for l in (text.splitlines() or [""])
                 for w in (textwrap.wrap(l, cols - indent, break_long_words=True) or [""])]
        body = [(rcls, first + [(cls, lines[0])])] + [(rcls, [("", " " * indent), (cls, l)]) for l in lines[1:]]
        rows.extend(wrap(body, cols, indent))

    for e in events:
        if e["kind"] == "prompt":
            if rows:
                rows.append(("", []))
            block([("pr", "> ")], redact(e["text"]), "user", 2, "prompt")
        elif e["kind"] == "text":
            block([("dot", "● ")], redact(e["text"]), "", 2)
        elif e["kind"] == "tool":
            arg = redact(e["arg"])
            if len(arg) > cols - len(e["name"]) - 6:
                arg = arg[: max(0, cols - len(e["name"]) - 7)] + "…"
            rows.append(("", [("tdot", "● "), ("tool", e["name"]), ("", "("), ("targ", arg), ("", ")")]))
        elif e["kind"] == "result":
            lines = [l for l in redact(e["text"]).splitlines() if l.strip()] or ["(no output)"]
            shown, extra = lines[:result_lines], len(lines) - result_lines
            cls = "err" if e["error"] else "res"
            for i, l in enumerate(shown):
                lead = "  ⎿  " if i == 0 else "     "
                rows.extend(wrap([("", [("res", lead), (cls, l)])], cols, 5))
            if extra > 0:
                rows.append(("", [("res", f"     … +{extra} lines")]))
    return rows


def cap_rows(rows: list[Row], max_rows: int) -> list[Row]:
    """Keep the newest rows, never starting mid-block, with an "earlier rows" marker."""
    if len(rows) <= max_rows:
        return rows
    kept = rows[-(max_rows - 1):]
    while kept and "".join(t for _, t in kept[0][1])[:1] in (" ", ""):
        kept.pop(0)  # first row must be a > prompt or a ● line
    return [("", [("res", f"… {len(rows) - len(kept)} earlier rows")])] + kept
