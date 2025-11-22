# 数据库迁移管理

本目录存放所有数据库结构变更的SQL脚本,确保两台电脑的数据库结构一致。

## 文件命名规范

```
YYYYMMDD_HHMM_description.sql
```

例如:
- `20251122_1430_add_stock_fields.sql` - 添加库存字段
- `20251122_1500_add_delivery_distance.sql` - 添加配送距离字段

## 迁移记录

| 日期 | 文件名 | 说明 | 状态 |
|------|--------|------|------|
| 2025-11-22 | v1_add_stock_fields.sql | 添加库存相关字段 | ✅ 已完成 |

## 使用方法

### 1. A电脑创建迁移

```powershell
# 1. 修改models.py添加新字段
# 2. 创建迁移SQL文件
# 3. 执行迁移
python database\migrations\apply_migration.py v1_add_stock_fields.sql

# 4. 提交到Git
git add database/migrations/v1_add_stock_fields.sql
git add database/models.py
git commit -m "添加库存字段"
git push
```

### 2. B电脑同步

```powershell
# 1. 拉取代码
git pull

# 2. 自动应用所有未执行的迁移
python database\migrations\sync_migrations.py

# 3. 验证
python database\migrations\check_structure.py
```

## 迁移脚本模板

参考 `migration_template.sql`
