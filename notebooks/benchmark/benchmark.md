# Comparativa de Rendimiento: Neo4j vs MongoDB

Sr analiza el rendimiento de las bases de datos **Neo4j** (modelo de grafos) y 
**MongoDB** (modelo de documentos) en tres operaciones fundamentales de procesamiento de datos:

1. Consultas de lectura simples y complejas.
2. Inserciones individuales y por lotes.
3. Actualizaciones de marcas de tiempo (`timestamp`) desde enteros UNIX a objetos `datetime`.

Cada operación fue ejecutada en escenarios controlados, midiendo métricas clave como latencia, uso de CPU, uso de memoria y throughput. 
El objetivo es entender el comportamiento y eficiencia de cada base en contextos reales de uso analítico.

---

## Entorno de Ejecución

Todos los benchmarks fueron realizados localmente bajo condiciones uniformes para asegurar resultados comparables.

```json
{
   "python_version": "3.12.1",
   "hardware": {
      "sistema_operativo": "macOS 24.5.0",
      "arquitectura": "x86_64",
      "procesador": "M2: 8 núcleos físicos (2.4 GHz)",
      "memoria": "16 GB RAM"
   }
}
```

### Versiones de Software

| Componente         | Versión                |
|--------------------|------------------------|
| Neo4j Server	      | 2025.05.0              |
| Neo4j Controller   | Python	Neo4j 5.28.1    |
| MongoDB Server     | 7.0.20                 |
| MongoDB Controller | PyMongo 4.13.1         |


---

## Resultados

### 1. Carga Inicial de Datos

Se utilizaron 500 usuarios aleatorios y sus correspondientes películas, calificaciones (ratings) y etiquetas.
A continuación se presentan los tiempos medidos para cada motor de base de datos durante el proceso de carga inicial.

#### Neo4j

| Tipo de Datos | Registros | Tiempo          |
| ------------- | --------- |-----------------|
| Usuarios      | 500       | 36.59 segundos  |
| Películas     | 7,141     | 127.62 segundos |
| Ratings       | 62,834    | 85.41 segundos  |
| Etiquetas     | 811,156   | 77.37 segundos  |
| Total         | —         | 168.17 segundos |

#### MongoDB

| Tipo de Datos | Registros | Tiempo        |
| ------------- | --------- | ------------- |
| Usuarios      | 500       | 0.33 segundos |
| Películas     | 7,141     | 0.33 segundos |
| Total         | —         | 0.33 segundos |

MongoDB presenta una carga inicial significativamente más rápida que Neo4j, principalmente debido a su modelo de documentos embebidos que no requiere relaciones explícitas.

---

## 2. Single-Threaded Benchmark: Lectura, Escritura y Actualización

En esta sección se presentan los resultados del benchmark que evalúa el rendimiento de MongoDB y 
Neo4j al ejecutar operaciones de lectura, escritura y actualización bajo condiciones controladas. 
El objetivo es observar el comportamiento de cada base bajo carga puntual y continua, midiendo desempeño individual por operación.

### Métricas Clave a Medir

Durante las pruebas de actualización de timestamps, se registraron las siguientes métricas clave para comparar objetivamente el rendimiento de ambos motores:

| Métrica                                        | Descripción                                                                                                                                                   |
|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Latencia Total (`wall_ms`)                     | Mide el tiempo real total por consulta, incluyendo cliente, servidor y red. Refleja la experiencia real del usuario.                                          |
| Latencia del Controlador (`driver_ms`)         | Mide el tiempo reportado por el controlador de la base de datos. Permite aislar el tiempo real del servidor, excluyendo el procesamiento del lado del cliente. |
| Uso de CPU del Sistema (`sys_cpu_pct`)         | Mide el porcentaje de utilización de CPU durante las consultas. Identifica cuellos de botella de procesamiento.                                               |
| Uso de Memoria del Sistema (`sys_mem_pct`)     | Mide el porcentaje de memoria RAM utilizada. Detecta problemas de saturación de memoria.                                                                      |
| Memoria RSS de MongoDB (`driver_mem_rss`) | Mide la memoria física utilizada por el proceso de MongoDB. Muestra el footprint de memoria real del servidor.                                                |
| Fallos de Página por Segundo (`major_faults`)  | Mide accesos a disco por falta de páginas en memoria. Indica problemas de I/O.                                                                                |
| Queries por Segundo (`throughput_qps`)         | Mide el proxy de Ancho de Banda teniendo en cuenta el throttling aplicado.                                                                                    |

### Estrategia de Ejecución

- Se utilizó una solo hilo para evitar paralelismo y medir latencia real por operación.
- Se simularon escenarios realistas con datos previamente cargados.
- Se aplicaron índices manualmente para optimizar rendimiento de lectura.
- Cada tipo de operación se ejecutó en intervalos de 20 segundos para la recolección de métricas, aplicando una espera (throttling) de 0.5 segundos entre ejecuciones consecutivas. 
Esta pausa tuvo como objetivo evitar conflictos por bloqueos (locks), lo que podría haber dificultado el análisis posterior.

### Índices Utilizados

#### MongoDB

```python
movies_col.create_index("movieId")
movies_col.create_index("genres")
users_col.create_index("userId")
```

#### Neo4j
```python
session.run("CREATE INDEX movie_id_index FOR (m:Movie) ON (m.movieId)")
session.run("CREATE INDEX genres_index FOR (m:Movie) ON (m.genres)")
session.run("CREATE INDEX user_id_index FOR (u:User) ON (u.userId)")
```

### Consultas de Lectura
Se evalúa el rendimiento en consultas individuales, típicas en aplicaciones de usuario final,
con el objetivo de medir la latencia real por operación, el uso de recursos y el rendimiento de búsqueda indexada.

#### Consultas Ejecutadas

| Consulta                | Descripción                                                         |
| ----------------------- | ------------------------------------------------------------------- |
| `find_by_movie_id`      | Buscar una película por ID                                          |
| `top_rated_movie`       | Películas con calificación promedio mayor a 4.5                     |
| `search_by_genre`       | Buscar películas por género (`"Comedy"`)                            |
| `search_by_title_regex` | Buscar películas con "story" en el título (insensible a mayúsculas) |
| `user_movie_join`       | Hacer join entre usuarios y sus películas calificadas               |

#### Resultados MongoDB

| Consulta                | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS   | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
| ----------------------- | ------------------- | -------- | -------- | ----- | -------------- | ------- |------------|
| `find_by_movie_id`      | 2.90                | 5.42     | 11.91    | 17.6  | 134.01         | 11.64   | 0.15       |
| `top_rated_movie`       | 3.24                | 5.22     | 11.70    | 17.5  | 102.78         | 8.79    | 0.00       |
| `search_by_genre`       | 4.40                | 6.48     | 19.49    | 17.0  | 90.73          | 9.37    | 0.00       |
| `search_by_title_regex` | 4.71                | 7.91     | 10.29    | 17.0  | 92.41          | 10.97   | 0.80       |
| `user_movie_join`       | 4.09                | 7.68     | 12.62    | 17.25 | 84.76          | 10.08   | 0.60       |

#### Resultados Neo4j

| Consulta                | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS   | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
| ----------------------- | ------------------- | -------- | -------- | ----- | -------------- | ------- | ------ |
| `find_by_movie_id`      | 7.81                | 13.09    | 16.17    | 16.25 | 44.14          | 8.58    | 0.00   |
| `top_rated_movie`       | 8.65                | 13.32    | 16.12    | 16.05 | 45.74          | 14.01   | 0.00   |
| `search_by_genre`       | 9.18                | 12.91    | 17.62    | 15.85 | 47.13          | 9.75    | 0.00   |
| `search_by_title_regex` | 8.27                | 11.83    | 17.28    | 16.15 | 48.37          | 9.46    | 0.00   |
| `user_movie_join`       | 40.77               | 112.83   | 183.16   | 10.6  | 43.53          | 11.87   | 0.00   |

#### Análisis Comparativo
- MongoDB fue consistentemente más rápido en todas las consultas, con menor latencia promedio y mayor throughput (QPS).
- Neo4j mostró un uso de memoria (RSS) más bajo en promedio, y cero fallos de página en todas las pruebas.
- Las consultas que involucran joins complejos (user_movie_join) penalizan mucho más a Neo4j, 
indicando que sus patrones de acceso en grafos son más costosos en tiempo cuando no se explotan relaciones profundas.
- MongoDB se mantuvo más eficiente pero tuvo mayor variación en los faults y uso de RSS en general.

---

### Consultas de Escritura
Se comparan las operaciones de escritura más comunes realizadas sobre ambas bases de datos. Se evalúan tres tipos de inserciones:

#### Consultas Ejecutadas

| Operación                  | Descripción                                                              |
|----------------------------|--------------------------------------------------------------------------|
| `insert_single_movie`      | Inserta una película individual con metadatos, distribución y tags       |
| `insert_multiple_movies`   | Inserta 5 películas en una operación en lote                             |
| `insert_user_with_ratings` | Inserta un usuario con 5 ratings vinculando a películas existentes       |


#### Resultados MongoDB

| Operación                 | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS  | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
|---------------------------|---------------------|----------|----------|------|----------------|---------|--------|
| `insert_single_movie`     | 3.88                | 7.85     | 16.69    | 17.4 | 58.17          | 10.89   | 0.0    |
| `insert_multiple_movies`  | 8.01                | 11.71    | 16.89    | 16.2 | 66.97          | 11.77   | 0.0    |
| `insert_user_with_ratings`| 2.61                | 5.59     | 10.01    | 17.75| 114.71         | 11.84   | 0.0    |

#### Resultados Neo4j

| Operación                 | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS  | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
|---------------------------|---------------------|----------|----------|------|----------------|---------|--------|
| `insert_single_movie`     | 8.94                | 13.32    | 21.98    | 15.95| 47.30          | 14.25   | 0.0    |
| `insert_multiple_movies`  | 15.10               | 19.34    | 25.57    | 14.5 | 43.27          | 11.80   | 0.0    |
| `insert_user_with_ratings`| 49.72               | 63.05    | 76.83    | 9.7  | 45.42          | 12.04   | 0.1    |

#### Análisis Comparativo

- MongoDB demostró mejor rendimiento general en inserciones simples y por lotes, con menor latencia promedio y mayor throughput (`QPS`).
- La operación `insert_user_with_ratings` es particularmente más rápida en MongoDB debido a que sus documentos embeben los ratings directamente, 
sin necesidad de crear relaciones explícitas entre nodos como en Neo4j. Esto refleja el costo de la creación de nodos + relaciones múltiples en el modelo de grafos.
- Neo4j presentó un uso de memoria (`RSS`) más contenido y estable.

---

### Consultas de Actualización

Se compara el rendimiento de MongoDB y Neo4j al actualizar marcas de tiempo (`timestamp`) almacenadas como enteros UNIX, convirtiéndolos en objetos `datetime`. 
La operación es representativa de procesos de normalización de datos históricos en sistemas analíticos.

#### Estrategia de Prueba

- Se seleccionaron 300 usuarios al azar sin reemplazo (`SAMPLE_POOL`).
- En cada iteración:
  - Se seleccionó un usuario.
  - Se actualizaron todas las calificaciones (`ratings`) de ese usuario.
  - Se midió la latencia y el uso de recursos.
- Las conversiones se realizaron directamente dentro del motor de base de datos (sin lógica en el cliente).

#### Operación MongoDB

```python
pipeline = [
    {"$match": {"userId": user_id}},
    {
        "$set": {
            "ratings": {
                "$map": {
                    "input": "$ratings",
                    "as": "r",
                    "in": {
                        "$mergeObjects": [
                            "$$r",
                            {
                                "timestamp": {
                                    "$cond": [
                                        {"$isNumber": "$$r.timestamp"},
                                        {"$toDate": {"$multiply": ["$$r.timestamp", 1000]}},
                                        "$$r.timestamp"
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
    },
    {
        "$merge": {
            "into": "users",
            "whenMatched": "merge",
            "whenNotMatched": "discard"
        }
    }
]
```

#### Operación Neo4j
```
MATCH (u:User {userId: $userId})-[r:RATED]->(:Movie)
SET r.timestamp = datetime({ epochSeconds: r.timestamp })
```

#### Resultados Comparativos

| Motor   | Iteraciones | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS  | CPU (%) | Memoria RSS (MB) | Fallos/Seg |
| ------- | ----------- |---------------------| -------- | -------- |------| ------- | ---------------- | -------------- |
| MongoDB | 82          | 6.95                | 20.47    | 50.60    | 16.4 | 7.07    | 50.40            | 8.8            |
| Neo4j   | 75          | 13.51               | 44.41    | 178.80   | 15.0 | 15.79   | 42.11            | 0.0            |


#### Análisis Comparativo
- MongoDB muestra mejor latencia promedio y mayor throughput.
- El uso de memoria es comparable, aunque MongoDB reporta más fallos de página (major_faults_per_sec = 8.8), lo que podría indicar presión sobre la memoria mapeada del sistema.
- La transformación en MongoDB utiliza $map y $toDate, mientras que Neo4j emplea datetime({ epochSeconds: ... }), ambos ejecutados en el servidor.
