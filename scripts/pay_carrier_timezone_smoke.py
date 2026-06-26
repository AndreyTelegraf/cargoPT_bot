from datetime import UTC
from datetime import datetime
from datetime import timedelta

now = datetime.now(UTC)

for base in (None, (now + timedelta(days=1)).replace(tzinfo=None), now + timedelta(days=1)):
    if base is not None and base.tzinfo is None:
        base = base.replace(tzinfo=UTC)

    if base is None or base < now:
        base = now

    assert base.tzinfo is not None

print("PAY_CARRIER_TIMEZONE_SMOKE_OK")
