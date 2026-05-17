# ==========================================
# ⚡ Hermes Docker Sandbox Engine
# ==========================================
FROM python:3.12-slim

# 安裝必要系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HERMES_WORKSPACE=/app \
    HERMES_PORT=8000

WORKDIR /app

# 複製專案檔案 (排除不需要的暫存檔)
COPY . /app

# 建立 non-root 使用者以保證 Sandbox 內部安全邊界，符合 L5 安全限制
RUN useradd -u 1000 -m hermes && \
    chown -R hermes:hermes /app

USER hermes

# 暴露服務埠
EXPOSE 8000

# 啟動命令
CMD ["python", "start_hermes.py"]
