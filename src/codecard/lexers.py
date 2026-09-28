"""Turn raw text into rows of styled tokens.

A row is (row_class, [(token_class, text), ...]). Row classes colour a whole
line (diff add/del); token classes colour spans. Everything downstream works on
this one shape, so wrapping and rendering never care what the input was.
"""
import re

Row = tuple[str, list[tuple[str, str]]]


def wrap(rows: list[Row], cols: int, indent: int = 0) -> list[Row]:
    """Hard-wrap rows at `cols` characters, continuing wrapped lines with `indent` spaces."""
    out: list[Row] = []
    for rcls, toks in rows:
        line: list[tuple[str, str]] = []
        used = 0
        for cls, text in toks:
            while text:
                room = cols - used
                if room <= 0:
                    out.append((rcls, line))
                    line, used = ([("", " " * indent)] if indent else []), indent
                    room = cols - used
                piece, text = text[:room], text[room:]
                line.append((cls, piece))
                used += len(piece)
        out.append((rcls, line))
    return out


# ---- terminal ---------------------------------------------------------------
_TERM = re.compile(
    r"""(?P<st>'[^']*'?|"[^"]*"?)"""
    r"""|(?P<fl>(?<![\w-])--?[A-Za-z][\w-]*)"""
    r"""|(?P<nu>\b\d[\d.]*\b)"""
    r"""|(?P<tx>[^'"\-\d\s]+|\s+|.)"""
)
_COMMENT = re.compile(r"\s#\s")
_PROMPT = re.compile(r"^(\s*)([$>❯%])(\s)")


def _outside_quotes(s: str, i: int) -> bool:
    return s.count("'", 0, i) % 2 == 0 and s.count('"', 0, i) % 2 == 0


def term(text: str) -> list[Row]:
    rows: list[Row] = []
    cont = False  # previous command line ended with \ or left a quote open
    quotes = 0
    for line in text.splitlines():
        toks: list[tuple[str, str]] = []
        comment = ""
        m = _COMMENT.search(line)
        if m and _outside_quotes(line, m.start()) and quotes % 2 == 0:
            line, comment = line[: m.start()], line[m.start():]
        pm = None if cont else _PROMPT.match(line)
        if pm or cont:
            body = line
            if pm:
                toks += [("", pm.group(1)), ("pr", pm.group(2)), ("", pm.group(3))]
                body = line[pm.end():]
                cmd = re.match(r"\S+", body)
                # in a chat prompt (>) only /commands and ! bash mode are "commands"
                if cmd and (pm.group(2) != ">" or cmd.group(0)[0] in "/!"):
                    toks.append(("cm", cmd.group(0)))
                    body = body[cmd.end():]
                quotes = 0
            for mm in _TERM.finditer(body):
                toks.append((mm.lastgroup if mm.lastgroup != "tx" else "", mm.group(0)))
            quotes += line.count("'")
            cont = line.rstrip().endswith("\\") or quotes % 2 == 1
        else:
            toks.append(("out", line))  # command output: plain, slightly dimmed
        if comment:
            toks.append(("co", comment))
        rows.append(("", toks))
    return rows


# ---- diff ---------------------------------------------------------------------
def diff(text: str) -> list[Row]:
    rows: list[Row] = []
    for line in text.splitlines():
        if line.startswith(("diff --git", "index ", "--- ", "+++ ", "new file", "deleted file")):
            rows.append(("meta", [("", line)]))
        elif line.startswith("@@"):
            rows.append(("hunk", [("", line)]))
        elif line.startswith("+"):
            rows.append(("add", [("", line)]))
        elif line.startswith("-"):
            rows.append(("del", [("", line)]))
        else:
            rows.append(("", [("", line)]))
    return rows


# ---- source code (pygments) -----------------------------------------------------
def code(text: str, lang: str | None = None, filename: str | None = None) -> list[Row]:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer
    from pygments.token import Comment, Keyword, Name, Number, Operator, String, Token
    from pygments.util import ClassNotFound

    try:
        if lang:
            lexer = get_lexer_by_name(lang)
        elif filename:
            lexer = get_lexer_for_filename(filename)
        else:
            lexer = guess_lexer(text)
    except ClassNotFound:
        lexer = get_lexer_by_name("text")

    def cls(tt) -> str:
        for base, c in (
            (Comment, "co"), (String, "st"), (Number, "nu"), (Keyword, "kw"),
            (Name.Function, "fn"), (Name.Class, "fn"), (Name.Builtin, "bi"),
            (Name.Decorator, "bi"), (Operator, "op"), (Name.Tag, "kw"), (Name.Attribute, "fl"),
        ):
            if tt in base:
                return c
        return ""

    rows: list[Row] = [("", [])]
    for tt, value in lex(text.rstrip("\n") + "\n", lexer):
        c = cls(tt) if tt is not Token.Text else ""
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i:
                rows.append(("", []))
            if part:
                rows[-1][1].append((c, part.replace("\t", "    ")))
    if rows and not rows[-1][1]:
        rows.pop()
    return rows
