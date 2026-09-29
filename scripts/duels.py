#!/usr/bin/env python3
"""Copy the standings picktwo last committed for the shows into the website's database.

picktwo ranks these same shows by duel, and its "Commit results" button saves the
standings of every show in picktwo's own database. /shows/ reads only the website's
public API, so this copies them into public.duel_ratings, which api.shows serves as
duel_rating and duel_rank. Nothing crosses databases: it reads picktwo's API and writes
the website's own. Each show's `rating` is left alone, because picktwo starts from it.

It runs on kamaji as the launch agent com.harsh.personal_website.duels (kamaji-server),
checking every 15 seconds and copying only when picktwo has committed since. It reads
picktwo's PostgREST on 127.0.0.1:3003, which only answers on kamaji, and writes with psql
as the macOS user, like scripts/shows.py. When a check fails, the last copy stays, so
/shows/ shows the standings from before rather than none.

Once, by hand:  ssh kamaji python3 ~/Developer/personal/harshagrawal13.github.io/scripts/duels.py --once
(stdlib only)
"""

import json
import subprocess
import sys
import time
import urllib.request

PSQL = ["/opt/homebrew/opt/postgresql@18/bin/psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", "personal_website"]
PICKTWO = "http://127.0.0.1:3003/scores?set_id=eq.shows&select=item,rank,score,committed_at&order=rank.asc"
EVERY = 15  # seconds between checks

# The copy is replaced whole, in one transaction. A show picktwo ranked that has since left
# the site is skipped (the join); one deleted later takes its copy with it (the cascade).
REPLACE_SQL = """
begin;
delete from public.duel_ratings;
insert into public.duel_ratings (show_id, rank, score, committed_at)
  select r.show_id, r.rank, r.score, r.committed_at
  from json_to_recordset(:'rows') as r(show_id integer, rank integer, score numeric, committed_at timestamptz)
  join public.shows s on s.id = r.show_id;
commit;
select count(*) from public.duel_ratings;
"""


def log(msg: str) -> None:
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def standings() -> list:
    """picktwo's committed standings for the shows, best first. Each item is "website:<id>"."""
    with urllib.request.urlopen(PICKTWO, timeout=10) as resp:
        rows = json.load(resp)
    if not isinstance(rows, list):
        raise ValueError("picktwo didn't answer with a list")
    return rows


def show_id(item) -> int | None:
    prefix, _, rest = str(item).partition(":")
    return int(rest) if prefix == "website" and rest.isdigit() else None


def copy(rows: list) -> int:
    """Replaces the copy with `rows`, and says how many landed."""
    ours = [{"show_id": show_id(r["item"]), "rank": r["rank"], "score": r["score"], "committed_at": r["committed_at"]}
            for r in rows if show_id(r.get("item")) is not None]
    done = subprocess.run(PSQL + ["-At", "-v", f"rows={json.dumps(ours)}"], input=REPLACE_SQL,
                          capture_output=True, text=True, check=True)
    return int(done.stdout.split()[-1])


def main() -> int:
    once = "--once" in sys.argv[1:]
    copied = None   # (commit time, row count) of the standings last copied, this run
    failing = False
    while True:
        try:
            rows = standings()
            mark = (rows[0]["committed_at"] if rows else None, len(rows))
            if mark != copied:
                n = copy(rows)
                skipped = f" ({len(rows) - n} for shows no longer on the site skipped)" if n < len(rows) else ""
                log(f"copied {n} duel ratings, committed {mark[0]}{skipped}" if rows else "picktwo has no standings for the shows; the copy is empty")
                copied = mark
            if failing:
                log("copying again")
            failing = False
        except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as err:  # OSError covers HTTP and network errors
            if not failing:  # say it once per outage, not every 15 seconds
                detail = err.stderr.strip() if isinstance(err, subprocess.CalledProcessError) else err
                log(f"couldn't copy the standings, so the last copy stays: {detail}")
            failing = True
        if once:
            return 1 if failing else 0
        time.sleep(EVERY)


if __name__ == "__main__":
    sys.exit(main())
