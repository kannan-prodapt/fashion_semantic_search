import mysql.connector
from mysql.connector import Error

from app.db.db_config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
)

# (table_name, alias)
LABEL_TABLES = [
    ("product_category_labels", "pc"),
    ("product_style_labels", "ps"),
    ("product_vibe_labels", "pv"),
    ("product_occasion_labels", "po"),
    ("product_gender_labels", "pg"),
    ("product_age_labels", "pa"),
]


def cleanup_table(conn, table_name: str, alias: str):
    """
    Delete rows from the given label table where the label text
    does NOT appear in the product title as a separate word
    (case-insensitive, word-boundary aware).
    """

    # We match label as a 'word' using a regex:
    #   (^|[^a-z0-9])label([^a-z0-9]|$)
    #
    # Example:
    #   label = 'men'
    #   title = 'men t-shirt'      -> MATCH  (ok)
    #   title = 'for women only'   -> NO MATCH (correct)
    #
    # LOWER() on both sides keeps it case-insensitive.
    sql = f"""
        DELETE {alias}
        FROM {table_name} AS {alias}
        JOIN products AS p ON p.id = {alias}.product_id
        WHERE NOT (
            LOWER(p.title) REGEXP CONCAT(
                '(^|[^a-z0-9])',
                LOWER({alias}.label),
                '([^a-z0-9]|$)'
            )
        );
    """

    cursor = conn.cursor()
    try:
        print(f"Running cleanup on table: {table_name} ...")
        cursor.execute(sql)
        affected = cursor.rowcount
        conn.commit()
        print(f"  -> Removed {affected} rows from {table_name}")
    finally:
        cursor.close()


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

        print("✅ Connected to MySQL")

        for table_name, alias in LABEL_TABLES:
            cleanup_table(conn, table_name, alias)

    except Error as e:
        print(f"❌ MySQL Error: {e}")
    finally:
        if "conn" in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    main()
