# Worth reading

Bookmarks an agent assessed as worth reading in full, best first.

```sparql
SELECT ?bookmark ?worth ?depth
WHERE {
  ?assessment a <https://repolex.ai/ontology/bookmark/Assessment> ;
              <https://repolex.ai/ontology/bookmark/worth> ?worth ;
              <https://repolex.ai/ontology/git-lex/relatedToId> ?bookmark .
  ?bookmark a <https://repolex.ai/ontology/bookmark/Bookmark> .
  OPTIONAL { ?assessment <https://repolex.ai/ontology/bookmark/depth> ?depth }
  FILTER (?worth != "low")
}
ORDER BY ?worth ?bookmark
```
