# =============================================================================
# 设置 PowerShell 7+ 为右键菜单默认项
# =============================================================================
# 功能: 将 Shift+右键 的 PowerShell 改为 PowerShell 7+
# 需要管理员权限运行
# =============================================================================

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "=========================================================================" -ForegroundColor Red
    Write-Host "                      需要管理员权限                                      " -ForegroundColor Red
    Write-Host "=========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "此脚本需要管理员权限来修改注册表。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请按以下步骤操作:" -ForegroundColor Cyan
    Write-Host "  1. 右键点击此脚本文件" -ForegroundColor White
    Write-Host "  2. 选择 '以管理员身份运行'" -ForegroundColor White
    Write-Host ""
    Write-Host "或者在管理员PowerShell中运行:" -ForegroundColor Cyan
    Write-Host "  .\设置PowerShell7为默认.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "=========================================================================" -ForegroundColor Red
    Write-Host ""
    Read-Host "按任意键退出"
    exit 1
}

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "              设置 PowerShell 7+ 为右键菜单默认项                         " -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# 查找 PowerShell 7+ 路径
$pwshPath = $null
$possiblePaths = @(
    "C:\Program Files\PowerShell\7\pwsh.exe",
    "C:\Program Files\PowerShell\7-preview\pwsh.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $pwshPath = $path
        break
    }
}

if (-not $pwshPath) {
    Write-Host "错误: 未找到 PowerShell 7+ 安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装 PowerShell 7+:" -ForegroundColor Yellow
    Write-Host "  winget install Microsoft.PowerShell" -ForegroundColor White
    Write-Host ""
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "找到 PowerShell 7+: $pwshPath" -ForegroundColor Green
Write-Host ""

# 注册表路径
$regPaths = @(
    # 文件夹背景右键菜单
    "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\Powershell",
    # 文件夹右键菜单
    "Registry::HKEY_CLASSES_ROOT\Directory\shell\Powershell",
    # 驱动器右键菜单
    "Registry::HKEY_CLASSES_ROOT\Drive\shell\Powershell"
)

Write-Host "正在配置右键菜单..." -ForegroundColor Yellow
Write-Host ""

$successCount = 0
$totalCount = $regPaths.Count

foreach ($regPath in $regPaths) {
    try {
        if (Test-Path $regPath) {
            # 备份原始命令
            $commandPath = Join-Path $regPath "command"
            if (Test-Path $commandPath) {
                $originalValue = (Get-ItemProperty -Path $commandPath -Name "(default)" -ErrorAction SilentlyContinue)."(default)"
                
                # 创建新的命令 - 使用 PowerShell 7+
                $newCommand = "`"$pwshPath`" -NoExit -Command `"Set-Location '%V'`""
                
                # 更新注册表
                Set-ItemProperty -Path $commandPath -Name "(default)" -Value $newCommand -Force
                
                Write-Host "[成功] 已更新: $regPath" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "[跳过] 未找到命令路径: $regPath" -ForegroundColor Gray
            }
        } else {
            Write-Host "[跳过] 注册表项不存在: $regPath" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[失败] $regPath" -ForegroundColor Red
        Write-Host "       错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "配置完成!" -ForegroundColor Green
    Write-Host ""
    Write-Host "已成功更新 $successCount/$totalCount 个右键菜单项" -ForegroundColor White
    Write-Host ""
    Write-Host "现在您可以:" -ForegroundColor Yellow
    Write-Host "  * Shift + 右键 文件夹 -> 选择 '在此处打开 PowerShell 窗口'" -ForegroundColor White
    Write-Host "  * 这将启动 PowerShell 7+ (而不是 PowerShell 5.1)" -ForegroundColor White
    Write-Host ""
    Write-Host "提示: 可能需要重启资源管理器才能生效" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "是否重启资源管理器? (Y/N): " -ForegroundColor Yellow -NoNewline
    $restart = Read-Host
    
    if ($restart -eq "Y" -or $restart -eq "y") {
        Write-Host ""
        Write-Host "正在重启资源管理器..." -ForegroundColor Green
        Stop-Process -Name explorer -Force
        Start-Sleep -Seconds 2
        Start-Process explorer
        Write-Host "完成!" -ForegroundColor Green
        Write-Host ""
    }
} else {
    Write-Host "未能更新任何菜单项" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  * 权限不足" -ForegroundColor White
    Write-Host "  * 注册表项不存在" -ForegroundColor White
    Write-Host "  * 系统版本不支持" -ForegroundColor White
    Write-Host ""
}

Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
