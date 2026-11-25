"""Configuration loader for the HMT watch monitor."""

from dataclasses import dataclass
import os

DEFAULT_PRODUCT_URL = "https://www.hmtwatches.in/product-1180-hmt-mens-gandaberunda-jgss-01"


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from environment variables."""

    product_url: str
    telegram_bot_token: str
    telegram_chat_id: str
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_to: str
    callmebot_phone: str
    callmebot_apikey: str
    gemini_api_key: str
    request_timeout: int
    notify_on_unknown: bool


def load_config() -> Config:
    """Load configuration from environment variables with safe defaults."""
    timeout_raw = os.getenv("REQUEST_TIMEOUT", "20").strip()
    try:
        request_timeout = max(5, int(timeout_raw))
    except ValueError:
        request_timeout = 20

    return Config(
        product_url=os.getenv("PRODUCT_URL", DEFAULT_PRODUCT_URL).strip(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        whatsapp_token=os.getenv("WHATSAPP_TOKEN", "").strip(),
        whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
        whatsapp_to=os.getenv("WHATSAPP_TO", "").strip(),
        callmebot_phone=os.getenv("CALLMEBOT_PHONE", "").strip(),
        callmebot_apikey=os.getenv("CALLMEBOT_APIKEY", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        request_timeout=request_timeout,
        notify_on_unknown=os.getenv("NOTIFY_ON_UNKNOWN", "false").strip().lower() == "true",
    )
