import asyncio
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cargopt-fk-smoke-") as temporary:
        database = Path(temporary) / "foreign-keys.db"
        os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{database}"

        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError
        from app.db.session import engine

        async with engine.begin() as connection:
            enabled = (
                await connection.execute(text("PRAGMA foreign_keys"))
            ).scalar_one()
            assert enabled == 1
            await connection.execute(
                text("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
            )
            await connection.execute(
                text(
                    "CREATE TABLE child ("
                    "id INTEGER PRIMARY KEY, "
                    "parent_id INTEGER NOT NULL REFERENCES parent(id)"
                    ")"
                )
            )

        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text("INSERT INTO child (id, parent_id) VALUES (1, 999)")
                )
        except IntegrityError:
            pass
        else:
            raise AssertionError("invalid foreign key reference was accepted")

        await engine.dispose()

        with sqlite3.connect(database) as connection:
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            child_count = connection.execute(
                "SELECT count(*) FROM child"
            ).fetchone()[0]
            assert child_count == 0

    print("SQLITE_FOREIGN_KEYS_SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
