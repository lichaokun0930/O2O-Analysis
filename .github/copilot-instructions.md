# O2O智能门店经营看板 - AI开发指南

## 项目概览

**业务场景**: O2O闪购零售系统(美团/饿了么),6000+ SKU,上千家门店,24小时运营  
**核心目标**: 门店利润最大化,基于数据驱动的经营决策  
**技术栈**: Dash Web框架 + PostgreSQL + Redis + 智能分析引擎

## 架构关键点

### 数据流架构
```
Excel订单导入 → PostgreSQL(orders表) → Redis缓存层 → Dash看板 → ECharts/Plotly可视化
                        ↓
                  AI分析引擎(GLM-4/Gemini)
```

### 核心组件
- **主看板**: `智能门店看板_Dash版.py` (21910行,6个Tab页,统一入口)
- **数据库**: `database/models.py` (Order/Product/SceneTag等表结构)
- **AI引擎**: 
  - `商品场景智能打标引擎.py` - 多维度场景识别(早餐/夜宵/季节/节假日)
  - `场景营销智能决策引擎.py` - FP-Growth关联挖掘、XGBoost场景预测、RFM客户分群
  - `ai_analyzer.py` - 统一AI接口(支持GLM/Gemini/Qwen)
  - `ai_business_context.py` - 业务上下文和Few-Shot示例库
- **缓存层**: `redis_cache_manager.py` + `cache_utils.py` (多用户数据共享)
- **UI工厂**: `echarts_factory.py`, `component_styles.py`, `loading_components.py`

## 关键业务逻辑

### ⚠️ 订单数据结构 - 多行一订单
```python
# 一个订单ID对应多行数据,每行=一个商品SKU
# 订单2212367025示例:
#   行1: 商品A(冲锋衣) → 商品实售价:78元, 预计订单收入:69.56元
#   行2: 商品B(购物袋) → 商品实售价:0元,  预计订单收入:0元

# ✅ 正确聚合方式
order_agg = df.groupby('订单ID').agg({
    '配送费': 'first',        # 订单级字段用first(多行中值相同)
    '商品实售价': 'sum',       # 商品级字段用sum
    '预计订单收入': 'sum',     # ⭐ 商品级字段,不能用first!
    '平台服务费': 'sum',       # ⭐ 商品级字段,每个SKU一条记录
    '利润额': 'sum'
})

# ❌ 错误: 用first聚合商品级字段会丢失60%数据
```

**权威数据字典**: 见`【权威】业务逻辑与数据字典完整手册.md` (1389行完整定义)

### 利润计算标准
```python
# 商品毛利 = 商品实售价 - 商品成本
# 订单利润 = Σ(商品毛利) - 配送费 - 平台佣金 - 平台服务费 + 企客后返
# 利润率 = 订单利润 / 订单总额 × 100%

# 健康指标阈值
利润率: 8-15% (警戒线<5%)
商品成本占比: 55-65% (失控线>70%)
履约成本占比: 8-12% (失控线>15%)
```

### 商品角色分类
- **流量品**: 高频刚需,低毛利(<15%),占比25-30%,用于引流不单独促销
- **利润品**: 高毛利(>30%),占比40-50%,核心盈利来源,最大化销量
- **形象品**: 品牌力强,毛利15-30%,占比20-25%,提升门店信任度

## 开发工作流

### 0. 新电脑首次配置
```powershell
# 从GitHub克隆后第一次使用
.\setup_new_pc.ps1  # 自动配置Python环境和依赖

# 手动配置数据库和Redis
# 1. 安装PostgreSQL 15.x (https://www.postgresql.org/download/windows/)
# 2. 安装Redis/Memurai (运行 .\启动Redis.ps1 自动安装)
# 3. 修改.env文件中的数据库密码
# 4. 初始化数据库: python database\migrate.py

# 详细步骤见: 新电脑完整配置指南.md 或 新电脑配置状态报告.md
```

### 1. 启动系统
```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 启动PostgreSQL数据库
.\启动数据库.ps1

# 启动Redis缓存
.\启动Redis.ps1

# 启动看板(开发模式)
.\启动看板.ps1
# 访问: http://localhost:8050

# 后台模式(生产环境)
.\启动看板-后台模式.bat
```

### 2. 数据库操作
```python
# 查询订单数据
from database.connection import get_db_connection
from sqlalchemy.orm import Session

with get_db_connection() as session:
    orders = session.query(Order).filter(
        Order.date >= start_date,
        Order.store_name == '祥和路店'
    ).all()

# 数据导入: 使用 智能导入门店数据.py
# 数据迁移: database/migrate.py (Alembic框架)
```

### 3. AI分析调用
```python
# 统一AI接口
from ai_analyzer import get_ai_analyzer

analyzer = get_ai_analyzer(model_type='glm')  # 或'gemini'
response = analyzer.analyze_with_context(
    prompt="分析当前利润率下降原因",
    data_context={"利润率": 0.065, "历史利润率": 0.12}
)

# 环境变量配置 (见 .env.example)
ZHIPU_API_KEY=your_glm_key
GEMINI_API_KEY=your_gemini_key
```

### 4. 缓存策略
```python
# 装饰器模式缓存DataFrame
from redis_config import cache_dataframe, redis_cache

@cache_dataframe(redis_cache, 'orders_by_date', expire=1800)
def get_orders_by_date(start_date, end_date):
    # 第一次: 查数据库存Redis
    # 后续: 直接从Redis读(30分钟内)
    return query_database(start_date, end_date)

# 手动清理缓存
redis_cache.clear_all()
```

## 项目约定

### 代码风格
- **字段命名**: 使用中文字段名(如`订单ID`, `商品实售价`)与Excel数据保持一致
- **函数注释**: Docstring必须包含业务逻辑说明和数据聚合规则
- **错误处理**: 数据异常时返回友好提示,不抛出裸异常给前端

### UI组件规范
```python
# 使用统一卡片工厂
from component_styles import create_card, create_stat_card

card = create_stat_card(
    title="利润率",
    value="8.5%",
    icon="📊",
    trend="+2.3%",
    color="success"
)

# ECharts图表使用工厂函数
from echarts_factory import create_metric_bar_card, COMMON_COLORS

chart = create_metric_bar_card(
    title="销售趋势",
    data=sales_data,
    color=COMMON_COLORS['blue']['base']
)
```

### 文档驱动开发
- **新功能**: 先更新`快速开始指南.md`再编码
- **数据字段**: 必须同步更新`【权威】业务逻辑与数据字典完整手册.md`
- **AI优化**: 在`ai_business_context.py`添加Few-Shot示例

## 测试和调试

### 单元测试
```powershell
# 运行全部测试
pytest verify_check/

# 测试特定模块
pytest verify_check/test_scene_tagging.py -v
```

### 性能分析
```python
# 查看Redis缓存统计
python 测试Redis性能.py

# 分析SQL查询性能
python database/analyze_query_performance.py
```

### 数据验证
```python
# 检查订单成本数据
python 检查Order表cost字段.py

# 验证利润计算
python 验证祥和路成本.py
```

## 常见陷阱

1. **订单聚合错误**: 不要对商品级字段(预计订单收入/平台服务费)使用`.first()`
2. **缓存穿透**: 高频查询必须加Redis缓存,避免打爆数据库
3. **AI调用限流**: GLM-4 API有频率限制,批量分析时加`time.sleep(0.5)`
4. **时区问题**: 订单时间统一使用`Asia/Shanghai`,不要用UTC
5. **门店筛选**: "咖啡"渠道订单需单独剔除(非标准O2O业务)

## 参考资料

- **新电脑配置**: `新电脑完整配置指南.md`, `新电脑配置状态报告.md`, `setup_new_pc.ps1`
- **业务逻辑**: `【权威】业务逻辑与数据字典完整手册.md`
- **数据标准**: `数据结构统一标准.md`, `数据字段映射规范.md`
- **快速上手**: `快速开始指南.md`, `智能门店看板_Dash版使用指南.md`
- **环境配置**: `PostgreSQL环境配置完整指南.md`, `Redis安装配置指南.md`
- **AI集成**: `GLM-4.6接入指南.md`, `商品场景智能打标_集成指南.md`
- **部署指南**: `局域网多人访问指南.md`, `B电脑克隆清单.md`
