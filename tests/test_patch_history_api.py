import unittest
import json
import os
import time
import subprocess
from urllib.request import urlopen, Request
from urllib.error import HTTPError

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

class TestPatchHistoryAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 啟動伺服器，開啟測試模式 (動態埠)
        cls.port = get_free_port()
        cls.base_url = f"http://localhost:{cls.port}"
        cls.server_process = subprocess.Popen(
            ["python", "start_hermes.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "HERMES_PORT": str(cls.port), "HERMES_TEST_MODE": "1"}
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

    def _inject_patch(self, task_id="test-task", status="pending", changes=None):
        if changes is None:
            changes = [{"path": "test.py", "operation": "modify", "reason": "test"}]
        
        url = f"{self.base_url}/api/test/inject_patch"
        req = Request(url, data=json.dumps({"task_id": task_id, "status": status, "changes": changes}).encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/json')
        with urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))["patch_id"]

    def test_patch_lifecycle_and_history(self):
        # 1. 注入 Pending Patch
        pid_pending = self._inject_patch(task_id="pending-task")
        
        # 檢查 /api/patch/pending
        with urlopen(f"{self.base_url}/api/patch/pending") as resp:
            pending_list = json.loads(resp.read().decode('utf-8'))
            self.assertTrue(any(p["id"] == pid_pending for p in pending_list))
        
        # 檢查 /api/patch/history (不應存在)
        with urlopen(f"{self.base_url}/api/patch/history") as resp:
            history_list = json.loads(resp.read().decode('utf-8'))
            self.assertFalse(any(p["id"] == pid_pending for p in history_list))

        # 2. 注入並 Reject Patch
        pid_reject = self._inject_patch(task_id="reject-task")
        # 執行 Reject
        req = Request(f"{self.base_url}/api/patch/reject/{pid_reject}", method='POST')
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(data["status"], "rejected")

        # 檢查 /api/patch/pending (應移除)
        with urlopen(f"{self.base_url}/api/patch/pending") as resp:
            pending_list = json.loads(resp.read().decode('utf-8'))
            self.assertFalse(any(p["id"] == pid_reject for p in pending_list))

        # 檢查 /api/patch/history (應出現且為 rejected)
        with urlopen(f"{self.base_url}/api/patch/history") as resp:
            history_list = json.loads(resp.read().decode('utf-8'))
            rejected_entry = next((p for p in history_list if p["id"] == pid_reject), None)
            self.assertIsNotNone(rejected_entry)
            self.assertEqual(rejected_entry["status"], "rejected")

        # 3. 測試 Approved 不應出現在 History (剛才加固的語意)
        pid_approve = self._inject_patch(task_id="approve-task")
        # 執行 Approve
        req = Request(f"{self.base_url}/api/patch/approve/{pid_approve}", method='POST')
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIn("token", data)
        
        # 檢查 /api/patch/history (不應出現 approved，因為非終態)
        with urlopen(f"{self.base_url}/api/patch/history") as resp:
            history_list = json.loads(resp.read().decode('utf-8'))
            self.assertFalse(any(p["id"] == pid_approve for p in history_list))


    def test_applied_patch_appears_in_history(self):
        # 1. 注入 Patch (使用 create 確保一定成功)
        pid = self._inject_patch(task_id="apply-task", changes=[{"path": "test_create.py", "operation": "create", "replacement": "print(1)", "reason": "test"}])
        
        # 2. Approve 獲取 Token
        req_app = Request(f"{self.base_url}/api/patch/approve/{pid}", method='POST')
        with urlopen(req_app) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            token = data["token"]
            self.assertIsNotNone(token)
            
        # 3. Apply Patch
        apply_data = json.dumps({"patch_id": pid, "token": token}).encode('utf-8')
        req_apply = Request(f"{self.base_url}/api/patch/apply", data=apply_data, method='POST')
        req_apply.add_header('Content-Type', 'application/json')
        with urlopen(req_apply) as resp:
            self.assertEqual(resp.status, 200)
            
        # 4. 驗證不在 Pending
        with urlopen(f"{self.base_url}/api/patch/pending") as resp:
            pending_list = json.loads(resp.read().decode('utf-8'))
            self.assertFalse(any(p["id"] == pid for p in pending_list))
            
        # 5. 驗證出現在 History 且狀態為 applied
        with urlopen(f"{self.base_url}/api/patch/history") as resp:
            history_list = json.loads(resp.read().decode('utf-8'))
            applied_entry = next((p for p in history_list if p["id"] == pid), None)
            self.assertIsNotNone(applied_entry)
            self.assertEqual(applied_entry["status"], "applied")

if __name__ == "__main__":
    unittest.main()
