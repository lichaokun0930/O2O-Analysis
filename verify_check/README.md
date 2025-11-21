# O2O Smart Store Dashboard - Complete Package

## 📦 Package Contents

This package contains the **complete working directory** (excluding backup files, virtual environments, and cache).

### Package Date
2025-11-19 19:26:22

### Excluded Items
- ✅ Backup folders (待删除文件_* / deleted_files_*)
- ✅ Virtual environments (.venv, .venv311)
- ✅ Python cache (__pycache__, *.pyc)
- ✅ Git version control (.git)
- ✅ Archived files (Archived_*)
- ✅ Temporary files (*.log, *.zip)

---

## 🚀 Quick Start Guide

### 1️⃣ Prerequisites
```bash
# Ensure these are installed:
- Python 3.7+
- PostgreSQL 12+
- pip
```

### 2️⃣ Install Dependencies
```powershell
# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Database Configuration
1. Copy `.env.example` to `.env`
2. Edit `.env` with your database credentials:
   ```ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=o2o_dashboard
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```

3. Create database:
   ```sql
   CREATE DATABASE o2o_dashboard;
   ```

### 4️⃣ Launch Dashboard
```powershell
# Use the renamed startup script
.\start_dashboard.ps1

# Or run main program directly
python dashboard_main.py
```

**Note**: Core files have been automatically renamed to English to avoid encoding issues.

---

## 📚 Key Documentation

### Core Documents
- **数据库配置快速指南.md** - Database configuration guide
- **README_Dash版使用指南.md** - Dashboard usage guide
- **依赖和环境说明.md** - Environment setup
- **PostgreSQL环境配置完整指南.md** - PostgreSQL setup

### Core Code Files
- **dashboard_main.py** - Main dashboard application
- **order_processor.py** - Order data processor
- **real_data_processor.py** - Real data processor
- **scenario_decision_engine.py** - AI decision engine
- **product_tagging_engine.py** - Product tagging engine

**Note**: Files with Chinese names have been automatically renamed to English.

---

## ⚙️ Quick Launch Scripts

### Dashboard Launch
- **start_dashboard.ps1** - Main dashboard launcher
- **start_dashboard.bat** - Batch launcher
- **start_smart_dashboard.ps1** - Smart dashboard

### Database Management
- **start_database.ps1** - Database service manager
- **check_db_status.py** - Check database status

### Utility Scripts
- **main_menu.ps1** - Unified management menu (recommended)
- **install_dependencies.ps1** - Auto-install dependencies

---

## 🆘 Troubleshooting

### Issue 1: Database Connection Failed
**Solution**: Check .env configuration, ensure PostgreSQL service is running

### Issue 2: Dependency Installation Failed
**Solution**: 
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Use China mirror (if in China)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Issue 3: Dashboard Not Accessible
**Solution**: Check if port is occupied (default: 8060)

### Issue 4: Need Chinese Interface
**Solution**: Chinese documentation files (*.md) are preserved in the package with original names

---

## 📝 File Naming

Core Python and PowerShell files have been automatically renamed to English during packaging to avoid encoding issues across different systems. Documentation files retain their original Chinese names for reference.

**Renamed Files**:
- 智能门店看板_Dash版.py → dashboard_main.py
- 订单数据处理器.py → order_processor.py
- 启动看板.ps1 → start_dashboard.ps1
- 主菜单.ps1 → main_menu.ps1
- (and more...)

---

## 📞 Technical Support

For questions, refer to the detailed documentation in the package or contact the development team.

---

**Package Info**:
- Files copied: 473
- Items skipped: 56902
- Package date: 2025-11-19 19:26:22
- Encoding: UTF-8 (supports Chinese and English)
