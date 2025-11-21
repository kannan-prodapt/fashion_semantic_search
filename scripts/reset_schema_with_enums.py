import mysql.connector
from mysql.connector import Error

# ==========================
# DB CONFIG
# ==========================

from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


# ==========================
# ENUM DEFINITIONS
# (must match your fashion_map keys)
# ==========================

VIBE_ENUM = (
    "casual",
    "smart casual",
    "street",
    "sporty",
    "ethnic",
    "formal",
    "luxury",
    "boho",
    "vintage",
    "minimal",
    "korean",
    "grunge",
    "preppy",
)

OCCASION_ENUM = (
    "casual",
    "office",
    "party",
    "festive",
    "wedding",
    "gym",
    "travel",
    "loungewear",
    "summer",
    "winter",
    "beach",
)

GENDER_ENUM = (
    "men",
    "women",
    "unisex",
    "kids",
)

CATEGORY_ENUM = (
    "tshirt",
    "shirt",
    "top",
    "kurta",
    "dress",
    "jumpsuit",
    "sweater",
    "cardigan",
    "hoodie",
    "sweatshirt",
    "winterwear",
    "jeans",
    "trousers",
    "trackpants",
    "shorts",
    "skirts",
    "leggings",
    "jackets",
    "shoes",
    "sandals",
    "heels",
    "boots",
    "ethnicset",
    "saree",
    "lehenga",
    "innerwear",
    "sleepwear",
    "sportswear",
    "swimwear",
    "bags",
    "accessories",
)

AGE_ENUM = (
    "infant",
    "toddler",
    "kids",
    "teens",
    "adults",
    "plus size",
)

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
)


def enum_sql(values):
    """
    Turn a Python iterable of strings into a MySQL ENUM(...) definition.
    Handles quotes properly.
    """
    escaped = [v.replace("'", "\\'") for v in values]
    inner = ", ".join(f"'{v}'" for v in escaped)
    return f"ENUM({inner})"


# ==========================
# DDL STATEMENTS
# ==========================

def get_drop_statements():
    # Drop child tables first (due to FKs), then products
    return [
        "DROP TABLE IF EXISTS product_bought_together;",
        "DROP TABLE IF EXISTS product_videos;",
        "DROP TABLE IF EXISTS product_images;",
        "DROP TABLE IF EXISTS product_style_labels;",
        "DROP TABLE IF EXISTS product_age_labels;",
        "DROP TABLE IF EXISTS product_category_labels;",
        "DROP TABLE IF EXISTS product_gender_labels;",
        "DROP TABLE IF EXISTS product_occasion_labels;",
        "DROP TABLE IF EXISTS product_vibe_labels;",
        "DROP TABLE IF EXISTS products;",
    ]


def get_create_statements():
    vibe_enum_sql = enum_sql(VIBE_ENUM)
    occasion_enum_sql = enum_sql(OCCASION_ENUM)
    gender_enum_sql = enum_sql(GENDER_ENUM)
    category_enum_sql = enum_sql(CATEGORY_ENUM)
    age_enum_sql = enum_sql(AGE_ENUM)
    style_enum_sql = enum_sql(STYLE_ENUM)

    return [

        # Master products table
        f"""
        CREATE TABLE IF NOT EXISTS products (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

            main_category   VARCHAR(100)      NOT NULL,
            title           VARCHAR(500)      NOT NULL,
            average_rating  DECIMAL(3,2)      NULL,
            rating_number   INT UNSIGNED      NULL,
            price           DECIMAL(10,2)     NULL,
            store           VARCHAR(255)      NULL,
            parent_asin     VARCHAR(32)       NOT NULL,

            created_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP
                                              ON UPDATE CURRENT_TIMESTAMP,

            PRIMARY KEY (id),
            UNIQUE KEY uq_parent_asin (parent_asin),
            KEY idx_main_category (main_category),
            KEY idx_store (store)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Vibe labels
        f"""
        CREATE TABLE IF NOT EXISTS product_vibe_labels (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            label {vibe_enum_sql} NOT NULL,
            confidence DECIMAL(4,3) NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_vibe_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Occasion labels
        f"""
        CREATE TABLE IF NOT EXISTS product_occasion_labels (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            label {occasion_enum_sql} NOT NULL,
            confidence DECIMAL(4,3) NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_occasion_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Gender labels
        f"""
        CREATE TABLE IF NOT EXISTS product_gender_labels (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            label {gender_enum_sql} NOT NULL,
            confidence DECIMAL(4,3) NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_gender_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Category labels
        f"""
        CREATE TABLE IF NOT EXISTS product_category_labels (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            label {category_enum_sql} NOT NULL,
            confidence DECIMAL(4,3) NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_category_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Age labels
        f"""
        CREATE TABLE IF NOT EXISTS product_age_labels (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            label {age_enum_sql} NOT NULL,
            confidence DECIMAL(4,3) NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_age_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Style labels
        f"""
        CREATE TABLE IF NOT EXISTS product_style_labels (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            label {style_enum_sql} NOT NULL,
            confidence DECIMAL(4,3) NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_style_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Images
        """
        CREATE TABLE IF NOT EXISTS product_images (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            thumb_url  TEXT NULL,
            large_url  TEXT NULL,
            variant    VARCHAR(50) NULL,
            hi_res_url TEXT NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_images_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Videos
        """
        CREATE TABLE IF NOT EXISTS product_videos (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id BIGINT UNSIGNED NOT NULL,
            video_url  TEXT NULL,
            variant    VARCHAR(50) NULL,
            thumb_url  TEXT NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            CONSTRAINT fk_videos_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        # Bought together
        """
        CREATE TABLE IF NOT EXISTS product_bought_together (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            product_id   BIGINT UNSIGNED NOT NULL,
            related_asin VARCHAR(32) NOT NULL,

            PRIMARY KEY (id),
            KEY idx_product (product_id),
            KEY idx_related_asin (related_asin),
            CONSTRAINT fk_bt_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    ]


# ==========================
# RESET LOGIC
# ==========================

def reset_schema():
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

        print("\nDropping existing tables (if any)...")
        for stmt in get_drop_statements():
            print(stmt)
            cursor.execute(stmt)
        conn.commit()
        print("✅ Dropped all target tables.\n")

        print("Creating tables with ENUM-based schemas...")
        for stmt in get_create_statements():
            cursor.execute(stmt)
        conn.commit()
        print("🎉 All tables created successfully with ENUM columns.\n")

        cursor.close()

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    reset_schema()

