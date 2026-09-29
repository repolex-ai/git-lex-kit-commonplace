# Bookmarks with no page fetched yet

What `lex-bookmark fetch` will pick up next.

```sparql
SELECT ?bookmark ?url
WHERE {
  ?bookmark a <https://repolex.ai/ontology/bookmark/Bookmark> ;
            <https://repolex.ai/ontology/bookmark/url> ?url .
  FILTER NOT EXISTS {
    ?page a <https://repolex.ai/ontology/bookmark/PageSource> ;
          <https://repolex.ai/ontology/git-lex/relatedToId> ?bookmark .
  }
}
ORDER BY ?bookmark
```
