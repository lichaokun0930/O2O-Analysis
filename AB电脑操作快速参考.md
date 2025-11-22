# A/B电脑操作快速参考

## A电脑: 修改数据库结构

### 方式1: 快捷脚本(推荐)
```powershell
# 1. 修改database\models.py添加字段

# 2. 创建并应用迁移
.\A电脑_创建迁移.ps1 -description "字段名"
# 会自动打开notepad,编辑SQL后按Enter继续

# 3. 提交到Git
.\A电脑_提交迁移.ps1 -filename "v2_字段名.sql" -message "添加xx字段"
# 提示: 脚本会检测其他修改,可选择[1]仅迁移 [2]所有修改
```

---

## A电脑: 提交代码修改(非数据库)

### 快捷提交所有修改
```powershell
# 修改了看板、分析引擎、工具脚本等代码后
.\A电脑_提交所有修改.ps1 -message "优化客单价分析功能"

# 会显示所有修改文件,确认后提交
```

### 选择性提交
```powershell
# 只提交特定文件
git add 智能门店看板_Dash版.py 订单数据处理器.py
git commit -m "修复客单价计算逻辑"
git push
```

### 方式2: 手动操作
```powershell
# 1. 修改models.py
# 2. 创建迁移文件
Copy-Item database\migrations\migration_template.sql database\migrations\v2_new_field.sql
# 编辑v2_new_field.sql添加ALTER TABLE语句

# 3. 应用迁移
python database\migrations\apply_migration.py v2_new_field.sql

# 4. 验证
python database\migrations\check_structure.py

# 5. 提交Git
git add database\migrations\v2_new_field.sql database\models.py
git commit -m "添加新字段"
git push
```

---

## B电脑: 同步数据库结构

### 仅同步数据库(快捷)
```powershell
.\B电脑_同步数据库.ps1
```

**自动完成:**
- ✅ 检查是否需要git pull
- ✅ 自动检测并应用新迁移
- ✅ 验证数据库结构一致性
- ✅ 清理Redis缓存

---

## B电脑: 拉取所有代码更新

### 拉取所有代码(推荐)
```powershell
.\B电脑_拉取代码.ps1
```

**智能功能:**
- ✅ 自动检测本地修改(可暂存或放弃)
- ✅ git pull 拉取最新代码
- ✅ 显示更新的文件分类
- ✅ 自动检测是否需要同步数据库
- ✅ 清理Redis缓存

### 手动拉取
```powershell
# 1. 拉取代码
git pull

# 2. 如果有数据库修改
.\B电脑_同步数据库.ps1

# 3. 如果只是代码修改
python 清理Redis缓存.py

# 4. 重启看板
.\启动看板.ps1
```

---

## 常见场景示例

### 场景1: A电脑添加字段,B电脑同步
```powershell
# A电脑
.\A电脑_创建迁移.ps1 -description "delivery_person"
# 编辑SQL: ADD COLUMN delivery_person VARCHAR(50)
.\A电脑_提交迁移.ps1 -filename "v2_delivery_person.sql" -message "添加配送员字段"

# B电脑
.\B电脑_同步数据库.ps1
```

### 场景2: A电脑修改看板代码,B电脑同步
```powershell
# A电脑
# 修改智能门店看板_Dash版.py等文件
.\A电脑_提交所有修改.ps1 -message "优化客单价分析功能"

# B电脑
.\B电脑_拉取代码.ps1
# 会自动检测没有数据库修改,只清理Redis缓存
```

### 场景3: A电脑同时修改代码+数据库,B电脑同步
```powershell
# A电脑
# 1. 修改models.py和看板代码
.\A电脑_创建迁移.ps1 -description "customer_profile"
# 2. 编辑SQL添加字段
.\A电脑_提交迁移.ps1 -filename "v3_customer_profile.sql" -message "添加客户档案"
# 3. 选择 [2]提交所有修改

# B电脑
.\B电脑_拉取代码.ps1
# 会自动检测到数据库修改,询问是否同步数据库
# 选择 y,自动调用 B电脑_同步数据库.ps1
```

### 场景4: B电脑有本地修改时拉取
```powershell
# B电脑
.\B电脑_拉取代码.ps1
# 检测到本地修改,提供选项:
# [1] 暂存本地修改 (git stash)
# [2] 放弃本地修改 (git reset)
# [3] 取消
```

---

## 故障排查

### A电脑问题

**问题1: 迁移应用失败**
```powershell
# 检查SQL语法
# 查看具体错误信息
python database\migrations\apply_migration.py v2_xxx.sql
```

**问题2: 数据库结构不一致**
```powershell
# 验证差异
python database\migrations\check_structure.py

# 手动对比
psql -U postgres -d o2o_analysis -c "\d orders"
```

### B电脑问题

**问题1: git pull冲突**
```powershell
# 查看冲突文件
git status

# 选择操作:
# 方案1: 保留本地修改
git stash
git pull
git stash pop

# 方案2: 放弃本地修改
git reset --hard HEAD
git pull
```

**问题2: 迁移同步失败**
```powershell
# 检查migration_history表
python -c "from database.migrations.migration_history import *; init_migration_history(); print(get_applied_migrations())"

# 手动应用特定迁移
python database\migrations\apply_migration.py v2_xxx.sql
```

**问题3: 看板显示旧数据**
```powershell
# 清理Redis缓存
python 清理Redis缓存.py

# 重启看板
.\启动看板.ps1
```

**问题4: 本地有未提交修改**
```powershell
# 使用B电脑_拉取代码.ps1会自动处理
.\B电脑_拉取代码.ps1
# 选择[1]暂存或[2]放弃
```

---

## 文件位置速查

```
database/
├── models.py                          # 数据模型定义
├── migrations/
│   ├── migration_history.py          # 迁移历史管理
│   ├── apply_migration.py            # 应用单个迁移
│   ├── sync_migrations.py            # 同步所有迁移
│   ├── check_structure.py            # 验证结构一致性
│   ├── migration_template.sql        # 迁移模板
│   ├── v1_add_stock_fields.sql       # 示例迁移
│   └── v2_xxx.sql                    # 你的新迁移

根目录/
├── A电脑_创建迁移.ps1                # A电脑快捷脚本1 - 创建并应用迁移
├── A电脑_提交迁移.ps1                # A电脑快捷脚本2 - 提交迁移到Git
├── A电脑_提交所有修改.ps1            # A电脑快捷脚本3 - 提交所有代码修改
├── B电脑_同步数据库.ps1              # B电脑快捷脚本1 - 仅同步数据库
├── B电脑_拉取代码.ps1                # B电脑快捷脚本2 - 拉取所有代码(智能)
├── A电脑操作指南.md                  # A电脑详细文档
├── 两台电脑数据库同步方案.md          # 完整设计文档
├── 数据库同步快速参考.md              # 命令速查
└── 清理Redis缓存.py                  # 缓存清理工具
```

---

## 最佳实践

### A电脑
1. **迁移命名**: 使用描述性名称,如`v2_add_delivery_person`而非`v2_change`
2. **SQL注释**: 在迁移文件中详细注释每个ALTER语句的目的
3. **验证流程**: 每次迁移后都运行`check_structure.py`验证
4. **及时提交**: 修改完立即提交Git,避免B电脑长时间滞后
5. **选择提交**: 数据库修改用`A电脑_提交迁移.ps1`,代码修改用`A电脑_提交所有修改.ps1`

### B电脑
1. **及时同步**: 每天开始工作前先运行`.\B电脑_拉取代码.ps1`
2. **缓存清理**: 同步后必须清理Redis缓存
3. **测试验证**: 同步后验证看板功能是否正常
4. **本地修改**: 拉取前先处理本地修改(暂存或放弃)
5. **智能拉取**: 优先使用`B电脑_拉取代码.ps1`,会自动检测数据库修改

---

## 📞 需要帮助?

查看详细文档:
- `A电脑操作指南.md` - 完整的6步流程
- `两台电脑数据库同步方案.md` - 架构设计和原理
- `数据库同步快速参考.md` - 命令速查清单
