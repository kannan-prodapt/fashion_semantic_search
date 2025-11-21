import mysql.connector
from mysql.connector import Error

# reuse your existing DB config
from db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def update_category_for_keyword(
    keyword: str,
    category_label: str,
    confidence: float = None,
):
    """
    For all products whose title contains `keyword` (case-insensitive),
    insert a row into product_category_labels with label = category_label
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

        # Now insert missing category rows
        print(f"\n✏️ Inserting category '{category_label}' for matching products (if missing)...")

        if confidence is None:
            insert_sql = """
                INSERT INTO product_category_labels (product_id, label, confidence)
                SELECT 
                    p.id,
                    %s AS label,
                    NULL AS confidence
                FROM products p
                LEFT JOIN product_category_labels pcl
                       ON pcl.product_id = p.id
                      AND pcl.label = %s
                WHERE LOWER(p.title) LIKE %s
                  AND pcl.id IS NULL;
            """
            params = (category_label, category_label, f"%{keyword.lower()}%")
        else:
            insert_sql = """
                INSERT INTO product_category_labels (product_id, label, confidence)
                SELECT 
                    p.id,
                    %s AS label,
                    %s AS confidence
                FROM products p
                LEFT JOIN product_category_labels pcl
                       ON pcl.product_id = p.id
                      AND pcl.label = %s
                WHERE LOWER(p.title) LIKE %s
                  AND pcl.id IS NULL;
            """
            params = (category_label, float(confidence), category_label, f"%{keyword.lower()}%")

        cursor.execute(insert_sql, params)
        affected = cursor.rowcount
        conn.commit()

        print(f"🎉 Inserted {affected} new rows into product_category_labels.")

        cursor.close()

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    # Example: update socks category from title keyword "socks"
    update_category_for_keyword(
        keyword="socks",
        category_label="socks",  # must be in ENUM
        confidence=1.0,          # or None if you want NULL
    )
