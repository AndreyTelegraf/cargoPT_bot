from pathlib import Path

source = Path("app/bot/handlers/admin_controls.py").read_text(encoding="utf-8")

assert 'Command("pay_carrier")' in source
assert "async def pay_carrier(" in source
assert "paid_until = base + timedelta(days=days)" in source
assert "base = now" in source
assert "Количество дней должно быть больше нуля." in source
assert "Формат: /pay_carrier <carrier_id|@username> <days> [note]" in source

print("ADMIN_CARRIER_PAYMENT_SMOKE_OK")
