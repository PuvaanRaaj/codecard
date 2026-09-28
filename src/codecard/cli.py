"""codecard CLI. Prints the written file path on stdout, errors on stderr."""
import argparse
import sys
from pathlib import Path

from . import render
from .card import render_card


def _read(src: str | None) -> tuple[str, str | None]:
    if not src or src == "-":
        if sys.stdin.isatty():
            sys.exit("codecard: no input — pass a file or pipe text on stdin")
        return sys.stdin.read(), None
    p = Path(src).expanduser()
    return p.read_text(encoding="utf-8", errors="replace"), p.name


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

    try:
        kw = dict(title=a.title, bg=a.bg, cols=a.cols, gif=a.gif, scale=a.scale, redact_on=not a.no_redact)
        if a.kind == "transcript":
            kw.update(session=a.session, turns=a.turns, max_rows=a.max_rows, result_lines=a.result_lines)
        else:
            kw["text"], kw["name"] = _read(a.input)
            if a.kind == "code":
                kw["lang"] = a.lang
        out = Path(a.out or f"codecard-{a.kind}.{'gif' if a.gif else 'png'}")
        path = render_card(a.kind, out, **kw)
    except (FileNotFoundError, RuntimeError, OSError, ValueError) as e:
        print(f"codecard: {e}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
