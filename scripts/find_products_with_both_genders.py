import mysql.connector
from mysql.connector import Error

from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def main():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        # SQL query:
        # Step 1 → get product_id, gender
        # Step 2 → group and filter only those having both men & women
        sql = """
            SELECT product_id
            FROM product_gender_labels
            WHERE label IN ('men', 'women')
            GROUP BY product_id
            HAVING COUNT(DISTINCT label) = 2;
        """

        cur.execute(sql)
        rows = cur.fetchall()

        product_ids = [row["product_id"] for row in rows]

        print("=== Products Tagged as BOTH men & women ===")
        print("Count:", len(product_ids))
        print(product_ids[:50])   # print first 50 for preview

        cur.close()
        conn.close()

    except Error as e:
        print("❌ Database error:", e)


if __name__ == "__main__":
    main()
