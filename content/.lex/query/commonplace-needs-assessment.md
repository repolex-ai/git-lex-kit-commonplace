# Bookmarks waiting for an assessment

The work queue for the `commonplace-base-assess` skill: status new, or no status at all.

```sparql
SELECT ?bookmark ?url
WHERE {
  ?bookmark a <https://repolex.ai/ontology/commonplace/Bookmark> ;
            <https://repolex.ai/ontology/commonplace/url> ?url .
  OPTIONAL { ?bookmark <https://repolex.ai/ontology/commonplace/bookmarkStatus> ?status }
  FILTER (!BOUND(?status) || ?status = "new")
}
ORDER BY ?bookmark
```
