# Comparación de Modelos para Sistemas de Recomendación

### Contexto del Problema

Diseñamos un sistema de recomendaciones en tiempo real para la página principal de una plataforma de streaming, considerando los siguientes requisitos:

- Lecturas de baja latencia (<50 ms) para recomendaciones personalizadas.
- Alta disponibilidad, especialmente durante picos de tráfico.
- Soporte para más de 1 millón de usuarios con aproximadamente 100 interacciones por usuario.
- Escrituras poco frecuentes (valoraciones 1 a 5 veces por semana).
- Exportación semanal de datos para entrenamiento de modelos de machine learning.

### Modelo Embebido

En este esquema, toda la información relevante (interacciones, metadatos, estadísticas) se almacena dentro de documentos individuales por usuario o película, permitiendo:

- Lecturas eficientes con una sola operación (`O(1)`), eliminando la necesidad de joins.
- Escalabilidad horizontal al fragmentar por `user_id` o `movie_id` (sharding).
- Alta localidad de datos, incluso durante particiones de red.

Este modelo favorece sistemas con cargas de lectura intensas, donde la latencia mínima y la disponibilidad son prioritarias.

### Limitaciones del Modelo Embebido

- Tamaños de documento pueden superar los 16MB (mongoDB) en usuarios muy activos.
- Dificultad para mantener consistencia estricta en datos frecuentemente actualizados.

### Modelo Normalizado

El modelo normalizado, basado en colecciones separadas (usuarios, películas, interacciones), proporciona:

- Integridad transaccional y consistencia fuerte.
- Evita la duplicación de datos.
- Mayor idoneidad para operaciones analíticas o actualizaciones concurrentes.

Actualizar el título de una película requiere una sola operación en el modelo normalizado, mientras que en el embebido implica modificar múltiples documentos.

### CAP

La decisión entre modelos depende del enfoque deseado:

- **Modelo embebido:** prioriza **disponibilidad** y **baja latencia**, aceptando cierta **consistencia eventual**.
- **Modelo normalizado:** tiene una alta **consistencia**, especialmente util en escenarios analíticos.

### Enfoque Híbrido

Una arquitectura mixta puede ser beneficiosa: usar un modelo embebido optimizado para recomendaciones en tiempo real y 
sincronizar periódicamente con un esquema normalizado para análisis. Esta dualidad permite balancear velocidad y precisión según el contexto.
