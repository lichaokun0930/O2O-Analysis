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

# 获取所有文件和文件夹
$allItems = Get-ChildItem -Path . -Recurse -Force

$copiedCount = 0
$skippedCount = 0

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
        $destPath = Join-Path $tempDir $relativePath
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

# 创建同事环境配置说明
Write-Host "5️⃣ 创建配置说明..." -ForegroundColor Cyan
$readme = @"
# 智能门店看板 - 独立环境配置包

## 📦 包含内容
- Python核心文件
- database模块
- 配置文件模板
- 使用文档

## 🚀 完整配置步骤

### 第1步: 安装PostgreSQL数据库

**下载安装:**
1. 访问: https://www.postgresql.org/download/windows/
2. 下载并安装PostgreSQL 14或更高版本
3. 安装时记住设置的密码(默认用户名是postgres)

**创建数据库:**
``````powershell
# 打开PowerShell,运行:
psql -U postgres -c "CREATE DATABASE o2o_dashboard;"
``````

### 第2步: 解压文件
将此压缩包解压到工作目录

### 第3步: 创建虚拟环境
``````powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
``````

### 第4步: 安装依赖
``````powershell
pip install -r requirements.txt
``````

### 第5步: 配置数据库连接
``````powershell
# 复制配置文件模板
Copy-Item .env.example .env
``````

**编辑 .env 文件,修改数据库连接:**
``````ini
# 使用你自己的PostgreSQL密码
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/o2o_dashboard
``````

**示例:**
- 如果你的PostgreSQL密码是 `123456`:
  ``````
  DATABASE_URL=postgresql://postgres:123456@localhost:5432/o2o_dashboard
  ``````

### 第6步: 测试数据库连接
``````powershell
python database\connection.py
``````

如果看到 `[OK] Database connection successful!` 就成功了!

### 第7步: 启动看板
``````powershell
python 智能门店看板_Dash版.py
``````

然后访问: http://localhost:8050

## 📚 详细文档
- 数据库配置快速指南.md - 数据库配置详细说明
- README_Dash版使用指南.md - 看板使用说明
- 依赖和环境说明.md - 环境要求说明

## ❓ 常见问题

### Q: 如何安装PostgreSQL?
A: 
1. 下载: https://www.postgresql.org/download/windows/
2. 运行安装程序,一路Next
3. 设置postgres用户密码(记住这个密码!)
4. 端口保持默认5432
5. 安装完成后,在开始菜单找到SQL Shell(psql)

### Q: 如何创建数据库?
A: 
``````powershell
# 方法1: 使用psql命令
psql -U postgres -c "CREATE DATABASE o2o_dashboard;"

# 方法2: 使用pgAdmin图形界面
# 1. 打开pgAdmin
# 2. 连接到PostgreSQL
# 3. 右键Databases -> Create -> Database
# 4. 输入名称: o2o_dashboard
``````

### Q: 提示模块找不到?
A: 确保已激活虚拟环境并安装了所有依赖:
``````powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
``````

### Q: 数据库连接失败?
A: 检查:
1. PostgreSQL服务是否运行(服务名: postgresql-x64-14)
2. .env文件中的密码是否正确
3. 数据库o2o_dashboard是否已创建

### Q: 没有数据怎么办?
A: 
- 看板支持通过界面上传Excel数据
- 或联系项目负责人获取示例数据

### Q: 端口8050被占用?
A: 在.env中修改:
``````ini
PORT=8051  # 改成其他端口
``````

## 📞 需要帮助?
联系项目负责人

---
打包时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@

$readme | Out-File -FilePath (Join-Path $tempDir "README.md") -Encoding UTF8
Write-Host "  ✅ README.md" -ForegroundColor Green

Write-Host ""

# 创建快速启动脚本
Write-Host "6️⃣ 创建快速启动脚本..." -ForegroundColor Cyan
$quickStart = @'
# 快速启动脚本

Write-Host "智能门店看板 - 快速启动" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ 虚拟环境不存在,正在创建..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ 虚拟环境创建完成" -ForegroundColor Green
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# 检查依赖
Write-Host "检查依赖..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# 测试数据库连接
Write-Host ""
Write-Host "测试数据库连接..." -ForegroundColor Yellow
python database\connection.py

# 启动看板
Write-Host ""
Write-Host "启动看板..." -ForegroundColor Green
python 智能门店看板_Dash版.py
'@

$quickStart | Out-File -FilePath (Join-Path $tempDir "快速启动.ps1") -Encoding UTF8
Write-Host "  ✅ 快速启动.ps1" -ForegroundColor Green

Write-Host ""

# 压缩打包
Write-Host "7️⃣ 压缩打包..." -ForegroundColor Cyan
if (Test-Path $packageName) {
    Remove-Item -Path $packageName -Force
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $packageName -Force
Write-Host "  ✅ $packageName" -ForegroundColor Green

# 清理临时目录
Remove-Item -Path $tempDir -Recurse -Force

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ 打包完成!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 输出文件: $packageName" -ForegroundColor Yellow
Write-Host "📏 文件大小: $((Get-Item $packageName).Length / 1KB) KB" -ForegroundColor Yellow
Write-Host ""
Write-Host "📮 发送给同事:" -ForegroundColor Cyan
Write-Host "  1. 把 $packageName 发给同事" -ForegroundColor White
Write-Host "  2. 告诉他解压后运行 '快速启动.ps1'" -ForegroundColor White
Write-Host "  3. 或者按照 README.md 中的步骤操作" -ForegroundColor White
Write-Host ""
