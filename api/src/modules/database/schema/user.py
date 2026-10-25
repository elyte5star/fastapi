from sqlalchemy import ForeignKey, PickleType, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from modules.database.schema.base import (
    Audit,
    Base,
    str_pk_60,
    required_30,
    required_100,
    required_60,
    required_600,
    timestamp,
    bool_col,
    PydanticColumn,
    JSONEncodedDict,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList

from sqlalchemy.ext.hybrid import hybrid_property
from modules.queue.models import ShippingAddress
from datetime import datetime
from typing import List, Set


class User(Audit):
    # add ForeignKey to mapped_column(String, primary_key=True)
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    email: Mapped[required_30]
    username: Mapped[required_30]
    password: Mapped[required_600]
    active: Mapped[bool_col]
    enabled: Mapped[bool_col]
    admin: Mapped[bool_col]
    telephone: Mapped[required_30]
    failed_attempts: Mapped[int] = mapped_column(default=0)
    discount: Mapped[float] = mapped_column(default=0.0)
    lock_time: Mapped[datetime | None] = mapped_column(
        default=None,
        nullable=True,
    )
    is_using_mfa: Mapped[bool_col]
    is_locked: Mapped[bool_col]
    otp = relationship("Otp", uselist=False, back_populates="owner")
    password_reset = relationship(
        "PasswordResetToken", uselist=False, back_populates="owner"
    )
    locations: Mapped[Set["UserLocation"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", lazy="selectin"
    )
    addresses: Mapped[List["Address"]] = relationship(
        cascade="all, delete", lazy="selectin"
    )

    bookings: Mapped[List["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
        lazy="selectin",
    )

    __mapper_args__ = {
        "polymorphic_identity": "user",
    }

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id:{self.id}, "
            f" failed_attempts:{self.failed_attempts}, "
            f" is_locked:{self.is_locked}, "
            f" lock_time:{self.lock_time},"
            f" locations:{self.locations},"
            f" bookings:{self.bookings},"
            f" username:{self.username},"
            f" email:{self.email},"
            f" created_at:{self.created_at},"
            f" created_by:{self.created_by},"
            f" modified_at:{self.modified_at},"
            f" modified_by:{self.modified_by}"
            f")>"
        )


class Address(Base):
    id: Mapped[str_pk_60]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    first_name: Mapped[required_30]
    last_name: Mapped[required_30]
    street_address: Mapped[required_100]
    country: Mapped[required_30]
    city: Mapped[required_30]
    zip_code: Mapped[required_30]
    user = relationship("User", back_populates="addresses")

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name


class Booking(Base):
    id: Mapped[str_pk_60]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    cart: Mapped[MutableList] = mapped_column(
        MutableList.as_mutable(ARRAY(JSONEncodedDict)), default=[]
    )
    address: Mapped[ShippingAddress] = mapped_column(
        PydanticColumn(ShippingAddress), nullable=False
    )
    created_at: Mapped[timestamp]
    total_price: Mapped[float]
    user: Mapped["User"] = relationship(back_populates="bookings")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id:{self.id}, "
            f" user_id:{self.user_id}, "
            f" address:{self.address}, "
            f" created_at:{self.created_at},"
            f" total_price:{self.total_price},"
            f" cart:{self.cart}"
            f")>"
        )


class UserLocation(Base):
    id: Mapped[str_pk_60]
    country: Mapped[required_30]
    enabled: Mapped[bool_col]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner = relationship("User", back_populates="locations")
    new_location = relationship(
        "NewLocationToken",
        uselist=False,
        back_populates="location",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id:{self.id}, "
            f" country:{self.country}, "
            f" enabled:{self.enabled},"
            f" userid:{self.user_id},"
            f")>"
        )


class NewLocationToken(Base):
    id: Mapped[str_pk_60]
    token: Mapped[required_100]
    user_loc_id: Mapped[required_60] = mapped_column(
        ForeignKey("userlocation.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    location = relationship(
        "UserLocation",
        back_populates="new_location",
        single_parent=True,
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} ("
            f" id:{self.id}, "
            f" user_location:{self.location} )>"
        )


class Otp(Base):
    id: Mapped[str_pk_60]
    email: Mapped[required_30]
    token: Mapped[required_100]
    expiry: Mapped[timestamp]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner = relationship(
        "User", back_populates="otp", single_parent=True, lazy="selectin"
    )
    __table_args__ = (UniqueConstraint("user_id"),)


class PasswordResetToken(Base):
    id: Mapped[str_pk_60]
    token: Mapped[required_100]
    expiry: Mapped[timestamp]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner = relationship(
        "User",
        back_populates="password_reset",
        single_parent=True,
        lazy="selectin",
    )
    __table_args__ = (UniqueConstraint("user_id"),)


class DeviceMetaData(Base):
    id: Mapped[str_pk_60]
    device_details: Mapped[required_100]
    location: Mapped[required_60]
    last_login_date: Mapped[timestamp]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id::{self.id}, "
            f"last_login_date::{self.last_login_date}, "
            f"userid::{self. user_id}"
            f")>"
        )


class Enquiry(Audit):
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    client_name: Mapped[required_60]
    client_email: Mapped[required_30]
    country: Mapped[required_30]
    subject: Mapped[required_30]
    message: Mapped[required_600]
    is_closed: Mapped[bool_col]

    __mapper_args__ = {
        "polymorphic_identity": "enquiry",
    }
