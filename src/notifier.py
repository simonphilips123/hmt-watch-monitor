"""WhatsApp notification sender using the free CallMeBot API."""

import requests

CALLMEBOT_ENDPOINT = "https://api.callmebot.com/whatsapp.php"


def send_whatsapp_callmebot(
    phone: str,
    apikey: str,
    message: str,
    timeout: int = 20,
) -> bool:
    """Send a WhatsApp message via CallMeBot.

    Returns True if CallMeBot accepted the message, raises ValueError if credentials
    are missing, or raises requests.RequestException on HTTP/network failure.
    """
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
