"""commonplace — bring bookmarks into a git-lex commonplace and fetch their pages.

  commonplace add <url> [--title T] [--note N]   add one link by hand
  commonplace sync <source>                      import new bookmarks (pinboard, x)
  commonplace fetch [--limit N]                  fetch pages for bookmarks without a PageSource
  commonplace enrich x                           add each X bookmark's context: whole post, Article, reply/quote
  commonplace auth x                             sign in to X once

Run inside the commonplace repo (or pass --repo). Each run ends with one `git lex save`.
The tool writes Bookmarks and PageSources only. Assessing is an agent's job (see the kit's skills).

Secrets are read from the environment, or from ~/.config/commonplace/env (KEY=value lines).
They never go in the repo.
"""

import argparse
import os

import httpx
from pathlib import Path

from . import fetch, sources
from .library import Commonplace
from .sources import Item

ENV_FILE = Path.home() / ".config" / "commonplace" / "env"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def main() -> None:
    ap = argparse.ArgumentParser(prog="commonplace", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="the commonplace repo (default: current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("url")
    a.add_argument("--title", default="")
    a.add_argument("--note", default="")
    s = sub.add_parser("sync")
    s.add_argument("source")
    f = sub.add_parser("fetch")
    f.add_argument("--limit", type=int, default=50)
    en = sub.add_parser("enrich")
    en.add_argument("source", choices=["x"])
    au = sub.add_parser("auth")
    au.add_argument("source", choices=["x"])
    args = ap.parse_args()
    load_env()

    if args.cmd == "auth":
        sources.get(args.source).auth()
        return

    book = Commonplace(Path(args.repo))

    if args.cmd == "add":
        doc_id = book.add_bookmark(Item(url=args.url, source="manual", title=args.title, note=args.note))
        if doc_id is None:
            print("Already in the commonplace.")
            return
        book.save(f"bookmark added by hand: {doc_id} — commonplace")
        print(f"Added {doc_id}.")

    elif args.cmd == "sync":
        try:
            items = sources.get(args.source).fetch_items(known=lambda url: book.find_bookmark(url) is not None)
        except httpx.HTTPStatusError as e:
            r = e.response
            hint = {
                401: "The sign-in token was refused. Run `commonplace auth x` again.",
                402: "The API account has no credit. Add credit in the developer console's billing page.",
                403: "The app isn't allowed this call. Check its permissions and sign-in settings.",
                429: "Rate limited. Wait and try again later.",
            }.get(r.status_code, "")
            raise SystemExit(f"{args.source}: {r.status_code} {r.reason_phrase}. {hint}\n{r.text[:500]}")
        added = [doc_id for item in items if (doc_id := book.add_bookmark(item))]
        if added:
            book.save(f"{len(added)} new bookmark(s) from {args.source} — commonplace")
        print(f"{args.source}: {len(items)} seen, {len(added)} new.")

    elif args.cmd == "enrich":
        by_post = book.posts_needing_context()
        context = sources.get(args.source).fetch_context(list(by_post))
        for post_id, doc_id in by_post.items():
            book.add_context(doc_id, context.get(post_id, ["Not returned by X: the post may be deleted or protected."]))
        if by_post:
            book.save(f"context added to {len(by_post)} {args.source} bookmark(s) — commonplace")
        print(f"{args.source}: context added to {len(by_post)} bookmark(s).")

    elif args.cmd == "fetch":
        todo = [b for b in book.bookmark_ids() if not book.has("PageSource", b)][: args.limit]
        ok_count = 0
        for doc_id in todo:
            url = book.bookmark_url(doc_id)
            if fetch.is_post(url):
                # A post page can't be read without the API; its text is already in the Bookmark.
                # What's worth fetching is the first outside link the post points at.
                links = book.post_links(doc_id)
                url = links[0] if links else url
            try:
                ok, title, final_url, text = fetch.page(url)
            except Exception as e:  # a page that breaks the extractor is a failed page, not a crashed run
                ok, title, final_url, text = False, url, url, f"Could not read the page: {e}"
            book.add_page_source(doc_id, title, final_url, ok, text)
            ok_count += ok
            print(f"{'ok    ' if ok else 'failed'} {doc_id}")
        if todo:
            book.save(f"fetched {len(todo)} page(s), {ok_count} readable — commonplace")
        print(f"{len(todo)} fetched, {ok_count} readable.")


if __name__ == "__main__":
    main()
