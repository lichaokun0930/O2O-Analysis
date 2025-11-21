# Demo依赖安装脚本
Write-Host "=" -NoNewline; Write-Host ("="*59)
Write-Host "📦 安装三个UI方案的依赖包"
Write-Host "=" -NoNewline; Write-Host ("="*59)

Write-Host "`n🔧 方案A: Mantine UI 依赖" -ForegroundColor Cyan
pip install dash-mantine-components dash-iconify

Write-Host "`n🔧 方案B: Ant Design 依赖" -ForegroundColor Cyan
pip install feffery-antd-components

Write-Host "`n🔧 方案C: CSS定制 (无额外依赖)" -ForegroundColor Cyan
Write-Host "✅ 方案C使用纯CSS，无需安装额外包" -ForegroundColor Green

Write-Host "`n✅ 依赖安装完成！" -ForegroundColor Green
Write-Host "=" -NoNewline; Write-Host ("="*59)
Write-Host "`n📍 现在可以运行三个demo了:"
Write-Host "   方案A: python demo_方案A_Mantine.py      (端口8881)"
Write-Host "   方案B: python demo_方案B_AntDesign.py    (端口8882)"
Write-Host "   方案C: python demo_方案C_CSS定制.py       (端口8883)"
Write-Host "=" -NoNewline; Write-Host ("="*59)
