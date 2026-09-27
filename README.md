# Personal Site

This repository contains the source for my personal website (`harsh-agrawal.com`). It is a lightweight static page written in plain HTML and CSS—no frameworks or build steps.

## Shows page

[`/shows/`](https://harsh-agrawal.com/shows/) draws `shows/shows.json` as a ranked poster grid. The JSON is the source of truth and has one show per line: your fields (`title`, `rating`, `status`, `season`, `tags`) first, then fields filled from [TVmaze](https://www.tvmaze.com/api) (`seasons`, `episodes`, `episode_minutes`, `genres`, `tvmaze`, `imdb`, `poster`).

- **Change a rating, status or season:** edit the line and push. The page sorts shows by rating, and tied ratings share a rank. Status is `completed`, `watching` or `abandoned`. For the last two, `season` is the season you're on or left at: the card says "Watching Season 2 of 4" or "Left at Season 3 of 7", and the poster stays in colour for that share of the show (counting the current season as half watched), then turns grey.
- **Add a show:** add `{"title": "…", "rating": 8.1, "status": "completed"}` anywhere in the list, plus `"season"` if you haven't finished it. You can add `"tags": ["Sitcom"]` or `["Documentary"]`. Then run `python3 scripts/shows.py`: it matches the show on TVmaze and fills in the TVmaze fields. Check the match it prints. If it's wrong, delete the TVmaze fields, set the right `"tvmaze"` id, and run it again. For a show TVmaze doesn't have, set `"tvmaze": null`.
- **Filters** match `genres` and `tags`, and the Status dropdown matches `status`. Drama comes from TVmaze's genres, "Indian" is added to genres for Indian-language shows, and Sitcom and Documentary are your tags. The script only fills missing fields, so your edits stick. `seasons` and `episodes` count what has aired; to refresh them while a show airs, delete both and rerun.
- **Before pushing a hand edit,** run the script anyway. It checks the file, and if no show needs TVmaze data it finishes instantly without touching the network.
- **Preview locally:** from the repo root run `python3 -m http.server 4000`, then open `http://localhost:4000/shows/`. Pages use root-relative paths, so opening the HTML file directly won't work.

Genres, episode data and IDs come from TVmaze (CC BY-SA). Posters are © their networks and studios. They're loaded from TVmaze's image server rather than copied into this repo, as TVmaze asks.

## Inspiration
Primarily inspired by [amyx.lu](https://amyx.lu) and [salabs.me](https://salabs.me). Additional inspiration was drawn from [jakublala.github.io](https://jakublala.github.io) and [aryxnsharma.com](https://www.aryxnsharma.com).