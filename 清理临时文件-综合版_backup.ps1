# 缁煎悎娓呯悊鑴氭湰 - 娓呯悊涓存椂鏂囦欢銆佹祴璇曡剼鏈€佸啑浣欐枃妗?
# 鍒涘缓鏃堕棿: 2025-11-22
# 璇存槑: 鍒犻櫎璋冭瘯杩囩▼涓骇鐢熺殑涓存椂鏂囦欢鍜屽凡瀹屾垚椤圭洰鐨勬姤鍛婃枃妗?

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "馃Ч 椤圭洰鏂囦欢缁煎悎娓呯悊" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 鍒涘缓澶囦唤鐩綍
$backupDir = "鍒犻櫎鏂囦欢澶囦唤_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "馃摝 鍒涘缓澶囦唤鐩綍: $backupDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host ""

# Python娴嬭瘯鑴氭湰
$pyFilesToDelete = @(
    "add_remaining_stock_column.py",
    "check_product_sku.py",
    "check_stock.py",
    "verify_stock.py",
    "test_stock_loading.py",
    "verify_calculation_logic.py",
    "test.py",
    "妫€鏌ユ暟鎹簱鎴愭湰.py",
    "妫€鏌ョゥ鍜岃矾鎴愭湰.py",
    "妫€鏌xcel鎴愭湰.py",
    "妫€鏌rder琛╟ost瀛楁.py",
    "楠岃瘉绁ュ拰璺垚鏈?py",
    "鐩存帴璁＄畻绁ュ拰璺垚鏈?py",
    "妫€鏌ラ噸澶嶈鍗?py"
)

# 鎵瑰鐞嗚剼鏈?
$batFilesToDelete = @(
    "瀵煎叆鏁版嵁.bat",
    "琛ュ厖娓呯悊.bat",
    "鎵ц娓呯悊_瀹夊叏鐗?bat",
    "鎺ㄩ€佸墠妫€鏌?bat",
    "鎺ㄩ€佸埌Github.bat",
    "鎺ㄩ€佽惀閿€鍒嗘瀽鏂囦欢.bat"
)

# PowerShell鑴氭湰
$ps1FilesToDelete = @(
    "git_clone_fresh.ps1",
    "鍒濆鍖朑it浠撳簱.ps1",
    "妫€鏌emurai瀹夎.ps1",
    "妫€鏌ヨ惀閿€鍒嗘瀽鏂囦欢.ps1"
)

# Markdown鏂囨。 (淇濈暀: 寰呭崌绾Waitress鐢熶骇鏈嶅姟鍣?md, 鍚庣画浼樺寲璁″垝.md)
$mdFilesToDelete = @(
    "Redis缂撳瓨闆嗘垚瀹屾垚鎶ュ憡.md",
    "UI_UX浼樺寲瀹屾垚鎶ュ憡.md",
    "鍚姩鑴氭湰娴嬭瘯鎶ュ憡.md",
    "瀵煎叆鑴氭湰涓氬姟閫昏緫淇鎶ュ憡.md",
    "鏂囦欢娓呯悊鍒嗘瀽鎶ュ憡.md",
    "娓呯悊瀹屾垚鎶ュ憡.md",
    "鏂扮數鑴戦厤缃姸鎬佹姤鍛?md",
    "requirements杩借釜绯荤粺娴嬭瘯鎶ュ憡.md",
    "蹇€熷紑濮嬫寚鍗?md",
    "README_Dash鐗堜娇鐢ㄦ寚鍗?md",
    "鏅鸿兘闂ㄥ簵缁忚惀鐪嬫澘_浣跨敤鎸囧崡.md",
    "鏁版嵁搴撻厤缃揩閫熸寚鍗?md",
    "requirements杩借釜-蹇€熷紑濮?md",
    "鏃舵涓庡満鏅嚜鍔ㄧ敓鎴愬揩閫熷弬鑰?md",
    "B鐢佃剳鍏嬮殕娓呭崟.md",
    "Github鎺ㄩ€佹枃浠舵竻鍗?md",
    "瀹屾暣鎺ㄩ€佺‘璁ゆ竻鍗?md",
    "鏁版嵁閲忚瘎浼版姤鍛?md"
)

# 鍏朵粬鏂囦欢
$otherFilesToDelete = @(
    "鎴愭湰楠岃瘉缁撴灉.txt",
    "result.txt"
)

# 鏂囦欢澶?
$foldersToDelete = @(
    "寰呭垹闄ゆ枃浠禵20251119_175725",
    "寰呭垹闄ゆ枃浠禵鍛ㄤ笁022511_180718"
)

Write-Host "馃搵 灏嗗垹闄ょ殑鍐呭:" -ForegroundColor Yellow
Write-Host ""
Write-Host "馃悕 Python娴嬭瘯鑴氭湰 ($($pyFilesToDelete.Count)涓?:" -ForegroundColor Cyan
$pyFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "馃摐 鎵瑰鐞嗚剼鏈?($($batFilesToDelete.Count)涓?:" -ForegroundColor Cyan
$batFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "鈿?PowerShell鑴氭湰 ($($ps1FilesToDelete.Count)涓?:" -ForegroundColor Cyan
$ps1FilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "馃搫 Markdown鏂囨。 ($($mdFilesToDelete.Count)涓?:" -ForegroundColor Cyan
$mdFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "馃搼 鍏朵粬鏂囦欢 ($($otherFilesToDelete.Count)涓?:" -ForegroundColor Cyan
$otherFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "馃搧 鏂囦欢澶?($($foldersToDelete.Count)涓?:" -ForegroundColor Cyan
$foldersToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "鎬昏: $($pyFilesToDelete.Count + $batFilesToDelete.Count + $ps1FilesToDelete.Count + $mdFilesToDelete.Count + $otherFilesToDelete.Count) 涓枃浠?+ $($foldersToDelete.Count) 涓枃浠跺す" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "纭鍒犻櫎? (yes/no)"

if ($confirmation -eq "yes") {
    $totalDeleted = 0
    $totalNotFound = 0
    $totalBackedUp = 0
    
    Write-Host ""
    Write-Host "寮€濮嬪浠藉苟鍒犻櫎鏂囦欢..." -ForegroundColor Cyan
    Write-Host ""
    
    # 鍒犻櫎Python鏂囦欢
    Write-Host "姝ｅ湪澶勭悊Python鏂囦欢..." -ForegroundColor Yellow
    foreach ($file in $pyFilesToDelete) {
        if (Test-Path $file) {
            # 澶囦唤
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            # 鍒犻櫎
            Remove-Item $file -Force
            Write-Host "鉁?$file (宸插浠?" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 鍒犻櫎鎵瑰鐞嗘枃浠?
    Write-Host ""
    Write-Host "姝ｅ湪澶勭悊鎵瑰鐞嗘枃浠?.." -ForegroundColor Yellow
    foreach ($file in $batFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "鉁?$file (宸插浠?" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 鍒犻櫎PowerShell鏂囦欢
    Write-Host ""
    Write-Host "姝ｅ湪澶勭悊PowerShell鑴氭湰..." -ForegroundColor Yellow
    foreach ($file in $ps1FilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "鉁?$file (宸插浠?" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 鍒犻櫎Markdown鏂囦欢
    Write-Host ""
    Write-Host "姝ｅ湪澶勭悊Markdown鏂囨。..." -ForegroundColor Yellow
    foreach ($file in $mdFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "鉁?$file (宸插浠?" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 鍒犻櫎鍏朵粬鏂囦欢
    Write-Host ""
    Write-Host "姝ｅ湪澶勭悊鍏朵粬鏂囦欢..." -ForegroundColor Yellow
    foreach ($file in $otherFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "鉁?$file (宸插浠?" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 鍒犻櫎鏂囦欢澶?
    Write-Host ""
    Write-Host "姝ｅ湪澶勭悊鏂囦欢澶?.." -ForegroundColor Yellow
    foreach ($folder in $foldersToDelete) {
        if (Test-Path $folder) {
            $folderBackup = Join-Path $backupDir $folder
            Copy-Item $folder -Destination $folderBackup -Recurse -Force
            $totalBackedUp++
            Remove-Item $folder -Recurse -Force
            Write-Host "鉁?$folder\ (宸插浠?" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "鉁?娓呯悊瀹屾垚!" -ForegroundColor Green
    Write-Host "宸插浠? $totalBackedUp 椤?鈫?$backupDir\" -ForegroundColor Cyan
    Write-Host "宸插垹闄? $totalDeleted 椤? -ForegroundColor Green
    if ($totalNotFound -gt 0) {
        Write-Host "鏈壘鍒? $totalNotFound 椤? -ForegroundColor Yellow
    }
    Write-Host "===========================================" -ForegroundColor Cyan
    
} else {
    Write-Host ""
    Write-Host "鉂?宸插彇娑堟竻鐞嗘搷浣? -ForegroundColor Red
}

Write-Host ""
Write-Host "馃挕 宸蹭繚鐣欑殑閲嶈鏂囨。:" -ForegroundColor Cyan
Write-Host "   鉁?README.md (椤圭洰涓绘枃妗?" -ForegroundColor Gray
Write-Host "   鉁?銆愭潈濞併€戜笟鍔￠€昏緫涓庢暟鎹瓧鍏稿畬鏁存墜鍐?md" -ForegroundColor Gray
Write-Host "   鉁?鏅鸿兘闂ㄥ簵鐪嬫澘_Dash鐗堜娇鐢ㄦ寚鍗?md" -ForegroundColor Gray
Write-Host "   鉁?鏂扮數鑴戝畬鏁撮厤缃寚鍗?md" -ForegroundColor Gray
Write-Host "   鉁?PostgreSQL鐜閰嶇疆瀹屾暣鎸囧崡.md" -ForegroundColor Gray
Write-Host "   鉁?Redis瀹夎閰嶇疆鎸囧崡.md" -ForegroundColor Gray
Write-Host "   鉁?Git浣跨敤鎸囧崡.md" -ForegroundColor Gray
Write-Host "   鉁?寰呭崌绾Waitress鐢熶骇鏈嶅姟鍣?md (淇濈暀)" -ForegroundColor Cyan
Write-Host "   鉁?鍚庣画浼樺寲璁″垝.md (淇濈暀)" -ForegroundColor Cyan
Write-Host ""
Write-Host "馃捑 澶囦唤浣嶇疆: $backupDir\" -ForegroundColor Yellow
Write-Host "   濡傞渶鎭㈠,鍙粠姝ょ洰褰曞鍒舵枃浠? -ForegroundColor Gray
Write-Host ""

