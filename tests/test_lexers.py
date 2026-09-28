from codecard import lexers


def text(row):
    return "".join(t for _, t in row[1])


def test_wrap_preserves_text_and_width():
    rows = [("", [("kw", "abcdef"), ("", "ghij")])]
    out = lexers.wrap(rows, 4)
    assert [text(r) for r in out] == ["abcd", "efgh", "ij"]
    assert all(len(text(r)) <= 4 for r in out)


def test_wrap_indent_on_continuation():
    out = lexers.wrap([("", [("", "aaaaaa")])], 4, indent=2)
    assert [text(r) for r in out] == ["aaaa", "  aa"]


def test_term_prompt_command_flag_comment():
    (_, toks), = lexers.term("$ claude --safe-mode  # all off")
    kinds = {c for c, _ in toks}
    assert {"pr", "cm", "fl", "co"} <= kinds
    assert "".join(t for _, t in toks) == "$ claude --safe-mode  # all off"


def test_term_hash_inside_quotes_is_not_comment():
    (_, toks), = lexers.term("$ echo 'a # b'")
    assert "co" not in {c for c, _ in toks}


def test_term_output_lines_dimmed():
    rows = lexers.term("$ ls\nREADME.md")
    assert rows[1][1] == [("out", "README.md")]


def test_diff_row_classes():
    rows = lexers.diff("diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new\n ctx")
    assert [r[0] for r in rows] == ["meta", "meta", "meta", "hunk", "del", "add", ""]


def test_code_highlights_and_keeps_lines():
    src = "def f(x):\n    return x  # id\n"
    rows = lexers.code(src, lang="python")
    assert [text(r) for r in rows] == ["def f(x):", "    return x  # id"]
    assert "kw" in {c for c, _ in rows[0][1]} and "co" in {c for c, _ in rows[1][1]}


def test_term_continuation_lines_stay_commands():
    rows = lexers.term("$ claude -p \\\n    --json-schema '{\n  \"a\": 1\n}' \\\n  | jq .x\nresult")
    kinds = [{c for c, _ in r[1]} for r in rows]
    assert "fl" in kinds[1]                       # --json-schema after a backslash
    assert "out" not in kinds[2] and "out" not in kinds[3]  # inside the open quote
    assert "out" not in kinds[4]                  # after the second backslash
    assert kinds[5] == {"out"}                    # real output again


def test_chat_prompt_only_highlights_slash_and_bang():
    (_, t1), (_, t2), (_, t3) = lexers.term("> fix that\n> /context\n> ! npm test")
    assert "cm" not in {c for c, _ in t1}
    assert ("cm", "/context") in t2 and ("cm", "!") in t3
