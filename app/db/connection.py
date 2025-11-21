import mysql.connector
from app.db.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# ==========================
# DB CONNECTION
# ==========================

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

