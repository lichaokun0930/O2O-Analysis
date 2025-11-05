# P1/P2/P3 任务说明

## 📋 任务概览

### ✅ P1: 批量历史数据导入
**文件**: `database/batch_import.py`

**功能**:
- 扫描指定目录下的所有Excel文件
- 自动提取商品和订单数据
- 批量导入到PostgreSQL数据库
- 记录导入历史和错误日志

**使用方法**:
```powershell
# 导入默认目录（实际数据）
D:/办公/Python/python.exe database/batch_import.py

# 导入指定目录
D:/办公/Python/python.exe database/batch_import.py "D:\Your\Data\Path"
```

**特性**:
- ✅ 自动处理重复数据（更新而非报错）
- ✅ 支持多种Excel格式（.xlsx, .xls, .xlsm）
- ✅ 自动过滤耗材和咖啡渠道
- ✅ 记录每个文件的导入状态

---

### ✅ P2: 数据源管理器
**文件**: `database/data_source_manager.py`

**功能**:
- 统一的数据加载接口
- 支持Excel和数据库双数据源
- 提供数据库统计和查询功能

**使用方法**:
```python
from database.data_source_manager import DataSourceManager

manager = DataSourceManager()

# 从Excel加载
df_excel = manager.load_data(source='excel', file_path='订单数据.xlsx')

# 从数据库加载
df_db = manager.load_data(source='database', store_name='门店A')

# 获取数据库统计
stats = manager.get_database_stats()
```

**API**:
- `load_from_excel(file_path)` - 从Excel加载数据
- `load_from_database(store_name, start_date, end_date)` - 从数据库加载
- `load_data(source, **kwargs)` - 统一接口
- `get_available_stores()` - 获取门店列表
- `get_date_range()` - 获取数据日期范围
- `get_database_stats()` - 获取数据库统计

---

### ✅ P2增强: 数据源切换看板
**文件**: `dashboard_with_source_switch.py`

**功能**:
- Dash可视化看板
- **UI数据源切换器**（Excel/数据库）
- 实时数据加载和刷新
- 多维度数据分析

**启动方法**:
```powershell
# 启动看板（端口8050）
D:/办公/Python/python.exe dashboard_with_source_switch.py

# 访问地址
http://localhost:8050
```

**特性**:
- 📁 **数据源选择器**: 一键切换Excel和数据库
- 🔍 **数据库过滤器**: 按门店、日期范围筛选
- 📊 **4大分析模块**: 订单概览、商品分析、收入分析、场景分析
- 🔄 **实时刷新**: 手动刷新数据按钮
- 📈 **交互式图表**: Plotly可视化

---

### ✅ P3: 前后端集成看板
**文件**: `dashboard_integrated.py`

**功能**:
- 完全通过API调用后端
- 前后端分离架构
- RESTful接口集成

**启动方法**:
```powershell
# 1. 确保后端运行
python -m uvicorn backend.main:app --port 8000

# 2. 启动前端（端口8051，避免冲突）
D:/办公/Python/python.exe dashboard_integrated.py

# 访问地址
http://localhost:8051
```

**架构**:
```
前端 (Dash - 8051)  →  HTTP API  →  后端 (FastAPI - 8000)  →  数据库 (PostgreSQL)
```

**API调用示例**:
- `/api/health` - 健康检查
- `/api/stats` - 数据统计
- `/api/orders?limit=1000` - 订单列表
- `/api/products?limit=500` - 商品列表

---

## 🚀 快速开始

### 1. P1: 导入历史数据
```powershell
# 进入项目目录
cd "D:\Python1\O2O_Analysis\O2O数据分析\测算模型"

# 执行批量导入
D:/办公/Python/python.exe database/batch_import.py

# 确认导入（输入yes）
```

### 2. P2: 启动数据源切换看板
```powershell
# 确保数据库服务运行
# 启动看板
D:/办公/Python/python.exe dashboard_with_source_switch.py

# 打开浏览器: http://localhost:8050
# 1. 选择数据源: Excel 或 数据库
# 2. 点击"加载数据"
# 3. 查看分析结果
```

### 3. P3: 启动前后端集成看板
```powershell
# 终端1: 启动后端
python -m uvicorn backend.main:app --port 8000 --reload

# 终端2: 启动前端
D:/办公/Python/python.exe dashboard_integrated.py

# 访问: http://localhost:8051
```

---

## 📊 任务对比

| 特性 | P1 批量导入 | P2 数据源切换 | P3 API集成 |
|------|------------|--------------|-----------|
| **用途** | 数据导入 | 看板展示 | 前后端分离 |
| **Excel支持** | ✅ 批量导入 | ✅ 实时加载 | ❌ 仅API |
| **数据库支持** | ✅ 写入 | ✅ 读取 | ✅ 通过API |
| **用户交互** | 命令行 | Web UI | Web UI |
| **数据过滤** | 自动 | 手动选择 | API参数 |
| **实时性** | 离线导入 | 实时切换 | 实时API |

---

## 🔧 配置说明

### 数据库配置
文件: `.env`
```
DATABASE_URL=postgresql://postgres:308352588@localhost:5432/o2o_dashboard
```

### 默认路径
- Excel数据: `门店数据\比价看板模块\订单数据-本店.xlsx`
- 历史数据: `实际数据\` (P1批量导入)
- 数据库: `localhost:5432/o2o_dashboard`

### 端口分配
- 后端 FastAPI: `8000`
- 前端 Dash (P2): `8050`
- 前端 Dash (P3): `8051`

---

## ✅ 完成标准

### P1 完成标准
- [x] 支持批量扫描Excel文件
- [x] 自动提取商品和订单
- [x] 处理重复数据（更新）
- [x] 记录导入历史
- [x] 错误处理和日志

### P2 完成标准
- [x] 数据源管理器类
- [x] Excel加载功能
- [x] 数据库加载功能
- [x] UI切换器
- [x] 数据统计API

### P3 完成标准
- [x] 通过API调用后端
- [x] 不直接读取Excel/数据库
- [x] 前后端分离架构
- [x] 实时数据刷新
- [x] 健康检查和错误处理

---

## 📝 下一步计划

### P4: 高级功能（未来）
- 多门店对比分析
- 趋势预测（时间序列）
- 自动化报告生成
- 数据导出功能
- 用户权限管理

---

## 🆘 故障排除

### 问题1: 导入失败
```
错误: 找不到Excel文件
解决: 检查文件路径是否正确
```

### 问题2: 数据库连接失败
```
错误: could not connect to server
解决: 
1. 检查PostgreSQL服务是否启动
2. 验证.env中的数据库密码
3. 测试连接: psql -U postgres -d o2o_dashboard
```

### 问题3: 看板无法加载数据库数据
```
错误: 数据库返回0行
解决:
1. 先运行P1导入数据
2. 检查数据库是否有数据: SELECT COUNT(*) FROM orders;
```

### 问题4: P3看板API调用失败
```
错误: API Error: Connection refused
解决:
1. 确保后端服务已启动
2. 检查端口8000是否被占用
3. 访问: http://localhost:8000/api/health
```

---

## 📚 相关文件

- `DEVELOPMENT_ROADMAP.md` - 开发路线图
- `DATABASE_FIRST_STANDARD.py` - 数据库优先规范
- `test_system.py` - 系统集成测试
- `.env` - 环境配置
- `requirements.txt` - Python依赖

---

**创建时间**: 2025-11-05  
**状态**: ✅ P1/P2/P3 全部完成  
**下一步**: 用户测试和反馈
