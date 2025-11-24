# =============================================================================
# PowerShell版本检查工具
# =============================================================================
# 功能: 检查当前PowerShell版本并提供升级建议
# =============================================================================

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "                  PowerShell 版本检查工具                                " -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# 获取当前版本信息
$currentVersion = $PSVersionTable.PSVersion
$edition = $PSVersionTable.PSEdition
$osInfo = if ($PSVersionTable.OS) { $PSVersionTable.OS } else { "Windows (传统版本)" }

Write-Host "当前PowerShell信息" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  版本号: $currentVersion" -ForegroundColor White
Write-Host "  版本类型: $edition" -ForegroundColor White
Write-Host "  操作系统: $osInfo" -ForegroundColor Gray
Write-Host ""

# 判断版本类型
if ($edition -eq "Desktop") {
    Write-Host "您正在使用 Windows PowerShell (传统版本)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "版本说明:" -ForegroundColor Cyan
    Write-Host "  * Windows PowerShell 5.1 是最后的传统版本" -ForegroundColor White
    Write-Host "  * 仅支持Windows系统" -ForegroundColor White
    Write-Host "  * 基于 .NET Framework" -ForegroundColor White
    Write-Host "  * Microsoft不再为其添加新功能" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "推荐升级到 PowerShell 7+ (现代版本)" -ForegroundColor Green
    Write-Host ""
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "PowerShell 7+ 的新特性:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  性能提升:" -ForegroundColor Yellow
    Write-Host "    + 启动速度更快" -ForegroundColor Green
    Write-Host "    + 执行效率更高" -ForegroundColor Green
    Write-Host "    + 内存占用更少" -ForegroundColor Green
    Write-Host ""
    Write-Host "  跨平台支持:" -ForegroundColor Yellow
    Write-Host "    + Windows、Linux、macOS 全平台支持" -ForegroundColor Green
    Write-Host "    + 基于 .NET Core / .NET 5+" -ForegroundColor Green
    Write-Host ""
    Write-Host "  新语法特性:" -ForegroundColor Yellow
    Write-Host "    + 三元运算符" -ForegroundColor Green
    Write-Host "    + 管道链运算符" -ForegroundColor Green
    Write-Host "    + null 合并运算符" -ForegroundColor Green
    Write-Host "    + ForEach-Object -Parallel (并行处理)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  增强功能:" -ForegroundColor Yellow
    Write-Host "    + 改进的错误处理和调试" -ForegroundColor Green
    Write-Host "    + 更好的JSON/REST API支持" -ForegroundColor Green
    Write-Host "    + 改进的自动补全" -ForegroundColor Green
    Write-Host "    + 更好的Unicode支持" -ForegroundColor Green
    Write-Host ""
    Write-Host "  兼容性:" -ForegroundColor Yellow
    Write-Host "    + 可与Windows PowerShell 5.1并存" -ForegroundColor Green
    Write-Host "    + 向后兼容大多数脚本" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "安装方式:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  方式1: 使用 winget (推荐)" -ForegroundColor Yellow
    Write-Host "    winget install Microsoft.PowerShell" -ForegroundColor White
    Write-Host ""
    Write-Host "  方式2: 使用 MSI安装包" -ForegroundColor Yellow
    Write-Host "    访问: https://aka.ms/PSWindows" -ForegroundColor White
    Write-Host "    或: https://github.com/PowerShell/PowerShell/releases" -ForegroundColor White
    Write-Host ""
    Write-Host "  方式3: 使用 Microsoft Store" -ForegroundColor Yellow
    Write-Host "    搜索 'PowerShell' 并安装" -ForegroundColor White
    Write-Host ""
    
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "提示:" -ForegroundColor Cyan
    Write-Host "  * 安装后,您的系统将同时拥有两个版本" -ForegroundColor White
    Write-Host "  * Windows PowerShell 5.1: 运行 'powershell.exe'" -ForegroundColor Gray
    Write-Host "  * PowerShell 7+: 运行 'pwsh.exe'" -ForegroundColor Gray
    Write-Host "  * 您现有的脚本大多可以直接在新版本中运行" -ForegroundColor White
    Write-Host ""
    
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "是否立即打开下载页面? (Y/N): " -ForegroundColor Yellow -NoNewline
    $openPage = Read-Host
    
    if ($openPage -eq "Y" -or $openPage -eq "y") {
        Write-Host ""
        Write-Host "正在打开下载页面..." -ForegroundColor Green
        Start-Process "https://aka.ms/PSWindows"
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "您可以稍后访问: https://aka.ms/PSWindows" -ForegroundColor Cyan
        Write-Host ""
    }
    
} elseif ($edition -eq "Core") {
    $majorVersion = $currentVersion.Major
    
    Write-Host "您正在使用 PowerShell Core (现代版本)" -ForegroundColor Green
    Write-Host ""
    
    if ($majorVersion -lt 7) {
        Write-Host "当前版本 $currentVersion 较旧" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "建议升级到 PowerShell 7.4+ (LTS)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  升级命令:" -ForegroundColor Yellow
        Write-Host "    winget upgrade Microsoft.PowerShell" -ForegroundColor White
        Write-Host ""
    } elseif ($majorVersion -eq 7) {
        $minorVersion = $currentVersion.Minor
        
        if ($minorVersion -lt 4) {
            Write-Host "当前版本 $currentVersion" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "建议升级到 PowerShell 7.4+ (LTS长期支持版)" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  最新LTS版本特性:" -ForegroundColor Yellow
            Write-Host "    + 长期支持 (3年)" -ForegroundColor Green
            Write-Host "    + 性能优化" -ForegroundColor Green
            Write-Host "    + 安全更新" -ForegroundColor Green
            Write-Host "    + Bug修复" -ForegroundColor Green
            Write-Host ""
            Write-Host "  升级命令:" -ForegroundColor Yellow
            Write-Host "    winget upgrade Microsoft.PowerShell" -ForegroundColor White
            Write-Host ""
        } else {
            Write-Host "您的PowerShell版本已是较新版本!" -ForegroundColor Green
            Write-Host ""
            Write-Host "  检查更新:" -ForegroundColor Yellow
            Write-Host "    winget upgrade Microsoft.PowerShell" -ForegroundColor White
            Write-Host ""
        }
    } else {
        Write-Host "您的PowerShell版本非常新!" -ForegroundColor Green
        Write-Host ""
    }
    
    Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "保持更新:" -ForegroundColor Cyan
    Write-Host "  * 定期检查: winget upgrade Microsoft.PowerShell" -ForegroundColor White
    Write-Host "  * 查看更新日志: https://github.com/PowerShell/PowerShell/releases" -ForegroundColor White
    Write-Host ""
}

Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "参考链接:" -ForegroundColor Cyan
Write-Host "  * 官方网站: https://aka.ms/PSWindows" -ForegroundColor White
Write-Host "  * GitHub: https://github.com/PowerShell/PowerShell" -ForegroundColor White
Write-Host "  * 文档: https://docs.microsoft.com/powershell" -ForegroundColor White
Write-Host ""
Write-Host "-------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
