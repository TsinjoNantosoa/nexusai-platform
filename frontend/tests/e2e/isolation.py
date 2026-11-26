import os
from collections.abc import Mapping


_DISABLED_VALUES = {"", "0", "false", "no", "off"}
_STRIPE_CREDENTIAL_ENV_NAMES = (
    "NEXUSAI_STRIPE_SECRET_KEY",
    "NEXUSAI_STRIPE_WEBHOOK_SECRET",
)


def _assert_no_stripe_credentials(environ: Mapping[str, str]) -> None:
    if any(environ.get(name, "").strip() for name in _STRIPE_CREDENTIAL_ENV_NAMES):
        raise RuntimeError(
            "Automated browser journeys refuse inherited Stripe credentials."
        )


def prepare_isolated_e2e_environment() -> dict[str, str]:
    environ = dict(os.environ)
    enabled = environ.get("NEXUSAI_STRIPE_ENABLED", "").strip().lower()
    if enabled not in _DISABLED_VALUES:
        raise RuntimeError("Automated browser journeys require Stripe to be disabled.")
    _assert_no_stripe_credentials(environ)
    environ["NEXUSAI_E2E_MODE"] = "isolated"
    environ["NEXUSAI_STRIPE_ENABLED"] = "false"
    for name in _STRIPE_CREDENTIAL_ENV_NAMES:
        environ.pop(name, None)
    return environ


def assert_isolated_e2e_environment(environ: Mapping[str, str] | None = None) -> None:
    values = os.environ if environ is None else environ
    if values.get("NEXUSAI_E2E_MODE") != "isolated":
        raise RuntimeError(
            "Automated browser journeys require the isolated E2E launcher."
        )
    enabled = values.get("NEXUSAI_STRIPE_ENABLED", "").strip().lower()
    if enabled not in _DISABLED_VALUES:
        raise RuntimeError("Automated browser journeys require Stripe to be disabled.")
    _assert_no_stripe_credentials(values)
