"""Notification senders: Telegram Bot API, Meta WhatsApp Cloud API, and CallMeBot."""

import requests

from src.config import Config

CALLMEBOT_ENDPOINT = "https://api.callmebot.com/whatsapp.php"


def send_telegram(bot_token: str, chat_id: str, message: str, timeout: int = 20) -> bool:
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=timeout,
    )
    resp.raise_for_status()
    return True


def send_whatsapp_cloud(
    token: str,
    phone_number_id: str,
    to_number: str,
    message: str,
    timeout: int = 20,
) -> bool:
    """Send a WhatsApp text message via the official Meta WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number.lstrip("+"),
        "type": "text",
        "text": {"body": message},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return True


def send_whatsapp_callmebot(
    phone: str,
    apikey: str,
    message: str,
    timeout: int = 20,
) -> bool:
    """Send a WhatsApp message via CallMeBot."""
    if not phone or not apikey:
        raise ValueError("CALLMEBOT_PHONE and CALLMEBOT_APIKEY must be set.")

    resp = requests.get(
        CALLMEBOT_ENDPOINT,
        params={"phone": phone, "text": message, "apikey": apikey},
        timeout=timeout,
    )
    resp.raise_for_status()

    body_lower = resp.text.lower()
    if "error" in body_lower and "queued" not in body_lower and "sent" not in body_lower:
        raise RuntimeError(f"CallMeBot returned an error: {resp.text.strip()}")
    return True


def send_alert(config: Config, message: str) -> list[str]:
    """Send an alert to every configured notification channel.

    Returns a list of channel names that succeeded, or raises ValueError if no
    notification channel is configured.
    """
    sent_channels: list[str] = []

    if config.telegram_bot_token and config.telegram_chat_id:
        send_telegram(
            bot_token=config.telegram_bot_token,
            chat_id=config.telegram_chat_id,
            message=message,
            timeout=config.request_timeout,
        )
        sent_channels.append("telegram")

    if config.whatsapp_token and config.whatsapp_phone_number_id and config.whatsapp_to:
        send_whatsapp_cloud(
            token=config.whatsapp_token,
            phone_number_id=config.whatsapp_phone_number_id,
            to_number=config.whatsapp_to,
            message=message,
            timeout=config.request_timeout,
        )
        sent_channels.append("whatsapp_cloud")

    if config.callmebot_phone and config.callmebot_apikey:
        send_whatsapp_callmebot(
            phone=config.callmebot_phone,
            apikey=config.callmebot_apikey,
            message=message,
            timeout=config.request_timeout,
        )
        sent_channels.append("callmebot")

    if not sent_channels:
        raise ValueError(
            "No notification channel configured. Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID "
            "(recommended), or WHATSAPP_TOKEN + WHATSAPP_PHONE_NUMBER_ID + WHATSAPP_TO."
        )

    return sent_channels
