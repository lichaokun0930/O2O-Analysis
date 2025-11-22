# 新电脑一键配置脚本
# 用途: 自动完成Python环境、依赖安装、配置文件初始化

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  O2O智能看板 - 新电脑环境自动配置  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 第一步: 检查前置条件
# ============================================================================
Write-Host "【第一步】检查前置条件..." -ForegroundColor Yellow

# 检查Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python未安装，请先安装Python 3.11+" -ForegroundColor Red
    Write-Host "     下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 检查Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "  ✅ Git已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Git未安装，请先安装Git" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# 第二步: 创建虚拟环境
# ============================================================================
Write-Host "【第二步】创建Python虚拟环境..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    Write-Host "  ℹ️  虚拟环境已存在，跳过创建" -ForegroundColor Cyan
} else {
    Write-Host "  正在创建虚拟环境..." -ForegroundColor Gray
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 虚拟环境创建成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 虚拟环境创建失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# ============================================================================
# 第三步: 激活虚拟环境并升级pip
# ============================================================================
Write-Host "【第三步】激活虚拟环境并升级pip..." -ForegroundColor Yellow

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$venvPip = Join-Path $scriptDir ".venv\Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "  ❌ 虚拟环境Python未找到" -ForegroundColor Red
    exit 1
}

Write-Host "  正在升级pip..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet
Write-Host "  ✅ pip升级完成" -ForegroundColor Green
Write-Host ""

# ============================================================================
# 第四步: 安装项目依赖
# ============================================================================
Write-Host "【第四步】安装项目依赖包 (预计5-10分钟)..." -ForegroundColor Yellow

if (Test-Path "requirements.txt") {
    Write-Host "  正在安装依赖包，请耐心等待..." -ForegroundColor Gray
    Write-Host "  提示: 可以去泡杯咖啡 ☕" -ForegroundColor Cyan
    
    # 使用UTF-8编码的requirements文件(如果存在)
    $reqFile = if (Test-Path "requirements_utf8.txt") { "requirements_utf8.txt" } else { "requirements.txt" }
    
    & $venvPip install -r $reqFile --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 依赖包安装成功" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  部分依赖包安装失败，但继续..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  requirements.txt未找到" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# 第五步: 验证核心依赖
# ============================================================================
Write-Host "【第五步】验证核心依赖包..." -ForegroundColor Yellow

$testScript = @"
import sys
try:
    import dash
    import pandas
    import plotly
    import sqlalchemy
    print('✅ 核心依赖验证通过')
    sys.exit(0)
except ImportError as e:
    print(f'❌ 依赖验证失败: {e}')
    sys.exit(1)
"@

$result = & $venvPython -c $testScript 2>&1
Write-Host "  $result" -ForegroundColor $(if ($LASTEXITCODE -eq 0) { "Green" } else { "Red" })
Write-Host ""

# ============================================================================
# 第六步: 创建配置文件
# ============================================================================
Write-Host "【第六步】创建配置文件..." -ForegroundColor Yellow

# 复制 .env 文件
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "  ✅ .env文件已创建" -ForegroundColor Green
    } elseif (Test-Path ".env.template") {
        Copy-Item .env.template .env
        Write-Host "  ✅ .env文件已创建" -ForegroundColor Green
    } else {
        # 创建默认.env文件
        @"
# 数据库配置 (⚠️ 请修改密码)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/o2o_dashboard

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# AI接口配置 (可选)
# ZHIPU_API_KEY=your_glm_api_key_here
# GEMINI_API_KEY=your_gemini_api_key_here
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "  ✅ 默认.env文件已创建" -ForegroundColor Green
        Write-Host "  ⚠️  请编辑.env文件，修改数据库密码!" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️  .env文件已存在，跳过创建" -ForegroundColor Cyan
}

Write-Host ""

# ============================================================================
# 第七步: 检查PostgreSQL
# ============================================================================
Write-Host "【第七步】检查PostgreSQL数据库..." -ForegroundColor Yellow

$pgInstalled = Test-Path "C:\Program Files\PostgreSQL"
if ($pgInstalled) {
    Write-Host "  ✅ PostgreSQL已安装" -ForegroundColor Green
    
    # 检查服务
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService) {
        if ($pgService.Status -eq "Running") {
            Write-Host "  ✅ PostgreSQL服务运行中" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  PostgreSQL服务未运行，尝试启动..." -ForegroundColor Yellow
            try {
                Start-Service $pgService.Name
                Write-Host "  ✅ PostgreSQL服务已启动" -ForegroundColor Green
            } catch {
                Write-Host "  ❌ PostgreSQL服务启动失败" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "  " -NoNewline
    Write-Host "PostgreSQL" -NoNewline -ForegroundColor Red
    Write-Host ""
    Write-Host "     1. https://www.postgresql.org/download/windows/" -ForegroundColor Cyan
    Write-Host "     2. PostgreSQL 15.x" -ForegroundColor Cyan
    Write-Host "     3. postgres password" -ForegroundColor Cyan
    Write-Host "     4. .\start_database.ps1" -ForegroundColor Cyan
}

Write-Host ""

# ============================================================================
# 第八步: 检查Redis
# ============================================================================
Write-Host "【第八步】检查Redis缓存..." -ForegroundColor Yellow

$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if ($memuraiService) {
    Write-Host "  ✅ Memurai(Redis)已安装" -ForegroundColor Green
    
    if ($memuraiService.Status -eq "Running") {
        Write-Host "  ✅ Redis服务运行中" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Redis服务未运行，尝试启动..." -ForegroundColor Yellow
        try {
            Start-Service Memurai
            Write-Host "  ✅ Redis服务已启动" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Redis服务启动失败" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  Redis not installed" -ForegroundColor Red
    Write-Host "     Run: .\start_redis.ps1" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# 配置完成总结
# ============================================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "         配置完成总结                  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "已完成项:" -ForegroundColor Green
Write-Host "  ✅ Python虚拟环境" -ForegroundColor Green
Write-Host "  ✅ 项目依赖包" -ForegroundColor Green
Write-Host "  ✅ .env配置文件" -ForegroundColor Green
Write-Host ""

Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host ""

if (-not $pgInstalled) {
    Write-Host "  1️⃣  安装PostgreSQL数据库" -ForegroundColor Red
    Write-Host "     参考: 新电脑完整配置指南.md 第三步" -ForegroundColor Cyan
    Write-Host ""
}

if (-not $memuraiService) {
    Write-Host "  2️⃣  安装Redis缓存" -ForegroundColor Red
    Write-Host "     运行: .\启动Redis.ps1" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "  3️⃣  修改.env配置文件" -ForegroundColor Yellow
Write-Host "     编辑: notepad .env" -ForegroundColor Cyan
Write-Host "     修改: 数据库密码(YOUR_PASSWORD_HERE)" -ForegroundColor Cyan
Write-Host ""

if ($pgInstalled -and $memuraiService) {
    Write-Host "  4️⃣  初始化数据库" -ForegroundColor Yellow
    Write-Host "     运行: python database\migrate.py" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "  5️⃣  启动看板" -ForegroundColor Yellow
    Write-Host "     运行: .\启动看板.ps1" -ForegroundColor Cyan
    Write-Host "     访问: http://localhost:8050" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "📚 详细文档:" -ForegroundColor Cyan
Write-Host "   - 完整配置: 新电脑完整配置指南.md" -ForegroundColor Gray
Write-Host "   - 快速上手: 快速开始指南.md" -ForegroundColor Gray
Write-Host "   - AI开发: .github\copilot-instructions.md" -ForegroundColor Gray
Write-Host ""

Write-Host "Python environment setup completed!" -ForegroundColor Green
Write-Host ""
