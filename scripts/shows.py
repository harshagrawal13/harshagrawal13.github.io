#!/usr/bin/env python3
"""Check shows/shows.json and fill in TVmaze data and posters for new shows.

A new show needs only "title", "rating" (out of 10) and "status" ("completed",
"watching" or "partial"); "watches" (default 1) and "episodes" are optional.
Any show missing TVmaze data is matched on TVmaze and gets "tvmaze", "imdb",
"episode_minutes" and "tags" (its genres, plus "Indian" for Indian-language
shows), and its poster is saved as assets/shows/<tvmaze>.jpg. Only missing
fields are filled, so your edits always stick.

If a show matched the wrong TVmaze entry, cut its line back to your own fields,
set the right "tvmaze" id, and run the script again.

Usage: python3 scripts/shows.py   (stdlib only; data from https://www.tvmaze.com/api)
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOWS_JSON = ROOT / "shows" / "shows.json"
POSTER_DIR = ROOT / "assets" / "shows"
API = "https://api.tvmaze.com"

STATUSES = ("completed", "watching", "partial")
KEY_ORDER = ("title", "rating", "status", "watches", "episodes", "episode_minutes", "tags", "tvmaze", "imdb")
INDIAN_LANGUAGES = {"Hindi", "Tamil", "Telugu", "Malayalam", "Kannada", "Bengali", "Marathi", "Punjabi"}
REQUEST_GAP = 0.5  # seconds before each call (TVmaze allows about 20 calls per 10 s), doubled on each retry
RETRIES = 5


def fetch(url: str) -> bytes:
    """GET a URL, retrying rate limits and dropped connections with backoff."""
    for attempt in range(RETRIES):
        time.sleep(REQUEST_GAP * 2**attempt)
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            permanent = isinstance(err, urllib.error.HTTPError) and err.code != 429
            if permanent or attempt == RETRIES - 1:
                raise
    raise AssertionError("unreachable")


def lookup(show: dict) -> dict:
    """The TVmaze record for a show, matched by TVmaze id, then IMDb id, then title."""
    if "tvmaze" in show:
        return json.loads(fetch(f"{API}/shows/{show['tvmaze']}"))
    if "imdb" in show:
        return json.loads(fetch(f"{API}/lookup/shows?imdb={show['imdb']}"))
    record = json.loads(fetch(f"{API}/singlesearch/shows?q={urllib.parse.quote(show['title'])}"))
    year = (record.get("premiered") or "?")[:4]
    print(f"  matched {show['title']!r} -> {record['name']} ({year}) {record['url']}")
    return record


def fill(show: dict, record: dict) -> None:
    """Copy TVmaze fields into a show, keeping every field that is already set."""
    indian = ["Indian"] if record.get("language") in INDIAN_LANGUAGES else []
    fields = {
        "tvmaze": record["id"],
        "imdb": (record.get("externals") or {}).get("imdb"),
        "episode_minutes": record.get("runtime") or record.get("averageRuntime"),
        "tags": (record.get("genres") or []) + indian,
    }
    for key, value in fields.items():
        if value is not None:
            show.setdefault(key, value)


def poster_path(show: dict) -> Path:
    return POSTER_DIR / f"{show['tvmaze']}.jpg"


def download_poster(show: dict, record: dict) -> None:
    url = (record.get("image") or {}).get("medium")
    if url:
        poster_path(show).write_bytes(fetch(url))
    else:
        print(f"  TVmaze has no poster for {show['title']!r}; save one as {poster_path(show).relative_to(ROOT)}")


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(shows: list) -> list[str]:
    problems = []
    for i, show in enumerate(shows, 1):
        title = show.get("title")
        where = repr(title) if title else f"show {i}"
        if not isinstance(title, str) or not title.strip():
            problems.append(f"{where}: needs a title")
        if not is_number(show.get("rating")) or not 0 <= show["rating"] <= 10:
            problems.append(f"{where}: rating must be a number from 0 to 10")
        if show.get("status") not in STATUSES:
            problems.append(f"{where}: status must be one of {', '.join(STATUSES)}")
        for key in ("watches", "episodes", "episode_minutes"):
            if key in show and not (is_number(show[key]) and show[key] >= 0):
                problems.append(f"{where}: {key} must be a non-negative number")
    return problems


def write(shows: list) -> None:
    """One show per line, so every edit is a one-line diff. Known keys come first, in KEY_ORDER."""
    lines = ["  " + json.dumps({k: show[k] for k in KEY_ORDER if k in show} | show, ensure_ascii=False) for show in shows]
    SHOWS_JSON.write_text("[\n" + ",\n".join(lines) + "\n]\n")


def main() -> int:
    shows = json.loads(SHOWS_JSON.read_text())
    problems = validate(shows)
    if problems:
        print(f"{SHOWS_JSON.relative_to(ROOT)} has problems:", *problems, sep="\n  ")
        return 1

    POSTER_DIR.mkdir(parents=True, exist_ok=True)
    for show in shows:
        if "tvmaze" in show and "tags" in show and poster_path(show).exists():
            continue
        try:
            record = lookup(show)
        except urllib.error.HTTPError as err:
            if err.code != 404:
                raise
            print(f"  no TVmaze match for {show['title']!r}; set its \"tvmaze\" id by hand")
            continue
        fill(show, record)
        if not poster_path(show).exists():
            download_poster(show, record)

    used = {poster_path(show).name for show in shows if "tvmaze" in show}
    unused = sorted(p.name for p in POSTER_DIR.glob("*.jpg") if p.name not in used)
    if unused:
        print("posters no show uses:", *unused, sep="\n  ")

    write(shows)
    print(f"{len(shows)} shows OK in {SHOWS_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
