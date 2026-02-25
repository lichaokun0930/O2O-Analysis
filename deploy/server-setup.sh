#!/bin/bash
# ============================================================
# O2O 订单数据看板 - 云服务器初始化脚本
# 
# 适用于: Ubuntu 22.04 / Debian 12
# 
# 使用方法:
#   1. SSH 登录到云服务器
#   2. 上传此脚本: scp server-setup.sh root@your-server:/root/
#   3. 运行: chmod +x server-setup.sh && ./server-setup.sh
# ============================================================

set -e

echo "============================================================"
echo "  O2O 订单数据看板 - 服务器初始化"
echo "============================================================"
echo ""

# 配置
APP_NAME="o2o-analysis"
APP_DIR="/opt/$APP_NAME"
APP_USER="o2o"
PYTHON_VERSION="3.11"
NODE_VERSION="20"
BACKEND_PORT=8080

# ==========================================
# 1. 系统更新
# ==========================================
echo "[1/8] 更新系统..."
apt update && apt upgrade -y

# ==========================================
# 2. 安装基础依赖
# ==========================================
echo "[2/8] 安装基础依赖..."
apt install -y \
    curl wget git vim \
    build-essential \
    software-properties-common \
    nginx \
    redis-server \
    postgresql postgresql-contrib \
    supervisor \
    certbot python3-certbot-nginx

# ==========================================
# 3. 安装 Python
# ==========================================
echo "[3/8] 安装 Python $PYTHON_VERSION..."
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev

# ==========================================
# 4. 安装 Node.js
# ==========================================
echo "[4/8] 安装 Node.js $NODE_VERSION..."
curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
apt install -y nodejs

# ==========================================
# 5. 创建应用用户和目录
# ==========================================
echo "[5/8] 创建应用目录..."
useradd -r -s /bin/false $APP_USER 2>/dev/null || true
mkdir -p $APP_DIR/{backend,frontend,logs}
chown -R $APP_USER:$APP_USER $APP_DIR

# 创建 Python 虚拟环境
cd $APP_DIR
python${PYTHON_VERSION} -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# ==========================================
# 6. 配置 PostgreSQL
# ==========================================
echo "[6/8] 配置 PostgreSQL..."
sudo -u postgres psql << EOF
CREATE USER o2o WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE o2o_analysis OWNER o2o;
GRANT ALL PRIVILEGES ON DATABASE o2o_analysis TO o2o;
EOF

# ==========================================
# 7. 配置 Nginx
# ==========================================
echo "[7/8] 配置 Nginx..."
cat > /etc/nginx/sites-available/$APP_NAME << 'NGINX'
server {
    listen 80;
    server_name _;  # 改成你的域名
    
    # 前端静态文件
    root /var/www/html;
    index index.html;
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ==========================================
# 8. 配置 Systemd 服务
# ==========================================
echo "[8/8] 配置后端服务..."
cat > /etc/systemd/system/o2o-backend.service << SERVICE
[Unit]
Description=O2O Analysis Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/.venv/bin"
Environment="PYTHONPATH=$APP_DIR:$APP_DIR/backend/app"
Environment="ENVIRONMENT=production"
Environment="DEBUG=false"
ExecStart=$APP_DIR/.venv/bin/python -m hypercorn app.main:app --bind 0.0.0.0:$BACKEND_PORT --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable o2o-backend
systemctl enable nginx
systemctl enable redis-server
systemctl enable postgresql

# ==========================================
# 完成
# ==========================================
echo ""
echo "============================================================"
echo "  ✅ 服务器初始化完成!"
echo "============================================================"
echo ""
echo "  下一步:"
echo "  1. 修改 PostgreSQL 密码: /etc/postgresql/*/main/pg_hba.conf"
echo "  2. 配置 .env 文件: $APP_DIR/backend/.env"
echo "  3. 上传代码后启动: systemctl start o2o-backend"
echo "  4. (可选) 配置 SSL: certbot --nginx -d your-domain.com"
echo ""
echo "  服务管理:"
echo "    systemctl status o2o-backend  # 查看状态"
echo "    systemctl restart o2o-backend # 重启后端"
echo "    journalctl -u o2o-backend -f  # 查看日志"
echo ""
