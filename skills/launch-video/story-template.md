# Story template: cinematic teaser shots + info cards

Default shape for a launch clip announcing a model on your AI gateway or product. ~13-22s,
16:9, 1920x1080, music only (no synced SFX, no voiceover/TTS) — see "Sound" below.

The default look is **real, graded film footage** for the cinematic beats — like Anthropic's
own launch clips — with the data beats (benchmarks, use cases, cost) as dark film-grain
cards, not a flat CSS-gradient background throughout. See `footage.md` for sourcing,
licensing, the MOOD MENU and the grade recipe, and `brand.md` for the brand pack (type and
logo assets). Fall back to a flat CSS-gradient brand card only when no usable,
clearly-licensed footage can be sourced in time — say so if you do.

Adapt beat count to the facts actually supplied — cut a beat rather than pad it, and never
invent a claim to fill time. Every claim shown on screen must trace to `facts.json` (below)
or to the standard mechanical facts (aliases, providers, prompt caching, price) the user gave
directly in chat.

## Beats (the shipped 9-beat structure)

1. **Intro montage** (~3s, **3 shots, no text**) — three quick real-footage cuts (each ~1s),
   no caption anywhere in this beat. Pick footage from the mood menu that fits the model's
   story (`footage.md` MOOD MENU) — e.g. a precision/craft trio (a dial, a piece of
   machinery, another instrument close-up) for a model pitched on rigor, or an
   intelligence/signal trio for one pitched on reasoning. Vary the source/subject across the
   three shots per `footage.md`'s rules (no two adjacent shots from the same film). Same grade
   throughout, pillarboxed 4:3 inside the black 16:9 frame.

2. **Title** (~2.5-3s) — a fourth real footage clip (can be a different sub-range of shot 1's
   clip), one line, large white serif, centered low: the model name (e.g. "Claude Sonnet
   5.5"). No wordmark yet.

3. **Benchmarks** (~4-5s, only if `facts.json` has a `benchmarks` array) — a dark film-grain
   card (a heavily blurred/darkened continuation of the footage, not a flat gradient — see
   footage.md "Card backgrounds"). Serif kicker/row labels, numbers bound from `facts.json` —
   never typed into the HTML by hand. Numbers ≥56px, labels ≥36px at 1080p (brand.md). If no
   sourced benchmark exists yet, render the same scene with the placeholder value `"XX.X%"`
   (or the unit `facts.json` declares) and a small muted "figures pending" tag, so the beat's
   layout/timing can be reviewed before real numbers land. Swap `facts.json` and re-render —
   never edit the number in the scene file. **Only bold/colour a number to imply a win on the
   specific row where the model actually leads** (a `hero: true` row) — don't blanket-colour
   every one of the model's own numbers across every row regardless of whether it actually
   wins that row.

4. **Use cases** (~3-4s, same film-grain card treatment) — one or two rows contrasting this
   model against its sibling (e.g. "Sonnet 5.5 — well-scoped everyday work" / "Opus 5.5 —
   complex work requiring judgment"), sourced from `facts.json.guidance` or from what the user
   stated directly. Skip this beat if no guidance was given — do not invent a use-case split.

5. **Cost** (~3s, same film-grain card treatment) — a price table bound from
   `facts.json.pricing` (input / output / cache-read per 1M tokens), plus a short comparison
   subline ("Half the price of Opus 5.5") and a source line. Never type a number directly into
   the scene HTML.

6. **Generally available** (~2.5s) — back on real footage (a fifth sub-range), a calm, dark,
   wide shot from the chosen mood (e.g. ocean at night, city lights, cloud timelapse, or
   space), one centered line: "Now generally available on `<Product Name>`".

7. **Aliases** (~2.5-3s) — real footage again (a sixth sub-range, same clip/world as beat 6),
   the live gateway alias(es) stacked center, each with its provider name below it (e.g.
   `<alias>` / Amazon Bedrock, `<alias>` / Google Vertex AI — generic examples: `bedrock-sonnet`,
   `vertex-sonnet`). Show only the alias(es) that are actually live — leave out one still
   gated behind an access request (note it in the report instead of putting it on screen).

8. **CTA** (~3-4s) — a calm, dark, wide shot from the chosen mood, a short line, a large
   readable URL, and a subline, from `facts.json.cta` (defaults below). Hold the URL and
   subline long enough to read per motion-video's reading-speed threshold (3 words/s, at least
   0.8s) — extend the scene's duration rather than truncating the copy the user asked for.

9. **End card** (~3-4s) — footage again (a final sub-range, clean — no lens flare or hot spot
   competing with the text), the org's own end-card mark
   (`assets/brand/mark-white.png`, from the brand pack, never a CSS approximation),
   "`<Product Name>`" in bold Inter next to it, and below that "by [org's mark, small
   inline] `<Org> <Team>`" in Inter 500, small.

When sourcing footage for the cinematic beats, pull **more than one sub-range** from the same
clip(s) where you reuse a source — repeating the identical seconds reads as a loop; a few
seconds' offset between beats (and previewing each range for lens flare, glare or a hot spot
that would fight with the text on top) keeps it feeling like one continuous shoot instead of a
repeated clip. Vary sources across beats per `footage.md`'s rules (max one space shot per
clip, no two adjacent shots from the same film).

## Sound

**Music only, no synced SFX** — set `"sfx": false` in `video.json`. Music is user-supplied
only (see SKILL.md "Music"); until a music file exists, render silent. Do not add
motion-video's synthesized SFX cues in this mode.

## Type

**One serif (Newsreader) for body text** — no mixed serif families, no mono for numbers. See
`brand.md`'s single-serif type system for the exact tokens and sizes.

## facts.json contract

Required before beat 3 (benchmarks), beat 4 (use cases) or beat 5 (cost) is built. Missing
file → build beats 1, 2, 6, 7, 8, 9 only, and tell the user which beats are waiting on facts.

```json
{
  "model": "Claude Sonnet 5.5",
  "aliases": ["<alias-1>", "<alias-2>"],
  "providers": ["Bedrock", "Vertex AI"],
  "benchmarks": [
    { "label": "SWE-bench Verified", "value": "XX.X", "unit": "%", "source": "PENDING — official Anthropic release notes" }
  ],
  "guidance": [
    "Reach for Sonnet 5.5 for day-to-day engineering work",
    "Reach for Opus 5.5 when a task needs longer, harder reasoning"
  ],
  "pricing": {
    "sonnet_5_5": { "input_per_1m": 2, "output_per_1m": 10, "cache_read_per_1m": 0.2 },
    "opus_5_5": { "input_per_1m": 4, "output_per_1m": 20, "cache_read_per_1m": 0.4 },
    "currency": "USD"
  },
  "prompt_caching": true,
  "cta": {
    "text": "Building with AI?",
    "url": "<registration-url>",
    "subtext": "Get gateway access for your app"
  }
}
```

**Example** (illustrative only — one clip's actual facts, not the template): a real Sonnet
5.5 launch clip used `benchmarks: Terminal-Bench 4.0 70.6/66.4/10.3 (hero), CursorBench 4.0,
OSWorld 2.1, GDPval-AA v2.1 Elo`, `pricing: Sonnet 5.5 $2/$10, Opus 5.5 $4/$20 per 1M`, and
`guidance: "Opus 5.5 — complex work requiring judgment" / "Sonnet 5.5 — well-scoped everyday
work"`. Don't treat these numbers as defaults for a different model — every figure must come
from that model's own sourced facts.

`cta` is optional and defaults to the placeholder block shown above (register a tool for
gateway access/usage, at `<registration-url>`) — override `text`/`url`/`subtext` with the
brand pack's real values, or when the user gives a different call to action. Omit the whole
`cta` object only if the user explicitly asks for no CTA beat.

- Every `benchmarks[].value` must carry a real `source` (a URL or a named official doc) once
  known. `"source": "PENDING — ..."` is the only acceptable value while waiting — it renders
  as the "figures pending" tag, never as a confident-looking number.
- `guidance` lines are short (fits one line of the type scale) and come from the user or an
  official comparison doc — never inferred from vibes.
- Do not add fields the scene doesn't consume; do not fabricate a `benchmarks` entry with a
  placeholder `source` of your own invention (e.g. "internal estimate") — that's an invented
  claim, which SKILL.md forbids.
