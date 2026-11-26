"""Run browser-based frontend demonstration journeys; not backend/Stripe validation."""
import subprocess
import sys
from pathlib import Path

from isolation import prepare_isolated_e2e_environment


isolated_environment = prepare_isolated_e2e_environment()


for script in ('financial_journey.py', 'chat_journey.py'):
    subprocess.run(
        [sys.executable, str(Path(__file__).parent / script)],
        check=True,
        env=isolated_environment,
    )
