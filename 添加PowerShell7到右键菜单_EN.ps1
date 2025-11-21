# PowerShell 7+ Right-Click Menu Setup
# Requires Administrator privileges

# Check admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Red
    Write-Host "                   Administrator Rights Required                     " -ForegroundColor Red
    Write-Host "=====================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this script as administrator" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "           Add PowerShell 7+ to Right-Click Menu                     " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Find PowerShell 7+ path
$pwshPath = $null
$possiblePaths = @(
    "C:\Program Files\PowerShell\7\pwsh.exe",
    "C:\Program Files\PowerShell\7-preview\pwsh.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $pwshPath = $path
        Write-Host "Found PowerShell 7+: $path" -ForegroundColor Green
        break
    }
}

if (-not $pwshPath) {
    Write-Host "Error: PowerShell 7+ not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install first: winget install Microsoft.PowerShell" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

Write-Host ""
Write-Host "Configuring right-click menu..." -ForegroundColor Yellow
Write-Host ""

try {
    # 1. Folder background context menu (Shift+Right-click on empty space)
    $regPath1 = "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\PowerShell7"
    New-Item -Path $regPath1 -Force | Out-Null
    Set-ItemProperty -Path $regPath1 -Name "(default)" -Value "Open PowerShell 7 here" -Force
    Set-ItemProperty -Path $regPath1 -Name "Icon" -Value $pwshPath -Force
    Set-ItemProperty -Path $regPath1 -Name "Extended" -Value "" -Force
    
    $commandPath1 = "$regPath1\command"
    New-Item -Path $commandPath1 -Force | Out-Null
    $cmd1 = "`"$pwshPath`" -NoExit -Command `"Set-Location '%V'`""
    Set-ItemProperty -Path $commandPath1 -Name "(default)" -Value $cmd1 -Force
    
    Write-Host "[OK] Added to folder background menu (Shift+Right-click)" -ForegroundColor Green
    
    # 2. Folder context menu (Shift+Right-click on folder)
    $regPath2 = "Registry::HKEY_CLASSES_ROOT\Directory\shell\PowerShell7"
    New-Item -Path $regPath2 -Force | Out-Null
    Set-ItemProperty -Path $regPath2 -Name "(default)" -Value "Open PowerShell 7 here" -Force
    Set-ItemProperty -Path $regPath2 -Name "Icon" -Value $pwshPath -Force
    Set-ItemProperty -Path $regPath2 -Name "Extended" -Value "" -Force
    
    $commandPath2 = "$regPath2\command"
    New-Item -Path $commandPath2 -Force | Out-Null
    $cmd2 = "`"$pwshPath`" -NoExit -Command `"Set-Location '%V'`""
    Set-ItemProperty -Path $commandPath2 -Name "(default)" -Value $cmd2 -Force
    
    Write-Host "[OK] Added to folder menu (Shift+Right-click)" -ForegroundColor Green
    
    # 3. Drive context menu (Shift+Right-click on drive)
    $regPath3 = "Registry::HKEY_CLASSES_ROOT\Drive\shell\PowerShell7"
    New-Item -Path $regPath3 -Force | Out-Null
    Set-ItemProperty -Path $regPath3 -Name "(default)" -Value "Open PowerShell 7 here" -Force
    Set-ItemProperty -Path $regPath3 -Name "Icon" -Value $pwshPath -Force
    Set-ItemProperty -Path $regPath3 -Name "Extended" -Value "" -Force
    
    $commandPath3 = "$regPath3\command"
    New-Item -Path $commandPath3 -Force | Out-Null
    $cmd3 = "`"$pwshPath`" -NoExit -Command `"Set-Location '%V'`""
    Set-ItemProperty -Path $commandPath3 -Name "(default)" -Value $cmd3 -Force
    
    Write-Host "[OK] Added to drive menu (Shift+Right-click)" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Configuration completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "How to use:" -ForegroundColor Yellow
    Write-Host "  1. Shift+Right-click on any folder empty space" -ForegroundColor White
    Write-Host "  2. Shift+Right-click on any folder" -ForegroundColor White
    Write-Host "  3. Shift+Right-click on any drive" -ForegroundColor White
    Write-Host ""
    Write-Host "  You will see: 'Open PowerShell 7 here'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Note: You may need to restart Explorer to see the new menu" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Restart Explorer now? (Y/N): " -ForegroundColor Yellow -NoNewline
    $restart = Read-Host
    
    if ($restart -eq "Y" -or $restart -eq "y") {
        Write-Host ""
        Write-Host "Restarting Explorer..." -ForegroundColor Green
        Stop-Process -Name explorer -Force
        Start-Sleep -Seconds 2
        Start-Process explorer
        Write-Host "Done!" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "You can manually restart Explorer later:" -ForegroundColor Cyan
        Write-Host "  Task Manager -> Windows Explorer -> Restart" -ForegroundColor Gray
        Write-Host ""
    }
    
} catch {
    Write-Host ""
    Write-Host "[Error] Configuration failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
