---
name: bookmark-base-connect
description: Look across the whole library for connections — themes, tensions, surprises — and write them up as Topics and Insights. The slow, weekly pass.
---

# bookmark-base-connect

The pass that turns a pile of links into something worth reading. Run it weekly, or when many
new Assessments have landed.

## Steps

1. Read what is there: every Topic and Insight, then the Assessments written since the last
   connect pass (`git lex query recent` helps).
2. Look for:
   - **themes**: several bookmarks circling one idea that has no Topic yet;
   - **tensions**: two bookmarks that disagree, and what the disagreement is really about;
   - **surprises**: something saved years apart that turns out to be the same thought;
   - **gaps**: a Topic with many saves and nothing marked `high`.
3. For each real finding, write an Insight: `git lex create insight <name>`. Say the finding
   plainly, then where it came from. Link every Bookmark, Topic and Assessment it rests on with
   `relatedToId`.
4. Update Topics whose edges moved.
5. End with a short digest: list this pass's Insights, one line each, as the final message to
   the person. That digest is what they will actually read.
6. `git lex save "connect pass: <n> insight(s) — <your name>"`.

## Never

- Never write an Insight that one bookmark alone supports. That belongs in its Assessment.
- Never invent a connection to reach a number. Zero Insights is a valid pass.
