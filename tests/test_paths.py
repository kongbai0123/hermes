import os
import unittest
from pathlib import Path

from hermes.memory.long_term import SemanticMemory, UserModeling
from hermes.memory.procedural import ProceduralMemory
from tests.support import test_workspace


class TestProjectPaths(unittest.TestCase):
    def setUp(self):
        self.workspace = test_workspace("paths_workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def test_memory_defaults_write_under_current_workspace_root(self):
        previous = os.environ.get("HERMES_WORKSPACE")
        os.environ["HERMES_WORKSPACE"] = str(self.workspace)
        try:
            semantic = SemanticMemory()
            procedural = ProceduralMemory()
            user = UserModeling()
        finally:
            if previous is None:
                os.environ.pop("HERMES_WORKSPACE", None)
            else:
                os.environ["HERMES_WORKSPACE"] = previous

        self.assertEqual(semantic.storage_path, str(self.workspace / "optimization" / "memory_semantic.json"))
        self.assertEqual(procedural.storage_path, str(self.workspace / "optimization" / "memory_procedural.json"))
        self.assertEqual(user.storage_path, str(self.workspace / "optimization" / "user_model.json"))

    def test_memory_store_creates_optimization_directory(self):
        previous = os.environ.get("HERMES_WORKSPACE")
        os.environ["HERMES_WORKSPACE"] = str(self.workspace)
        try:
            memory = SemanticMemory()
            memory.store("hello", {"type": "test"})
        finally:
            if previous is None:
                os.environ.pop("HERMES_WORKSPACE", None)
            else:
                os.environ["HERMES_WORKSPACE"] = previous

        self.assertTrue((self.workspace / "optimization" / "memory_semantic.json").is_file())


if __name__ == "__main__":
    unittest.main()
