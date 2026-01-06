#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    V8.9.1 启动并测试脚本
    
.DESCRIPTION
    自动启动看板并提供测试指引
    
.EXAMPLE
    .\启动并测试V8.9.1.ps1
#>

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " V8.9.1 启动并测试" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 运行自检
Write-Host "🔍 步骤 1/3: 运行系统自检..." -ForegroundColor Yellow
Write-Host ""
python 简易启动自检.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 自检失败，请先解决问题" -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "✅ 自检通过" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# 2. 测试修复
Write-Host "🔍 步骤 2/3: 测试 html.Style 修复..." -ForegroundColor Yellow
Write-Host ""
python 测试html_Style修复.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 修复测试失败" -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "✅ 修复测试通过" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# 3. 启动看板
Write-Host "🚀 步骤 3/3: 启动看板..." -ForegroundColor Yellow
Write-Host ""
Write-Host "即将启动看板，请按照以下步骤测试：" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 测试步骤：" -ForegroundColor White
Write-Host "  1. 等待看板启动完成" -ForegroundColor Gray
Write-Host "  2. 访问 http://localhost:8051" -ForegroundColor Gray
Write-Host "  3. 进入【今日必做】Tab" -ForegroundColor Gray
Write-Host "  4. 点击【商品健康度分析】" -ForegroundColor Gray
Write-Host "  5. 选择门店和时间范围" -ForegroundColor Gray
Write-Host "  6. 点击【开始分析】" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ 验证点：" -ForegroundColor White
Write-Host "  • 表格应该正常显示" -ForegroundColor Gray
Write-Host "  • 样式完整（圆角、字体、颜色）" -ForegroundColor Gray
Write-Host "  • 分类颜色正确（明星商品=绿色等）" -ForegroundColor Gray
Write-Host "  • 斑马纹显示正常" -ForegroundColor Gray
Write-Host "  • 无控制台错误" -ForegroundColor Gray
Write-Host ""
Write-Host "按回车键启动看板..." -ForegroundColor Yellow
$null = Read-Host

# 启动看板
.\启动看板.ps1
