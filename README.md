# 🏪 智能门店经营看板 - 全栈版

## 📊 项目介绍

O2O门店智能经营分析看板，采用前后端分离架构，提供：
- 📈 实时销售数据分析
- 🎯 商品四象限分析（动销 × 利润）
- ⏰ 时段场景智能分析
- 🤖 AI智能经营建议
- 📦 商品生命周期管理

## 🏗️ 技术架构

### 后端
- **FastAPI** - 高性能异步API框架
- **PostgreSQL** - 关系型数据库
- **SQLAlchemy** - ORM
- **Celery** - 异步任务队列（可选）

### 前端
- **Dash** - Python可视化框架
- **Plotly/ECharts** - 图表库
- **Dash Bootstrap** - UI组件

### AI引擎
- **智谱GLM-4** - 智能分析
- **场景智能打标引擎** - 自动场景识别
- **PandasAI** - 自然语言数据分析（可选）

## 📁 项目结构

```
测算模型/
├── backend/                    # 后端目录
│   ├── api/                   # API路由
│   ├── models/                # 数据库模型
│   ├── services/              # 业务逻辑
│   └── main.py               # 后端入口
├── frontend/                   # 前端目录
│   └── 智能门店看板_Dash版.py
├── database/                   # 数据库脚本
│   ├── models.py             # 表结构定义
│   └── migrate.py            # 数据迁移
├── ai_modules/                 # AI模块
│   ├── 商品场景智能打标引擎.py
│   ├── ai_business_context.py
│   └── ...
├── requirements.txt           # 依赖包
├── .env.example              # 环境变量示例
├── .gitignore                # Git忽略文件
└── README.md                 # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

复制 `.env.example` 为 `.env`，配置数据库连接：

```env
DATABASE_URL=postgresql://用户名:密码@localhost:5432/o2o_dashboard
```

### 3. 导入数据

```bash
python database/migrate.py
```

### 4. 启动后端

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. 启动前端

```bash
python frontend/智能门店看板_Dash版.py
```

### 6. 访问看板

浏览器打开：http://localhost:8050

## 📊 核心功能

### Tab 1 - 经营诊断
- 智能诊断引擎
- 异常预警
- AI建议

### Tab 2 - 商品分析
- 四象限分析
- 订单级盈利分析
- 商品生命周期

### Tab 3 - 竞品对比
- 价格对比
- 竞争力分析

### Tab 4 - 利润分析
- 分类利润结构
- 成本分析

### Tab 5 - 时段场景分析
- 场景智能识别
- 时段热力图
- 场景利润矩阵

## 🔧 开发指南

### 添加新API接口

在 `backend/api/` 下创建路由文件：

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/products")
async def get_products():
    return {"data": []}
```

### 数据库迁移

修改 `database/models.py` 后，运行：

```bash
python database/migrate.py --upgrade
```

## 📝 待办事项

- [ ] PostgreSQL数据库集成
- [ ] FastAPI后端API
- [ ] 前后端完全分离
- [ ] Redis缓存层
- [ ] Celery异步任务
- [ ] 用户认证系统
- [ ] 多门店支持
- [ ] Docker部署

## 📄 License

MIT License

## 👥 贡献者

- 主要开发者：您的名字

---

**最后更新：2025年11月3日**
