from __future__ import annotations

import unittest

from afterglow.api import app
from afterglow.interactive_surface import build_check_in_demo_html
from afterglow.product_surface import build_founder_demo_html


class ProductSurfaceTests(unittest.TestCase):
    def test_founder_surface_route_is_registered(self) -> None:
        paths = {route.path for route in app.routes}
        self.assertIn("/demo/founder-surface", paths)
        self.assertIn("/demo/check-in", paths)
        self.assertIn("/demo/check-in/session", paths)

    def test_founder_surface_html_covers_product_story_and_api_flow(self) -> None:
        html = build_founder_demo_html()

        self.assertIn("Why this is the first feature", html)
        self.assertIn("5 charged interested open yes", html)
        self.assertIn("POST /matches/register", html)
        self.assertIn("Customer research framing", html)

    def test_interactive_surface_html_uses_live_api_flow(self) -> None:
        html = build_check_in_demo_html()

        self.assertIn("POST /debriefs", html)
        self.assertIn("/demo/check-in/session", html)
        self.assertIn("Operator snapshot", html)
        self.assertIn("Start Fresh Demo", html)


if __name__ == "__main__":
    unittest.main()
