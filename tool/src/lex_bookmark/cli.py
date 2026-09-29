"""lex-bookmark — bring bookmarks into a git-lex bookmark library and fetch their pages.

  lex-bookmark add <url> [--title T] [--note N]   add one link by hand
  lex-bookmark sync <source>                      import new bookmarks (pinboard, x)
  lex-bookmark fetch [--limit N]                  fetch pages for bookmarks without a PageSource
  lex-bookmark auth x                             sign in to X once

Run inside the library repo (or pass --repo). Each run ends with one `git lex save`.
The tool writes Bookmarks and PageSources only. Assessments are an agent's job (see the kit's skills).
"""

import argparse
from pathlib import Path

from . import fetch, sources
from .library import Library
from .sources import Item


def main() -> None:
    ap = argparse.ArgumentParser(prog="lex-bookmark", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="the bookmark library repo (default: current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("url")
    a.add_argument("--title", default="")
    a.add_argument("--note", default="")
    s = sub.add_parser("sync")
    s.add_argument("source")
    f = sub.add_parser("fetch")
    f.add_argument("--limit", type=int, default=50)
    au = sub.add_parser("auth")
    au.add_argument("source", choices=["x"])
    args = ap.parse_args()

    if args.cmd == "auth":
        sources.get(args.source).auth()
        return

    lib = Library(Path(args.repo))

    if args.cmd == "add":
        doc_id = lib.add_bookmark(Item(url=args.url, source="manual", title=args.title, note=args.note))
        if doc_id is None:
            print("Already in the library.")
            return
        lib.save(f"bookmark added by hand: {doc_id} — lex-bookmark")
        print(f"Added {doc_id}.")

    elif args.cmd == "sync":
        items = sources.get(args.source).fetch_items()
        added = [doc_id for item in items if (doc_id := lib.add_bookmark(item))]
        if added:
            lib.save(f"{len(added)} new bookmark(s) from {args.source} — lex-bookmark")
        print(f"{args.source}: {len(items)} seen, {len(added)} new.")

    elif args.cmd == "fetch":
        todo = [b for b in lib.bookmark_ids() if not lib.has("PageSource", b)][: args.limit]
        ok_count = 0
        for doc_id in todo:
            ok, title, final_url, text = fetch.page(lib.bookmark_url(doc_id))
            lib.add_page_source(doc_id, title, final_url, ok, text)
            ok_count += ok
            print(f"{'ok    ' if ok else 'failed'} {doc_id}")
        if todo:
            lib.save(f"fetched {len(todo)} page(s), {ok_count} readable — lex-bookmark")
        print(f"{len(todo)} fetched, {ok_count} readable.")


if __name__ == "__main__":
    main()
