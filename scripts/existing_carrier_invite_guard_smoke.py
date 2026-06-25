from pathlib import Path

source = Path("app/bot/handlers/invite.py").read_text()

assert "existing_carrier = await repository.get_carrier_by_telegram_user_id" in source
assert "Вы уже зарегистрированы как перевозчик CargoPT" in source
assert "service.claim_invite_token" in source

print("EXISTING_CARRIER_INVITE_GUARD_SMOKE_OK")
