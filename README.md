# RFP Radar — public web front-end for `rfp-tracker`

A static, hostable website that presents the **public opportunity data** from the
[`rfp-tracker`](https://github.com/air5118/rfp-tracker) CLI: live advertising &
marketing RFPs for US agencies, browsable, searchable, and filterable by source.

It shows only outward-facing fields (title, issuer, type, posted date, deadline,
link, description). Internal triage fields — **status, assignee, notes** — are
never included.

## Structure

```
rfp-tracker-web/
├── index.html         # markup
├── assets/
│   ├── style.css      # styling (dark, responsive)
│   └── app.js         # loads data/rfps.json, renders + filters
├── data/
│   └── rfps.json      # the data feed (demo data included)
└── build_data.py      # convert a real rfp.py CSV export → data/rfps.json
```

## Run locally

The page fetches `data/rfps.json`, so it must be served over HTTP (not opened
as a `file://`):

```bash
cd rfp-tracker-web
python3 -m http.server 8000
# open http://localhost:8000
```

## Use real data

The site ships with demo data. To publish real opportunities from the tracker:

```bash
# in the rfp-tracker repo
python3 rfp.py fetch
python3 rfp.py export --file rfps.csv

# in this repo
python3 build_data.py /path/to/rfps.csv    # rewrites data/rfps.json
```

## Deploy (any static host)

- **GitHub Pages:** push this folder to a repo, enable Pages on the branch root.
- **Netlify / Cloudflare Pages:** point at the repo, no build command, publish dir = `/`.
- **Vercel:** import the repo as a static project.

No backend, no build step, no secrets. Nothing here touches the `rfp-tracker`
repo or its scheduled GitHub Actions.

### Keeping it fresh automatically

To auto-update the deployed feed, add a step to the tracker's existing daily
workflow that runs `export`, converts via `build_data.py`, and commits
`data/rfps.json` to this repo (or publishes it as an artifact your host reads).
