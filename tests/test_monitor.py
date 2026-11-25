"""Unit tests for the HMT watch stock monitor and multi-channel notifier."""

import unittest
from unittest.mock import MagicMock, patch

from src.checker import check_stock, parse_stock_from_html
from src.config import Config
from src.main import main
from src.notifier import send_alert, send_telegram, send_whatsapp_callmebot, send_whatsapp_cloud


def _make_config(**overrides) -> Config:
    defaults = {
        "product_url": "https://example.com/watch",
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "whatsapp_token": "",
        "whatsapp_phone_number_id": "",
        "whatsapp_to": "",
        "callmebot_phone": "",
        "callmebot_apikey": "",
        "gemini_api_key": "",
        "request_timeout": 20,
        "notify_on_unknown": False,
    }
    defaults.update(overrides)
    return Config(**defaults)


class TestStockParser(unittest.TestCase):
    def test_detects_out_of_stock_text(self) -> None:
        html = """
        <html><body>
          <h1>HMT Men's Gandaberunda JGSS 01</h1>
          <span class="price">₹2,599</span>
          <div class="stock-status">Out of Stock</div>
          <button disabled>Add to Cart</button>
        </body></html>
        """
        result = parse_stock_from_html(html)
        self.assertEqual(result.status, "OUT_OF_STOCK")
        self.assertEqual(result.price, "₹2,599")

    def test_detects_in_stock_active_button(self) -> None:
        html = """
        <html><body>
          <h1>HMT Men's Gandaberunda JGSS 01</h1>
          <span class="price">₹2,599</span>
          <button type="submit" class="btn-primary">Add to Cart</button>
        </body></html>
        """
        result = parse_stock_from_html(html)
        self.assertEqual(result.status, "IN_STOCK")
        self.assertEqual(result.price, "₹2,599")

    def test_unknown_when_no_clear_signals(self) -> None:
        html = "<html><body><h1>HMT Watch</h1><p>Loading details...</p></body></html>"
        result = parse_stock_from_html(html)
        self.assertEqual(result.status, "UNKNOWN")

    def test_detects_coming_soon_as_out_of_stock(self) -> None:
        html = "<html><body><h1>HMT Watch</h1><p>Coming Soon</p></body></html>"
        result = parse_stock_from_html(html)
        self.assertEqual(result.status, "OUT_OF_STOCK")

    def test_hmt_out_of_stock_ignores_unrelated_add_to_cart_buttons(self) -> None:
        html = """
        <html><body>
          <h1>HMT MEN'S GANDABERUNDA JGSS 01</h1>
          <span class="price">₹2599</span>
          <strong>Out Of Stock</strong>
          <div class="action">
            <a id="notifyMe" class="add-to-cart btn btn-default">Notify Me</a>
          </div>
          <div class="btn-ground">
            <button class="btn btn-primary add_to_cart">Add To Cart</button>
          </div>
        </body></html>
        """
        result = parse_stock_from_html(html)
        self.assertEqual(result.status, "OUT_OF_STOCK")
        self.assertEqual(result.price, "₹2599")


class TestCheckStockWithGeminiFallback(unittest.TestCase):
    @patch("src.checker.requests.post")
    @patch("src.checker.requests.get")
    def test_uses_gemini_fallback_on_unknown_html(self, mock_get: MagicMock, mock_post: MagicMock) -> None:
        page_resp = MagicMock()
        page_resp.text = "<html><body><h1>HMT Watch</h1><p>Limited edition</p></body></html>"
        page_resp.raise_for_status.return_value = None
        mock_get.return_value = page_resp

        ai_resp = MagicMock()
        ai_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"status": "IN_STOCK", "reason": "Available for purchase"}'}]
                    }
                }
            ]
        }
        ai_resp.raise_for_status.return_value = None
        mock_post.return_value = ai_resp

        result = check_stock("https://example.com/watch", gemini_api_key="fake-key")
        self.assertEqual(result.status, "IN_STOCK")
        self.assertIn("Gemini AI fallback", result.reason)
        mock_post.assert_called_once()


class TestNotifier(unittest.TestCase):
    def test_send_alert_raises_when_no_channel_configured(self) -> None:
        with self.assertRaises(ValueError):
            send_alert(_make_config(), "hello")

    @patch("src.notifier.requests.post")
    def test_sends_telegram_message(self, mock_post: MagicMock) -> None:
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp

        ok = send_telegram("bot-token", "12345", "Watch in stock!")
        self.assertTrue(ok)
        mock_post.assert_called_once()

    @patch("src.notifier.requests.post")
    def test_sends_whatsapp_cloud_message(self, mock_post: MagicMock) -> None:
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        mock_post.return_value = resp

        ok = send_whatsapp_cloud("wa-token", "987654", "+919999999999", "Watch in stock!")
        self.assertTrue(ok)
        mock_post.assert_called_once()

    @patch("src.notifier.requests.get")
    def test_sends_callmebot_message(self, mock_get: MagicMock) -> None:
        resp = MagicMock()
        resp.text = "Message queued."
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

        ok = send_whatsapp_callmebot("+919999999999", "123456", "Watch in stock!")
        self.assertTrue(ok)
        mock_get.assert_called_once()

    @patch("src.notifier.send_telegram", return_value=True)
    def test_send_alert_uses_configured_telegram(self, mock_tg: MagicMock) -> None:
        cfg = _make_config(telegram_bot_token="tok", telegram_chat_id="999")
        channels = send_alert(cfg, "Alert!")
        self.assertEqual(channels, ["telegram"])
        mock_tg.assert_called_once()


class TestMainCLI(unittest.TestCase):
    @patch("src.main.send_alert", return_value=["telegram"])
    @patch.dict(
        "os.environ",
        {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "999"},
        clear=False,
    )
    def test_test_notify_flag(self, mock_alert: MagicMock) -> None:
        exit_code = main(["--test-notify"])
        self.assertEqual(exit_code, 0)
        mock_alert.assert_called_once()

    @patch("src.main.send_alert", return_value=["telegram"])
    @patch("src.main.check_stock")
    @patch.dict(
        "os.environ",
        {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "999"},
        clear=False,
    )
    def test_notifies_on_unknown_by_default(self, mock_check: MagicMock, mock_alert: MagicMock) -> None:
        from src.checker import StockResult

        mock_check.return_value = StockResult(status="UNKNOWN", reason="Layout changed", price=None)
        exit_code = main([])
        self.assertEqual(exit_code, 0)
        mock_alert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
