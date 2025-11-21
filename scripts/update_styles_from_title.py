import mysql.connector
from mysql.connector import Error

# reuse your existing DB config
from db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def update_style_for_keyword(
    keyword: str,
    style_label: str,
    confidence: float = None,
):
    """
    For all products whose title contains `keyword` (case-insensitive),
    insert a row into product_style_labels with label = style_label
    and optional confidence, if such a row does not already exist.
    """

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

        print(f"✅ Connected to MySQL ({DB_NAME})")

        cursor = conn.cursor()

        # Preview count
        print(f"\n🔍 Checking products with title containing '{keyword}'...")
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM products p
            WHERE LOWER(p.title) LIKE %s
            """,
            (f"%{keyword.lower()}%",),
        )
        (cnt,) = cursor.fetchone()
        print(f"Found {cnt} products with '{keyword}' in title.")

        # Insert missing style/attribute rows
        print(f"\n✏️ Inserting style/attribute '{style_label}' for matching products (if missing)...")

        if confidence is None:
            insert_sql = """
                INSERT INTO product_style_labels (product_id, label, confidence)
                SELECT
                    p.id,
                    %s AS label,
                    NULL AS confidence
                FROM products p
                LEFT JOIN product_style_labels psl
                       ON psl.product_id = p.id
                      AND psl.label = %s
                WHERE LOWER(p.title) LIKE %s
                  AND psl.id IS NULL;
            """
            params = (style_label, style_label, f"%{keyword.lower()}%")

        else:
            insert_sql = """
                INSERT INTO product_style_labels (product_id, label, confidence)
                SELECT
                    p.id,
                    %s AS label,
                    %s AS confidence
                FROM products p
                LEFT JOIN product_style_labels psl
                       ON psl.product_id = p.id
                      AND psl.label = %s
                WHERE LOWER(p.title) LIKE %s
                  AND psl.id IS NULL;
            """
            params = (style_label, float(confidence), style_label, f"%{keyword.lower()}%")

        cursor.execute(insert_sql, params)
        affected = cursor.rowcount
        conn.commit()

        print(f"🎉 Inserted {affected} new rows into product_style_labels.")

        cursor.close()

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    # Example: detect color "red"
    update_style_for_keyword(
        keyword="red",
        style_label="red",     # must be in ENUM
        confidence=1.0,        # or None
    )
