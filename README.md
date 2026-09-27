# Personal Site

This repository contains the source for my personal website (`harsh-agrawal.com`). It is a lightweight static page written in plain HTML and CSS—no frameworks or build steps.

## Shows page

[`/shows/`](https://harsh-agrawal.com/shows/) draws `shows/shows.json` as a ranked poster grid. The JSON is the source of truth and has one show per line: your fields (`title`, `rating`, `status`, `tags`) first, then fields filled from [TVmaze](https://www.tvmaze.com/api) (`episodes`, `episode_minutes`, `genres`, `tvmaze`, `imdb`, `poster`).

- **Change a rating or status:** edit the line and push. The page sorts shows by rating, and tied ratings share a rank.
- **Add a show:** add `{"title": "…", "rating": 8.1, "status": "completed"}` anywhere in the list. Status is `completed`, `watching` or `partial`, and you can add `"tags": ["Sitcom"]` or `["Documentary"]`. Then run `python3 scripts/shows.py`: it matches the show on TVmaze and fills in the TVmaze fields. Check the match it prints. If it's wrong, delete the TVmaze fields, set the right `"tvmaze"` id, and run it again. For a show TVmaze doesn't have, set `"tvmaze": null`.
- **Filters** match `genres` and `tags`. Drama comes from TVmaze's genres, "Indian" is added to genres for Indian-language shows, and Sitcom and Documentary are your tags. The script only fills missing fields, so your edits stick. To refresh a show's episode count while it airs, delete `episodes` and rerun.
- **Before pushing a hand edit,** run the script anyway. It checks the file, and if no show needs TVmaze data it finishes instantly without touching the network.
- **Preview locally:** from the repo root run `python3 -m http.server 4000`, then open `http://localhost:4000/shows/`. Pages use root-relative paths, so opening the HTML file directly won't work.

Genres, episode data and IDs come from TVmaze (CC BY-SA). Posters are © their networks and studios. They're loaded from TVmaze's image server rather than copied into this repo, as TVmaze asks.

## Inspiration
Primarily inspired by [amyx.lu](https://amyx.lu) and [salabs.me](https://salabs.me). Additional inspiration was drawn from [jakublala.github.io](https://jakublala.github.io) and [aryxnsharma.com](https://www.aryxnsharma.com).