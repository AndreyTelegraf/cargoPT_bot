import asyncio
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import sqlite3
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class FakeBot:
    def __init__(self) -> None:
        self.messages = []

    async def send_message(self, *, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))
        raise AssertionError("idempotent intake must not call Telegram directly")


def request_payload() -> dict:
    return {
        "source_locale": "en",
        "customer_name": "Idempotency Client",
        "customer_email": "idempotency@example.test",
        "preferred_contact": "email",
        "requested_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "addresses": [
            {
                "kind": "pickup",
                "raw_text": "Lisboa",
                "normalized_address": "Lisboa, Portugal",
                "latitude": 38.7077507,
                "longitude": -9.1365919,
                "location_confirmed": True,
                "country_code": "pt",
            },
            {
                "kind": "dropoff",
                "raw_text": "Porto",
                "normalized_address": "Porto, Portugal",
                "latitude": 41.1494512,
                "longitude": -8.6107884,
                "location_confirmed": True,
                "country_code": "pt",
            },
        ],
        "items": [{"description": "10 boxes", "quantity": 10}],
        "comment": "same form submission",
    }


async def exercise(app, app_engine, fake_bot, database: Path) -> None:
    from httpx import ASGITransport, AsyncClient

    url = "/api/v1/requests"
    headers = {"Idempotency-Key": "web-submit-20260910-same"}
    payload = request_payload()
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        first, second = await asyncio.gather(
            client.post(url, json=payload, headers=headers),
            client.post(url, json=payload, headers=headers),
        )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["job_id"] == second.json()["job_id"]
    assert first.json()["tracking_token"] == second.json()["tracking_token"]

    await app_engine.dispose()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as restarted_client:
        replay = await restarted_client.post(
            url,
            json=payload,
            headers=headers,
        )
        assert replay.status_code == 200, replay.text
        assert replay.json()["job_id"] == first.json()["job_id"]

        changed = dict(payload)
        changed["comment"] = "changed payload"
        conflict = await restarted_client.post(
            url,
            json=changed,
            headers=headers,
        )
        assert conflict.status_code == 409, conflict.text

        new_request = await restarted_client.post(
            url,
            json=payload,
            headers={"Idempotency-Key": "web-submit-20260910-new-request"},
        )
        assert new_request.status_code == 200, new_request.text
        assert new_request.json()["job_id"] != first.json()["job_id"]

    await app_engine.dispose()

    connection = sqlite3.connect(database)
    try:
        job_count, keyed_count, unique_key_count = connection.execute(
            """
            SELECT
                count(*),
                sum(web_idempotency_key IS NOT NULL),
                count(DISTINCT web_idempotency_key)
            FROM job
            """
        ).fetchone()
        (
            notification_count,
            unique_notification_count,
            pending_count,
            notified_job_count,
        ) = connection.execute(
            """
            SELECT
                count(*),
                count(DISTINCT dedupe_key),
                sum(delivery_status = 'pending'),
                count(DISTINCT job_id)
            FROM telegram_notification_outbox
            """
        ).fetchone()
    finally:
        connection.close()

    assert (job_count, keyed_count, unique_key_count) == (2, 2, 2)
    assert (notification_count, unique_notification_count) == (2, 2)
    assert (pending_count, notified_job_count) == (2, 2)
    assert not fake_bot.messages


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="cargopt-web-request-idempotency-"
    ) as temporary:
        database = Path(temporary) / "idempotency.db"
        os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{database}"
        os.environ["ENVIRONMENT"] = "web-request-idempotency-smoke"

        import app.models  # noqa: F401
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.api.main import app
        from app.api.web_requests import get_api_bot
        from app.db.base import Base
        from app.db.session import engine as app_engine

        async def create_schema() -> None:
            engine = create_async_engine(os.environ["DATABASE_URL"])
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            await engine.dispose()

        asyncio.run(create_schema())

        fake_bot = FakeBot()

        async def override_bot():
            yield fake_bot

        app.dependency_overrides[get_api_bot] = override_bot
        try:
            asyncio.run(exercise(app, app_engine, fake_bot, database))
        finally:
            app.dependency_overrides.clear()

    print("WEB_REQUEST_IDEMPOTENCY_SMOKE_OK")


if __name__ == "__main__":
    main()
