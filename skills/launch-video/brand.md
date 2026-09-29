# Brand pack template

A launch clip is only ever built from a **brand pack** the user supplies. This file is the
template for that pack — fill in the fields below (in a project's own `brand.md`, or just
answered inline in chat) before the first render. Nothing in `SKILL.md`,
`story-template.md` or `footage.md` hard-codes a specific company; they all read from
whatever brand pack you provide.

## Fields

| Field | Placeholder | Notes |
|---|---|---|
| **Product name** | `<Product Name>` | e.g. "Acme AI Gateway". Shown on the title/end cards. |
| **Org / byline** | `by <Org> <Team>` | e.g. "by Acme Platform". Shown small, under the product name, on the opening and end card only. |
| **Accent colour** | `<accent-hex>` | One colour, used sparingly (underlines, glows, the CTA). Everything else stays dark/neutral — see "Palette" below. |
| **Logo files** | `assets/brand/mark-white.png`, `assets/brand/logo-white.png` | The user drops their own white/light-variant brand files here. `mark-white.png` is a small icon-only lockup (for an inline byline badge); `logo-white.png` is the full wordmark (for the end card). Never redraw a logo by hand — always start from the org's own brand file. |
| **Headline serif** | Newsreader (default), OFL | Fetched locally with `node video.mjs font "Newsreader"`. Swap for another OFL serif only if the brand pack names one. |
| **Lockup sans** | Inter (default), OFL | Used only for UI-chrome/byline text, never headlines. |

## Palette (dark theme — the video is dark)

Keep the palette minimal: one dark background, one slightly lighter surface, white/off-white
text, and a single accent colour for emphasis. Override these with the brand pack's own
tokens if given; otherwise these are a reasonable generic starting point:

| Token | Example hex | Use |
|---|---|---|
| `--brand` | `<accent-hex>` | primary accent — chips, underline, CTA — the ONE colour used for emphasis |
| `--page` (dark) | `#0d0d0d` | scene background |
| `--surface` (dark) | `#1a1a19` | card/panel background |
| `--rail` (dark) | `#0a0a0a` | deepest background / letterbox |
| `--ink` (dark) | `#ffffff` | primary text |
| `--ink-2` (dark) | `#d6d6d0` | secondary text |
| `--muted` (dark) | `#9a9a92` | tertiary / captions |
| `--line` (dark) | `#2c2c2a` | hairlines, dividers |
| `--good-ink` (dark) | `#4ad489` | positive claims (price, speed) |

If the story needs a second accent per provider (e.g. one chip colour per gateway provider),
add `--series-1`, `--series-2`, ... but keep them scoped to provider chips only — don't let a
second accent leak into headline/body text.

## Logo

- Ask the user for their own white/light-variant brand files, dropped into `assets/brand/`:
  `mark-white.png` (icon-only, for a small inline badge) and `logo-white.png` (full wordmark,
  for the end card). Use the org's own brand file, trimmed of transparent padding — never a
  CSS `filter: grayscale(1) brightness(N)` hack on a colour PNG, and never redraw the mark by
  hand.
- `scripts/make_white_logo.py` recolours a colour logo to white-on-transparent with a soft
  drop shadow, for when the user only has a colour or dark-background variant on hand:
  `python3 scripts/make_white_logo.py <colour-logo.png> assets/brand/logo-white.png`.
- **Byline lockup:** on the opening and end card, show the org's small inline mark followed by
  the byline text — "by [mark-white.png, small inline] `<Org> <Team>`". The product name is a
  separate, larger line (see "End-card lockup rules" below).
- **Animated end card:** if the brand pack includes a logo already split into layers (e.g. a
  mark and a wordmark as separate images), you can build a small entrance animation the same
  way `motion-video` builds any other scene element — sweep/fade/pop the layers in over ~2s,
  then hold. There's no shipped animation component in this skill; build one per-project from
  the user's own layer files if they want that treatment, or keep it simple and just fade in
  the static `logo-white.png` as one image.

## Typography

One serif, one weight, white/off-white only, modest sizes — no mono, no bold, no colour
highlight, no all-caps, anywhere in the video.

- **`--serif`**: `"Newsreader Variable", serif`, **text optical size** (not display) — set
  `font-variation-settings: "opsz" var(--serif-opsz)` with `--serif-opsz: 14`, weight 400
  (never bold), fetched locally with `node video.mjs font "Newsreader"` (OFL). Fall back to
  Source Serif 4 (`node video.mjs font "Source Serif 4"`) only if Newsreader isn't bundled
  locally, or the brand pack names a different OFL serif. Pick the actual value by eye from
  `out/font-specimen.png`, not from memory.
- **Type scale**, defined once in the project's `base.css` `:root` and used everywhere —
  headlines, card rows, aliases, URLs, byline, all the same family/weight, just different
  sizes:
  - `--t-title` — ~70px cap height at 1080p, the one hero line per video (e.g. the model
    name). A longer line that would overflow at this size steps down to `--t-body` instead of
    shrinking further.
  - `--t-body` — ~40px, benchmark rows, aliases, CTA sub-line, longer over-footage headlines.
  - `--t-small` — ~30px, byline, source line.
  - Colour is white or off-white only (`#ffffff` or `#f5f2ea`/similar) — never the accent
    colour on body text; that stays reserved for provider chips / emphasis only, per the
    palette table above.
- **Never**: mono for numbers/aliases/URLs, a second serif family mixed into the same video,
  bold weight for emphasis, or upper-case text. If a number needs to stand out on a benchmark
  row the model actually leads (`hero: true`), that's colour/weight restraint's only
  exception, and even then keep it in `--serif`, not mono.
- The lockup sans (Inter by default) remains available for any UI-chrome beat that isn't part
  of the cinematic look (e.g. a provider-chip label), but is not a headline or body face.

## Tone

Same register as the Anthropic launch-clip reference: confident, spare, one claim per beat,
generous negative space, music only by default (see `SKILL.md` "Sound"), no voiceover. The
default look is real, graded film footage (see `footage.md`) for the emotional/brand beats —
a flat CSS gradient background is a fallback only, for when no usable footage can be sourced
in time, not the first choice.

## End-card lockup rules

- Mark (small, inline) + product name in bold sans, together as one lockup.
- Below that, a small byline line: the org's inline mark + "by `<Org> <Team>`", dimmed
  (`--muted`), well below the claim/CTA text in the type scale — never competing with the
  model name or the alias.
- No URL, no alias, on the end card itself — those belong on the CTA beat just before it.
