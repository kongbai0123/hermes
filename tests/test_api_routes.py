import unittest
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import subprocess
import time
import os
import signal

import socket

def wait_for_server(base_url, timeout=10):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/api/status", timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Server did not become ready at {base_url}: {last_error}")

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class TestAPIRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 啟動伺服器進行測試 (動態埠)
        cls.port = get_free_port()
        cls.base_url = f"http://localhost:{cls.port}"
        cls.server_process = subprocess.Popen(
            ["python", "start_hermes.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "HERMES_PORT": str(cls.port)}
        )
        try:
            wait_for_server(cls.base_url)
        except Exception as e:
            # 讀取部分輸出以便 CI 除錯
            out, err = cls.server_process.communicate(timeout=1)
            print(f"\n[DEBUG] Server stdout: {out.decode('utf-8', errors='replace')}")
            print(f"[DEBUG] Server stderr: {err.decode('utf-8', errors='replace')}")
            cls.server_process.terminate()
            raise e

    @classmethod
    def tearDownClass(cls):
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()

    def test_patch_pending_json(self):
        url = f"{self.base_url}/api/patch/pending"
        with urlopen(url) as response:
            self.assertEqual(response.getheader('Content-Type'), 'application/json; charset=utf-8')
            data = json.loads(response.read().decode('utf-8'))
            self.assertIsInstance(data, list)

    def test_provider_health_json(self):
        url = f"{self.base_url}/api/providers/health"
        with urlopen(url) as response:
            self.assertEqual(response.getheader('Content-Type'), 'application/json; charset=utf-8')
            data = json.loads(response.read().decode('utf-8'))
            self.assertIn("ollama", data)
            self.assertIn("mock", data)

    def test_unknown_api_json_404(self):
        url = f"{self.base_url}/api/not-exist-route"
        try:
            urlopen(url)
            self.fail("Should have raised 404")
        except HTTPError as e:
            self.assertEqual(e.code, 404)
            self.assertEqual(e.headers.get('Content-Type'), 'application/json; charset=utf-8')
            data = json.loads(e.read().decode('utf-8'))
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"]["code"], "API_ROUTE_NOT_FOUND")

if __name__ == "__main__":
    unittest.main()
