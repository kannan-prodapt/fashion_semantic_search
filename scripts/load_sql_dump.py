import argparse
import mysql.connector
from mysql.connector import Error


def load_sql_dump(host, port, user, password, db, dump_file):
    try:
        print(f"🔌 Connecting to MySQL at {host}:{port} …")
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db,
            autocommit=True
        )
        cursor = conn.cursor()
        print(f"✅ Connected to database `{db}`")

        print(f"📥 Loading SQL dump: {dump_file}")

        with open(dump_file, "r", encoding="utf-8") as f:
            sql_commands = f.read()

        # Split by semicolon — MySQL dumping style
        statements = sql_commands.split(";")

        for stmt in statements:
            stmt_clean = stmt.strip()
            if stmt_clean:
                try:
                    cursor.execute(stmt_clean + ";")
                except Exception as ex:
                    print(f"⚠️ Skipping statement due to error:\n{stmt_clean}\nError: {ex}")

        print("🎉 SQL dump loaded successfully!")

    except Error as e:
        print(f"❌ MySQL error: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load a MySQL dump into a database")

    parser.add_argument("--host", required=True, help="MySQL host")
    parser.add_argument("--port", default=3306, type=int, help="MySQL port")
    parser.add_argument("--user", required=True, help="MySQL username")
    parser.add_argument("--password", required=True, help="MySQL password")
    parser.add_argument("--db", required=True, help="Target database")
    parser.add_argument("--file", required=True, help="Path to .sql dump file")

    args = parser.parse_args()

    load_sql_dump(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        db=args.db,
        dump_file=args.file
    )
