import os
import time
import mysql.connector
from mysql.connector import Error
import openai
from opensearchpy.helpers import bulk

# ⚠️ Adjust this import depending on where your db_config lives.
# If this fails, change to: from db.db_config import ...
from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

from scripts.opensearch_client2 import get_opensearch_client

OPENAI_EMBED_MODEL = "text-embedding-ada-002"
openai.api_key = os.getenv("OPENAI_API_KEY")

INDEX_NAME = "products"
DB_BATCH = 200  # rows per chunk from DB


def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def embed_texts(texts):
    """Return list of embedding vectors for list of strings."""
    resp = openai.Embedding.create(
        model=OPENAI_EMBED_MODEL,
        input=[t if t is not None else "" for t in texts],
    )
    return [d["embedding"] for d in resp["data"]]


def main():
    client = get_opensearch_client()

    try:
        conn = get_db()
        if not conn.is_connected():
            print("❌ Could not connect to MySQL")
            return

        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS cnt FROM products")
        total = cur.fetchone()["cnt"]
        print("Total products:", total)

        offset = 0
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
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (DB_BATCH, offset),
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

            print(f"🧠 Embedding {len(texts)} products (offset={offset})...")
            embeddings = embed_texts(texts)

            actions = []
            for row, emb in zip(meta, embeddings):
                doc = {
                    "product_id": row["product_id"],
                    "title": row["title"] or "",
                    "description": "",  # placeholder; fill later if you have it
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

            # Use bulk with retries & backoff to reduce 429 errors
            success, errors = bulk(
                client,
                actions,
                chunk_size=100,          # smaller chunks to reduce load on cluster
                max_retries=5,           # retry failed items (incl. 429) up to 5 times
                initial_backoff=2,       # 2s, 4s, 8s, 16s, 32s...
                max_backoff=60,          # cap backoff
                request_timeout=60,      # give cluster time to respond
                raise_on_error=False,    # don't raise on per-item error
                raise_on_exception=False # don't raise on exceptions inside helpers
            )

            if errors:
                # errors is a list of per-item error dicts
                print(f"⚠️ {len(errors)} doc(s) had errors in this batch (showing up to 5):")
                for err in errors[:5]:
                    print(err)

            processed += len(rows)
            offset += DB_BATCH
            print(f"✅ Indexed {processed}/{total} documents")

            # Small pause between batches to be nicer to the cluster
            time.sleep(1)

        cur.close()
        conn.close()
        print("🎉 Completed indexing")

    except Error as e:
        print("❌ MySQL error:", e)


if __name__ == "__main__":
    main()
