from pathlib import Path
s = Path("app/services/offer_notifications.py").read_text(encoding="utf-8")
assert "После разговора вернитесь в этот чат и подтвердите, состоялась ли сделка." in s
print("OFFER_NOTIFICATIONS_SMOKE_OK")
