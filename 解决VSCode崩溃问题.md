# 解决 VS Code 崩溃问题

## 问题原因
VS Code 出现内存溢出（OOM）崩溃，错误代码 `-536870904`

**根本原因：**
- 项目包含 24,310 个文件（太多）
- 1,372 个 `__pycache__` 缓存目录
- `.venv` 虚拟环境被 VS Code 扫描

## 已实施的解决方案

### 1. 清理缓存文件
运行清理脚本：
```powershell
.\清理缓存文件.ps1
```

**效果：** 删除 1,372 个缓存目录，文件数从 24,310 降至 14,593

### 2. VS Code 配置优化
已创建 `.vscode/settings.json`，配置了：
- `files.exclude` - 隐藏不需要的文件
- `search.exclude` - 搜索时排除缓存
- `files.watcherExclude` - 不监控缓存变化
- `python.analysis.exclude` - Python 分析排除目录

**排除的目录：**
- `__pycache__`
- `.venv` / `venv`
- `学习数据仓库`
- `实际数据`
- `.git`
- `.vs`

## 使用建议

### 定期清理
建议每周运行一次清理脚本：
```powershell
.\清理缓存文件.ps1
```

### 防止缓存累积
在 `.gitignore` 中已配置忽略缓存文件，确保不会提交到 Git

### 如果再次崩溃
1. 关闭 VS Code
2. 运行清理脚本
3. 重新打开 VS Code

### 长期优化建议
1. 考虑将大型数据文件移到项目外
2. 定期清理不用的备份文件
3. 使用 `.vscode/settings.json` 排除更多不需要的目录

## 技术细节
- Python 会在每个包目录生成 `__pycache__`
- 这些缓存文件会随着项目运行不断累积
- VS Code 默认会扫描所有文件，导致内存占用过高
