import pandas as pd
import mysql.connector
from mysql.connector import Error
import json
import ast
import math

# ==========================
# DB CONFIG
# ==========================

from app.db.db_config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

CSV_FILE_PATH = "final_processed_data.csv"
CHUNK_SIZE = 5000   # adjust as needed


# ==========================
# DB CONNECTION
# ==========================

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False
    )


# ==========================
# SAFE VALUE HELPERS
# ==========================

def is_nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def parse_label_list(label_str):
    if not isinstance(label_str, str):
        return []
    parts = [x.strip() for x in label_str.split(",")]
    return [x for x in parts if x]


def parse_conf_json(conf_str):
    if not isinstance(conf_str, str) or not conf_str.strip():
        return {}
    try:
        return json.loads(conf_str)
    except:
        return {}


def parse_list_of_dicts(value):
    if not isinstance(value, str) or value.strip() in ("", "[]", "nan", "None"):
        return []
    try:
        obj = ast.literal_eval(value)
        if isinstance(obj, list):
            return [d for d in obj if isinstance(d, dict)]
        return []
    except:
        return []


def parse_list_of_values(value):
    if not isinstance(value, str) or value.strip() in ("", "[]", "nan", "None"):
        return []
    try:
        obj = ast.literal_eval(value)
        if isinstance(obj, list):
            return [str(x).strip() for x in obj if x not in (None, "")]
        return []
    except:
        return []


# ==========================
# INSERT / UPSERT PRODUCTS
# ==========================

def upsert_products(conn, df):
    cursor = conn.cursor()

    sql = """
        INSERT INTO products (
            main_category, title, average_rating, rating_number,
            price, store, parent_asin
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            main_category=VALUES(main_category),
            title=VALUES(title),
            average_rating=VALUES(average_rating),
            rating_number=VALUES(rating_number),
            price=VALUES(price),
            store=VALUES(store)
    """

    rows = []
    for row in df.itertuples(index=False):
        rows.append((
            getattr(row, "main_category"),
            getattr(row, "title"),
            None if is_nan(getattr(row, "average_rating")) else getattr(row, "average_rating"),
            None if is_nan(getattr(row, "rating_number")) else getattr(row, "rating_number"),
            None if is_nan(getattr(row, "price")) else getattr(row, "price"),
            getattr(row, "store"),
            getattr(row, "parent_asin"),
        ))

    cursor.executemany(sql, rows)
    cursor.close()
    conn.commit()


def fetch_product_ids(conn, parent_asins):
    if not parent_asins:
        return {}

    cursor = conn.cursor()
    placeholders = ",".join(["%s"] * len(parent_asins))
    sql = f"""
        SELECT id, parent_asin
        FROM products
        WHERE parent_asin IN ({placeholders})
    """

    cursor.execute(sql, list(parent_asins))
    mapping = {parent_asin: pid for pid, parent_asin in cursor.fetchall()}
    cursor.close()
    return mapping


# ==========================
# GENERIC LABEL INSERTOR
# ==========================

def insert_label_rows(conn, df, product_id_map, labels_col, conf_col, table_name):
    cursor = conn.cursor()

    sql = f"INSERT INTO {table_name} (product_id, label, confidence) VALUES (%s, %s, %s)"

    rows = []

    for row in df.itertuples(index=False):
        parent_asin = getattr(row, "parent_asin")
        product_id = product_id_map.get(parent_asin)
        if not product_id:
            continue

        labels = parse_label_list(getattr(row, labels_col))
        conf_dict = parse_conf_json(getattr(row, conf_col))

        for label in labels:
            conf = conf_dict.get(label)
            rows.append((product_id, label, conf))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    cursor.close()


# ==========================
# MEDIA INSERTORS
# ==========================

def insert_images(conn, df, product_id_map):
    cursor = conn.cursor()
    sql = """
        INSERT INTO product_images
            (product_id, thumb_url, large_url, variant, hi_res_url)
        VALUES (%s, %s, %s, %s, %s)
    """
    rows = []

    for row in df.itertuples(index=False):
        pid = product_id_map.get(getattr(row, "parent_asin"))
        if not pid:
            continue

        imgs = parse_list_of_dicts(getattr(row, "images"))
        for img in imgs:
            rows.append((pid, img.get("thumb"), img.get("large"),
                         img.get("variant"), img.get("hi_res")))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    cursor.close()


def insert_videos(conn, df, product_id_map):
    cursor = conn.cursor()
    sql = """
        INSERT INTO product_videos
            (product_id, video_url, variant, thumb_url)
        VALUES (%s, %s, %s, %s)
    """
    rows = []

    for row in df.itertuples(index=False):
        pid = product_id_map.get(getattr(row, "parent_asin"))
        if not pid:
            continue

        vids = parse_list_of_dicts(getattr(row, "videos"))
        for v in vids:
            rows.append((pid,
                         v.get("url") or v.get("video_url"),
                         v.get("variant"),
                         v.get("thumb") or v.get("thumbnail")))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    cursor.close()


def insert_bought_together(conn, df, product_id_map):
    cursor = conn.cursor()

    sql = """
        INSERT INTO product_bought_together
            (product_id, related_asin)
        VALUES (%s, %s)
    """

    rows = []

    for row in df.itertuples(index=False):
        pid = product_id_map.get(getattr(row, "parent_asin"))
        if not pid:
            continue

        bt_list = parse_list_of_values(getattr(row, "bought_together"))
        for asin in bt_list:
            rows.append((pid, asin))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    cursor.close()


# ==========================
# MAIN INGESTION PIPELINE
# ==========================

def load_csv_normalized():
    conn = get_connection()

    try:
        chunk_iter = pd.read_csv(CSV_FILE_PATH, chunksize=CHUNK_SIZE)

        for i, chunk in enumerate(chunk_iter, start=1):
            print(f"\n=== Processing chunk {i} (rows={len(chunk)}) ===")

            # 1) Insert/Update products
            upsert_products(conn, chunk)

            # 2) Resolve product IDs
            parent_asins = set(chunk["parent_asin"].astype(str))
            product_id_map = fetch_product_ids(conn, parent_asins)

            # 3) Label tables
            insert_label_rows(conn, chunk, product_id_map,
                              "vibe_labels", "vibe_conf", "product_vibe_labels")

            insert_label_rows(conn, chunk, product_id_map,
                              "occasion_labels", "occasion_conf", "product_occasion_labels")

            insert_label_rows(conn, chunk, product_id_map,
                              "gender_labels", "gender_conf", "product_gender_labels")

            insert_label_rows(conn, chunk, product_id_map,
                              "category_labels", "category_conf", "product_category_labels")

            insert_label_rows(conn, chunk, product_id_map,
                              "age_labels", "age_conf", "product_age_labels")

            insert_label_rows(conn, chunk, product_id_map,
                              "style_labels", "style_conf", "product_style_labels")

            # 4) Media tables
            insert_images(conn, chunk, product_id_map)
            insert_videos(conn, chunk, product_id_map)
            insert_bought_together(conn, chunk, product_id_map)

            print(f"✅ Finished chunk {i}")

    except Exception as e:
        print("❌ Error:", e)

    finally:
        if conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    load_csv_normalized()

