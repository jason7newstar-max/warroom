#!/usr/bin/env python3
"""Fill the T-027 micro-site template from a client JSON file."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "tasks" / "T-027" / "template" / "index.html"
TOKEN_RE = re.compile(r"{{([A-Z0-9_]+)}}")


def required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value.strip()


def required_services(data: dict[str, Any]) -> list[dict[str, str]]:
    services = data.get("services")
    if not isinstance(services, list) or len(services) != 3:
        raise ValueError("services must be a list of exactly 3 items")

    cleaned: list[dict[str, str]] = []
    for index, item in enumerate(services, 1):
        if not isinstance(item, dict):
            raise ValueError(f"services[{index}] must be an object")
        cleaned.append(
            {
                "name": required_text(item, "name"),
                "desc": required_text(item, "desc"),
                "price": required_text(item, "price"),
            }
        )
    return cleaned


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_tokens(data: dict[str, Any]) -> dict[str, str]:
    brand = required_text(data, "brand")
    category = required_text(data, "category")
    tagline = required_text(data, "tagline")
    about = required_text(data, "about")
    address = required_text(data, "address")
    hours = required_text(data, "hours")
    contact_email = required_text(data, "contact_email")
    services = required_services(data)

    tokens = {
        "BRAND": brand,
        "CATEGORY": category,
        "TAGLINE": tagline,
        "CTA_EMAIL": contact_email,
        "CTA_LABEL": "Book a visit",
        "SECONDARY_CTA": "View menu",
        "ABOUT_HEADLINE": f"Inside {brand}",
        "ABOUT": about,
        "HIGHLIGHT_STAT": "3",
        "HIGHLIGHT_TEXT": "Signature offers ready for the site preview.",
        "SERVICES_HEADLINE": "Featured menu",
        "GALLERY_HEADLINE": "A quick visual direction",
        "CONTACT_HEADLINE": "Bring the next visit onto the calendar",
        "CONTACT_COPY": f"Send {brand} a note for reservations, catering, private events, or press inquiries.",
        "ADDRESS": address,
        "HOURS": hours,
        "CONTACT_BUTTON": "Email the team",
        "FOOTER_NOTE": f"{category} - Micro-site by ONE TEN LAB",
    }

    labels = ["Signature", "Guest Favorite", "Seasonal"]
    for index, service in enumerate(services, 1):
        tokens[f"SERVICE_{index}_LABEL"] = labels[index - 1]
        tokens[f"SERVICE_{index}_NAME"] = service["name"]
        tokens[f"SERVICE_{index}_DESC"] = service["desc"]
        tokens[f"SERVICE_{index}_PRICE"] = service["price"]
        tokens[f"GALLERY_{index}_TITLE"] = service["name"]
        tokens[f"GALLERY_{index}_CAPTION"] = service["desc"]
        tokens[f"GALLERY_{index}_ALT"] = f"{brand} {service['name']} preview"

    return {key: esc(value) for key, value in tokens.items()}


def fill_site(client_json: Path, output_html: Path) -> None:
    data = json.loads(client_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("client JSON root must be an object")

    html_text = TEMPLATE.read_text(encoding="utf-8")
    tokens = build_tokens(data)

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token not in tokens:
            raise ValueError(f"no value available for template token: {token}")
        return tokens[token]

    rendered = TOKEN_RE.sub(replace, html_text)
    leftovers = sorted(set(TOKEN_RE.findall(rendered)))
    if leftovers:
        raise ValueError(f"unfilled template tokens: {', '.join(leftovers)}")

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(rendered, encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Fill tasks/T-027/template/index.html from a client JSON file."
    )
    parser.add_argument("client_json", type=Path, help="Path to client details JSON.")
    parser.add_argument("output_html", type=Path, help="Path to write the filled index.html.")
    args = parser.parse_args(argv)

    try:
        fill_site(args.client_json, args.output_html)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"fill_site.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
