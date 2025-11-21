import mysql.connector
from mysql.connector import Error

# Reuse your existing DB config (same as update_categories_from_title.py)
from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


# IMPORTANT:
# This must be kept in sync with STYLE_ENUM in reset_schema_with_enums.py
STYLE_ENUM = (
    # Fits
    "slimfit",
    "regularfit",
    "relaxedfit",
    "tailored",
    "bodyfit",

    # Patterns
    "solid",
    "striped",
    "checked",
    "printed",
    "floral",
    "animal print",
    "tie-dye",
    "polka",

    # Dress silhouettes
    "aline",
    "fitflare",
    "wrap",
    "straightcut",
    "sheath",
    "maxi",
    "midi",

    # Bottom rise
    "highrise",
    "midrise",
    "lowrise",

    # Knit styles
    "cableknit",
    "chunkyknit",
    "ribbed",
    "waffleknit",
    "lightknit",

    # Sleeve styles
    "puff sleeve",
    "bell sleeve",
    "cap sleeve",
    "sleeveless",

    # Neck styles
    "roundneck",
    "vneck",
    "turtleneck",
    "collared",
    "halter",
    "boat",
    "sweetheart",

    # Materials
    "cotton",
    "polyester",
    "denim",
    "linen",
    "silk",
    "wool",
    "fleece",
    "nylon",
    "leather",
    "acrylic",
    "chiffon",
    "georgette",
    "satin",
    "tweed",

    # Closure styles
    "button",
    "zipper",
    "pullon",
    "open",
    "tie",
    "velcro",

    # Hem types
    "highlow",
    "frilled",
    "slit",

    # Footwear styles
    "flat",
    "block heel",
    "stiletto",
    "wedge",
    "round toe",
    "pointed toe",
    "square toe",

    # Features
    "stretch",
    "breathable",
    "quickdry",
    "waterresistant",
    "uvprotection",
    "insulated",
    "reflective",

    # Embellishments
    "embroidered",
    "sequins",
    "beaded",
    "mirrorwork",

    # Sustainability
    "organic",
    "recycled",

    # Colors
    "black",
    "white",
    "offwhite",
    "grey",
    "gray",
    "blue",
    "navy",
    "light blue",
    "dark blue",
    "red",
    "maroon",
    "burgundy",
    "pink",
    "hot pink",
    "peach",
    "orange",
    "yellow",
    "mustard",
    "green",
    "olive",
    "teal",
    "turquoise",
    "purple",
    "lavender",
    "brown",
    "tan",
    "beige",
    "cream",
    "gold",
    "silver",
    "multicolor",
)


def populate_styles_from_titles(default_confidence: float = 1.0):
    """
    For every style in STYLE_ENUM, look for it in products.title (case-insensitive).
    If found, insert into product_style_labels (product_id, label, confidence)
    when such a row does not already exist.
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

        for style in STYLE_ENUM:
            keyword = style.lower()
            print("\n========================================")
            print(f"🔍 Processing style '{style}' (keyword: '{keyword}')")

            # Count matching products
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM products p
                WHERE LOWER(p.title) LIKE %s
                """,
                (f"%{keyword}%",),
            )
            (cnt,) = cursor.fetchone()
            print(f"Found {cnt} products with '{keyword}' in title.")

            if cnt == 0:
                continue

            # Insert missing labels
            print(f"✏️ Inserting style '{style}' for matching products (if missing)...")
            insert_sql = """
                INSERT INTO product_style_labels (product_id, label, confidence)
                SELECT 
                    p.id,
                    %s AS label,
                    %s AS confidence
                FROM products p
                LEFT JOIN product_style_labels psl
                       ON psl.product_id = p.id
                      AND psl.label = %s
                WHERE LOWER(p.title) LIKE %s
                  AND psl.id IS NULL;
            """

            params = (
                style,
                float(default_confidence) if default_confidence is not None else None,
                style,
                f"%{keyword}%",
            )

            cursor.execute(insert_sql, params)
            affected = cursor.rowcount
            conn.commit()

            print(f"🎉 Inserted {affected} new rows for style '{style}'.")

        cursor.close()

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    # You can tweak default_confidence (or change to None to store NULL)
    populate_styles_from_titles(default_confidence=1.0)
