# Worth reading

Bookmarks assessed as worth reading in full, best first.

```sparql
SELECT ?bookmark ?worth ?status
WHERE {
  ?bookmark a <https://repolex.ai/ontology/commonplace/Bookmark> ;
            <https://repolex.ai/ontology/commonplace/worth> ?worth ;
            <https://repolex.ai/ontology/commonplace/bookmarkStatus> ?status .
  FILTER (?worth != "low")
}
ORDER BY ?worth ?bookmark
```
