import json

from codecard import transcript
from codecard.redact import redact


def write(tmp_path, lines):
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(l) for l in lines) + "\nnot json\n")
    return p


def u(content, **kw):
    return {"type": "user", "message": {"role": "user", "content": content}, **kw}


def a(*blocks, **kw):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}, **kw}


SESSION = [
    u("first question"),
    a({"type": "text", "text": "first answer"}),
    u("<system-reminder>injected</system-reminder>run the tests please"),
    a({"type": "thinking", "thinking": "SECRET THOUGHTS"},
      {"type": "tool_use", "name": "Bash", "input": {"command": "npm test", "description": "Run tests"}}),
    u([{"type": "tool_result", "tool_use_id": "1", "content": "ok 1\nok 2\nok 3\nok 4\nok 5", "is_error": False}]),
    a({"type": "text", "text": "All 5 pass."}),
    a({"type": "text", "text": "sidechain noise"}, isSidechain=True),
    u("meta noise", isMeta=True),
    {"type": "system", "content": "ignored"},
]


def test_events_skip_thinking_sidechain_meta_and_reminders(tmp_path):
    ev = transcript.load_events(write(tmp_path, SESSION))
    blob = json.dumps(ev)
    assert "SECRET THOUGHTS" not in blob and "sidechain noise" not in blob
    assert "meta noise" not in blob and "injected" not in blob
    assert [e["kind"] for e in ev] == ["prompt", "text", "prompt", "tool", "result", "text"]
    assert ev[2]["text"] == "run the tests please"
    assert ev[3] == {"kind": "tool", "name": "Bash", "arg": "npm test"}


def test_last_turns(tmp_path):
    ev = transcript.load_events(write(tmp_path, SESSION))
    assert transcript.last_turns(ev, 1)[0]["text"] == "run the tests please"
    assert transcript.last_turns(ev, 5)[0]["text"] == "first question"


def test_rows_tui_shape_and_result_truncation(tmp_path):
    ev = transcript.last_turns(transcript.load_events(write(tmp_path, SESSION)), 1)
    rows = transcript.to_rows(ev, cols=80, result_lines=3)
    flat = ["".join(t for _, t in r[1]) for r in rows]
    assert flat[0] == "> run the tests please"
    assert flat[1] == "● Bash(npm test)"
    assert flat[2] == "  ⎿  ok 1" and flat[4] == "     ok 3"
    assert flat[5] == "     … +2 lines"
    assert flat[6] == "● All 5 pass."


def test_redaction_applies_to_transcript(tmp_path):
    ev = transcript.load_events(write(tmp_path, [u("my token is glpat" + "-abcdefghijklmnopqrstuv")]))
    flat = "".join(t for r in transcript.to_rows(ev, 80, redact=redact) for _, t in r[1])
    assert "abcdefghijklmnop" not in flat


def test_find_session_by_explicit_path(tmp_path):
    p = write(tmp_path, SESSION)
    assert transcript.find_session(str(p)) == p



def test_cap_rows_starts_on_a_block_and_counts_dropped(tmp_path):
    ev = transcript.last_turns(transcript.load_events(write(tmp_path, SESSION)), 1)
    rows = transcript.to_rows(ev, 80)                    # 7 rows, rows[-3] is a result continuation
    capped = transcript.cap_rows(rows, 4)
    first = "".join(t for _, t in capped[1][1])
    assert first.startswith(("●", ">"))
    assert capped[0][1][0][1] == f"… {len(rows) - (len(capped) - 1)} earlier rows"
    assert transcript.cap_rows(rows, 100) == rows


def test_prose_wraps_on_word_boundaries(tmp_path):
    ev = transcript.load_events(write(tmp_path, [a({"type": "text", "text": "alpha beta gamma delta epsilon"})]))
    flat = ["".join(t for _, t in r[1]) for r in transcript.to_rows(ev, cols=16)]
    assert flat == ["● alpha beta", "  gamma delta", "  epsilon"]
