#!/usr/bin/env python3
"""
T-031 ShotPro Reddit free-makeover — BATCH MAKEOVER half.

Reads leads.jsonl from reddit_scout.py, downloads each lead image, calls the
running ShotPro app for two styles, and writes review-only assets:
  - before/after PNG: original | studio_white | marble_luxury
  - friendly draft comment .txt
  - index.md for the human to post MANUALLY

This script never posts, comments, votes, or DMs on Reddit.

Usage:
    python3 makeover_batch.py
"""

import base64
import json
import mimetypes
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Missing dependency: Pillow. Install with: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)


HERE = Path(__file__).resolve().parent
LEADS_PATH = HERE / "leads.jsonl"
OUT_DIR = Path.home() / "shared-review" / "reddit-makeovers"
SHOTPRO_URL = os.environ.get("SHOTPRO_URL", "http://localhost:5055").rstrip("/")
GENERATE_URL = f"{SHOTPRO_URL}/api/generate"
STYLES = ("studio_white", "marble_luxury")
USER_AGENT = "one-ten-shotpro-makeover/0.1"
DRAFT = (
    "Saw you wanted to sharpen your main image - ran yours through a couple of "
    "styles, free, yours to keep. Happy to do the rest if useful."
)


def read_leads(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run reddit_scout.py first.")

    leads = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                lead = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"Skipping invalid JSON on line {line_no}: {exc}", file=sys.stderr)
                continue
            missing = [k for k in ("thread_url", "author", "image_url") if not lead.get(k)]
            if missing:
                print(f"Skipping line {line_no}; missing {', '.join(missing)}", file=sys.stderr)
                continue
            leads.append(lead)
    return leads


def request_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def download_image(url):
    data, content_type = request_bytes(url)
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or Path(
        urllib.parse.urlparse(url).path
    ).suffix
    if ext.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    return data, ext


def multipart_body(fields, files):
    boundary = f"----shotpro-{uuid.uuid4().hex}"
    chunks = []

    def add(value):
        if isinstance(value, str):
            value = value.encode("utf-8")
        chunks.append(value)

    for name, value in fields.items():
        add(f"--{boundary}\r\n")
        add(f'Content-Disposition: form-data; name="{name}"\r\n\r\n')
        add(str(value))
        add("\r\n")

    for name, filename, content_type, data in files:
        add(f"--{boundary}\r\n")
        add(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        )
        add(data)
        add("\r\n")

    add(f"--{boundary}--\r\n")
    return boundary, b"".join(chunks)


def post_generate(image_data, filename, style):
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    boundary, body = multipart_body(
        fields={"style": style},
        files=[("product", filename, content_type, image_data)],
    )
    req = urllib.request.Request(
        GENERATE_URL,
        data=body,
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return parse_generate_response(resp.read(), resp.headers.get("Content-Type", ""))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"ShotPro {style} failed: HTTP {exc.code}: {detail}") from exc


def parse_generate_response(data, content_type):
    media_type = content_type.split(";")[0].strip().lower()
    if media_type.startswith("image/"):
        return data

    if media_type == "application/json" or data[:1] in (b"{", b"["):
        payload = json.loads(data.decode("utf-8"))
        parsed = find_image_in_json(payload)
        if parsed:
            return parsed
        keys = sorted(payload) if isinstance(payload, dict) else type(payload).__name__
        raise RuntimeError(f"ShotPro JSON response did not include an image field: {keys}")

    raise RuntimeError(f"Unsupported ShotPro response Content-Type: {content_type or '(empty)'}")


def parse_image_string(value):
    if value.startswith("data:image/"):
        _, encoded = value.split(",", 1)
        return base64.b64decode(encoded)
    if value.startswith(("http://", "https://")):
        return request_bytes(value)[0]
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        return None


def find_image_in_json(value):
    preferred = (
        "image",
        "image_base64",
        "imageUrl",
        "image_url",
        "result",
        "result_base64",
        "resultUrl",
        "result_url",
        "output",
        "outputUrl",
        "output_url",
        "url",
    )
    if isinstance(value, dict):
        for key in preferred:
            item = value.get(key)
            if isinstance(item, str):
                parsed = parse_image_string(item)
                if parsed:
                    return parsed
        for item in value.values():
            parsed = find_image_in_json(item)
            if parsed:
                return parsed
    elif isinstance(value, list):
        for item in value:
            parsed = find_image_in_json(item)
            if parsed:
                return parsed
    elif isinstance(value, str):
        return parse_image_string(value)
    return None


def thread_id(thread_url):
    match = re.search(r"/comments/([^/]+)/", thread_url)
    if match:
        return match.group(1)
    parsed = urllib.parse.urlparse(thread_url)
    fallback = Path(parsed.path.rstrip("/")).name or "thread"
    return fallback


def safe_part(value, fallback):
    value = str(value or fallback)
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return value or fallback


def fit_panel(image, size):
    image = ImageOps.exif_transpose(image).convert("RGB")
    return ImageOps.pad(image, size, method=Image.Resampling.LANCZOS, color=(248, 248, 248))


def build_side_by_side(original_bytes, result_bytes):
    panels = []
    source_images = [original_bytes] + result_bytes
    opened = [Image.open(BytesIO(data)) for data in source_images]
    max_w = max(img.width for img in opened)
    max_h = max(img.height for img in opened)
    panel_size = (max_w, max_h)
    for img in opened:
        panels.append(fit_panel(img, panel_size))

    gap = 12
    width = panel_size[0] * len(panels) + gap * (len(panels) - 1)
    height = panel_size[1]
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    x = 0
    for panel in panels:
        canvas.paste(panel, (x, 0))
        x += panel_size[0] + gap
    return canvas


def write_draft(path, lead):
    title = lead.get("title", "").strip()
    lines = [
        DRAFT,
        "",
        "Thread:",
        lead["thread_url"],
    ]
    if title:
        lines.extend(["", f"Context: {title}"])
    lines.extend(["", "Reminder: post manually only."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(entries):
    index_path = OUT_DIR / "index.md"
    lines = [
        "# ShotPro Reddit Makeovers",
        "",
        "Generate + draft only. Do not auto-post; human review and manual Reddit replies only.",
        "",
    ]
    if not entries:
        lines.append("_No makeovers generated._")
    for entry in entries:
        lines.extend(
            [
                f"## {entry['author']} / {entry['thread_id']}",
                f"- Thread: {entry['thread_url']}",
                f"- Image: `{entry['image_path']}`",
                f"- Draft: `{entry['draft_path']}`",
                "",
            ]
        )
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path


def main():
    leads = read_leads(LEADS_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = []

    print(f"Reading {len(leads)} lead(s) from {LEADS_PATH}")
    print(f"ShotPro endpoint: {GENERATE_URL}")
    print("Reminder: generate + draft only; never auto-post.")

    with tempfile.TemporaryDirectory(prefix="shotpro-reddit-") as tmp:
        tmpdir = Path(tmp)
        for idx, lead in enumerate(leads, 1):
            tid = safe_part(thread_id(lead["thread_url"]), "thread")
            author = safe_part(lead.get("author"), "unknown")
            stem = f"{author}__{tid}"
            png_path = OUT_DIR / f"{stem}.png"
            draft_path = OUT_DIR / f"{stem}.txt"

            print(f"[{idx}/{len(leads)}] {stem}: downloading source")
            original_bytes, ext = download_image(lead["image_url"])
            source_path = tmpdir / f"{stem}{ext}"
            source_path.write_bytes(original_bytes)

            results = []
            for style in STYLES:
                print(f"[{idx}/{len(leads)}] {stem}: generating {style}")
                results.append(post_generate(original_bytes, source_path.name, style))

            print(f"[{idx}/{len(leads)}] {stem}: writing review assets")
            build_side_by_side(original_bytes, results).save(png_path)
            write_draft(draft_path, lead)
            entries.append(
                {
                    "author": author,
                    "thread_id": tid,
                    "thread_url": lead["thread_url"],
                    "image_path": str(png_path),
                    "draft_path": str(draft_path),
                }
            )

    index_path = write_index(entries)
    print(f"Done. Wrote {len(entries)} makeover(s).")
    print(f"Index: {index_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
