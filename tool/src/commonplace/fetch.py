"""Fetch a page and turn its main content into readable markdown, with trafilatura."""

from urllib.parse import urlsplit

import httpx
import trafilatura

# Pages that need a login or JavaScript and return no readable text to a plain fetch.
# An X bookmark already carries the post text in its Bookmark body.
SKIP_HOSTS = {"x.com", "twitter.com", "mobile.twitter.com"}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; commonplace; +https://github.com/repolex-ai/git-lex-kit-commonplace)"}


def is_post(url: str) -> bool:
    return urlsplit(url).netloc.lower().removeprefix("www.") in SKIP_HOSTS


def page(url: str) -> tuple[bool, str, str, str]:
    """Returns (ok, title, final_url, markdown-or-reason)."""
    if is_post(url):
        return False, url, url, "Not fetched: the post has no outside link, and its text is already in the Bookmark."
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
        r.raise_for_status()
    except httpx.HTTPError as e:
        return False, url, url, f"Fetch failed: {e}"
    final_url = str(r.url)
    if "html" not in r.headers.get("content-type", "html"):
        return False, url, final_url, f"Not a web page ({r.headers.get('content-type')})."
    text = trafilatura.extract(r.text, url=final_url, output_format="markdown", include_links=True, include_tables=True)
    meta = trafilatura.extract_metadata(r.text, default_url=final_url)
    title = (meta.title if meta and meta.title else "") or url
    if not text:
        return False, title, final_url, "Fetched, but no readable main text was found."
    return True, title, final_url, text
