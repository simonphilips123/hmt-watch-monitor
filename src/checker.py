"""Stock availability checker for HMT Watches with optional free Gemini AI fallback."""

from dataclasses import dataclass
import json
import re
from typing import Optional

from bs4 import BeautifulSoup
import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

OUT_OF_STOCK_PHRASES = (
    "out of stock",
    "sold out",
    "currently unavailable",
    "notify me when available",
    "coming soon",
)

IN_STOCK_BUTTON_PHRASES = (
    "add to cart",
    "buy now",
    "add to bag",
)


@dataclass(frozen=True)
class StockResult:
    """Result of checking a product page for availability."""

    status: str  # "IN_STOCK", "OUT_OF_STOCK", or "UNKNOWN"
    reason: str
    price: Optional[str] = None


def _extract_price(soup: BeautifulSoup) -> Optional[str]:
    """Best-effort extraction of the INR price from the page."""
    text = soup.get_text(" ", strip=True)
    match = re.search(r"(?:₹|Rs\.?|INR)\s?[\d,]+(?:\.\d{1,2})?", text, re.IGNORECASE)
    return match.group(0) if match else None


def _element_label(el) -> str:
    return " ".join(
        filter(None, [el.get_text(" ", strip=True), el.get("value", ""), el.get("title", "")])
    ).lower()


def parse_stock_from_html(html: str) -> StockResult:
    """Deterministically inspect HTML for HMT product availability signals."""
    soup = BeautifulSoup(html, "html.parser")
    price = _extract_price(soup)

    # Remove non-visible tags before checking text
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # 1. Check HMT's #notifyMe control or explicit out-of-stock text FIRST
    #    (prevents false positives from related-product/modal Add-to-Cart buttons).
    notify_el = soup.find(id="notifyMe")
    if notify_el is not None:
        return StockResult(
            status="OUT_OF_STOCK",
            reason="Found #notifyMe button ('Notify Me').",
            price=price,
        )

    page_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).lower()
    for phrase in OUT_OF_STOCK_PHRASES:
        if phrase in page_text:
            return StockResult(
                status="OUT_OF_STOCK",
                reason=f"Found out-of-stock indicator: '{phrase}'",
                price=price,
            )

    # 2. Scope purchase-button check to the main product .action container when present
    action_container = soup.select_one("div.action")
    search_root = action_container if action_container is not None else soup

    for el in search_root.find_all(["button", "input", "a"]):
        label = _element_label(el)
        if not label:
            continue

        is_disabled = el.has_attr("disabled") or "disabled" in (el.get("class") or [])
        if any(phrase in label for phrase in IN_STOCK_BUTTON_PHRASES) and not is_disabled:
            return StockResult(
                status="IN_STOCK",
                reason=f"Active purchase control found: '{label[:60]}'",
                price=price,
            )

    return StockResult(
        status="UNKNOWN",
        reason="No clear Add-to-Cart button or Out-of-Stock text found in HTML.",
        price=price,
    )


def classify_with_gemini(html: str, api_key: str, timeout: int = 20) -> Optional[StockResult]:
    """Use the free-tier Gemini API to classify ambiguous product page text."""
    if not api_key:
        return None

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    visible_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:4000]

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    prompt = (
        "You are checking an e-commerce product page for stock availability. "
        "Based ONLY on the text below, reply with a JSON object having keys "
        '"status" (one of "IN_STOCK", "OUT_OF_STOCK", "UNKNOWN") and "reason" (short string).\n\n'
        f"PAGE TEXT:\n{visible_text}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.0},
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)
        status = parsed.get("status", "UNKNOWN").upper()
        if status not in {"IN_STOCK", "OUT_OF_STOCK", "UNKNOWN"}:
            status = "UNKNOWN"
        return StockResult(
            status=status,
            reason=f"Gemini AI fallback: {parsed.get('reason', 'no reason provided')}",
            price=_extract_price(soup),
        )
    except Exception as exc:
        return StockResult(
            status="UNKNOWN",
            reason=f"Gemini AI fallback failed: {exc}",
            price=None,
        )


def check_stock(product_url: str, timeout: int = 20, gemini_api_key: str = "") -> StockResult:
    """Fetch the product page and determine whether the watch is available to buy."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    resp = requests.get(product_url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    result = parse_stock_from_html(resp.text)
    if result.status == "UNKNOWN" and gemini_api_key:
        ai_result = classify_with_gemini(resp.text, gemini_api_key, timeout=timeout)
        if ai_result is not None:
            return ai_result
    return result
