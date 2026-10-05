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
                         "http://jarvis.home:8790/")
        self.assertIsNone(services["jellyfin"].status_url)

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
        self.assertIn("    external: true\n    name: jarvis-receipt-services\n", compose)
        self.assertNotIn("depends_on", compose)


if __name__ == "__main__":
    unittest.main()
