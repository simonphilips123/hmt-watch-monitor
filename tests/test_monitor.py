"""Unit tests for the HMT watch stock monitor and CallMeBot notifier."""

import unittest
from unittest.mock import MagicMock, patch

from src.checker import check_stock, parse_stock_from_html
from src.main import main
from src.notifier import send_whatsapp_callmebot


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
    def test_raises_when_credentials_missing(self) -> None:
        with self.assertRaises(ValueError):
            send_whatsapp_callmebot("", "", "hello")

    @patch("src.notifier.requests.get")
    def test_sends_callmebot_message(self, mock_get: MagicMock) -> None:
        resp = MagicMock()
        resp.text = "Message queued."
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

        ok = send_whatsapp_callmebot("+919999999999", "123456", "Watch in stock!")
        self.assertTrue(ok)
        mock_get.assert_called_once()


class TestMainCLI(unittest.TestCase):
    @patch("src.main.send_whatsapp_callmebot")
    @patch.dict(
        "os.environ",
        {"CALLMEBOT_PHONE": "+919999999999", "CALLMEBOT_APIKEY": "123456"},
        clear=False,
    )
    def test_test_notify_flag(self, mock_notify: MagicMock) -> None:
        exit_code = main(["--test-notify"])
        self.assertEqual(exit_code, 0)
        mock_notify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
