import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "cargopt_prod.db"

if not DB_PATH.exists():
    raise SystemExit(f"database not found: {DB_PATH}")

QUERY = """
WITH offer_counts AS (
    SELECT
        j.id,
        j.client_telegram_username,
        j.status AS job_status,
        SUM(CASE WHEN o.status = 'accepted' THEN 1 ELSE 0 END) AS accepted,
        SUM(CASE WHEN o.status = 'pending' THEN 1 ELSE 0 END) AS pending,
        SUM(CASE WHEN o.status = 'declined' THEN 1 ELSE 0 END) AS declined,
        SUM(CASE WHEN o.status = 'expired' THEN 1 ELSE 0 END) AS expired,
        SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
        COUNT(o.id) AS total_offers
    FROM job j
    LEFT JOIN job_offer o ON o.job_id = j.id
    GROUP BY j.id
)
SELECT *
FROM offer_counts
WHERE
      accepted > 1
   OR (accepted = 1 AND job_status NOT IN ('assigned','assigned_pending_confirmation'))
   OR (pending > 0 AND job_status NOT IN ('offered','matching'))
   OR (total_offers = 0 AND job_status NOT IN ('draft','ready_for_matching','unmatched','no_carriers_found'))
ORDER BY id;
"""

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(QUERY).fetchall()

print("JOB_CONSISTENCY_AUDIT")
print(f"db={DB_PATH}")
print(f"issues={len(rows)}")

for row in rows:
    print(
        "issue "
        f"job_id={row['id']} "
        f"client={row['client_telegram_username']} "
        f"job_status={row['job_status']} "
        f"accepted={row['accepted']} "
        f"pending={row['pending']} "
        f"declined={row['declined']} "
        f"expired={row['expired']} "
        f"cancelled={row['cancelled']} "
        f"total_offers={row['total_offers']}"
    )

if rows:
    raise SystemExit(1)

print("JOB_CONSISTENCY_AUDIT_OK")
