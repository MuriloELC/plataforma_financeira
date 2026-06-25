from pathlib import Path
import sys

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import create_database_engine  # noqa: E402


def main() -> int:
    engine = create_database_engine()
    with engine.connect() as connection:
        result = connection.execute(text("select 1")).scalar_one()

    if result != 1:
        print("Database connection failed")
        return 1

    print("Database connection OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
