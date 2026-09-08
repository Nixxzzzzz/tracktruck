"""
Relational Database Models for Users and Roles (RBAC Foundation).
"""

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Role(Base):
    """RBAC Role table defining system roles."""

    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    """System User account model supporting authentication, soft-delete, and RBAC."""

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    role_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("roles.role_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")
