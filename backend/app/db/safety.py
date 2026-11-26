import os
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url


class DatabaseSafetyError(ValueError):
    """Raised before an unsafe database operation can reach SQL execution."""


@dataclass(frozen=True)
class DatabaseIdentity:
    drivername: str
    host: str
    port: int | None
    database: str
    username: str

    @classmethod
    def from_url(cls, database_url: str) -> "DatabaseIdentity":
        try:
            parsed = make_url(database_url)
        except Exception as error:
            raise DatabaseSafetyError("The database URL is invalid.") from error
        if parsed.get_backend_name() != "postgresql":
            raise DatabaseSafetyError("Database safety checks require PostgreSQL.")
        if not parsed.database or not parsed.username:
            raise DatabaseSafetyError("The database URL must include a database and role.")
        return cls(
            drivername=parsed.drivername,
            host=(parsed.host or "localhost").lower(),
            port=parsed.port,
            database=parsed.database,
            username=parsed.username,
        )

    def same_target(self, other: "DatabaseIdentity") -> bool:
        return (
            self.drivername == other.drivername
            and self.host == other.host
            and self.port == other.port
            and self.database == other.database
            and self.username == other.username
        )


@dataclass(frozen=True)
class DisposableDatabaseConfig:
    database_name: str
    role: str
    disposable_authorized: bool
    development_database_url: str | None = None
    production_database_url: str | None = None


def database_config_from_environment(
    environ: Mapping[str, str] | None = None,
) -> DisposableDatabaseConfig:
    values = os.environ if environ is None else environ
    database_name = values.get("NEXUSAI_TEST_DATABASE_NAME", "")
    role = values.get("NEXUSAI_TEST_DATABASE_ROLE", "")
    development_database_url = values.get("NEXUSAI_DEVELOPMENT_DATABASE_URL")
    authorized = values.get("NEXUSAI_TEST_DATABASE_DISPOSABLE", "").lower() == "true"
    if not database_name or not role or not authorized or not development_database_url:
        raise DatabaseSafetyError(
            "Disposable test authorization requires test name, role, approval, and development URL."
        )
    return DisposableDatabaseConfig(
        database_name=database_name,
        role=role,
        disposable_authorized=authorized,
        development_database_url=development_database_url,
        production_database_url=values.get("NEXUSAI_PRODUCTION_DATABASE_URL"),
    )


def validate_disposable_test_target(
    database_url: str,
    config: DisposableDatabaseConfig,
) -> DatabaseIdentity:
    identity = DatabaseIdentity.from_url(database_url)
    if not config.disposable_authorized:
        raise DatabaseSafetyError("Destructive operations require explicit disposable approval.")
    if identity.database != config.database_name:
        raise DatabaseSafetyError(
            "The configured database name is not the authorized test database."
        )
    if identity.username != config.role:
        raise DatabaseSafetyError("The configured database role is not the authorized test role.")
    for label, known_url in (
        ("development", config.development_database_url),
        ("production", config.production_database_url),
    ):
        if known_url and identity.same_target(DatabaseIdentity.from_url(known_url)):
            raise DatabaseSafetyError(f"The test target matches the known {label} database.")
    return identity


def verify_effective_database_target(engine: Engine, configured: DatabaseIdentity) -> None:
    with engine.connect() as connection:
        database_name, role = connection.execute(
            text("SELECT current_database(), current_user")
        ).one()
    if database_name != configured.database or role != configured.username:
        raise DatabaseSafetyError(
            "The effective PostgreSQL database identity does not match configuration."
        )
def assert_safe_disposable_test_database(
    database_url: str,
    engine: Engine,
    config: DisposableDatabaseConfig | None = None,
) -> DatabaseIdentity:
    resolved_config = config or database_config_from_environment()
    identity = validate_disposable_test_target(database_url, resolved_config)
    verify_effective_database_target(engine, identity)
    return identity


def is_destructive_alembic_command(arguments: list[str]) -> bool:
    commands = {argument for argument in arguments if not argument.startswith("-")}
    return bool(commands.intersection({"downgrade", "stamp"}))
