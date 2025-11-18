"""
数据库优先开发规范 - 代码级烙印

⚠️ 重要：本文件定义了项目的核心开发原则
任何修改看板功能的开发者必须遵守这些规则！
"""

# ============================================================
# 核心烙印：DATABASE FIRST
# ============================================================

DATABASE_FIRST_PRINCIPLES = {
    "principle": "所有看板开发和优化必须结合数据库实现",
    
    "rules": [
        "数据存储 → 使用 PostgreSQL 数据库",
        "数据读取 → 优先从数据库查询",
        "数据上传 → 导入到数据库后再使用",
        "临时分析 → 可以用Excel，但最终要入库",
        "性能优化 → 使用数据库索引和缓存表",
        "多门店数据 → 必须使用数据库汇总",
    ],
    
    "禁止行为": [
        "❌ 硬编码Excel文件路径",
        "❌ 直接读取Excel而不考虑数据库",
        "❌ 使用临时CSV文件存储中间结果",
        "❌ 在代码中写死数据文件名",
        "❌ 忽略数据库已有的数据",
    ],
    
    "推荐架构": """
    用户 → Dash看板 → FastAPI → PostgreSQL
                ↓
            (临时：Excel)
    """,
}

# ============================================================
# 高优行动项（烙印到代码）
# ============================================================

HIGH_PRIORITY_TASKS = {
    "P0_CRITICAL": {
        "name": "修复订单导入重复ID问题",
        "status": "✅ COMPLETED - 2025-11-05",
        "impact": "已解除所有数据库功能阻塞",
        "file": "database/simple_order_import.py",
        "solution": "使用 check-update-or-insert 逻辑",
        "result": "成功导入 5,857 条订单数据",
    },
    
    "P1_HIGH": {
        "name": "批量历史数据导入",
        "status": "✅ COMPLETED - 2025-11-05",
        "file": "database/batch_import.py",
        "goal": "一键导入所有历史Excel到数据库",
        "features": [
            "✅ 递归扫描目录下所有Excel文件",
            "✅ 自动处理重复数据（更新模式）",
            "✅ 记录导入历史到数据库",
            "✅ 详细的进度和错误报告",
        ],
    },
    
    "P2_MEDIUM": {
        "name": "看板数据源切换",
        "status": "✅ COMPLETED - 2025-11-05",
        "files": [
            "database/data_source_manager.py - 数据源管理器",
            "dashboard_with_source_switch.py - 带切换的看板",
        ],
        "features": [
            "✅ 数据源选择器（Excel / 数据库）",
            "✅ Excel路径可配置",
            "✅ 数据库过滤器（门店、日期）",
            "✅ 实时数据加载和刷新",
        ],
    },
    
    "P3_NORMAL": {
        "name": "前后端完全集成",
        "status": "✅ COMPLETED - 2025-11-05",
        "file": "dashboard_integrated.py",
        "goal": "看板通过API获取数据，不直接连DB",
        "architecture": "前端(Dash:8051) → HTTP API → 后端(FastAPI:8000) → 数据库",
        "features": [
            "✅ 完全通过API通信",
            "✅ RESTful接口调用",
            "✅ 前后端分离架构",
            "✅ 手动刷新功能",
        ],
    },
    
    "P4_FUTURE": {
        "name": "高级分析功能",
        "status": "📋 待规划",
        "features": [
            "多门店数据对比",
            "趋势预测分析",
            "自动化报告生成",
            "数据导出功能",
        ],
    },
}

# ============================================================
# 开发前检查清单（代码级强制）
# ============================================================

def check_before_coding(feature_description: str) -> dict:
    """
    开发任何看板功能前，必须运行此检查
    
    Args:
        feature_description: 功能描述
    
    Returns:
        检查结果和建议
    """
    checklist = {
        "需要存储数据吗？": "如果是 → 使用数据库表",
        "需要查询历史数据吗？": "如果是 → 从数据库读取",
        "需要汇总多个文件吗？": "如果是 → 数据必须先入库",
        "数据会被重复使用吗？": "如果是 → 存入数据库避免重复计算",
        "需要跨时间段分析吗？": "如果是 → 数据库查询更高效",
        "是一次性临时分析吗？": "如果是 → 可以直接用Excel",
    }
    
    recommendations = {
        "数据源选择": "优先级：数据库 > API > Excel文件",
        "存储策略": "持久化数据必须入库，临时数据可用内存",
        "性能考虑": "大数据量（>10万行）必须用数据库",
        "维护性": "所有业务数据应该有数据库备份",
    }
    
    return {
        "checklist": checklist,
        "recommendations": recommendations,
        "database_first": True,
    }

# ============================================================
# 数据加载标准接口（统一规范）
# ============================================================

class DataLoadingStandard:
    """
    数据加载标准接口
    所有看板数据加载必须通过此接口
    """
    
    @staticmethod
    def load_orders(source: str = "database", **filters):
        """
        加载订单数据
        
        Args:
            source: "database" (推荐) 或 "excel" (临时)
            **filters: 筛选条件
        
        Returns:
            pd.DataFrame
        """
        if source == "database":
            # 从数据库加载（推荐）
            from database.data_loader import DatabaseDataLoader
            return DatabaseDataLoader.load_orders(**filters)
        
        elif source == "excel":
            # 从Excel加载（临时方案）
            print("⚠️ 警告：使用Excel临时方案，建议迁移到数据库！")
            from 真实数据处理器 import RealDataProcessor
            processor = RealDataProcessor()
            data_dict = processor.load_all_data()
            return list(data_dict.values())[0] if data_dict else None
        
        else:
            raise ValueError(f"不支持的数据源: {source}")
    
    @staticmethod
    def load_products(source: str = "database", **filters):
        """加载商品数据"""
        # 实现逻辑同上
        pass

# ============================================================
# 开发者备忘录（写在注释里的烙印）
# ============================================================

DEVELOPER_MEMO = """
┌──────────────────────────────────────────────────────────┐
│  🔥 如果你正在开发看板功能，请阅读此备忘录！              │
│                                                          │
│  核心原则：数据库优先 (Database First)                    │
│                                                          │
│  ✅ 推荐做法：                                            │
│     1. 数据存储到 PostgreSQL                              │
│     2. 通过 FastAPI 提供接口                              │
│     3. Dash看板调用API获取数据                            │
│     4. 使用 AnalysisCache 表缓存计算结果                  │
│                                                          │
│  ❌ 禁止做法：                                            │
│     1. 硬编码 Excel 文件路径                              │
│     2. 直接读取Excel不考虑数据库                          │
│     3. 用CSV临时存储中间结果                              │
│     4. 忽略已有的数据库数据                                │
│                                                          │
│  📋 开发前必问的3个问题：                                  │
│     Q1: 这个功能能从数据库获取数据吗？                     │
│     Q2: 如果能，为什么不用数据库？                         │
│     Q3: 如果用Excel，何时迁移到数据库？                   │
│                                                          │
│  🎯 当前高优任务：                                        │
│     P0: 修复订单导入重复ID (migrate_orders.py)           │
│     P1: 批量历史数据导入 (batch_import.py)               │
│     P2: 看板数据源切换 (智能门店看板_Dash版.py)           │
│                                                          │
│  📖 详细路线图：DEVELOPMENT_ROADMAP.md                    │
└──────────────────────────────────────────────────────────┘
"""

# ============================================================
# 版本控制（跟踪烙印执行情况）
# ============================================================

DATABASE_INTEGRATION_STATUS = {
    "版本": "1.0.0",
    "创建日期": "2025-11-04",
    "烙印状态": "🔥 ACTIVE - 强制执行",
    
    "数据库集成进度": {
        "后端API": "✅ 完成 (FastAPI + SQLAlchemy)",
        "数据库表": "✅ 完成 (6张表已创建)",
        "商品导入": "✅ 完成 (3,974条)",
        "订单导入": "❌ 阻塞 (重复ID问题)",
        "看板集成": "⏳ 待开始",
        "批量导入": "⏳ 待开始",
    },
    
    "下一里程碑": {
        "目标": "完成订单导入，解锁数据库完整功能",
        "预计完成": "立即执行",
        "责任人": "AI Assistant + User",
    },
}

# ============================================================
# 自动提醒机制（在关键文件中导入此模块）
# ============================================================

def remind_database_first():
    """在关键操作时提醒开发者遵守数据库优先原则"""
    print("\n" + "="*60)
    print("[DATABASE FIRST] 数据库优先原则提醒")
    print("="*60)
    print("[INFO] 你正在进行数据操作，请确认：")
    print("   OK  是否需要存储到数据库？")
    print("   OK  是否可以从数据库读取？")
    print("   OK  如果使用Excel，是否只是临时方案？")
    print("="*60 + "\n")

# 导出所有规范
__all__ = [
    'DATABASE_FIRST_PRINCIPLES',
    'HIGH_PRIORITY_TASKS',
    'check_before_coding',
    'DataLoadingStandard',
    'DEVELOPER_MEMO',
    'DATABASE_INTEGRATION_STATUS',
    'remind_database_first',
]

if __name__ == "__main__":
    print(DEVELOPER_MEMO)
    print("\n📊 当前数据库集成状态：")
    for key, value in DATABASE_INTEGRATION_STATUS["数据库集成进度"].items():
        print(f"   {key}: {value}")
