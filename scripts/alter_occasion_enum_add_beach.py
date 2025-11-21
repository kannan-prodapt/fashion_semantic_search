import mysql.connector
from mysql.connector import Error

from db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

ALTER_SQL = """
ALTER TABLE product_occasion_labels
MODIFY COLUMN label ENUM(
    'casual','office','party','festive','wedding',
    'gym','travel','loungewear','summer','winter','beach'
) NOT NULL;
"""


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
        cursor = conn.cursor()

        print("\nRunning ALTER on product_occasion_labels.label ...")
        cursor.execute(ALTER_SQL)
        conn.commit()
        print("🎉 ALTER completed successfully. 'beach' added to OCCASION ENUM.\n")

        cursor.close()

    except Error as e:
        print("❌ MySQL Error: %s" % e)

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    main()

