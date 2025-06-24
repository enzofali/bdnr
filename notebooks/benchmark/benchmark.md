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
| ------------- |-----------|-----------------|
| Usuarios      | 2025      | 2.39 segundos   |
| Películas     | 14,619    | 26.47 segundos  |
| Ratings       | 293,308   | 666.61 segundos |
| Etiquetas     | 924,902   | 274.78 segundos |
| Total         | —         | 970.24 segundos |

#### MongoDB

| Tipo de Datos | Registros | Tiempo        |
| ------------- |-----------|---------------|
| Usuarios      | 2025      | 0.77 segundos |
| Películas     | 14,619    | 0.77 segundos |
| Total         | —         | 0.77 segundos |

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
| ----------------------- | ------------------- | -------- | -------- | ----- | -------------- | ------- | ---------- |
| `find_by_movie_id`      | 2.31                | 4.85     | 37.33    | 17.8  | 161.87         | 7.28    | 0.35       |
| `top_rated_movie`       | 4.85                | 7.24     | 13.42    | 16.95 | 50.32          | 4.04    | 0.05       |
| `search_by_genre`       | 9.20                | 12.37    | 16.37    | 15.2  | 73.01          | 7.32    | 0.00       |
| `search_by_title_regex` | 6.93                | 9.83     | 11.12    | 16.2  | 120.48         | 5.52    | 0.80       |
| `user_movie_join`       | 5.25                | 8.34     | 10.64    | 16.75 | 121.35         | 4.74    | 2.15       |


#### Resultados Neo4j

| Consulta                | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS   | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
| ----------------------- | ------------------- | -------- | -------- | ----- | -------------- | ------- | ---------- |
| `find_by_movie_id`      | 7.84                | 13.48    | 16.31    | 16.25 | 43.12          | 8.80    | 9.70       |
| `top_rated_movie`       | 10.25               | 12.99    | 19.37    | 15.65 | 39.25          | 12.55   | 0.15       |
| `search_by_genre`       | 5.13                | 7.02     | 20.69    | 16.85 | 38.34          | 10.61   | 0.00       |
| `search_by_title_regex` | 4.87                | 6.75     | 19.27    | 17.0  | 40.93          | 9.20    | 0.00       |
| `user_movie_join`       | 66.42               | 200.08   | 430.62   | 8.35  | 39.20          | 9.03    | 0.00       |


#### Análisis Comparativo
- MongoDB ofrece mejor rendimiento bruto en términos de latencia y throughput, pero a costa de mayor uso de memoria.
- Neo4j, aunque más lento especialmente en consultas con joins complejos, fue más estable en cuanto a errores y mostró menor uso de memoria.
- Las consultas que involucran joins complejos (user_movie_join) penalizan mucho más a Neo4j, 
indicando que sus patrones de acceso en grafos son más costosos en tiempo cuando no se explotan relaciones profundas.

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

| Operación                  | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS  | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
| -------------------------- | ------------------- | -------- | -------- | ---- | -------------- | ------- | ---------- |
| `insert_single_movie`      | 4.10                | 6.39     | 13.57    | 17.3 | 70.00          | 7.54    | 0.0        |
| `insert_multiple_movies`   | 8.66                | 11.81    | 13.84    | 16.0 | 85.54          | 7.76    | 0.0        |
| `insert_user_with_ratings` | 3.27                | 4.46     | 7.05     | 17.5 | 90.70          | 5.10    | 0.0        |

#### Resultados Neo4j

| Operación                  | Latencia Prom. (ms) | p95 (ms) | p99 (ms) | QPS  | RSS Prom. (MB) | CPU (%) | Fallos/Seg |
| -------------------------- | ------------------- | -------- | -------- | ---- | -------------- | ------- | ---------- |
| `insert_single_movie`      | 10.97               | 14.98    | 19.06    | 15.4 | 39.64          | 4.88    | 0.0        |
| `insert_multiple_movies`   | 17.10               | 21.30    | 27.29    | 14.1 | 41.24          | 6.20    | 0.0        |
| `insert_user_with_ratings` | 50.23               | 63.01    | 83.64    | 9.65 | 42.76          | 6.06    | 0.0        |

#### Análisis Comparativo

- MongoDB muestra un rendimiento muy superior en latencia y throughput para inserciones individuales, en lote y con relaciones.
- Neo4j, aunque más lento en escrituras, mantiene un consumo de memoria más bajo y consistente
- La operación `insert_user_with_ratings` es particularmente más rápida en MongoDB debido a que sus documentos embeben los ratings directamente, 
sin necesidad de crear relaciones explícitas entre nodos como en Neo4j. Esto refleja el costo costo de mantener la integridad de grafos y vínculos entre nodos durante la escritura.
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
| ------- | ----------- | ------------------- | -------- | -------- | ---- | ------- | ---------------- | ---------- |
| MongoDB | 340         | 4.92                | 7.50     | 13.59    | 17.0 | 8.81    | 100.40           | 2.7        |
| Neo4j   | 290         | 15.23               | 45.81    | 57.59    | 14.5 | 7.67    | 43.22            | 0.0        |



#### Análisis Comparativo
- MongoDB resulta más eficiente en cuanto a latencia, throughput.
- Neo4j, aunque más lento, ofrece una ejecución más estable y con menor consumo de memoria.
- La transformación en MongoDB utiliza $map y $toDate, mientras que Neo4j emplea datetime({ epochSeconds: ... }), ambos ejecutados en el servidor.
