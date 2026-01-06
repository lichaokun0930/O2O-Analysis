# PostgreSQL 自动启动配置说明

**版本**: V8.10  
**更新时间**: 2025-12-11  
**功能**: 启动看板时自动启动PostgreSQL数据库

---

## 🎯 问题描述

**现象**: 每次启动看板都提示数据库连接失败，需要手动运行 `.\启动数据库.ps1`

**原因**: PostgreSQL数据库未设置为自动启动

**解决**: 在启动看板脚本中添加自动启动PostgreSQL的功能

---

## ✅ 已实施的解决方案

### 1. 创建自动启动脚本

**文件**: `自动启动PostgreSQL.ps1`

**功能**:
- 自动检测PostgreSQL是否已运行
- 自动查找PostgreSQL安装路径
- 自动查找数据目录
- 自动启动PostgreSQL
- 验证启动结果

**使用方法**:

```powershell
# 直接运行（显示详细信息）
.\自动启动PostgreSQL.ps1

# 静默模式（供其他脚本调用）
.\自动启动PostgreSQL.ps1 -Silent
```

### 2. 集成到启动看板脚本

**文件**: `启动看板.ps1`

**修改内容**:
- 在启动看板前检查PostgreSQL连接
- 如果连接失败，自动调用启动脚本
- 验证启动结果并显示状态

**工作流程**:
```
启动看板.ps1
  ↓
检查PostgreSQL连接
  ↓
连接失败？
  ├─ 是 → 调用自动启动PostgreSQL.ps1
  │        ↓
  │      启动成功？
  │        ├─ 是 → 继续启动看板
  │        └─ 否 → 提示手动启动
  └─ 否 → 继续启动看板
```

---

## 🚀 使用方法

### 方法1: 正常启动（推荐）

```powershell
.\启动看板.ps1
```

**效果**:
- 自动检查PostgreSQL状态
- 如果未运行，自动启动
- 启动成功后继续启动看板

**输出示例**:
```
🔍 检查 PostgreSQL 数据库...
✅ 使用虚拟环境: D:\Python\订单数据看板\.venv\Scripts\python.exe
⚠️  PostgreSQL 数据库未连接，正在尝试自动启动...
🚀 正在启动 PostgreSQL...
   安装路径: D:\PostgreSQL\bin
   数据目录: D:\PostgreSQL\data
✅ PostgreSQL 启动成功 (6 个进程)
✅ PostgreSQL 已成功启动并连接
```

### 方法2: 手动启动数据库

如果自动启动失败，可以手动启动：

```powershell
# 方法A: 使用自动启动脚本
.\自动启动PostgreSQL.ps1

# 方法B: 使用完整启动脚本（更多选项）
.\启动数据库.ps1
```

---

## 📋 支持的PostgreSQL安装路径

脚本会自动搜索以下路径：

**安装路径**:
- `D:\PostgreSQL\bin`
- `C:\Program Files\PostgreSQL\18\bin`
- `C:\Program Files\PostgreSQL\16\bin`
- `C:\Program Files\PostgreSQL\15\bin`
- `C:\Program Files\PostgreSQL\14\bin`
- `C:\Program Files\PostgreSQL\13\bin`

**数据目录**:
- `D:\PostgreSQL\data`
- `C:\Program Files\PostgreSQL\18\data`
- `C:\Program Files\PostgreSQL\16\data`
- `C:\Program Files\PostgreSQL\15\data`
- `C:\Program Files\PostgreSQL\14\data`
- `C:\Program Files\PostgreSQL\13\data`

---

## 🔧 自定义配置

### 添加自定义路径

如果你的PostgreSQL安装在其他位置，可以修改 `自动启动PostgreSQL.ps1`：

```powershell
# 在脚本中找到这两个数组，添加你的路径
$pgPaths = @(
    "D:\PostgreSQL\bin",
    "你的自定义路径\bin",  # 添加这一行
    "C:\Program Files\PostgreSQL\18\bin",
    # ...
)

$dataDirs = @(
    "D:\PostgreSQL\data",
    "你的自定义路径\data",  # 添加这一行
    "C:\Program Files\PostgreSQL\18\data",
    # ...
)
```

### 设置为Windows服务自动启动

如果希望PostgreSQL随Windows启动，可以设置为服务：

```powershell
# 以管理员身份运行PowerShell
# 查找PostgreSQL服务
Get-Service -Name "postgresql*"

# 设置为自动启动
Set-Service -Name "postgresql-x64-16" -StartupType Automatic

# 立即启动服务
Start-Service -Name "postgresql-x64-16"
```

**注意**: 服务名称可能不同，请根据实际情况调整。

---

## 🐛 故障排查

### 问题1: 自动启动失败

**症状**: 显示"PostgreSQL 自动启动失败"

**可能原因**:
1. PostgreSQL未安装
2. 安装路径不在搜索列表中
3. 数据目录权限问题

**解决方案**:

```powershell
# 1. 检查PostgreSQL是否安装
Get-Process postgres -ErrorAction SilentlyContinue

# 2. 查找PostgreSQL安装位置
Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter "pg_ctl.exe"

# 3. 手动启动并查看错误
.\启动数据库.ps1
```

### 问题2: 启动成功但连接失败

**症状**: 显示"PostgreSQL 已启动，但连接仍失败"

**可能原因**:
1. 数据库配置错误
2. 端口被占用
3. 认证配置问题

**解决方案**:

```powershell
# 1. 检查端口占用
netstat -ano | findstr :5432

# 2. 查看PostgreSQL日志
# 日志位置: D:\PostgreSQL\data\logfile
Get-Content "D:\PostgreSQL\data\logfile" -Tail 50

# 3. 检查pg_hba.conf配置
# 确保有以下行:
# host    all    all    127.0.0.1/32    trust
```

### 问题3: 权限不足

**症状**: 显示"拒绝访问"或"权限不足"

**解决方案**:

```powershell
# 以管理员身份运行PowerShell
# 右键点击PowerShell图标 → 以管理员身份运行
.\启动看板.ps1
```

---

## 📊 性能影响

**自动启动检查**:
- 检查时间: <1秒
- 启动时间: 3-5秒
- 总延迟: <6秒

**对比**:
- 手动启动: 需要打开新窗口，运行脚本，等待启动（约30秒）
- 自动启动: 无需人工干预，自动完成（约6秒）

**收益**:
- 节省时间: 约24秒/次
- 提升体验: 无需记住启动数据库
- 减少错误: 避免忘记启动数据库

---

## 🎉 总结

### 优化效果

**优化前**:
1. 运行 `.\启动看板.ps1`
2. 看到数据库连接失败
3. 打开新窗口
4. 运行 `.\启动数据库.ps1`
5. 等待启动完成
6. 关闭窗口
7. 重新运行 `.\启动看板.ps1`

**优化后**:
1. 运行 `.\启动看板.ps1`
2. 自动检测并启动PostgreSQL
3. 看板正常启动

### 核心优势

- ✅ **自动化**: 无需手动启动数据库
- ✅ **智能化**: 自动检测状态，按需启动
- ✅ **友好化**: 清晰的状态提示
- ✅ **可靠性**: 多路径搜索，兼容性好

### 适用场景

- ✅ 开发环境日常使用
- ✅ 演示环境快速启动
- ✅ 测试环境自动化部署
- ⚠️ 生产环境建议使用Windows服务

---

## 📚 相关文档

- `启动看板.ps1` - 主启动脚本（已集成自动启动）
- `自动启动PostgreSQL.ps1` - 独立的自动启动脚本
- `启动数据库.ps1` - 完整的数据库启动脚本（更多选项）
- `PostgreSQL环境配置完整指南.md` - PostgreSQL配置指南

---

**版本**: V8.10  
**状态**: ✅ 已实施并测试  
**建议**: 立即使用，享受自动化便利

