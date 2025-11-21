# 打包测算模型完整目录给同事
# 自动创建 测算模型交接包.zip

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          测算模型完整打包工具 - 交接专用                        " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 输出包名称
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packageName = "测算模型交接包_$timestamp.zip"
$tempDir = "temp_package_$timestamp"

Write-Host "📦 准备打包整个测算模型目录..." -ForegroundColor Yellow
Write-Host ""

# 排除的文件夹和文件
$excludeDirs = @(
    "待删除文件_*",
    "宸插垹闄ゆ枃浠跺浠絖*",
    ".venv",
    ".venv311",
    "__pycache__",
    ".git",
    ".vs",
    "Archived_Files_*",
    "temp_*",
    "node_modules"
)

$excludeFiles = @(
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "Thumbs.db",
    "*.zip",
    "*.log"
)

Write-Host "⚙️ 排除项:" -ForegroundColor Yellow
Write-Host "  - 备份文件夹 (待删除文件_*)" -ForegroundColor Gray
Write-Host "  - 虚拟环境 (.venv, .venv311)" -ForegroundColor Gray
Write-Host "  - 缓存文件 (__pycache__, *.pyc)" -ForegroundColor Gray
Write-Host "  - Git目录 (.git)" -ForegroundColor Gray
Write-Host "  - 归档文件 (Archived_*)" -ForegroundColor Gray
Write-Host ""

# 创建临时目录
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "📋 开始复制文件..." -ForegroundColor Cyan
Write-Host ""

# 定义重命名映射表（仅在打包时使用）
$renameMap = @{
    "智能门店看板_Dash版.py" = "dashboard_main.py"
    "订单数据处理器.py" = "order_processor.py"
    "真实数据处理器.py" = "real_data_processor.py"
    "场景营销智能决策引擎.py" = "scenario_decision_engine.py"
    "商品场景智能打标引擎.py" = "product_tagging_engine.py"
    "科学八象限分析器.py" = "octant_analyzer.py"
    "评分模型分析器.py" = "scoring_analyzer.py"
    "自适应学习引擎.py" = "adaptive_learning_engine.py"
    "学习数据管理系统.py" = "learning_data_manager.py"
    "增量学习优化器.py" = "incremental_optimizer.py"
    "智能导入门店数据.py" = "smart_data_import.py"
    "查看数据库状态.py" = "check_db_status.py"
    "导出数据库.py" = "export_database.py"
    "gemini_ai_助手.py" = "gemini_ai_assistant.py"
    "启动看板.ps1" = "start_dashboard.ps1"
    "启动看板.bat" = "start_dashboard.bat"
    "启动智能看板.ps1" = "start_smart_dashboard.ps1"
    "启动数据库.ps1" = "start_database.ps1"
    "启动看板_简易版.ps1" = "start_dashboard_simple.ps1"
    "启动看板_显示日志.ps1" = "start_dashboard_verbose.ps1"
    "启动看板-后台模式.bat" = "start_dashboard_background.bat"
    "启动多商品分析看板.ps1" = "start_multi_product_dashboard.ps1"
    "启动Dash看板.ps1" = "start_dash_dashboard.ps1"
    "主菜单.ps1" = "main_menu.ps1"
    "安装依赖.ps1" = "install_dependencies.ps1"
}

# 获取所有文件和文件夹
$allItems = Get-ChildItem -Path . -Recurse -Force

$copiedCount = 0
$skippedCount = 0
$renamedCount = 0

foreach ($item in $allItems) {
    # 获取相对路径
    $relativePath = $item.FullName.Substring((Get-Location).Path.Length + 1)
    
    # 检查是否需要排除
    $shouldExclude = $false
    
    # 检查目录排除规则
    foreach ($pattern in $excludeDirs) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    
    # 检查文件排除规则
    if (-not $shouldExclude -and $item.PSIsContainer -eq $false) {
        foreach ($pattern in $excludeFiles) {
            if ($item.Name -like $pattern) {
                $shouldExclude = $true
                break
            }
        }
    }
    
    # 复制文件
    if (-not $shouldExclude) {
        # 检查是否需要重命名（仅针对根目录文件）
        $fileName = $item.Name
        $parentPath = Split-Path $relativePath -Parent
        
        # 只有当文件在根目录（parentPath为空或"."）且在映射表中时才重命名
        if (($parentPath -eq "" -or $parentPath -eq ".") -and $renameMap.ContainsKey($fileName)) {
            $fileName = $renameMap[$fileName]
            $renamedCount++
        }
        
        # 构建目标路径
        $newRelativePath = if ($parentPath -eq "" -or $parentPath -eq ".") { 
            $fileName 
        } else { 
            Join-Path $parentPath $fileName 
        }
        
        $destPath = Join-Path $tempDir $newRelativePath
        $destDir = Split-Path $destPath -Parent
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if ($item.PSIsContainer -eq $false) {
            try {
                Copy-Item -Path $item.FullName -Destination $destPath -Force
                $copiedCount++
                if ($copiedCount % 50 -eq 0) {
                    Write-Host "  已复制 $copiedCount 个文件..." -ForegroundColor Gray
                }
            } catch {
                Write-Host "  ⚠️  跳过: $relativePath" -ForegroundColor Yellow
                $skippedCount++
            }
        }
    } else {
        $skippedCount++
    }
}

Write-Host ""
Write-Host "✅ 文件复制完成!" -ForegroundColor Green
Write-Host "  - 复制文件数: $copiedCount" -ForegroundColor Cyan
Write-Host "  - 自动重命名: $renamedCount (中文→英文)" -ForegroundColor Cyan
Write-Host "  - 跳过项目数: $skippedCount" -ForegroundColor Yellow
Write-Host ""

# 创建交接说明文件
Write-Host "📝 生成交接说明文档..." -ForegroundColor Cyan
$readmeContent = @"
# O2O Smart Store Dashboard - Complete Package

## 📦 Package Contents

This package contains the **complete working directory** (excluding backup files, virtual environments, and cache).

### Package Date
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

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
``````bash
# Ensure these are installed:
- Python 3.7+
- PostgreSQL 12+
- pip
``````

### 2️⃣ Install Dependencies
``````powershell
# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
``````

### 3️⃣ Database Configuration
1. Copy ``.env.example`` to ``.env``
2. Edit ``.env`` with your database credentials:
   ``````ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=o2o_dashboard
   DB_USER=your_username
   DB_PASSWORD=your_password
   ``````

3. Create database:
   ``````sql
   CREATE DATABASE o2o_dashboard;
   ``````

### 4️⃣ Launch Dashboard
``````powershell
# Use the renamed startup script
.\start_dashboard.ps1

# Or run main program directly
python dashboard_main.py
``````

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
``````powershell
# Upgrade pip
python -m pip install --upgrade pip

# Use China mirror (if in China)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
``````

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
- Files copied: $copiedCount
- Items skipped: $skippedCount
- Package date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- Encoding: UTF-8 (supports Chinese and English)
"@

$readmePath = Join-Path $tempDir "README.md"
$readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
Write-Host "  ✅ README.md (English)" -ForegroundColor Green

# 同时创建中文版README
$readmeContentCN = @"
# O2O智能门店看板 - 完整交接包

## 📦 包内容说明

本压缩包包含**测算模型**的完整工作目录（已排除备份文件、虚拟环境、缓存等）。

### 打包时间
$(Get-Date -Format "yyyy年MM月dd日 HH:mm:ss")

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
``````bash
# 确保已安装
- Python 3.7+
- PostgreSQL 12+
- pip
``````

### 2️⃣ 安装依赖
``````powershell
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
``````

### 3️⃣ 数据库配置
1. 复制 ``.env.example`` 为 ``.env``
2. 编辑 ``.env`` 填写数据库连接信息：
   ``````ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=o2o_dashboard
   DB_USER=你的用户名
   DB_PASSWORD=你的密码
   ``````

3. 创建数据库：
   ``````sql
   CREATE DATABASE o2o_dashboard;
   ``````

### 4️⃣ 启动看板
``````powershell
# 使用重命名后的启动脚本
.\start_dashboard.ps1

# 或直接运行主程序
python dashboard_main.py
``````

**说明**: 核心文件已自动重命名为英文，避免编码问题。

---

## 📝 文件命名说明

部分文件使用中文命名。为避免编码问题，可以：
1. 运行 ``.\重命名中文文件为英文.ps1`` 将核心文件重命名为英文
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
``````powershell
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
``````

### 问题3: 看板无法访问
**解决**: 检查端口是否被占用，默认8060端口

### 问题4: 中文文件名编码错误
**解决**: 运行重命名脚本将文件改为英文名：
``````powershell
.\重命名中文文件为英文.ps1
``````

---

## 📞 技术支持

如有问题，请参考项目内的详细文档或联系原开发团队。

---

**打包信息**:
- 复制文件数: $copiedCount
- 跳过项目数: $skippedCount
- 打包日期: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- 编码格式: UTF-8（支持中英文）
"@

$readmePathCN = Join-Path $tempDir "README_CN.md"
$readmeContentCN | Out-File -FilePath $readmePathCN -Encoding UTF8
Write-Host "  ✅ README_CN.md (中文)" -ForegroundColor Green

# 同时打包重命名脚本
$renameScriptSource = Join-Path $PSScriptRoot "重命名中文文件为英文.ps1"
if (Test-Path $renameScriptSource) {
    Copy-Item -Path $renameScriptSource -Destination $tempDir -Force
    Write-Host "  ✅ 重命名中文文件为英文.ps1" -ForegroundColor Green
}

Write-Host ""

# 压缩打包
Write-Host "🗜️  压缩打包中..." -ForegroundColor Cyan
Write-Host "  (文件较多,请稍候...)" -ForegroundColor Gray

try {
    # 尝试使用Compress-Archive（更稳定）
    if (Test-Path $packageName) {
        Remove-Item $packageName -Force
    }
    
    Compress-Archive -Path "$tempDir\*" -DestinationPath $packageName -CompressionLevel Optimal -Force
    
    $packageSize = (Get-Item $packageName).Length / 1MB
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "                    ✅ 打包完成!                                " -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 包名称: $packageName" -ForegroundColor Cyan
    Write-Host "📊 包大小: $([math]::Round($packageSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "📂 位置: $(Get-Location)\$packageName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 打包统计:" -ForegroundColor Yellow
    Write-Host "  - 复制文件: $copiedCount 个" -ForegroundColor White
    Write-Host "  - 自动重命名: $renamedCount 个 (中文→英文)" -ForegroundColor White
    Write-Host "  - 跳过项目: $skippedCount 个" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 交接步骤:" -ForegroundColor Yellow
    Write-Host "  1. 将 $packageName 发送给同事" -ForegroundColor White
    Write-Host "  2. 解压后阅读 README.md 或 README_CN.md" -ForegroundColor White
    Write-Host "  3. 按照说明配置环境和数据库" -ForegroundColor White
    Write-Host "  4. 运行 .\start_dashboard.ps1 启动系统" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 提示: 核心文件已自动重命名为英文,避免编码问题" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "❌ 压缩失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "📁 临时文件夹保留在: $tempDir" -ForegroundColor Yellow
    Write-Host "   可以手动压缩该文件夹或重试" -ForegroundColor Gray
    Write-Host ""
    return
}

# 清理临时目录
Write-Host "🧹 清理临时文件..." -ForegroundColor Gray
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "✅ 完成!" -ForegroundColor Green
Write-Host ""
