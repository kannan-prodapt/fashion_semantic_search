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

# Fashion Semantic Search

LLM-powered semantic search for fashion products with SQL filter generation and vector-based ranking. Converts natural-language queries into structured SQL filters that support advanced operations like IN/NOT IN (for vibes, occasions, categories, etc.), and ranks results using vector similarity. Also includes a fashionable taxonomy, caching for speed, and now features a Streamlit web app interface for seamless prototyping.

---

## 🚀 Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/kannan-prodapt/fashion_semantic_search.git
cd fashion_semantic_search
```

### 2. Create & Activate Python Environment

It's recommended to use Python 3.9+.

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Set Up OpenSearch/Elasticsearch for Vector Index

- Ensure your OpenSearch/Elasticsearch instance is running (see provided docker/docs as needed).
- Load the provided SQL database dump for a ready-to-use product catalog.

```bash
# Example using sqlite3
sqlite3 fashion_catalog.db < fashion_dump.sql
```

### 5. Run the Streamlit App

```bash
streamlit run amazon_ui.py
```

---

## 📝 API Endpoints

### Two Interactive Endpoints

- **`/v1/search`**  
  Performs a *hybrid search*: the system applies SQL-based filtering for hard constraints (including negations, structured, and categorical facets), and then reranks the filtered results using vector similarity for semantic matching.  
  *Recommended for most production uses as it provides both accuracy and semantic relevance.*

- **`/v1/search_sql`**  
  Performs *SQL-only retrieval*: returns matching results directly after SQL filtering, skipping the (costlier) vector reranking stage.  
  *This endpoint is much faster but may not provide nuanced ranking. It's ideal for speed-critical scenarios or analytic exploration.*

Try both endpoints interactively to see the trade-offs between speed and ranking accuracy.

---

## 📝 Sample Usage

### 1. Test Query Via Streamlit

Open the running Streamlit app in your browser (usually at http://localhost:8501) and enter a sample query:

```
"Show me summer dresses NOT in black, perfect for beach vibes, under $50"
```

#### Resulting Steps:
- The system parses your query, generating SQL filters (e.g. category=`dress`, color!=`black`, occasion=`beach`, price<50).
- It retrieves matching records from the fashion catalog using SQL.
- The shortlist is reranked using vector search (semantic similarity) against product/item embeddings (for `/v1/search`), or returned directly if using `/v1/search_sql`.
- Recommendations are displayed with matching scores.

### 2. Sample API Query

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/search",  # or "/v1/search_sql"
    json={"query": "Trendy party tops not in red, suitable for winter evenings, below $100"}
)
print(response.json())
```

---

## ⚙️ Key Design Decisions & Trade-offs

### Hybrid SQL + Vector Search

- **SQL Filtering First:**  
  All logical negations (e.g., NOT black, NOT party) and structured constraints (category, price, rating) are translated into SQL for *exact* filtering.  
  **Advantage:** Ensures accurate support for negations and categorical filters, which pure vector search often mishandles.

- **Vector-based Re-ranking:**  
  After SQL extracts the candidate set, a vector similarity model ranks candidates based on semantic match to the query.  
  **Advantage:** Allows nuanced, context-aware ranking of results within the filtered set.

- **Consistency:**  
  This layered approach produces more reliable results, especially in edge-cases where pure vector search may “miss” critical exclusions or inclusions.

- **Endpoint Choices:**  
  `/v1/search_sql` offers the fastest runtime, suitable for applications that need an instant response or just structured retrieval, while `/v1/search` (hybrid) offers higher quality ranking at some computational cost.

### Streamlit for Interactive Prototyping

- Fast, intuitive interface for demo and prototyping
- Easy visualization of query parsing and final recommendations

### Caching & Configurable Taxonomy

- Caching increases performance for repeated or similar queries.
- Fashion taxonomy is easily configurable for new categories, occasions, and style attributes.

---

## 🧰 Notes

- `sql_dump.sql` included for jump-starting your local database.
- Use the provided embedding/query script to load item vectors into OpenSearch before doing vector search.

---

## 📄 License

See [LICENSE](LICENSE) for details.

---
