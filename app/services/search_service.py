# app/services/search_service.py
import os
from typing import List, Dict, Any, Tuple

import openai
from fastapi import HTTPException
from mysql.connector import Error

from app.schemas.search import SearchRequest, ProductOut, SearchResponse
from app.db.connection import get_db_connection
from app.core.llm_filters import llm_filters_cached
from app.core.sql_builder import build_sql_from_filters
from app.opensearch_client import get_opensearch_client

OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "MYKEY")
openai.api_key = os.getenv("OPENAI_API_KEY")


def verify_search_key(search_key: str) -> None:
    if search_key != SEARCH_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid search_key")


def embed_query(text: str) -> List[float]:
    resp = openai.Embedding.create(
        model=OPENAI_EMBED_MODEL,
        input=text,
    )
    return resp["data"][0]["embedding"]


def get_candidate_ids_from_sql(req: SearchRequest) -> Tuple[str, List[Any], List[int]]:
    filters = llm_filters_cached(req.query)
    sql, params = build_sql_from_filters(filters, req.limit)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()  # (id, title)
        cur.close()
        conn.close()
    except Error as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    sql_ids = [row[0] for row in rows]
    return sql, filters, sql_ids


def hydrate_products_in_order(id_order: List[int]) -> List[ProductOut]:
    if not id_order:
        return []

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        placeholders = ", ".join(["%s"] * len(id_order))

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
            id_order,
        )
        product_rows = cur.fetchall()
        product_by_id: Dict[int, Dict[str, Any]] = {r["id"]: r for r in product_rows}

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
            id_order,
        )
        image_rows = cur.fetchall()
        image_by_id: Dict[int, str] = {}

        for row in image_rows:
            pid = row["product_id"]
            if pid in image_by_id:
                continue
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

    results: List[ProductOut] = []
    for pid in id_order:
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
    return results


def search_sql_only(req: SearchRequest) -> SearchResponse:
    verify_search_key(req.search_key)
    sql, filters, sql_ids = get_candidate_ids_from_sql(req)
    results = hydrate_products_in_order(sql_ids)
    print("sql => ", sql)
    return SearchResponse(filters=filters, results=results)


def search_with_vector(req: SearchRequest) -> SearchResponse:
    verify_search_key(req.search_key)
    sql, filters, sql_ids = get_candidate_ids_from_sql(req)

    if not sql_ids:
        return SearchResponse(filters=filters, results=[])

    try:
        os_client = get_opensearch_client()
        query_vec = embed_query(req.query)

        body = {
            "size": len(sql_ids),
            "query": {
                "knn": {
                    "embedding": {
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

        ranked = []
        for h in hits:
            src = h.get("_source", {})
            pid_val = src.get("product_id") or h.get("_id")
            try:
                pid = int(pid_val)
            except (TypeError, ValueError):
                continue
            score = float(h.get("_score", 0.0))
            ranked.append((pid, score))

        if not ranked:
            ranked = [(pid, 1.0) for pid in sql_ids]

    except Exception as e:
        print("Vector search error, falling back to SQL ordering:", e)
        ranked = [(pid, 1.0) for pid in sql_ids]

    ranked_ids = [pid for pid, _ in ranked]
    results = hydrate_products_in_order(ranked_ids)
    print("sql => ", sql)
    return SearchResponse(filters = filters, results=results)
