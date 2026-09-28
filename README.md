# codecard

Carbon-style images of **code, terminal sessions, diffs and Claude Code transcripts** — rendered on your machine, driven from the command line, so agents can make them too.

Carbon and ray.so are web UIs for humans, and hosted APIs like Supagist upload your snippet. codecard runs locally (headless Chrome + Pillow): internal code and session logs never leave the laptop, and redaction is on by default.

```bash
codecard code src/app.py -o app.png                 # syntax-highlighted source
codecard term session.txt -o cmds.png --gif          # $ commands, output, # comments — animated
git diff HEAD~1 | codecard diff -o change.png        # +/- coloured diff
codecard transcript -n 1 -o turn.png                 # last turn of this Claude Code session
```

Options: `-t/--title`, `--bg razer|ocean|sunset|grape|none|<css>`, `--cols N`, `--gif`, `--scale N`, `--no-redact`.
`transcript` also takes a session id or `.jsonl` path, `-n/--turns`, `--max-rows`, `--result-lines`.

## Install

```bash
uv tool install ~/programming/codecard      # puts `codecard` on PATH
# Claude skill (so "make an image of this" works):
ln -s ~/programming/codecard/skill ~/.claude/skills/codecard
```

Needs Chrome, Chromium, Edge or Brave. Set `CODECARD_CHROME=/path/to/binary` if it isn't found.

## Safety

- **Redaction on by default:** GitLab/GitHub/Anthropic/Slack/AWS tokens, bearer tokens, JWTs, private keys, `*TOKEN*=` / `*PASSWORD*:` style assignments, Luhn-valid card numbers (masked to first6/last4), and your home directory (shown as `~`). `--no-redact` turns it off.
- **Transcripts** read `~/.claude*/projects/**/<session>.jsonl` (honours `CLAUDE_CONFIG_DIR`). Thinking blocks, subagent sidechains, meta lines and injected `<system-reminder>` text are never rendered. Prompts and tool output are, so look at the image before sharing it.
- Pattern-based redaction catches common formats, not every secret. It's a seatbelt, not a guarantee.

## How it works

Input → rows of styled tokens (`lexers.py`, `transcript.py`) → hard-wrapped to `--cols` → HTML card with a computed height (`render.py`) → one headless-Chrome screenshot → optional GIF made by painting over not-yet-revealed rows (Pillow), so a GIF costs one Chrome call rather than one per frame.

## Develop

```bash
uv sync && uv run --group dev pytest -q
```
