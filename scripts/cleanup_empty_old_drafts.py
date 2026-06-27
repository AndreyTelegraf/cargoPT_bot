import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "cargopt_prod.db"
MAX_AGE_HOURS = 24

SELECT_QUERY = """
WITH draft_state AS (
  SELECT
    j.id,
    j.client_telegram_username,
    j.created_at,
    j.requested_date,
    j.estimated_payload_kg,
    j.estimated_volume_m3,
    j.required_loaders,
    j.client_phone,
    j.client_whatsapp,
    j.comment,
    COUNT(DISTINCT a.id) AS addresses,
    COUNT(DISTINCT i.id) AS items,
    COUNT(DISTINCT m.id) AS media
  FROM job j
  LEFT JOIN job_address a ON a.job_id = j.id
  LEFT JOIN job_item i ON i.job_id = j.id
  LEFT JOIN job_media m ON m.job_id = j.id
  WHERE j.status = 'draft'
    AND j.created_at < datetime('now', ?)
  GROUP BY j.id
)
SELECT id, client_telegram_username, created_at
FROM draft_state
WHERE addresses = 0
  AND items = 0
  AND media = 0
  AND requested_date IS NULL
  AND estimated_payload_kg IS NULL
  AND estimated_volume_m3 IS NULL
  AND required_loaders IS NULL
  AND client_phone IS NULL
  AND client_whatsapp IS NULL
  AND comment IS NULL
ORDER BY id;
"""

DELETE_QUERY = """
DELETE FROM job
WHERE id IN (
  WITH draft_state AS (
    SELECT
      j.id,
      j.requested_date,
      j.estimated_payload_kg,
      j.estimated_volume_m3,
      j.required_loaders,
      j.client_phone,
      j.client_whatsapp,
      j.comment,
      COUNT(DISTINCT a.id) AS addresses,
      COUNT(DISTINCT i.id) AS items,
      COUNT(DISTINCT m.id) AS media
    FROM job j
    LEFT JOIN job_address a ON a.job_id = j.id
    LEFT JOIN job_item i ON i.job_id = j.id
    LEFT JOIN job_media m ON m.job_id = j.id
    WHERE j.status = 'draft'
      AND j.created_at < datetime('now', ?)
    GROUP BY j.id
  )
  SELECT id
  FROM draft_state
  WHERE addresses = 0
    AND items = 0
    AND media = 0
    AND requested_date IS NULL
    AND estimated_payload_kg IS NULL
    AND estimated_volume_m3 IS NULL
    AND required_loaders IS NULL
    AND client_phone IS NULL
    AND client_whatsapp IS NULL
    AND comment IS NULL
);
"""

def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"database not found: {DB_PATH}")

    age_arg = f"-{MAX_AGE_HOURS} hours"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(SELECT_QUERY, (age_arg,)).fetchall()

        print("EMPTY_OLD_DRAFT_CLEANUP")
        print(f"db={DB_PATH}")
        print(f"max_age_hours={MAX_AGE_HOURS}")
        print(f"candidates={len(rows)}")

        for row in rows:
            print(
                "candidate "
                f"job_id={row['id']} "
                f"client={row['client_telegram_username']} "
                f"created_at={row['created_at']}"
            )

        if rows:
            conn.execute(DELETE_QUERY, (age_arg,))
            conn.commit()

    print("EMPTY_OLD_DRAFT_CLEANUP_OK")


if __name__ == "__main__":
    main()
