# Bookmarks with no page fetched yet

What `commonplace fetch` will pick up next.

```sparql
SELECT ?bookmark ?url
WHERE {
  ?bookmark a <https://repolex.ai/ontology/commonplace/Bookmark> ;
            <https://repolex.ai/ontology/commonplace/url> ?url .
  FILTER NOT EXISTS {
    ?page a <https://repolex.ai/ontology/commonplace/PageSource> ;
          <https://repolex.ai/ontology/git-lex/relatedToId> ?bookmark .
  }
}
ORDER BY ?bookmark
```
