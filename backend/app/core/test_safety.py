import os
from collections.abc import Mapping


class AutomatedTestSafetyError(RuntimeError):
    """Raised when automated tests inherit a live integration configuration."""


_DISABLED_VALUES = {"", "0", "false", "no", "off"}
_STRIPE_CREDENTIAL_ENV_NAMES = (
    "NEXUSAI_STRIPE_SECRET_KEY",
    "NEXUSAI_STRIPE_WEBHOOK_SECRET",
)


def validate_automated_test_environment(
    environ: Mapping[str, str] | None = None,
) -> None:
    values = os.environ if environ is None else environ
    enabled = values.get("NEXUSAI_STRIPE_ENABLED", "").strip().lower()
    if enabled not in _DISABLED_VALUES:
        raise AutomatedTestSafetyError(
            "Automated tests require NEXUSAI_STRIPE_ENABLED=false or unset."
        )
    if any(values.get(name, "").strip() for name in _STRIPE_CREDENTIAL_ENV_NAMES):
        raise AutomatedTestSafetyError(
            "Automated tests must not inherit Stripe credentials; use a mocked gateway."
        )
