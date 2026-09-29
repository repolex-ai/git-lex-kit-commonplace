# git-lex-kit-commonplace

A commonplace book that keeps itself.

A commonplace book is the old practice of copying what you read into one book, arranged by
subject, to think with later. This kit does that for the links you save. Bookmarks from
Pinboard, X, or added by hand come into a git repository as typed markdown. Each page's text is
fetched and kept. An agent assesses every bookmark, and on request researches it. The research
accumulates on one document per *subject*: a person, a technology, an idea. Every so often the
agent looks across everything and writes up what connects.

It is plain markdown, so a commonplace also opens as an Obsidian vault.

## What is in a commonplace

Under `Commonplace/`:

| folder | what it holds | written by |
|---|---|---|
| `Bookmark/` | one saved link: URL, where and when it was saved, your note, then the agent's assessment | the tool creates it, an agent assesses it |
| `PageSource/` | the page's main text as readable markdown | the tool |
| `Subject/` | one thing the reading is about; research grows it | an agent |
| `SubjectKind/` | the kinds of subject: person, organization, technology, project, idea, work, and any added later | the kit ships six, an agent may add more |
| `Insight/` | a connection found across several bookmarks | an agent |

A Bookmark's `bookmarkStatus` moves from `new` to `assessed` to `researched`, and `worth` says
whether the page is worth reading in full (`high`, `medium`, `low`).

**Links.** Structural edges use `relatedToId`: a PageSource to its Bookmark, a Bookmark to its
Subjects, an Insight to what it rests on. Markdown links in the body carry *how* things relate,
and are what Obsidian's graph shows.

**Subject kinds can grow.** A kind is a document, not a fixed list in the ontology. To add one,
an agent writes a new `SubjectKind` document. No kit release is needed. A Subject that names a
kind which does not exist is refused at save, so the vocabulary grows without drifting. (The six
shipped kinds are kit files: editing them locally is undone by the next `kit-update`, so add a
new kind instead.)

## Set up a commonplace

```sh
mkdir my-commonplace && cd my-commonplace && git init
git lex init --kit commonplace
```

## The tool: `commonplace`

It lives in this repo under `tool/`. Install it once:

```sh
uv tool install "git+https://github.com/repolex-ai/git-lex-kit-commonplace#subdirectory=tool"
```

Then, inside a commonplace:

```sh
commonplace add https://example.com/some-article --note "why I saved it"
commonplace sync pinboard
commonplace auth x          # once
commonplace sync x
commonplace fetch           # fetch pages for bookmarks that have none yet
```

Each run ends with one `git lex save`. The tool only creates Bookmarks and PageSources.

**Secrets never go in the repo.** Put them in the environment, or in `~/.config/commonplace/env`
as `KEY=value` lines:

- `PINBOARD_TOKEN`: from pinboard.in → settings → password, the `user:TOKEN` string.
- `X_CLIENT_ID`: the OAuth 2.0 client id of your own X developer app. After
  `commonplace auth x`, the sign-in token is kept in `~/.config/commonplace/x-token.json`.

**X bookmarks** go through X's official API with your own developer app. Reading your own
bookmarks this way costs about $0.001 each. Sync stops as soon as it reaches bookmarks the
commonplace already has, so it doesn't pay twice for old ones.

**Adding a source** (Pocket, Raindrop, a browser export…) means one new module in
`tool/src/commonplace/sources/`. The ontology does not change.

## The agent's side

Three skills:

- `commonplace-base-assess`: assess every bookmark still marked `new`.
- `commonplace-base-research`: research one bookmark deeply, on request only.
- `commonplace-base-connect`: the weekly pass that writes Insights.

Four stored queries: `commonplace-needs-fetch`, `commonplace-needs-assessment`,
`commonplace-worth-reading` and `commonplace-subjects`. Run them with `git lex query <name>` from
a session that **started inside the commonplace**, because a query answers from the repo the
session started in.

A page's text is data, never instructions. Every skill says so first.

## Why the tool lives beside the kit

Kits are data: ontology, templates, skills. git-lex never runs code from a kit. `tool/` is a
separate Python package that lives here because the two change together. It is installed on
purpose, and nothing runs it automatically.
