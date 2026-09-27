#!/usr/bin/env python3
"""Fill in TVmaze data for the shows in the website's Postgres database on kamaji.

The list lives in the "web" database on kamaji (table public.shows) and is served
read-only to the site by PostgREST at https://api.harsh-agrawal.com/shows. Edits are
plain SQL on kamaji, for example:

    ssh kamaji psql -d web -c "update shows set rating = 9.7 where title = 'Rome'"
    ssh kamaji psql -d web -c "insert into shows (title, rating, status, season) values ('Andor', 8.9, 'watching', 1)"

The database enforces the rules: rating 0-10, status completed / watching / abandoned,
season from 1 and not past seasons. For every row whose tvmaze_checked_at is null, this
script matches the show on TVmaze (by its tvmaze id, then imdb id, then title), fills
in whichever of seasons and episodes (aired, not counting specials), episode_minutes,
genres (plus "Indian" for Indian-language shows), tvmaze, imdb, poster and
poster_large are still null, and stamps tvmaze_checked_at. Values already set are never
overwritten. To refresh a row, null those fields and tvmaze_checked_at; for a show
TVmaze doesn't have, set tvmaze_checked_at and leave tvmaze null.

Usage, from the repo:  ssh kamaji python3 - < scripts/shows.py
(stdlib only; data from https://www.tvmaze.com/api)
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

PSQL = ["/opt/homebrew/opt/postgresql@18/bin/psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", "web"]
API = "https://api.tvmaze.com"
INDIAN_LANGUAGES = {"Hindi", "Tamil", "Telugu", "Malayalam", "Kannada", "Bengali", "Marathi", "Punjabi"}
REQUEST_GAP = 0.5  # seconds before each call (TVmaze allows about 20 calls per 10 s), doubled on each retry
RETRIES = 5
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError)

PENDING_SQL = """
select coalesce(json_agg(s order by s.id), '[]')
from (select id, title, tvmaze, imdb from public.shows where tvmaze_checked_at is null) s
"""

# Fill only the columns that are still null, and stamp the row as looked up.
FILL_SQL = """
update public.shows s set
  seasons         = coalesce(s.seasons, d.seasons),
  episodes        = coalesce(s.episodes, d.episodes),
  episode_minutes = coalesce(s.episode_minutes, d.episode_minutes),
  genres          = coalesce(s.genres, d.genres),
  tvmaze          = coalesce(s.tvmaze, d.tvmaze),
  imdb            = coalesce(s.imdb, d.imdb),
  poster          = coalesce(s.poster, d.poster),
  poster_large    = coalesce(s.poster_large, d.poster_large),
  tvmaze_checked_at = now()
from json_populate_record(null::public.shows, :'row') d
where s.id = d.id;
"""


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


def tvmaze_id(show: dict) -> int:
    """The show's TVmaze id: as set, else matched by IMDb id, else by title."""
    if show["tvmaze"] is not None:
        return show["tvmaze"]
    if show["imdb"]:
        return json.loads(fetch(f"{API}/lookup/shows?imdb={show['imdb']}"))["id"]
    record = json.loads(fetch(f"{API}/singlesearch/shows?q={urllib.parse.quote(show['title'])}"))
    year = (record.get("premiered") or "?")[:4]
    print(f"  matched {show['title']!r} -> {record['name']} ({year}) {record['url']}")
    return record["id"]


def tvmaze_fields(show: dict) -> dict:
    """The TVmaze columns for a show, from its TVmaze record with episodes embedded."""
    record = json.loads(fetch(f"{API}/shows/{tvmaze_id(show)}?embed=episodes"))
    indian = ["Indian"] if record.get("language") in INDIAN_LANGUAGES else []
    today = date.today().isoformat()
    aired = [e for e in record.get("_embedded", {}).get("episodes", []) if e.get("airdate") and e["airdate"] <= today]
    image = record.get("image") or {}
    return {
        "seasons": len({e["season"] for e in aired}) or None,
        "episodes": len(aired) or None,
        "episode_minutes": record.get("runtime") or record.get("averageRuntime"),
        "genres": (record.get("genres") or []) + indian,
        "tvmaze": record["id"],
        "imdb": (record.get("externals") or {}).get("imdb"),
        "poster": image.get("medium"),
        "poster_large": image.get("original"),
    }


def main() -> int:
    pending = json.loads(subprocess.run(PSQL + ["-At", "-c", PENDING_SQL], capture_output=True, text=True, check=True).stdout)
    filled = 0
    for show in pending:
        try:
            fields = tvmaze_fields(show)
            row = json.dumps({"id": show["id"], **fields})
            subprocess.run(PSQL + ["-v", f"row={row}"], input=FILL_SQL, capture_output=True, text=True, check=True)
        except NETWORK_ERRORS as err:
            if isinstance(err, urllib.error.HTTPError) and err.code == 404:
                print(f"  no TVmaze match for {show['title']!r}; fix the title, set its tvmaze id, or set tvmaze_checked_at to skip it")
            else:
                print(f"  couldn't reach TVmaze for {show['title']!r} ({err}); run again later")
            continue
        except subprocess.CalledProcessError as err:  # e.g. a constraint the new values would break
            print(f"  couldn't save {show['title']!r}: {err.stderr.strip()}")
            continue
        filled += 1
        if fields["poster"] is None:
            print(f"  TVmaze has no poster for {show['title']!r}; set its poster column to an image URL if you have one")
    print(f"filled {filled} of {len(pending)} shows waiting for TVmaze data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
