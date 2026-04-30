import os
from contextlib import contextmanager

import psycopg2


@contextmanager
def get_connection():
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
