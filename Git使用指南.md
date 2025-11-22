# 📦 Git 使用指南 - 日常推送和克隆

**项目**: O2O智能门店经营看板  
**仓库**: lichaokun0930/O2O-Analysis

---

## 🚀 快速使用

### 每日工作流程

#### 早上开始工作
```powershell
# 方式1: 完整的早晨例程(推荐)
.\daily_workflow.ps1 start

# 方式2: 仅拉取最新代码
.\git_pull.ps1
```

#### 晚上结束工作
```powershell
# 完整的晚间例程(提交、推送、备份)
.\daily_workflow.ps1 end
```

---

## 📋 脚本说明

### 1. `git_pull.ps1` - 拉取最新代码

**用途**: 从GitHub获取最新代码

**使用**:
```powershell
.\git_pull.ps1
```

**功能**:
- 检查本地是否有未提交的更改
- 如有更改,提示是否暂存(stash)
- 从GitHub拉取最新代码
- 显示更新的文件和提交历史

**适用场景**:
- 早上开始工作前
- 其他团队成员推送代码后
- 切换工作电脑前

---

### 2. `git_push.ps1` - 推送代码到GitHub

**用途**: 将本地修改推送到GitHub

**使用**:
```powershell
# 使用默认提交信息
.\git_push.ps1

# 使用自定义提交信息
.\git_push.ps1 "修复了利润计算bug"
```

**功能**:
- 添加所有更改的文件
- 提交更改(带时间戳或自定义信息)
- 推送到GitHub远程仓库
- 显示推送状态

**适用场景**:
- 完成一个功能模块后
- 修复bug后
- 晚上下班前

---

### 3. `git_sync.ps1` - 同步代码(拉取+推送)

**用途**: 先拉取最新代码,再推送本地修改

**使用**:
```powershell
# 使用默认提交信息
.\git_sync.ps1

# 使用自定义提交信息
.\git_sync.ps1 "添加了新的分析功能"
```

**功能**:
- 先执行`git_pull.ps1`拉取最新代码
- 再执行`git_push.ps1`推送本地修改
- 确保代码同步到最新状态

**适用场景**:
- 多人协作时
- 需要确保代码最新的情况
- 日常提交工作成果

---

### 4. `git_clone_fresh.ps1` - 克隆新副本

**用途**: 克隆仓库到新位置(全新环境)

**使用**:
```powershell
.\git_clone_fresh.ps1
```

**功能**:
- 自动获取当前仓库URL
- 克隆到新目录(带时间戳)
- 可选自动创建虚拟环境并安装依赖
- 提供后续配置步骤指引

**适用场景**:
- 新电脑配置
- 创建测试环境
- 隔离开发环境
- 回退到干净状态

---

### 5. `daily_workflow.ps1` - 日常工作流

**用途**: 自动化每日开始/结束工作流程

**使用**:
```powershell
# 早上开始工作
.\daily_workflow.ps1 start

# 晚上结束工作
.\daily_workflow.ps1 end
```

**早晨例程(start)**:
1. 拉取最新代码
2. 检查Python依赖
3. 启动PostgreSQL和Redis服务
4. 检查数据库连接
5. 显示快速命令提示

**晚间例程(end)**:
1. 停止看板进程
2. 可选备份数据库
3. 提交并推送今日修改
4. 可选停止后台服务

**适用场景**:
- 规律的日常开发
- 确保代码及时提交
- 保持开发环境整洁

---

## 📖 常见场景示例

### 场景1: 早上开始工作

```powershell
# 一键启动工作环境
.\daily_workflow.ps1 start

# 或手动执行
.\git_pull.ps1
.\启动看板.ps1
```

### 场景2: 完成一个功能

```powershell
# 提交并推送
.\git_push.ps1 "完成了商品四象限分析功能"

# 或同步(更安全)
.\git_sync.ps1 "完成了商品四象限分析功能"
```

### 场景3: 晚上下班

```powershell
# 一键结束工作
.\daily_workflow.ps1 end

# 会提示你:
# - 是否备份数据库
# - 输入提交信息
# - 是否停止服务
```

### 场景4: 克隆到新电脑

```powershell
# 在旧电脑上推送最新代码
.\git_push.ps1 "最新版本"

# 在新电脑上克隆
git clone https://github.com/lichaokun0930/O2O-Analysis.git
cd O2O-Analysis

# 或使用脚本
.\git_clone_fresh.ps1

# 然后配置环境
.\setup_new_pc.ps1
```

### 场景5: 团队协作

```powershell
# 每次修改前先拉取
.\git_pull.ps1

# 修改代码...

# 修改后立即推送
.\git_push.ps1 "描述你的修改"

# 或使用同步(推荐)
.\git_sync.ps1 "描述你的修改"
```

---

## 🔧 Git基础命令参考

### 查看状态
```powershell
# 查看当前状态
git status

# 查看简洁状态
git status --short

# 查看提交历史
git log --oneline -10
```

### 分支操作
```powershell
# 查看当前分支
git branch

# 创建新分支
git branch feature-new-analysis

# 切换分支
git checkout feature-new-analysis

# 创建并切换
git checkout -b feature-new-analysis

# 合并分支
git merge feature-new-analysis
```

### 撤销操作
```powershell
# 撤销工作区修改
git checkout -- filename.py

# 撤销暂存区
git reset HEAD filename.py

# 撤销最后一次提交(保留修改)
git reset --soft HEAD~1

# 完全撤销最后一次提交
git reset --hard HEAD~1
```

### 暂存操作
```powershell
# 暂存当前修改
git stash

# 查看暂存列表
git stash list

# 恢复暂存
git stash pop

# 恢复特定暂存
git stash apply stash@{0}
```

---

## ⚠️ 注意事项

### 推送前检查

1. **确保代码能运行**
   ```powershell
   # 测试主程序
   python 智能门店看板_Dash版.py --check
   ```

2. **不要推送敏感信息**
   - .env文件已在.gitignore中(包含密码)
   - 数据库备份文件不要推送
   - 个人API密钥不要推送

3. **大文件处理**
   - Excel数据文件不要推送(放在本地)
   - 生成的图片/报告不要推送
   - 日志文件不要推送

### 冲突处理

如果出现合并冲突:

```powershell
# 1. 查看冲突文件
git status

# 2. 编辑冲突文件,手动解决冲突
# 查找 <<<<<<< HEAD 标记

# 3. 标记为已解决
git add conflicted_file.py

# 4. 完成合并
git commit -m "解决合并冲突"

# 5. 推送
git push origin master
```

### 忘记推送

如果本地有很多未推送的提交:

```powershell
# 查看未推送的提交
git log origin/master..HEAD

# 确认后推送
git push origin master
```

---

## 📊 .gitignore 配置

确保以下文件/目录不被提交:

```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/

# 环境配置
.env
.env.local

# 数据库
*.db
*.sqlite3
verify_check/数据库导出/

# 数据文件
*.xlsx
*.xls
*.csv
data/
backups/

# 日志
logs/
*.log

# 缓存
*.cache
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp

# 系统文件
.DS_Store
Thumbs.db
```

---

## 🎯 最佳实践

### 提交信息规范

```powershell
# 功能开发
git commit -m "feat: 添加商品生命周期分析功能"

# Bug修复
git commit -m "fix: 修复利润率计算错误"

# 文档更新
git commit -m "docs: 更新使用指南"

# 性能优化
git commit -m "perf: 优化数据库查询性能"

# 代码重构
git commit -m "refactor: 重构场景分析模块"

# 测试相关
git commit -m "test: 添加利润计算单元测试"
```

### 分支策略

```
master (主分支) - 生产环境代码
    ↓
develop (开发分支) - 开发中的代码
    ↓
feature-xxx (功能分支) - 单个功能开发
```

### 定期操作

- **每天早上**: 拉取最新代码
- **每次修改后**: 及时提交
- **每天下班**: 推送代码到GitHub
- **每周**: 清理无用分支
- **每月**: 检查仓库大小

---

## 🆘 常见问题

### Q1: 推送失败 "rejected"

**原因**: 远程仓库有新提交

**解决**:
```powershell
# 先拉取
.\git_pull.ps1

# 再推送
.\git_push.ps1
```

### Q2: 账号密码验证失败

**原因**: GitHub不再支持密码认证

**解决**:
1. 生成Personal Access Token
   - 访问: https://github.com/settings/tokens
   - 点击 "Generate new token"
   - 选择权限: repo
2. 使用token替代密码

### Q3: 仓库过大

**原因**: 包含了大文件

**解决**:
```powershell
# 查找大文件
git ls-files | xargs du -h | sort -rh | head -20

# 从历史中删除
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
```

### Q4: 误推送敏感信息

**解决**:
1. 立即修改密码
2. 从历史中删除
3. 更新.gitignore
4. Force push

---

## 📞 获取帮助

- **Git官方文档**: https://git-scm.com/doc
- **GitHub Help**: https://docs.github.com/
- **项目Issues**: https://github.com/lichaokun0930/O2O-Analysis/issues

---

**快速命令总结**:
```powershell
.\git_pull.ps1                      # 拉取最新代码
.\git_push.ps1 "提交信息"            # 推送代码
.\git_sync.ps1 "提交信息"            # 同步代码
.\git_clone_fresh.ps1               # 克隆新副本
.\daily_workflow.ps1 start          # 早上例程
.\daily_workflow.ps1 end            # 晚上例程
```
