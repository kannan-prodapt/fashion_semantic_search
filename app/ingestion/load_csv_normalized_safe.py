import pandas as pd
import mysql.connector
from mysql.connector import Error
import ast
import json

# ==========================
# DB CONFIG
# ==========================

from db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

CSV_FILE_PATH = "final_processed_data.csv"
CHUNK_SIZE = 3000


# ==========================
# DB CONNECTION
# ==========================

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
    )


# ==========================
# GENERIC CLEANERS
# ==========================

def is_nan(x):
    return pd.isna(x)


def clean_scalar(x):
    """Convert any NaN / 'nan' / 'NaN' / 'None' / '' to None."""
    if is_nan(x):
        return None
    if isinstance(x, str) and x.strip().lower() in ("nan", "none", ""):
        return None
    return x


def parse_list_of_dicts(value):
    value = clean_scalar(value)
    if not isinstance(value, str) or value.strip() in ("", "[]"):
        return []
    try:
        obj = ast.literal_eval(value)
        return obj if isinstance(obj, list) else []
    except Exception:
        return []


def parse_list_of_values(value):
    value = clean_scalar(value)
    if not isinstance(value, str) or value.strip() in ("", "[]"):
        return []
    try:
        obj = ast.literal_eval(value)
        return [str(x).strip() for x in obj if x not in (None, "")] if isinstance(obj, list) else []
    except Exception:
        return []


def parse_label_list(x):
    x = clean_scalar(x)
    if not isinstance(x, str):
        return []
    return [v.strip() for v in x.split(",") if v.strip()]


def parse_conf_json(x):
    x = clean_scalar(x)
    if not isinstance(x, str) or not x.strip():
        return {}
    try:
        return json.loads(x)
    except Exception:
        return {}


# ==========================
# COLUMN PRINTER
# ==========================

printed_tables = set()

def print_table_columns_once(conn, table_name):
    if table_name in printed_tables:
        return

    cur = conn.cursor()
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (DB_NAME, table_name),
    )
    cols = [row[0] for row in cur.fetchall()]
    cur.close()

    print("\n" + "=" * 48)
    print(f"TABLE: {table_name}")
    print("DATABASE COLUMNS:")
    for c in cols:
        print(" -", c)
    print("=" * 48 + "\n")

    printed_tables.add(table_name)


# ==========================
# PRODUCTS (UPSERT)
# ==========================

def upsert_products(conn, df):
    table = "products"
    print_table_columns_once(conn, table)

    sql = """
        INSERT INTO products (
            main_category, title, average_rating, rating_number,
            price, store, parent_asin
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            main_category = VALUES(main_category),
            title         = VALUES(title),
            average_rating= VALUES(average_rating),
            rating_number = VALUES(rating_number),
            price         = VALUES(price),
            store         = VALUES(store)
    """

    cur = conn.cursor()
    rows = []

    for row in df.itertuples(index=False):
        avg_rating = clean_scalar(getattr(row, "average_rating", None))
        rating_num = clean_scalar(getattr(row, "rating_number", None))
        price      = clean_scalar(getattr(row, "price", None))

        rows.append((
            clean_scalar(getattr(row, "main_category")),
            clean_scalar(getattr(row, "title")),
            float(avg_rating) if avg_rating is not None else None,
            int(rating_num)   if rating_num is not None else None,
            float(price)      if price is not None else None,
            clean_scalar(getattr(row, "store")),
            clean_scalar(getattr(row, "parent_asin")),
        ))

    cur.executemany(sql, rows)
    conn.commit()
    cur.close()


def fetch_product_ids(conn, asins):
    asins = {clean_scalar(a) for a in asins if clean_scalar(a) is not None}
    if not asins:
        return {}

    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(asins))
    sql = f"""
        SELECT id, parent_asin
        FROM products
        WHERE parent_asin IN ({placeholders})
    """
    cur.execute(sql, list(asins))
    mapping = {asin: pid for pid, asin in cur.fetchall()}
    cur.close()
    return mapping


# ==========================
# GENERIC LABEL INSERT
# ==========================

def insert_label_table(conn, df, id_map, label_col, conf_col, table_name):
    print_table_columns_once(conn, table_name)

    sql = f"""
        INSERT INTO {table_name} (product_id, label, confidence)
        VALUES (%s, %s, %s)
    """

    cur = conn.cursor()
    rows = []

    for row in df.itertuples(index=False):
        asin = clean_scalar(getattr(row, "parent_asin"))
        pid = id_map.get(asin)
        if not pid:
            continue

        labels = parse_label_list(getattr(row, label_col, None))
        confs  = parse_conf_json(getattr(row, conf_col, None))

        for label in labels:
            label_clean = clean_scalar(label)
            if label_clean is None:
                continue
            conf = clean_scalar(confs.get(label)) if isinstance(confs, dict) else None
            rows.append((pid, label_clean, conf))

    if rows:
        cur.executemany(sql, rows)
        conn.commit()

    cur.close()


# ==========================
# MEDIA TABLE INSERTS
# ==========================

def insert_images(conn, df, id_map):
    table = "product_images"
    print_table_columns_once(conn, table)

    sql = """
        INSERT INTO product_images
            (product_id, thumb_url, large_url, variant, hi_res_url)
        VALUES (%s,%s,%s,%s,%s)
    """

    cur = conn.cursor()
    rows = []

    for row in df.itertuples(index=False):
        asin = clean_scalar(getattr(row, "parent_asin"))
        pid = id_map.get(asin)
        if not pid:
            continue

        imgs = parse_list_of_dicts(getattr(row, "images", None))
        for img in imgs:
            rows.append((
                pid,
                clean_scalar(img.get("thumb")),
                clean_scalar(img.get("large")),
                clean_scalar(img.get("variant")),
                clean_scalar(img.get("hi_res")),
            ))

    if rows:
        cur.executemany(sql, rows)
        conn.commit()

    cur.close()


def insert_videos(conn, df, id_map):
    table = "product_videos"
    print_table_columns_once(conn, table)

    sql = """
        INSERT INTO product_videos
            (product_id, video_url, variant, thumb_url)
        VALUES (%s,%s,%s,%s)
    """

    cur = conn.cursor()
    rows = []

    for row in df.itertuples(index=False):
        asin = clean_scalar(getattr(row, "parent_asin"))
        pid = id_map.get(asin)
        if not pid:
            continue

        vids = parse_list_of_dicts(getattr(row, "videos", None))
        for v in vids:
            rows.append((
                pid,
                clean_scalar(v.get("url") or v.get("video_url")),
                clean_scalar(v.get("variant")),
                clean_scalar(v.get("thumb") or v.get("thumbnail")),
            ))

    if rows:
        cur.executemany(sql, rows)
        conn.commit()

    cur.close()


def insert_bought_together(conn, df, id_map):
    table = "product_bought_together"
    print_table_columns_once(conn, table)

    sql = """
        INSERT INTO product_bought_together
            (product_id, related_asin)
        VALUES (%s,%s)
    """

    cur = conn.cursor()
    rows = []

    for row in df.itertuples(index=False):
        asin = clean_scalar(getattr(row, "parent_asin"))
        pid = id_map.get(asin)
        if not pid:
            continue

        bt_list = parse_list_of_values(getattr(row, "bought_together", None))
        for related in bt_list:
            related_clean = clean_scalar(related)
            if related_clean is None:
                continue
            rows.append((pid, related_clean))

    if rows:
        cur.executemany(sql, rows)
        conn.commit()

    cur.close()


# ==========================
# MAIN PIPELINE
# ==========================

def load_csv():
    conn = get_conn()

    try:
        chunk_iter = pd.read_csv(CSV_FILE_PATH, chunksize=CHUNK_SIZE)

        for i, chunk in enumerate(chunk_iter, start=1):
            print(f"\n=== Processing chunk {i} (rows={len(chunk)}) ===")

            # 1) Upsert products
            upsert_products(conn, chunk)

            # 2) Resolve product IDs
            asins = set(chunk["parent_asin"])
            id_map = fetch_product_ids(conn, asins)
            print(f"Resolved {len(id_map)} product_ids for this chunk.")

            # 3) Labels
            insert_label_table(conn, chunk, id_map,
                               "vibe_labels", "vibe_conf", "product_vibe_labels")
            insert_label_table(conn, chunk, id_map,
                               "occasion_labels", "occasion_conf", "product_occasion_labels")
            insert_label_table(conn, chunk, id_map,
                               "gender_labels", "gender_conf", "product_gender_labels")
            insert_label_table(conn, chunk, id_map,
                               "category_labels", "category_conf", "product_category_labels")
            insert_label_table(conn, chunk, id_map,
                               "age_labels", "age_conf", "product_age_labels")
            insert_label_table(conn, chunk, id_map,
                               "style_labels", "style_conf", "product_style_labels")

            # 4) Media
            insert_images(conn,   chunk, id_map)
            insert_videos(conn,   chunk, id_map)
            insert_bought_together(conn, chunk, id_map)

            print(f"✅ Chunk {i} complete.")

    except Error as e:
        print("❌ MySQL Error:", e)
    except Exception as e:
        print("❌ Python Error:", e)
    finally:
        if conn.is_connected():
            conn.close()
            print("🔒 DB connection closed.")


if __name__ == "__main__":
    load_csv()

