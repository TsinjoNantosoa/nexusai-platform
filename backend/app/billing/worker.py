from __future__ import annotations

import argparse
import time
from uuid import UUID

from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory

from .fulfillment import WebhookProcessor, requeue_event


def run_once() -> str:
    settings = get_settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    try:
        with factory() as session:
            processor = WebhookProcessor(session, settings)
            event_id = processor.claim_next()
            if event_id is None:
                return "idle"
            return processor.process_one(event_id)
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Process the NexusAI Stripe webhook inbox.")
    parser.add_argument("--once", action="store_true", help="Process at most one event.")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds.")
    parser.add_argument("--replay", type=UUID, help="Requeue one terminal event before processing.")
    args = parser.parse_args()
    settings = get_settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    try:
        if args.replay:
            with factory() as session:
                requeue_event(session, args.replay)
        while True:
            result = run_once()
            if args.once or result == "idle":
                return
            time.sleep(max(0.1, args.interval))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
