import argparse
import json
import sys

from app.billing.catalogue import CatalogueBootstrapError, run_catalogue_bootstrap
from app.billing.stripe_client import StripeClientError
from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NexusAI Stripe Sandbox catalogue bootstrap")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "--dry-run", action="store_true", help="Plan changes without Stripe or DB mutations"
    )
    modes.add_argument(
        "--apply", action="store_true", help="Create or reuse the approved catalogue"
    )
    modes.add_argument(
        "--verify", action="store_true", help="Verify Stripe resources and persisted mappings"
    )
    args = parser.parse_args(argv)
    mode = "dry-run" if args.dry_run else "apply" if args.apply else "verify"
    settings = get_settings()
    engine = build_engine(settings)
    try:
        result = run_catalogue_bootstrap(settings, mode, build_session_factory(engine))
        print(
            json.dumps(
                {
                    "mode": result.mode,
                    "stripe_account_id": result.stripe_account_id,
                    "plans": [plan.__dict__ for plan in result.plans],
                },
                sort_keys=True,
            )
        )
        return 0
    except (CatalogueBootstrapError, StripeClientError) as error:
        print(f"catalogue bootstrap failed: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
