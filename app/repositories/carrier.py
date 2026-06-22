from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrier import AdminInviteToken
from app.models.carrier import CarrierCompany
from app.models.carrier import CarrierVehicle


class CarrierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_carrier(self, carrier: CarrierCompany) -> CarrierCompany:
        self.session.add(carrier)
        await self.session.flush()
        return carrier

    async def get_carrier_by_id(self, carrier_id: int) -> CarrierCompany | None:
        stmt = select(CarrierCompany).where(CarrierCompany.id == carrier_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_carrier_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> CarrierCompany | None:
        stmt = select(CarrierCompany).where(
            CarrierCompany.telegram_user_id == telegram_user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_invite_token(
        self,
        invite: AdminInviteToken,
    ) -> AdminInviteToken:
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def get_invite_token(
        self,
        token: str,
    ) -> AdminInviteToken | None:
        stmt = select(AdminInviteToken).where(
            AdminInviteToken.token == token
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_vehicles_by_carrier(
        self,
        carrier_id: int,
    ) -> list[CarrierVehicle]:
        stmt = (
            select(CarrierVehicle)
            .where(CarrierVehicle.carrier_id == carrier_id)
            .order_by(CarrierVehicle.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
