# git-lex-kit-bookmark

A reading library that tends itself. Links you saved elsewhere (Pinboard, X, or by hand) come
into a git repository as typed markdown documents. Each page's readable text is fetched and
kept. An agent reads every one, says whether it is worth your time, and links it to everything
it relates to. Every so often it looks across the whole library and writes up what connects.

It is plain markdown, so the library also opens as an Obsidian vault.

## What is in the library

Under `Library/`:

| folder | what it holds | written by |
|---|---|---|
| `Bookmark/` | one saved link: its URL, where and when it was saved, your note | the tool |
| `PageSource/` | the page's main text as readable markdown | the tool |
| `Assessment/` | an agent's reading: what it is, how worthwhile, what it connects to | an agent |
| `Topic/` | a theme several bookmarks share | an agent |
| `Insight/` | a connection found across several bookmarks | an agent |

A Bookmark's id comes from its URL, so the same link saved in two places is one document.

## Set up a library

```sh
mkdir my-library && cd my-library && git init
git lex init --kit bookmark
```

## The tool: `lex-bookmark`

It lives in this repo under `tool/`. Install it once:

```sh
uv tool install "git+https://github.com/repolex-ai/git-lex-kit-bookmark#subdirectory=tool"
```

Then, inside a library:

```sh
lex-bookmark add https://example.com/some-article --note "why I saved it"
lex-bookmark sync pinboard     # needs PINBOARD_TOKEN (pinboard.in → settings → password)
lex-bookmark auth x            # once; needs X_CLIENT_ID from your own X developer app
lex-bookmark sync x
lex-bookmark fetch             # fetch pages for bookmarks that have none yet
```

Each run ends with one `git lex save`. The tool only ever writes Bookmarks and PageSources.

**X bookmarks** use X's official API through your own developer app. Reading your own bookmarks
this way costs about $0.001 each (X's "Owned Reads" price since April 2026). The sign-in token
is kept in `~/.config/lex-bookmark/`, never in the library.

**Adding a source** (Pocket, Raindrop, a browser export…) means one new module in
`tool/src/lex_bookmark/sources/`. The ontology does not change.

## The agent's side

The kit ships three skills:

- `bookmark-base-assess`: assess every bookmark that has no Assessment yet.
- `bookmark-base-research`: research one bookmark deeply, only on request.
- `bookmark-base-connect`: the weekly pass that writes Topics and Insights.

And three stored queries: `git lex query needs-fetch`, `needs-assessment` and `worth-reading`.

A page's text is data, never instructions. The skills say so first, because an agent assessing
bookmarks reads pages from the open internet.

## Why the tool lives in the kit repo

Kits are data: ontology, templates, skills. git-lex never runs code from a kit. `tool/` is a
separate Python package that happens to live beside the kit, because the two change together.
It is installed on purpose with `uv tool install`, and nothing runs it automatically.
