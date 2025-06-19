## Example Queries

### **1. Tags for a Movie**

Returns the genome tags and relevance scores for a given movie title:


```cypher
MATCH (m:Movie {title: $title})-[r:HAS_RELEVANCE]->(t:GenomeTag)
RETURN t.tag AS etiqueta, r.score AS relevancia
ORDER BY relevancia DESC
LIMIT $top
```

### **2. Movies by Tag Relevance**

Finds movies most associated with a given genome tag:

```cypher
MATCH (m:Movie)-[r:HAS_RELEVANCE]->(t:GenomeTag {tag: $tag})
RETURN m.title AS pelicula, r.score AS relevancia
ORDER BY relevancia DESC
LIMIT $top
```


### 3. **Similar Movies Based on High-Relevance Tags** 

Finds movies that share high-relevance genome tags with a given movie:

```cypher
MATCH (m1:Movie {title: $title})-[r1:HAS_RELEVANCE]->(t:GenomeTag)
WHERE r1.score > 0.8
WITH m1, COLLECT(t) AS etiquetas_filtradas
MATCH (m2:Movie)-[r2:HAS_RELEVANCE]->(t2:GenomeTag)
WHERE m2 <> m1 AND r2.score > 0.8 AND t2 IN etiquetas_filtradas
WITH m2, COUNT(DISTINCT t2) AS etiquetas_comunes_relevantes
RETURN m2.title AS pelicula_similar, etiquetas_comunes_relevantes
ORDER BY etiquetas_comunes_relevantes DESC
LIMIT $top
```
