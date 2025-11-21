import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="sb-database-instance.c50geqe0uhru.ap-south-1.rds.amazonaws.com",      # e.g. mydb.abc123.ap-south-1.rds.amazonaws.com
            port=3306,                         # default MySQL port
            user="admin",
            password="kpgt1234"
        )

        if connection.is_connected():
            print("✅ Connected to MySQL database")
            return connection

    except Error as e:
        print(f"❌ Error while connecting to MySQL: {e}")

    return None


def create_table(connection):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        connection.commit()
        print("✅ Table 'users' created (or already exists).")

    except Error as e:
        print(f"❌ Error while creating table: {e}")

    finally:
        cursor.close()


def main():
    connection = create_connection()
    if connection:
        try:
            create_table(connection)
        finally:
            connection.close()
            print("🔒 MySQL connection closed.")


if __name__ == "__main__":
    main()

