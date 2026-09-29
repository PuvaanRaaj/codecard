---
name: launch-video
description: Make a short Anthropic-style cinematic launch clip announcing a model on your AI gateway or product, using real public-domain footage, a brand pack and music you supply. Triggers on "make a launch video for model X on the gateway", "announcement clip for <model> on <product>", "launch clip", "gateway launch video".
---

# launch-video — cinematic model launch clips

Wraps `motion-video` (cloned at `~/.claude/skills/motion-video`, its own workflow in its own
SKILL.md) with fixed defaults and a user-supplied brand pack, so a "model X is now on
`<product>`" ask turns into a rendered MP4 with at most 1-2 clarifying questions.

**Default look: real, graded film footage** for the opening/closing beats, like Anthropic's
own launch clips — not a flat CSS gradient. See `footage.md` (sourcing + licensing + grade
recipe), `brand.md` (the brand pack template — product name, org, logo, accent colour,
type) and `story-template.md` (the beat shape) before building. A flat gradient card is a
documented fallback only, for when no usable footage can be sourced in time.

Do not add video generation to `codecard` itself — this skill calls codecard's CLI (`uv run
codecard ...` from `~/programming/codecard`) as a subprocess to render one code-shot PNG, and
imports that PNG as a scene asset. Everything else is motion-video.

## Setup (one-time, per machine)

1. Install `ffmpeg`/`ffprobe` (`brew install ffmpeg` or your platform's package manager).
2. Clone the rendering engine: `git clone https://github.com/farhan-syah/motion-video-skill
   ~/.claude/skills/motion-video`, then `cd ~/.claude/skills/motion-video/scripts && bun
   install` (or `npm install`). Run `node video.mjs doctor` and follow any MISSING line.
3. Symlink or copy this skill into `~/.claude/skills/launch-video` so Claude Code picks it up.
4. Create a brand pack (see `brand.md`): product name, org/byline, accent colour, and drop
   `mark-white.png` / `logo-white.png` into a project's `assets/brand/`.

## 1. Gather facts — before touching motion-video

Collect, from the user's message (never invent):
- **Model name** (e.g. "Claude Sonnet 5.5").
- **Provider(s)** it's served from (e.g. Bedrock, Vertex AI).
- **Gateway alias(es)** (e.g. `<alias>` — generic examples: `vertex-sonnet`, `bedrock-sonnet`).
- **1-3 claims, each with a source.** Acceptable claims with no external source needed:
  aliases, providers, prompt caching on/off, price per 1M tokens — these come straight from
  what the user told you. Anything else (benchmark scores, "N% faster", "N% cheaper" as a
  comparative claim, "use X over Y for..." guidance) requires either the user's own words in
  chat, or a **sourced facts file** (`facts.json`, see `story-template.md` §facts.json
  contract) with a real citation per figure.
- **Never invent or recall a benchmark number from training knowledge.** If the user wants a
  benchmark or "when to use X vs Y" beat and hasn't supplied a sourced fact for it yet: build
  every other beat now, render the benchmark/guidance beat with the placeholder value
  `"XX.X%"` (or whatever unit applies) and a small "figures pending" tag, and tell the user
  those beats are waiting on `facts.json`. Re-render once it arrives — never hand-edit a
  number into a scene file.

## 2. Ask, at most 1-2 questions

Everything else is a fixed default — don't ask about aspect ratio, duration, voice, or the
craft rules:
- **Aspect / size:** 16:9, 1920x1080. Fixed.
- **Duration:** ~13-20s depending on how many beats the facts support. Fixed budget, not
  asked.
- **Sound:** music only. Set `"sfx": false` in `video.json` (no whooshes, pops or cut
  sounds; no `data-sfx` attributes in scenes) and mix a cinematic track at `volume` 0.25,
  landing its swell on the end card. No voiceover/TTS ever (skip motion-video's Voice
  workflow step entirely). There is no default track shipped with this skill — the music is
  always a track the user supplies, with its licence recorded (see "Music" below).
- **Brand:** from the brand pack the user provides — see `brand.md`. If no brand pack exists
  yet, ask for it once (product name, org/byline, accent colour, logo files) rather than
  guessing.
- **Byline:** "by [org's mark, small inline] `<Org> <Team>`" on the end card only, Inter 500,
  small and dimmed, under the product-name lockup. Fixed.
- **CTA beat:** a beat just before the end card, pointing at `<registration-url>` for
  gateway access/usage. Defaults to the placeholder copy in `story-template.md`'s
  `facts.json` contract — only ask if the user wants different CTA copy/URL or none at all.

Only ask when the facts are genuinely ambiguous or incomplete for a beat the user clearly
wants (e.g. they mention "benchmarks" but gave no numbers or facts file — ask once whether to
render with placeholders now or wait for `facts.json`).

## 3. Source footage — before touching motion-video

**Pick footage from the mood menu that fits the model's story — don't default to space.**
`footage.md`'s MOOD MENU (precision/craft, speed/scale, intelligence/signal, human/craft,
nature/scale, city/light, space) maps a story to search terms; space footage is one option
among several, capped at one shot per clip unless the brief is explicitly about space.

Per `footage.md`: search across NASA, Internet Archive (Prelinger and general movies),
Wikimedia Commons, Library of Congress, and — only if the user has exported
`PEXELS_API_KEY`/`PIXABAY_API_KEY` in their own shell — Pexels/Pixabay
(`scripts/fetch_footage.py search <source> "<query>"` or `--mood <mood>`, no API key required
for the first four). Keep only clips with confirmed public-domain/CC0/CC BY/CC BY-SA licence
evidence (the source table in `footage.md` gives the exact rule per source), download only the
video files, and never execute anything downloaded. Vary sources and subjects across a clip's
shots — no two adjacent shots from the same film/source item. Preview candidates with ffmpeg
contact sheets before committing to an in/out range (watch for burned-in captions throughout,
dissolves at the range's start that would make a bad frame-0 thumbnail, and lens flare/hot
spots that will fight with text later). Cut and grade each chosen range straight into the
project's `assets/footage/` with `scripts/grade_footage.sh` (or `fetch_footage.py grade`), and
write `assets/footage/credits.json`: one entry per clip with source URL, title, the exact
licence evidence, and the in/out timestamps used. A CC BY/CC BY-SA clip's credit line goes in
`credits.json` **and** in the post/share text that goes out with the video. If nothing with a
clear licence fits a beat, use the closest licensed alternative and say so in the report —
never fake it with CSS.

## 4. Drive motion-video

From the target directory (e.g. `<your-video-projects-dir>/<model-slug>/`):

1. `node ~/.claude/skills/motion-video/scripts/video.mjs doctor <dir>` — confirm READY, note
   any LIMIT.
2. `node .../video.mjs init <dir>` (run from the parent, target `<dir>`; refuse if `<dir>`
   is not empty — pick a fresh subdirectory instead).
3. `node .../video.mjs font "Newsreader"` — fetches the OFL body/headline serif locally
   (`brand.md`'s single-serif system; fall back to `font "Source Serif 4"` only if Newsreader
   isn't bundled locally). Copy the user's `assets/brand/logo-white.png` (full wordmark) and
   `assets/brand/mark-white.png` (end-card/inline mark) into the project — see `brand.md`
   "Logo".
4. Write `<dir>/direction.md`: one concept (not three — the concept is fixed by
   `story-template.md`), naming the beats this render will actually include, their facts,
   footage sources, and the sonic concept ("music only from `assets/music/<file>`, swell on
   the end card; no SFX, no voice").
5. Build scenes per beat in `story-template.md`, using `brand.md` tokens/type and the graded
   clips from `assets/footage/` (imported via motion-video's own `footage` command — never a
   raw `<video>` tag). Bind any benchmark/guidance numbers from `facts.json` — never type a
   number directly into scene HTML. Respect the minimum type sizes in `brand.md`.
6. For the optional code-shot beat: write a short snippet (curl or OpenAI SDK) calling
   `https://<gateway-host>/v1/chat/completions` with the model set to the primary gateway
   alias and `Authorization: Bearer $GATEWAY_KEY` (placeholder only — never a real key), then
   `cd ~/programming/codecard && uv run codecard code <snippet> -o <dir>/assets/call.png
   --bg none -t "<model> on <Product Name>"`. Import `<dir>/assets/call.png` into the code
   shot scene. This is not one of the default 9 beats in `story-template.md` — only add it as
   an extra beat (before the CTA) when the user specifically wants the call demonstrated, or
   the clip has room to breathe; it competes with the aliases beat for "how do I call it", so
   drop it under a tight budget.
7. `check --scene N` after each scene; fix findings against motion-video's `references/craft.md`
   thresholds before moving on. A "scene opens near-empty: shapes cover 0.0%" warning on a
   footage-only scene is a known checker limitation (it doesn't count a full-bleed `<img
   data-frames>` as a shape) — confirm visually via the scene's still sheet that the footage
   actually fills the frame from frame 0, then treat the warning as accepted, not a bug to
   chase.
8. `render --draft`, review `out/sheet.png`, fix, then full `render`.
9. Open `out/sheet.png` and `out/thumbnail.png` — the
   thumbnail is frame 0 of scene 1, so if it lands on a source dissolve/transition, shift that
   scene's footage in-point later until frame 0 is a clean, legible still. Verify with
   `ffprobe`: duration in the 13-20s budget (up to ~22s if a CTA line needed more reading
   time), 1920x1080, one audio stream carrying the music (`volumedetect` on `out/stems/music.wav` is
   non-empty; there's no fresh effects stem because `sfx` is false), and **no rotation flag**
   (`-show_entries stream_side_data=rotation` prints nothing). Tell the user to play
   `video-compressed.mp4` and not to press ⌘R/⌘⇧R in QuickTime: it saves a 180° flag into
   the file.
10. Report the master `out/video.mp4`, `-compressed.mp4`, `out/thumbnail.png`, `out/sheet.png`,
    the chosen footage clips with their licence evidence (from `assets/footage/credits.json`),
    and which beats used placeholder figures pending `facts.json`.

## Never

- Never invent a benchmark number, percentage, or "vs <other model>" claim not sourced from
  the user or a `facts.json` entry with a real citation.
- Never colour/bold a model's number on every benchmark row to imply it always wins — only on
  the row(s) it actually leads (`hero: true`).
- Never add a voice track — this format has no voiceover/TTS.
- Never add music the user did not supply, and never fetch/download music from YouTube or any
  other source on the user's behalf — music is user-supplied only, dropped into
  `assets/music/` by them (see "Music" below).
- Never add video-rendering code to codecard itself; call its CLI as a subprocess.
- Never write a real API key into the code-shot snippet — `$GATEWAY_KEY` only.
- Never fetch footage from Pexels/Pixabay without a user-exported `PEXELS_API_KEY`/
  `PIXABAY_API_KEY` in the shell (never read from a `.env` file), or from any source without a
  confirmed public-domain/CC0/CC BY/CC BY-SA item (see `footage.md`'s source table for the
  exact rule per source); never execute a downloaded file.
- Never fake real footage with a CSS gradient/pattern when the brief or the user asks for real
  footage — source an actual clip, or say plainly that none could be found in time.
- Never approximate the white logo with a CSS `grayscale`/`brightness` filter on the colour
  PNG — use the brand pack's pre-made white asset (or regenerate it with `make_white_logo.py`).

## Music (user-supplied only)

Music is never picked by this skill on its own — there is no shipped default track. Use
whichever track the user names, with its licence recorded in `credits.json` (see step 5
below). One example of how to credit a free-with-attribution track: the Infraction "Cinematic
Documentary Violin" track requires a credit line in the post/share text if used — treat any
similar free-with-attribution track the same way. When the user names a track, prefer the
artist's official download (e.g. the link in the video description, or the label's own site)
over ripping a platform copy, read its licence terms first, and don't use a file from an
unlicensed MP3 site or a label-released song ("Various Artists - Topic" on YouTube) without a
licence the user can point to.

Once a music file exists:

1. Copy it into `<dir>/assets/music/` if it isn't already there.
2. Set `video.json`: `"music": { "file": "assets/music/<name>", "volume": 0.25, "start": <s> }`,
   and raise `sound.fadeIn` to about `1.0` and `sound.fadeOut` to cover the last scene, so the
   whole mix fades the music in over ~1s and out at the end (motion-video applies these to the
   whole mix; there's no separate per-track fade knob — with no voice and sparse SFX this reads
   as the music fading).
3. Run `node .../video.mjs beats --start <rough-s>` (`references/cli.md`, `beats`). It prints
   the bpm, key, downbeats and bar energy in video-relative time, and tells you the nearest
   on-grid `music.start` to snap to a downbeat. Use the bar-energy list to find a build/swell
   and land it on the brand or end-card beat, and set `music.start` to the on-grid value it
   suggests.
4. Analyze the chosen in/out window with `ffprobe`/`ffmpeg` (`volumedetect`, a `showwavespic`
   or `showspectrumpic` contact sheet) before committing: a preview/promo file
   (often named `-pr`/`-preview`) can carry a spoken watermark tag or have structural dropouts
   elsewhere in the track. A spoken tag shows as a wide, dense, broadband smudge unlike the
   thin, pitched, periodic lines of an instrument; a dropout shows as a flat silent block in
   the waveform. If either lands inside your chosen window, shift the window or fall back to
   whichever alternate copy of the track the user supplied.
5. Add a `music` object to `assets/footage/credits.json` (same file as the footage credits):
   `file`, `title`, `artist`, `source_url`, `licence`, `attribution_required`, `credit_line`,
   and the in/out window used.
6. If `attribution_required` is true, put `credit_line` in the post/share text that goes out
   with the video — never only in `credits.json`. If the licence is free-use-with-credit but
   doesn't cover the video's actual distribution (e.g. it needs a paid subscription for
   external/commercial use and this clip is going external), say so plainly in the report
   instead of guessing.
7. Re-render (`render --draft` then `render`) and confirm with `ffprobe`/`out/stems/music.wav`
   that the music stem is non-empty and the mix lands around -14 LUFS.
