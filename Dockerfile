# 订单数据看板 - 后端 Dockerfile
# 基于 Python 3.11 构建
# 支持千万级数据优化（DuckDB + Parquet）

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    DEBUG=false \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装 Python 依赖（包含 DuckDB、PyArrow、APScheduler）
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/app ./app
COPY database ./database

# 创建数据目录（Parquet 存储）
RUN mkdir -p /app/data/raw /app/data/aggregated /app/data/metadata

# 暴露端口
EXPOSE 8080

# 启动命令 - 使用 Gunicorn + Uvicorn workers（Linux 下性能最佳）
# workers 数量根据 CPU 核心数调整，建议 2-4 倍核心数
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
