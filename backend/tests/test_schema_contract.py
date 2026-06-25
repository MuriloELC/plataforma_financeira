import os

import pytest
from sqlalchemy import text

from app.db.schema_contract import REQUIRED_COLUMNS, REQUIRED_SCHEMAS, REQUIRED_TABLES
from app.db.session import create_database_engine


@pytest.mark.integration
def test_database_schema_contract_when_enabled() -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate a live PostgreSQL schema.")

    engine = create_database_engine()
    with engine.connect() as connection:
        schemas = set(
            connection.execute(
                text(
                    """
                    select schema_name
                    from information_schema.schemata
                    where schema_name = any(:schemas)
                    """
                ),
                {"schemas": list(REQUIRED_SCHEMAS)},
            ).scalars()
        )

        tables = set(
            connection.execute(
                text(
                    """
                    select table_schema, table_name
                    from information_schema.tables
                    where table_schema = any(:schemas)
                      and table_type = 'BASE TABLE'
                    """
                ),
                {"schemas": list(REQUIRED_TABLES)},
            ).all()
        )

        columns = set(
            connection.execute(
                text(
                    """
                    select table_schema, table_name, column_name
                    from information_schema.columns
                    where table_schema = any(:schemas)
                    """
                ),
                {"schemas": list(REQUIRED_TABLES)},
            ).all()
        )

    assert set(REQUIRED_SCHEMAS).issubset(schemas)

    for schema, required_tables in REQUIRED_TABLES.items():
        for table in required_tables:
            assert (schema, table) in tables

    for (schema, table), required_columns in REQUIRED_COLUMNS.items():
        for column in required_columns:
            assert (schema, table, column) in columns
