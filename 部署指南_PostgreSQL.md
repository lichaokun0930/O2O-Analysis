# 智能门店看板 - PostgreSQL 全栈部署指南

## 📋 准备工作

### 1. 安装 PostgreSQL

**Windows:**
1. 下载：https://www.postgresql.org/download/windows/
2. 安装时设置密码（记住这个密码！）
3. 默认端口：5432
4. 安装完成后会有 pgAdmin 图形化工具

**验证安装:**
```powershell
psql --version
```

### 2. 创建数据库

打开 pgAdmin 或命令行：

```sql
CREATE DATABASE o2o_dashboard;
```

或者用命令行：
```powershell
psql -U postgres
CREATE DATABASE o2o_dashboard;
\q
```

### 3. 安装 Python 依赖

```powershell
cd d:\Python1\O2O_Analysis\O2O数据分析\测算模型
pip install -r requirements.txt
```

## ⚙️ 配置环境变量

### 1. 复制环境变量模板

```powershell
copy .env.example .env
```

### 2. 编辑 .env 文件

用记事本打开 `.env`，修改以下内容：

```env
# 修改为您的PostgreSQL密码
DATABASE_URL=postgresql://postgres:您的密码@localhost:5432/o2o_dashboard

# 填入您的API密钥
ZHIPU_API_KEY=您的智谱API密钥

# 其他配置保持默认即可
```

## 🚀 数据迁移

### 1. 导入Excel数据到数据库

```powershell
python database/migrate.py
```

**可选参数：**
- `--file 文件路径` - 指定Excel文件
- `--force` - 强制重新导入

**输出示例：**
```
🚀 开始数据迁移：Excel → PostgreSQL
✅ 数据库连接成功！
🔧 正在创建数据库表...
✅ 数据库表创建完成！
📂 正在加载数据...
✅ 数据导入完成！
  - 商品数量: 3928 个
  - 订单数量: 17450 条
  - 场景标签: 3928 个
```

## 🎯 启动服务

### 方案A：分别启动（推荐调试）

**终端1 - 启动后端API:**
```powershell
python backend/main.py
```

访问 API 文档：http://localhost:8000/api/docs

**终端2 - 启动前端看板:**
```powershell
python 智能门店看板_Dash版.py
```

访问看板：http://localhost:8050

### 方案B：一键启动（生产环境）

```powershell
.\启动全栈服务.ps1
```

## 🔍 验证部署

### 1. 检查后端API

浏览器访问：http://localhost:8000/api/health

应该返回：
```json
{
  "status": "healthy",
  "database": "connected",
  "stats": {
    "products": 3928,
    "orders": 17450
  }
}
```

### 2. 检查前端看板

浏览器访问：http://localhost:8050

应该能看到完整的看板界面

### 3. 测试API接口

**商品列表：**
http://localhost:8000/api/products?limit=10

**订单统计：**
http://localhost:8000/api/orders/stats

**四象限分析：**
http://localhost:8000/api/analysis/quadrant

## 📊 数据库管理

### 使用 pgAdmin（图形化）

1. 打开 pgAdmin
2. 连接到 localhost
3. 选择 `o2o_dashboard` 数据库
4. 可以查看表、运行SQL等

### 使用命令行

```powershell
# 连接数据库
psql -U postgres -d o2o_dashboard

# 查看所有表
\dt

# 查询商品数量
SELECT COUNT(*) FROM products;

# 查询订单数量
SELECT COUNT(*) FROM orders;

# 退出
\q
```

## 🔧 常见问题

### 问题1：数据库连接失败

**错误：** `could not connect to server`

**解决：**
1. 确认PostgreSQL服务正在运行
2. 检查 `.env` 中的密码是否正确
3. 确认数据库 `o2o_dashboard` 已创建

### 问题2：表已存在

**错误：** `Table 'orders' already exists`

**解决：**
```powershell
# 删除所有表重新创建
python -c "from database.connection import drop_all_tables; drop_all_tables()"
python database/migrate.py
```

### 问题3：依赖安装失败

**错误：** `error: Microsoft Visual C++ 14.0 is required`

**解决：**
```powershell
# 使用预编译的二进制包
pip install psycopg2-binary
```

## 📈 性能优化建议

### 1. 创建索引（已自动创建）

数据库模型中已定义索引，migrate时会自动创建

### 2. 开启查询缓存

后端已实现 `AnalysisCache` 表，分析结果会自动缓存

### 3. 定期清理过期缓存

```sql
DELETE FROM analysis_cache WHERE expire_at < NOW();
```

## 🔄 数据更新

### 增量导入新数据

```powershell
python database/migrate.py --file 新数据.xlsx
```

系统会自动检测文件哈希，避免重复导入

### 全量更新

```powershell
python database/migrate.py --file 数据.xlsx --force
```

## 🎉 部署完成！

现在您已经拥有：
- ✅ PostgreSQL 企业级数据库
- ✅ FastAPI 高性能后端
- ✅ Dash 交互式前端
- ✅ 完整的数据分析能力

**下一步：**
- 探索 API 文档：http://localhost:8000/api/docs
- 使用看板分析数据：http://localhost:8050
- 查看数据库：打开 pgAdmin

有任何问题随时咨询！🚀
