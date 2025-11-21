# 🚀 Requirements追踪系统 - 快速开始

## 📦 已交付文件

| 文件 | 说明 | 状态 |
|------|------|------|
| `tools/track_requirements_changes.py` | 核心追踪工具(520行) | ✅ 已创建 |
| `requirements变更追踪使用指南.md` | 完整使用文档 | ✅ 已创建 |
| `测试requirements追踪.py` | 功能测试脚本 | ✅ 已创建 |
| `.requirements_snapshots/` | 快照存储目录 | ✅ 已创建 |

---

## ⚡ 3步快速上手

### 步骤1: 创建初始快照

```powershell
python tools\track_requirements_changes.py
```

**预期输出:**
```
✅ 初始快照已创建
   📦 记录了 52 个依赖包
   💡 下次运行将开始追踪变更
```

---

### 步骤2: 修改requirements.txt

示例: 添加新包
```powershell
echo "requests==2.31.0" >> requirements.txt
```

---

### 步骤3: 追踪变更

```powershell
python tools\track_requirements_changes.py -r "添加requests库"
```

**自动生成:**
- ✅ `requirements_changelog.md` - 变更日志
- ✅ `.requirements_snapshots/requirements_*.json` - 新快照

---

## 🎯 核心功能

| 功能 | 命令 |
|------|------|
| **基本追踪** | `python tools\track_requirements_changes.py` |
| **添加说明** | `python tools\track_requirements_changes.py -r "原因"` |
| **显示所有包** | `python tools\track_requirements_changes.py --show` |
| **清理旧快照** | `python tools\track_requirements_changes.py --cleanup` |

---

## 📊 变更类型识别

系统自动识别3种变更:

| 类型 | 说明 | 示例 |
|------|------|------|
| ✅ **新增** | 新增的依赖包 | `+ requests==2.31.0` |
| ❌ **删除** | 删除的依赖包 | `- matplotlib>=3.7.0` |
| 🔄 **更新** | 版本变更的包 | `pandas: >=2.0.0 → >=2.1.0` |

---

## 📝 变更日志格式

自动生成的`requirements_changelog.md`:

```markdown
## 📅 2025-11-19 14:30:22

**变更原因:** 添加requests库

### 📊 变更统计
| 类型 | 数量 |
|------|------|
| ✅ 新增 | 1 |
| ❌ 删除 | 0 |
| 🔄 更新 | 0 |
| **总计** | **52** |

### ✅ 新增依赖
- **requests** `==2.31.0`
```

---

## 🧪 运行测试

```powershell
python 测试requirements追踪.py
```

**测试内容:**
1. ✅ 创建初始快照
2. ✅ 新增依赖包追踪
3. ✅ 删除依赖包追踪
4. ✅ 版本更新追踪
5. ✅ 混合变更追踪
6. ✅ 显示包列表
7. ✅ 清理旧快照

---

## 💡 使用场景

### 场景1: 团队协作
```powershell
# 开发者A添加新依赖
python tools\track_requirements_changes.py -r "添加爬虫库"
git add requirements.txt requirements_changelog.md .requirements_snapshots/
git commit -m "deps: 添加beautifulsoup4"
git push

# 开发者B拉取更新
git pull
# 查看变更日志了解依赖变化
cat requirements_changelog.md
pip install -r requirements.txt
```

### 场景2: 版本升级
```powershell
# 升级关键依赖
python tools\track_requirements_changes.py -r "升级pandas修复安全漏洞CVE-2024-1234"
```

### 场景3: 定期维护
```powershell
# 每月清理一次旧快照
python tools\track_requirements_changes.py --cleanup --keep 10
```

---

## 📂 文件结构

```
测算模型/
├── requirements.txt                          # 依赖清单
├── requirements_changelog.md                 # 变更日志(自动生成)
├── .requirements_snapshots/                  # 快照目录
│   ├── requirements_20251119_140000.json    # 快照1
│   └── requirements_20251119_150000.json    # 快照2
└── tools/
    └── track_requirements_changes.py         # 追踪工具
```

---

## ⚙️ 高级选项

### 查看所有依赖包
```powershell
python tools\track_requirements_changes.py --show
```

### 清理旧快照(保留20个)
```powershell
python tools\track_requirements_changes.py --cleanup --keep 20
```

### 查看帮助
```powershell
python tools\track_requirements_changes.py --help
```

---

## 🔍 查看历史快照

### PowerShell查看
```powershell
# 列出所有快照
Get-ChildItem .requirements_snapshots

# 查看特定快照
Get-Content .requirements_snapshots\requirements_20251119_140000.json | ConvertFrom-Json | ConvertTo-Json
```

### Python查看
```python
import json
from pathlib import Path

# 读取快照
with open('.requirements_snapshots/requirements_20251119_140000.json') as f:
    snapshot = json.load(f)

# 查看特定包版本
print(f"pandas版本: {snapshot['packages']['pandas']}")
```

---

## 🎯 最佳实践

### ✅ 推荐
- ✅ 每次修改requirements后立即追踪
- ✅ 使用`-r`参数添加变更说明
- ✅ 将变更日志和快照提交到Git
- ✅ 定期清理旧快照(保留10-20个)

### ❌ 避免
- ❌ 修改后忘记追踪
- ❌ 不添加变更说明
- ❌ 手动编辑变更日志
- ❌ 删除快照目录

---

## 📚 完整文档

详细使用指南请查看: `requirements变更追踪使用指南.md`

---

## 🐛 常见问题

**Q: 首次运行显示"无历史快照"?**  
A: 正常!首次运行创建初始快照,第二次才开始追踪变更。

**Q: 变更日志会被覆盖吗?**  
A: 不会!使用追加模式,不覆盖已有内容。

**Q: 快照文件太多怎么办?**  
A: 运行 `python tools\track_requirements_changes.py --cleanup`

---

## ✅ 功能特性

| 特性 | 状态 |
|------|------|
| 自动对比检测 | ✅ 已实现 |
| 变更分类(新增/删除/更新) | ✅ 已实现 |
| Markdown变更日志 | ✅ 已实现 |
| JSON历史快照 | ✅ 已实现 |
| 命令行参数 | ✅ 已实现 |
| 快照清理 | ✅ 已实现 |
| 包列表显示 | ✅ 已实现 |
| 完整文档 | ✅ 已实现 |
| 测试脚本 | ✅ 已实现 |

---

## 📞 技术支持

如遇到问题:
1. 查看 `requirements变更追踪使用指南.md`
2. 运行测试脚本: `python 测试requirements追踪.py`
3. 检查Python版本 >= 3.7

---

**版本:** v1.0  
**创建日期:** 2025-11-19  
**维护人:** AI助手
