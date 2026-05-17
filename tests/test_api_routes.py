import unittest
import subprocess
import os
import json
import socket
from urllib.request import urlopen
from tests.test_utils import wait_for_server

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class TestAPIRoutes(unittest.TestCase):
    """
    HTTP Integration Tests for Hermes API Routes.
    使用 wait_for_server 確保 CI 環境下的高穩定性。
    """
    
    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        cls.base_url = f"http://localhost:{cls.port}"
        cls.process = None

        env = os.environ.copy()
        env["HERMES_PORT"] = str(cls.port)
        
        # 啟動 Hermes Server
        cls.process = subprocess.Popen(
            ["python", "start_hermes.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )

        # 使用動態 Polling 取代脆弱的 time.sleep()
        if not wait_for_server(cls.base_url, timeout=20):
            stdout, stderr = cls.process.communicate(timeout=5)
            print("\n=== SERVER STDOUT ===")
            print(stdout[:2000] if stdout else "No stdout")
            print("\n=== SERVER STDERR ===")
            print(stderr[:2000] if stderr else "No stderr")
            raise RuntimeError("Server did not become ready in time for integration tests.")

    @classmethod
    def tearDownClass(cls):
        if cls.process:
            cls.process.terminate()
            try:
                cls.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.process.kill()

    def test_status_endpoint(self):
        """測試伺服器狀態端點是否正常回應"""
        with urlopen(f"{self.base_url}/api/status") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
            self.assertIn("agent_id", data)
            self.assertTrue("current_state" in data or "status" in data)

    def test_providers_health(self):
        """測試模型供應商健康檢查端點"""
        with urlopen(f"{self.base_url}/api/providers/health") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
            self.assertTrue(isinstance(data, dict))
