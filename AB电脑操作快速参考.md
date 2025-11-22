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

### 一键同步
```powershell
.\B电脑_同步数据库.ps1
```

**自动完成:**
- ✅ git pull 拉取最新代码
- ✅ 自动检测并应用新迁移
- ✅ 验证数据库结构一致性
- ✅ 清理Redis缓存
- ✅ 重启Dash看板

### 手动同步
```powershell
# 1. 拉取代码
git pull

# 2. 同步迁移
python database\migrations\sync_migrations.py

# 3. 验证
python database\migrations\check_structure.py

# 4. 清理缓存
python 清理Redis缓存.py

# 5. 重启看板
.\启动看板.ps1
```

---

## 常见场景示例

### 场景1: 添加单个字段
```powershell
# A电脑
.\A电脑_创建迁移.ps1 -description "delivery_person"
# 编辑SQL: ADD COLUMN delivery_person VARCHAR(50)
.\A电脑_提交迁移.ps1 -filename "v2_delivery_person.sql" -message "添加配送员字段"

# B电脑
.\B电脑_同步数据库.ps1
```

### 场景2: 添加多个相关字段
```powershell
# A电脑
.\A电脑_创建迁移.ps1 -description "customer_profile"
# 编辑SQL添加多个ADD COLUMN
.\A电脑_提交迁移.ps1 -filename "v3_customer_profile.sql" -message "添加客户档案字段"

# B电脑
.\B电脑_同步数据库.ps1
```

### 场景3: 修改字段类型
```powershell
# A电脑
.\A电脑_创建迁移.ps1 -description "alter_price_precision"
# 编辑SQL: ALTER COLUMN price TYPE NUMERIC(12,4)
.\A电脑_提交迁移.ps1 -filename "v4_alter_price_precision.sql" -message "提高价格字段精度"

# B电脑
.\B电脑_同步数据库.ps1
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

**问题1: git pull失败**
```powershell
# 检查网络
# 确认A电脑已push
git remote -v
git fetch
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
├── A电脑_创建迁移.ps1                # A电脑快捷脚本1
├── A电脑_提交迁移.ps1                # A电脑快捷脚本2
├── B电脑_同步数据库.ps1              # B电脑一键同步
├── A电脑操作指南.md                  # A电脑详细文档
├── 两台电脑数据库同步方案.md          # 完整设计文档
├── 数据库同步快速参考.md              # 命令速查
└── 清理Redis缓存.py                  # 缓存清理工具
```

---

## 最佳实践

1. **迁移命名**: 使用描述性名称,如`v2_add_delivery_person`而非`v2_change`
2. **SQL注释**: 在迁移文件中详细注释每个ALTER语句的目的
3. **验证流程**: 每次迁移后都运行`check_structure.py`验证
4. **及时提交**: 修改完立即提交Git,避免B电脑长时间滞后
5. **缓存清理**: B电脑同步后必须清理Redis缓存
6. **测试验证**: 同步后验证看板功能是否正常

---

## 📞 需要帮助?

查看详细文档:
- `A电脑操作指南.md` - 完整的6步流程
- `两台电脑数据库同步方案.md` - 架构设计和原理
- `数据库同步快速参考.md` - 命令速查清单
