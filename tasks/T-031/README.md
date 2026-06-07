# T-031 — ShotPro Reddit free-makeover · SCOUT

The **discovery half** of the ShotPro Reddit makeover funnel. It finds recent
Reddit threads where sellers are asking for product-photo help **and** have an
image attached, so a human can offer a free makeover and reply **manually**.

> ⚠️ **SCOUT ONLY.** `reddit_scout.py` never posts, comments, votes, or DMs.
> Reddit bans bots that auto-reply. Posting stays 100% manual.

## What it does
1. Searches r/AmazonSeller, r/FulfillmentByAmazon, r/EtsySellers, r/Flipping,
   r/dropship for photo-help phrases (`rate my photo`, `main image`,
   `photo help`, `listing photo`, `improve my photos`, …).
2. Keeps only posts whose title/body matches the intent **and** that have an
   image (`.jpg/.jpeg/.png`, `i.redd.it`, or a gallery).
3. Writes one JSON lead per line to `leads.jsonl`:
   `subreddit, thread_url, title, author, image_url, created_utc`.
4. Dedupes across runs by thread id in `seen.txt`.

## Run
```bash
python3 reddit_scout.py [limit]   # limit = posts scanned per subreddit (default 50)
```

## Auth (optional but recommended)
With creds + `praw` it uses the official Reddit API (higher quality, fewer blocks):
```bash
export REDDIT_CLIENT_ID=xxxx
export REDDIT_CLIENT_SECRET=xxxx
export REDDIT_USER_AGENT="shotpro-scout/0.1 by u/yourname"
pip install praw
```
Get creds at https://www.reddit.com/prefs/apps (type: **script**).

**No creds?** It automatically falls back to Reddit's public `.json` search
endpoints (no auth). Note: Reddit may `403` non-browser/datacenter IPs on the
public endpoint — if so, add creds + `praw`, or run from a residential IP.

## Output
- `leads.jsonl` — append-only leads (gitignored from real runs; review manually).
- `leads.sample.jsonl` — example of the exact line format.
- `seen.txt` — thread ids already processed (dedupe state).

## Next step (manual)
Open each `thread_url`, grab `image_url`, run it through the ShotPro makeover,
and reply by hand offering the free result. → handoff to Mini's batch half.
