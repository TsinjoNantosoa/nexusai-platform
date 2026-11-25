import argparse

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import User
from app.db.session import build_engine, build_session_factory


def provision_admin(email: str) -> None:
    settings = get_settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    with factory.begin() as session:
        user = session.execute(
            select(User).where(User.email == email.strip().lower())
        ).scalar_one_or_none()
        if user is None:
            raise SystemExit("User does not exist; register a fictional local account first.")
        user.role = "admin"
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Promote an existing local account to administrator."
    )
    parser.add_argument("--email", required=True)
    provision_admin(parser.parse_args().email)
