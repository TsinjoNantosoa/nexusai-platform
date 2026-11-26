"""Run browser-based frontend demonstration journeys; not backend/Stripe validation."""
import subprocess
import sys
from pathlib import Path


for script in ('financial_journey.py', 'chat_journey.py'):
    subprocess.run([sys.executable, str(Path(__file__).parent / script)], check=True)
