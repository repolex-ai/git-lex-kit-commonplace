---
name: commonplace-base-connect
description: Look across the whole commonplace for connections — themes, tensions, surprises — and write them up as Insights. The slow, weekly pass.
---

# commonplace-base-connect

The pass that turns a pile of links into something worth reading. Run it weekly, or when many
new assessments have landed.

## Steps

1. Read what is there: `git lex query commonplace-subjects` for the subjects the reading
   circles most, every existing Insight, and the Bookmarks assessed since the last pass
   (`git lex query recent` helps).
2. Look for:
   - **themes**: several bookmarks circling one subject or one question;
   - **tensions**: two bookmarks that disagree, and what the disagreement is really about;
   - **surprises**: something saved years apart that turns out to be the same thought;
   - **gaps**: a subject with many saves and nothing marked `high`.
3. For each real finding, write an Insight: `git lex create insight <name>`. Say the finding
   plainly, then where it came from. Link every Bookmark and Subject it rests on, both in
   `relatedToId` and as markdown links in the body.
4. End with a short digest: this pass's Insights, one line each, as your final message to the
   person. That digest is what they will actually read.
5. `git lex save "connect pass: <n> insight(s) — <your name>"`.

## Never

- Never write an Insight that one bookmark alone supports. That belongs in its assessment.
- Never invent a connection to reach a number. Zero Insights is a valid pass.
