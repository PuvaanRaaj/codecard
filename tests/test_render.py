import shutil
import subprocess
import sys

import pytest
from PIL import Image

from codecard import render


def test_geometry_grows_with_rows():
    w, h1 = render.geometry(1, 80)
    _, h5 = render.geometry(5, 80)
    assert h5 - h1 == 4 * render.LH and w > 80 * 9


def test_html_escapes_content():
    doc, _, _ = render.to_html([("", [("st", "<script>x</script>")])], "t<i>", 40)
    assert "<script>x" not in doc and "&lt;script&gt;" in doc and "t&lt;i&gt;" in doc


def _chrome():
    try:
        return render.find_chrome()
    except FileNotFoundError:
        return None


@pytest.mark.skipif(_chrome() is None, reason="no Chrome available")
@pytest.mark.parametrize("gif", [False, True])
def test_cli_renders_png_and_gif(tmp_path, gif):
    out = tmp_path / ("c.gif" if gif else "c.png")
    r = subprocess.run([sys.executable, "-m", "codecard.cli", "term", "-o", str(out)],
                       input="$ echo hi  # say hi\nhi\n", capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    im = Image.open(out)
    w, h = render.geometry(2, 40)
    scale = 1 if gif else 2
    assert im.size == (w * scale, h * scale)
    if gif:
        assert im.n_frames >= 3
