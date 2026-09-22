# ===== Backend（FastAPI）镜像 =====
FROM python:3.10-slim

WORKDIR /app

# 先复制依赖清单，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个 rag_server 代码
COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
