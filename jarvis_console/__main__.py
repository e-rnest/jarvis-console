"""Jarvis Console process entry point."""

import logging

from .config import load_config
from .http import make_server


def main() -> None:
    config = load_config()
    logging.basicConfig(level=logging.INFO)
    with make_server(config) as server:
        logging.info("Serving Jarvis Console on %s:%d", config.host, server.server_port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
