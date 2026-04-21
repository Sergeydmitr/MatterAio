from __future__ import annotations

import unittest

from matteraio import MattermostConfig


class MattermostConfigTests(unittest.TestCase):
    def test_websocket_url_uses_ws_scheme(self) -> None:
        config = MattermostConfig(base_url="http://mattermost.example.com", token="token-123")

        self.assertEqual(
            config.websocket_url,
            "ws://mattermost.example.com/api/v4/websocket",
        )

    def test_websocket_url_uses_wss_scheme_for_https(self) -> None:
        config = MattermostConfig(
            base_url="https://mattermost.example.com/api/v4",
            token="token-123",
        )

        self.assertEqual(
            config.websocket_url,
            "wss://mattermost.example.com/api/v4/websocket",
        )
