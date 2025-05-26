import logging
import sqlite3

DATABASE_URL = "sqlite:///./mcp_registry.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DATABASE_URL.split("///")[1])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y crea la tabla 'mcps' si no existe."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                capabilities TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("Base de datos inicializada y tabla 'mcps' creada (si no existía).")

if __name__ == "__main__":
    init_db()
    logger.info("Script de inicialización de base de datos ejecutado.")
