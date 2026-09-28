"""codecard CLI. Prints the written file path on stdout, errors on stderr."""
import argparse
import sys
from pathlib import Path

from . import lexers, render, transcript
from .redact import redact


def _read(src: str | None) -> tuple[str, str | None]:
    if not src or src == "-":
        if sys.stdin.isatty():
            sys.exit("codecard: no input — pass a file or pipe text on stdin")
        return sys.stdin.read(), None
    p = Path(src).expanduser()
    return p.read_text(encoding="utf-8", errors="replace"), p.name


def _auto_cols(rows, lo=40, hi=100) -> int:
    longest = max((sum(len(t) for _, t in toks) for _, toks in rows), default=lo)
    return max(lo, min(hi, longest + 1))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="codecard", description="Carbon-style images of code, terminals, diffs and Claude Code transcripts. Renders locally; nothing is uploaded.")
    sub = ap.add_subparsers(dest="kind", required=True)

    def common(p):
        p.add_argument("-o", "--out", help="output file (.png or .gif); default codecard-<kind>.png")
        p.add_argument("-t", "--title", help="window title")
        p.add_argument("--bg", default="razer", help=f"background: {', '.join(render.BACKGROUNDS)} or any CSS color/gradient")
        p.add_argument("--cols", type=int, help="wrap width in characters (default: fit content, 40-100)")
        p.add_argument("--gif", action="store_true", help="animated line-by-line reveal instead of a still PNG")
        p.add_argument("--scale", type=int, help="pixel density (default 2 for PNG, 1 for GIF)")
        p.add_argument("--no-redact", action="store_true", help="do NOT mask tokens, passwords and card numbers")

    p = sub.add_parser("code", help="syntax-highlighted source code")
    p.add_argument("input", nargs="?", help="file, or - / omitted for stdin")
    p.add_argument("-l", "--lang", help="language (default: from filename, else guessed)")
    common(p)
    p = sub.add_parser("term", help="terminal session: $ commands, output, # comments")
    p.add_argument("input", nargs="?")
    common(p)
    p = sub.add_parser("diff", help="unified diff, e.g. git diff | codecard diff")
    p.add_argument("input", nargs="?")
    common(p)
    p = sub.add_parser("transcript", help="the last turns of a Claude Code session")
    p.add_argument("session", nargs="?", help="session .jsonl path or id (default: newest session for this directory)")
    p.add_argument("-n", "--turns", type=int, default=1, help="how many of the last prompts to include (default 1)")
    p.add_argument("--max-rows", type=int, default=40, help="cap on rendered rows; oldest are dropped (default 40)")
    p.add_argument("--result-lines", type=int, default=3, help="lines of each tool result to show (default 3)")
    common(p)
    a = ap.parse_args(argv)

    scrub = (lambda s: s) if a.no_redact else redact
    try:
        if a.kind == "transcript":
            path = transcript.find_session(a.session)
            events = transcript.last_turns(transcript.load_events(path), a.turns)
            cols = a.cols or 90
            rows = transcript.to_rows(events, cols, a.result_lines, scrub)
            rows = transcript.cap_rows(rows, a.max_rows)
            title = a.title or "Claude Code"
        else:
            text, name = _read(a.input)
            text = scrub(text)
            if a.kind == "code":
                rows = lexers.code(text, a.lang, name)
            elif a.kind == "term":
                rows = lexers.term(text)
            else:
                rows = lexers.diff(text)
            cols = a.cols or _auto_cols(rows)
            rows = lexers.wrap(rows, cols)
            title = a.title if a.title is not None else (name or {"term": "Terminal", "diff": "diff", "code": ""}[a.kind])

        out = Path(a.out or f"codecard-{a.kind}.{'gif' if a.gif else 'png'}")
        as_gif = a.gif or out.suffix.lower() == ".gif"
        scale = a.scale or (1 if as_gif else 2)
        doc, w, h = render.to_html(rows, title, cols, a.bg)
        if as_gif:
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                png = render.screenshot(doc, w, h, Path(tmp) / "full.png", scale)
                render.gif(png, rows, cols, out, scale)
        else:
            render.screenshot(doc, w, h, out, scale, transparent=a.bg == "none")
    except (FileNotFoundError, RuntimeError, OSError) as e:
        print(f"codecard: {e}", file=sys.stderr)
        return 1
    print(out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
