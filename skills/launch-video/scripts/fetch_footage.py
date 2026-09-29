#!/usr/bin/env python3
"""
Search and fetch public-domain / free-licence footage for launch-video, from sources that
need no API key (plus two optional stock sources that do):

  - NASA Image and Video Library (images-api.nasa.gov)     -> generally public domain.
                                                                Max ONE shot per clip unless
                                                                the brief is explicitly space.
  - Internet Archive Prelinger Archives (archive.org)      -> check licenseurl per item
  - Internet Archive, general movies (archive.org)         -> licenseurl filtered to
                                                                publicdomain / CC0 / CC BY
  - Wikimedia Commons (commons.wikimedia.org)              -> extmetadata LicenseShortName
                                                                filtered to PD/CC0/CC BY/CC BY-SA
  - Library of Congress film & video (loc.gov)             -> rights field filtered to
                                                                no known restrictions / public domain
  - Pexels stock video   (needs PEXELS_API_KEY in env)     -> skipped silently if unset
  - Pixabay stock video  (needs PIXABAY_API_KEY in env)    -> skipped silently if unset

Never executes downloaded media. Never reads .env files — API keys, if used, come only from
the shell's own environment (os.environ). Only fetches, lists licence evidence, and
(optionally) trims + grades a chosen clip with ffmpeg into a project's assets/footage/.

Use `--mood` to expand a mood into search terms instead of typing your own query — see
footage.md's MOOD MENU for the full list and the "max one space shot" / "vary sources and
subjects" rules.

Usage:
  # search only, print candidates with licence evidence
  python3 fetch_footage.py search nasa "cupola earth"
  python3 fetch_footage.py search prelinger "tachometer gauge dial"
  python3 fetch_footage.py search archive "ocean waves slow motion"
  python3 fetch_footage.py search wikimedia "radio telescope"
  python3 fetch_footage.py search loc "switchboard operators"
  python3 fetch_footage.py search pexels "city skyline night"      # needs PEXELS_API_KEY
  python3 fetch_footage.py search pixabay "aurora timelapse"       # needs PIXABAY_API_KEY

  # or let a mood pick the query
  python3 fetch_footage.py search wikimedia --mood precision
  python3 fetch_footage.py search --source archive --source wikimedia --mood intelligence

  # download one item's largest reasonable video file
  python3 fetch_footage.py download nasa <nasa_id> -o /tmp/clip.mp4
  python3 fetch_footage.py download prelinger <archive_id> -o /tmp/clip.mp4 [--file NAME]
  python3 fetch_footage.py download archive <archive_id> -o /tmp/clip.mp4 [--file NAME]
  python3 fetch_footage.py download wikimedia <title_or_url> -o /tmp/clip.mp4
  python3 fetch_footage.py download loc <item_id> -o /tmp/clip.mp4
  python3 fetch_footage.py download pexels <video_id> -o /tmp/clip.mp4
  python3 fetch_footage.py download pixabay <video_id> -o /tmp/clip.mp4

  # cut + grade a local file with the shared warm/filmic recipe (see grade_footage.sh)
  python3 fetch_footage.py grade IN.mp4 OUT.mp4 --start 12.0 --duration 5 \
      --crop "crop=1440:1080:(1620-1440)/2:0"   # omit --crop for an already-4:3 source
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

NASA_SEARCH = "https://images-api.nasa.gov/search"
NASA_ASSET = "https://images-api.nasa.gov/asset/{}"
IA_SEARCH = "https://archive.org/advancedsearch.php"
IA_METADATA = "https://archive.org/metadata/{}"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
LOC_SEARCH = "https://www.loc.gov/film-and-videos/"
PEXELS_SEARCH = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH = "https://pixabay.com/api/videos/"

# Mood -> search terms, per footage.md's MOOD MENU. Each mood expands to an OR'd query string
# a source's search can use as-is (sources that don't support boolean OR just get the first term).
MOODS = {
    "precision": ["clockwork", "watchmaking", "machining lathe", "typewriter mechanism"],
    "speed": ["steam train", "jet engine", "highway at night", "rocket launch"],
    "intelligence": ["radio telescope", "telephone switchboard", "vintage computer", "oscilloscope", "data center"],
    "human": ["hands at work", "laboratory researcher", "drafting table engineer"],
    "nature": ["ocean waves slow motion", "clouds timelapse", "forest canopy", "aurora borealis"],
    "city": ["city skyline night", "neon signs", "traffic light trails"],
    "space": ["earth from orbit", "cupola earth", "rocket launch"],
}


def _get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "launch-video-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def mood_query(mood, source=None):
    terms = MOODS.get(mood)
    if not terms:
        sys.exit(f"unknown mood {mood!r}; choose from {sorted(MOODS)}")
    # sources that support boolean OR in a single query string get the full expansion;
    # everything else gets the first term only (still a reasonable single search).
    if source in ("archive", "prelinger"):
        return " OR ".join(terms)
    return terms[0]


# ---------- NASA ----------

def search_nasa(query, rows=10):
    url = f"{NASA_SEARCH}?q={urllib.parse.quote(query)}&media_type=video"
    d = _get_json(url)
    items = d["collection"]["items"][:rows]
    out = []
    for it in items:
        data = it["data"][0]
        out.append({
            "source": "nasa",
            "id": data.get("nasa_id"),
            "title": data.get("title"),
            "description": (data.get("description") or "")[:160],
            "resolution": None,
            "licence": "NASA media usage guidelines: generally public domain "
                       "(https://www.nasa.gov/nasa-brand-center/images-and-videos/). "
                       "Do not include NASA insignia/logos in the frame; no endorsement implied.",
        })
    return out


def nasa_files(nasa_id):
    d = _get_json(NASA_ASSET.format(nasa_id))
    return [it["href"] for it in d["collection"]["items"]]


# ---------- Internet Archive: Prelinger ----------

def search_prelinger(query, rows=20):
    q = f"collection:prelinger AND ({query})"
    params = {
        "q": q,
        "fl[]": ["identifier", "title", "licenseurl"],
        "rows": str(rows),
        "output": "json",
    }
    url = IA_SEARCH + "?" + urllib.parse.urlencode(params, doseq=True)
    d = _get_json(url)
    docs = d["response"]["docs"]
    out = []
    for doc in docs:
        licence = doc.get("licenseurl")
        out.append({
            "source": "prelinger",
            "id": doc["identifier"],
            "title": doc.get("title"),
            "resolution": None,
            "licence": licence or "NOT CONFIRMED — no licenseurl field returned; "
                                    "verify on the archive.org item page before using.",
        })
    return out


def prelinger_files(identifier):
    d = _get_json(IA_METADATA.format(identifier))
    files = [f["name"] for f in d.get("files", [])
             if f["name"].lower().endswith((".mp4", ".ogv", ".mov", ".m4v"))]
    licence = d.get("metadata", {}).get("licenseurl")
    return files, licence


# ---------- Internet Archive: general movies, licence-filtered ----------

IA_OK_LICENCE_FRAGMENTS = ("publicdomain", "publicdomain/zero", "creativecommons.org/publicdomain",
                             "creativecommons.org/licenses/by/", "cc0")


def search_archive(query, rows=20):
    # licenseurl:* forces the field to be present, then we filter client-side for the
    # specific licences we accept (publicdomain / CC0 / CC BY — never NC/ND/BY-SA-only here).
    q = f"mediatype:movies AND licenseurl:* AND ({query})"
    params = {
        "q": q,
        "fl[]": ["identifier", "title", "licenseurl"],
        "rows": str(rows * 3),  # over-fetch, then filter
        "output": "json",
    }
    url = IA_SEARCH + "?" + urllib.parse.urlencode(params, doseq=True)
    d = _get_json(url)
    docs = d["response"]["docs"]
    out = []
    for doc in docs:
        licence = (doc.get("licenseurl") or "").lower()
        if not any(frag in licence for frag in IA_OK_LICENCE_FRAGMENTS):
            continue
        out.append({
            "source": "archive",
            "id": doc["identifier"],
            "title": doc.get("title"),
            "resolution": None,
            "licence": doc.get("licenseurl"),
        })
        if len(out) >= rows:
            break
    return out


def archive_files(identifier):
    return prelinger_files(identifier)  # identical metadata shape


# ---------- Wikimedia Commons ----------

WIKIMEDIA_OK_LICENCES = ("public domain", "cc0", "cc by", "cc by-sa")
WIKIMEDIA_ATTRIBUTION_REQUIRED = ("cc by", "cc by-sa")  # substrings needing credit (not plain PD/CC0)


def search_wikimedia(query, rows=15):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{query} filetype:video",
        "srnamespace": "6",  # File: namespace
        "srlimit": str(rows * 2),
    }
    url = WIKIMEDIA_API + "?" + urllib.parse.urlencode(params)
    d = _get_json(url, headers={"User-Agent": "launch-video-fetch/1.0 (contact: n/a)"})
    hits = d.get("query", {}).get("search", [])
    out = []
    for hit in hits:
        title = hit["title"]  # e.g. "File:Something.webm"
        if not title.lower().endswith((".webm", ".ogv", ".mp4")):
            continue
        info = _wikimedia_file_info(title)
        if not info:
            continue
        licence_name = (info.get("LicenseShortName") or "").strip()
        if not any(licence_name.lower() == ok or licence_name.lower().startswith(ok)
                   for ok in WIKIMEDIA_OK_LICENCES):
            continue
        artist = _strip_html(info.get("Artist", ""))
        attribution_required = any(ok in licence_name.lower() for ok in WIKIMEDIA_ATTRIBUTION_REQUIRED)
        out.append({
            "source": "wikimedia",
            "id": title,
            "title": title,
            "resolution": info.get("_resolution"),
            "licence": licence_name,
            "attribution_required": attribution_required,
            "attribution_text": f"{artist} / Wikimedia Commons, {licence_name}" if attribution_required else None,
        })
        if len(out) >= rows:
            break
    return out


def _strip_html(s):
    import re
    return re.sub("<[^<]+?>", "", s or "").strip()


def _wikimedia_file_info(title):
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
    }
    url = WIKIMEDIA_API + "?" + urllib.parse.urlencode(params)
    d = _get_json(url, headers={"User-Agent": "launch-video-fetch/1.0 (contact: n/a)"})
    pages = d.get("query", {}).get("pages", {})
    for page in pages.values():
        info_list = page.get("imageinfo")
        if not info_list:
            return None
        info = info_list[0]
        meta = info.get("extmetadata", {})
        out = {k: v.get("value") for k, v in meta.items()}
        out["_url"] = info.get("url")
        w, h = info.get("width"), info.get("height")
        out["_resolution"] = f"{w}x{h}" if w and h else None
        return out
    return None


def wikimedia_file_url(title):
    info = _wikimedia_file_info(title if title.startswith("File:") else f"File:{title}")
    if not info:
        sys.exit(f"no such Commons file: {title}")
    return info["_url"]


# ---------- Library of Congress ----------

LOC_OK_RIGHTS_FRAGMENTS = ("no known restrictions", "public domain")


def search_loc(query, rows=15):
    params = {"q": query, "fo": "json", "c": str(rows)}
    url = LOC_SEARCH + "?" + urllib.parse.urlencode(params)
    # loc.gov rejects urllib's default User-Agent with a 403; a plain browser-style UA works.
    d = _get_json(url, headers={"User-Agent": "Mozilla/5.0 (launch-video-fetch/1.0)"})
    results = d.get("results", [])
    out = []
    for item in results:
        rights = " ".join(str(x) for x in ([item.get("rights")] if isinstance(item.get("rights"), str)
                                             else (item.get("rights") or [])))
        access = str(item.get("access_restricted", "")).lower()
        rights_check = (rights or "").lower()
        if not any(frag in rights_check for frag in LOC_OK_RIGHTS_FRAGMENTS):
            continue
        if access == "true":
            continue
        out.append({
            "source": "loc",
            "id": item.get("id") or item.get("url"),
            "title": item.get("title"),
            "resolution": None,
            "licence": rights or "marked 'no known restrictions' by the Library of Congress",
        })
        if len(out) >= rows:
            break
    return out


def loc_files(item_id):
    url = item_id if item_id.startswith("http") else f"https://www.loc.gov/item/{item_id}/?fo=json"
    d = _get_json(url, headers={"User-Agent": "Mozilla/5.0 (launch-video-fetch/1.0)"})
    resources = d.get("resources", []) or []
    files = []
    # loc.gov item JSON nests media file lists under resources[].files[][] -> stream/video urls
    for res in resources:
        for group in res.get("files", []) or []:
            for f in group if isinstance(group, list) else [group]:
                if isinstance(f, dict) and f.get("mimetype", "").startswith("video"):
                    files.append(f.get("url"))
    return [f for f in files if f]


# ---------- Pexels (needs PEXELS_API_KEY, never read from .env) ----------

def search_pexels(query, rows=15):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None  # signal "skipped, no key" — caller decides how to report it
    params = {"query": query, "per_page": str(rows)}
    url = PEXELS_SEARCH + "?" + urllib.parse.urlencode(params)
    d = _get_json(url, headers={"Authorization": key})
    out = []
    for v in d.get("videos", []):
        best = max(v.get("video_files", []), key=lambda f: (f.get("width") or 0) * (f.get("height") or 0), default=None)
        out.append({
            "source": "pexels",
            "id": v["id"],
            "title": f"pexels video {v['id']} by {v.get('user', {}).get('name')}",
            "resolution": f"{best['width']}x{best['height']}" if best else None,
            "licence": "Pexels License (free to use, no attribution required): "
                       "https://www.pexels.com/license/",
            "_file_url": best["link"] if best else None,
        })
    return out


def pexels_file_url(video_id):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        sys.exit("PEXELS_API_KEY not set in this shell's environment")
    d = _get_json(f"https://api.pexels.com/videos/videos/{video_id}", headers={"Authorization": key})
    best = max(d.get("video_files", []), key=lambda f: (f.get("width") or 0) * (f.get("height") or 0), default=None)
    if not best:
        sys.exit(f"no video files for pexels id {video_id}")
    return best["link"]


# ---------- Pixabay (needs PIXABAY_API_KEY, never read from .env) ----------

def search_pixabay(query, rows=15):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return None
    params = {"key": key, "q": query, "per_page": str(max(rows, 3))}
    url = PIXABAY_SEARCH + "?" + urllib.parse.urlencode(params)
    d = _get_json(url)
    out = []
    for v in d.get("hits", []):
        videos = v.get("videos", {})
        best = max(videos.values(), key=lambda f: (f.get("width") or 0) * (f.get("height") or 0), default=None)
        out.append({
            "source": "pixabay",
            "id": v["id"],
            "title": v.get("tags"),
            "resolution": f"{best['width']}x{best['height']}" if best else None,
            "licence": "Pixabay Content License (free to use, no attribution required): "
                       "https://pixabay.com/service/license-summary/",
            "_file_url": best["url"] if best else None,
        })
    return out


def pixabay_file_url(video_id):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        sys.exit("PIXABAY_API_KEY not set in this shell's environment")
    d = _get_json(PIXABAY_SEARCH + "?" + urllib.parse.urlencode({"key": key, "id": video_id}))
    hits = d.get("hits", [])
    if not hits:
        sys.exit(f"no pixabay hit for id {video_id}")
    videos = hits[0].get("videos", {})
    best = max(videos.values(), key=lambda f: (f.get("width") or 0) * (f.get("height") or 0), default=None)
    if not best:
        sys.exit(f"no video files for pixabay id {video_id}")
    return best["url"]


SOURCES = ["nasa", "prelinger", "archive", "wikimedia", "loc", "pexels", "pixabay"]


def download(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": "launch-video-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(out_path, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


GRADE = (
    "eq=contrast=1.08:saturation=0.96:brightness=0.0,"
    "colorbalance=rs=-0.09:gs=0.02:bs=0.11:rm=0.02:gm=0.0:bm=0.02:rh=0.09:gh=0.0:bh=-0.06,"
    "curves=r='0/0.02 0.5/0.51 1/0.97':b='0/0.02 0.5/0.48 1/0.9',"
    "vignette=PI/3.2,noise=alls=14:allf=t+u"
)
PILLARBOX = "pad=1920:1080:(1920-1440)/2:0:color=black"


def grade(in_path, out_path, start, duration, crop=None, extra=None):
    vf = f"{crop},{GRADE},{PILLARBOX}" if crop else f"{GRADE},{PILLARBOX}"
    if extra:
        vf = f"{vf},{extra}"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(start), "-t", str(duration), "-i", in_path,
        "-vf", vf, "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {out_path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("source", nargs="?", choices=SOURCES,
                    help="omit when using --source one-or-more-times instead")
    s.add_argument("query", nargs="?", help="omit when using --mood instead")
    s.add_argument("--rows", type=int, default=10)
    s.add_argument("--mood", choices=sorted(MOODS), help="expand a mood into a search query (see footage.md)")
    s.add_argument("--source", action="append", dest="sources",
                    help="repeatable: search multiple sources in one call")

    d = sub.add_parser("download")
    d.add_argument("source", choices=SOURCES)
    d.add_argument("id")
    d.add_argument("-o", "--out", required=True)
    d.add_argument("--file", help="prelinger/archive only: exact filename from `search`'s file list "
                                    "(prints candidates if omitted)")
    d.add_argument("--variant", default="large", help="nasa only: orig|large|medium|mobile|preview|small")

    g = sub.add_parser("grade")
    g.add_argument("in_path")
    g.add_argument("out_path")
    g.add_argument("--start", type=float, required=True)
    g.add_argument("--duration", type=float, required=True)
    g.add_argument("--crop", help='e.g. "crop=1440:1080:(1620-1440)/2:0" for a wider-than-4:3 source; '
                                    'omit if the source is already 4:3')
    g.add_argument("--extra", help="extra ffmpeg filter fragment appended after the grade, before pillarbox")

    args = p.parse_args()

    if args.cmd == "search":
        sources = args.sources or ([args.source] if args.source else None)
        if not sources:
            sys.exit("pass a source positionally, or one or more --source flags")
        for src in sources:
            if src not in SOURCES:
                sys.exit(f"unknown source {src!r}; choose from {SOURCES}")
        results = {}
        for src in sources:
            query = args.query or (mood_query(args.mood, src) if args.mood else None)
            if not query:
                sys.exit("pass a query, or --mood")
            fn = {
                "nasa": search_nasa, "prelinger": search_prelinger, "archive": search_archive,
                "wikimedia": search_wikimedia, "loc": search_loc,
                "pexels": search_pexels, "pixabay": search_pixabay,
            }[src]
            try:
                out = fn(query, args.rows)
            except Exception as e:  # noqa: BLE001 - report and keep going
                results[src] = {"error": str(e)}
                continue
            if out is None:
                results[src] = {"skipped": "no API key in shell env (PEXELS_API_KEY/PIXABAY_API_KEY)"}
            else:
                results[src] = out
        if len(sources) == 1:
            print(json.dumps(results[sources[0]], indent=2))
        else:
            print(json.dumps(results, indent=2))

    elif args.cmd == "download":
        if args.source == "nasa":
            files = nasa_files(args.id)
            hit = next((f for f in files if f"~{args.variant}.mp4" in f), None)
            if not hit:
                hit = next((f for f in files if f.endswith(".mp4")), None)
            if not hit:
                sys.exit(f"no mp4 found for {args.id}: {files}")
            download(hit, args.out)
            print(f"downloaded {hit} -> {args.out}")
        elif args.source in ("prelinger", "archive"):
            files, licence = (prelinger_files(args.id) if args.source == "prelinger" else archive_files(args.id))
            if not args.file:
                print(f"licenceurl: {licence!r}")
                print("candidate files:")
                for f in files:
                    print(" ", f)
                sys.exit("pass --file NAME to download one")
            url = f"https://archive.org/download/{args.id}/{args.file}"
            download(url, args.out)
            print(f"downloaded {url} -> {args.out}  (licenceurl: {licence!r})")
        elif args.source == "wikimedia":
            url = wikimedia_file_url(args.id)
            download(url, args.out)
            print(f"downloaded {url} -> {args.out}")
        elif args.source == "loc":
            files = loc_files(args.id)
            if not files:
                sys.exit(f"no downloadable video files found for loc item {args.id}")
            download(files[0], args.out)
            print(f"downloaded {files[0]} -> {args.out}")
        elif args.source == "pexels":
            url = pexels_file_url(args.id)
            download(url, args.out)
            print(f"downloaded {url} -> {args.out}")
        elif args.source == "pixabay":
            url = pixabay_file_url(args.id)
            download(url, args.out)
            print(f"downloaded {url} -> {args.out}")

    elif args.cmd == "grade":
        grade(args.in_path, args.out_path, args.start, args.duration, args.crop, args.extra)


if __name__ == "__main__":
    main()
