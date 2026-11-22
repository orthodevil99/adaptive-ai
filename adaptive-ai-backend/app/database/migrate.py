"""Create tables and add any missing nullable columns (so a v2 SQLite/Postgres DB keeps working)."""

import logging

from sqlalchemy import Engine, inspect, text

from app.database.connection import Base

logger = logging.getLogger(__name__)


def init_database(engine: Engine) -> list[str]:
    Base.metadata.create_all(bind=engine)
    return add_missing_columns(engine)


def add_missing_columns(engine: Engine) -> list[str]:
    added: list[str] = []
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                if not column.nullable:
                    logger.warning("Cannot auto-add NOT NULL column %s.%s", table.name, column.name)
                    continue
                ddl_type = column.type.compile(dialect=engine.dialect)
                connection.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {ddl_type}'))
                added.append(f"{table.name}.{column.name}")
    if added:
        logger.info("Migrated database: added %s", ", ".join(added))
    return added
