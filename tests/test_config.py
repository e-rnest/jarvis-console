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
        self.assertIsNone(services["homeassistant"].status_url)
        self.assertEqual(services["homeassistant"].launch_url,
                         "http://ha.jarvis.home/")
        self.assertEqual(services["homeassistant"].secondary_links, (
            ("Short alias", "http://ha.home/"),
            ("Direct", "http://192.168.1.100:8123/"),
        ))
        self.assertEqual(services["triviarom"].status_url,
                         "http://triviarom-service:8080/health")
        self.assertEqual(services["triviarom"].launch_url,
                         "http://trivia.jarvis.home/")
        self.assertEqual(services["wallboard"].status_url,
                         "http://wallboard.home/health")
        self.assertEqual(services["wallboard"].launch_url,
                         "http://wallboard.home/")
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
        self.assertEqual(services["label"].secondary_links, (
            ("Quick Labels", "http://label.jarvis.home/labels"),
            ("Fridge", "http://label.jarvis.home/inventory"),
            ("Freezer", "http://label.jarvis.home/inventory/frozen"),
        ))
        self.assertEqual(services["manifest"].status_url,
                         "http://manifest.home/health")
        self.assertEqual(services["manifest"].launch_url,
                         "http://manifest.home/")
        self.assertEqual(services["jeopardy"].launch_url,
                         "http://jeopardy.home/")
        self.assertEqual(services["blacktorrent"].status_url,
                         "http://192.168.1.100:8080/")
        self.assertEqual(services["blacktorrent"].launch_url,
                         "http://blacktorrent.home/")
        self.assertEqual(services["blacktorrent"].secondary_links, ((
            "Backup", "http://blacktorrent.jarvis.home/",
        ),))
        self.assertEqual(services["jellyfin"].launch_url,
                         "http://jellyfin.home")
        self.assertEqual(services["jellyfin"].secondary_links, ((
            "TV Guide",
            "http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1",
        ),))
        self.assertIsNone(services["semavox"].status_url)
        self.assertEqual(services["semavox"].name, "Semavox")
        self.assertEqual(services["semavox"].launch_url,
                         "http://semavox.home")
        self.assertEqual(services["semavox"].secondary_links, (
            ("Fixed IP", "http://192.168.1.80"),
            ("GitHub", "https://github.com/e-rnest/semavox"),
        ))

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
        self.assertIn("HOME_ASSISTANT_LAUNCH_URL: ${HOME_ASSISTANT_LAUNCH_URL:-http://ha.jarvis.home/}",
                      compose)
        self.assertIn("BLACKTORRENT_STATUS_URL: ${BLACKTORRENT_STATUS_URL:-http://192.168.1.100:8080/}",
                      compose)
        self.assertIn("MANIFEST_STATUS_URL: ${MANIFEST_STATUS_URL:-http://manifest.home/health}",
                      compose)
        self.assertIn("MANIFEST_LAUNCH_URL: ${MANIFEST_LAUNCH_URL:-http://manifest.home/}",
                      compose)
        self.assertIn("WALLBOARD_STATUS_URL: ${WALLBOARD_STATUS_URL:-http://wallboard.home/health}",
                      compose)
        self.assertIn("WALLBOARD_LAUNCH_URL: ${WALLBOARD_LAUNCH_URL:-http://wallboard.home/}",
                      compose)
        self.assertIn("LABEL_QUICK_LABELS_URL: ${LABEL_QUICK_LABELS_URL:-http://label.jarvis.home/labels}",
                      compose)
        self.assertIn("BLACKTORRENT_LAUNCH_URL: ${BLACKTORRENT_LAUNCH_URL:-http://blacktorrent.home/}",
                      compose)
        self.assertIn("BLACKTORRENT_BACKUP_URL: ${BLACKTORRENT_BACKUP_URL:-http://blacktorrent.jarvis.home/}",
                      compose)
        self.assertIn("JELLYFIN_TV_GUIDE_URL: ${JELLYFIN_TV_GUIDE_URL:-http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1}",
                      compose)
        self.assertIn("SEMAVOX_LAUNCH_URL: ${SEMAVOX_LAUNCH_URL:-http://semavox.home}",
                      compose)
        self.assertIn("SEMAVOX_FALLBACK_URL: ${SEMAVOX_FALLBACK_URL:-http://192.168.1.80}",
                      compose)
        self.assertIn("SEMAVOX_REPOSITORY_URL: ${SEMAVOX_REPOSITORY_URL:-https://github.com/e-rnest/semavox}",
                      compose)
        self.assertIn("    external: true\n    name: jarvis-receipt-services\n", compose)
        self.assertNotIn("depends_on", compose)


if __name__ == "__main__":
    unittest.main()
