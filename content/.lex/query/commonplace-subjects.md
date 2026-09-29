# Subjects, by how much the reading mentions them

Every Subject with its kind and the number of bookmarks linked to it.

```sparql
SELECT ?subject ?kind (COUNT(DISTINCT ?bookmark) AS ?bookmarks)
WHERE {
  ?subject a <https://repolex.ai/ontology/commonplace/Subject> .
  OPTIONAL { ?subject <https://repolex.ai/ontology/commonplace/subjectKind> ?kind }
  OPTIONAL { ?bookmark a <https://repolex.ai/ontology/commonplace/Bookmark> ; <https://repolex.ai/ontology/git-lex/relatedToId> ?subject }
}
GROUP BY ?subject ?kind
ORDER BY DESC(?bookmarks)
```
