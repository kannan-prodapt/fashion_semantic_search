#!/usr/bin/env python3

import re
import mysql.connector
from mysql.connector import Error

from app.db.db_config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
)

# (table_name, human_name)
LABEL_TABLES = [
    ("product_vibe_labels", "vibe"),
    ("product_occasion_labels", "occasion"),
    ("product_gender_labels", "gender"),
    ("product_category_labels", "category"),
    ("product_age_labels", "age"),
    ("product_style_labels", "style"),
]

ENUM_COLUMN_NAME = "label"


def get_enum_values(conn, table_name: str, column_name: str):
    """
    Read ENUM values from information_schema for a given table.column.
    Returns a list of strings.
    """
    sql = """
        SELECT COLUMN_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s;
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (DB_NAME, table_name, column_name))
        row = cursor.fetchone()
        if not row:
            print(f"⚠ No column_type found for {table_name}.{column_name}")
            return []

        column_type = row[0]  # e.g. enum('casual','formal',...)

        # Ensure we have a Python string, not bytes
        if isinstance(column_type, (bytes, bytearray)):
            column_type = column_type.decode("utf-8")

        # Expect: enum('val1','val2',...)
        m = re.match(r"^enum\((.*)\)$", column_type, re.IGNORECASE)
        if not m:
            print(f"⚠ Column {table_name}.{column_name} is not ENUM: {column_type}")
            return []

        inner = m.group(1)  # "'casual','formal',..."

        # ✅ ENUM values don't contain commas, so a simple split works
        parts = inner.split(",")
        values = []
        for part in parts:
            part = part.strip()
            if part.startswith("'") and part.endswith("'"):
                part = part[1:-1]      # strip surrounding quotes
            part = part.replace("\\'", "'")  # unescape single quotes
            values.append(part)

        return values
    finally:
        cursor.close()


def count_label_usage(conn, table_name: str, label_value: str) -> int:
    """
    Count how many rows in table_name have label = label_value.
    """
    sql = f"SELECT COUNT(*) FROM {table_name} WHERE {ENUM_COLUMN_NAME} = %s"
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (label_value,))
        (count,) = cursor.fetchone()
        return int(count)
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

        print(f"✅ Connected to MySQL database '{DB_NAME}'")

        for table_name, dim_name in LABEL_TABLES:
            print(f"\n=== Checking {dim_name} labels in table: {table_name} ===")
            enum_values = get_enum_values(conn, table_name, ENUM_COLUMN_NAME)
            if not enum_values:
                print(f"  ⚠ No ENUM values found for {table_name}.{ENUM_COLUMN_NAME}")
                continue

            unused = []
            for value in enum_values:
                cnt = count_label_usage(conn, table_name, value)
                print(f"  {dim_name}='{value}': {cnt} rows")
                if cnt == 0:
                    unused.append(value)

            if unused:
                print(f"\n  👉 UNUSED {dim_name} labels (no rows in {table_name}):")
                for v in unused:
                    print(f"    - {v}")
                print("  Suggestion: remove these from SCHEMA_DESCRIPTION / prompt schema.")
            else:
                print(f"  ✅ All {dim_name} ENUM values are used at least once.")

    except Error as e:
        print(f"❌ MySQL Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("\n🔒 Connection closed.")


if __name__ == "__main__":
    main()
