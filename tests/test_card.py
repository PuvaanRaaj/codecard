from pathlib import Path

import pytest

from codecard import card, render


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake_shot(doc, w, h, out, scale=2, transparent=False):
        seen["doc"] = doc
        Path(out).write_bytes(b"png")
        return Path(out)

    monkeypatch.setattr(render, "screenshot", fake_shot)
    return seen


def test_render_card_redacts_by_default(tmp_path, captured):
    card.render_card("term", tmp_path / "c.png", text="$ export API_KEY=supersecret123")
    assert "supersecret123" not in captured["doc"]


def test_render_card_no_redact_keeps_text(tmp_path, captured):
    card.render_card("term", tmp_path / "c.png", text="$ export API_KEY=supersecret123", redact_on=False)
    assert "supersecret123" in captured["doc"]


def test_render_card_rejects_unknown_kind(tmp_path):
    with pytest.raises(ValueError):
        card.render_card("pdf", tmp_path / "c.png", text="x")
