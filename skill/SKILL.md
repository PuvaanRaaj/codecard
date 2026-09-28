---
name: codecard
description: Make carbon-style images (PNG or animated GIF) of code, terminal sessions, diffs, or the last turns of this Claude Code session, rendered locally with codecard — nothing is uploaded. Use when the user asks to "make an image of this", "screenshot this code", "carbon this", "make a card for the post", "turn this session into an image", "gif of this terminal", or wants visuals for a post, slide, MR or chat message.
---

# codecard — local carbon-style cards

CLI: `codecard <code|term|diff|transcript> [input] -o out.png|out.gif [-t title] [--bg razer|ocean|sunset|grape|none] [--cols N] [--gif]`.
Prints the absolute output path on success; errors go to stderr with exit 1.

## Pick the kind
| Content | Command |
|---|---|
| Source file or snippet | `codecard code path/to/file.py -o card.png` (language from filename; `-l` to force) |
| Commands + output + `# comments` | write lines to a temp file, `codecard term cmds.txt -o card.png` (`$ ` / `> ` lines are commands, others are output) |
| A change | `git diff <range> -- <paths> \| codecard diff -o change.png -t "<what changed>"` |
| What we just did in this session | `codecard transcript -n 1 --max-rows 24 -o turn.png` (newest session for the cwd; pass an id or `.jsonl` path for another) |
| Animated | add `--gif` (line-by-line reveal); keep it under ~20 rows |

## Rules
- **Redaction is on by default** (tokens, `KEY=value` secrets, JWTs, Luhn-valid card numbers, home dir → `~`). Never pass `--no-redact` for anything that will be shared.
- Transcripts never include thinking, subagent sidechains or injected system reminders — but they do include prompts and tool output. Read the image before handing it over and ask if anything internal (hostnames, customer data) is visible.
- Keep cards readable: trim snippets to the lines that matter, `--cols 70-90`, <= ~30 rows. Split long content into several cards rather than one huge one.
- **Always view the result** with the Read tool before reporting it done; fix clipping or awkward wrapping with `--cols` or by trimming input.
- Report the output path(s) so the user can drag them into the post.
