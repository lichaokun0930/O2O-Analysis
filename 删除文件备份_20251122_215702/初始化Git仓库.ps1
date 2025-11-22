# Git 仓库初始化和推送脚本

Write-Host @"
╔══════════════════════════════════════════════════════════╗
║       📦 Git 仓库初始化向导                                 ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# 检查Git是否安装
Write-Host "`n[1/6] 检查Git环境..." -ForegroundColor Yellow
git --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git未安装，请先安装Git" -ForegroundColor Red
    Write-Host "   下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Git已安装" -ForegroundColor Green

# 初始化Git仓库
Write-Host "`n[2/6] 初始化Git仓库..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "ℹ️  Git仓库已存在，跳过初始化" -ForegroundColor Cyan
} else {
    git init
    Write-Host "✅ Git仓库初始化完成" -ForegroundColor Green
}

# 配置用户信息
Write-Host "`n[3/6] 配置Git用户信息..." -ForegroundColor Yellow
$userName = Read-Host "请输入您的名字（如：张三）"
$userEmail = Read-Host "请输入您的邮箱（如：zhangsan@example.com）"

git config user.name "$userName"
git config user.email "$userEmail"
Write-Host "✅ 用户信息配置完成" -ForegroundColor Green

# 添加所有文件
Write-Host "`n[4/6] 添加文件到暂存区..." -ForegroundColor Yellow
git add .
Write-Host "✅ 文件已添加" -ForegroundColor Green

# 首次提交
Write-Host "`n[5/6] 创建首次提交..." -ForegroundColor Yellow
git commit -m "🎉 初始提交：智能门店经营看板 - PostgreSQL全栈版"
Write-Host "✅ 提交完成" -ForegroundColor Green

# 选择远程仓库
Write-Host @"

[6/6] 配置远程仓库
╔══════════════════════════════════════════════════════════╗
║  选择代码托管平台：                                         ║
║  1. Gitee (码云) - 推荐，国内访问快                          ║
║  2. GitHub - 国际主流平台                                   ║
║  3. 两者都配置（推荐）                                       ║
║  4. 暂不配置                                                ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

$platformChoice = Read-Host "请选择 (1-4)"

function Add-Remote($name, $url) {
    $existing = git remote get-url $name 2>$null
    if ($existing) {
        Write-Host "  ℹ️  远程仓库'$name'已存在: $existing" -ForegroundColor Cyan
    } else {
        git remote add $name $url
        Write-Host "  ✅ 添加远程仓库'$name': $url" -ForegroundColor Green
    }
}

switch ($platformChoice) {
    "1" {
        Write-Host "`n📌 配置Gitee远程仓库..." -ForegroundColor Yellow
        Write-Host "请先在Gitee创建仓库: https://gitee.com/projects/new" -ForegroundColor Cyan
        $giteeUrl = Read-Host "请输入Gitee仓库地址 (如: https://gitee.com/用户名/仓库名.git)"
        Add-Remote "origin" $giteeUrl
    }
    "2" {
        Write-Host "`n📌 配置GitHub远程仓库..." -ForegroundColor Yellow
        Write-Host "请先在GitHub创建仓库: https://github.com/new" -ForegroundColor Cyan
        $githubUrl = Read-Host "请输入GitHub仓库地址 (如: https://github.com/用户名/仓库名.git)"
        Add-Remote "origin" $githubUrl
    }
    "3" {
        Write-Host "`n📌 配置双远程仓库..." -ForegroundColor Yellow
        
        Write-Host "`n  [Gitee]" -ForegroundColor Cyan
        Write-Host "  请先在Gitee创建仓库: https://gitee.com/projects/new" -ForegroundColor Cyan
        $giteeUrl = Read-Host "  Gitee仓库地址"
        Add-Remote "gitee" $giteeUrl
        
        Write-Host "`n  [GitHub]" -ForegroundColor Cyan
        Write-Host "  请先在GitHub创建仓库: https://github.com/new" -ForegroundColor Cyan
        $githubUrl = Read-Host "  GitHub仓库地址"
        Add-Remote "github" $githubUrl
        
        # 设置默认推送到Gitee
        git remote set-url origin $giteeUrl
        Write-Host "`n  ✅ 默认推送到Gitee，可手动推送到GitHub" -ForegroundColor Green
    }
    "4" {
        Write-Host "`n⏭️  跳过远程仓库配置" -ForegroundColor Yellow
    }
    default {
        Write-Host "`n❌ 无效选择" -ForegroundColor Red
        exit 1
    }
}

# 推送到远程
if ($platformChoice -ne "4") {
    Write-Host "`n🚀 准备推送到远程仓库..." -ForegroundColor Yellow
    $push = Read-Host "是否现在推送？(y/n)"
    
    if ($push -eq "y") {
        git branch -M main
        
        if ($platformChoice -eq "3") {
            Write-Host "`n推送到Gitee..." -ForegroundColor Cyan
            git push -u gitee main
            
            $pushGithub = Read-Host "是否也推送到GitHub？(y/n)"
            if ($pushGithub -eq "y") {
                Write-Host "推送到GitHub..." -ForegroundColor Cyan
                git push -u github main
            }
        } else {
            git push -u origin main
        }
        
        Write-Host "`n✅ 推送完成！" -ForegroundColor Green
    } else {
        Write-Host "`n⏭️  已跳过推送，稍后可手动执行: git push -u origin main" -ForegroundColor Yellow
    }
}

# 完成
Write-Host @"

╔══════════════════════════════════════════════════════════╗
║  🎉 Git 仓库配置完成！                                      ║
╠══════════════════════════════════════════════════════════╣
║  📚 常用Git命令：                                           ║
║  - git status       查看文件状态                            ║
║  - git add .        添加所有修改                            ║
║  - git commit -m "说明"  提交修改                           ║
║  - git push         推送到远程                              ║
║  - git pull         拉取最新代码                            ║
║  - git log          查看提交历史                            ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Green

# 显示仓库状态
Write-Host "`n📊 当前仓库状态：" -ForegroundColor Cyan
git status

Write-Host "`n📍 远程仓库：" -ForegroundColor Cyan
git remote -v
