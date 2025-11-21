Write-Host "Checking Memurai installation..." -ForegroundColor Cyan

# Check installation directory
$paths = @(
    "C:\Program Files\Memurai",
    "C:\Program Files (x86)\Memurai",
    "C:\Memurai"
)

$found = $false
foreach ($path in $paths) {
    if (Test-Path $path) {
        Write-Host "Found at: $path" -ForegroundColor Green
        Get-ChildItem $path | Select-Object Name, Length | Format-Table
        $found = $true
    }
}

if (-not $found) {
    Write-Host "Memurai directory not found" -ForegroundColor Red
}

# Check service
Write-Host "`nChecking Memurai service..." -ForegroundColor Cyan
$service = Get-Service | Where-Object {$_.Name -like "*memurai*" -or $_.DisplayName -like "*memurai*"}
if ($service) {
    $service | Format-Table Name, Status, StartType
} else {
    Write-Host "Memurai service not found" -ForegroundColor Red
}

# Check if download file exists
Write-Host "`nChecking download folder..." -ForegroundColor Cyan
$downloads = "$env:USERPROFILE\Downloads"
Get-ChildItem $downloads -Filter "*emurai*.msi" -ErrorAction SilentlyContinue | Select-Object Name, LastWriteTime
