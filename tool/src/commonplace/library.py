"""Writing Bookmark and PageSource documents into a commonplace repo.

Every document is started with `git lex create` and then filled in, and a run ends with one
`git lex save`. The tool never writes assessments, Subjects or Insights; those are the agent's.
"""

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = re.compile(r"^(utm_|fbclid$|gclid$|mc_|ref$|ref_src$|s$|t$)")
NS = "commonplace"


class Commonplace:
    def __init__(self, root: Path):
        self.root = root.resolve()
        if not (self.root / ".lex").is_dir():
            raise SystemExit(f"{self.root} is not a git-lex repo. Run inside a commonplace.")
        self.folder = self.root / "Commonplace"

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
    def url_hash(cls, url: str) -> str:
        return hashlib.sha1(cls.normalize(url).encode()).hexdigest()[:6]

    @classmethod
    def id_for(cls, url: str, title: str = "") -> str:
        """A readable slug from the title (or the address when there is none), plus a hash of the
        URL. The hash is what makes the same link saved twice one document."""
        if title and not title.startswith(("http://", "https://")):
            words = title
        else:
            parts = urlsplit(cls.normalize(url))
            words = f"{parts.netloc} {parts.path}"
        slug = re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")[:60].strip("-") or "link"
        return f"{slug}-{cls.url_hash(url)}"

    def path(self, cls: str, doc_id: str) -> Path:
        return self.folder / cls / f"{doc_id}.md"

    def has(self, cls: str, doc_id: str) -> bool:
        return self.path(cls, doc_id).exists()

    def find_bookmark(self, url: str) -> str | None:
        """The id of the Bookmark for this URL, whatever its title slug, if there is one."""
        found = sorted((self.folder / "Bookmark").glob(f"*-{self.url_hash(url)}.md"))
        return found[0].stem if found else None

    def bookmark_ids(self) -> list[str]:
        return sorted(p.stem for p in (self.folder / "Bookmark").glob("*.md") if not p.name.startswith("__"))

    def bookmark_url(self, doc_id: str) -> str:
        m = re.search(rf"^{NS}\.Bookmark\.url:\s*(.+)$", self.path("Bookmark", doc_id).read_text(), re.M)
        return json.loads(m.group(1)) if m else ""

    def post_links(self, doc_id: str) -> list[str]:
        """Outside links listed in a bookmarked post (an X post's 'Links in the post')."""
        text = self.path("Bookmark", doc_id).read_text()
        if "Links in the post:" not in text:
            return []
        block = text.split("Links in the post:", 1)[1].split("\n## ", 1)[0]
        links = re.findall(r"^- (https?://\S+)", block, re.M)
        return [u for u in links if urlsplit(u).netloc.lower().removeprefix("www.") not in ("x.com", "twitter.com", "t.co")]

    def source_id(self, doc_id: str) -> str:
        m = re.search(rf"^{NS}\.Bookmark\.sourceId:\s*(.+)$", self.path("Bookmark", doc_id).read_text(), re.M)
        return json.loads(m.group(1)) if m else ""

    def needs_context(self, source: str) -> list[str]:
        """Bookmarks from a source whose body has no Context section yet."""
        out = []
        for doc_id in self.bookmark_ids():
            text = self.path("Bookmark", doc_id).read_text()
            if f'{NS}.Bookmark.source: "{source}"' in text and "\n## Context\n" not in text:
                out.append(doc_id)
        return out

    def add_context(self, doc_id: str, lines: list[str]) -> None:
        """Insert a Context section just before the Assessment. The tool's section, not the agent's."""
        path = self.path("Bookmark", doc_id)
        text = path.read_text()
        section = "## Context\n\n" + "\n".join(lines).strip() + "\n\n"
        if "\n## Assessment" in text:
            text = text.replace("\n## Assessment", "\n" + section + "## Assessment", 1)
        else:
            text = text.rstrip() + "\n\n" + section
        path.write_text(text)

    # ---- writing ----------------------------------------------------------------------------

    def _git_lex(self, *args: str) -> None:
        r = subprocess.run(["git", "lex", *args], cwd=self.root, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git lex {' '.join(args)} failed:\n{r.stdout}\n{r.stderr}")

    def _write(self, cls: str, doc_id: str, fields: dict, body: str) -> None:
        """git lex create, then replace the template with the filled document."""
        self._git_lex("create", cls.lower(), doc_id)
        prefix = f"{NS}.{cls}."
        id_key = cls[0].lower() + cls[1:] + "Id"
        lines = ["---", f"type: {cls}", f"{prefix}id: <{NS}/{cls}/{doc_id}>", f"{prefix}{id_key}: {json.dumps(doc_id)}"]
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
        """Write a Bookmark for an item. Returns its id, or None if the commonplace already has it."""
        if self.find_bookmark(item.url):
            return None
        title = " ".join(item.title.split()) or item.url  # one line: titles land in RDF literals
        doc_id = self.id_for(item.url, title)
        details = item.details or (["Added by hand."] if item.source == "manual" else [f"Saved on {item.source}."])
        body = [f"# {title}", "", "## Saved note", "", item.note.strip(), "", "## From the source", "", *details,
                "", "## Assessment", "", "*Not assessed yet.*"]
        self._write(
            "Bookmark",
            doc_id,
            {
                "title": title,
                "url": item.url,
                "source": item.source,
                "sourceId": item.source_id,
                "savedDate": item.saved,
                "bookmarkStatus": "new",
            },
            "\n".join(body),
        )
        return doc_id

    def add_page_source(self, doc_id: str, title: str, final_url: str, ok: bool, text: str) -> None:
        title = " ".join(title.split()) or final_url  # one line: titles land in RDF literals
        body = [f"# {title}", "", "## Text", "", text]
        self._write(
            "PageSource",
            doc_id,
            {
                "title": title,
                "relatedToId": [f"<{NS}/Bookmark/{doc_id}>"],
                "fetchedDate": datetime.now().astimezone().replace(microsecond=0),
                "finalUrl": final_url,
                "fetchStatus": "ok" if ok else "failed",
            },
            "\n".join(body),
        )

    def save(self, message: str) -> None:
        self._git_lex("save", message)
