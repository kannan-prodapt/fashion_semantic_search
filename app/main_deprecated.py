import os
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
import openai
from mysql.connector import Error  # 👈 important for DB error handling

from app.schemas.search import SearchRequest, ProductOut, SearchResponse
from app.db.connection import get_db_connection
from app.core.llm_filters import llm_filters_cached
from app.core.sql_builder import build_sql_from_filters
from app.opensearch_client import get_opensearch_client


app = FastAPI(title="Fashion Search API")

OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "MYKEY")
openai.api_key = os.getenv("OPENAI_API_KEY")


def embed_query(text: str) -> List[float]:
    resp = openai.Embedding.create(
        model=OPENAI_EMBED_MODEL,
        input=text,
    )
    return resp["data"][0]["embedding"]


@app.post("/search", response_model=SearchResponse)
def search_products(req: SearchRequest):
    print("internal key = ", SEARCH_API_KEY)
    if req.search_key != SEARCH_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid search_key")

    # 1) Ask LLM for filters
    filters = llm_filters_cached(req.query)
    print("LLM filters:", filters)

    # 2) Build SQL
    sql, params = build_sql_from_filters(filters, req.limit)
    print("SQL:", sql)
    print("Params:", params)

    # 3) Execute SQL to get candidate IDs
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()  # (id, title)
        cur.close()
        conn.close()
    except Error as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not rows:
        return SearchResponse(sql=sql, params=params, results=[])

    sql_ids = [row[0] for row in rows]

    # 4) Vector search in OpenSearch, restricted to these IDs
    try:
        os_client = get_opensearch_client()

        # a) embed the user query
        query_vec = embed_query(req.query)

        # b) k-NN search with filter on product_id
        body = {
            "size": len(sql_ids),
            "query": {
                "knn": {
                    "embedding": {   # field name in your index
                        "vector": query_vec,
                        "k": len(sql_ids),
                        "filter": {
                            "terms": {
                                "product_id": [str(pid) for pid in sql_ids]
                            }
                        }
                    }
                }
            }
        }

        es_resp = os_client.search(index="products", body=body)
        hits = es_resp.get("hits", {}).get("hits", [])

        # Build (product_id, score) list in similarity order
        ranked: List[tuple[int, float]] = []
        for h in hits:
            src = h.get("_source", {})
            pid_val = src.get("product_id") or h.get("_id")
            try:
                pid = int(pid_val)
            except (TypeError, ValueError):
                continue
            score = float(h.get("_score", 0.0))
            ranked.append((pid, score))

        # Fallback if ES returns nothing
        if not ranked:
            ranked = [(pid, 1.0) for pid in sql_ids]

    except Exception as e:
        print("Vector search error, falling back to SQL ordering:", e)
        ranked = [(pid, 1.0) for pid in sql_ids]

    ranked_ids = [pid for pid, _ in ranked]

    # 5) Hydrate from MySQL: title, rating, price, store, primary image
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        placeholders = ", ".join(["%s"] * len(ranked_ids))

        # Core product fields
        cur.execute(
            f"""
            SELECT
                id,
                title,
                average_rating,
                rating_number,
                price,
                store
            FROM products
            WHERE id IN ({placeholders})
            """,
            ranked_ids,
        )
        product_rows = cur.fetchall()
        product_by_id: Dict[int, Dict[str, Any]] = {r["id"]: r for r in product_rows}

        # Images: pick one "primary" per product (prefer variant='MAIN')
        cur.execute(
            f"""
            SELECT
                product_id,
                variant,
                thumb_url,
                large_url,
                hi_res_url
            FROM product_images
            WHERE product_id IN ({placeholders})
            ORDER BY
                product_id,
                CASE WHEN variant = 'MAIN' THEN 0 ELSE 1 END,
                id
            """,
            ranked_ids,
        )
        image_rows = cur.fetchall()
        image_by_id: Dict[int, str] = {}

        for row in image_rows:
            pid = row["product_id"]
            if pid in image_by_id:
                continue  # already picked best one

            url = (
                row.get("hi_res_url")
                or row.get("large_url")
                or row.get("thumb_url")
            )
            if url:
                image_by_id[pid] = url

        cur.close()
        conn.close()

    except Error as e:
        raise HTTPException(status_code=500, detail=f"DB error (details step): {e}")

    # 6) Build final results in similarity order (ranked by _score desc)
    results: List[ProductOut] = []
    for pid, _score in ranked:
        p = product_by_id.get(pid)
        if not p:
            continue

        results.append(
            ProductOut(
                id=pid,
                title=p["title"],
                average_rating=float(p["average_rating"]) if p["average_rating"] is not None else None,
                rating_number=p["rating_number"],
                price=float(p["price"]) if p["price"] is not None else None,
                store=p["store"],
                image_url=image_by_id.get(pid),
            )
        )

    return SearchResponse(sql=sql, params=params, results=results)
