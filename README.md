# Personal Site

This repository contains the source for my personal website (`harsh-agrawal.com`). It is a lightweight static page written in plain HTML and CSS—no frameworks or build steps.

## Shows page

[`/shows/`](https://harsh-agrawal.com/shows/) draws `shows/shows.json` as a ranked poster grid. The JSON is the source of truth and has one show per line.

- **Change a rating or status:** edit the line and push. The page sorts shows by rating, and tied ratings share a rank.
- **Add a show:** add `{"title": "…", "rating": 8.1, "status": "completed"}` anywhere in the list (status is `completed`, `watching` or `partial`; `watches` defaults to 1 and `episodes` is optional), then run `python3 scripts/shows.py`. It matches the show on [TVmaze](https://www.tvmaze.com/api), fills in its IDs, episode length and tags, and saves the poster as `assets/shows/<tvmaze id>.jpg`. Check the match it prints. If it's wrong, cut the line back to your own fields, set the right `"tvmaze"` id, and run it again.
- **Filters** read `tags`. Drama comes from TVmaze genres, "Indian" is added automatically for Indian-language shows, and Sitcom and Documentary are added by hand. The script only fills missing fields, so your edits stick.
- **Before pushing a hand edit,** run the script anyway. It checks the file, and if no show needs TVmaze data it finishes instantly without touching the network.
- **Preview locally:** from the repo root run `python3 -m http.server 4000`, then open `http://localhost:4000/shows/`. Pages use root-relative paths, so opening the HTML file directly won't work.

Posters, genres and other TVmaze fields are from TVmaze and licensed under CC BY-SA.

## Inspiration
Primarily inspired by [amyx.lu](https://amyx.lu) and [salabs.me](https://salabs.me). Additional inspiration was drawn from [jakublala.github.io](https://jakublala.github.io) and [aryxnsharma.com](https://www.aryxnsharma.com).