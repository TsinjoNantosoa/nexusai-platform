import os
import unittest

from isolation import assert_isolated_e2e_environment, prepare_isolated_e2e_environment


class E2EIsolationTests(unittest.TestCase):
    def test_launcher_sets_an_isolated_disabled_environment(self) -> None:
        environment = prepare_isolated_e2e_environment()
        self.assertEqual(environment["NEXUSAI_E2E_MODE"], "isolated")
        self.assertEqual(environment["NEXUSAI_STRIPE_ENABLED"], "false")
        self.assertNotIn("NEXUSAI_STRIPE_SECRET_KEY", environment)
        self.assertNotIn("NEXUSAI_STRIPE_WEBHOOK_SECRET", environment)

    def test_journey_rejects_missing_isolated_mode(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "isolated E2E launcher"):
            assert_isolated_e2e_environment({"NEXUSAI_STRIPE_ENABLED": "false"})

    def test_launcher_rejects_inherited_stripe_credentials(self) -> None:
        original = dict(os.environ)
        try:
            os.environ["NEXUSAI_STRIPE_ENABLED"] = "false"
            os.environ["NEXUSAI_STRIPE_SECRET_KEY"] = "sk_test_owner_value"
            with self.assertRaisesRegex(RuntimeError, "inherited Stripe credentials"):
                prepare_isolated_e2e_environment()
        finally:
            os.environ.clear()
            os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
