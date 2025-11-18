# PostgreSQL + Python 数据分析系统环境配置完整指南

## 📋 完整技术栈概览

### 数据流程架构
```
Excel订单数据 
    ↓ (导入)
PostgreSQL数据库
    ↓ (查询 - SQL)
Python数据处理层 (SQLAlchemy ORM)
    ↓ (计算 - Python/Pandas)
Dash可视化看板
    ↓ (展示)
用户浏览器
```

## 🔧 环境配置步骤

### 第一步：安装PostgreSQL数据库

#### Windows系统

**1. 下载安装包**
- 访问：https://www.postgresql.org/download/windows/
- 选择最新版本（推荐15.x或16.x）
- 下载installer

**2. 安装PostgreSQL**
```
安装路径：默认 C:\Program Files\PostgreSQL\15
端口：5432（默认）
超级用户：postgres
密码：[设置一个强密码，务必记住！]
Locale：Chinese, China
```

**3. 验证安装**
```powershell
# 打开PowerShell
psql --version
# 应显示：psql (PostgreSQL) 15.x

# 测试连接
psql -U postgres
# 输入密码后应能进入PostgreSQL命令行
```

#### 常见问题

**问题1：`psql`命令找不到**
```powershell
# 解决方案：添加到PATH环境变量
# 路径通常为：C:\Program Files\PostgreSQL\15\bin
```

**问题2：密码验证失败**
```
修改：C:\Program Files\PostgreSQL\15\data\pg_hba.conf
将 md5 改为 trust（仅本地开发）
重启PostgreSQL服务
```

### 第二步：创建数据库

**方法A：使用pgAdmin（推荐新手）**
1. 打开pgAdmin（安装PostgreSQL时自动安装）
2. 连接到PostgreSQL服务器（输入密码）
3. 右键 Databases → Create → Database
4. 数据库名：`o2o_dashboard`
5. Owner：postgres
6. 点击Save

**方法B：使用命令行（推荐高级用户）**
```powershell
# 连接到PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE o2o_dashboard;

# 验证创建成功
\l
# 应该能看到 o2o_dashboard

# 退出
\q
```

### 第三步：配置Python环境

#### 1. 检查Python版本

```powershell
python --version
# 要求：Python 3.9 或以上
# 推荐：Python 3.11
```

**如果版本不符合**：
- 下载：https://www.python.org/downloads/
- 安装时勾选"Add Python to PATH"

#### 2. 创建虚拟环境（强烈推荐）

```powershell
cd d:\Python1\O2O_Analysis\O2O数据分析\测算模型

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 如果提示执行策略错误
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. 安装Python依赖

```powershell
# 确保在虚拟环境中（提示符前面有(.venv)）
pip install -r requirements.txt
```

**关键依赖包清单**：

##### 核心数据库驱动（必需）
```
sqlalchemy==2.0.23          # ORM框架
psycopg2-binary==2.9.9      # PostgreSQL驱动（主驱动）
pg8000                       # PostgreSQL驱动（备用，纯Python）
alembic==1.12.1             # 数据库迁移工具
```

##### 数据处理（必需）
```
pandas>=2.0.0               # 数据分析核心
numpy>=1.24.0               # 数值计算
openpyxl>=3.1.0            # Excel读写
```

##### Web框架（必需）
```
dash>=2.14.0                # 前端框架
dash-bootstrap-components>=1.5.0  # UI组件
dash-echarts>=1.0.0         # 图表组件
```

##### 后端API（可选，仅全栈模式）
```
fastapi==0.104.1            # REST API框架
uvicorn[standard]==0.24.0   # ASGI服务器
pydantic==2.5.0             # 数据验证
```

##### 辅助工具
```
python-dotenv>=1.0.0        # 环境变量管理
tqdm>=4.65.0                # 进度条
```

**安装验证**：
```powershell
# 验证关键包
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
python -c "import psycopg2; print(psycopg2.__version__)"
python -c "import pandas; print(pandas.__version__)"
python -c "import dash; print(dash.__version__)"
```

### 第四步：配置环境变量

#### 1. 创建.env文件

```powershell
# 复制模板（如果不存在）
copy .env.template .env
```

#### 2. 编辑.env文件

打开`.env`，配置数据库连接：

```env
# =============================================================================
# PostgreSQL数据库配置
# =============================================================================
# 格式：postgresql://用户名:密码@主机:端口/数据库名
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/o2o_dashboard

# 示例（假设密码是123456）
# DATABASE_URL=postgresql://postgres:123456@localhost:5432/o2o_dashboard

# =============================================================================
# AI模型配置（可选）
# =============================================================================
GEMINI_API_KEY=你的Gemini密钥  # 如果不用AI功能可以留空
GEMINI_MODEL=gemini-2.5-pro
GEMINI_TEMPERATURE=0.7

# =============================================================================
# 应用配置
# =============================================================================
# 调试模式
DEBUG=True

# 日志级别
LOG_LEVEL=INFO
```

**重要提醒**：
- ⚠️ 密码中如果有特殊字符（如@、#、:等），需要URL编码
- ⚠️ `.env`文件包含敏感信息，不要上传到Git仓库

### 第五步：初始化数据库表结构

#### 方法A：使用内置迁移脚本

```powershell
# 创建所有数据库表
python -c "from database.models import Base; from database.connection import engine; Base.metadata.create_all(engine); print('✅ 数据库表创建成功')"
```

#### 方法B：使用Alembic（推荐生产环境）

```powershell
# 初始化Alembic（首次使用）
alembic init alembic

# 生成迁移脚本
alembic revision --autogenerate -m "初始化数据库"

# 执行迁移
alembic upgrade head
```

**验证表创建成功**：
```powershell
psql -U postgres -d o2o_dashboard
\dt  # 查看所有表
# 应该看到：orders, products, analysis_results等表
```

### 第六步：导入数据

#### 使用智能导入脚本

```powershell
python 智能导入门店数据.py
```

**交互式导入流程**：
```
1. 选择Excel文件
2. 系统自动检测字段映射
3. 确认导入
4. 显示导入进度
5. 导入完成统计
```

#### 或使用Python代码导入

```python
from database.data_lifecycle_manager import DataLifecycleManager
import pandas as pd

# 读取Excel
df = pd.read_excel('实际数据/订单明细.xlsx')

# 初始化管理器
manager = DataLifecycleManager()

# 导入数据
manager.import_from_excel(df, store_name='测试门店')

print(f"✅ 导入完成: {len(df)} 条记录")
```

## 🚀 启动系统

### 单体模式（仅看板）

```powershell
# 启动Dash看板
python 智能门店看板_Dash版.py

# 访问 http://localhost:8050
```

### 全栈模式（看板+API）

**终端1 - 后端API**：
```powershell
cd backend
python main.py
# 访问 http://localhost:8000/docs
```

**终端2 - 前端看板**：
```powershell
python 智能门店看板_Dash版.py
# 访问 http://localhost:8050
```

### 一键启动（推荐）

```powershell
.\启动全栈服务.ps1
```

## ✅ 验证清单

### 1. PostgreSQL验证
```powershell
# 连接测试
psql -U postgres -d o2o_dashboard
\conninfo  # 显示连接信息
```

### 2. Python环境验证
```powershell
# 在虚拟环境中
python -c "from database.connection import engine; print(engine.url)"
# 应显示数据库URL
```

### 3. 数据导入验证
```sql
-- 在psql中执行
SELECT COUNT(*) FROM orders;     -- 查看订单数量
SELECT COUNT(*) FROM products;   -- 查看商品数量
SELECT DISTINCT store_name FROM orders;  -- 查看门店列表
```

### 4. 看板功能验证
- [ ] 能正常访问 http://localhost:8050
- [ ] 能看到门店下拉选项
- [ ] 选择门店后能加载数据
- [ ] 分类销售图表显示正常
- [ ] 滞销品统计显示正常（不是全0）
- [ ] 库存周转显示正常（不是全0）

## 🔧 常见问题排查

### 问题1：psycopg2安装失败

**症状**：
```
ERROR: Could not build wheels for psycopg2
```

**解决方案A**（推荐）：
```powershell
# 使用binary版本
pip install psycopg2-binary==2.9.9
```

**解决方案B**：
```powershell
# 安装Visual C++ Build Tools
# 下载：https://visualstudio.microsoft.com/downloads/
# 安装时选择"Desktop development with C++"
```

### 问题2：数据库连接失败

**症状**：
```
FATAL: password authentication failed for user "postgres"
```

**排查步骤**：
1. 检查密码是否正确
2. 检查.env中的DATABASE_URL格式
3. 验证PostgreSQL服务是否运行
```powershell
# 检查服务状态
Get-Service postgresql*
# 应显示 Status: Running
```

### 问题3：库存字段全是0

**原因**：数据库JOIN逻辑问题（已修复）

**验证修复**：
```powershell
# 检查data_source_manager.py
python -c "from database.data_source_manager import DataSourceManager; print('✅ 数据源管理器正常')"
```

### 问题4：导入数据后表为空

**排查**：
```sql
-- 检查数据是否真的导入了
SELECT COUNT(*) FROM orders;

-- 检查表结构
\d orders
```

**解决方案**：
- 确认Excel文件路径正确
- 检查字段映射是否匹配
- 查看导入日志中的错误信息

## 📊 性能优化建议

### 数据库优化

```sql
-- 创建索引（提升查询速度）
CREATE INDEX idx_orders_date ON orders(date);
CREATE INDEX idx_orders_store ON orders(store_name);
CREATE INDEX idx_orders_product ON orders(product_name);

-- 分析表（更新统计信息）
ANALYZE orders;
ANALYZE products;
```

### Python优化

```python
# 使用连接池（connection.py已配置）
pool_size=5           # 同时5个连接
max_overflow=10       # 最多15个连接
pool_recycle=3600     # 1小时回收
```

## 🔐 安全建议

### 生产环境配置

**1. 修改默认密码**
```sql
ALTER USER postgres WITH PASSWORD '复杂的强密码';
```

**2. 限制远程访问**
编辑 `pg_hba.conf`：
```
# 仅允许本地连接
host    all    all    127.0.0.1/32    md5
```

**3. 定期备份**
```powershell
# 备份数据库
pg_dump -U postgres -d o2o_dashboard -f backup.sql

# 恢复数据库
psql -U postgres -d o2o_dashboard -f backup.sql
```

## 📚 进阶学习资源

### PostgreSQL
- 官方文档：https://www.postgresql.org/docs/
- 中文教程：https://www.runoob.com/postgresql/

### SQLAlchemy
- 官方文档：https://docs.sqlalchemy.org/
- ORM教程：https://docs.sqlalchemy.org/en/20/orm/

### Dash
- 官方文档：https://dash.plotly.com/
- 示例库：https://dash-gallery.plotly.host/

## 🎯 总结

**必需环境**：
1. ✅ PostgreSQL 15+（数据库）
2. ✅ Python 3.9+（运行环境）
3. ✅ pip包：sqlalchemy, psycopg2-binary, pandas, dash

**可选环境**：
1. pgAdmin（图形化管理工具）
2. Redis（缓存加速，可选）
3. Nginx（生产部署，可选）

**配置核心**：
- `.env`文件：数据库连接配置
- `requirements.txt`：Python依赖清单
- `database/models.py`：数据表结构定义
- `database/data_source_manager.py`：数据加载逻辑

**数据流程**：
```
Excel → PostgreSQL → SQLAlchemy → Pandas → Dash → 浏览器
 导入     存储        查询        计算      展示     显示
```

---

**配置完成后的验证命令**：
```powershell
# 1. 测试数据库连接
python -c "from database.connection import engine; print(engine.connect())"

# 2. 测试数据查询
python -c "from database.data_source_manager import DataSourceManager; m=DataSourceManager(); df=m.load_from_database(store_name='惠宜选超市（徐州祥和路店）'); print(f'查询到{len(df)}条数据')"

# 3. 启动看板
python 智能门店看板_Dash版.py
```

如有问题，请参考本文档的"常见问题排查"章节。
