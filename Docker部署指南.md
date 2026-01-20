# 订单数据看板 - Docker 部署指南

本文档介绍如何使用 Docker 部署订单数据看板系统，支持 300+ 并发用户。

---

## 一、架构概览

```
                                    ┌─────────────────────────────────────┐
                                    │           用户浏览器                 │
                                    │     http://服务器IP 或 域名          │
                                    └──────────────┬──────────────────────┘
                                                   │
                                    ┌──────────────▼──────────────────────┐
                                    │         Nginx (端口 80)              │
                                    │   负载均衡 + 静态资源 + API代理       │
                                    └──────────────┬──────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
           ┌────────▼────────┐           ┌────────▼────────┐           ┌────────▼────────┐
           │   静态资源       │           │   API 请求       │           │   WebSocket     │
           │   (React 前端)   │           │   /api/*        │           │   (未来扩展)     │
           └─────────────────┘           └────────┬────────┘           └─────────────────┘
                                                  │
                                    ┌─────────────▼─────────────┐
                                    │      FastAPI 后端          │
                                    │   Gunicorn + 4 Workers    │
                                    └─────────────┬─────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
           ┌────────▼────────┐           ┌───────▼────────┐           ┌────────▼────────┐
           │   PostgreSQL    │           │     Redis      │           │   预聚合表       │
           │   数据库         │           │     缓存       │           │   (性能优化)     │
           └─────────────────┘           └────────────────┘           └─────────────────┘
```

---

## 二、环境要求

### 服务器配置建议

| 并发用户 | CPU | 内存 | 磁盘 |
|---------|-----|------|------|
| 50 人   | 2核 | 4GB  | 50GB |
| 100 人  | 4核 | 8GB  | 100GB |
| 300 人  | 8核 | 16GB | 200GB |

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+

---

## 三、快速部署（5分钟）

### 1. 安装 Docker

**Ubuntu/Debian:**
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo apt install docker-compose-plugin
```

**CentOS/RHEL:**
```bash
# 安装 Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows:**
1. 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. 安装并启动
3. 在设置中启用 WSL2 后端

### 2. 上传代码

将整个 `O2O-Analysis` 文件夹上传到服务器：
```bash
# 使用 scp
scp -r O2O-Analysis user@服务器IP:/home/user/

# 或使用 rsync（推荐，支持断点续传）
rsync -avz --progress O2O-Analysis user@服务器IP:/home/user/
```

### 3. 一键启动

```bash
cd O2O-Analysis

# 构建并启动所有服务
docker-compose up -d --build

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问系统

打开浏览器访问：`http://服务器IP`

---

## 四、数据库迁移

如果你有现有的 PostgreSQL 数据，需要迁移：

### 方法一：导出导入

```bash
# 在原服务器导出
pg_dump -U postgres -d o2o_analysis > backup.sql

# 复制到新服务器
scp backup.sql user@新服务器:/home/user/

# 在新服务器导入
docker exec -i o2o-postgres psql -U postgres -d o2o_analysis < backup.sql
```

### 方法二：直接连接外部数据库

修改 `docker-compose.yml`，注释掉 db 服务，修改 backend 的环境变量：
```yaml
backend:
  environment:
    - DATABASE_URL=postgresql://用户名:密码@外部数据库IP:5432/数据库名
```

---

## 五、常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启某个服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 进入容器
docker exec -it o2o-backend bash
docker exec -it o2o-postgres psql -U postgres
```

### 更新部署

```bash
# 拉取最新代码后
docker-compose down
docker-compose up -d --build
```

### 数据备份

```bash
# 备份数据库
docker exec o2o-postgres pg_dump -U postgres o2o_analysis > backup_$(date +%Y%m%d).sql

# 备份 Redis
docker exec o2o-redis redis-cli BGSAVE
docker cp o2o-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

---

## 六、性能调优

### 1. 增加后端 Workers

修改 `Dockerfile` 中的 workers 数量：
```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--workers", "8", \  # 改成 CPU核心数 * 2
     ...
```

### 2. 水平扩展（多实例）

修改 `docker-compose.yml`：
```yaml
backend:
  deploy:
    replicas: 4  # 启动 4 个后端实例
```

然后修改 `nginx.conf` 添加更多上游服务器。

### 3. 数据库优化

```bash
# 进入 PostgreSQL
docker exec -it o2o-postgres psql -U postgres

# 执行优化
VACUUM ANALYZE;
REINDEX DATABASE o2o_analysis;
```

---

## 七、监控与告警

### 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 输出示例：
# CONTAINER    CPU %   MEM USAGE / LIMIT     MEM %
# o2o-backend  15.2%   512MiB / 4GiB         12.5%
# o2o-frontend 0.1%    32MiB / 256MiB        12.5%
# o2o-postgres 5.3%    256MiB / 1GiB         25.0%
# o2o-redis    0.5%    64MiB / 256MiB        25.0%
```

### 健康检查

```bash
# 检查后端 API
curl http://localhost/api/health

# 检查前端
curl http://localhost/health
```

---

## 八、故障排查

### 问题：容器启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 常见原因：
# 1. 端口被占用 → 修改 docker-compose.yml 中的端口
# 2. 数据库连接失败 → 检查 DATABASE_URL
# 3. 依赖未安装 → 重新构建 docker-compose build --no-cache
```

### 问题：访问慢

```bash
# 检查后端响应时间
curl -w "@curl-format.txt" http://localhost/api/health

# 检查数据库慢查询
docker exec -it o2o-postgres psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### 问题：内存不足

```bash
# 限制容器内存
# 修改 docker-compose.yml
backend:
  deploy:
    resources:
      limits:
        memory: 2G
```

---

## 九、安全建议

### 1. 修改默认密码

```yaml
# docker-compose.yml
db:
  environment:
    - POSTGRES_PASSWORD=你的强密码
```

### 2. 启用 HTTPS

使用 Let's Encrypt 免费证书：
```bash
# 安装 certbot
apt install certbot

# 获取证书
certbot certonly --standalone -d your-domain.com

# 修改 nginx.conf 启用 SSL
```

### 3. 防火墙设置

```bash
# 只开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## 十、云服务器部署

### 阿里云 ECS

1. 购买 ECS 实例（推荐 4核8G）
2. 安全组开放 80、443 端口
3. 按上述步骤部署

### 腾讯云 CVM

1. 购买 CVM 实例
2. 安全组配置
3. 按上述步骤部署

### AWS EC2

1. 启动 EC2 实例（推荐 t3.large）
2. 配置 Security Group
3. 按上述步骤部署

---

## 附录：文件说明

| 文件 | 说明 |
|-----|------|
| `Dockerfile` | 后端镜像构建文件 |
| `Dockerfile.frontend` | 前端镜像构建文件 |
| `docker-compose.yml` | 服务编排文件 |
| `nginx.conf` | Nginx 配置 |
| `.dockerignore` | Docker 构建忽略文件 |

---

**有问题？** 查看日志 `docker-compose logs -f` 或联系开发团队。
