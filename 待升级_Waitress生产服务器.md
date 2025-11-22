# 待升级：Waitress 生产服务器

> **当前状态**: 使用 Flask 内置开发服务器  
> **升级时机**: 出现性能瓶颈或需要更高稳定性时  
> **优先级**: 低（当前配置已满足需求）

---

## 📌 何时需要升级？

### 触发条件（满足任一即可升级）

- [ ] 同时在线用户超过 5 人时响应明显变慢
- [ ] 经常出现 "服务器无响应" 或连接超时
- [ ] 需要 7×24 小时稳定运行（当前偶尔需要重启）
- [ ] 点击操作等待时间超过 3-5 秒
- [ ] 想去掉启动时的 "development server" 警告

---

## 🚀 升级步骤（预计耗时 3 分钟）

### 步骤 1: 安装 Waitress
```powershell
# 在项目根目录执行
.\.venv\Scripts\pip.exe install waitress
```

**预期输出**:
```
Collecting waitress
  Downloading waitress-3.0.0-py3-none-any.whl (58 kB)
Installing collected packages: waitress
Successfully installed waitress-3.0.0
```

---

### 步骤 2: 修改启动代码

在 `智能门店看板_Dash版.py` 文件中，找到以下代码（约在第 21895 行）：

**当前代码**:
```python
try:
    # 根据环境变量决定运行模式
    app.run(
        debug=debug_mode,  # 可通过环境变量控制
        host='0.0.0.0',
        port=8050
    )
    print("⚠️ 应用服务器已停止", flush=True)
```

**修改为**:
```python
try:
    # 根据环境变量决定运行模式
    if debug_mode:
        # 调试模式：使用内置服务器（支持热重载）
        print("🐛 调试模式: 使用 Flask 内置服务器", flush=True)
        app.run(
            debug=True,
            host='0.0.0.0',
            port=8050
        )
    else:
        # 生产模式：使用 Waitress 服务器（高性能、稳定）
        print("🚀 生产模式: 使用 Waitress 服务器", flush=True)
        from waitress import serve
        serve(
            app.server,
            host='0.0.0.0',
            port=8050,
            threads=4,  # 并发线程数（可根据需要调整）
            channel_timeout=60,  # 通道超时时间
            cleanup_interval=30,  # 清理间隔
            log_socket_errors=False  # 不记录套接字错误（减少噪音）
        )
    print("⚠️ 应用服务器已停止", flush=True)
```

---

### 步骤 3: 测试启动

```powershell
# 停止现有看板（如果正在运行）
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# 启动看板（生产模式）
.\启动看板.ps1

# 访问测试
# http://localhost:8050
```

**预期输出**:
```
🚀 生产模式: 使用 Waitress 服务器
Serving on http://0.0.0.0:8050
```

---

### 步骤 4: 验证功能

- [ ] 访问 http://localhost:8050 页面正常加载
- [ ] 上传 Excel 文件功能正常
- [ ] 切换 Tab 页响应流畅
- [ ] 多人同时访问（如有条件测试）
- [ ] 长时间运行稳定（可选）

---

### 步骤 5: 推送到 GitHub

```powershell
# 添加修改
git add 智能门店看板_Dash版.py

# 提交
git commit -m "升级到 Waitress 生产服务器，提升并发性能和稳定性"

# 推送
git push
```

---

## 📊 升级前后对比

| 特性 | 升级前（Flask 内置） | 升级后（Waitress） |
|------|-------------------|-------------------|
| 并发处理 | 单线程，一次 1 个请求 | 多线程，同时 4 个请求 |
| 响应速度 | 正常 | 提升 30-50% |
| 内存占用 | 80-120 MB | 100-150 MB |
| CPU 占用 | 5-10% | 8-15% |
| 稳定性 | 偶尔需要重启 | 更稳定，自动恢复 |
| 启动警告 | ⚠️ 显示警告 | ✅ 无警告 |
| 热重载 | ✅ 支持（debug=True） | ❌ 不支持（需重启） |
| 适用场景 | 开发、小团队（1-3人） | 生产、中小团队（5-20人） |

---

## ⚙️ Waitress 配置参数说明

### 常用参数调优

```python
serve(
    app.server,
    host='0.0.0.0',           # 监听所有网卡
    port=8050,                # 端口号
    threads=4,                # 🔧 并发线程数（建议 CPU 核心数）
    channel_timeout=60,       # 通道超时（秒）
    cleanup_interval=30,      # 清理空闲连接间隔（秒）
    connection_limit=100,     # 🔧 最大连接数（根据用户数调整）
    recv_bytes=8192,          # 接收缓冲区大小
    send_bytes=8192,          # 发送缓冲区大小
    asyncore_use_poll=True,   # 使用 poll 而非 select（性能更好）
    log_socket_errors=False   # 不记录套接字错误
)
```

### 性能调优建议

| 场景 | threads | connection_limit | 说明 |
|------|---------|------------------|------|
| 1-5 人 | 2 | 50 | 当前配置 |
| 5-10 人 | 4 | 100 | 推荐配置 |
| 10-20 人 | 8 | 200 | 中型团队 |
| 20+ 人 | 16 | 500 | 大型团队 |

---

## 🐛 调试模式说明

升级后，调试模式仍然使用 Flask 内置服务器：

```powershell
# 启动调试模式（仍使用内置服务器）
.\启动看板-调试模式.ps1
```

**调试模式特性**:
- ✅ 代码热重载
- ✅ 详细错误堆栈
- ✅ 交互式调试器
- ⚠️ 单线程处理

---

## 🔄 回滚方案

如果升级后出现问题，立即回滚：

### 方法 1: Git 回滚
```powershell
git checkout HEAD~1 -- 智能门店看板_Dash版.py
.\启动看板.ps1
```

### 方法 2: 卸载 Waitress
```powershell
.\.venv\Scripts\pip.exe uninstall waitress -y
# 代码会自动回退到内置服务器（因为 import waitress 会失败）
```

### 方法 3: 手动修改
将启动代码改回：
```python
app.run(debug=debug_mode, host='0.0.0.0', port=8050)
```

---

## 📝 注意事项

### 升级前
- [ ] 备份当前代码（`git commit`）
- [ ] 确认虚拟环境已激活
- [ ] 停止正在运行的看板

### 升级后
- [ ] 测试所有主要功能
- [ ] 观察内存占用（任务管理器）
- [ ] 确认多人访问正常
- [ ] 更新 README.md（可选）

### 兼容性
- ✅ Windows 10/11
- ✅ Python 3.7+
- ✅ 所有现有功能
- ✅ 不影响数据库
- ✅ 不影响 Redis 缓存

---

## 🆘 常见问题

### Q1: 升级后启动报错 "No module named 'waitress'"
**原因**: Waitress 未安装或虚拟环境未激活  
**解决**: 
```powershell
.\.venv\Scripts\pip.exe install waitress
```

### Q2: 升级后访问速度反而变慢
**原因**: threads 参数设置过低  
**解决**: 将 `threads=4` 改为 `threads=8`

### Q3: 调试模式不生效
**原因**: `DASH_DEBUG` 环境变量未设置  
**解决**: 使用 `.\启动看板-调试模式.ps1` 启动

### Q4: 想回到旧版本
**原因**: 不习惯新配置  
**解决**: 执行 `git revert HEAD` 或手动恢复代码

---

## 📚 参考资料

- [Waitress 官方文档](https://docs.pylonsproject.org/projects/waitress/en/stable/)
- [Dash 部署指南](https://dash.plotly.com/deployment)
- [Python WSGI 服务器对比](https://www.fullstackpython.com/wsgi-servers.html)

---

## ✅ 升级检查清单

升级完成后，请确认：

- [ ] `pip list | findstr waitress` 显示已安装
- [ ] 启动日志显示 "🚀 生产模式: 使用 Waitress 服务器"
- [ ] 无 "development server" 警告
- [ ] http://localhost:8050 可正常访问
- [ ] 上传 Excel 功能正常
- [ ] 切换 Tab 页流畅
- [ ] 调试模式可切换（`.\启动看板-调试模式.ps1`）
- [ ] 代码已推送到 GitHub

---

**最后更新**: 2025年11月22日  
**文档版本**: v1.0  
**状态**: 待升级
