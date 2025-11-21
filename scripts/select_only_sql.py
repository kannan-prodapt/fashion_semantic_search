#!/usr/bin/env python3

import sys
import mysql.connector
from mysql.connector import Error

from app.db.db_config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
)


def is_safe_select(sql: str) -> bool:
    """
    Ensures ONLY SELECT statements are allowed.
    Blocks DELETE, UPDATE, INSERT, ALTER, DROP, TRUNCATE, etc.
    """

    sql_clean = sql.strip().lower()
    print(sql_clean)
    # Must start with SELECT
    if not sql_clean.startswith("select"):
        return False

    # Forbidden keywords anywhere in the query
    forbidden = [
        "delete", "update", "insert", "alter", "drop",
        "truncate", "create", "replace", "rename",
        "grant", "revoke", "commit", "rollback",
    ]

    return not any(word in sql_clean for word in forbidden)


def run_safe_select(sql: str):
    """Executes ONLY SELECT commands and prints results."""

    if not is_safe_select(sql):
        print("❌ ERROR: Only SELECT queries are allowed.")
        print("Blocked query:", sql)
        return

    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )

        if not conn.is_connected():
            print("❌ Could not connect to database")
            return

        cursor = conn.cursor()

        print(f"\n🔍 Executing SELECT query:\n{sql}\n")

        cursor.execute(sql)
        rows = cursor.fetchall()

        print(f"📊 Returned {cursor.rowcount} rows:\n")
        for row in rows:
            print(row)

    except Error as e:
        print(f"❌ SQL error: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("\n🔒 Connection closed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 select_only_sql.py \"SELECT * FROM products LIMIT 5\"")
        sys.exit(1)

    sql = sys.argv[1]
    run_safe_select(sql)
