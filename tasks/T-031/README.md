# T-031 - ShotPro Reddit free-makeover

Two-part ShotPro Reddit makeover funnel:

1. `reddit_scout.py` finds recent Reddit threads where sellers ask for
   product-photo help and have an image attached.
2. `makeover_batch.py` downloads those images, runs two ShotPro styles, writes
   before/after assets, and drafts a helpful comment for human review.

> WARNING: Generate + draft only. These scripts never post, comment, vote, or DM.
> Reddit replies stay 100% manual.

## Scout

1. Searches r/AmazonSeller, r/FulfillmentByAmazon, r/EtsySellers, r/Flipping,
   r/dropship for photo-help phrases (`rate my photo`, `main image`,
   `photo help`, `listing photo`, `improve my photos`, ...).
2. Keeps only posts whose title/body matches the intent and that have an image
   (`.jpg/.jpeg/.png`, `i.redd.it`, or a gallery).
3. Writes one JSON lead per line to `leads.jsonl`:
   `subreddit, thread_url, title, author, image_url, created_utc`.
4. Dedupes across runs by thread id in `seen.txt`.

### Run

```bash
python3 reddit_scout.py [limit]   # limit = posts scanned per subreddit (default 50)
```

### Auth

With creds plus `praw` it uses the official Reddit API:

```bash
export REDDIT_CLIENT_ID=xxxx
export REDDIT_CLIENT_SECRET=xxxx
export REDDIT_USER_AGENT="shotpro-scout/0.1 by u/yourname"
pip install praw
```

Get creds at https://www.reddit.com/prefs/apps (type: `script`).

Without creds, it falls back to Reddit's public `.json` search endpoints.

### Scout Output

- `leads.jsonl` - append-only leads from real runs.
- `leads.sample.jsonl` - example of the exact line format.
- `seen.txt` - thread ids already processed.

## Batch Makeover

`makeover_batch.py` reads `leads.jsonl`, downloads each `image_url`, and calls
the running ShotPro app twice:

- `style=studio_white`
- `style=marble_luxury`

It posts multipart form data to:

```text
${SHOTPRO_URL:-http://localhost:5055}/api/generate
product=<file>
style=<id>
```

### Dependencies

```bash
python3 -m pip install Pillow
```

HTTP calls use Python's standard library; no `requests` dependency is required.

### Run

Start ShotPro locally first, then:

```bash
cd tasks/T-031
python3 makeover_batch.py
```

Optional custom ShotPro URL:

```bash
SHOTPRO_URL=http://localhost:5055 python3 makeover_batch.py
```

### Batch Output

Assets are written outside the repo for manual review:

```text
~/shared-review/reddit-makeovers/<author>__<threadid>.png
~/shared-review/reddit-makeovers/<author>__<threadid>.txt
~/shared-review/reddit-makeovers/index.md
```

The PNG is a side-by-side `original | studio_white | marble_luxury`.

The `.txt` is a friendly ready-to-post draft:

```text
Saw you wanted to sharpen your main image - ran yours through a couple of styles, free, yours to keep. Happy to do the rest if useful.
```

Open `index.md`, review each image and draft, then post manually from a human
Reddit account only where it is welcome and useful.
