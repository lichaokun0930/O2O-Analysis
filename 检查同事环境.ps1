# 同事环境配置脚本
# 用途: 帮助同事快速设置开发环境

Write-Host "================================" -ForegroundColor Cyan
Write-Host "智能门店看板 - 环境配置检查" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查必需文件
$requiredFiles = @(
    "echarts_responsive_utils.py",
    "echarts_factory.py", 
    "component_styles.py",
    "智能门店看板_Dash版.py",
    "database\config.py",
    "database\connection.py",
    "database\models.py",
    "database\data_source_manager.py",
    ".env.example",
    "requirements.txt"
)

Write-Host "1️⃣ 检查必需文件..." -ForegroundColor Yellow
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (缺失)" -ForegroundColor Red
        $missingFiles += $file
    }
}

Write-Host ""

# 检查.env文件
Write-Host "2️⃣ 检查配置文件..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✅ .env 文件存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  .env 文件不存在" -ForegroundColor Yellow
    Write-Host "     请复制 .env.example 为 .env 并修改数据库密码" -ForegroundColor Yellow
}

Write-Host ""

# 检查Python环境
Write-Host "3️⃣ 检查Python环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python 未安装" -ForegroundColor Red
}

Write-Host ""

# 检查虚拟环境
Write-Host "4️⃣ 检查虚拟环境..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "  ✅ 虚拟环境 .venv 存在" -ForegroundColor Green
} elseif (Test-Path ".venv311") {
    Write-Host "  ✅ 虚拟环境 .venv311 存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  虚拟环境不存在" -ForegroundColor Yellow
    Write-Host "     运行: python -m venv .venv" -ForegroundColor Yellow
}

Write-Host ""

# 总结
Write-Host "================================" -ForegroundColor Cyan
Write-Host "检查结果总结" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

if ($missingFiles.Count -eq 0) {
    Write-Host "✅ 所有文件完整!" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Cyan
    Write-Host "1. 配置 .env 文件 (复制 .env.example 并修改数据库密码)" -ForegroundColor White
    Write-Host "2. 激活虚拟环境: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "3. 安装依赖: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "4. 测试连接: python database\connection.py" -ForegroundColor White
} else {
    Write-Host "❌ 缺少以下文件:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "解决方法:" -ForegroundColor Yellow
    Write-Host "1. 从Git拉取完整代码: git pull origin master" -ForegroundColor White
    Write-Host "2. 或联系项目负责人获取缺失文件" -ForegroundColor White
}

Write-Host ""
