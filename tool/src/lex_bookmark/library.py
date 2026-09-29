"""Writing Bookmark and PageSource documents into a bookmark library repo.

Every document is started with `git lex create` and then filled in, and a run ends with one
`git lex save`. The tool never writes Assessments, Topics or Insights; those are the agent's.
"""

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = re.compile(r"^(utm_|fbclid$|gclid$|mc_|ref$|ref_src$|s$|t$)")


class Library:
    def __init__(self, root: Path):
        self.root = root.resolve()
        if not (self.root / ".lex").is_dir():
            raise SystemExit(f"{self.root} is not a git-lex repo. Run inside a bookmark library.")
        self.folder = self.root / "Library"

    # ---- identity ---------------------------------------------------------------------------

    @staticmethod
    def normalize(url: str) -> str:
        """The form used for sameness: no fragment, no tracking parameters, no trailing slash."""
        parts = urlsplit(url.strip())
        query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not TRACKING.match(k)])
        host = parts.netloc.lower().removeprefix("www.")
        if host in ("twitter.com", "mobile.twitter.com", "mobile.x.com"):
            host = "x.com"
        return urlunsplit((parts.scheme.lower(), host, parts.path.rstrip("/"), query, ""))

    @classmethod
    def id_for(cls, url: str) -> str:
        norm = cls.normalize(url)
        parts = urlsplit(norm)
        slug = re.sub(r"[^a-z0-9]+", "-", f"{parts.netloc} {parts.path}".lower()).strip("-")[:60].strip("-")
        return f"{slug}-{hashlib.sha1(norm.encode()).hexdigest()[:6]}"

    def path(self, cls: str, doc_id: str) -> Path:
        return self.folder / cls / f"{doc_id}.md"

    def has(self, cls: str, doc_id: str) -> bool:
        return self.path(cls, doc_id).exists()

    def bookmark_ids(self) -> list[str]:
        return sorted(p.stem for p in (self.folder / "Bookmark").glob("*.md") if not p.name.startswith("__"))

    def bookmark_url(self, doc_id: str) -> str:
        m = re.search(r"^bookmark\.Bookmark\.url:\s*(.+)$", self.path("Bookmark", doc_id).read_text(), re.M)
        return json.loads(m.group(1)) if m else ""

    # ---- writing ----------------------------------------------------------------------------

    def _git_lex(self, *args: str) -> None:
        r = subprocess.run(["git", "lex", *args], cwd=self.root, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git lex {' '.join(args)} failed:\n{r.stdout}\n{r.stderr}")

    def _write(self, cls: str, doc_id: str, fields: dict, body: str) -> None:
        """git lex create, then replace the template with the filled document."""
        self._git_lex("create", cls.lower(), doc_id)
        prefix = f"bookmark.{cls}."
        lines = ["---", f"type: {cls}", f"{prefix}id: <bookmark/{cls}/{doc_id}>"]
        id_key = cls[0].lower() + cls[1:] + "Id"
        lines.append(f"{prefix}{id_key}: {json.dumps(doc_id)}")
        for key, value in fields.items():
            if value is None or value == "":
                continue
            if isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                lines += [f"  - {v}" for v in value]
            elif isinstance(value, datetime):
                lines.append(f"{prefix}{key}: {value.isoformat()}")
            else:
                lines.append(f"{prefix}{key}: {json.dumps(value, ensure_ascii=False)}")
        lines.append("---")
        self.path(cls, doc_id).write_text("\n".join(lines) + "\n\n" + body.strip() + "\n")

    def add_bookmark(self, item) -> str | None:
        """Write a Bookmark for an item. Returns its id, or None if the library already has it."""
        doc_id = self.id_for(item.url)
        if self.has("Bookmark", doc_id):
            return None
        title = item.title.strip() or item.url
        body = [f"# {title}", "", "## Saved note", "", item.note.strip(), "", "## From the source", ""]
        body += item.details or [f"Saved on {item.source}."]
        self._write(
            "Bookmark",
            doc_id,
            {"title": title, "url": item.url, "source": item.source, "sourceId": item.source_id, "savedDate": item.saved},
            "\n".join(body),
        )
        return doc_id

    def add_page_source(self, doc_id: str, title: str, final_url: str, ok: bool, text: str) -> None:
        body = [f"# {title}", "", "## Text", "", text]
        self._write(
            "PageSource",
            doc_id,
            {
                "title": title,
                "relatedToId": [f"<bookmark/Bookmark/{doc_id}>"],
                "fetchedDate": datetime.now().astimezone().replace(microsecond=0),
                "finalUrl": final_url,
                "fetchStatus": "ok" if ok else "failed",
            },
            "\n".join(body),
        )

    def save(self, message: str) -> None:
        self._git_lex("save", message)
