# =============================================================================
# PowerShell 7+ 定位和启动工具
# =============================================================================

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "              PowerShell 7+ 定位和启动工具                               " -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# 可能的安装路径
$possiblePaths = @(
    "C:\Program Files\PowerShell\7\pwsh.exe",
    "C:\Program Files\PowerShell\7-preview\pwsh.exe",
    "$env:LOCALAPPDATA\Microsoft\PowerShell\7\pwsh.exe",
    "$env:ProgramFiles\PowerShell\7\pwsh.exe"
)

Write-Host "正在搜索 PowerShell 7+ 安装位置..." -ForegroundColor Yellow
Write-Host ""

$foundPath = $null

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        Write-Host "[找到] $path" -ForegroundColor Green
        $foundPath = $path
        break
    } else {
        Write-Host "[未找到] $path" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

if ($foundPath) {
    Write-Host "PowerShell 7+ 已安装!" -ForegroundColor Green
    Write-Host "安装位置: $foundPath" -ForegroundColor White
    Write-Host ""
    
    # 获取版本信息
    try {
        $version = & $foundPath --version
        Write-Host "版本信息: $version" -ForegroundColor Cyan
    } catch {
        Write-Host "无法获取版本信息" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "启动方式:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  方式1: 使用完整路径 (当前可用)" -ForegroundColor Cyan
    Write-Host "    & `"$foundPath`"" -ForegroundColor White
    Write-Host ""
    Write-Host "  方式2: 添加到PATH后使用简短命令 (推荐)" -ForegroundColor Cyan
    Write-Host "    pwsh" -ForegroundColor White
    Write-Host ""
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    
    # 检查PATH
    $pwshInPath = $env:Path -split ';' | Where-Object { Test-Path "$_\pwsh.exe" -ErrorAction SilentlyContinue }
    
    if (-not $pwshInPath) {
        Write-Host "问题诊断: pwsh 不在系统PATH中" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "解决方案:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1. 重启电脑 (最简单)" -ForegroundColor White
        Write-Host "     安装程序可能需要重启才能更新PATH" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  2. 重启 VS Code / 终端" -ForegroundColor White
        Write-Host "     关闭所有VS Code窗口后重新打开" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  3. 刷新当前会话的PATH (临时)" -ForegroundColor White
        Write-Host "     运行以下命令:" -ForegroundColor Gray
        Write-Host '     $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")' -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  4. 使用完整路径启动 (立即可用)" -ForegroundColor White
        Write-Host "     & `"$foundPath`"" -ForegroundColor DarkGray
        Write-Host ""
    } else {
        Write-Host "PATH 配置正常" -ForegroundColor Green
        Write-Host "可以直接使用: pwsh" -ForegroundColor White
        Write-Host ""
    }
    
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "是否立即启动 PowerShell 7+? (Y/N): " -ForegroundColor Yellow -NoNewline
    $launch = Read-Host
    
    if ($launch -eq "Y" -or $launch -eq "y") {
        Write-Host ""
        Write-Host "正在启动 PowerShell 7+..." -ForegroundColor Green
        Write-Host ""
        & $foundPath
    } else {
        Write-Host ""
        Write-Host "提示: 使用以下命令启动:" -ForegroundColor Cyan
        Write-Host "  & `"$foundPath`"" -ForegroundColor White
        Write-Host ""
    }
    
} else {
    Write-Host "未找到 PowerShell 7+ 安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. 安装尚未完成" -ForegroundColor White
    Write-Host "  2. 安装到了非标准位置" -ForegroundColor White
    Write-Host "  3. 安装失败" -ForegroundColor White
    Write-Host ""
    Write-Host "建议操作:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. 检查安装状态:" -ForegroundColor White
    Write-Host "     winget list Microsoft.PowerShell" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. 重新安装:" -ForegroundColor White
    Write-Host "     winget install Microsoft.PowerShell" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. 使用 MSI 安装包:" -ForegroundColor White
    Write-Host "     访问 https://aka.ms/PSWindows" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
