from modules.database.connection import AsyncDatabaseSession, Job, TaskResult, Task
from modules.utils.misc import get_indent, date_time_now_utc
from itsdangerous import (
    URLSafeTimedSerializer,
    BadTimeSignature,
    SignatureExpired,
)
import geoip2.errors
import geoip2.database
from fastapi import Request
from modules.database.schema.user import User, UserLocation
from modules.database.schema.product import Product
from sqlalchemy import __version__, inspect
from multiprocessing import cpu_count
from asyncpg.exceptions import PostgresError
from collections.abc import Sequence
import bcrypt
from pydantic import AnyHttpUrl


class CommonQueries(AsyncDatabaseSession):

    async def add_job_to_db_query(self, job: Job) -> Job:
        try:
            self.async_session.add(job)
            await self.async_session.commit()
            await self.async_session.refresh(job)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return job

    async def add_task_result_db_query(self, result: TaskResult) -> TaskResult:
        try:
            self.async_session.add(result)
            await self.async_session.commit()
            await self.async_session.refresh(result)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return result

    async def add_task_to_db_query(self, task: Task) -> Task:
        try:
            self.async_session.add(task)
            await self.async_session.commit()
            await self.async_session.refresh(task)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return task

    async def find_job_by_id(self, job_id: str) -> Job | None:
        return await self.async_session.get(Job, job_id)

    async def find_tasks_by_job_id(self, job_id: str) -> Sequence[Task]:
        stmt = self.select(Task).where(Task.job_id == job_id)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def find_result_by_task_id(self, task_id: str) -> TaskResult | None:
        stmt = self.select(TaskResult).where(TaskResult.task_id == task_id)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def get_jobs_query(self) -> Sequence[Job]:
        stmt = self.select(Job).order_by(Job.created_at)
        result = await self.async_session.execute(stmt)
        jobs = result.scalars().all()
        return jobs

    async def delete_job_by_id_query(self, job_id: str) -> None:
        try:
            stmt = self.delete(Job).where(Job.id == job_id)
            await self.async_session.execute(stmt)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    def get_new_id(self) -> str:
        return get_indent()

    async def find_product_by_id(self, pid: str) -> Product | None:
        return await self.async_session.get(Product, pid)

    async def find_user_by_id(self, userid: str) -> User | None:
        return await self.async_session.get(User, userid)

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = self.select(User).where(User.username == username)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def find_user_by_email(self, email: str) -> User | None:
        stmt = self.select(User).where(User.email == email)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    def create_timed_token(self, email: str) -> str:
        serializer = URLSafeTimedSerializer(
            self.cf.secret_key, salt=str(self.cf.rounds)
        )
        return serializer.dumps(email)

    def get_client_ip_address(self, request: Request) -> str:
        xf_header = request.headers.get("X-Forwarded-For")
        if xf_header is not None:
            return xf_header.split(",")[0]
        # return "128.101.101.101"  # for testing Richfield,United States
        # return "41.238.0.198"  # for testing Giza, Egypt
        return request.client.host if request.client else ""

    async def get_location_from_ip(self, ip: str) -> tuple:
        location = ("UNKNOWN", "UNKNOWN")
        try:
            with geoip2.database.Reader(
                "./modules/static/maxmind/GeoLite2-City.mmdb"
            ) as reader:
                response = reader.city(ip)
                return (response.country.name, response.city.name)
        except geoip2.errors.AddressNotFoundError as e:
            self.logger.error(e)
            return location

    async def async_inspect_schema(self):
        async with self._engine.connect() as conn:
            tables = await conn.run_sync(self.use_inspector)
        # self.logger.info(tables)
        return tables

    def use_inspector(self, conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async def lock_user_account_query(self, user: User) -> None:
        changes = dict(
            lock_time=date_time_now_utc(),
            is_locked=True,
            modified_at=date_time_now_utc(),
            modified_by=user.id,
        )
        await self.update_user_info(user.id, changes)
        self.logger.warning(f"User with id: {user.id} is locked")

    def verify_email_token(self, token: str, expiration: int = 3600) -> bool:
        serializer = URLSafeTimedSerializer(self.cf.secret_key)
        try:
            _ = serializer.loads(
                token,
                salt=str(self.cf.rounds),
                max_age=expiration,
            )
            return True
        except SignatureExpired:
            return False
        except BadTimeSignature:
            return False

    async def system_info(self) -> dict:
        async with self.async_session as _:
            _, kwargs = self._engine.dialect.create_connect_args(
                self._engine.url,
            )
        return {
            "databaseParameters": kwargs,
            "sqlalchemyVersion": __version__,
            "databaseTables": await self.async_inspect_schema(),
            "rabbitMQDns": self.cf.amqp_url,
            "cpuCount": cpu_count(),
            "apiVersion": self.cf.version,
        }

    async def check_if_user_exist(
        self, email: str, username: str, telephone: str
    ) -> User | None:
        stmt = (
            self.select(User.email, User.username)
            .where(
                self.or_(
                    User.email == email,
                    User.username == username,
                    User.telephone == telephone,
                )
            )
            .limit(1)
        )
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    def hash_password(self, plain_password: str) -> str:
        hashed_password = bcrypt.hashpw(
            plain_password.encode(self.cf.encoding),
            bcrypt.gensalt(rounds=self.cf.rounds),
        ).decode(self.cf.encoding)
        return hashed_password

    async def create_admin_account(self) -> None:
        admin_username = self.cf.contacts["username"]
        admin_email = self.cf.contacts["email"]
        tel = self.cf.contacts["telephone"]
        user_exist = await self.check_if_user_exist(
            admin_email,
            admin_username,
            tel,
        )
        if user_exist is None:
            password = self.cf.contacts["password"]
            admin_user = User(
                **dict(
                    id=get_indent(),
                    email=admin_email,
                    username=admin_username,
                    password=password,
                    active=True,
                    is_using_mfa=True,
                    telephone=tel,
                    admin=True,
                    enabled=True,
                    created_by=self.cf.contacts["username"],
                )
            )
            try:
                self.async_session.add(admin_user)
                await self.async_session.commit()
                self.logger.info(f"Admin account::{admin_user.id} created")
                await self.admin_location(admin_user)
            except PostgresError:
                await self.async_session.rollback()
                raise
        else:
            self.logger.info(f"Admin account::{admin_username} exist already")

    async def admin_location(self, user: User):
        user_loc = UserLocation(
            **dict(
                id=get_indent(),
                country="UNKNOWN",
                owner=user,
                enabled=True,
            )
        )
        await self.create_user_location_query(user_loc)

    async def update_user_info(self, user_id: str, changes: dict):
        try:
            user = await self.async_session.get(User, user_id)
            for key, value in changes.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update user:", e)
            raise

    async def update_product_info_query(self, pid: str, changes: dict):
        try:
            user = await self.async_session.get(Product, pid)
            for key, value in changes.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update user:", e)
            raise

    def get_app_url(self, request: Request) -> str | AnyHttpUrl:
        client_url = self.get_client_url()
        if client_url is None:
            heading_dict = dict(request.scope["headers"])
            origin_url = heading_dict.get(b"referer", b"").decode()
            return origin_url
        return client_url

    def get_client_url(self) -> str | AnyHttpUrl | None:
        client_urls = self.cf.origins
        return next(iter(client_urls)) if client_urls else None

    def is_geo_ip_enabled(self) -> bool:
        return self.cf.is_geo_ip_enabled

    async def create_user_location_query(
        self, user_loc: UserLocation
    ) -> UserLocation | None:
        try:
            self.async_session.add(user_loc)
            await self.async_session.commit()
            await self.async_session.refresh(user_loc)
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create user location: ", e)
            raise
        else:
            return user_loc
