# Copilot Instructions — scrapper-papers

## Contexto del proyecto
Esta app apoya el objetivo específico 1 del Taller de Título: "Investigar el
estado del arte sobre modelos de lenguaje de gran escala aplicados a problemas
de scheduling y sistemas multiagente, junto con el funcionamiento del sistema
de despacho existente..."

Título del trabajo: "Evaluación de modelos de lenguaje de gran escala como
componente de recomendación de parámetros en sistemas multiagente de
scheduling: el caso del despacho minero."

Objetivo de esta app: construir y curar, de forma automatizada, un pool de
20-30 papers relevantes sobre LLM + sistemas multiagente + scheduling/despacho
minero.

## Principios de diseño
- **Nada de caja negra**: toda la lógica de filtrado y clasificación debe ser
  inspeccionable — código legible, sin abstracciones que la oculten.
- **Ninguna credencial en el repositorio, bajo ninguna circunstancia**: toda
  API key va en variables de entorno (`.env`, incluido en `.gitignore`) —
  nunca hardcodeada en código, tests, scripts de prueba, logs ni historial de
  commits.

## Stack técnico
- Lenguaje: Python. Código claro y directo — funciones cortas, nombres
  descriptivos, comentarios en pasos no triviales. Evitar metaprogramación y
  patrones de diseño complejos.
- Dependencias: pip + requirements.txt
- Testing: pytest
- Persistencia: CSV como fuente de verdad; exportable a Excel (pandas/openpyxl).
- Interfaz: Streamlit, con filtros modificables en vivo (rango de años,
  fuente, llm sí/no, mineria sí/no, categoría, venue_type).

## Fuentes de datos
- **Semantic Scholar API** (gratuita, sin restricción institucional): fuente
  principal y automatizada de búsqueda y recolección.
- **CrossRef API** (gratuita): enriquecer/validar metadata, especialmente
  venue_type (journal-article vs proceedings-article).
- **Scopus** (Elsevier): API key ya registrada (guardada como variable de
  entorno). Antes de integrarla como collector automatizado, correr una
  prueba de entitlement conectado a la red/VPN de la UNAP, para confirmar si
  trae metadata completa (incluye `dc:description`/abstract) o solo parcial —
  documentar el resultado y ajustar el collector según corresponda.
- **ScienceDirect / Web of Science**: opcional, no bloqueante para el MVP.
- Sin preprints (excluir explícitamente).

## Criterios de inclusión
- Antigüedad máxima: 5 años (2021–2026)
- Evitar conference papers — priorizar journals
- Sin preprints
- Meta: pool de 20-30 papers

## Clasificación temática
MAS (sistemas multiagente) es el criterio base de todo el pool, no una
etiqueta. Los ejes que varían por paper:
- `llm`: sí/no
- `mineria`: sí/no (despacho minero específicamente)

Clasificación por similitud semántica entre el título y abstract del paper y
frases de referencia en inglés usando `sentence-transformers` con el modelo
`all-MiniLM-L6-v2`. Cada eje conserva un score numérico trazable y un umbral
independiente configurable; no se usan listas de keywords hardcodeadas.

Todas las combinaciones cuentan como aporte válido al tema:
- MAS-LLM (llm=sí, mineria=no)
- MAS-DESPACHO-MINERO (llm=no, mineria=sí)
- MAS-DESPACHO-MINERO-LLM (llm=sí, mineria=sí)
- MAS-SCHEDULING (llm=no, mineria=no)

## Esquema de metadata por paper
`title, authors, year, venue, venue_type (journal/conference), doi, abstract,
source (semantic_scholar/crossref/scopus/sciencedirect/wos), llm (bool),
mineria (bool), categoria, relevance_score, decision
(incluido/excluido/pendiente), justification`

## Fuera de alcance (por ahora)
- Agente de IA que recomiende qué papers quitar/agregar — descartado de
  momento. Si se retoma más adelante, requiere definir backend LLM (API de
  Anthropic con créditos pagados — Claude Pro no incluye acceso a la API — o
  modelo local vía Ollama).

## Roles de los agentes de desarrollo
- Planificador: built-in de VS Code.
- Implementador y Tester: se scaffoldean con `/create-agent` en Copilot Chat,
  usando este documento y los `SKILL.md` como fuente de verdad.

## Estructura del repo (objetivo)
```
scrapper-papers/
├── src/
│   ├── collectors/       # clientes Semantic Scholar, CrossRef y Scopus
│   ├── importers/          # futuro/opcional: parser RIS/BibTeX si activas WOS/ScienceDirect
│   ├── scoring/                # clasificación temática basada en reglas/keywords
│   ├── storage/                    # persistencia CSV + export a Excel
│   ├── ui/                            # Streamlit
│   └── cli.py
├── tests/
├── requirements.txt
└── data/
```

## Reglas generales
- No commitear API keys ni tokens — variables de entorno (`.env`, en
  `.gitignore`). Ninguna credencial debe aparecer en código, tests, logs ni
  historial de commits.
- Todo cambio pasa por pytest antes de mergear.