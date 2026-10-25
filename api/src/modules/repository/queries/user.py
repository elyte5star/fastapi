from modules.database.schema.user import (
    User,
    Otp,
    NewLocationToken,
    UserLocation,
    PasswordResetToken,
    Enquiry,
)
from modules.repository.queries.common import CommonQueries
from asyncpg.exceptions import PostgresError
from datetime import datetime
from collections.abc import Sequence


class UserQueries(CommonQueries):
    async def create_user_query(self, user: User) -> User:
        try:
            self.async_session.add(user)
            await self.async_session.commit()
            await self.async_session.refresh(user)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return user

    async def get_users_query(self) -> Sequence[User]:
        stmt = self.select(User).order_by(User.created_at)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def delete_user_query(self, userid: str) -> None:
        try:
            stmt = self.delete(User).where(User.id == userid)
            await self.async_session.execute(stmt)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    # OTP
    async def create_otp_query(self, otp: Otp) -> Otp:
        try:
            self.async_session.add(otp)
            await self.async_session.commit()
            await self.async_session.refresh(otp)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return otp

    async def delete_otp_by_id_query(self, otp_id: str) -> bool:
        stmt = self.delete(Otp).where(Otp.id == otp_id)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return True

    async def get_otp_by_user_query(self, user: User) -> Otp | None:
        stmt = self.select(Otp).where(Otp.owner == user)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def get_otp_by_email_query(self, email: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.email == email)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def get_otp_by_token_query(self, token: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.token == token)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def del_otp_by_expiry_date_less_than(self, now: datetime) -> None:
        stmt = self.delete(Otp).where(Otp.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError:
            await self.async_session.rollback()
            raise

    async def del_all_expired_otps_since(self, now: datetime) -> None:
        stmt = self.delete(Otp).where(Otp.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError:
            await self.async_session.rollback()
            raise

    async def find_all_otps_expiry_less(self, now: datetime) -> Sequence[Otp]:
        stmt = self.select(Otp).where(Otp.expiry <= now)
        result = await self.async_session.execute(stmt)
        otps = result.scalars().all()
        return otps

    async def update_otp_query(self, id: str, data: dict):
        stmt = (
            self.sqlalchemy_update(Otp)
            .where(Otp.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            result = await self.async_session.execute(stmt)
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update otp:", e)
            raise
        else:
            return result.last_updated_params()

    async def find_new_location_by_user_location_query(
        self, user_loc: UserLocation
    ) -> NewLocationToken | None:
        stmt = self.select(NewLocationToken).where(
            NewLocationToken.location == user_loc
        )
        new_locs = await self.async_session.execute(stmt)
        return new_locs.scalars().first()

    async def update_new_loc_query(self, id: str, data: dict) -> None:
        stmt = (
            self.sqlalchemy_update(NewLocationToken)
            .where(NewLocationToken.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError:
            await self.async_session.rollback()
            raise

    # PASSWORD RESET
    async def create_pass_reset_query(self, token: PasswordResetToken) -> str:
        self.async_session.add(token)
        result = ""
        try:
            await self.async_session.commit()
            result = token.id
        except PostgresError:
            await self.async_session.rollback()
            raise
        finally:
            return result

    async def update_pass_token_query(
        self,
        id: str,
        data: dict,
    ):
        stmt = (
            self.sqlalchemy_update(PasswordResetToken)
            .where(PasswordResetToken.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            result = await self.async_session.execute(stmt)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return result.last_updated_params()

    async def find_passw_token_by_token_query(
        self, token: str
    ) -> PasswordResetToken | None:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def find_passw_token_by_user_query(
        self,
        user: User,
    ) -> PasswordResetToken | None:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.owner == user)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def find_all_passw_reset_token_expiry_less(
        self, now: datetime
    ) -> Sequence[PasswordResetToken]:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.expiry <= now)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def del_all_expired_passw_reset_token_since(
        self,
        now: datetime,
    ) -> None:
        stmt = self.delete(PasswordResetToken).where(PasswordResetToken.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError:
            await self.async_session.rollback()
            raise

    async def delete_passw_reset_token_by_id_query(self, id: str) -> bool:
        stmt = self.delete(PasswordResetToken).where(PasswordResetToken.id == id)
        result = False
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
            result = True
        except PostgresError:
            await self.async_session.rollback()
            raise
        finally:
            return result

    async def create_enquiry_query(self, enquiry: Enquiry) -> Enquiry | None:
        try:
            self.async_session.add(enquiry)
            await self.async_session.commit()
            await self.async_session.refresh(enquiry)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return enquiry
