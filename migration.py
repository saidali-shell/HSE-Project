# apply_training_migration.py
import os
import re
import sys
import psycopg2
from urllib.parse import urlparse

# ----------------------------------------------------------------------
# 1️⃣ Load the DATABASE_URL from .env (fallback to env var if already set)
# ----------------------------------------------------------------------
env_path = os.path.abspath(os.path.join("backend", ".env"))
db_url = None
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("DATABASE_URL"):
                db_url = line.strip().split("=", 1)[1]
                break
if not db_url:
    db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ Could not find DATABASE_URL. Check .env or set the env var.")
    sys.exit(1)

# ----------------------------------------------------------------------
# 2️⃣ Parse the URL into connection components
# ----------------------------------------------------------------------
parsed = urlparse(db_url)
user = parsed.username
password = parsed.password
host = parsed.hostname or "localhost"
port = parsed.port or 5432
dbname = parsed.path.lstrip("/")

# ----------------------------------------------------------------------
# 3️⃣ Connect and run the three ALTER statements
# ----------------------------------------------------------------------
sql_statements = [
    """
    ALTER TABLE trainings
    DROP CONSTRAINT IF EXISTS trainings_status_check;
    """,
    """
    ALTER TABLE trainings
    ALTER COLUMN status SET DEFAULT 'Incomplete';
    """,
    """
    ALTER TABLE trainings
    ADD CONSTRAINT trainings_status_check
        CHECK (status IN ('Completed','Incomplete'));
    """
]

try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )
    conn.autocommit = True
    cur = conn.cursor()
    for stmt in sql_statements:
        cur.execute(stmt)
        print("✅ Executed:", re.sub(r"\s+", " ", stmt).strip()[:80] + "…")
    cur.close()
    conn.close()
    print("\n🎉 Migration finished successfully.")
except Exception as e:
    print("❌ Migration failed:", e)
    sys.exit(1)
