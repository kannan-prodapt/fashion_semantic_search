import mysql.connector
from mysql.connector import Error

# ==========================
# DB CONFIG
# ==========================
from db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# ==========================
# SQL STATEMENTS
# ==========================

CREATE_TABLES_SQL = [

    # --------------------------
    # Master products table
    # --------------------------
    """
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

    # --------------------------
    # Label tables
    # --------------------------
    """
    CREATE TABLE IF NOT EXISTS product_vibe_labels (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        product_id BIGINT UNSIGNED NOT NULL,
        label VARCHAR(100) NOT NULL,
        confidence DECIMAL(4,3) NULL,

        PRIMARY KEY (id),
        KEY idx_product (product_id),
        CONSTRAINT fk_vibe_product
            FOREIGN KEY (product_id) REFERENCES products(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    """
    CREATE TABLE IF NOT EXISTS product_occasion_labels (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        product_id BIGINT UNSIGNED NOT NULL,
        label VARCHAR(100) NOT NULL,
        confidence DECIMAL(4,3) NULL,

        PRIMARY KEY (id),
        KEY idx_product (product_id),
        CONSTRAINT fk_occasion_product
            FOREIGN KEY (product_id) REFERENCES products(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    """
    CREATE TABLE IF NOT EXISTS product_gender_labels (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        product_id BIGINT UNSIGNED NOT NULL,
        label VARCHAR(50) NOT NULL,
        confidence DECIMAL(4,3) NULL,

        PRIMARY KEY (id),
        KEY idx_product (product_id),
        CONSTRAINT fk_gender_product
            FOREIGN KEY (product_id) REFERENCES products(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    """
    CREATE TABLE IF NOT EXISTS product_category_labels (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        product_id BIGINT UNSIGNED NOT NULL,
        label VARCHAR(100) NOT NULL,
        confidence DECIMAL(4,3) NULL,

        PRIMARY KEY (id),
        KEY idx_product (product_id),
        CONSTRAINT fk_category_product
            FOREIGN KEY (product_id) REFERENCES products(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    """
    CREATE TABLE IF NOT EXISTS product_age_labels (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        product_id BIGINT UNSIGNED NOT NULL,
        label VARCHAR(100) NOT NULL,
        confidence DECIMAL(4,3) NULL,

        PRIMARY KEY (id),
        KEY idx_product (product_id),
        CONSTRAINT fk_age_product
            FOREIGN KEY (product_id) REFERENCES products(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    """
    CREATE TABLE IF NOT EXISTS product_style_labels (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        product_id BIGINT UNSIGNED NOT NULL,
        label VARCHAR(100) NOT NULL,
        confidence DECIMAL(4,3) NULL,

        PRIMARY KEY (id),
        KEY idx_product (product_id),
        CONSTRAINT fk_style_product
            FOREIGN KEY (product_id) REFERENCES products(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # --------------------------
    # Media tables
    # --------------------------
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
# CREATION LOGIC
# ==========================

def create_tables():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )

        if conn.is_connected():
            print("✅ Connected to MySQL")
            cursor = conn.cursor()

            for i, sql in enumerate(CREATE_TABLES_SQL, start=1):
                print(f"\n--- Creating table {i} ---")
                cursor.execute(sql)
                print("Done.")

            conn.commit()
            cursor.close()
            print("\n🎉 All tables created (or already existed).")

    except Error as e:
        print(f"❌ Error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔒 Connection closed.")


if __name__ == "__main__":
    create_tables()

