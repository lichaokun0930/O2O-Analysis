# A电脑智能提交 - 使用指南

## 🚀 一键搞定所有提交!

这个脚本会**自动检测**你的修改类型,智能处理:
- ✅ 检测到`models.py`修改 → 自动创建迁移、应用到数据库
- ✅ 提交所有修改(数据库+代码)到GitHub
- ✅ 一条命令完成!

---

## 使用方法

### 基本用法
```powershell
.\A电脑_智能提交.ps1 -message "提交信息"
```

---

## 场景演示

### 场景1: 只修改了看板代码(无数据库修改)
```powershell
# 1. 修改了 智能门店看板_Dash版.py
# 2. 运行智能提交
.\A电脑_智能提交.ps1 -message "优化客单价分析功能"

# 脚本会:
# ✅ 检测到没有models.py修改
# ✅ 跳过迁移步骤
# ✅ 直接提交所有代码到GitHub
```

### 场景2: 修改了models.py(需要数据库迁移)
```powershell
# 1. 修改了 database/models.py (添加新字段)
# 2. 运行智能提交
.\A电脑_智能提交.ps1 -message "添加配送员字段"

# 脚本会:
# ✅ 检测到models.py修改
# ✅ 询问迁移描述: delivery_person
# ✅ 自动创建迁移文件: v2_delivery_person.sql
# ✅ 打开notepad让你编辑SQL
# ✅ 应用迁移到A电脑数据库
# ✅ 验证数据库结构
# ✅ 提交所有修改到GitHub
```

### 场景3: 同时修改了代码+数据库
```powershell
# 1. 修改了 models.py + 智能门店看板_Dash版.py
# 2. 运行智能提交
.\A电脑_智能提交.ps1 -message "添加客户档案功能"

# 脚本会:
# ✅ 检测到models.py修改
# ✅ 创建迁移(你输入描述: customer_profile)
# ✅ 让你编辑SQL添加字段
# ✅ 应用迁移
# ✅ 提交所有修改(迁移+代码)到GitHub
```

---

## 完整工作流程

```
1. 修改代码(看板、分析引擎等)
   ↓
2. 如果修改了models.py,添加新字段定义
   ↓
3. 运行: .\A电脑_智能提交.ps1 -message "xxx"
   ↓
4. 脚本自动检测是否需要迁移
   ↓
5. 如需迁移:
   - 询问迁移描述
   - 打开notepad编辑SQL
   - 应用到数据库
   - 验证结构
   ↓
6. 提交所有修改到GitHub
   ↓
7. 完成! B电脑运行 .\B电脑_拉取代码.ps1 同步
```

---

## 实际示例

### 示例1: 添加配送员姓名字段
```powershell
# 步骤1: 编辑 database/models.py
class Order(Base):
    # ... 现有字段 ...
    delivery_person = Column(String(50), comment='配送员姓名')

# 步骤2: 运行智能提交
.\A电脑_智能提交.ps1 -message "添加配送员字段"

# 交互过程:
# Q: 请输入迁移描述(如: add_delivery_person)
# A: delivery_person [回车]
# 
# → 打开notepad,编辑SQL:
ALTER TABLE orders ADD COLUMN delivery_person VARCHAR(50);
# 
# → 保存并关闭notepad,按Enter继续
# → 自动应用迁移、验证、提交GitHub
```

### 示例2: 只修改了看板样式
```powershell
# 步骤1: 修改 component_styles.py
# 步骤2: 运行智能提交
.\A电脑_智能提交.ps1 -message "优化卡片样式"

# 脚本输出:
# ✓ 未检测到models.py修改,跳过迁移步骤
# ✓ 直接提交到GitHub
```

---

## 对比旧方式

### 旧方式(3个脚本,5步操作)
```powershell
# 1. 创建迁移
.\A电脑_创建迁移.ps1 -description "delivery_person"

# 2. 编辑SQL
notepad database\migrations\v2_delivery_person.sql

# 3. 应用迁移(已在步骤1完成)

# 4. 提交迁移
.\A电脑_提交迁移.ps1 -filename "v2_delivery_person.sql" -message "添加配送员字段"

# 5. 选择[2]提交所有修改
```

### 新方式(1个脚本,1步操作)
```powershell
# 一条命令搞定!
.\A电脑_智能提交.ps1 -message "添加配送员字段"
```

---

## 常见问题

### Q1: 如果我不想创建迁移怎么办?
**A:** 当脚本询问迁移描述时,直接按Enter跳过,会直接提交代码。

### Q2: 如果迁移应用失败怎么办?
**A:** 脚本会提示SQL语法错误,修复`database/migrations/vX_xxx.sql`后重新运行脚本。

### Q3: 我可以在提交前预览修改吗?
**A:** 可以!脚本会显示所有修改文件,并询问确认才提交。

### Q4: 如果我只想提交部分文件怎么办?
**A:** 使用旧脚本:`.\A电脑_提交所有修改.ps1`或手动`git add`

---

## 最佳实践

1. **提交信息规范**: 使用清晰描述,如"添加XX字段"、"优化XX功能"
2. **迁移描述规范**: 使用小写+下划线,如`delivery_person`、`customer_tags`
3. **SQL编辑仔细**: 打开notepad时仔细编写ALTER语句,避免语法错误
4. **测试后提交**: 如果修改重要功能,先本地测试再运行脚本

---

## 脚本对比

| 脚本 | 用途 | 推荐度 |
|------|------|--------|
| `A电脑_智能提交.ps1` | **一键搞定所有提交** | ⭐⭐⭐⭐⭐ 强烈推荐 |
| `A电脑_创建迁移.ps1` | 仅创建迁移,不提交 | ⭐⭐ 高级用户 |
| `A电脑_提交迁移.ps1` | 提交迁移+可选代码 | ⭐⭐⭐ 需要分步控制时 |
| `A电脑_提交所有修改.ps1` | 提交所有代码,无迁移 | ⭐⭐⭐ 纯代码修改时 |

**新手推荐**: 只用`A电脑_智能提交.ps1`就够了! 🎉
