import unittest
from pathlib import Path


class TestDashboardStaticModules(unittest.TestCase):
    def setUp(self):
        self.html = Path("hermes/api/dashboard.html").read_text(encoding="utf-8")

    def test_dashboard_loads_no_build_static_modules(self):
        expected = [
            "static/api.js",
            "static/workspace.js",
            "static/renderers.js",
            "static/management.js",
            "static/boot.js",
        ]

        for src in expected:
            with self.subTest(src=src):
                self.assertIn(f'<script src="{src}" defer></script>', self.html)
                self.assertTrue(Path("hermes/api", src).exists())


if __name__ == "__main__":
    unittest.main()
