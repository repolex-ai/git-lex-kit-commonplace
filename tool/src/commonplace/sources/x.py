"""X (x.com) bookmarks, through the official API.

Needs your own developer app (developer.x.com) with OAuth 2.0 turned on, type "Native App",
callback URL http://127.0.0.1:8723/callback, and X_CLIENT_ID set. Run `commonplace auth x`
once to sign in; the token is kept in ~/.config/commonplace/, never in the commonplace repo.

Reading your own bookmarks with your own app is billed as an "Owned Read" (about $0.001 each
since 2026-04-20). X does not say when a post was bookmarked, so savedDate is left empty.
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import time
import urllib.parse
import webbrowser
from pathlib import Path

import httpx

from . import Item

NAME = "x"
API = "https://api.x.com/2"
AUTHORIZE = "https://x.com/i/oauth2/authorize"
TOKEN = "https://api.x.com/2/oauth2/token"
REDIRECT = "http://127.0.0.1:8723/callback"
SCOPES = "tweet.read users.read bookmark.read offline.access"
TOKEN_FILE = Path.home() / ".config" / "commonplace" / "x-token.json"


def _client_id() -> str:
    cid = os.environ.get("X_CLIENT_ID")
    if not cid:
        raise SystemExit("Set X_CLIENT_ID to your X developer app's OAuth 2.0 client id.")
    return cid


def _save_token(data: dict) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["expires_at"] = time.time() + data.get("expires_in", 7200) - 60
    TOKEN_FILE.write_text(json.dumps(data))
    TOKEN_FILE.chmod(0o600)


def auth() -> None:
    """Sign in once in the browser; keeps a refreshable token."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    params = {
        "response_type": "code",
        "client_id": _client_id(),
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    got: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            got.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Signed in. You can close this tab.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 8723), Handler)
    webbrowser.open(f"{AUTHORIZE}?{urllib.parse.urlencode(params)}")
    print("Waiting for you to approve in the browser…")
    server.handle_request()
    if got.get("state", [""])[0] != state or "code" not in got:
        raise SystemExit("Sign-in did not complete.")
    r = httpx.post(
        TOKEN,
        data={
            "grant_type": "authorization_code",
            "code": got["code"][0],
            "redirect_uri": REDIRECT,
            "code_verifier": verifier,
            "client_id": _client_id(),
        },
    )
    r.raise_for_status()
    _save_token(r.json())
    print(f"Signed in. Token kept at {TOKEN_FILE}.")


def _access_token() -> str:
    if not TOKEN_FILE.exists():
        raise SystemExit("Not signed in to X. Run: commonplace auth x")
    data = json.loads(TOKEN_FILE.read_text())
    if time.time() > data.get("expires_at", 0):
        r = httpx.post(
            TOKEN,
            data={"grant_type": "refresh_token", "refresh_token": data["refresh_token"], "client_id": _client_id()},
        )
        r.raise_for_status()
        data = r.json()
        _save_token(data)
    return data["access_token"]


def fetch_items(known=lambda url: False) -> list[Item]:
    headers = {"Authorization": f"Bearer {_access_token()}"}
    me = httpx.get(f"{API}/users/me", headers=headers).raise_for_status().json()["data"]
    items, token = [], None
    while True:
        params = {
            "max_results": 100,
            "expansions": "author_id",
            "post.fields": "created_at,text,entities",
            "user.fields": "username,name",
        }
        if token:
            params["pagination_token"] = token
        page = httpx.get(f"{API}/users/{me['id']}/bookmarks", headers=headers, params=params).raise_for_status().json()
        users = {u["id"]: u for u in page.get("includes", {}).get("users", [])}
        for post in page.get("data", []):
            author = users.get(post.get("author_id"), {})
            handle = author.get("username", "i")
            details = [f"Post by {author.get('name', handle)} (@{handle}), {post.get('created_at', '')}:", ""]
            details += [f"> {line}" for line in post.get("text", "").splitlines()]
            links = [u.get("expanded_url") for u in post.get("entities", {}).get("urls", []) if u.get("expanded_url")]
            if links:
                details += ["", "Links in the post:"] + [f"- {link}" for link in links]
            items.append(
                Item(
                    url=f"https://x.com/{handle}/status/{post['id']}",
                    source=NAME,
                    source_id=post["id"],
                    title=f"@{handle}: {' '.join(post.get('text', '').split())[:80]}",
                    details=details,
                )
            )
        # Bookmarks arrive newest first, and each one read costs money. Once a page holds a
        # bookmark the commonplace already has, everything older is already in too.
        seen_known = any(known(item.url) for item in items[-len(page.get("data", [])) :]) if page.get("data") else False
        token = page.get("meta", {}).get("next_token")
        if not token or seen_known:
            return items


def _full_text(post: dict) -> str:
    """A long post's whole text lives in note_post; `text` stops at 280 characters."""
    note = post.get("note_post") or post.get("note_tweet") or {}
    return (note.get("text") or post.get("text") or "").strip()


def fetch_context(post_ids: list[str]) -> dict[str, list[str]]:
    """For each post id, markdown lines giving the context a bookmark needs to be understood:
    the full text of a long post, its X Article, and the post it replies to or quotes."""
    headers = {"Authorization": f"Bearer {_access_token()}"}
    out: dict[str, list[str]] = {}
    for i in range(0, len(post_ids), 100):
        params = {
            "ids": ",".join(post_ids[i : i + 100]),
            "post.fields": "text,note_post,article,created_at,author_id,referenced_posts,conversation_id",
            "expansions": "author_id,referenced_posts.id,referenced_posts.id.author_id",
            "user.fields": "username,name",
        }
        page = httpx.get(f"{API}/tweets", headers=headers, params=params).raise_for_status().json()
        inc = page.get("includes", {})
        users = {u["id"]: u for u in inc.get("users", [])}
        refs = {p["id"]: p for p in inc.get("posts", inc.get("tweets", []))}

        def who(p: dict) -> str:
            return "@" + users.get(p.get("author_id"), {}).get("username", "unknown")

        for post in page.get("data", []):
            lines: list[str] = []
            full = _full_text(post)
            if len(full) > len(post.get("text", "")):
                lines += ["**The whole post** (the saved text was cut at 280 characters):", ""]
                lines += [f"> {line}" for line in full.splitlines()] + [""]
            article = post.get("article") or {}
            if article:
                lines += [f"**X Article:** {article.get('title', '(untitled)')}", ""]
                body = article.get("plain_text") or article.get("preview_text") or ""
                lines += [f"> {line}" for line in body.splitlines()] + ([""] if body else [])
            for ref in post.get("referenced_posts", post.get("referenced_tweets", [])):
                target = refs.get(ref.get("id"))
                label = {"replied_to": "In reply to", "quoted": "Quoting", "retweeted": "Reposting"}.get(ref.get("type"), "Referencing")
                if not target:
                    lines += [f"**{label}** a post that is deleted or not visible ({ref.get('id')}).", ""]
                    continue
                lines += [f"**{label} {who(target)}**, {target.get('created_at', '')}:", ""]
                lines += [f"> {line}" for line in _full_text(target).splitlines()] + [""]
            out[post["id"]] = lines or ["No further context: the post stands on its own."]
    return out
