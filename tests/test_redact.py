from codecard.redact import MASK, redact


def test_known_token_prefixes_keep_prefix():
    s = redact("glpat-abcdefghijklmnopqrst12 and ghp_" + "a" * 36)
    assert "glpat-" + MASK in s and "ghp_" + MASK in s
    assert "abcdefghij" not in s


def test_anthropic_and_aws_keys():
    s = redact("sk-ant-api03-" + "x" * 30 + " AKIAABCDEFGHIJKLMNOP")
    assert "xxxxxxxx" not in s and "ABCDEFGHIJKLMNOP" not in s


def test_assignments_masked_quotes_kept():
    assert redact('DB_PASSWORD="hunter2"') == f'DB_PASSWORD="{MASK}"'
    assert redact("API_KEY: abc123") == f"API_KEY: {MASK}"
    assert redact('"access_token": "zzz"') == f'"access_token": "{MASK}"'


def test_bearer_and_jwt():
    s = redact("Authorization: Bearer abcdefghijklmnopqrstuvwx eyJhbGciOiJI.eyJzdWIiOiIx.c2lnbmF0dXJl")
    assert "abcdefghijklmnop" not in s and "eyJhbGciOiJI" not in s


def test_pan_luhn_masked_but_ids_and_amounts_left():
    assert redact("card 4111111111111111 ok") == "card 411111******1111 ok"
    assert redact("tranID 1234567890") == "tranID 1234567890"          # too short
    assert redact("amt 5.0000000000000000") == "amt 5.0000000000000000"  # decimal
    assert redact("id 4111111111111112") == "id 4111111111111112"       # fails Luhn


def test_plain_text_untouched():
    t = "git commit -m 'fix(auth): handle expired refresh token'"
    assert redact(t) == t


def test_home_dir_shown_as_tilde():
    assert redact("cd /Users/alice/code && ls /Users/alicex", home="/Users/alice") == "cd ~/code && ls /Users/alicex"
