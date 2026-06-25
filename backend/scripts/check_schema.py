from pathlib import Path
import sys

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.schema_contract import REQUIRED_COLUMNS, REQUIRED_SCHEMAS, REQUIRED_TABLES  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402


def main() -> int:
    engine = create_database_engine()
    errors: list[str] = []

    with engine.connect() as connection:
        existing_schemas = set(
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
        for schema in REQUIRED_SCHEMAS:
            if schema not in existing_schemas:
                errors.append(f"Missing schema: {schema}")

        existing_tables = set(
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
        for schema, tables in REQUIRED_TABLES.items():
            for table in tables:
                if (schema, table) not in existing_tables:
                    errors.append(f"Missing table: {schema}.{table}")

        existing_columns = set(
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
        for (schema, table), columns in REQUIRED_COLUMNS.items():
            for column in columns:
                if (schema, table, column) not in existing_columns:
                    errors.append(f"Missing column: {schema}.{table}.{column}")

    if errors:
        for error in errors:
            print(error)
        return 1

    print("Database schema OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
