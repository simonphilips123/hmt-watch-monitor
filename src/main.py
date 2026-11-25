"""CLI entrypoint for the HMT watch availability monitor."""

import argparse
from datetime import datetime, timezone
import sys

from src.checker import check_stock
from src.config import load_config
from src.notifier import send_whatsapp_callmebot


def build_alert_message(product_url: str, price: str | None, reason: str) -> str:
    """Format a concise WhatsApp alert message."""
    price_line = f"Price: {price}\n" if price else ""
    return (
        "HMT WATCH AVAILABLE!\n"
        "Model: HMT Men's Gandaberunda JGSS 01\n"
        f"{price_line}"
        f"Status: {reason}\n"
        f"Buy now: {product_url}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check HMT watch stock and alert via WhatsApp.")
    parser.add_argument(
        "--test-notify",
        action="store_true",
        help="Send a test WhatsApp message via CallMeBot and exit.",
    )
    args = parser.parse_args(argv)
    config = load_config()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if args.test_notify:
        print(f"[{now_utc}] Sending test WhatsApp notification...")
        send_whatsapp_callmebot(
            phone=config.callmebot_phone,
            apikey=config.callmebot_apikey,
            message=f"Test alert from HMT Watch Monitor ({now_utc}). Setup is working!",
            timeout=config.request_timeout,
        )
        print("Test WhatsApp notification sent successfully.")
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
        send_whatsapp_callmebot(
            phone=config.callmebot_phone,
            apikey=config.callmebot_apikey,
            message=msg,
            timeout=config.request_timeout,
        )
        print("WhatsApp IN_STOCK alert sent!")
    elif result.status == "UNKNOWN" and config.notify_on_unknown:
        msg = (
            "HMT Watch Monitor: Could not determine stock status.\n"
            f"Reason: {result.reason}\n"
            f"Link: {config.product_url}"
        )
        send_whatsapp_callmebot(
            phone=config.callmebot_phone,
            apikey=config.callmebot_apikey,
            message=msg,
            timeout=config.request_timeout,
        )
        print("WhatsApp UNKNOWN-status alert sent.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
