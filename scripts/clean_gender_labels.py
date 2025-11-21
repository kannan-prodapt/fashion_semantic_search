import mysql.connector
from app.db.db_config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

DELETE_QUERY = """
DELETE pg
FROM product_gender_labels pg
JOIN product_gender_labels pg2
    ON pg.product_id = pg2.product_id
WHERE pg.label = 'men'
  AND pg2.label = 'women';
"""


def clean_gender_labels():
    print("Connecting to database...")

    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    try:
        cursor = conn.cursor()
        print("Running cleanup query...")

        cursor.execute(DELETE_QUERY)
        conn.commit()

        print(f"Rows affected: {cursor.rowcount}")

    finally:
        cursor.close()
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    clean_gender_labels()
