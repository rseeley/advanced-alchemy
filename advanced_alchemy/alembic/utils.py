from contextlib import AbstractAsyncContextManager, AbstractContextManager
from pathlib import Path
from typing import TYPE_CHECKING, Union

from sqlalchemy import Engine, MetaData, Table
from typing_extensions import TypeIs

from advanced_alchemy.exceptions import MissingDependencyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
    from sqlalchemy.orm import DeclarativeBase, Session

__all__ = ("drop_all", "dump_tables")


async def drop_all(engine: "Union[AsyncEngine, Engine]", version_table_name: str, metadata: MetaData) -> None:
    """Drop all tables in the database.

    Args:
        engine: The database engine.
        version_table_name: The name of the version table.
        metadata: The metadata object containing the tables to drop.

    Raises:
        MissingDependencyError: If the `rich` package is not installed.
    """
    try:
        from rich import get_console
    except ImportError as e:  # pragma: no cover
        msg = "rich"
        raise MissingDependencyError(msg, install_package="cli") from e

    console = get_console()

    def _is_sync(engine: "Union[Engine, AsyncEngine]") -> "TypeIs[Engine]":
        return isinstance(engine, Engine)

    def _drop_tables_sync(engine: Engine) -> None:
        console.rule("[bold red]Connecting to database backend.")
        with engine.begin() as db:
            console.rule("[bold red]Dropping the db", align="left")
            metadata.drop_all(db)
            console.rule("[bold red]Dropping the version table", align="left")
            Table(version_table_name, metadata).drop(db, checkfirst=True)
        console.rule("[bold yellow]Successfully dropped all objects", align="left")

    async def _drop_tables_async(engine: "AsyncEngine") -> None:
        console.rule("[bold red]Connecting to database backend.", align="left")
        async with engine.begin() as db:
            console.rule("[bold red]Dropping the db", align="left")
            await db.run_sync(metadata.drop_all)
            console.rule("[bold red]Dropping the version table", align="left")
            await db.run_sync(Table(version_table_name, metadata).drop, checkfirst=True)
        console.rule("[bold yellow]Successfully dropped all objects", align="left")

    if _is_sync(engine):
        return _drop_tables_sync(engine)
    return await _drop_tables_async(engine)


async def dump_tables(
    dump_dir: Path,
    session: "Union[AbstractContextManager[Session], AbstractAsyncContextManager[AsyncSession]]",
    models: "list[type[DeclarativeBase]]",
) -> None:
    from types import new_class

    from advanced_alchemy._serialization import encode_json

    try:
        from rich import get_console
    except ImportError as e:  # pragma: no cover
        msg = "rich"
        raise MissingDependencyError(msg, install_package="cli") from e

    console = get_console()

    def _is_sync(
        session: "Union[AbstractAsyncContextManager[AsyncSession], AbstractContextManager[Session]]",
    ) -> "TypeIs[AbstractContextManager[Session]]":
        return isinstance(session, AbstractContextManager)

    def _dump_table_sync(session: "AbstractContextManager[Session]") -> None:
        from advanced_alchemy.repository import SQLAlchemySyncRepository

        with session as _session:
            for model in models:
                json_path = dump_dir / f"{model.__tablename__}.json"
                console.rule(
                    f"[yellow bold]Dumping table '{json_path.stem}' to '{json_path}'",
                    style="yellow",
                    align="left",
                )
                repo = new_class(
                    "repo",
                    (SQLAlchemySyncRepository,),
                    exec_body=lambda ns, model=model: ns.setdefault("model_type", model),  # type: ignore[misc]
                )
                json_path.write_text(encode_json([row.to_dict() for row in repo(session=_session).list()]))

    async def _dump_table_async(session: "AbstractAsyncContextManager[AsyncSession]") -> None:
        from advanced_alchemy.repository import SQLAlchemyAsyncRepository

        async with session as _session:
            for model in models:
                json_path = dump_dir / f"{model.__tablename__}.json"
                console.rule(
                    f"[yellow bold]Dumping table '{json_path.stem}' to '{json_path}'",
                    style="yellow",
                    align="left",
                )
                repo = new_class(
                    "repo",
                    (SQLAlchemyAsyncRepository,),
                    exec_body=lambda ns, model=model: ns.setdefault("model_type", model),  # type: ignore[misc]
                )
                json_path.write_text(encode_json([row.to_dict() for row in await repo(session=_session).list()]))

    dump_dir.mkdir(exist_ok=True)

    if _is_sync(session):
        return _dump_table_sync(session)
    return await _dump_table_async(session)
