import mysql.connector
from mysql.connector import Error

from db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def update_occasion_beach_from_title(confidence=1.0):
    """
    For all products whose title contains 'beach' (case-insensitive),
    insert a row into product_occasion_labels with label='beach'
    if it does not already exist.
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

        print("✅ Connected to MySQL (%s)" % DB_NAME)
        cursor = conn.cursor()

        # Preview how many products match
        print("\n🔍 Counting products with 'beach' in title...")
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM products p
            WHERE LOWER(p.title) LIKE %s
            """,
            ("%beach%",),
        )
        (count,) = cursor.fetchone()
        print("Found %d products with 'beach' in title." % count)

        print("\n✏️ Inserting 'beach' occasion labels for matching products (if missing)...")

        if confidence is None:
            insert_sql = """
                INSERT INTO product_occasion_labels (product_id, label, confidence)
                SELECT
                    p.id,
                    'beach' AS label,
                    NULL AS confidence
                FROM products p
                LEFT JOIN product_occasion_labels pol
                       ON pol.product_id = p.id
                      AND pol.label = 'beach'
                WHERE LOWER(p.title) LIKE %s
                  AND pol.id IS NULL;
            """
            params = ("%beach%",)
        else:
            insert_sql = """
                INSERT INTO product_occasion_labels (product_id, label, confidence)
                SELECT
                    p.id,
                    'beach' AS label,
                    %s AS confidence
                FROM products p
                LEFT JOIN product_occasion_labels pol
                       ON pol.product_id = p.id
                      AND pol.label = 'beach'
                WHERE LOWER(p.title) LIKE %s
                  AND pol.id IS NULL;
            """
            params = (float(confidence), "%beach%")

        cursor.execute(insert_sql, params)
        affected = cursor.rowcount
        conn.commit()

        print("🎉 Inserted %d new 'beach' occasion rows." % affected)

        cursor.close()

    except Error as e:
        print("❌ MySQL Error: %s" % e)

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    # default: confidence 1.0, change if you like
    update_occasion_beach_from_title(confidence=1.0)
