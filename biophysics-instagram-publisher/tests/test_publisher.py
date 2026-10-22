import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PIL import Image
import publisher


CONFIG = {
    "IG_ACCESS_TOKEN": "test-secret-never-log",
    "IG_PAGE_ID": "123", "IG_ACCOUNT_ID": "456",
    "IG_EXPECTED_USERNAME": "gangopadhyay.poulomi", "IG_API_VERSION": "v26.0",
}


def api_responses():
    return [
        {"id": "123", "instagram_business_account": {"id": "456"}},
        {"id": "456", "username": "gangopadhyay.poulomi"},
        {"data": [{"quota_usage": 0, "config": {"quota_total": 100}}]},
        {"id": "789"}, {"status_code": "FINISHED"}, {"id": "900"},
    ]


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=publisher.ROOT)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.caption = self.root / "caption.txt"
        self.caption.write_text("Approved Biophysics + AI poster", encoding="utf-8")
        self.args = SimpleNamespace(caption_file=self.caption,
                                    image_url="https://images.example.org/poster.jpg",
                                    publish=True, confirm_publish=True)
        self.graph = Mock()
        self.graph.call.side_effect = api_responses()
        self.output = io.StringIO()

    def run_flow(self):
        with patch.object(publisher, "ROOT", self.root), patch.object(
            publisher, "inspect_image", return_value={"width": 1080, "height": 1350, "sha256": "abc"}
        ), contextlib.redirect_stdout(self.output):
            publisher.run(self.args, CONFIG, self.graph)

    def test_success_receipt_and_one_publish(self):
        with patch("builtins.input", side_effect=AssertionError("No second confirmation")):
            self.run_flow()
        receipts = list((self.root / "receipts").glob("*.json"))
        self.assertEqual(len(receipts), 1)
        receipt = json.loads(receipts[0].read_text())
        self.assertEqual(receipt["media_id"], "900")
        self.assertNotIn(CONFIG["IG_ACCESS_TOKEN"], receipts[0].read_text() + self.output.getvalue())
        self.assertNotIn("image_url", receipt)
        self.assertEqual(sum(call.args[1].endswith("/media_publish")
                             for call in self.graph.call.call_args_list), 1)

    def test_dry_run_has_no_posts_or_receipts(self):
        self.args.publish = False
        self.run_flow()
        self.assertTrue(all(call.args[0] == "GET" for call in self.graph.call.call_args_list))
        self.assertFalse((self.root / "receipts").exists())
        self.assertFalse((self.root / ".attempts").exists())

    def test_username_mismatch_blocks(self):
        responses = api_responses()
        responses[1]["username"] = "wrong.account"
        self.graph.call.side_effect = responses
        with self.assertRaises(publisher.PublishError):
            self.run_flow()
        self.assertEqual(self.graph.call.call_count, 2)

    def test_page_link_mismatch_blocks(self):
        self.graph.call.side_effect = [{"id": "123", "instagram_business_account": {"id": "999"}}]
        with self.assertRaises(publisher.PublishError):
            self.run_flow()
        self.assertEqual(self.graph.call.call_count, 1)

    def test_ambiguous_publish_has_guard_no_receipt_no_retry(self):
        self.graph.call.side_effect = api_responses()[:-1] + [publisher.PublishError("timeout")]
        with self.assertRaises(publisher.AmbiguousPublish):
            self.run_flow()
        self.assertEqual(self.graph.call.call_count, 6)
        self.assertFalse((self.root / "receipts").exists())
        self.assertEqual(len(list((self.root / ".attempts").glob("*.json"))), 1)
        self.graph.call.side_effect = api_responses()
        self.graph.call.reset_mock()
        with self.assertRaises(publisher.PublishError):
            self.run_flow()
        self.assertTrue(all(call.args[0] == "GET" for call in self.graph.call.call_args_list))

    def test_missing_publish_id_is_ambiguous(self):
        self.graph.call.side_effect = api_responses()[:-1] + [{}]
        with self.assertRaises(publisher.AmbiguousPublish):
            self.run_flow()
        self.assertFalse((self.root / "receipts").exists())

    def test_one_interactive_confirmation(self):
        self.args.confirm_publish = False
        with patch("builtins.input", return_value="PUBLISH") as prompt:
            self.run_flow()
        prompt.assert_called_once()

    def test_cancel_has_no_writes(self):
        self.args.confirm_publish = False
        with patch("builtins.input", return_value="no") as prompt:
            with self.assertRaises(publisher.PublishError):
                self.run_flow()
        prompt.assert_called_once()
        self.assertTrue(all(call.args[0] == "GET" for call in self.graph.call.call_args_list))

    def test_unready_container_never_publishes(self):
        self.graph.call.side_effect = api_responses()[:4] + [{"status_code": "ERROR"}]
        with self.assertRaises(publisher.PublishError):
            self.run_flow()
        self.assertFalse((self.root / ".attempts").exists())

    def test_caption_rejections(self):
        for caption in ("", "  ", "text" * 551, "bad\x1bcaption", "#tag " * 31, "@user " * 21):
            with self.subTest(caption=caption[:20]), self.assertRaises(publisher.PublishError):
                publisher.validate_caption(caption)

    def test_url_rejections(self):
        for url in ("http://example.org/a.jpg", "https://user:pass@example.org/a.jpg",
                    "https://example.org/a.jpg?token=secret", "https://example.org/a.jpg#fragment"):
            with self.subTest(url=url), self.assertRaises(publisher.PublishError):
                publisher.validate_url(url)
        with patch.object(publisher.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(publisher.PublishError):
                publisher.validate_url("https://example.org/a.jpg")

    def test_real_jpeg_decode_without_network(self):
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), "white").save(buffer, format="JPEG")
        response = Mock()
        response.status = 200
        response.headers.get_content_type.return_value = "image/jpeg"
        response.read.return_value = buffer.getvalue()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch.object(publisher, "validate_url"), patch.object(publisher, "opener") as network:
            network.return_value.open.return_value = response
            result = publisher.inspect_image(self.args.image_url)
        self.assertEqual(result["width"], 1080)

    def test_token_in_caption_is_never_displayed(self):
        self.caption.write_text(CONFIG["IG_ACCESS_TOKEN"], encoding="utf-8")
        with self.assertRaises(publisher.PublishError):
            self.run_flow()
        self.assertNotIn(CONFIG["IG_ACCESS_TOKEN"], self.output.getvalue())
        self.graph.call.assert_not_called()


if __name__ == "__main__":
    unittest.main()