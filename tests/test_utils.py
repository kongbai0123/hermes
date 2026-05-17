import time
from urllib.request import urlopen

def wait_for_server(base_url, timeout=15):
    """
    Polling 等待 server 就緒，取代固定 sleep。
    用於解決 CI 環境下的 HTTP Integration Test race condition。
    """
    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/api/status", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception as exc:
            last_error = exc
            time.sleep(0.3)

    print(f"\n[CI DEBUG] Server failed to start or respond in time. Last error: {last_error}")
    return False
