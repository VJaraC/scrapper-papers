---
applyTo: "tests/**"
---

# Convenciones de testing — scrapper-papers

## Filosofía
Los tests no buscan ser exhaustivos por volumen, sino no dejar pasar nada roto
en silencio. Prioriza cobertura donde el fallo es más costoso: clasificación
temática, filtros de inclusión, y parsing de respuestas de APIs externas.

## Mocking de APIs externas
- Nunca hacer llamadas reales a Semantic Scholar, CrossRef o Scopus en los
  tests — usar `unittest.mock` o `pytest-mock` con respuestas de ejemplo
  fijas guardadas en `tests/fixtures/`.
- No testear el formato exacto de la respuesta real de una API — eso se
  rompe cuando la API cambia un campo y no dice nada sobre si tu lógica
  funciona. Testea tu propio código de parsing contra fixtures fijas que tú
  controlas.
- Para Scopus, incluir un fixture que simule metadata parcial (sin
  `dc:description`/abstract), reflejando el caso de entitlement
  institucional incompleto.

## Casos a cubrir por módulo

### `scoring/` (clasificación temática)
- Paper con keywords claras de cada categoría (MAS-LLM, MAS-DESPACHO-MINERO,
  MAS-DESPACHO-MINERO-LLM, MAS-SCHEDULING).
- Paper sin abstract (solo título/keywords).
- Keywords en mayúsculas/minúsculas mezcladas o con tildes.
- Paper que no encaja en ninguna categoría — debe marcarse explícitamente,
  no clasificarse por defecto ni fallar en silencio.

### `collectors/` (Semantic Scholar, CrossRef, Scopus)
- Respuesta válida completa.
- Respuesta con campos faltantes (sin DOI, sin abstract, sin año).
- Error HTTP (4xx, 5xx) — debe manejarse sin caer la app entera.
- Respuesta vacía (0 resultados).

### Filtros (año, venue_type, preprints)
- Paper de exactamente 5 años de antigüedad (caso borde del límite).
- Paper de 6 años (debe excluirse).
- Preprint explícito — debe excluirse siempre, incluso si cumple el resto de
  criterios.
- Conference paper — debe marcarse/excluirse según la regla vigente.

### `storage/` (CSV / Excel)
- Exportar e reimportar sin pérdida de datos.
- Títulos/abstracts con caracteres especiales, comillas, saltos de línea.
- Archivo vacío o recién creado (sin filas aún).

## Herramientas
- Framework: `pytest`.
- Mocking: `unittest.mock` (stdlib) o `pytest-mock` si se agrega a
  `requirements.txt`.
- Un archivo de test por módulo de `src/` (`test_scoring.py`,
  `test_collectors.py`, etc.), reflejando la misma estructura.

## Qué evitar
- Tests que dependan de conexión a internet o de las APIs reales.
- Tests que verifiquen implementación interna en vez de comportamiento
  (qué resultado entrega, no qué función interna se llamó).
- Asserts sin mensaje cuando el fallo no es obvio por sí solo.