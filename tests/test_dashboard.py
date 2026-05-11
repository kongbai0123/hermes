import unittest
from pathlib import Path


class TestDashboardInteractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("hermes/api/dashboard.html").read_text(encoding="utf-8")

    def test_system_prompt_is_persisted_and_clearable(self):
        self.assertIn("hermes_system_prompt", self.html)
        self.assertIn("saveSystemPrompt", self.html)
        self.assertIn("clearSystemPrompt", self.html)

    def test_task_input_is_cleared_after_submit(self):
        self.assertIn("taskInput.value = ''", self.html)
        self.assertIn("taskInput.focus()", self.html)

    def test_phase_a_read_only_trace_components_are_present(self):
        self.assertIn("cursor: pointer", self.html)
        self.assertIn("permission-badge", self.html)
        self.assertIn("MODE: READ_ONLY", self.html)
        self.assertIn("trace-timeline", self.html)
        self.assertIn("renderTraceTimeline", self.html)
        self.assertIn("tool-result-preview", self.html)
        self.assertIn("renderToolResultPreview", self.html)

    def test_redundant_empty_or_native_titles_are_removed(self):
        self.assertNotIn('title=""', self.html)
        self.assertNotIn('title="Refresh dashboard"', self.html)


if __name__ == "__main__":
    unittest.main()
