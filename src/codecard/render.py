"""Rows -> HTML card -> PNG (headless Chrome) -> optional line-reveal GIF (Pillow).

Heights are computed, not measured: monospace font, fixed line height, rows
already hard-wrapped. That keeps Chrome to a single screenshot per card.
"""
import html
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .lexers import Row

LH, PAD, BAR, CODEPAD_Y, CODEPAD_X, FONT_PX, CH_EM = 26, 56, 44, 26, 30, 16, 0.61
WIN_BG = (21, 23, 28)

BACKGROUNDS = {
    "razer": "linear-gradient(135deg,#0b3d0b 0%,#1f7a1f 45%,#44d62c 100%)",
    "ocean": "linear-gradient(135deg,#0f2027 0%,#203a43 50%,#2c5364 100%)",
    "sunset": "linear-gradient(135deg,#ff5f6d 0%,#ffc371 100%)",
    "grape": "linear-gradient(135deg,#41295a 0%,#2f0743 100%)",
    "none": "transparent",
}

CSS = """
.pr{color:#6b7280} .cm{color:#44d62c;font-weight:600} .fl{color:#f5c26b} .st{color:#9ecbff}
.kw{color:#ff79c6} .nu{color:#ff9e64} .co{color:#6b7280;font-style:italic} .fn{color:#82aaff}
.bi{color:#7fdbca} .op{color:#c792ea} .out{color:#b8bcc4}
.l.add{background:rgba(46,160,67,.22);color:#aff5b4} .l.del{background:rgba(248,81,73,.20);color:#ffc1bd}
.l.hunk{color:#79c0ff} .l.meta{color:#8b949e;font-weight:600}
.l.prompt{color:#fff} .user{color:#fff} .dot{color:#e6e6e6} .tdot{color:#44d62c}
.tool{color:#fff;font-weight:700} .targ{color:#b8bcc4} .res{color:#8b949e} .err{color:#ff7b72}
"""


def geometry(n_rows: int, cols: int) -> tuple[int, int]:
    code_w = math.ceil(cols * CH_EM * FONT_PX)
    w = PAD * 2 + CODEPAD_X * 2 + code_w + 8
    h = PAD * 2 + BAR + CODEPAD_Y * 2 + max(n_rows, 1) * LH
    return w, h


def to_html(rows: list[Row], title: str, cols: int, bg: str = "razer") -> tuple[str, int, int]:
    w, h = geometry(len(rows), cols)
    body = "".join(
        f'<div class="l {html.escape(rc)}">'
        + ("".join(f'<span class="{c}">{html.escape(t)}</span>' if c else html.escape(t) for c, t in toks) or "&nbsp;")
        + "</div>"
        for rc, toks in rows
    )
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
body{{background:{BACKGROUNDS.get(bg, bg)};display:flex;align-items:center;justify-content:center}}
.win{{width:{w - PAD * 2}px;background:rgb{WIN_BG};border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.55);overflow:hidden}}
.bar{{height:{BAR}px;display:flex;align-items:center;padding:0 18px;gap:8px;position:relative}}
.d{{width:13px;height:13px;border-radius:50%}}
.t{{position:absolute;left:0;right:0;text-align:center;color:#8a8f98;font:500 14px -apple-system,"Segoe UI",sans-serif}}
.code{{padding:{CODEPAD_Y}px {CODEPAD_X}px;font:{FONT_PX}px/{LH}px "SF Mono",Menlo,Consolas,monospace;color:#e6e6e6;white-space:pre}}
.l{{margin:0 -{CODEPAD_X}px;padding:0 {CODEPAD_X}px}}
{CSS}</style></head><body><div class="win"><div class="bar">
<span class="d" style="background:#ff5f57"></span><span class="d" style="background:#febc2e"></span><span class="d" style="background:#28c840"></span>
<span class="t">{html.escape(title)}</span></div><div class="code">{body}</div></div></body></html>"""
    return doc, w, h


def find_chrome() -> str:
    env = os.environ.get("CODECARD_CHROME")
    if env:
        return env
    for p in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ):
        if os.path.exists(p):
            return p
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        if shutil.which(name):
            return shutil.which(name)
    raise FileNotFoundError("no Chrome/Chromium found; set CODECARD_CHROME to its binary")


def screenshot(doc: str, w: int, h: int, out: Path, scale: int = 2, transparent: bool = False, timeout: float = 60) -> Path:
    """Screenshot `doc` with headless Chrome.

    Some Chrome builds write the PNG and then never exit, so success is "file
    written and stable", after which the process is killed.
    """
    out = out.resolve()
    out.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(doc, encoding="utf-8")
        cmd = [find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--no-first-run", "--no-default-browser-check",
               f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
               f"--screenshot={out}", page.as_uri()]
        if transparent:
            cmd.insert(1, "--default-background-color=00000000")
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        deadline, last = time.monotonic() + timeout, -1
        try:
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    break
                size = out.stat().st_size if out.exists() else -1
                if size > 0 and size == last:
                    break
                last = size
                time.sleep(0.3)
        finally:
            if proc.poll() is None:
                proc.kill()
            _, err = proc.communicate()
        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError(f"chrome did not write {out}: {(err or '').strip()[-400:]}")
    return out


def gif(png: Path, rows: list[Row], cols: int, out: Path, scale: int, line_ms: int = 280, hold_ms: int = 2500) -> Path:
    """Reveal the card one row at a time by painting over the rows not yet shown."""
    from PIL import Image, ImageDraw

    full = Image.open(png).convert("RGB")
    w, _ = geometry(len(rows), cols)
    x0, x1 = (PAD + 1) * scale, (w - PAD - 1) * scale
    top = (PAD + BAR + CODEPAD_Y) * scale
    bottom = top + len(rows) * LH * scale
    palette = full.quantize(colors=255, method=Image.Quantize.MAXCOVERAGE)

    frames, durations = [], []
    shown = 0
    while shown <= len(rows):
        f = full.copy()
        if shown < len(rows):
            d = ImageDraw.Draw(f)
            y = top + shown * LH * scale
            d.rectangle([x0, y, x1, bottom], fill=WIN_BG)
            cx = (PAD + CODEPAD_X) * scale
            d.rectangle([cx, y + 4 * scale, cx + 9 * scale, y + (LH - 4) * scale], fill=(68, 214, 44))
        frames.append(f.quantize(palette=palette, dither=Image.Dither.NONE))
        durations.append(hold_ms if shown == len(rows) else line_ms)
        shown += 1
        while shown < len(rows) and not "".join(t for _, t in rows[shown - 1][1]).strip():
            shown += 1  # blank rows appear together with the next line
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    return out
