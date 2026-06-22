FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết cho PostgreSQL (psycopg2/asyncpg)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Lệnh chạy FastAPI
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
