import os
from pathlib import Path
import unittest
from unittest.mock import patch

from jarvis_console.config import load_config


ROOT = Path(__file__).resolve().parent.parent


class ConfigTests(unittest.TestCase):
    def test_defaults_keep_internal_and_launch_urls_separate(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
        services = {service.key: service for service in config.services}
        self.assertEqual(services["triviarom"].status_url,
                         "http://triviarom-service:8080/health")
        self.assertEqual(services["triviarom"].launch_url,
                         "http://trivia.jarvis.home/")
        self.assertEqual(services["receipt"].name, "Receipt Service")
        self.assertIsNone(services["receipt"].launch_url)
        self.assertEqual(services["receipt"].secondary_links, ((
            "GitHub", "https://github.com/e-rnest/receipt-service",
        ),))
        self.assertIsNone(services["jellyfin"].status_url)
        self.assertEqual(config.morning_brief_url,
                         "http://receipt-service:8080/print/morning")
        self.assertEqual(services["label"].launch_url,
                         "http://label.jarvis.home/print")
        self.assertEqual(services["jeopardy"].launch_url,
                         "http://jeopardy.home/")
        self.assertEqual(services["blacktorrent"].status_url,
                         "http://192.168.1.100:8080/")
        self.assertEqual(services["blacktorrent"].launch_url,
                         "http://192.168.1.100:8080/")
        self.assertEqual(services["jellyfin"].launch_url,
                         "http://jellyfin.home")
        self.assertEqual(services["jellyfin"].secondary_links, ((
            "TV Guide",
            "http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1",
        ),))

    def test_invalid_timeout_is_rejected(self):
        with patch.dict(os.environ, {"STATUS_TIMEOUT_SECONDS": "60"}, clear=True):
            with self.assertRaisesRegex(ValueError, "between 0.1 and 10"):
                load_config()

    def test_compose_preserves_network_and_port_contract(self):
        compose = (ROOT / "compose.yaml").read_text()
        self.assertTrue(compose.startswith("name: jarvis-console\n"))
        self.assertIn("  jarvis-console:\n", compose)
        self.assertIn("    container_name: jarvis-console\n", compose)
        self.assertIn('${CONSOLE_HOST_PORT:-8791}:8080', compose)
        self.assertIn("MORNING_BRIEF_URL: ${MORNING_BRIEF_URL:-http://receipt-service:8080/print/morning}",
                      compose)
        self.assertIn("RECEIPT_REPOSITORY_URL: ${RECEIPT_REPOSITORY_URL:-https://github.com/e-rnest/receipt-service}",
                      compose)
        self.assertIn("BLACKTORRENT_STATUS_URL: ${BLACKTORRENT_STATUS_URL:-http://192.168.1.100:8080/}",
                      compose)
        self.assertIn("JELLYFIN_TV_GUIDE_URL: ${JELLYFIN_TV_GUIDE_URL:-http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1}",
                      compose)
        self.assertIn("    external: true\n    name: jarvis-receipt-services\n", compose)
        self.assertNotIn("depends_on", compose)


if __name__ == "__main__":
    unittest.main()
