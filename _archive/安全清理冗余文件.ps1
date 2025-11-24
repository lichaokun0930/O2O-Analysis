# ============================================================================
# 安全清理冗余文件脚本
# ============================================================================
# 功能: 将冗余文件移动到临时文件夹,而不是直接删除
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "           测算模型目录 - 安全清理冗余文件                            " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# 创建临时备份文件夹
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFolder = "待删除文件_$timestamp"

Write-Host "准备清理冗余文件..." -ForegroundColor Yellow
Write-Host "备份文件夹: $backupFolder" -ForegroundColor Gray
Write-Host ""

# 定义要清理的文件列表
$filesToClean = @(
    # 测试文件
    "测试requirements追踪.py",
    "测试启动脚本.ps1",
    "测试成本字段.py",
    "测试数据字段.py",
    "测试标准化字段.py",
    "测试看板数据加载.py",
    "测试门店加盟类型字段.py",
    
    # 检查文件
    "检查Excel与看板差异.py",
    "检查Excel数据.py",
    "检查PowerShell版本_兼容版.ps1",
    "检查佣金兜底订单.py",
    "检查利润额来源.py",
    "检查同事环境.ps1",
    "检查当前看板数据.py",
    "检查数据库利润数据.py",
    "检查数据库表.py",
    "检查数据库门店.py",
    "检查枫瑞美团共橙数据.py",
    "检查渠道过滤.py",
    "检查源数据.py",
    "检查物流费.py",
    "检查物流费差异.py",
    "检查看板数据文件.py",
    "检查耗材利润.py",
    "检查耗材订单结构.py",
    "检查订单结构.py",
    "检查门店数据文件夹.py",
    "快速检查耗材.py",
    "快速检查耗材数据.py",
    
    # 验证文件
    "验证all_no_fallback结果.py",
    "验证Line1016影响.py",
    "验证保留剔除耗材.py",
    "验证修复后的利润计算.py",
    "验证兜底逻辑.py",
    "验证商品级剔除.py",
    "验证实际利润公式.py",
    "验证数据分离.py",
    "验证数据库数据.py",
    "验证最终修改结果.py",
    "验证渠道利润计算.py",
    "验证物流配送费聚合.py",
    "验证用户计算.py",
    "验证祥和路利润.py",
    "验证祥和路店利润.py",
    "验证过滤影响.py",
    "快速验证利润.py",
    "完整数据流程验证.py",
    "完整数据流程验证_clean.py",
    "完整自检.py",
    "完整验证数据分离.py",
    
    # 诊断文件
    "诊断利润异常.py",
    "诊断美团共橙负利润.py",
    
    # 对比文件
    "对比三种计算方案.py",
    "对比剔除前后数据.py",
    "对比订单ID和利润额.py",
    "深度对比结果.txt",
    "最终方案对比.py",
    "完整模拟结果.txt",
    
    # 分析追踪文件
    "分析利润差异.py",
    "逐步追踪利润额.py",
    "反推看板数据.py",
    "商品分类结构分析.py",
    "分析冗余文件.py",
    "理解剔除负值逻辑.py",
    "理解耗材逻辑.py",
    "用核心代码计算美团共橙.py",
    "直接调用看板函数验证.py",
    "精确计算枫瑞店利润.py",
    "计算美团共橙利润_不剔除耗材.py",
    "重新理解耗材逻辑.py",
    "最终完整计算.py",
    "最终验证.py",
    
    # 演示Demo
    "demo_price_data.json",
    "分类销售看板布局demo.html",
    "用户复购分析看板demo.html",
    "演示requirements追踪.py",
    
    # 清理脚本 (旧版)
    "清理缓存.py",
    "清理过时文件_安全版.ps1",
    "清除缓存.bat",
    "清空数据库.py",
    "安全清理仓库文件.ps1",
    "安全清理文件.ps1",
    "执行清理.ps1",
    
    # 旧版冗余脚本
    "启动P1_P2_P3.ps1",
    "启动全栈服务.ps1",
    "启动全栈服务_自动.py",
    "快速启动看板.py",
    "快速启动数据库.ps1",
    "定位PowerShell7.ps1",
    "设置PowerShell7为默认.ps1",
    "智能门店看板_简化版.py",
    "智能门店经营看板_可视化.py",
    
    # 临时文件
    "调研结果.txt",
    "营销分析结果.txt",
    "批量替换calc_mode.py",
    "重新导入数据.py",
    "重新导入铜山万达.ps1",
    "已禁用TAB功能归档.py",
    
    # 旧的配置脚本
    "添加PowerShell7到右键菜单.ps1"
)

# 统计
$movedCount = 0
$notFoundCount = 0
$errorCount = 0

# 确认操作
Write-Host "准备移动 $($filesToClean.Count) 个文件到: $backupFolder" -ForegroundColor Yellow
Write-Host ""
Write-Host "文件将被移动(不删除),您可以稍后确认无问题后再删除备份文件夹" -ForegroundColor Cyan
Write-Host ""
Write-Host "是否继续? (Y/N): " -ForegroundColor Yellow -NoNewline
$confirm = Read-Host

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host ""
    Write-Host "操作已取消" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# 创建备份文件夹
Write-Host ""
Write-Host "创建备份文件夹..." -ForegroundColor Green
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null

# 移动文件
Write-Host ""
Write-Host "正在移动文件..." -ForegroundColor Yellow
Write-Host ""

foreach ($file in $filesToClean) {
    if (Test-Path $file) {
        try {
            Move-Item -Path $file -Destination $backupFolder -Force
            Write-Host "[OK] $file" -ForegroundColor Green
            $movedCount++
        } catch {
            Write-Host "[Error] $file - $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
        }
    } else {
        Write-Host "[Not Found] $file" -ForegroundColor Gray
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "清理完成!" -ForegroundColor Green
Write-Host ""
Write-Host "统计信息:" -ForegroundColor Yellow
Write-Host "  已移动文件: $movedCount" -ForegroundColor Green
Write-Host "  未找到: $notFoundCount" -ForegroundColor Gray
Write-Host "  错误: $errorCount" -ForegroundColor Red
Write-Host ""
Write-Host "备份位置: $backupFolder" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示:" -ForegroundColor Yellow
Write-Host "  1. 测试您的应用是否正常运行" -ForegroundColor White
Write-Host "  2. 确认无问题后,可以删除备份文件夹" -ForegroundColor White
Write-Host "  3. 如有问题,可以从备份文件夹恢复文件" -ForegroundColor White
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
