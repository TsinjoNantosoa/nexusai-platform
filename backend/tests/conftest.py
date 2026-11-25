import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.db.models import Product
from app.db.session import build_session_factory
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = (
    ("free", "Free", "free", 0, 20),
    ("starter", "Starter", "one_time", 299, 100),
    ("plus", "Plus", "one_time", 999, 500),
    ("premium", "Premium", "recurring", 1999, 1500),
)


@pytest.fixture(scope="session")
def test_database_url() -> str:
    value = os.getenv("NEXUSAI_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set NEXUSAI_TEST_DATABASE_URL to run PostgreSQL integration tests.")
    return value


@pytest.fixture(scope="session")
def db_engine(test_database_url: str) -> Iterator[Engine]:
    engine = create_engine(test_database_url, pool_pre_ping=True)
    try:
        with engine.connect():
            pass
    except Exception as error:
        engine.dispose()
        pytest.fail(f"PostgreSQL integration database is unavailable: {error}")
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", test_database_url.replace("%", "%%"))
    command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def clean_database(db_engine: Engine) -> Iterator[None]:
    with db_engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE audit_logs, wallet_entries, wallets, sessions, products, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        for sku, name, product_type, price_cents, gems in PRODUCTS:
            session.add(
                Product(
                    sku=sku,
                    name=name,
                    product_type=product_type,
                    price_cents=price_cents,
                    currency="EUR",
                    gems=gems,
                    active=True,
                )
            )
    yield


@pytest.fixture
def client(test_database_url: str) -> Iterator[TestClient]:
    settings = Settings(database_url=test_database_url)
    with TestClient(create_app(settings)) as test_client:
        yield test_client
