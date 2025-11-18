# 打包给同事的必需文件
# 自动创建 colleague_package.zip

Write-Host "================================" -ForegroundColor Cyan
Write-Host "打包同事环境必需文件" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 输出包名称
$packageName = "colleague_package.zip"
$tempDir = "temp_package"

# 创建临时目录
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "📦 开始收集文件..." -ForegroundColor Yellow
Write-Host ""

# 必需的Python文件
$pythonFiles = @(
    "echarts_responsive_utils.py",
    "echarts_factory.py",
    "component_styles.py",
    "智能门店看板_Dash版.py",
    "订单数据处理器.py",
    "真实数据处理器.py",
    "cache_utils.py",
    "component_styles.py"
)

Write-Host "1️⃣ 复制Python文件..." -ForegroundColor Cyan
foreach ($file in $pythonFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $tempDir
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (文件不存在,跳过)" -ForegroundColor Yellow
    }
}

Write-Host ""

# database文件夹
Write-Host "2️⃣ 复制database文件夹..." -ForegroundColor Cyan
$databaseDir = Join-Path $tempDir "database"
New-Item -ItemType Directory -Path $databaseDir | Out-Null

$databaseFiles = @(
    "database\__init__.py",
    "database\config.py",
    "database\connection.py",
    "database\models.py",
    "database\data_source_manager.py",
    "database\data_lifecycle_manager.py"
)

foreach ($file in $databaseFiles) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        Copy-Item -Path $file -Destination (Join-Path $databaseDir $fileName)
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (文件不存在,跳过)" -ForegroundColor Yellow
    }
}

Write-Host ""

# 配置文件
Write-Host "3️⃣ 复制配置文件..." -ForegroundColor Cyan
$configFiles = @(
    ".env.example",
    "requirements.txt",
    ".gitignore"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $tempDir
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (文件不存在,跳过)" -ForegroundColor Yellow
    }
}

Write-Host ""

# 文档文件
Write-Host "4️⃣ 复制文档..." -ForegroundColor Cyan
$docFiles = @(
    "数据库配置快速指南.md",
    "PostgreSQL环境配置完整指南.md",
    "README_Dash版使用指南.md",
    "依赖和环境说明.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $tempDir
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (文件不存在,跳过)" -ForegroundColor Yellow
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
