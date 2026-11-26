import pytest
from app.db.safety import (
    DatabaseSafetyError,
    DisposableDatabaseConfig,
    assert_safe_disposable_test_database,
    database_config_from_environment,
    is_destructive_alembic_command,
    validate_disposable_test_target,
)

TEST_URL = "postgresql+psycopg://nexusai_test:test-password@127.0.0.1:55433/nexusai_test"
DEVELOPMENT_URL = "postgresql+psycopg://nexusai:dev-password@127.0.0.1:55432/nexusai"
PRODUCTION_URL = "postgresql+psycopg://nexusai_prod:prod-password@db.example.test:5432/nexusai"


def disposable_config(**overrides: object) -> DisposableDatabaseConfig:
    values: dict[str, object] = {
        "database_name": "nexusai_test",
        "role": "nexusai_test",
        "disposable_authorized": True,
        "development_database_url": DEVELOPMENT_URL,
        "production_database_url": PRODUCTION_URL,
    }
    values.update(overrides)
    return DisposableDatabaseConfig(**values)


class FakeConnection:
    def __init__(self, row: tuple[object, ...]) -> None:
        self.row = row
        self.execute_count = 0

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, _statement: object) -> "FakeResult":
        self.execute_count += 1
        return FakeResult(self.row)


class FakeResult:
    def __init__(self, row: tuple[object, ...]) -> None:
        self.row = row

    def one(self) -> tuple[object, ...]:
        return self.row


class FakeEngine:
    def __init__(self, row: tuple[object, ...]) -> None:
        self.connection = FakeConnection(row)

    def connect(self) -> FakeConnection:
        return self.connection


def test_missing_test_configuration_is_rejected() -> None:
    with pytest.raises(DatabaseSafetyError):
        database_config_from_environment({})


def test_test_database_name_alone_is_not_authorization() -> None:
    with pytest.raises(DatabaseSafetyError):
        database_config_from_environment(
            {
                "NEXUSAI_TEST_DATABASE_NAME": "nexusai_test",
                "NEXUSAI_TEST_DATABASE_ROLE": "nexusai_test",
            }
        )


def test_development_target_must_be_declared() -> None:
    with pytest.raises(DatabaseSafetyError):
        database_config_from_environment(
            {
                "NEXUSAI_TEST_DATABASE_NAME": "nexusai_test",
                "NEXUSAI_TEST_DATABASE_ROLE": "nexusai_test",
                "NEXUSAI_TEST_DATABASE_DISPOSABLE": "true",
            }
        )


def test_development_and_production_targets_are_rejected() -> None:
    config = disposable_config()
    with pytest.raises(DatabaseSafetyError):
        validate_disposable_test_target(DEVELOPMENT_URL, config)
    with pytest.raises(DatabaseSafetyError):
        validate_disposable_test_target(PRODUCTION_URL, config)


def test_incorrect_role_and_database_identity_are_rejected() -> None:
    config = disposable_config()
    with pytest.raises(DatabaseSafetyError):
        validate_disposable_test_target(
            "postgresql+psycopg://wrong_role:password@127.0.0.1:55433/nexusai_test",
            config,
        )
    with pytest.raises(DatabaseSafetyError):
        validate_disposable_test_target(
            "postgresql+psycopg://nexusai_test:password@127.0.0.1:55433/example_test",
            config,
        )


def test_effective_database_identity_must_match_before_destructive_sql() -> None:
    engine = FakeEngine(("nexusai", "nexusai"))
    with pytest.raises(DatabaseSafetyError):
        assert_safe_disposable_test_database(TEST_URL, engine, disposable_config())
    assert engine.connection.execute_count == 1


def test_rejected_static_target_does_not_execute_identity_query() -> None:
    engine = FakeEngine(("nexusai_test", "nexusai_test"))
    with pytest.raises(DatabaseSafetyError):
        assert_safe_disposable_test_database(DEVELOPMENT_URL, engine, disposable_config())
    assert engine.connection.execute_count == 0


def test_explicitly_authorized_effective_test_target_is_accepted() -> None:
    engine = FakeEngine(("nexusai_test", "nexusai_test"))
    identity = assert_safe_disposable_test_database(TEST_URL, engine, disposable_config())
    assert identity.database == "nexusai_test"
    assert identity.username == "nexusai_test"
    assert engine.connection.execute_count == 1


def test_only_destructive_alembic_commands_require_the_guard() -> None:
    assert is_destructive_alembic_command(["downgrade", "base"])
    assert is_destructive_alembic_command(["stamp", "base"])
    assert not is_destructive_alembic_command(["upgrade", "head"])
