# PostgreSQL 数据库初始化脚本

Write-Host @"
╔══════════════════════════════════════════════════════════╗
║       🗄️ PostgreSQL 数据库初始化                          ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "`n[1/3] 检查PostgreSQL是否运行..." -ForegroundColor Yellow

# 检查PostgreSQL服务
$service = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -eq "Running") {
        Write-Host "✅ PostgreSQL服务正在运行" -ForegroundColor Green
    } else {
        Write-Host "⚠️  PostgreSQL服务未运行，正在启动..." -ForegroundColor Yellow
        Start-Service $service.Name
        Write-Host "✅ PostgreSQL服务已启动" -ForegroundColor Green
    }
} else {
    Write-Host "❌ 未找到PostgreSQL服务" -ForegroundColor Red
    Write-Host "   请确认PostgreSQL已正确安装" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[2/3] 配置数据库..." -ForegroundColor Yellow
Write-Host "请输入PostgreSQL配置信息：" -ForegroundColor Cyan

# 获取配置信息
$dbUser = Read-Host "数据库用户名 (默认: postgres)"
if ([string]::IsNullOrWhiteSpace($dbUser)) { $dbUser = "postgres" }

$dbPassword = Read-Host "数据库密码" -AsSecureString
$dbPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassword)
)

$dbHost = Read-Host "数据库主机 (默认: localhost)"
if ([string]::IsNullOrWhiteSpace($dbHost)) { $dbHost = "localhost" }

$dbPort = Read-Host "数据库端口 (默认: 5432)"
if ([string]::IsNullOrWhiteSpace($dbPort)) { $dbPort = "5432" }

$dbName = "o2o_dashboard"

Write-Host "`n[3/3] 创建数据库..." -ForegroundColor Yellow

# 设置PostgreSQL环境变量
$env:PGPASSWORD = $dbPasswordPlain

# 创建数据库
$createDbSql = @"
SELECT 'CREATE DATABASE $dbName'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$dbName')\gexec
"@

Write-Host "正在创建数据库 '$dbName'..." -ForegroundColor Cyan

try {
    # 尝试连接并创建数据库
    $createDbSql | psql -U $dbUser -h $dbHost -p $dbPort -d postgres 2>&1 | Out-Null
    
    # 验证数据库是否存在
    $checkDb = "SELECT 1 FROM pg_database WHERE datname = '$dbName'" | psql -U $dbUser -h $dbHost -p $dbPort -d postgres -t -A
    
    if ($checkDb -eq "1") {
        Write-Host "✅ 数据库 '$dbName' 创建成功或已存在" -ForegroundColor Green
    } else {
        Write-Host "⚠️  无法确认数据库是否创建成功" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ℹ️  数据库可能已存在，继续下一步" -ForegroundColor Cyan
}

# 清除密码环境变量
Remove-Item Env:\PGPASSWORD

Write-Host "`n[✓] 生成 .env 配置文件..." -ForegroundColor Yellow

# 生成.env文件
$envContent = @"
# 数据库配置
DATABASE_URL=postgresql://${dbUser}:${dbPasswordPlain}@${dbHost}:${dbPort}/${dbName}

# API配置
API_HOST=0.0.0.0
API_PORT=8000

# 应用配置
DEBUG=True
HOST=0.0.0.0
PORT=8050

# 安全配置 (生产环境请修改)
SECRET_KEY=dev-secret-key-change-in-production

# AI配置 (可选)
# ZHIPU_API_KEY=your_zhipu_api_key
# QWEN_API_KEY=your_qwen_api_key
# GEMINI_API_KEY=your_gemini_api_key
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ .env 配置文件已创建" -ForegroundColor Green

Write-Host @"

╔══════════════════════════════════════════════════════════╗
║  ✅ 数据库配置完成！                                       ║
╠══════════════════════════════════════════════════════════╣
║  📊 数据库信息:                                            ║
║     • 主机: $dbHost
║     • 端口: $dbPort
║     • 数据库: $dbName
║     • 用户: $dbUser
║                                                           ║
║  📝 配置文件: .env                                         ║
║                                                           ║
║  🎯 下一步:                                                ║
║     1. 运行: python database/migrate.py                  ║
║        (创建数据表)                                        ║
║     2. 运行: python backend/main.py                      ║
║        (启动后端API)                                       ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Green

Write-Host "`n按任意键继续..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
