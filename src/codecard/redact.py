"""Mask secrets and card numbers before anything is rendered."""
import re
from pathlib import Path

MASK = "••••••"

_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(glpat-)[A-Za-z0-9_-]{20,}"),
    re.compile(r"\b(gh[pousr]_)[A-Za-z0-9]{30,}"),
    re.compile(r"\b(sk-(?:ant-)?)[A-Za-z0-9_-]{20,}"),
    re.compile(r"\b(xox[baprs]-)[A-Za-z0-9-]{10,}"),
    re.compile(r"\b(AKIA)[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/-]{16,}=*"),
]
# NAME_TOKEN=value, "password": "value", API_KEY: value
_ASSIGN = re.compile(
    r"""(?ix)
    (\b[A-Z0-9_]*(?:token|secret|passwd|password|pass|api[_-]?key|apikey|private[_-]?key)[A-Z0-9_]*"?\s*[=:]\s*)
    ("[^"\n]*"|'[^'\n]*'|[^\s,;]+)
    """
)
_PAN = re.compile(r"(?<![\d.])(\d[ -]?){12,18}\d(?![\d.])")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def _mask_pan(m: re.Match) -> str:
    raw = m.group(0)
    digits = re.sub(r"\D", "", raw)
    if not 13 <= len(digits) <= 19 or not _luhn_ok(digits):
        return raw
    return f"{digits[:6]}{'*' * (len(digits) - 10)}{digits[-4:]}"


def redact(text: str, home: str | None = None) -> str:
    """Mask secrets and Luhn-valid card numbers, and show the home directory as ~."""
    home = home or str(Path.home())
    if len(home) > 1:
        text = re.sub(re.escape(home) + r"(?=/|\b)", "~", text)
    for p in _PATTERNS:
        text = p.sub(lambda m: (m.group(1) if m.groups() else "") + MASK, text)

    def _assign(m: re.Match) -> str:
        val = m.group(2)
        q = val[0] if val[:1] in "\"'" else ""
        return f"{m.group(1)}{q}{MASK}{q}"

    text = _ASSIGN.sub(_assign, text)
    return _PAN.sub(_mask_pan, text)
