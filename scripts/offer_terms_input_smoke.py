import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_offer_response import _parse_offer_price_input
from app.repositories.job import JobRepository


def verify_parser() -> None:
    parsed = _parse_offer_price_input(
        "120,50\nLoading and unloading\nTolls if applicable\n"
        "12 Sep, 14:00-16:00\nfinal\nCall before arrival"
    )
    assert parsed.price_cents == 12050
    assert parsed.included_services == "Loading and unloading"
    assert parsed.possible_surcharges == "Tolls if applicable"
    assert parsed.service_window == "12 Sep, 14:00-16:00"
    assert parsed.estimate_status == "final"
    assert parsed.carrier_note == "Call before arrival"

    assert _parse_offer_price_input(
        "90\nCarga e descarga\nnenhum\n13/09 manhã\nestimativa"
    ).estimate_status == "estimate"
    assert _parse_offer_price_input(
        "75\nПогрузка\nнет\n14.09 вечером\nпредварительная"
    ).estimate_status == "estimate"

    for invalid in (
        "120",
        "120\nIncluded\nNone\nTomorrow",
        "120\nIncluded\nNone\nTomorrow\nunknown",
        "0\nIncluded\nNone\nTomorrow\nfinal",
    ):
        try:
            _parse_offer_price_input(invalid)
        except ValueError:
            continue
        raise AssertionError(f"invalid offer input accepted: {invalid!r}")


async def verify_repository_storage() -> None:
    offer = SimpleNamespace()
    session = SimpleNamespace(flush=AsyncMock())
    repository = JobRepository(session)
    repository.get_offer_by_id = AsyncMock(return_value=offer)
    now = datetime.now(UTC)

    result = await repository.update_offer_terms(
        offer_id=7,
        price_cents=12050,
        included_services="Loading and unloading",
        possible_surcharges="Tolls if applicable",
        service_window="12 Sep, 14:00-16:00",
        estimate_status="final",
        carrier_note="Call before arrival",
        updated_at=now,
    )

    assert result is offer
    assert offer.price_cents == 12050
    assert offer.included_services == "Loading and unloading"
    assert offer.possible_surcharges == "Tolls if applicable"
    assert offer.service_window == "12 Sep, 14:00-16:00"
    assert offer.estimate_status == "final"
    assert offer.carrier_note == "Call before arrival"
    assert offer.updated_at == now
    session.flush.assert_awaited_once()


verify_parser()
asyncio.run(verify_repository_storage())
print("OFFER_TERMS_INPUT_SMOKE_OK")
