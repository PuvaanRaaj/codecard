# launch-video

Wraps [motion-video-skill](https://github.com/farhan-syah/motion-video-skill) with fixed
cinematic defaults and a brand pack you supply, so "model X is now on our gateway" becomes a
rendered MP4 with at most 1-2 questions. See `SKILL.md` for the workflow, `brand.md` for the
brand pack template (product name, org, logo, accent colour, type), `story-template.md` for
the default beat structure and the `facts.json` contract (no invented benchmark numbers,
ever).

## Install (one-time, per machine)

1. `ffmpeg`/`ffprobe` on PATH: `brew install ffmpeg` (or your platform's package manager).
2. Clone the engine: `git clone https://github.com/farhan-syah/motion-video-skill
   ~/.claude/skills/motion-video`, then `cd ~/.claude/skills/motion-video/scripts && bun
   install` (or `npm install`). Run `node video.mjs doctor` and follow any MISSING line
   (e.g. `bunx playwright install chromium-headless-shell` if no system Chrome/Chromium is
   found).
3. Symlink this skill into `~/.claude/skills` so Claude Code picks it up:
   `ln -s /path/to/launch-video ~/.claude/skills/launch-video`.
4. Create a brand pack (see `brand.md`): product name, org/byline, accent colour, and drop
   `mark-white.png` / `logo-white.png` into a project's `assets/brand/`.

## Usage

> "Claude Sonnet 5.5 is now on our AI gateway — aliases `<alias-1>` and `<alias-2>`, prompt
> caching on, priced $2/$10 per 1M."

The skill gathers facts, asks at most 1-2 questions, then drives motion-video's
`init` → scenes → `check` → `render --draft` → `render` loop into whatever project
directory you point it at (e.g. `<your-video-projects-dir>/sonnet-5.5/`), producing
`out/video.mp4`, `out/thumbnail.png` and `out/sheet.png`.

Benchmark or "when to use X vs Y" claims are never invented — supply them in chat or in a
sourced `facts.json` (see `story-template.md`). Until real figures arrive, those beats render
with an obvious `"XX.X%"` placeholder and a "figures pending" tag.
