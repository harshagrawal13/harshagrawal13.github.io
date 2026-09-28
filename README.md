# Personal Site

This repository contains the source for my personal website (`harsh-agrawal.com`). It is a lightweight static page written in plain HTML and CSS—no frameworks or build steps.

## Shows page

[`/shows/`](https://harsh-agrawal.com/shows/) draws my shows as a ranked poster grid. The list lives in **Postgres on kamaji** (my always-on Mac) and the page reads it from **https://api.harsh-agrawal.com/shows**:

```
page (GitHub Pages) ─▶ api.harsh-agrawal.com ─▶ Cloudflare Tunnel "kamaji" ─▶ PostgREST 127.0.0.1:3000 ─▶ Postgres 18 "personal_website"
```

PostgREST serves the view `api.shows` read-only as role `personal_website_anon`; nothing public can write. Postgres listens on localhost only. If kamaji is down, the page says "Couldn't load the list." The database's structure lives in [`db/migrations/`](db/migrations/) as [dbmate](https://github.com/amacneil/dbmate) migrations: the table and its rules, the public view, and what `personal_website_anon` may read. The database and its roles are created by kamaji's own setup, [harshagrawal13/kamaji-server](https://github.com/harshagrawal13/kamaji-server), whose `deploy` script applies new migrations. To change the structure, add a new migration; never edit one that has been applied.

- **Edit with SQL on kamaji** (or ask Claude to): `ssh kamaji psql -d personal_website`, then e.g. `update shows set rating = 9.7 where title = 'Rome';`. My columns are `title`, `rating` (0–10), `status` (`completed`, `watching` or `abandoned`), `season` (for unfinished shows: the one I'm on or left at) and `tags` (e.g. `{Sitcom}`, `{Documentary}`). The database rejects invalid values, including a `season` past `seasons`. The page ranks shows by rating within the current filters, and tied ratings share a rank. Unfinished posters stay in colour for (season − ½) ÷ seasons of the show.
- **Add a show:** `insert into shows (title, rating, status, season) values ('Andor', 8.9, 'watching', 1);`, then from this repo run `ssh kamaji python3 - < scripts/shows.py`. It matches every row that hasn't been looked up yet on [TVmaze](https://www.tvmaze.com/api) and fills the TVmaze columns (`seasons`, `episodes`, `episode_minutes`, `genres`, `tvmaze`, `imdb`, `poster`, `poster_large`), only where they're empty. Check the match it prints. If it's wrong, set `tvmaze` to the right id, null the other TVmaze columns and `tvmaze_checked_at`, and rerun. For a show TVmaze doesn't have, set `tvmaze_checked_at = now()` and leave `tvmaze` null.
- **Filters** match `genres` and `tags`, and the Status dropdown matches `status`. Drama comes from TVmaze's genres, and "Indian" is added to genres for Indian-language shows. `seasons` and `episodes` count what has aired; to refresh them while a show airs, null them and `tvmaze_checked_at`, then rerun the script.
- **Backups:** a launchd job on kamaji (`com.harsh.pg-backup`, 03:30) dumps every database to Google Drive `Backups/kamaji-postgres/` and keeps 30 days. Restore with `pg_restore -d personal_website --clean --if-exists personal_website-YYYY-MM-DD.dump`. Dumps from before 2026-09-28 are named `web-…` and grant to the old role `web_anon`.
- **Preview locally:** from the repo root run `python3 -m http.server 4000`, then open `http://localhost:4000/shows/`. The page still reads the live API. Pages use root-relative paths, so opening the HTML file directly won't work.

Genres, episode data and IDs come from TVmaze (CC BY-SA). Posters are © their networks and studios. They're loaded from TVmaze's image server rather than copied into this repo, as TVmaze asks.

## Inspiration
Primarily inspired by [amyx.lu](https://amyx.lu) and [salabs.me](https://salabs.me). Additional inspiration was drawn from [jakublala.github.io](https://jakublala.github.io) and [aryxnsharma.com](https://www.aryxnsharma.com).