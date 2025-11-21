# Fashion Semantic Search

LLM-powered semantic search for fashion products. Converts natural-language queries into structured SQL filters with IN/NOT IN support for vibes, occasions, categories, styles, colors, price, ratings, and more. Includes an SQL builder, LLM filter interpreter, vector reranking, and a highly configurable fashion taxonomy.

---

## 🚀 Demo

Try it live:
👉 **[http://ec2-13-234-76-80.ap-south-1.compute.amazonaws.com:8501/](http://ec2-13-234-76-80.ap-south-1.compute.amazonaws.com:8501/)**

---

## 🏁 Quick Start

To set up and use this repository, follow these steps:

---

### **1. Database Setup**

1. Place your SQL dump file (e.g., `fashion_dump.sql`) inside the directory expected by:

```
scripts/load_sql_dump.py
```

(Usually this is: `scripts/sql/` unless configured otherwise.)

2. Load the SQL dump:

```bash
python scripts/load_sql_dump.py
```

---

### **2. Populate OpenSearch**

After your database is populated, index products into OpenSearch:

```bash
python scripts/index_products_to_opensearch.py
```

This creates embeddings and indexes them for vector-based ranking.

---

### ▶️ Start all services:

```bash
./server.sh start
```

This launches:

* **FastAPI backend** (port 8000)
* **Streamlit UI** (port 8501)

Logs are usually written to `logs/`.

### ⏹ Stop all services:

```bash
./server.sh stop
```

This gracefully kills:

* Uvicorn (FastAPI)
* Streamlit frontend

Your entire application stack can now be managed with two commands.

---

# 4️⃣ Run Manually (Optional)

If you prefer manual control:

### Start backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Streamlit:

```bash
streamlit run app/ui/amazon_ui.py --server.port=8501
```

---


### **4. Your system is ready!**

You can now run natural-language searches like:

* “Beach dress under 1500 rupees, not black”
* “Formal office shirt for men, slim fit”
* “Cute summer tops for teens”
* “Winter jacket NOT in red”

---

## ⭐ Features

### **Semantic Search**

* Natural language → Structured SQL filters
* Supports IN / NOT IN for all categorical facets
* Accurate handling of negations (“not red”, “except sportswear”)

### **Vector Reranking**

* Hybrid model:

  * SQL extracts hard constraints
  * OpenSearch vectors rerank for semantic relevance

### **Fashion Taxonomy**

* Vibes, occasions, styles, categories, colors, material, fits, etc.
* Fully configurable via prompt
* Automatically mapped by LLM

### **Robust SQL Builder**

* Generates JOIN/WHERE clauses dynamically
* Handles facets independently
* Uses `NOT EXISTS` for NOT IN logic

### **Streamlit UI**

* Amazon-styled browsing
* Dynamic sidebar with detected filters
* Instant product grid updates

---

## 🧩 Architecture

```
User Query
     ↓
LLM Filter Generator (OpenAI)
     ↓                → Invalid/missing mappings auto-cleaned
SQL Builder
     ↓
MySQL Candidate Retrieval
     ↓
OpenSearch Vector Reranking
     ↓
Final Product Ranking
     ↓
Streamlit UI
```

---

## 📝 API Endpoints

### **1. `/v1/search` — Hybrid Search (Recommended)**

* Structured SQL + Vector reranking
* Best relevance for real-world queries

### **2. `/v1/search_sql` — SQL Only**

* Fastest
* Useful for debugging or lightweight filtering

### Example usage:

```bash
POST /v1/search
{
  "query": "Red floral dress for summer under 1500",
  "limit": 50,
  "search_key": "YOUR_KEY"
}
```

---

## 📂 Project Structure

```
app/
 ├── core/
 │    ├── llm_filters.py
 │    ├── sql_builder.py
 │    └── ...
 ├── services/
 │    └── search_service.py
 ├── ui/
 │    └── amazon_ui.py
 ├── db/
 │    └── db_config.py
 └── ...
scripts/
 ├── load_sql_dump.py
 ├── index_products_to_opensearch.py
 ├── select_only_sql.py
 └── ...
prompts/
 └── schema_prompts.py
```

---

## 🗄️ Database Schema (Simplified)

* `products` — main product metadata
* `product_vibe_labels`
* `product_occasion_labels`
* `product_gender_labels`
* `product_category_labels`
* `product_age_labels`
* `product_style_labels` (colors, prints, fabric, fit, features, etc.)

---

## 🧪 Testing the System

Run queries in the UI or via API:

```
"Party tops not in black for wedding"
"Teal kurti for festive occasions"
"Mens winter jackets under 2000"
"Outfits for funeral"  → mapped to dark colors, no wedding/party noise
```

Scripts available:

* `scripts/find_unused_enum_labels.py`
* `scripts/cleanup_mappings.py`
* `scripts/sql_wrapper_select_only.py`

---

## 📦 Scripts Included

### Load SQL dump

```bash
python scripts/load_sql_dump.py
```

### Index to OpenSearch

```bash
python scripts/index_products_to_opensearch.py
```

### Debug SQL

```bash
python -m scripts.select_only_sql "SELECT * FROM products LIMIT 10;"
```

---

## 🔧 Configuration

Set up environment variables:

```bash
export OPENAI_API_KEY="..."
export SEARCH_KEY="..."
export DB_HOST="..."
export DB_USER="..."
export DB_PASSWORD="..."
export OS_HOST="..."
```

---

## 📄 License

See `LICENSE`
