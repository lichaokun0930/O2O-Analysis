# Redis安装和配置指南

## 📋 Redis简介

Redis是一个高性能的内存数据存储系统，用于：
- ✅ 缓存热点数据
- ✅ 多用户共享数据
- ✅ 分布式会话管理

---

## 🪟 Windows安装Redis

### 方法1：使用Memurai（推荐）

Memurai是Redis的Windows原生版本，性能优秀。

**下载地址**：https://www.memurai.com/get-memurai

**安装步骤**：
1. 下载Memurai安装包
2. 双击安装，默认端口6379
3. 安装后自动启动服务

**验证安装**：
```powershell
# 打开PowerShell，连接Redis
redis-cli
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> exit
```

### 方法2：使用WSL + Redis

如果已安装WSL（Windows Subsystem for Linux）：

```bash
# 在WSL中安装Redis
sudo apt update
sudo apt install redis-server

# 启动Redis
sudo service redis-server start

# 测试
redis-cli ping
```

### 方法3：使用Docker

```powershell
# 拉取Redis镜像
docker pull redis:latest

# 启动Redis容器
docker run -d -p 6379:6379 --name redis redis:latest

# 连接测试
docker exec -it redis redis-cli ping
```

---

## 🐧 Linux/Mac安装Redis

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server

# 启动服务
sudo systemctl start redis-server

# 设置开机启动
sudo systemctl enable redis-server

# 检查状态
sudo systemctl status redis-server
```

### CentOS/RHEL

```bash
sudo yum install redis

# 启动服务
sudo systemctl start redis

# 设置开机启动
sudo systemctl enable redis
```

### Mac (使用Homebrew)

```bash
brew install redis

# 启动Redis
brew services start redis

# 或手动启动
redis-server
```

---

## ⚙️ Redis配置

### 基础配置文件

**Windows (Memurai)**：
- 配置文件位置：`C:\Program Files\Memurai\memurai.conf`

**Linux/Mac**：
- 配置文件位置：`/etc/redis/redis.conf`

### 推荐配置

```conf
# 绑定所有IP（如需远程访问）
bind 0.0.0.0

# 默认端口
port 6379

# 设置密码（推荐）
requirepass your_strong_password_here

# 最大内存限制（根据服务器配置）
maxmemory 1gb

# 内存淘汰策略（LRU最近最少使用）
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1      # 900秒内至少1个键改变时保存
save 300 10     # 300秒内至少10个键改变时保存
save 60 10000   # 60秒内至少10000个键改变时保存

# 日志级别
loglevel notice

# 日志文件
logfile "/var/log/redis/redis-server.log"
```

### 修改配置后重启

**Windows (Memurai)**：
```powershell
# 服务管理器中重启Memurai服务
# 或PowerShell命令
Restart-Service Memurai
```

**Linux**：
```bash
sudo systemctl restart redis-server
```

---

## 🔧 Python客户端配置

### 安装依赖

```bash
pip install redis
```

### 基本连接

```python
import redis

# 无密码连接
r = redis.Redis(host='localhost', port=6379, db=0)

# 有密码连接
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    password='your_password'
)

# 测试连接
r.ping()  # 返回True表示成功
```

### 系统中的配置

修改 `智能门店看板_Dash版.py` 中的配置：

```python
# 如果Redis有密码
REDIS_CACHE_MANAGER = get_cache_manager(
    host='localhost',
    port=6379,
    db=0,
    password='your_password',  # 添加这行
    default_ttl=1800
)
```

---

## 🚀 启动和测试

### 1. 启动Redis服务

**Windows (Memurai)**：
- 服务已自动启动
- 或在服务管理器中手动启动

**Linux/Mac**：
```bash
sudo systemctl start redis-server
```

### 2. 测试Redis连接

```python
# 运行测试脚本
python redis_cache_manager.py
```

期望输出：
```
======================================================================
 Redis缓存管理器测试
======================================================================

✅ Redis连接成功: localhost:6379/0
...
```

### 3. 启动智能门店看板

```bash
python 智能门店看板_Dash版.py
```

检查启动日志：
```
✅ Redis缓存模块已加载
✅ Redis缓存已启用 - 支持多用户数据共享
📊 缓存配置: TTL=30分钟, 自动过期
```

---

## 🛠️ 常见问题排查

### 问题1：连接被拒绝

**错误信息**：
```
⚠️  Redis连接失败，缓存功能已禁用: Connection refused
```

**解决方案**：
1. 检查Redis服务是否启动
   ```bash
   # Windows
   Get-Service Memurai
   
   # Linux
   sudo systemctl status redis-server
   ```

2. 检查端口是否正确（默认6379）
   ```bash
   netstat -an | grep 6379
   ```

3. 检查防火墙设置

### 问题2：密码认证失败

**错误信息**：
```
redis.exceptions.AuthenticationError: Authentication required
```

**解决方案**：
在代码中添加password参数：
```python
REDIS_CACHE_MANAGER = get_cache_manager(
    host='localhost',
    port=6379,
    password='your_password'
)
```

### 问题3：内存不足

**错误信息**：
```
OOM command not allowed when used memory > 'maxmemory'
```

**解决方案**：
1. 增加maxmemory配置
2. 设置淘汰策略：
   ```conf
   maxmemory-policy allkeys-lru
   ```

### 问题4：连接超时

**解决方案**：
增加超时时间：
```python
REDIS_CACHE_MANAGER = get_cache_manager(
    host='localhost',
    port=6379,
    socket_connect_timeout=5,
    socket_timeout=5
)
```

---

## 📊 监控和维护

### 使用Redis CLI监控

```bash
# 连接Redis
redis-cli

# 查看信息
127.0.0.1:6379> INFO

# 查看所有键
127.0.0.1:6379> KEYS *

# 查看键的TTL
127.0.0.1:6379> TTL key_name

# 查看内存使用
127.0.0.1:6379> INFO memory

# 清空数据库（谨慎使用）
127.0.0.1:6379> FLUSHDB
```

### 性能监控

```bash
# 实时监控命令
redis-cli --stat

# 实时监控所有命令
redis-cli monitor
```

### 日常维护

1. **定期备份**：
   ```bash
   # 手动触发RDB快照
   redis-cli BGSAVE
   ```

2. **清理过期键**：
   ```bash
   # 自动清理，无需手动操作
   # Redis会自动删除过期键
   ```

3. **检查内存使用**：
   ```bash
   redis-cli INFO memory | grep used_memory_human
   ```

---

## 🔒 安全建议

### 1. 设置强密码

```conf
# redis.conf
requirepass StrongP@ssw0rd!2024
```

### 2. 限制访问IP

```conf
# 仅允许本机访问
bind 127.0.0.1

# 允许指定IP
bind 127.0.0.1 192.168.1.100
```

### 3. 禁用危险命令

```conf
# 禁用FLUSHALL和FLUSHDB
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
```

### 4. 使用防火墙

**Windows**：
- 仅允许受信任的IP访问6379端口

**Linux**：
```bash
# 使用ufw
sudo ufw allow from 192.168.1.0/24 to any port 6379
```

---

## 📈 性能优化

### 1. 连接池

系统已自动使用Redis连接池，无需额外配置。

### 2. 持久化策略

根据需求选择：

**RDB（快照）**：
- 优点：性能好，文件小
- 缺点：可能丢失部分数据

**AOF（追加日志）**：
- 优点：数据更安全
- 缺点：文件大，恢复慢

**推荐配置**（RDB + AOF混合）：
```conf
save 900 1
appendonly yes
appendfsync everysec
```

### 3. 内存优化

```conf
# 启用压缩
list-compress-depth 1
set-max-intset-entries 512

# 限制最大内存
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

## 🎯 使用建议

### 本地开发环境

- 使用默认配置即可
- 无需设置密码
- 内存限制256MB足够

### 生产环境

- ✅ 必须设置强密码
- ✅ 限制访问IP
- ✅ 配置持久化
- ✅ 设置maxmemory（建议50%服务器内存）
- ✅ 启用监控和告警
- ✅ 定期备份

---

## 📞 获取帮助

### 官方资源

- Redis官网：https://redis.io
- Redis文档：https://redis.io/docs
- Redis命令参考：https://redis.io/commands

### 社区资源

- GitHub：https://github.com/redis/redis
- Stack Overflow：搜索"redis"标签

### Windows版本

- Memurai：https://www.memurai.com
- Redis for Windows（Microsoft维护）：https://github.com/microsoftarchive/redis

---

## ✅ 安装检查清单

- [ ] Redis服务已安装并启动
- [ ] 可以通过redis-cli连接
- [ ] Python redis包已安装
- [ ] 测试脚本运行成功
- [ ] 智能门店看板启动时显示Redis启用信息
- [ ] 加载数据时能看到Redis缓存命中日志

---

**文档版本**：v1.0  
**更新日期**：2025-11-09  
**适用系统**：Windows/Linux/Mac
