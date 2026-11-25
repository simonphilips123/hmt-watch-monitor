"""CLI entrypoint for the HMT watch availability monitor."""

import argparse
from datetime import datetime, timezone
import sys

from src.checker import check_stock
from src.config import load_config
from src.notifier import send_alert


def build_alert_message(product_url: str, price: str | None, reason: str) -> str:
    """Format a concise stock alert message."""
    price_line = f"Price: {price}\n" if price else ""
    return (
        "HMT WATCH AVAILABLE!\n"
        "Model: HMT Men's Gandaberunda JGSS 01\n"
        f"{price_line}"
        f"Status: {reason}\n"
        f"Buy now: {product_url}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check HMT watch stock and send alerts.")
    parser.add_argument(
        "--test-notify",
        action="store_true",
        help="Send a test alert to all configured channels and exit.",
    )
    args = parser.parse_args(argv)
    config = load_config()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if args.test_notify:
        print(f"[{now_utc}] Sending test notification...")
        channels = send_alert(
            config,
            f"Test alert from HMT Watch Monitor ({now_utc}). Setup is working!",
        )
        print(f"Test notification sent successfully via: {', '.join(channels)}")
        return 0

    print(f"[{now_utc}] Checking stock for: {config.product_url}")
    result = check_stock(
        product_url=config.product_url,
        timeout=config.request_timeout,
        gemini_api_key=config.gemini_api_key,
    )
    print(f"Result: status={result.status} | price={result.price} | reason={result.reason}")

    if result.status == "IN_STOCK":
        msg = build_alert_message(config.product_url, result.price, result.reason)
        channels = send_alert(config, msg)
        print(f"IN_STOCK alert sent via: {', '.join(channels)}")
    elif result.status == "UNKNOWN" and config.notify_on_unknown:
        msg = (
            "HMT Watch Monitor: Could not determine stock status.\n"
            f"Reason: {result.reason}\n"
            f"Link: {config.product_url}"
        )
        channels = send_alert(config, msg)
        print(f"UNKNOWN-status alert sent via: {', '.join(channels)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
