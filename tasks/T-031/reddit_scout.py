#!/usr/bin/env python3
"""
T-031 ShotPro Reddit free-makeover — SCOUT (discovery half).

Finds recent Reddit threads where sellers ask for product-photo help AND have an
image attached, then writes one JSON lead per line to leads.jsonl for a HUMAN to
review and reply to manually.

⚠️ SCOUT ONLY. This never posts, comments, votes, or DMs. Reddit bans bots that
auto-reply; posting stays 100% manual. This only reads public search results.

Auth: if REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USER_AGENT are set AND
praw is installed, it uses the official API. Otherwise it falls back to Reddit's
public .json search endpoints (no auth) so it still runs anywhere.

Usage:
    python3 reddit_scout.py [limit]      # limit = posts to scan per subreddit (default 50)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LEADS = os.path.join(HERE, "leads.jsonl")
SEEN = os.path.join(HERE, "seen.txt")

SUBREDDITS = [
    "AmazonSeller",
    "FulfillmentByAmazon",
    "EtsySellers",
    "Flipping",
    "dropship",
]

# Search terms (run per subreddit). Reddit search is OR-ish on quoted phrases.
SEARCH_TERMS = [
    "rate my photo",
    "main image",
    "photo help",
    "listing photo",
    "improve my photos",
]

# Title/body must match one of these to qualify as a photo-help ask.
WANT = re.compile(
    r"rate my photo|main image|photo help|listing photo|how to improve my photos|"
    r"improve my photos|product photo|photography help|better photos",
    re.I,
)

IMG_EXT = re.compile(r"\.(jpe?g|png)(\?.*)?$", re.I)


def has_image(post):
    """post is a dict with url, is_gallery, post_hint. Return image url or None."""
    url = post.get("url") or ""
    if IMG_EXT.search(url):
        return url
    if "i.redd.it" in url:
        return url
    if post.get("is_gallery"):
        # gallery: use the post permalink-resolvable url; best-effort first item
        return url or post.get("permalink")
    if post.get("post_hint") == "image":
        return url
    return None


def load_seen():
    if not os.path.exists(SEEN):
        return set()
    with open(SEEN) as f:
        return {ln.strip() for ln in f if ln.strip()}


def append_seen(ids):
    with open(SEEN, "a") as f:
        for i in ids:
            f.write(i + "\n")


def write_lead(rec):
    with open(LEADS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------- praw path (authed) ----------
def scan_praw(limit, seen):
    import praw  # noqa

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )
    reddit.read_only = True
    hits = []
    for sub in SUBREDDITS:
        for term in SEARCH_TERMS:
            try:
                results = reddit.subreddit(sub).search(
                    term, sort="new", time_filter="month", limit=limit
                )
            except Exception as e:
                print(f"  ! {sub} search '{term}' failed: {e}", file=sys.stderr)
                continue
            for s in results:
                tid = s.id
                if tid in seen:
                    continue
                text = f"{s.title}\n{getattr(s, 'selftext', '')}"
                if not WANT.search(text):
                    continue
                post = {
                    "url": s.url,
                    "is_gallery": getattr(s, "is_gallery", False),
                    "post_hint": getattr(s, "post_hint", ""),
                    "permalink": "https://reddit.com" + s.permalink,
                }
                img = has_image(post)
                if not img:
                    continue
                seen.add(tid)
                hits.append(
                    {
                        "_id": tid,
                        "subreddit": sub,
                        "thread_url": post["permalink"],
                        "title": s.title,
                        "author": str(s.author),
                        "image_url": img,
                        "created_utc": int(s.created_utc),
                    }
                )
            time.sleep(1)
    return hits


# ---------- no-auth path (public .json) ----------
def fetch_json(url):
    # Reddit 403s generic UAs. A descriptive UA works best for the API; the public
    # .json endpoints are happier with a browser-like one. Prefer the user's UA.
    ua = os.environ.get("REDDIT_USER_AGENT") or (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def scan_public(limit, seen):
    hits = []
    for sub in SUBREDDITS:
        for term in SEARCH_TERMS:
            q = urllib.parse.quote(term)
            url = (
                f"https://www.reddit.com/r/{sub}/search.json"
                f"?q={q}&restrict_sr=1&sort=new&t=month&limit={limit}"
            )
            try:
                data = fetch_json(url)
            except Exception as e:
                print(f"  ! {sub} search '{term}' failed: {e}", file=sys.stderr)
                time.sleep(2)
                continue
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                tid = d.get("id")
                if not tid or tid in seen:
                    continue
                text = f"{d.get('title','')}\n{d.get('selftext','')}"
                if not WANT.search(text):
                    continue
                post = {
                    "url": d.get("url_overridden_by_dest") or d.get("url", ""),
                    "is_gallery": d.get("is_gallery", False),
                    "post_hint": d.get("post_hint", ""),
                    "permalink": "https://reddit.com" + d.get("permalink", ""),
                }
                img = has_image(post)
                if not img:
                    continue
                seen.add(tid)
                hits.append(
                    {
                        "_id": tid,
                        "subreddit": sub,
                        "thread_url": post["permalink"],
                        "title": d.get("title", ""),
                        "author": d.get("author", ""),
                        "image_url": img,
                        "created_utc": int(d.get("created_utc", 0)),
                    }
                )
            time.sleep(2)  # be polite to the public endpoint
    return hits


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    seen = load_seen()

    authed = (
        os.environ.get("REDDIT_CLIENT_ID")
        and os.environ.get("REDDIT_CLIENT_SECRET")
        and os.environ.get("REDDIT_USER_AGENT")
    )
    use_praw = False
    if authed:
        try:
            import praw  # noqa

            use_praw = True
        except ImportError:
            print("praw not installed; using public .json fallback.", file=sys.stderr)

    print(f"Scout starting ({'authed API' if use_praw else 'public no-auth'}), limit={limit}/sub")
    hits = scan_praw(limit, seen) if use_praw else scan_public(limit, seen)

    new_ids = []
    for h in hits:
        tid = h.pop("_id")
        write_lead(h)
        new_ids.append(tid)
    if new_ids:
        append_seen(new_ids)

    print(f"Done. {len(new_ids)} new lead(s) -> {LEADS}")
    print("⚠️  Review leads.jsonl and reply MANUALLY on Reddit. Do not automate posting.")


if __name__ == "__main__":
    main()
