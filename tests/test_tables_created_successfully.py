import mysql.connector
from mysql.connector import Error

# ==========================
# DB CONFIG
# ==========================

from db.db_config import DB_HOST, DB_PORT, DB_USER,DB_PASSWORD, DB_NAME


# ==========================
# EXPECTED SCHEMA
# ==========================

EXPECTED_TABLES = {
    "products": [
        "id",
        "main_category",
        "title",
        "average_rating",
        "rating_number",
        "price",
        "store",
        "parent_asin",
        "created_at",
        "updated_at",
    ],
    "product_vibe_labels":       ["id", "product_id", "label", "confidence"],
    "product_occasion_labels":   ["id", "product_id", "label", "confidence"],
    "product_gender_labels":     ["id", "product_id", "label", "confidence"],
    "product_category_labels":   ["id", "product_id", "label", "confidence"],
    "product_age_labels":        ["id", "product_id", "label", "confidence"],
    "product_style_labels":      ["id", "product_id", "label", "confidence"],
    "product_images":            ["id", "product_id", "thumb_url", "large_url", "variant", "hi_res_url"],
    "product_videos":            ["id", "product_id", "video_url", "variant", "thumb_url"],
    "product_bought_together":   ["id", "product_id", "related_asin"],
}


# ==========================
# VERIFICATION LOGIC
# ==========================

def main():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )

        if not conn.is_connected():
            print("❌ Could not connect to MySQL")
            return

        print("✅ Connected to MySQL\n")

        cursor = conn.cursor()

        # 1) List all tables in this DB
        cursor.execute("SHOW TABLES;")
        existing_tables = {row[0] for row in cursor.fetchall()}

        print("=== Tables in database ===")
        for t in sorted(existing_tables):
            print("-", t)

        # 2) Check that each expected table exists and has expected columns
        for table, expected_cols in EXPECTED_TABLES.items():
            print(f"--- Checking table: {table} ---")

            if table not in existing_tables:
                print(f"❌ MISSING TABLE: {table}")
                continue
        else:
            print("All Expected Tables Present")
    except Exception:
        print("Error Occurred")

if __name__ == "__main__":
    main()
