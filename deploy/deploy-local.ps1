<# 
O2O 订单数据看板 - 本地一键部署脚本
用于从 Windows 本地直接部署到云服务器

使用前配置:
1. 修改下方的服务器信息
2. 确保已配置 SSH 免密登录
#>

param(
    [string]$ServerHost = "",      # 服务器 IP，如: 123.45.67.89
    [string]$ServerUser = "root",  # SSH 用户名
    [int]$ServerPort = 22,         # SSH 端口
    [string]$DeployPath = "/opt/o2o-analysis"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectDir = Split-Path -Parent $scriptDir

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  O2O 订单数据看板 - 一键部署到云服务器" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查配置
if (-not $ServerHost) {
    Write-Host "(!) 请配置服务器 IP" -ForegroundColor Red
    Write-Host "    用法: .\deploy-local.ps1 -ServerHost 123.45.67.89" -ForegroundColor Gray
    exit 1
}

Write-Host "  服务器: ${ServerUser}@${ServerHost}:${ServerPort}" -ForegroundColor Gray
Write-Host "  部署路径: $DeployPath" -ForegroundColor Gray
Write-Host ""

# ==========================================
# 1. 构建前端
# ==========================================
Write-Host "[1/4] 构建前端..." -ForegroundColor Cyan
Set-Location "$projectDir\frontend-react"

if (-not (Test-Path "node_modules")) {
    Write-Host "      安装依赖..." -ForegroundColor Gray
    npm ci
}

npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "(X) 前端构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "      (OK) 前端构建完成" -ForegroundColor Green

# ==========================================
# 2. 上传后端代码
# ==========================================
Write-Host "[2/4] 上传后端代码..." -ForegroundColor Cyan

$excludeArgs = @(
    "--exclude", ".git",
    "--exclude", "node_modules",
    "--exclude", ".venv",
    "--exclude", "__pycache__",
    "--exclude", "*.pyc",
    "--exclude", ".env.local"
)

# 如果没有 rsync，使用 scp
$scpAvailable = Get-Command scp -ErrorAction SilentlyContinue
if ($scpAvailable) {
    Write-Host "      使用 SCP 上传..." -ForegroundColor Gray
    scp -P $ServerPort -r "$projectDir\backend\*" "${ServerUser}@${ServerHost}:$DeployPath/backend/"
} else {
    Write-Host "(!) 需要安装 OpenSSH 或 Git Bash" -ForegroundColor Yellow
    exit 1
}
Write-Host "      (OK) 后端代码已上传" -ForegroundColor Green

# ==========================================
# 3. 上传前端构建产物
# ==========================================
Write-Host "[3/4] 上传前端构建产物..." -ForegroundColor Cyan
scp -P $ServerPort -r "$projectDir\frontend-react\dist\*" "${ServerUser}@${ServerHost}:$DeployPath/frontend/"
Write-Host "      (OK) 前端已上传" -ForegroundColor Green

# ==========================================
# 4. 重启服务
# ==========================================
Write-Host "[4/4] 重启服务..." -ForegroundColor Cyan

$restartScript = @"
cd $DeployPath
source .venv/bin/activate
pip install -r backend/requirements.txt -q
sudo systemctl restart o2o-backend
sudo cp -r frontend/* /var/www/html/
sudo systemctl reload nginx
echo 'Done!'
"@

ssh -p $ServerPort "${ServerUser}@${ServerHost}" $restartScript
Write-Host "      (OK) 服务已重启" -ForegroundColor Green

# ==========================================
# 完成
# ==========================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✅ 部署完成!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  访问地址: http://$ServerHost" -ForegroundColor Cyan
Write-Host ""

Set-Location $scriptDir
