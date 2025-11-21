````markdown name=README.md
# Fashion Semantic Search

LLM-powered semantic search for fashion products. Converts natural-language queries into structured SQL filters with IN/NOT IN support for vibes, occasions, categories, styles, price, and ratings. Includes SQL builder, caching, and a configurable fashion taxonomy.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [API Usage](#api-usage)
- [Database Schema](#database-schema)
- [Indexing & OpenSearch](#indexing--opensearch)
- [Scripts](#scripts)
- [Testing](#testing)
- [License](#license)

---

## Overview

This repository provides a semantic search engine for fashion products. It leverages large language models (LLMs) to interpret free-form natural language queries and converts them into highly specific SQL queries for efficient product retrieval. It supports semantic and vector search using OpenSearch, caching, and extensible fashion taxonomies.

---

## Features

- **Semantic Search API**: Users submit natural language queries (e.g., "red summer dress for party under $100"), and the API translates them into SQL and vector filters.
- **LLM-based SQL Filter Builder**: Converts queries into SQL with support for advanced filters (e.g., `IN`, `NOT IN`).
- **Configurable Fashion Taxonomy**: Supports various categories, vibes, occasions, and style enums.
- **OpenAI Embeddings**: Uses OpenAI for vector representation of queries and products.
- **OpenSearch Integration**: Embeddings are indexed and searched via OpenSearch for fast, scalable retrieval.
- **Robust Database Schema**: Modular MySQL schema for extensibility.
- **Health Check Endpoint**: For quick liveness probes with `/health`.
- **Extensible API**: Built using FastAPI and modular routing under `/v1`.

---

## Architecture

- **FastAPI** server (`app/main.py`) exposes endpoints for both LLM and vector semantic search.
- **APIRouter** (`app/api/v1/search_routes.py`) mounts endpoints:
  - `/search_sql`: SQL-only filter search
  - `/search`: Vector + SQL hybrid semantic search
- **Search service** (`app/services/search_service.py`): Handles request validation, OpenAI embedding, database lookup, and OpenSearch integration.
- **Database Layer** (`app/db/`): Contains scripts and configs for MySQL database.
- **OpenSearch client** (`scripts/opensearch_client2.py`): Connects and manages product vector indexes.

---

## Installation

1. **Clone the repo**:
   ```sh
   git clone https://github.com/kannan-prodapt/fashion_semantic_search.git
   cd fashion_semantic_search
   ```
2. **Configure Python environment**:
   - Python 3.8+
   - Install dependencies (example):
     ```sh
     pip install -r requirements.txt
     ```
3. **Set environment variables**:
   - `OPENAI_API_KEY`
   - `SEARCH_API_KEY`
   - Configure MySQL credentials in `app/db/db_config.py`

4. **Start the FastAPI server**:
   ```sh
   uvicorn app.main:app --reload
   ```

---

## API Usage

**Endpoints**:

- `POST /v1/search_sql`: Find products via LLM-generated SQL filters (send `SearchRequest` JSON).
- `POST /v1/search`: Hybrid semantic search using both vector and SQL filtering.
- `GET /health`: Health check endpoint.

Sample search request:
```json
{
  "query": "blue jacket for winter parties under $150"
}
```

---

## Database Schema

- Core table: `products` (ID, main_category, title, price, store, etc.)
- Aux tables: `product_images`, `product_videos`, `product_vibes`, `product_occasions`, etc.
- Example creation scripts:
  - `app/db/create_tables.py`: Main table definitions.
  - `app/db/db_initialise.py`: Initializes users table for authentication/demo.
  - Enum modification (example): `scripts/alter_occasion_enum_add_beach.py`.

See `tests/test_tables_created_successfully.py` for verification logic.

---

## Indexing & OpenSearch

- Product and query embedding using OpenAI.
- Vector indexing managed by:
  - `scripts/create_products_index.py`: Creates/updates OpenSearch index with KNN support.
  - `scripts/opensearch_client2.py`: Connects to AWS OpenSearch for diagnostics and management.

---

## Scripts

Useful scripts for administration and migration:

- `scripts/create_products_index.py`: Set up or reset product vector indices.
- `scripts/alter_occasion_enum_add_beach.py`: Update or add enums for category/occasion logic.
- `scripts/reset_schema_with_enums.py`: Full schema reset with up-to-date enums.

---

## Testing

- Includes basic DB and schema validation tests in `tests/`.
- Recommended: Extend with integration and API endpoint tests.

---

## License

BSD 3-Clause License.

See [LICENSE](https://github.com/kannan-prodapt/fashion_semantic_search/blob/main/LICENSE) for details.
````
