# ==========================================
# ⚡ Hermes Docker Sandbox Engine
# ==========================================
FROM python:3.11-slim

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HERMES_WORKSPACE=/workspace \
    HERMES_AUTONOMY_LEVEL=L2

# 建立一個非 root 使用者，確保 L5 腳本執行時的安全性
RUN groupadd -r hermesgroup && useradd -r -g hermesgroup -d /workspace -s /bin/bash hermes

# 安裝基礎依賴 (如 git, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 先複製 requirements 以利用 Docker 快取
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼
COPY . .

# 確保 hermes 使用者擁有資料夾權限
RUN chown -R hermes:hermesgroup /workspace

# 切換到非 root 使用者
USER hermes

# 預設執行 Validator 作為健康檢查或啟動 Agent API
CMD ["python", "scripts/validate_autonomy.py", "--level", "ALL"]
