from datetime import UTC
from datetime import datetime
from datetime import timedelta
from secrets import token_urlsafe

from app.models.carrier import AdminInviteToken
from app.models.carrier import CarrierCompany
from app.repositories.carrier import CarrierRepository


class CarrierOnboardingService:
    def __init__(self, repository: CarrierRepository) -> None:
        self.repository = repository

    async def create_draft_carrier(
        self,
        *,
        company_name: str,
        contact_name: str | None = None,
        phone: str | None = None,
        paid_until: datetime | None = None,
        internal_note: str | None = None,
    ) -> CarrierCompany:
        now = datetime.now(UTC)

        carrier = CarrierCompany(
            company_name=company_name,
            contact_name=contact_name,
            phone=phone,
            telegram_user_id=None,
            status="draft",
            paid_until=paid_until,
            internal_note=internal_note,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create_carrier(carrier)

    async def create_invite_token(
        self,
        *,
        carrier_id: int,
        created_by_admin_id: int,
        expires_in_days: int = 7,
    ) -> AdminInviteToken:
        now = datetime.now(UTC)

        invite = AdminInviteToken(
            token=token_urlsafe(32),
            carrier_id=carrier_id,
            created_by_admin_id=created_by_admin_id,
            expires_at=now + timedelta(days=expires_in_days),
            used_at=None,
            used_by_telegram_id=None,
            status="active",
            created_at=now,
        )

        await self.repository.create_invite_token(invite)
        await self.repository.update_carrier_status(
            carrier_id=carrier_id,
            status="invited",
        )

        return invite

    async def validate_invite_token(
        self,
        token: str,
        now=None,
    ):
        invite = await self.repository.get_invite_token(token)

        if invite is None:
            raise ValueError("invite not found")

        if invite.status != "active":
            raise ValueError("invite inactive")

        from datetime import UTC
        from datetime import datetime

        current = now or datetime.now(UTC)

        if invite.expires_at <= current:
            raise ValueError("invite expired")

        if invite.used_at is not None:
            raise ValueError("invite already used")

        return invite

    async def get_invite_token(
        self,
        token: str,
    ) -> AdminInviteToken | None:
        return await self.repository.get_invite_token(token)

    async def claim_invite_token(
        self,
        token: str,
        telegram_user_id: int,
    ) -> AdminInviteToken:
        invite = await self.validate_invite_token(token)

        now = datetime.now(UTC)

        return await self.repository.claim_invite(
            token=invite.token,
            telegram_user_id=telegram_user_id,
            used_at=now,
        )

    async def complete_profile(
        self,
        carrier_id: int,
        assembly_required: bool,
        packing_required: bool,
        operating_regions: str,
    ):
        return await self.repository.complete_profile(
            carrier_id=carrier_id,
            assembly_required=assembly_required,
            packing_required=packing_required,
            operating_regions=operating_regions,
            completed_at=datetime.now(UTC),
        )
