# 🎯 Git 脚本快速参考卡

## 📦 已创建的脚本

| 脚本 | 用途 | 快捷命令 |
|------|------|----------|
| `git_pull.ps1` | 拉取最新代码 | `.\git_pull.ps1` |
| `git_push.ps1` | 推送代码到GitHub | `.\git_push.ps1 "提交信息"` |
| `git_sync.ps1` | 同步(拉取+推送) | `.\git_sync.ps1 "提交信息"` |
| `git_clone_fresh.ps1` | 克隆到新位置 | `.\git_clone_fresh.ps1` |
| `daily_workflow.ps1` | 每日工作流 | `.\daily_workflow.ps1 start/end` |

## ⚡ 一分钟快速上手

### 早上开始工作
```powershell
.\daily_workflow.ps1 start
```
**自动执行**: 拉取代码 → 启动服务 → 检查环境

### 提交修改
```powershell
.\git_push.ps1 "修复了XX问题"
```
**自动执行**: 添加文件 → 提交 → 推送

### 晚上下班
```powershell
.\daily_workflow.ps1 end
```
**自动执行**: 停止服务 → 备份 → 提交推送

### 安全同步(推荐)
```powershell
.\git_sync.ps1 "今日工作完成"
```
**自动执行**: 先拉取 → 再推送(避免冲突)

---

## 📅 典型的一天

### 08:30 - 到达办公室
```powershell
cd "d:\Python\订单数据看板\O2O-Analysis"
.\daily_workflow.ps1 start
```

### 09:00 - 开始编码
```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 启动看板
.\启动看板.ps1
```

### 12:00 - 午休前保存
```powershell
.\git_push.ps1 "上午工作:完成XX功能"
```

### 18:00 - 下班前
```powershell
.\daily_workflow.ps1 end
```

---

## 🔥 常用命令组合

### 场景1: 修改了多个文件
```powershell
# 查看修改
git status

# 推送所有修改
.\git_push.ps1 "更新了商品分析和利润计算"
```

### 场景2: 团队协作
```powershell
# 每次开始前
.\git_pull.ps1

# 修改代码...

# 提交前先同步
.\git_sync.ps1 "添加了新功能"
```

### 场景3: 多台电脑工作
```powershell
# A电脑下班前
.\git_push.ps1 "今日工作"

# B电脑开始前
.\git_pull.ps1
```

### 场景4: 创建测试环境
```powershell
# 克隆到新目录
.\git_clone_fresh.ps1

# 按提示配置环境
```

---

## ⚠️ 重要提醒

### ❌ 不要推送的文件
- `.env` (包含密码)
- `*.xlsx` (数据文件)
- `.venv/` (虚拟环境)
- `verify_check/数据库导出/` (数据库备份)

### ✅ 应该推送的文件
- `*.py` (Python代码)
- `*.ps1` (PowerShell脚本)
- `*.md` (文档)
- `requirements.txt` (依赖清单)
- `database/models.py` (数据库模型)

---

## 🆘 紧急情况处理

### 推送失败
```powershell
# 通常是因为远程有新提交
.\git_pull.ps1   # 先拉取
.\git_push.ps1   # 再推送
```

### 误提交了敏感信息
```powershell
# 1. 立即修改密码
# 2. 删除最后一次提交
git reset --soft HEAD~1
# 3. 修改文件
# 4. 重新提交
.\git_push.ps1 "修正提交"
```

### 代码冲突
```powershell
# 1. 备份当前修改
git stash

# 2. 拉取最新代码
.\git_pull.ps1

# 3. 恢复修改(可能有冲突)
git stash pop

# 4. 手动解决冲突后
.\git_push.ps1 "解决冲突"
```

---

## 📊 脚本功能对比

| 功能 | git_pull | git_push | git_sync | daily_workflow |
|------|----------|----------|----------|----------------|
| 拉取代码 | ✅ | ❌ | ✅ | ✅(start) |
| 推送代码 | ❌ | ✅ | ✅ | ✅(end) |
| 启动服务 | ❌ | ❌ | ❌ | ✅(start) |
| 停止服务 | ❌ | ❌ | ❌ | ✅(end) |
| 备份数据库 | ❌ | ❌ | ❌ | ✅(end) |
| 冲突检测 | ✅ | ❌ | ✅ | ✅ |

---

## 💡 专业技巧

### 技巧1: 使用别名
在PowerShell配置文件中添加:
```powershell
# 打开配置文件
notepad $PROFILE

# 添加别名
function gp { .\git_pull.ps1 }
function gs { param($m) .\git_sync.ps1 $m }
function gps { param($m) .\git_push.ps1 $m }
function work-start { .\daily_workflow.ps1 start }
function work-end { .\daily_workflow.ps1 end }
```

### 技巧2: 定时提交
创建Windows计划任务,每小时自动提交:
```powershell
# 创建任务
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File 'D:\Python\订单数据看板\O2O-Analysis\git_push.ps1'"
$trigger = New-ScheduledTaskTrigger -Once -At 9am -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 9)
Register-ScheduledTask -TaskName "AutoGitPush" -Action $action -Trigger $trigger
```

### 技巧3: 查看提交历史
```powershell
# 图形化历史
git log --graph --oneline --all -10

# 查看某个文件的历史
git log --follow -- "智能门店看板_Dash版.py"

# 查看谁修改了什么
git blame "智能门店看板_Dash版.py"
```

---

## 📖 更多帮助

- 完整文档: `Git使用指南.md`
- 环境配置: `新电脑完整配置指南.md`
- AI开发: `.github\copilot-instructions.md`

---

**记住**: 每日三件事
1. 早上: `.\daily_workflow.ps1 start`
2. 编码: 随时 `.\git_push.ps1 "描述"`
3. 晚上: `.\daily_workflow.ps1 end`
