import os, re
import time
import mysql.connector
from mysql.connector import Error

import openai
from openai.error import InvalidRequestError

from opensearchpy.helpers import bulk

from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from scripts.opensearch_client2 import get_opensearch_client

# -----------------------------
# CONFIG
# -----------------------------
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
openai.api_key = os.getenv("OPENAI_API_KEY")

INDEX_NAME = "products"
DB_BATCH = 200          # rows per chunk from DB
MAX_TEXT_CHARS = 4000   # truncate very long titles/desc


# -----------------------------
# DB CONNECTION
# -----------------------------
def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


# -----------------------------
# EMBEDDING HELPER (0.28.0 style)
# -----------------------------
def _sanitize_text(t):
    """Convert anything to a safe, short string for embeddings."""
    if t is None:
        t = ""
    try:
        t = str(t)
    except Exception:
        t = ""

    # remove weird control chars
    t = re.sub(r"[^\x20-\x7E\n]", " ", t)
    # collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()

    # avoid truly empty strings – replace with a placeholder
    if t == "":
        t = "empty"

    # hard length cap (very generous for titles)
    return t[:2000]

def get_last_indexed_id(os_client):
    """
    Returns the highest product_id currently indexed in OpenSearch,
    or 0 if the index is empty.
    """
    try:
        resp = os_client.search(
            index=INDEX_NAME,
            body={
                "size": 1,
                "sort": [{"product_id": {"order": "desc"}}],
                "_source": ["product_id"],
                "query": {"match_all": {}}
            }
        )
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return 0
        return int(hits[0]["_source"]["product_id"])
    except Exception as e:
        print("⚠️ Could not fetch last indexed id from OpenSearch:", e)
        return 0

def embed_texts(texts):
    """Return list of embedding vectors for list of strings (with debug)."""
    cleaned = [_sanitize_text(t) for t in texts]

    # Optional: see first few items for sanity
    print("Embedding batch sample (first 3):", [repr(c) for c in cleaned[:3]])

    # ---- 1) Try batch mode ----
    try:
        resp = openai.Embedding.create(
            model=OPENAI_EMBED_MODEL,
            input=cleaned,     # list of strings
        )
        return [d["embedding"] for d in resp["data"]]

    except InvalidRequestError as e:
        # Batch failed – now we hunt the problematic entries.
        print("⚠️ Batch failed → falling back to per-item embeddings.")
        print("   Reason:", e)

        vectors = []
        for idx, text in enumerate(cleaned):
            try:
                r = openai.Embedding.create(
                    model=OPENAI_EMBED_MODEL,
                    input=[text],   # single string as 1-element list
                )
                vectors.append(r["data"][0]["embedding"])
            except Exception as e2:
                # Log *exactly* what blew up
                print("❌ EMBEDDING FAILED at index", idx)
                print("   TEXT repr:", repr(text))
                print("   ERROR:", e2)

                # As a last resort, use embedding of a safe placeholder
                fallback = openai.Embedding.create(
                    model=OPENAI_EMBED_MODEL,
                    input=["fallback text"],
                )
                vectors.append(fallback["data"][0]["embedding"])

        return vectors


def embed_texts_old(texts):
    """
    Return list of embedding vectors for a list of strings.
    Uses legacy openai==0.28.0 client.

    - Truncates to MAX_TEXT_CHARS.
    - If batch call fails, falls back to per-item calls and
      replaces any failing item with an embedding of "".
    """
    cleaned = []
    for t in texts:
        if t is None:
            t = ""
        t = str(t)
        if len(t) > MAX_TEXT_CHARS:
            t = t[:MAX_TEXT_CHARS]
        cleaned.append(t)

    # 1) Try single batch call
    try:
        resp = openai.Embedding.create(
            model=OPENAI_EMBED_MODEL,
            input=cleaned,
        )
        return [d["embedding"] for d in resp["data"]]

    except InvalidRequestError as e:
        print("⚠️ Batch embedding failed with InvalidRequestError:", e)
        print("   Falling back to per-item embeddings…")

        vectors = []
        # 2) Per-item fallback
        for idx, t in enumerate(cleaned):
            try:
                r = openai.Embedding.create(
                    model=OPENAI_EMBED_MODEL,
                    input=[t],
                )
                vectors.append(r["data"][0]["embedding"])
            except InvalidRequestError as e2:
                # Log and use embedding of empty string as safe fallback
                print(f"   ⚠️ Skipping/repairing item idx={idx} due to:", e2)
                r = openai.Embedding.create(
                    model=OPENAI_EMBED_MODEL,
                    input=[""],
                )
                vectors.append(r["data"][0]["embedding"])
        return vectors

    except Exception as e:
        # Any other unexpected error → re-raise so you see it
        print("❌ Unexpected error calling OpenAI embeddings:", repr(e))
        raise


# -----------------------------
# MAIN INDEXING LOOP
# -----------------------------
def main():
    os_client = get_opensearch_client()

    try:
        conn = get_db()
        if not conn.is_connected():
            print("❌ Could not connect to MySQL")
            return

        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS cnt FROM products")
        total = cur.fetchone()["cnt"]
        print("Total products:", total)

        # get last indexed id from OpenSearch
        last_id = get_last_indexed_id(os_client)
        print(f"🔁 Resuming indexing from product_id > {last_id}")

        processed = 0

        while True:
            cur.execute(
                """
                SELECT 
                    id AS product_id,
                    title,
                    main_category,
                    price
                FROM products
                WHERE id > %s
                ORDER BY id
                LIMIT %s
                """,
                (last_id, DB_BATCH),
            )
            rows = cur.fetchall()
            if not rows:
                break

            texts = []
            meta = []
            for row in rows:
                title = row["title"] or ""
                combined = title.strip()
                texts.append(combined)
                meta.append(row)

            print(f"🧠 Embedding {len(texts)} products (last_id={last_id})...")
            embeddings = embed_texts(texts)

            actions = []
            for row, emb in zip(meta, embeddings):
                doc = {
                    "product_id": row["product_id"],
                    "title": row["title"] or "",
                    "description": "",
                    "main_category": row["main_category"],
                    "price": float(row["price"]) if row["price"] is not None else None,
                    "embedding": emb,
                }
                actions.append(
                    {
                        "_op_type": "index",
                        "_index": INDEX_NAME,
                        "_id": str(row["product_id"]),
                        "_source": doc,
                    }
                )

            print(f"📦 Indexing batch of {len(actions)} docs to OpenSearch...")

            success, errors = bulk(
                os_client,
                actions,
                chunk_size=100,
                request_timeout=60,
                raise_on_error=False,
                raise_on_exception=False,
            )

            if errors:
                print(f"⚠️ {len(errors)} doc(s) had errors in this batch (showing up to 5):")
                for err in errors[:5]:
                    print(err)

            processed += len(rows)
            last_id = rows[-1]["product_id"]  # advance to the last id in this batch

            print(f"✅ Indexed {processed} new documents (up to id={last_id})")
            time.sleep(1)

        cur.close()
        conn.close()
        print("🎉 Completed indexing")

    except Error as e:
        print("❌ MySQL error:", e)


if __name__ == "__main__":
    main()
