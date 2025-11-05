"""
数据库快速配置工具
"""
import os
from pathlib import Path

print("="*80)
print("  PostgreSQL Database Setup")
print("="*80)

# 获取配置信息
print("\nPlease enter database configuration:")
db_user = input("Database user (default: postgres): ").strip() or "postgres"
db_password = input("Database password: ").strip()
db_host = input("Database host (default: localhost): ").strip() or "localhost"
db_port = input("Database port (default: 5432): ").strip() or "5432"
db_name = "o2o_dashboard"

# 构建DATABASE_URL
database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# 生成.env文件
env_content = f"""# Database Configuration
DATABASE_URL={database_url}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8050

# Security (change in production)
SECRET_KEY=dev-secret-key-change-in-production

# AI Configuration (optional)
# ZHIPU_API_KEY=your_zhipu_api_key
# QWEN_API_KEY=your_qwen_api_key
# GEMINI_API_KEY=your_gemini_api_key
"""

# 写入.env文件
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("\n" + "="*80)
print("  Configuration Saved!")
print("="*80)
print(f"\nDatabase: {db_name}")
print(f"User: {db_user}")
print(f"Host: {db_host}:{db_port}")
print(f"\nConfiguration file: .env")
print("\nNext steps:")
print("  1. Create database:")
print(f"     psql -U {db_user} -c \"CREATE DATABASE {db_name};\"")
print("  2. Initialize tables:")
print("     python database/migrate.py")
print("  3. Start backend:")
print("     python backend/main.py")
print("\n" + "="*80)
