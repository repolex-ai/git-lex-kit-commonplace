# Bookmarks nobody has assessed yet

The work queue for the `bookmark-base-assess` skill.

```sparql
SELECT ?bookmark ?url
WHERE {
  ?bookmark a <https://repolex.ai/ontology/bookmark/Bookmark> ;
            <https://repolex.ai/ontology/bookmark/url> ?url .
  FILTER NOT EXISTS {
    ?assessment a <https://repolex.ai/ontology/bookmark/Assessment> ;
                <https://repolex.ai/ontology/git-lex/relatedToId> ?bookmark .
  }
}
ORDER BY ?bookmark
```
