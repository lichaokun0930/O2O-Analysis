# GLM-4.6三阶段优化 - 依赖安装脚本

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "GLM-4.6三阶段优化 - 依赖安装" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# 阶段1依赖 (必需)
Write-Host "`n【阶段1】Prompt工程优化 - 基础依赖" -ForegroundColor Yellow
Write-Host "安装: zhipuai python-dotenv" -ForegroundColor White

pip install zhipuai python-dotenv

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 阶段1依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "❌ 阶段1依赖安装失败" -ForegroundColor Red
}

# 阶段2依赖 (可选)
Write-Host "`n【阶段2】PandasAI集成 - 可选依赖" -ForegroundColor Yellow
Write-Host "安装: pandasai" -ForegroundColor White

$response = Read-Host "是否安装阶段2依赖? (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    pip install pandasai
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 阶段2依赖安装成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 阶段2依赖安装失败" -ForegroundColor Red
    }
} else {
    Write-Host "⏭️ 跳过阶段2依赖" -ForegroundColor Gray
}

# 阶段3依赖 (可选)
Write-Host "`n【阶段3】向量检索+RAG - 可选依赖" -ForegroundColor Yellow
Write-Host "安装: chromadb sentence-transformers" -ForegroundColor White

$response = Read-Host "是否安装阶段3依赖? (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    pip install chromadb sentence-transformers
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 阶段3依赖安装成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 阶段3依赖安装失败" -ForegroundColor Red
    }
} else {
    Write-Host "⏭️ 跳过阶段3依赖" -ForegroundColor Gray
}

# 验证安装
Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "安装验证" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

Write-Host "`n运行快速验证脚本..." -ForegroundColor White
python "快速验证GLM优化.py"

Write-Host "`n✅ 依赖安装完成!" -ForegroundColor Green
Write-Host "`n📝 下一步:" -ForegroundColor Yellow
Write-Host "   1. 运行测试: python 测试GLM优化_三阶段.py" -ForegroundColor White
Write-Host "   2. 查看文档: GLM-4.6三阶段优化完整指南.md" -ForegroundColor White
