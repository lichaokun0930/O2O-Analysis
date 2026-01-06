# 归档历史文档脚本
# 将有价值的历史文档移动到 docs/archive/ 目录

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "历史文档归档工具" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 创建归档目录结构
$archiveDir = "docs\archive"
$categoriesDir = @{
    '业务分析' = "$archiveDir\业务分析"
    '性能优化' = "$archiveDir\性能优化"
    '功能开发' = "$archiveDir\功能开发"
    '使用指南' = "$archiveDir\使用指南"
    '问题修复' = "$archiveDir\问题修复"
}

Write-Host "📁 创建归档目录..." -ForegroundColor Yellow
foreach ($dir in $categoriesDir.Values) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Write-Host "✅ 目录创建完成" -ForegroundColor Green
Write-Host ""

# 归档函数
function Archive-File {
    param($filePath, $category)
    
    if (Test-Path $filePath) {
        $fileName = Split-Path $filePath -Leaf
        $targetDir = $categoriesDir[$category]
        $targetPath = Join-Path $targetDir $fileName
        
        try {
            Move-Item $filePath $targetPath -ErrorAction Stop
            Write-Host "   ✓ $fileName → $category" -ForegroundColor DarkGray
            return $true
        } catch {
            Write-Host "   ⚠️  归档失败: $fileName - $_" -ForegroundColor Red
            return $false
        }
    }
    return $false
}

$archivedCount = 0

# 1. 业务分析文档
Write-Host "📊 归档业务分析文档..." -ForegroundColor Yellow
$businessDocs = @(
    "今日必做Tab加载缓慢问题分析.md",
    "六象限判定逻辑评估报告.md",
    "动销判定逻辑分析报告.md",
    "动销指数V7.1评估报告.md",
    "周转率问题分析报告.md",
    "基础设施评估报告.md",
    "六象限V7.3保守优化说明.md",
    "六象限与智能调价联动方案评估.md",
    "六象限与调价计算器联动开发说明.md"
)

foreach ($file in $businessDocs) {
    if (Archive-File $file '业务分析') {
        $archivedCount++
    }
}

# 2. 性能优化文档
Write-Host "`n⚡ 归档性能优化文档..." -ForegroundColor Yellow
$perfDocs = @(
    "今日必做优化.md",
    "内存优化方案文档.md",
    "后续优化计划.md",
    "企业级性能优化_实施路线图.md",
    "企业级性能优化_方案D实施文档.md",
    "企业级性能优化方案_完整实施文档.md",
    "企业级缓存扩展方案.md",
    "生产级升级_实施指南.md",
    "生产级升级方案_30-200人.md",
    "待升级_Waitress生产服务器.md"
)

foreach ($file in $perfDocs) {
    if (Archive-File $file '性能优化') {
        $archivedCount++
    }
}

# 3. 功能开发文档
Write-Host "`n🔧 归档功能开发文档..." -ForegroundColor Yellow
$featureDocs = @(
    "智能调价V3.0开发文档.md",
    "智能调价计算器V2开发文档.md",
    "智能调价计算器V3.0开发文档.md",
    "时段与场景业务设计文档.md",
    "商品场景智能打标_快速启动指南.md",
    "商品场景智能打标_集成指南.md",
    "场景营销智能决策引擎_使用指南.md",
    "门店加盟类型字段使用指南.md",
    "门店加盟类型字段部署清单.md"
)

foreach ($file in $featureDocs) {
    if (Archive-File $file '功能开发') {
        $archivedCount++
    }
}

# 4. 使用指南
Write-Host "`n📖 归档使用指南..." -ForegroundColor Yellow
$guideDocs = @(
    "智能门店看板_Dash版使用指南.md",
    "智能门店看板_业务运营使用指南.md",
    "智能门店看板_核心双Tab功能详解.md",
    "智能门店看板_模块功能梳理_业务运营视角.md",
    "智能门店看板_全面优化路线图.md",
    "Tab7八象限分析使用指南.md",
    "Tab1业务逻辑说明文档.md",
    "Tab1订单数据概览_卡片计算公式汇总.md",
    "requirements变更追踪使用指南.md",
    "门店数据清理和空间回收使用指南.md",
    "数据管理-按门店清理指南.md",
    "局域网多人访问指南.md",
    "局域网访问README.md",
    "手动性能测试指南.md",
    "联动功能测试指南.md",
    "启动自检说明.md",
    "启动脚本日志问题说明.md",
    "看板启动模式说明.md"
)

foreach ($file in $guideDocs) {
    if (Archive-File $file '使用指南') {
        $archivedCount++
    }
}

# 5. 问题修复文档
Write-Host "`n🔨 归档问题修复文档..." -ForegroundColor Yellow
$fixDocs = @(
    "商品健康分析导出修复说明.md",
    "商品健康分析周期选择优化报告.md",
    "联动功能BUG修复说明.md",
    "联动功能V3.1修复说明.md",
    "联动功能重新设计方案.md",
    "上传功能优化说明.md",
    "客单价渠道筛选功能说明.md",
    "营销分析功能说明.md",
    "解决VSCode崩溃问题.md",
    "自检报告_操作指南vs代码逻辑.md"
)

foreach ($file in $fixDocs) {
    if (Archive-File $file '问题修复') {
        $archivedCount++
    }
}

# 6. 配置指南（保留在根目录，但创建副本到归档）
Write-Host "`n⚙️  备份配置指南..." -ForegroundColor Yellow
$configDocs = @(
    "PostgreSQL环境配置完整指南.md",
    "PostgreSQL自动启动配置说明.md",
    "PostgreSQL+Redis方案实施总结.md",
    "Redis安装配置指南.md",
    "Redis缓存方案使用指南.md",
    "新电脑完整配置指南.md",
    "依赖和环境说明.md",
    "数据库同步快速参考.md",
    "数据库数据源使用说明.md",
    "同步数据库结构指南.md",
    "两台电脑数据库同步方案.md"
)

foreach ($file in $configDocs) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        $targetPath = Join-Path "$archiveDir\使用指南" $fileName
        try {
            Copy-Item $file $targetPath -ErrorAction Stop
            Write-Host "   ✓ $fileName (已备份)" -ForegroundColor DarkGray
        } catch {
            Write-Host "   ⚠️  备份失败: $fileName" -ForegroundColor Red
        }
    }
}

# 创建归档索引文件
Write-Host "`n📝 创建归档索引..." -ForegroundColor Yellow
$indexContent = @"
# 历史文档归档索引

**归档时间**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 📁 目录结构

\`\`\`
docs/archive/
├── 业务分析/          # 业务逻辑分析、评估报告
├── 性能优化/          # 性能优化方案、实施报告
├── 功能开发/          # 功能开发文档、设计方案
├── 使用指南/          # 各类使用指南、操作手册
└── 问题修复/          # BUG修复、问题解决方案
\`\`\`

## 📊 归档统计

- 业务分析文档: $(($businessDocs | Where-Object { Test-Path (Join-Path $categoriesDir['业务分析'] $_) }).Count) 个
- 性能优化文档: $(($perfDocs | Where-Object { Test-Path (Join-Path $categoriesDir['性能优化'] $_) }).Count) 个
- 功能开发文档: $(($featureDocs | Where-Object { Test-Path (Join-Path $categoriesDir['功能开发'] $_) }).Count) 个
- 使用指南: $(($guideDocs | Where-Object { Test-Path (Join-Path $categoriesDir['使用指南'] $_) }).Count) 个
- 问题修复文档: $(($fixDocs | Where-Object { Test-Path (Join-Path $categoriesDir['问题修复'] $_) }).Count) 个

**总计**: $archivedCount 个文档

## 💡 说明

这些文档具有历史参考价值，但不是日常使用的核心文档。
如需查阅历史信息，可以在对应分类目录中查找。

## 🔍 快速查找

### 业务分析
- 六象限判定逻辑评估报告
- 动销判定逻辑分析报告
- 周转率问题分析报告

### 性能优化
- 企业级性能优化方案
- 生产级升级方案
- 内存优化方案

### 功能开发
- 智能调价开发文档
- 场景智能打标集成指南
- 门店加盟类型字段部署

### 使用指南
- 智能门店看板使用指南
- Tab7八象限分析使用指南
- 局域网多人访问指南

### 问题修复
- 联动功能修复说明
- 商品健康分析修复
- VSCode崩溃问题解决

---

**注意**: 当前版本的文档请查看项目根目录的 V8.9.1 系列文档。
"@

$indexPath = Join-Path $archiveDir "README.md"
$indexContent | Out-File -FilePath $indexPath -Encoding UTF8
Write-Host "✅ 归档索引已创建: $indexPath" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ 归档完成!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 归档统计:" -ForegroundColor Yellow
Write-Host "   已归档文档: $archivedCount 个" -ForegroundColor White
Write-Host "   归档位置: $archiveDir" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Cyan
Write-Host "   - 归档文档已按类别整理" -ForegroundColor Gray
Write-Host "   - 查看 docs\archive\README.md 了解详情" -ForegroundColor Gray
Write-Host "   - 配置指南已保留在根目录" -ForegroundColor Gray
Write-Host ""
