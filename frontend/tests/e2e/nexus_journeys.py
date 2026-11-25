"""Run browser-based frontend demonstration journeys; not backend/Stripe validation."""
import os
import subprocess
from pathlib import Path
for script in ('financial_journey.py', 'chat_journey.py'):
    subprocess.run(['python3', str(Path(__file__).parent / script)], check=True)
