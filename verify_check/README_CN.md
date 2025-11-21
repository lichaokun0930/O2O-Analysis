# O2O智能门店看板 - 完整交接包

## 📦 包内容说明

本压缩包包含**测算模型**的完整工作目录（已排除备份文件、虚拟环境、缓存等）。

### 打包时间
2025年11月19日 19:26:22

### 排除的内容
- ✅ 备份文件夹 (待删除文件_*)
- ✅ 虚拟环境 (.venv, .venv311)
- ✅ Python缓存 (__pycache__, *.pyc)
- ✅ Git版本控制 (.git)
- ✅ 归档文件 (Archived_*)
- ✅ 临时文件 (*.log, *.zip)

---

## 🚀 快速开始指南

### 1️⃣ 环境准备
```bash
# 确保已安装
- Python 3.7+
- PostgreSQL 12+
- pip
```

### 2️⃣ 安装依赖
```powershell
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 3️⃣ 数据库配置
1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env` 填写数据库连接信息：
   ```ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=o2o_dashboard
   DB_USER=你的用户名
   DB_PASSWORD=你的密码
   ```

3. 创建数据库：
   ```sql
   CREATE DATABASE o2o_dashboard;
   ```

### 4️⃣ 启动看板
```powershell
# 使用重命名后的启动脚本
.\start_dashboard.ps1

# 或直接运行主程序
python dashboard_main.py
```

**说明**: 核心文件已自动重命名为英文，避免编码问题。

---

## 📝 文件命名说明

部分文件使用中文命名。为避免编码问题，可以：
1. 运行 `.\重命名中文文件为英文.ps1` 将核心文件重命名为英文
2. 或直接使用中文文件名（UTF-8编码在大多数系统都能正常工作）

**文件名对照表**:
- 智能门店看板_Dash版.py → dashboard_main.py
- 订单数据处理器.py → order_processor.py
- 真实数据处理器.py → real_data_processor.py
- 启动看板.ps1 → start_dashboard.ps1
- 主菜单.ps1 → main_menu.ps1

---

## 📚 重要文档

### 核心文档
- **数据库配置快速指南.md** - 数据库配置详细说明
- **README_Dash版使用指南.md** - 看板使用完整指南
- **依赖和环境说明.md** - 环境配置说明
- **PostgreSQL环境配置完整指南.md** - PostgreSQL安装配置

### 核心代码
- **dashboard_main.py** - 主看板程序
- **order_processor.py** - 订单数据处理
- **real_data_processor.py** - 数据处理逻辑
- **scenario_decision_engine.py** - AI决策引擎
- **product_tagging_engine.py** - 智能标签引擎

**说明**: 中文文件名已自动改为英文，避免编码问题。

---

## 🆘 常见问题

### 问题1: 数据库连接失败
**解决**: 检查 .env 文件配置是否正确，确保PostgreSQL服务已启动

### 问题2: 依赖安装失败
**解决**: 
```powershell
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题3: 看板无法访问
**解决**: 检查端口是否被占用，默认8060端口

### 问题4: 中文文件名编码错误
**解决**: 运行重命名脚本将文件改为英文名：
```powershell
.\重命名中文文件为英文.ps1
```

---

## 📞 技术支持

如有问题，请参考项目内的详细文档或联系原开发团队。

---

**打包信息**:
- 复制文件数: 473
- 跳过项目数: 56902
- 打包日期: 2025-11-19 19:26:22
- 编码格式: UTF-8（支持中英文）
