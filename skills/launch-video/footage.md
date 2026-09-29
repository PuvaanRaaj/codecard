# Real footage: sourcing, licensing and grade

Default look as of the Sonnet 5.5 v3 rework: launch clips open and close on real, graded
film footage (like Anthropic's own launch clips), not a CSS gradient. Info cards (benchmarks,
pricing) still exist, but sit on a blurred/darkened continuation of the same footage instead
of a flat brand-colour background.

**Don't default to space.** NASA/ISS footage is one mood among several (see MOOD MENU below),
not the house look — vary sources and subjects clip to clip, per the rules below.

## Sourcing

| Source | Licence rule | Attribution needed? | How to search |
|---|---|---|---|
| **NASA Image and Video Library** | Generally public domain per NASA media usage guidelines. Never include NASA insignia/logos in frame; no endorsement implied. | No | `fetch_footage.py search nasa "<query>"` — `images-api.nasa.gov/search?q=<query>&media_type=video`, then `/asset/<nasa_id>` for files. |
| **Internet Archive — Prelinger** | Keep only items with an explicit `licenseurl` field (e.g. `.../publicdomain/`). No `licenseurl` = not confirmed — skip or verify by hand on the item page. | No (PD) | `fetch_footage.py search prelinger "<query>"` — `advancedsearch.php?q=collection:prelinger AND (<query>)`. |
| **Internet Archive — general movies** | Same `licenseurl` rule, but kept to `publicdomain` / `CC0` / `CC BY` only (no BY-SA/NC/ND) since these aren't curated the way Prelinger is. | CC BY hits: yes, credit the uploader | `fetch_footage.py search archive "<query>"` — `mediatype:movies AND licenseurl:*`, filtered client-side. |
| **Wikimedia Commons** | Kept only if `extmetadata.LicenseShortName` is exactly Public domain, CC0, CC BY, or CC BY-SA. Anything else (NC, ND, unclear) is dropped automatically. | CC BY / CC BY-SA: yes — `Artist + LicenseShortName` | `fetch_footage.py search wikimedia "<query>"` — MediaWiki API `list=search` in the File: namespace, filtered to webm/ogv/mp4, then `prop=imageinfo` for licence + resolution. |
| **Library of Congress (film & video)** | Kept only if the item's `rights` field says "no known restrictions" or "public domain". | No | `fetch_footage.py search loc "<query>"` — `loc.gov/film-and-videos/?q=<query>&fo=json`. **Known issue:** loc.gov puts scripted requests behind a Cloudflare bot challenge (403 "Just a moment..."), so this source currently fails from an automated script even with a normal `User-Agent`. The code path is kept (in case that changes, or for a browser-driven manual check), but treat it as unavailable for now and say so in the report. |
| **Pexels stock video** | Pexels License: free to use, no attribution required. | No | Only runs if `PEXELS_API_KEY` is exported in the user's own shell env (`os.environ`, never a `.env` file) — `fetch_footage.py search pexels "<query>"`. Silently skipped (prints `{"skipped": ...}`) if the key is absent. |
| **Pixabay stock video** | Pixabay Content License: free to use, no attribution required. | No | Same as Pexels: only runs with `PIXABAY_API_KEY` in the shell env, silently skipped otherwise. |

`scripts/fetch_footage.py` wraps every search, a `--mood` helper (below), and the download
step:

```
python3 scripts/fetch_footage.py search nasa "cupola earth"
python3 scripts/fetch_footage.py search prelinger "tachometer OR gauge OR dial"
python3 scripts/fetch_footage.py search archive "ocean waves slow motion"
python3 scripts/fetch_footage.py search wikimedia "radio telescope"
python3 scripts/fetch_footage.py search loc "switchboard operators"
python3 scripts/fetch_footage.py search pexels "city skyline night"     # needs PEXELS_API_KEY
python3 scripts/fetch_footage.py search pixabay "aurora timelapse"     # needs PIXABAY_API_KEY

# mood instead of typing your own query
python3 scripts/fetch_footage.py search wikimedia --mood precision
python3 scripts/fetch_footage.py search --source archive --source wikimedia --mood intelligence

python3 scripts/fetch_footage.py download nasa <nasa_id> -o /tmp/clip.mp4
python3 scripts/fetch_footage.py download prelinger <archive_id> -o /tmp/clip.mp4 --file <name>
python3 scripts/fetch_footage.py download archive <archive_id> -o /tmp/clip.mp4 --file <name>
python3 scripts/fetch_footage.py download wikimedia "<File title>" -o /tmp/clip.mp4
python3 scripts/fetch_footage.py download loc <item_id> -o /tmp/clip.mp4
python3 scripts/fetch_footage.py download pexels <video_id> -o /tmp/clip.mp4
python3 scripts/fetch_footage.py download pixabay <video_id> -o /tmp/clip.mp4
```

Never execute a downloaded file. Preview candidate footage with `ffmpeg -vf fps=... ` contact
sheets (sample frames, tile them, `Read` the tile) before committing to a range — vintage
prints often dissolve between title cards and the clip you want; step past the dissolve so
the shot's first second (and the video's frame 0, if it's the opening scene) is already clean.

## MOOD MENU

Pick footage that matches the model's story, not always space. `--mood` expands one of these
into search terms for you; you can also just search a term from the list by hand.

- **precision / craft** — clockwork, watchmaking, machining, lathes, typewriters
- **speed / scale** — trains, jets, highways at night, rocket launches
- **intelligence / signal** — radio telescopes, switchboards, vintage computers, oscilloscopes,
  data centres
- **human / craft** — hands at work, labs, drafting tables
- **nature / scale** — ocean waves, clouds timelapse, forests, aurora
- **city / light** — skylines, neon, traffic trails
- **space** — Earth from orbit, ISS cupola, rocket launch. **Max ONE shot per clip** unless the
  brief is explicitly about space.

### Rules

- Vary sources and subjects — don't pull every shot in a clip from the same archive or the
  same handful of "cool space b-roll" clips.
- At most one NASA/space shot per clip, unless the brief is explicitly about space.
- No two adjacent shots from the same film/source item — cut to a different clip before
  returning to one already used.
- Prefer the highest resolution available among licence-clean candidates.
- CC BY / CC BY-SA clips need their credit both in `assets/footage/credits.json` **and** in
  the post/share text that goes out with the video — never only in the credits file.

## Licence log

Every clip that ends up in a project's `assets/footage/` gets an entry in
`assets/footage/credits.json`: source URL, title, the exact licence field/evidence, and the
in/out timestamps used. If a shot can't be found with a clear PD/CC0/CC BY licence, use the
closest licensed alternative and say so in the report — never fake it with CSS instead.

## Grade recipe (shared, `scripts/grade_footage.sh`)

```
eq=contrast=1.08:saturation=0.96:brightness=0.0,
colorbalance=rs=-0.09:gs=0.02:bs=0.11:rm=0.02:gm=0.0:bm=0.02:rh=0.09:gh=0.0:bh=-0.06,
curves=r='0/0.02 0.5/0.51 1/0.97':b='0/0.02 0.5/0.48 1/0.9',
vignette=PI/3.2,
noise=alls=14:allf=t+u
```

— teal shadows, warm highlights, a soft vignette, visible grain. Crop/scale to a 4:3 picture
(1440x1080) *before* the grade, then pad it into the 1920x1080 black frame after
(`pad=1920:1080:(1920-1440)/2:0:color=black`) for the pillarbox. `grade_footage.sh <crop-or-empty>
<in> <out>` runs the whole chain; pass an empty first argument when the source is already 4:3
(no crop needed, just the implicit scale you add yourself), or a `crop=...`/`scale=...`
fragment when it isn't.

**Card backgrounds** (behind benchmark/pricing numbers): reuse the same footage, but blur it
past recognizability and darken it hard so it reads as an abstract film-grain field, not a
second "shot": `scale` up, `gblur=sigma=22`, `eq=... :saturation=0.55:brightness=-0.22`, a
milder `colorbalance`/`vignette`/`noise`, no pillarbox (full-bleed, edge to edge — it's a
background, not a framed shot). Add a `radial-gradient` scrim `<div>` over it in the scene
for extra text contrast; don't rely on the footage grade alone.

## Importing into a scene

Use motion-video's own `footage` command (`references/building.md` in motion-video), never a
raw `<video>` tag (forbidden by the render's seek contract):

```
node ~/.claude/skills/motion-video/scripts/video.mjs footage assets/footage/<clip>.mp4 \
  --name <scene-asset-name> --from 0 --to <seconds>
```

prints an `<img data-frames="../assets/<name>" data-count="N" data-fps="30" data-at="0">` tag
— style that `<img>` like any full-bleed image (`position:absolute; inset:0; object-fit:cover`).
It's fine to extract more seconds than the scene's duration; the footage just holds on the
last frame it reaches when the scene cuts away.
