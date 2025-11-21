# app/services/search_service.py
import os
from typing import List, Dict, Any, Tuple, Optional

import openai
from fastapi import HTTPException
from mysql.connector import Error

from app.schemas.search import SearchRequest, ProductOut, SearchResponse
from app.db.connection import get_db_connection
from app.core.llm_filters import llm_filters_cached
from app.core.sql_builder import build_sql_from_filters
from app.opensearch_client import get_opensearch_client

import json
import time
from collections import OrderedDict

_RANK_CACHE: "OrderedDict[str, Tuple[float, List[int]]]" = OrderedDict()

RANK_CACHE_TTL_SECONDS = 300  # 5 minutes
RANK_CACHE_MAX_SIZE = 1024    # tune as needed



def _make_rank_cache_key(filters: Dict[str, Any], sql_ids: List[int], query: str) -> str:
    """
    Create a deterministic, hashable cache key from filters, candidate IDs and query.
    """
    return json.dumps(
        {
            "filters": filters,       # must be JSON serializable
            "sql_ids": sql_ids,       # preserves ordering of SQL candidates
            "query": query.strip(),   # normalized query
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _rank_cache_get(key: str) -> Optional[List[int]]:
    """
    LRU + TTL get. Returns ranked_ids or None if not present / expired.
    """
    now = time.time()
    item = _RANK_CACHE.get(key)
    if not item:
        return None

    ts, ranked_ids = item
    if now - ts > RANK_CACHE_TTL_SECONDS:
        # expired
        try:
            del _RANK_CACHE[key]
        except KeyError:
            pass
        return None

    _RANK_CACHE.move_to_end(key)
    return ranked_ids



def _rank_cache_set(key: str, ranked_ids: List[int]) -> None:
    """
    LRU insert/update for ranked_ids.
    """
    now = time.time()
    _RANK_CACHE[key] = (now, ranked_ids)
    _RANK_CACHE.move_to_end(key)

    if len(_RANK_CACHE) > RANK_CACHE_MAX_SIZE:
        # pop oldest
        _RANK_CACHE.popitem(last=False)

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

def get_candidate_ids_from_sql(req: SearchRequest) -> Tuple[str, List[Any], Dict[str, Any], List[int]]:
    """
    Use LLM filters; if the initial filter combo returns 0 results,
    progressively relax filters in a defined hierarchy until we get hits
    or run out of filters to drop.

    Returns:
        sql:        final SQL string (with %s placeholders)
        params:     final param list
        filters:    final filters dict actually used
        sql_ids:    list of product IDs
    """
    base_filters: Dict[str, Any] = llm_filters_cached(req.query)

    # Order of relaxation (least important first)
    RELAX_GROUPS = [
        ["style_in", "style_not_in"],
        ["vibe_in", "vibe_not_in"],
        ["occasion_in", "occasion_not_in"],
        ["age_in", "age_not_in"],
        ["gender_in", "gender_not_in"],
        ["category_in", "category_not_in"],
        # if you ever want to relax price/rating/store, add groups here
        # e.g. ["price_min", "price_max"], ["rating_min"], ...
    ]

    current_filters = dict(base_filters)
    last_sql: str = ""
    last_params: List[Any] = []
    last_ids: List[int] = []

    # Try base filters, then progressively relax
    for idx in range(len(RELAX_GROUPS) + 1):
        # Run query for current_filters
        sql, params, sql_ids = run_sql_for_filters(current_filters, req.limit)
        last_sql, last_params, last_ids = sql, params, sql_ids

        if sql_ids:
            # We have results – return with the filters actually used
            return sql, params, current_filters, sql_ids

        # No results and no more groups to relax -> stop
        if idx == len(RELAX_GROUPS):
            break

        # Drop the next group of filters (if present)
        group = RELAX_GROUPS[idx]
        dropped_any = False
        for key in group:
            if key in current_filters:
                current_filters.pop(key, None)
                dropped_any = True

        # If this group had nothing, just move on to the next group
        if dropped_any:
            print(f"[RELAX] No results, removed filters: {group}")

    # If we reach here, even fully relaxed filters gave 0 rows
    return last_sql, last_params, current_filters, last_ids

def get_candidate_ids_from_sql_deprecated(req: SearchRequest) -> Tuple[str, List[Any], List[int]]:
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

def run_sql_for_filters(filters: Dict[str, Any], limit: int) -> Tuple[str, List[Any], List[int]]:
    """
    Build SQL + params from filters, execute, and return (sql, params, id_list).
    """
    sql, params = build_sql_from_filters(filters, limit)

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
    return sql, params, sql_ids

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


def debug_sql(sql: str, params: list) -> str:
    """
    Returns a readable SQL string with %s replaced by escaped parameters.
    For DEBUG ONLY — do NOT execute this output.
    """
    if not params:
        return sql

    out = sql
    for p in params:
        if isinstance(p, str):
            rep = "'" + p.replace("'", "\\'") + "'"   # escape quotes
        elif p is None:
            rep = "NULL"
        else:
            rep = str(p)
        out = out.replace("%s", rep, 1)

    return out


def search_sql_only_deprecated(req: SearchRequest) -> SearchResponse:
    verify_search_key(req.search_key)
    sql, filters, sql_ids = get_candidate_ids_from_sql(req)
    results = hydrate_products_in_order(sql_ids)
    print("sql => ", debug_sql(sql, filters))
    return SearchResponse(filters=filters, results=results)

def search_sql_only(req: SearchRequest) -> SearchResponse:
    verify_search_key(req.search_key)
    sql, params, filters, sql_ids = get_candidate_ids_from_sql(req)
    results = hydrate_products_in_order(sql_ids)
    print("sql => ", debug_sql(sql, params))
    return SearchResponse(filters=filters, results=results)



def search_with_vector(req: SearchRequest) -> SearchResponse:
    verify_search_key(req.search_key)
    sql, params, filters, sql_ids = get_candidate_ids_from_sql(req)

    if not sql_ids:
        return SearchResponse(filters=filters, results=[])

    # --- Cache key based on filters + candidate ids + query ---
    cache_key = _make_rank_cache_key(filters, sql_ids, req.query)
    cached_ranked_ids = _rank_cache_get(cache_key)

    if cached_ranked_ids is not None:
        # Cache hit: bypass embedding + OpenSearch entirely
        ranked_ids = cached_ranked_ids
    else:
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
    print("sql => ", debug_sql(sql, params))
    return SearchResponse(filters = filters, results=results)
