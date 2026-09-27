#!/usr/bin/env python3
"""Check shows/shows.json and fill in TVmaze data for new shows.

Each show starts with your fields -- "title", "rating" (out of 10), "status"
("completed", "watching" or "abandoned"), "season" (for unfinished shows: the
season you're on or left at) and optionally "tags" (e.g. "Sitcom") --
followed by fields filled from TVmaze: "seasons" and "episodes" (how many
have aired, not counting specials), "episode_minutes", "genres" (plus
"Indian" for Indian-language shows), "tvmaze", "imdb", "poster" and
"poster_large" (full size, used for the page's big top tiles). Posters are
image URLs on TVmaze's CDN: TVmaze asks sites to link to its images rather
than copy them. While a show airs, delete "seasons" and "episodes" to
refresh them.

A show missing any TVmaze field is matched by TVmaze id, then IMDb id, then
title, and only the missing fields are filled, so your edits always stick. To
fix a wrong match, delete its TVmaze fields, set the right "tvmaze" id and run
again. For a show TVmaze doesn't have, set "tvmaze" to null.

Usage: python3 scripts/shows.py   (stdlib only; data from https://www.tvmaze.com/api)
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SHOWS_JSON = Path(__file__).resolve().parent.parent / "shows" / "shows.json"
API = "https://api.tvmaze.com"

STATUSES = ("completed", "watching", "abandoned")
YOUR_FIELDS = ("title", "rating", "status", "season", "tags")
TVMAZE_FIELDS = ("seasons", "episodes", "episode_minutes", "genres", "tvmaze", "imdb", "poster", "poster_large")
INDIAN_LANGUAGES = {"Hindi", "Tamil", "Telugu", "Malayalam", "Kannada", "Bengali", "Marathi", "Punjabi"}
REQUEST_GAP = 0.5  # seconds before each call (TVmaze allows about 20 calls per 10 s), doubled on each retry
RETRIES = 5
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError)


def fetch(url: str) -> bytes:
    """GET a URL, retrying rate limits and dropped connections with backoff."""
    for attempt in range(RETRIES):
        time.sleep(REQUEST_GAP * 2**attempt)
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return resp.read()
        except NETWORK_ERRORS as err:
            permanent = isinstance(err, urllib.error.HTTPError) and err.code != 429
            if permanent or attempt == RETRIES - 1:
                raise
    raise AssertionError("unreachable")


def needs_lookup(show: dict) -> bool:
    if "tvmaze" in show and show["tvmaze"] is None:  # not on TVmaze
        return False
    return any(key not in show for key in TVMAZE_FIELDS)


def tvmaze_id(show: dict) -> int:
    """The show's TVmaze id: as set, else matched by IMDb id, else by title."""
    if "tvmaze" in show:
        return show["tvmaze"]
    if show.get("imdb"):
        return json.loads(fetch(f"{API}/lookup/shows?imdb={show['imdb']}"))["id"]
    record = json.loads(fetch(f"{API}/singlesearch/shows?q={urllib.parse.quote(show['title'])}"))
    year = (record.get("premiered") or "?")[:4]
    print(f"  matched {show['title']!r} -> {record['name']} ({year}) {record['url']}")
    return record["id"]


def lookup(show: dict) -> dict:
    """The show's TVmaze record, with its episodes embedded so they can be counted."""
    return json.loads(fetch(f"{API}/shows/{tvmaze_id(show)}?embed=episodes"))


def fill(show: dict, record: dict) -> None:
    """Copy TVmaze fields into a show, keeping every field that is already set.

    Missing values are stored as null, so the show isn't looked up again on the next run.
    """
    indian = ["Indian"] if record.get("language") in INDIAN_LANGUAGES else []
    today = date.today().isoformat()
    aired = [e for e in record.get("_embedded", {}).get("episodes", []) if e.get("airdate") and e["airdate"] <= today]
    fields = {
        "seasons": len({e["season"] for e in aired}) or None,
        "episodes": len(aired) or None,
        "episode_minutes": record.get("runtime") or record.get("averageRuntime"),
        "genres": (record.get("genres") or []) + indian,
        "tvmaze": record["id"],
        "imdb": (record.get("externals") or {}).get("imdb"),
        "poster": (record.get("image") or {}).get("medium"),
        "poster_large": (record.get("image") or {}).get("original"),
    }
    for key, value in fields.items():
        show.setdefault(key, value)
    if show["poster"] is None:
        print(f"  TVmaze has no poster for {show['title']!r}; set \"poster\" to an image URL if you have one")


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
        for key in ("seasons", "episodes", "episode_minutes"):
            if show.get(key) is not None and not (is_number(show[key]) and show[key] >= 0):
                problems.append(f"{where}: {key} must be a non-negative number")
        season = show.get("season")
        if season is not None:
            if not (isinstance(season, int) and not isinstance(season, bool) and season >= 1):
                problems.append(f"{where}: season must be a whole number from 1")
            elif is_number(show.get("seasons")) and season > show["seasons"]:
                problems.append(f"{where}: season {season} is past TVmaze's {show['seasons']}; delete \"seasons\" to refresh it")
        for key in ("tags", "genres"):
            if key in show and not (isinstance(show[key], list) and all(isinstance(t, str) for t in show[key])):
                problems.append(f"{where}: {key} must be a list of strings")
    return problems


def write(shows: list) -> None:
    """One show per line, so every edit is a one-line diff: your fields, then TVmaze's, then any others."""
    order = YOUR_FIELDS + TVMAZE_FIELDS
    lines = ["  " + json.dumps({k: show[k] for k in order if k in show} | show, ensure_ascii=False) for show in shows]
    SHOWS_JSON.write_text("[\n" + ",\n".join(lines) + "\n]\n", encoding="utf-8")


def main() -> int:
    shows = json.loads(SHOWS_JSON.read_text(encoding="utf-8"))
    problems = validate(shows)
    if problems:
        print(f"{SHOWS_JSON.name} has problems:", *problems, sep="\n  ")
        return 1

    for show in filter(needs_lookup, shows):
        try:
            fill(show, lookup(show))
        except NETWORK_ERRORS as err:
            if isinstance(err, urllib.error.HTTPError) and err.code == 404:
                print(f"  no TVmaze match for {show['title']!r}; fix the title, or set \"tvmaze\" to its id or null")
            else:
                print(f"  couldn't reach TVmaze for {show['title']!r} ({err}); run again later")

    write(shows)
    print(f"{len(shows)} shows OK in {SHOWS_JSON.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
