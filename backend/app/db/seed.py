from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import Product
from app.db.session import build_engine, build_session_factory

PRODUCTS = (
    {"sku": "free", "name": "Free", "product_type": "free", "price_cents": 0, "gems": 20},
    {
        "sku": "starter",
        "name": "Starter",
        "product_type": "one_time",
        "price_cents": 299,
        "gems": 100,
    },
    {"sku": "plus", "name": "Plus", "product_type": "one_time", "price_cents": 999, "gems": 500},
    {
        "sku": "premium",
        "name": "Premium",
        "product_type": "recurring",
        "price_cents": 1999,
        "gems": 1500,
    },
)


def seed_products() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    with factory.begin() as session:
        for values in PRODUCTS:
            product = session.execute(
                select(Product).where(Product.sku == values["sku"])
            ).scalar_one_or_none()
            if product is None:
                session.add(Product(currency="EUR", active=True, **values))
            else:
                for key, value in values.items():
                    setattr(product, key, value)
                product.currency = "EUR"
                product.active = True
                product.updated_at = datetime.now(UTC)
    engine.dispose()


if __name__ == "__main__":
    seed_products()
