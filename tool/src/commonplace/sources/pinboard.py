"""Pinboard (pinboard.in). Needs PINBOARD_TOKEN, from https://pinboard.in/settings/password.

posts/all may be called once every five minutes; one call returns every bookmark.
"""

import os
from datetime import datetime

import httpx

from . import Item

NAME = "pinboard"
API = "https://api.pinboard.in/v1"


def fetch_items(known=lambda url: False) -> list[Item]:
    token = os.environ.get("PINBOARD_TOKEN")
    if not token:
        raise SystemExit("Set PINBOARD_TOKEN (user:TOKEN, from https://pinboard.in/settings/password).")
    r = httpx.get(f"{API}/posts/all", params={"auth_token": token, "format": "json"}, timeout=120)
    r.raise_for_status()
    items = []
    for post in r.json():
        details = []
        if post.get("tags"):
            details.append(f"Tags: {post['tags']}")
        if post.get("toread") == "yes":
            details.append("Marked to read later.")
        items.append(
            Item(
                url=post["href"],
                source=NAME,
                source_id=post.get("hash", ""),
                title=post.get("description", ""),
                saved=datetime.fromisoformat(post["time"].replace("Z", "+00:00")) if post.get("time") else None,
                note=post.get("extended", ""),
                details=details,
            )
        )
    return items
