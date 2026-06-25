import os

import pytest
from sqlalchemy import text

from app.db.session import create_database_engine


@pytest.mark.integration
def test_database_connection_when_enabled() -> None:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to validate a live PostgreSQL connection.")

    engine = create_database_engine()
    with engine.connect() as connection:
        result = connection.execute(text("select 1")).scalar_one()

    assert result == 1
