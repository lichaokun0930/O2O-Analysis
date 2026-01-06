# A电脑操作指南 - 修改数据库结构

## ⭐ 最新推荐: 智能提交(超级简单!)

**一条命令搞定所有操作!**

```powershell
.\A电脑_智能提交.ps1 -message "你的提交信息"
```

**自动识别并处理:**
- ✅ 检测到models.py修改 → 自动创建迁移、应用
- ✅ 没有数据库修改 → 直接提交代码
- ✅ 提交所有修改到GitHub

**详细使用指南**: `A电脑_智能提交使用指南.md`

---

## 🚀 手动分步方式(高级用户)

### 一键创建并应用迁移
```powershell
.\A电脑_创建迁移.ps1 -description "字段描述"
```

**功能:**
- ✅ 自动生成版本号和文件名
- ✅ 从模板创建迁移文件  
- ✅ 打开编辑器让你修改SQL
- ✅ 应用到A电脑数据库
- ✅ 验证数据库结构
- ✅ 显示Git提交建议

**示例:**
```powershell
# 添加商品评分字段
.\A电脑_创建迁移.ps1 -description "product_rating"

# 添加客户标签字段
.\A电脑_创建迁移.ps1 -description "customer_tags"
```

### 一键提交到Git
```powershell
.\A电脑_提交迁移.ps1 -filename "v2_product_rating.sql" -message "添加商品评分字段"
```

**功能:**
- ✅ 自动添加迁移文件和models.py
- ✅ 提交到本地Git
- ✅ 推送到GitHub
- ✅ 验证推送结果

---

## 📋 完整工作流程(手动操作)

### 场景: 需要添加新字段到数据库

---

## 🔧 操作步骤

### 步骤1: 修改models.py

```python
# 打开 database/models.py
# 在Order类中添加新字段

class Order(Base):
    # ... 现有字段 ...
    
    # ✅ 添加新字段
    new_field_name = Column(String(100), comment='字段说明')
```

**示例:**
```python
# 假设要添加"配送员姓名"字段
delivery_person = Column(String(50), comment='配送员姓名')
```

---

### 步骤2: 创建迁移脚本

```powershell
# 进入迁移目录
cd database\migrations

# 复制模板创建新迁移(使用有意义的名称)
copy migration_template.sql v2_add_delivery_person.sql

# 编辑迁移文件
notepad v2_add_delivery_person.sql
```

**编辑迁移文件内容:**
```sql
-- v2_add_delivery_person.sql
-- 日期: 2025-11-23
-- 说明: 添加配送员姓名字段

-- 添加字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_person VARCHAR(50);
COMMENT ON COLUMN orders.delivery_person IS '配送员姓名';

-- 验证
DO $$
DECLARE
    field_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO field_count
    FROM information_schema.columns
    WHERE table_name = 'orders' AND column_name = 'delivery_person';
    
    IF field_count > 0 THEN
        RAISE NOTICE '✓ 字段添加成功';
    ELSE
        RAISE WARNING '✗ 字段添加失败';
    END IF;
END $$;
```

---

### 步骤3: 应用迁移到A电脑数据库

```powershell
# 返回项目根目录
cd ..\..

# 激活虚拟环境(如果未激活)
.\.venv\Scripts\Activate.ps1

# 应用迁移
python database\migrations\apply_migration.py v2_add_delivery_person.sql
```

**期望输出:**
```
============================================================
应用迁移: v2_add_delivery_person.sql
============================================================

✓ 迁移应用成功: v2_add_delivery_person.sql
```

---

### 步骤4: 验证数据库结构

```powershell
# 验证A电脑数据库结构是否一致
python database\migrations\check_structure.py
```

**期望输出:**
```
============================================================
数据库结构一致性检查
============================================================

数据库字段数: 45
models.py字段数: 45

✓ 共有字段 (45 个)

============================================================
✓ 数据库结构完全一致!
============================================================
```

---

### 步骤5: 测试功能

```powershell
# 重启看板测试新字段
.\启动看板.ps1

# 或者运行测试脚本
python 测试新字段.py
```

确认:
- ✅ 看板能正常启动
- ✅ 数据能正确显示
- ✅ 新字段功能正常

---

### 步骤6: 提交到Git

```powershell
# 查看修改
git status

# 添加相关文件
git add database\migrations\v2_add_delivery_person.sql
git add database\models.py
git add database\batch_import.py  # 如果修改了导入逻辑

# 提交(使用清晰的commit信息)
git commit -m "添加配送员姓名字段

- models.py: 添加delivery_person字段
- v2_add_delivery_person.sql: 数据库迁移脚本
- batch_import.py: 支持导入配送员数据(如果有修改)"

# 推送到GitHub
git push
```

---

## ⚡ 一键操作脚本

如果经常需要创建迁移,可以使用快捷脚本:

### 方式1: 交互式创建(推荐)

```powershell
.\A电脑_创建迁移.ps1 add_delivery_person
```

脚本会:
1. 自动创建迁移文件(带时间戳)
2. 打开编辑器让你编辑SQL
3. 应用迁移到数据库
4. 验证结构一致性
5. 提示提交命令

### 方式2: 手动执行(如上面步骤1-6)

---

## 📝 常见场景快速参考

### 场景A: 添加单个字段

```sql
-- vX_add_fieldname.sql
ALTER TABLE orders ADD COLUMN IF NOT EXISTS field_name VARCHAR(100);
COMMENT ON COLUMN orders.field_name IS '字段说明';
```

### 场景B: 添加多个字段

```sql
-- vX_add_multiple_fields.sql
ALTER TABLE orders ADD COLUMN IF NOT EXISTS field1 VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS field2 INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS field3 FLOAT;

COMMENT ON COLUMN orders.field1 IS '字段1说明';
COMMENT ON COLUMN orders.field2 IS '字段2说明';
COMMENT ON COLUMN orders.field3 IS '字段3说明';
```

### 场景C: 修改字段类型

```sql
-- vX_modify_field_type.sql
ALTER TABLE orders ALTER COLUMN existing_field TYPE VARCHAR(200);
```

### 场景D: 添加索引

```sql
-- vX_add_index.sql
CREATE INDEX IF NOT EXISTS idx_orders_field_name ON orders(field_name);
```

---

## ⚠️ 注意事项

### 1. 迁移文件命名规范

```
vX_description.sql
```

- ✅ `v2_add_delivery_person.sql`
- ✅ `v3_add_payment_method.sql`
- ❌ `add_field.sql` (缺少版本号)
- ❌ `v2.sql` (缺少描述)

### 2. 必须包含的内容

每个迁移脚本必须包含:
- ✅ 日期和说明注释
- ✅ `IF NOT EXISTS` 避免重复执行
- ✅ `COMMENT` 说明字段用途
- ✅ 验证代码确认成功

### 3. 测试流程

```
修改models.py → 创建迁移 → 应用迁移 → 验证结构 → 测试功能 → 提交Git
```

每一步都要确保成功后再进行下一步!

### 4. 不要跳过步骤

❌ 错误做法:
```powershell
# 直接修改数据库,不创建迁移
psql -c "ALTER TABLE orders ADD COLUMN new_field VARCHAR(100);"
git add database\models.py
git commit -m "添加字段"
git push
```

这样B电脑拉取代码后会报错!

✅ 正确做法:
```powershell
# 1. 修改models.py
# 2. 创建迁移脚本
# 3. 应用迁移
# 4. 一起提交
```

---

## 🔍 故障排查

### 问题1: 应用迁移失败

```powershell
# 查看详细错误
python database\migrations\apply_migration.py vX_xxx.sql

# 检查迁移历史
python database\migrations\migration_history.py

# 手动执行SQL调试
psql -U postgres -d o2o_dashboard -f database\migrations\vX_xxx.sql
```

### 问题2: 结构验证失败

```powershell
# 检查差异
python database\migrations\check_structure.py

# 查看数据库实际字段
psql -U postgres -d o2o_dashboard -c "\d orders"

# 查看models.py字段
python -c "from database.models import Order; from sqlalchemy import inspect; print([c.name for c in inspect(Order).columns])"
```

### 问题3: 忘记创建迁移就修改了数据库

**补救方法:**

```powershell
# 1. 查看数据库当前结构
psql -U postgres -d o2o_dashboard -c "\d orders" > current_structure.txt

# 2. 根据差异反向生成迁移脚本
# 手动创建迁移文件,包含之前手动执行的ALTER TABLE语句

# 3. 记录到迁移历史
python database\migrations\apply_migration.py vX_补救迁移.sql
```

---

## 📚 完整示例

### 示例: 添加"支付方式"字段

#### 1. 修改models.py

```python
# database/models.py
class Order(Base):
    # ... 现有字段 ...
    
    # 添加支付方式字段
    payment_method = Column(String(50), comment='支付方式(微信/支付宝/现金)')
```

#### 2. 创建迁移

```powershell
cd database\migrations
copy migration_template.sql v3_add_payment_method.sql
notepad v3_add_payment_method.sql
```

#### 3. 编辑迁移文件

```sql
-- v3_add_payment_method.sql
-- 日期: 2025-11-23
-- 说明: 添加支付方式字段,用于统计不同支付渠道的订单

ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);
COMMENT ON COLUMN orders.payment_method IS '支付方式(微信/支付宝/现金)';

-- 为现有数据设置默认值
UPDATE orders SET payment_method = '未知' WHERE payment_method IS NULL;

-- 验证
DO $$
DECLARE
    field_count INTEGER;
    data_count INTEGER;
BEGIN
    -- 检查字段存在
    SELECT COUNT(*) INTO field_count
    FROM information_schema.columns
    WHERE table_name = 'orders' AND column_name = 'payment_method';
    
    -- 检查数据已更新
    SELECT COUNT(*) INTO data_count
    FROM orders
    WHERE payment_method IS NOT NULL;
    
    IF field_count > 0 AND data_count > 0 THEN
        RAISE NOTICE '✓ 迁移成功: 字段已添加,数据已更新';
    ELSE
        RAISE WARNING '⚠ 迁移可能不完整';
    END IF;
END $$;
```

#### 4. 应用并验证

```powershell
cd ..\..
python database\migrations\apply_migration.py v3_add_payment_method.sql
python database\migrations\check_structure.py
```

#### 5. 提交

```powershell
git add database\migrations\v3_add_payment_method.sql database\models.py
git commit -m "添加支付方式字段

- 新增payment_method字段用于支付渠道分析
- 已有数据默认设为'未知'
- 迁移脚本: v3_add_payment_method.sql"
git push
```

---

## 🎯 快速命令清单

```powershell
# 创建迁移
cd database\migrations
copy migration_template.sql vX_description.sql
notepad vX_description.sql

# 应用迁移
cd ..\..
python database\migrations\apply_migration.py vX_description.sql

# 验证
python database\migrations\check_structure.py

# 查看历史
python database\migrations\migration_history.py

# 提交
git add database\migrations\vX_description.sql database\models.py
git commit -m "描述"
git push
```

---

## 💡 最佳实践

1. **一个迁移只做一件事** - 便于回滚和理解
2. **使用有意义的命名** - 便于查找和维护
3. **添加详细注释** - 说明为什么要这样改
4. **包含验证逻辑** - 确保迁移成功执行
5. **先测试再提交** - 避免提交有问题的迁移
6. **立即提交** - 不要积累多个迁移一起提交

---

## 📞 需要帮助?

遇到问题时:
1. 查看 `两台电脑数据库同步方案.md` 完整文档
2. 运行 `python database\migrations\check_structure.py` 检查差异
3. 查看 `database\migrations\README.md` 迁移目录说明
