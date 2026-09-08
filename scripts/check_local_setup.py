import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Ensure app root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.logging import logger


def ensure_postgres_database() -> bool:
    """Ensure that the target PostgreSQL database exists; create if not."""
    try:
        logger.info("Connecting to PostgreSQL server at %s:%s...", settings.POSTGRES_SERVER, settings.POSTGRES_PORT)
        conn = psycopg2.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}';")
        exists = cursor.fetchone()

        if not exists:
            logger.info("Database '%s' does not exist. Creating...", settings.POSTGRES_DB)
            cursor.execute(f"CREATE DATABASE {settings.POSTGRES_DB};")
            logger.info("Database '%s' created successfully!", settings.POSTGRES_DB)
        else:
            logger.info("Database '%s' already exists.", settings.POSTGRES_DB)

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error("Failed to connect or create PostgreSQL database: %s", e)
        return False


def verify_setup() -> None:
    """Verify local directories and database connection."""
    print("=" * 60)
    print("Checking Civic AI Assistant Local Setup")
    print("=" * 60)

    # Check directories
    for dir_path in [settings.VECTOR_STORE_PATH, settings.KNOWLEDGE_BASE_PATH, settings.STORAGE_PATH]:
        p = settings.get_absolute_path(dir_path)
        print(f"[OK] Directory ready: {p}")

    # Check PostgreSQL
    if "postgresql" in settings.DATABASE_URL:
        success = ensure_postgres_database()
        if success:
            print(f"[OK] PostgreSQL connected: {settings.POSTGRES_DB}")
        else:
            print("[FAIL] Could not establish PostgreSQL connection. Please check credentials.")
    else:
        print(f"[OK] Using SQLite: {settings.DATABASE_URL}")

    print("=" * 60)


if __name__ == "__main__":
    verify_setup()
