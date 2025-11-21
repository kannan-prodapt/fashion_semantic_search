import mysql.connector
from mysql.connector import Error

from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

NEW_COLORS = [
    "black","white","offwhite","grey","gray",
    "blue","navy","light blue","dark blue",
    "red","maroon","burgundy","pink","hot pink","peach",
    "orange","yellow","mustard",
    "green","olive","teal","turquoise",
    "purple","lavender","brown","tan","beige","cream",
    "gold","silver","multicolor"
]


def alter_enum_add_colors():
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

        # -----------------------------------
        # 1. Read CURRENT ENUM
        # -----------------------------------
        cursor.execute("SHOW COLUMNS FROM product_style_labels LIKE 'label';")
        row = cursor.fetchone()

        if not row:
            print("❌ Column 'label' not found in product_style_labels")
            return

        type_definition = row[1]
        print("\n📌 Current ENUM:", type_definition)
        if isinstance(type_definition, (bytes, bytearray)):
            type_definition = type_definition.decode("utf-8")
        if type_definition.startswith("enum("):
            current_values = type_definition[5:-1]
            current_values = [
                v.strip().strip("'")
                for v in current_values.split(",")
            ]
        else:
            print("❌ Unexpected ENUM format:", type_definition)
            return

        print(f"Found {len(current_values)} existing ENUM entries.")

        # -----------------------------------
        # 2. Merge new values
        # -----------------------------------
        merged_values = list(current_values)

        for color in NEW_COLORS:
            if color not in merged_values:
                merged_values.append(color)

        print(f"Total ENUM size after merging = {len(merged_values)}")

        # -----------------------------------
        # 3. Build ENUM SQL safely (NO f-string escaping)
        # -----------------------------------
        enum_sql = ", ".join("'" + v.replace("'", "\\'") + "'" for v in merged_values)

        alter_sql = f"""
        ALTER TABLE product_style_labels
        MODIFY COLUMN label ENUM({enum_sql}) NOT NULL;
        """

        print("\n🚀 Executing ALTER TABLE...")
        print(alter_sql)

        cursor.execute(alter_sql)
        conn.commit()

        print("\n🎉 ENUM successfully updated. No data dropped.")

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        if "conn" in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    alter_enum_add_colors()
