"""Example domain objects for testing."""

import datetime

from sqlalchemy import Column, FetchedValue, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.orm.decl_base import _TableArgsType as TableArgsType  # pyright: ignore[reportPrivateUsage]

from advanced_alchemy.base import BigIntAuditBase, BigIntBase, merge_table_arguments
from advanced_alchemy.mixins import SlugKey
from advanced_alchemy.types import EncryptedString, EncryptedText, FileObject, FileObjectList, StoredObject
from advanced_alchemy.types.file_object import storages


class BigIntAuthor(BigIntAuditBase):
    """The Author domain object."""

    name: Mapped[str] = mapped_column(String(length=100))
    string_field: Mapped[str] = mapped_column(String(20), default="static value", nullable=True)
    dob: Mapped[datetime.date] = mapped_column(nullable=True)
    books: Mapped[list["BigIntBook"]] = relationship(
        lazy="selectin",
        back_populates="author",
        cascade="all, delete",
    )


class BigIntBook(BigIntBase):
    """The Book domain object."""

    title: Mapped[str] = mapped_column(String(length=250))  # pyright: ignore
    author_id: Mapped[int] = mapped_column(ForeignKey("big_int_author.id"))  # pyright: ignore
    author: Mapped[BigIntAuthor] = relationship(  # pyright: ignore
        lazy="joined",
        innerjoin=True,
        back_populates="books",
    )


class BigIntSlugBook(BigIntBase, SlugKey):
    """The Book domain object with a slug key."""

    title: Mapped[str] = mapped_column(String(length=250))  # pyright: ignore
    author_id: Mapped[str] = mapped_column(String(length=250))  # pyright: ignore

    @declared_attr.directive
    @classmethod
    def __table_args__(cls) -> TableArgsType:
        return merge_table_arguments(
            cls,
            table_args={"comment": "Slugbook"},
        )


class BigIntEventLog(BigIntAuditBase):
    """The event log domain object."""

    logged_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now())  # pyright: ignore
    payload: Mapped[dict] = mapped_column(default=lambda: {})  # pyright: ignore


class BigIntModelWithFetchedValue(BigIntBase):
    """The ModelWithFetchedValue BigIntBase."""

    val: Mapped[int]  # pyright: ignore
    updated: Mapped[datetime.datetime] = mapped_column(  # pyright: ignore
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        server_onupdate=FetchedValue(),
    )


bigint_item_tag = Table(
    "bigint_item_tag",
    BigIntBase.metadata,
    Column("item_id", ForeignKey("big_int_item.id"), primary_key=True),  # pyright: ignore
    Column("tag_id", ForeignKey("big_int_tag.id"), primary_key=True),  # pyright: ignore
)


class BigIntItem(BigIntBase):
    name: Mapped[str] = mapped_column(String(length=50))  # pyright: ignore
    description: Mapped[str] = mapped_column(String(length=100), nullable=True)  # pyright: ignore
    tags: Mapped[list["BigIntTag"]] = relationship(secondary=lambda: bigint_item_tag, back_populates="items")


class BigIntTag(BigIntBase):
    """The event log domain object."""

    name: Mapped[str] = mapped_column(String(length=50))  # pyright: ignore
    items: Mapped[list[BigIntItem]] = relationship(secondary=lambda: bigint_item_tag, back_populates="tags")


class BigIntRule(BigIntAuditBase):
    """The rule domain object."""

    name: Mapped[str] = mapped_column(String(length=250))  # pyright: ignore
    config: Mapped[dict] = mapped_column(default=lambda: {})  # pyright: ignore


class BigIntSecret(BigIntBase):
    """The secret domain model."""

    secret: Mapped[str] = mapped_column(
        EncryptedString(key="super_secret"),
    )
    long_secret: Mapped[str] = mapped_column(
        EncryptedText(key="super_secret"),
    )
    length_validated_secret: Mapped[str] = mapped_column(
        EncryptedString(key="super_secret", length=10),
        nullable=True,
    )


class BigIntFileDocument(BigIntBase):
    """The file document domain model."""

    title: Mapped[str] = mapped_column(String(length=100))
    attachment: Mapped[FileObject] = mapped_column(
        StoredObject(backend="memory"),
        nullable=True,
    )
    required_file: Mapped[FileObject] = mapped_column(StoredObject(backend="memory"), nullable=True)
    required_files: Mapped[FileObjectList] = mapped_column(
        StoredObject(backend="memory", multiple=True),
        nullable=True,
    )


if not storages.is_registered("memory"):
    storages.register_backend("memory://", "memory")
