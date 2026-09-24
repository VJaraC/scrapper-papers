# scrapper-papers

Herramienta para recolectar, clasificar y curar automáticamente un pool de papers académicos sobre **modelos de lenguaje de gran escala (LLM)**, **sistemas multiagente** y **scheduling / despacho minero**. Se desarrolló como apoyo al Taller de Título *"Evaluación de modelos de lenguaje de gran escala como componente de recomendación de parámetros en sistemas multiagente de scheduling: el caso del despacho minero"* (UNAP).

La app consulta **tres fuentes de búsqueda académica** (Semantic Scholar, Scopus y Web of Science) más CrossRef para enriquecer metadata, para reducir el sesgo de cobertura de cualquier base de datos individual y ampliar la cantidad de papers relevantes encontrados. Cada paper se clasifica automáticamente por reglas explícitas (no por IA) sobre si trata LLM, minería, o ambos, y se guarda en un CSV que sirve como fuente de verdad para curar manualmente el pool final.

## Requisitos previos

- **Python 3.10 o superior** (el código usa sintaxis de type hints tipo `str | None`, disponible desde Python 3.10). El proyecto no fija una versión exacta en ningún archivo de configuración; se desarrolló y probó con Python 3.12.10.
- **pip**
- **git**

## Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/VJaraC/scrapper-papers.git
   cd scrapper-papers
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv venv
   ```

   Activarlo:

   - **Windows (PowerShell):**
     ```powershell
     venv\Scripts\Activate.ps1
     ```
   - **Windows (cmd):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

   Si además vas a correr la suite de tests, instala también las dependencias de desarrollo:

   ```bash
   pip install -r requirements-dev.txt
   ```

## Configuración de variables de entorno

Copia `.env.example` a `.env`:

```bash
cp .env.example .env
```

Y completa cada variable:

| Variable | Obligatoria | Qué es | Cómo conseguirla |
|---|---|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | Opcional | El collector de Semantic Scholar funciona sin key, pero comparte un límite de tasa público con todos los usuarios sin key (en la práctica suele estar saturado y devuelve `429 Too Many Requests` seguido). Con key propia se obtiene una cuota propia (documentada como 1 request/segundo, acumulada entre todos los endpoints de la API). | [Solicitar key](https://www.semanticscholar.org/product/api#api-key-form) |
| `SCOPUS_API_KEY` | **Obligatoria** para ese collector (si falta, `scopus.collect_papers` simplemente no trae resultados de esa fuente, sin romper el resto de la búsqueda) | Key de la Scopus Search API de Elsevier. | Registra una cuenta y una aplicación en el [Portal de Desarrolladores de Elsevier](https://dev.elsevier.com) y suscríbete a la Scopus Search API. |
| `WOS_API_KEY` | **Obligatoria** para ese collector (si falta, `wos.collect_papers` lanza un error controlado que la búsqueda reporta como fuente fallida, sin interrumpir las demás fuentes) | Key de la Web of Science Starter API de Clarivate. | Registra una cuenta y una aplicación en el [Portal de Desarrolladores de Clarivate](https://developer.clarivate.com) y suscríbete a la Web of Science Starter API, plan "Free Trial" (requiere correo institucional universitario para la aprobación). |
| `CROSSREF_EMAIL` | Opcional / no usada actualmente | Está pensada para identificarte ante la API de CrossRef, pero **el código actual no la lee** (`crossref.py` no la usa en ninguna llamada) — puedes dejarla vacía o completarla para uso futuro. | — |

CrossRef en sí **no requiere ninguna API key**: se usa únicamente para enriquecer metadata (venue y tipo de venue) a partir del DOI de un paper que ya fue encontrado por otra fuente.

> ⚠️ **Nunca commitees el archivo `.env` con valores reales.** Ya está en `.gitignore`. El único archivo de variables de entorno que debe versionarse es `.env.example`, y siempre sin valores reales.

## Cómo usarlo

### Por línea de comandos

```bash
python -m src.cli buscar "large language models multi-agent scheduling"
```

Opciones disponibles:

```bash
python -m src.cli buscar "<query>" --year-from 2021 --year-to 2026 --limit 20 --csv-path data/papers.csv
```

- `--year-from` / `--year-to`: rango de años de publicación (por defecto 2021–2026).
- `--limit`: cantidad máxima de resultados por fuente (por defecto 20).
- `--csv-path`: ruta del CSV donde se guarda el pool (por defecto `data/papers.csv`).

Ejecuta siempre estos comandos desde la raíz del repositorio — la ruta del CSV es relativa al directorio de trabajo.

### Interfaz visual (Streamlit)

```bash
streamlit run src/ui/app.py
```

Desde ahí puedes:

- Buscar papers con el mismo pipeline que el CLI, sin salir del navegador.
- Filtrar el pool existente por año, fuente, LLM, minería, categoría, tipo de venue y decisión (incluido/excluido/pendiente).
- Marcar cada paper como `revisado` (checkbox editable en la tabla) para llevar control manual de curaduría.
- Exportar los papers filtrados actualmente visibles a un archivo Excel (`data/papers_filtrados.xlsx`).

### Dónde queda guardado el resultado

- `data/papers.csv` es la **fuente de verdad**: cada búsqueda inserta papers nuevos, actualiza los existentes (por DOI) y protege de sobrescritura cualquier paper que ya hayas marcado como `revisado`.
- La exportación a Excel es un **snapshot** de un momento dado — no se vuelve a leer ni se sincroniza de regreso al CSV.

## Cómo correr los tests

```bash
pytest tests/ -q
```

## Estructura del proyecto

```
scrapper-papers/
├── src/
│   ├── collectors/    # Clientes HTTP de cada fuente: Semantic Scholar, Scopus, WoS y CrossRef
│   ├── scoring/        # Clasificación temática (classifier.py) y reglas de inclusión/exclusión (decision.py), ambas basadas en keywords explícitas, no en IA
│   ├── storage/           # Persistencia del pool en CSV (con merge por DOI) y exportación a Excel
│   ├── ui/                    # Interfaz Streamlit
│   ├── pipeline.py                # Orquesta collectors + enriquecimiento CrossRef + clasificación + persistencia
│   └── cli.py                         # Punto de entrada por línea de comandos
├── tests/              # Suite de pytest, con fixtures de respuestas reales de cada API
└── data/                   # papers.csv (fuente de verdad) y exportaciones a Excel
```

## Notas sobre las fuentes de datos

| Fuente | Qué aporta | Sintaxis de búsqueda | Trae abstract |
|---|---|---|---|
| **Semantic Scholar** | Búsqueda amplia, fuente principal | Texto libre | Sí |
| **Scopus** | Búsqueda indexada en Elsevier | Campo `TITLE-ABS-KEY(...)`, términos unidos con `AND` explícito | No |
| **Web of Science** | Búsqueda indexada en Clarivate | Field tag `TS=(...)`, términos unidos con `AND` explícito | No |
| **CrossRef** | Solo enriquecimiento (venue y `venue_type`) a partir del DOI, no aporta papers nuevos por sí sola | — | No |

**Limitaciones conocidas:**

- Solo Semantic Scholar trae abstract; Scopus y WoS solo aportan metadata (título, autores, año, venue, DOI). El campo `abstract` queda vacío para papers que solo vengan de esas dos fuentes.
- La deduplicación entre fuentes es **por DOI**. Un paper que no tenga DOI (o que las distintas fuentes reporten con DOIs inconsistentes) puede aparecer duplicado en el pool.
