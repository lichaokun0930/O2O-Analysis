#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能门店经营看板 - Dash版
启动命令: python "智能门店看板_Dash版.py"
访问地址: http://localhost:8050
"""
import base64
import io
import json
import os
import re
import sys
import warnings
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

# ⚡ 解决 Windows PowerShell 下 emoji 输出乱码问题 - 必须在任何print之前设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context, no_update
from dash.dependencies import ALL
from dash.exceptions import PreventUpdate

# 尝试导入 dash_echarts，如果失败则使用 Plotly 作为后备方案
try:
    from dash_echarts import DashECharts
    ECHARTS_AVAILABLE = True
    print("✅ ECharts 可用，将使用 ECharts 图表")
except ImportError:
    ECHARTS_AVAILABLE = False
    print("⚠️ dash_echarts 未安装，将使用 Plotly 图表作为后备方案")
    print("   提示：运行 'pip install dash-echarts' 以获得更好的图表效果")

warnings.filterwarnings('ignore')

# 应用目录及模块导入路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

# 导入商品场景智能打标引擎
try:
    from 商品场景智能打标引擎 import ProductSceneTagger
    SMART_TAGGING_AVAILABLE = True
    print("✅ 商品场景智能打标引擎已加载")
except ImportError as e:
    SMART_TAGGING_AVAILABLE = False
    print(f"⚠️ 商品场景智能打标引擎未找到: {e}")
    print("   部分高级场景分析功能将不可用")

# 导入Tab 5扩展渲染函数
try:
    from tab5_extended_renders import (
        render_heatmap_profit_matrix,
        render_trend_price_analysis,
        render_product_scene_network,
        render_product_scene_profile
    )
    TAB5_EXTENDED_RENDERS_AVAILABLE = True
    print("✅ Tab 5扩展渲染模块已加载")
except ImportError as e:
    TAB5_EXTENDED_RENDERS_AVAILABLE = False
    print(f"⚠️ Tab 5扩展渲染模块未找到: {e}")
    print("   热力图、利润矩阵等高级功能将不可用")

# 业务模块导入
from 问题诊断引擎 import ProblemDiagnosticEngine
from 真实数据处理器 import RealDataProcessor

# ✨ 导入数据源管理器（支持Excel/数据库双数据源）
try:
    from database.data_source_manager import DataSourceManager
    DATABASE_AVAILABLE = True
    print("✅ 数据库数据源已启用")
except ImportError as e:
    DATABASE_AVAILABLE = False
    DataSourceManager = None
    print(f"⚠️ 数据库模块未找到: {e}")
    print("   仅支持Excel数据源")

# ✨ 导入AI分析器模块（专注于数据洞察和策略建议）
from ai_analyzer import get_ai_analyzer

# ✨ 导入AI业务上下文模块（标准化业务逻辑 + 阶段1优化）
try:
    from ai_business_context import (
        get_health_warnings,
        BUSINESS_CONTEXT,
        get_analysis_prompt,
        FEW_SHOT_EXAMPLES,
        COT_TEMPLATE,
        DATA_VALIDATION_RULES
    )
    BUSINESS_CONTEXT_AVAILABLE = True
    print("✅ 业务上下文模块已加载 - GLM-4.6 阶段1优化启用")
    print("   ✓ Few-Shot示例库 (3个典型案例)")
    print("   ✓ CoT思维链 (6步分析流程)")
    print("   ✓ 数据验证规则 (刻在基因中)")
except ImportError:
    BUSINESS_CONTEXT_AVAILABLE = False
    print("⚠️ 业务上下文模块未找到,将使用基础AI分析")

# ✨ 导入场景推断工具模块（统一场景推断逻辑）
from scene_inference import (
    add_scene_and_timeslot_fields,
    get_available_scenes,
    get_available_timeslots,
    infer_scene,
    classify_timeslot
)

# ✨ 导入缓存工具模块（优化哈希计算）
from cache_utils import (
    calculate_data_hash_fast,
    save_dataframe_compressed,
    load_dataframe_compressed,
    get_cache_metadata,
    cleanup_old_caches
)

# ✨ 导入响应式工具函数
from echarts_responsive_utils import (
    calculate_chart_height,
    calculate_dynamic_grid,
    get_responsive_font_size,
    create_responsive_echarts_config
)

# ✨ 导入 PandasAI 智能分析模块（GLM-4.6 阶段2）
try:
    from ai_pandasai_integration import (
        SmartDataAnalyzer,
        QUERY_TEMPLATES,
        get_template_query
    )
    PANDAS_AI_MODULE_AVAILABLE = True
    print("✅ PandasAI 智能分析模块已加载 - 阶段2启用")
except ImportError as e:
    PANDAS_AI_MODULE_AVAILABLE = False
    print(f"⚠️ PandasAI 模块未找到: {e}")
    print("   自然语言数据洞察功能暂不可用")

# ✨ 导入 RAG 向量知识库模块（GLM-4.6 阶段3）- 暂时禁用避免下载模型
RAG_MODULE_AVAILABLE = False
VectorKnowledgeBase = None
RAGAnalyzer = None
init_default_knowledge_base = None
print("ℹ️ RAG 向量知识库模块已暂时禁用（避免下载模型）")

# 原始导入代码（需要时取消注释）
# try:
#     from ai_rag_knowledge_base import (
#         VectorKnowledgeBase,
#         RAGAnalyzer,
#         init_default_knowledge_base
#     )
#     RAG_MODULE_AVAILABLE = True
#     print("✅ RAG 向量知识库模块已加载 - 阶段3启用")
# except ImportError as e:
#     RAG_MODULE_AVAILABLE = False
#     print(f"⚠️ RAG 知识库模块未找到: {e}")
#     print("   历史案例检索与RAG增强分析暂不可用")
# except OSError as e:
#     # Torch DLL 加载失败时优雅降级
#     RAG_MODULE_AVAILABLE = False
#     if "DLL" in str(e) or "1114" in str(e):
#         print("⚠️ RAG 模块依赖的 Torch DLL 加载失败")
#         print("   解决方案: 安装 Visual C++ Redistributable")
#         print("   下载: https://aka.ms/vs/17/release/vc_redist.x64.exe")
#         print("   或执行: pip uninstall torch -y && pip install torch --index-url https://download.pytorch.org/whl/cpu")
#     else:
#         print(f"⚠️ RAG 模块加载失败: {e}")
#     print("   阶段3功能暂不可用，阶段1/2功能不受影响")

# ⭐ 关键业务规则：需要剔除的渠道（咖啡业务非O2O零售核心，与Streamlit保持一致）
CHANNELS_TO_REMOVE = ['饿了么咖啡', '美团咖啡']

# 缓存目录
CACHE_DIR = APP_DIR / "学习数据仓库" / "uploaded_data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Dash 应用初始化
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
)
app.title = "智能门店经营看板 - Dash版"
server = app.server
server.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB 上传限制

# 全局数据容器
GLOBAL_DATA = None
DIAGNOSTIC_ENGINE = None
UPLOADED_DATA_CACHE = None
DATA_SOURCE_MANAGER = None  # 数据源管理器实例

# 阶段2/阶段3 AI 智能助手全局实例
PANDAS_AI_ANALYZER = None
PANDAS_AI_TEMPLATES: Dict[str, str] = {}
VECTOR_KB_INSTANCE = None
RAG_ANALYZER_INSTANCE = None

PANDAS_TEMPLATE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "高利润商品": {"threshold": 20, "top_n": 10},
    "低客单价订单": {"threshold": 25},
    "滞销商品": {"days": 30},
    "时段销量分析": {},
    "场景营销效果": {},
    "商品角色分布": {},
    "成本结构分析": {},
    "营销ROI排名": {"top_n": 10}
}


def load_real_business_data():
    """加载真实业务数据（使用标准化处理器）"""
    candidate_dirs = [
        APP_DIR / "实际数据",
        APP_DIR.parent / "实际数据",
        APP_DIR / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据" / "比价看板模块",
    ]

    data_file = None
    for data_dir in candidate_dirs:
        if data_dir.exists():
            excel_files = sorted([f for f in data_dir.glob("*.xlsx") if not f.name.startswith("~$")])
            if excel_files:
                data_file = excel_files[0]
                break

    if not data_file:
        print("⚠️ 未找到数据文件，使用示例数据")
        return None

    try:
        print(f"📂 正在加载数据: {data_file.name}")
        xls = pd.ExcelFile(data_file)

        # 读取第一个sheet作为订单数据
        df = pd.read_excel(xls, sheet_name=0)
        print(f"📊 原始数据加载: {len(df)} 行 × {len(df.columns)} 列")
        print(f"📋 原始字段: {list(df.columns)[:10]}...")

        # ⭐ 使用真实数据处理器标准化（关键步骤）
        processor = RealDataProcessor()
        df_standardized = processor.standardize_sales_data(df)

        print(f"✅ 数据标准化完成: {len(df_standardized)} 行")
        print(f"📊 标准化字段: {list(df_standardized.columns)[:10]}...")

        # 检查关键字段
        required_fields = ['商品名称', '商品实售价', '日期']
        missing_fields = [f for f in required_fields if f not in df_standardized.columns]

        if missing_fields:
            print(f"⚠️ 缺失关键字段: {missing_fields}")
        else:
            print(f"✅ 关键字段验证通过")

        # 🆕 使用统一的场景推断模块
        df_standardized = add_scene_and_timeslot_fields(df_standardized)

        scenes = get_available_scenes(df_standardized)
        timeslots = get_available_timeslots(df_standardized)

        print(f"✅ 已生成场景和时段字段")
        print(f"   场景选项: {scenes}")
        print(f"   时段选项: {timeslots}")

        return df_standardized

    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return None


def _sanitize_filename(file_name: str) -> str:
    if not file_name:
        return "uploaded_data"
    stem = Path(file_name).stem if file_name else "uploaded_data"
    sanitized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]+", "_", stem).strip("_")
    return sanitized or "uploaded_data"


def save_data_to_cache(df: pd.DataFrame, original_file: str) -> str:
    """保存DataFrame到缓存目录，自动去重并写入元数据"""
    try:
        if df is None or df.empty:
            return "跳过保存：数据为空"

        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        data_hash = calculate_data_hash_fast(df)
        existing = load_cached_data_list()
        for cache_info in existing:
            if cache_info.get('data_hash') == data_hash:
                return f"跳过保存：已存在相同数据 ({cache_info.get('file_name', '未知文件')})"

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = _sanitize_filename(original_file)
        cache_file = CACHE_DIR / f"{safe_name}_{timestamp}_{data_hash[:8]}.pkl.gz"

        metadata = {
            'original_file': original_file,
            'upload_time': datetime.now().isoformat(),
            'rows': int(len(df)),
            'columns': list(df.columns),
            'data_hash': data_hash,
            'file_name': cache_file.name
        }

        payload: Dict[str, Any] = {
            'data': df,
            'metadata': metadata
        }

        size_bytes = save_dataframe_compressed(payload, cache_file)
        metadata['size_mb'] = round(size_bytes / 1024 / 1024, 2) if size_bytes else 0

        # 清理过期缓存，保留最近的12个，最长保留14天
        try:
            cleanup_old_caches(CACHE_DIR, max_age_hours=24 * 14, keep_latest=12)
        except Exception as cleanup_err:
            print(f"⚠️ 清理缓存失败: {cleanup_err}")

        return str(cache_file)

    except Exception as e:
        print(f"❌ 保存缓存失败: {e}")
        return f"保存失败: {e}"


def load_data_from_cache(file_path: str) -> Optional[pd.DataFrame]:
    """从缓存文件加载DataFrame"""
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️ 缓存文件不存在: {file_path}")
            return None

        payload = load_dataframe_compressed(path)

        if isinstance(payload, dict):
            df = payload.get('data')
            if isinstance(df, pd.DataFrame):
                return df
            if df is not None:
                return pd.DataFrame(df)
        elif isinstance(payload, pd.DataFrame):
            return payload

        print(f"⚠️ 缓存文件格式未知: {file_path}")
        return None

    except Exception as e:
        print(f"❌ 加载缓存失败: {e}")
        return None


def load_cached_data_list() -> List[Dict[str, Any]]:
    """列出缓存目录中的所有历史数据"""
    if not CACHE_DIR.exists():
        return []

    cached_files: List[Dict[str, Any]] = []

    for file_path in sorted(CACHE_DIR.glob("*.pkl.gz"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = load_dataframe_compressed(file_path)
            metadata: Dict[str, Any] = {}
            df: Optional[pd.DataFrame] = None

            if isinstance(payload, dict):
                metadata = payload.get('metadata', {}) or {}
                df_obj = payload.get('data')
                if isinstance(df_obj, pd.DataFrame):
                    df = df_obj
            elif isinstance(payload, pd.DataFrame):
                df = payload

            rows = metadata.get('rows')
            if rows is None and isinstance(df, pd.DataFrame):
                rows = len(df)

            cached_files.append({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'original_file': metadata.get('original_file', file_path.stem),
                'upload_time': metadata.get('upload_time', 'Unknown'),
                'rows': int(rows) if rows is not None else 0,
                'size_mb': round(file_path.stat().st_size / 1024 / 1024, 2),
                'data_hash': metadata.get('data_hash', ''),
            })

        except Exception as e:
            print(f"⚠️ 读取缓存文件失败: {file_path.name} - {e}")
            continue

    return cached_files


def process_uploaded_excel(contents, filename):
    """
    处理上传的Excel文件
    
    Args:
        contents: base64编码的文件内容
        filename: 文件名
        
    Returns:
        处理后的DataFrame或None
    """
    import base64
    
    import base64

    try:
        # 解码base64内容
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        file_suffix = Path(filename).suffix.lower()
        buffer = BytesIO(decoded)

        if file_suffix in {'.xlsx', '.xls', '.xlsm', '.xlsb'}:
            df = pd.read_excel(buffer)
        elif file_suffix == '.csv':
            # 尝试常见编码读取CSV
            for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']:
                buffer.seek(0)
                try:
                    df = pd.read_csv(buffer, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("CSV 文件无法解码（尝试编码: utf-8-sig / utf-8 / gbk / gb2312）")
        else:
            raise ValueError(f"不支持的文件类型: {file_suffix or '（无后缀）'}")

        print(f"📖 成功读取文件: {filename} ({len(df):,}行 × {len(df.columns)}列)")

        # 保存到缓存
        save_data_to_cache(df, filename)

        return df

    except Exception as e:
        print(f"❌ 读取文件 {filename} 失败: {str(e)}")
        return None


def initialize_data():
    """初始化数据和诊断引擎"""
    global GLOBAL_DATA, DIAGNOSTIC_ENGINE, DATA_SOURCE_MANAGER
    
    # 初始化数据源管理器
    if DATABASE_AVAILABLE and DATA_SOURCE_MANAGER is None:
        try:
            DATA_SOURCE_MANAGER = DataSourceManager()
            print("✅ 数据源管理器已初始化", flush=True)
        except Exception as e:
            print(f"⚠️ 数据源管理器初始化失败: {e}", flush=True)
            DATA_SOURCE_MANAGER = None
    
    if GLOBAL_DATA is None:
        print("\n" + "="*80, flush=True)
        print("🔄 正在初始化数据...", flush=True)
        print("="*80, flush=True)
        
        GLOBAL_DATA = load_real_business_data()
        
        if GLOBAL_DATA is not None:
            # ========== 🔍 调试日志：初始加载数据检查 ==========
            print("\n" + "="*80, flush=True)
            print("🔍 [调试] GLOBAL_DATA 初始加载完成", flush=True)
            print(f"📊 数据量: {len(GLOBAL_DATA)} 行", flush=True)
            print(f"📋 字段数量: {len(GLOBAL_DATA.columns)} 列", flush=True)
            
            if '商品采购成本' in GLOBAL_DATA.columns:
                print(f"\n✅ '商品采购成本' 字段存在", flush=True)
                print(f"   数据类型: {GLOBAL_DATA['商品采购成本'].dtype}", flush=True)
                print(f"   总和: ¥{GLOBAL_DATA['商品采购成本'].sum():,.2f}", flush=True)
                print(f"   非零数量: {(GLOBAL_DATA['商品采购成本'] > 0).sum()} / {len(GLOBAL_DATA)}", flush=True)
                print(f"   NaN数量: {GLOBAL_DATA['商品采购成本'].isna().sum()}", flush=True)
            else:
                print(f"\n❌ '商品采购成本' 字段不存在！", flush=True)
            print("="*80 + "\n", flush=True)
            
            # ⭐ 关键业务规则1：剔除耗材数据（购物袋等）
            # 识别标准：一级分类名 == '耗材'
            # 参考：订单数据业务逻辑确认.md、业务逻辑最终确认.md
            original_rows = len(GLOBAL_DATA)
            category_col = None
            for col_name in ['一级分类名', '美团一级分类', '一级分类']:
                if col_name in GLOBAL_DATA.columns:
                    category_col = col_name
                    break
            
            if category_col:
                GLOBAL_DATA = GLOBAL_DATA[GLOBAL_DATA[category_col] != '耗材'].copy()
                removed_consumables = original_rows - len(GLOBAL_DATA)
                if removed_consumables > 0:
                    print(f"🔴 已剔除耗材数据: {removed_consumables:,} 行 (购物袋等，一级分类='耗材')", flush=True)
                    print(f"📊 剔除耗材后数据量: {len(GLOBAL_DATA):,} 行", flush=True)
            else:
                print(f"⚠️ 未找到一级分类列，无法剔除耗材数据", flush=True)
            
            # ⭐ 关键业务规则2：剔除咖啡渠道数据（与Streamlit保持一致）
            if '渠道' in GLOBAL_DATA.columns:
                before_count = len(GLOBAL_DATA)
                GLOBAL_DATA = GLOBAL_DATA[~GLOBAL_DATA['渠道'].isin(CHANNELS_TO_REMOVE)].copy()
                removed_count = before_count - len(GLOBAL_DATA)
                if removed_count > 0:
                    print(f"☕ 已剔除咖啡渠道数据: {removed_count:,} 行 (剔除渠道: {CHANNELS_TO_REMOVE})", flush=True)
                    print(f"📊 最终数据量: {len(GLOBAL_DATA):,} 行")
            
            # ⭐ 使用统一的场景推断模块（替代重复代码）
            GLOBAL_DATA = add_scene_and_timeslot_fields(GLOBAL_DATA)
            
            scenes = get_available_scenes(GLOBAL_DATA)
            timeslots = get_available_timeslots(GLOBAL_DATA)
            
            print(f"✅ 已智能生成场景和时段字段")
            print(f"   场景选项: {scenes}")
            print(f"   时段选项: {timeslots}")
            
            # ========== 🎯 商品场景智能打标 (在剔除耗材和咖啡后执行) ==========
            if SMART_TAGGING_AVAILABLE:
                print("\n" + "="*80, flush=True)
                print("🎯 执行商品场景智能打标...", flush=True)
                print("="*80, flush=True)
                try:
                    tagger = ProductSceneTagger()
                    GLOBAL_DATA = tagger.tag_product_scenes(GLOBAL_DATA)
                    print(f"   ✅ 打标完成! 添加了扩展场景维度标签", flush=True)
                    print(f"      - 基础场景: {GLOBAL_DATA['场景'].nunique()} 种", flush=True)
                    if '季节场景' in GLOBAL_DATA.columns:
                        print(f"      - 季节场景: {GLOBAL_DATA['季节场景'].nunique()} 种", flush=True)
                    if '节假日场景' in GLOBAL_DATA.columns:
                        print(f"      - 节假日场景: {GLOBAL_DATA['节假日场景'].nunique()} 种", flush=True)
                    if '购买驱动' in GLOBAL_DATA.columns:
                        print(f"      - 购买驱动: {GLOBAL_DATA['购买驱动'].nunique()} 种", flush=True)
                    print("="*80 + "\n", flush=True)
                except Exception as e:
                    print(f"   ⚠️ 智能打标失败: {e}", flush=True)
                    print("   将继续使用基础场景功能", flush=True)
                    print("="*80 + "\n", flush=True)
            
            # ========== 🔍 调试日志：剔除耗材和咖啡后的数据检查 ==========
            print("\n" + "="*80)
            print("🔍 [调试] 数据剔除完成")
            print(f"📊 最终数据量: {len(GLOBAL_DATA)} 行")
            
            if '商品采购成本' in GLOBAL_DATA.columns:
                print(f"\n✅ '商品采购成本' 字段仍然存在")
                print(f"   总和: ¥{GLOBAL_DATA['商品采购成本'].sum():,.2f}")
                print(f"   非零数量: {(GLOBAL_DATA['商品采购成本'] > 0).sum()} / {len(GLOBAL_DATA)}")
            else:
                print(f"\n❌ '商品采购成本' 字段丢失！")
            print("="*80 + "\n")
            
            print("🔧 正在初始化诊断引擎...")
            DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(GLOBAL_DATA)
            print("✅ 初始化完成！")
        else:
            print("⚠️ 使用示例数据")
            # 创建示例数据
            GLOBAL_DATA = pd.DataFrame({
                '商品名称': [f'商品{i}' for i in range(1, 21)],
                '场景': ['早餐', '午餐', '晚餐', '夜宵', '下午茶'] * 4,
                '时段': ['清晨(6-9点)', '正午(12-14点)', '傍晚(18-21点)', '晚间(21-24点)'] * 5,
                '一级分类名': ['饮料', '零食', '主食', '蔬菜'] * 5,
                '销量变化': [-50, -30, -20, -15, -10, -50, -30, -20, -15, -10, -50, -30, -20, -15, -10, -50, -30, -20, -15, -10],
                '变化幅度%': [-25.0, -15.0, -10.0, -7.5, -5.0, -25.0, -15.0, -10.0, -7.5, -5.0, -25.0, -15.0, -10.0, -7.5, -5.0, -25.0, -15.0, -10.0, -7.5, -5.0],
                '收入变化': [-500, -300, -200, -150, -100, -500, -300, -200, -150, -100, -500, -300, -200, -150, -100, -500, -300, -200, -150, -100],
                '利润变化': [-150, -90, -60, -45, -30, -150, -90, -60, -45, -30, -150, -90, -60, -45, -30, -150, -90, -60, -45, -30],
                '商品实售价': [10, 15, 20, 25, 30, 10, 15, 20, 25, 30, 10, 15, 20, 25, 30, 10, 15, 20, 25, 30]
            })
            DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(GLOBAL_DATA)
    
    return GLOBAL_DATA, DIAGNOSTIC_ENGINE


def initialize_ai_tools():
    """初始化 PandasAI（阶段2）与 RAG 知识库（阶段3）"""
    global PANDAS_AI_ANALYZER, PANDAS_AI_TEMPLATES, VECTOR_KB_INSTANCE, RAG_ANALYZER_INSTANCE

    if PANDAS_AI_MODULE_AVAILABLE and PANDAS_AI_ANALYZER is None:
        try:
            PANDAS_AI_ANALYZER = SmartDataAnalyzer()
            PANDAS_AI_TEMPLATES = dict(QUERY_TEMPLATES)
            print("✅ PandasAI 智能分析器已就绪")
        except Exception as exc:
            PANDAS_AI_ANALYZER = None
            print(f"⚠️ PandasAI 初始化失败: {exc}")
    elif not PANDAS_AI_MODULE_AVAILABLE:
        print("ℹ️ PandasAI 模块不可用，跳过阶段2初始化")

    # 暂时跳过 RAG 模块初始化（避免下载模型）
    if False and RAG_MODULE_AVAILABLE and RAG_ANALYZER_INSTANCE is None:
        try:
            knowledge_dir = APP_DIR / "知识库" / "向量案例库"
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            VECTOR_KB_INSTANCE = VectorKnowledgeBase(str(knowledge_dir))
            stats = VECTOR_KB_INSTANCE.get_stats()
            if stats.get('total_cases', 0) == 0:
                print("ℹ️ 知识库当前为空，自动预填充典型案例…")
                init_default_knowledge_base(VECTOR_KB_INSTANCE)
            api_key = os.getenv('ZHIPU_API_KEY')
            RAG_ANALYZER_INSTANCE = RAGAnalyzer(api_key=api_key, knowledge_base=VECTOR_KB_INSTANCE)
            print("✅ RAG 增强分析器已就绪")
        except Exception as exc:
            RAG_ANALYZER_INSTANCE = None
            print(f"⚠️ RAG 分析器初始化失败: {exc}")
    else:
        print("ℹ️ RAG 模块已跳过，后续可启用")


def get_active_dataframe(data_scope: str, diagnostic_records: Optional[List[Dict[str, Any]]]) -> Optional[pd.DataFrame]:
    """根据用户选择返回副本数据，用于AI分析"""
    if data_scope == 'diagnostic' and diagnostic_records:
        try:
            df = pd.DataFrame(diagnostic_records)
            if not df.empty:
                return df.copy()
        except Exception as exc:
            print(f"⚠️ 将诊断记录转换为DataFrame失败: {exc}")

    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return None
    return GLOBAL_DATA.copy()


def build_business_summary(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """生成业务数据摘要，供RAG分析使用"""
    summary: Dict[str, Any] = {}
    if df is None or df.empty:
        return summary

    revenue_candidates = ['预计订单收入', '订单零售额', '订单实收金额', '实收价格', '商品实售价']
    revenue_col = next((col for col in revenue_candidates if col in df.columns), None)
    order_col = next((col for col in ['订单ID', '订单编号', '订单号'] if col in df.columns), None)

    total_sales = 0.0
    order_count = 0
    if revenue_col and order_col:
        order_sales = df.groupby(order_col)[revenue_col].sum()
        total_sales = float(order_sales.sum())
        order_count = int(order_sales.shape[0])
    elif revenue_col:
        total_sales = float(df[revenue_col].sum())
        order_count = int(df[revenue_col].notna().sum())

    if total_sales:
        summary['GMV(¥)'] = total_sales
    if order_count:
        summary['订单数'] = order_count
        if total_sales:
            summary['客单价(¥)'] = total_sales / max(order_count, 1)

    profit_col = next((col for col in ['实际利润', '利润额', '毛利润'] if col in df.columns), None)
    if profit_col:
        summary['利润总额(¥)'] = float(df[profit_col].sum())
    else:
        cost_cols = [col for col in ['商品采购成本', '物流配送费', '平台佣金', '营销成本', '优惠减免'] if col in df.columns]
        if cost_cols and revenue_col:
            total_cost = float(df[cost_cols].sum(axis=1).sum()) if len(cost_cols) > 1 else float(df[cost_cols[0]].sum())
            summary['成本合计(¥)'] = total_cost
            summary['估算利润(¥)'] = total_sales - total_cost

    if '商品名称' in df.columns:
        summary['SKU数量'] = int(df['商品名称'].nunique())
    if '场景' in df.columns:
        summary['场景数'] = int(df['场景'].nunique())
    if '时段' in df.columns:
        summary['时段数'] = int(df['时段'].nunique())

    if '日期' in df.columns:
        try:
            dates = pd.to_datetime(df['日期'])
            if not dates.isna().all():
                summary['时间范围'] = f"{dates.min():%Y-%m-%d} ~ {dates.max():%Y-%m-%d}"
        except Exception as exc:
            print(f"⚠️ 日期字段解析失败: {exc}")

    return summary


def format_summary_text(summary: Dict[str, Any]) -> str:
    """将摘要字典转为 Markdown 文本"""
    if not summary:
        return ""
    lines: List[str] = []
    for key, value in summary.items():
        if isinstance(value, (int, float)):
            if isinstance(value, int):
                lines.append(f"- {key}: {value:,}")
            else:
                lines.append(f"- {key}: {value:,.2f}")
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)

# 初始化数据
initialize_data()
initialize_ai_tools()

# 🔍 调试: 打印DATABASE_AVAILABLE状态
print(f"\n{'='*80}")
print(f"🔍 [UI渲染前检查] DATABASE_AVAILABLE = {DATABASE_AVAILABLE}")
print(f"🔍 [UI渲染前检查] DATA_SOURCE_MANAGER = {DATA_SOURCE_MANAGER}")
print(f"🔍 [UI渲染前检查] Tab将被{'启用' if DATABASE_AVAILABLE else '禁用(灰色)'}")
print(f"{'='*80}\n")

PANDAS_STATUS_TEXT = "可用" if PANDAS_AI_ANALYZER else ("待安装" if PANDAS_AI_MODULE_AVAILABLE else "未安装")
PANDAS_STATUS_COLOR = "success" if PANDAS_AI_ANALYZER else ("warning" if PANDAS_AI_MODULE_AVAILABLE else "secondary")
RAG_STATUS_TEXT = "可用" if RAG_ANALYZER_INSTANCE else ("待安装" if RAG_MODULE_AVAILABLE else "未安装")
RAG_STATUS_COLOR = "success" if RAG_ANALYZER_INSTANCE else ("warning" if RAG_MODULE_AVAILABLE else "secondary")
KB_STATS_TEXT = ""
if VECTOR_KB_INSTANCE:
    try:
        _kb_stats = VECTOR_KB_INSTANCE.get_stats()
        KB_STATS_TEXT = f"案例数: {_kb_stats.get('total_cases', 0)} | 标签数: {len(_kb_stats.get('tag_distribution', {}))}"
    except Exception as exc:
        KB_STATS_TEXT = f"知识库统计读取失败: {exc}"
else:
    KB_STATS_TEXT = "知识库未初始化"

# 自定义CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>智能门店经营看板 - Dash版</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                background-color: #f8f9fa;
                scroll-behavior: smooth;
            }
            html {
                scroll-behavior: smooth;
            }
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            .stat-card {
                text-align: center;
                padding: 15px;
            }
            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                font-size: 13px;
                color: #6c757d;
                margin-top: 5px;
            }
            /* 防止图表容器引起的自动滚动 */
            .js-plotly-plot {
                overflow: visible !important;
            }
            
            /* 日历选择器中文星期显示 */
            .DateInput_input {
                font-size: 14px;
                padding: 8px 12px;
            }
            
            /* 自定义星期标题为中文 */
            .CalendarMonth_caption {
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 10px;
            }
            
            /* 🔧 修复: 星期标题样式优化，避免和日期重叠 */
            .DayPicker_weekHeader {
                position: relative;
                top: 0;
                padding-bottom: 15px !important;  /* 进一步增加底部间距 */
                margin-bottom: 10px !important;   /* 进一步增加下边距 */
            }
            
            .DayPicker_weekHeader_ul {
                margin-bottom: 15px !important;  /* 进一步增加列表底部间距 */
                padding-bottom: 5px !important;  /* 额外内边距 */
            }
            
            .DayPicker_weekHeader_li {
                padding: 10px 0 !important;  /* 进一步增加上下内边距 */
                margin-bottom: 5px !important;  /* 额外底部边距 */
            }
            
            /* 隐藏原始英文星期文本 */
            .DayPicker_weekHeader small {
                font-size: 0 !important;  /* 隐藏原始英文文本 */
                visibility: hidden;
                display: inline-block;
                height: 20px;  /* 固定高度 */
            }
            
            /* 使用CSS伪元素添加中文星期（周一开始） */
            .DayPicker_weekHeader_li:nth-child(1) small:before { 
                font-size: 15px;
                font-weight: 600;
                content: "一"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(2) small:before { 
                font-size: 15px;
                font-weight: 600;
                content: "二"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(3) small:before { 
                font-size: 15px;
                font-weight: 600;
                content: "三"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(4) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "四"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(5) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "五"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(6) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "六"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(7) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "日"; 
                visibility: visible;
                display: inline-block;
                color: #d32f2f;  /* 周日用红色 */
            }
            
            /* 🔧 增加日历日期单元格的间距 */
            .CalendarDay {
                padding: 8px 0 !important;  /* 增加日期单元格内边距 */
                line-height: 1.5 !important;
            }
            
            /* 🔧 优化日历整体布局 */
            .DayPicker {
                padding-top: 12px !important;  /* 增加顶部内边距 */
            }
            
            .DayPicker_weekHeaders {
                margin-bottom: 20px !important;  /* 进一步增加星期标题和日期之间的间距 */
            }
            
            /* 🔧 日历日期容器额外间距 */
            .DayPicker_transitionContainer {
                padding-top: 10px !important;
            }
            
            /* 🆕 单日选择模式：完全隐藏结束日期输入框和箭头 */
            .single-day-picker .DateInput:last-child,
            .single-day-picker .DateRangePickerInput_arrow {
                display: none !important;  /* 完全隐藏结束日期和箭头 */
            }
            
            /* 🆕 单日选择模式：优化开始日期输入框样式 */
            .single-day-picker .DateInput:first-child {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            .single-day-picker .DateInput:first-child .DateInput_input {
                width: 100% !important;
                text-align: center;  /* 居中显示日期 */
                font-weight: 500;
            }
            
            /* 优化日期选择器的整体布局 */
            .DateRangePickerInput {
                display: flex;
                align-items: center;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 0.375rem 0.75rem;
            }
            
            .DateRangePickerInput_arrow {
                padding: 0 8px;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <script>
            // 强制触发周期选择器回调
            window.addEventListener('load', function() {
                console.log('🔄 页面加载完成，准备触发回调...');
                setTimeout(function() {
                    // 找到对比模式选择器
                    var selector = document.querySelector('#time-period-selector');
                    if (selector) {
                        console.log('✅ 找到选择器，当前值:', selector.value);
                        // 强制触发change事件
                        var event = new Event('change', { bubbles: true });
                        selector.dispatchEvent(event);
                        console.log('🚀 已触发change事件');
                    } else {
                        console.error('❌ 未找到选择器 #time-period-selector');
                    }
                }, 2000); // 等待2秒确保Dash初始化完成
                
                // 🆕 单日选择模式：自动同步开始和结束日期
                // 监听日期选择器的变化
                setTimeout(function() {
                    console.log('📅 初始化单日选择模式监听器...');
                    
                    // 获取所有日期选择器输入框
                    var dateInputs = document.querySelectorAll('input[id*="date-range"]');
                    
                    dateInputs.forEach(function(input) {
                        // 监听日期变化
                        input.addEventListener('change', function(e) {
                            var inputId = e.target.id;
                            
                            // 检查是否是开始日期输入框
                            if (inputId && inputId.includes('start')) {
                                console.log('📅 开始日期被选择:', e.target.value);
                                
                                // 找到对应的结束日期输入框
                                var endInputId = inputId.replace('start', 'end');
                                var endInput = document.getElementById(endInputId);
                                
                                if (endInput && e.target.value) {
                                    // 自动将结束日期设置为开始日期
                                    endInput.value = e.target.value;
                                    console.log('✅ 已自动同步结束日期:', e.target.value);
                                    
                                    // 触发change事件，通知Dash
                                    var changeEvent = new Event('change', { bubbles: true });
                                    endInput.dispatchEvent(changeEvent);
                                }
                            }
                        });
                    });
                    
                    console.log('✅ 单日选择模式已启用');
                }, 2500);
                
                // CSS已经优化了布局，移除其他JavaScript操作以提升性能
            });
        </script>
    </body>
</html>
'''

# ==================== 全局数据信息组件 ====================
def create_data_info_card():
    """创建全局数据信息卡片（显示在所有Tab顶部）"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # 数据状态指示器
                dbc.Col([
                    html.Div([
                        html.I(className="bi bi-database-check me-2", 
                               style={'fontSize': '1.2rem', 'color': '#28a745'}),
                        html.Span("数据已加载", id='data-status-text', 
                                 className="fw-bold", style={'color': '#28a745'})
                    ], className="d-flex align-items-center")
                ], width=2),
                
                # 数据文件名
                dbc.Col([
                    html.Small("📁 数据文件:", className="text-muted me-2"),
                    html.Span(id='data-filename', children="加载中...", className="fw-bold")
                ], width=3),
                
                # 数据时间范围
                dbc.Col([
                    html.Small("📅 时间范围:", className="text-muted me-2"),
                    html.Span(id='data-date-range', children="计算中...", className="fw-bold")
                ], width=3),
                
                # 数据量统计
                dbc.Col([
                    html.Small("📊 数据量:", className="text-muted me-2"),
                    html.Span(id='data-record-count', children="统计中...", className="fw-bold")
                ], width=2),
                
                # 最后更新时间
                dbc.Col([
                    html.Small("🕐 更新时间:", className="text-muted me-2"),
                    html.Span(id='data-update-time', children="--", className="text-muted small")
                ], width=2)
            ], align="center")
        ])
    ], className="mb-3", style={
        'borderLeft': '4px solid #28a745',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
    })


# ==================== 健康度预警组件(基于业务逻辑) ====================
def _create_health_warnings(total_sales: float, total_profit: float, order_agg: pd.DataFrame) -> list:
    """
    创建健康度预警组件
    
    Args:
        total_sales: 总销售额
        total_profit: 总利润
        order_agg: 订单聚合数据
    
    Returns:
        健康度预警组件列表
    """
    if not BUSINESS_CONTEXT_AVAILABLE:
        return []
    
    # 计算核心指标
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    # 计算成本占比
    product_cost = order_agg['商品采购成本'].sum() if '商品采购成本' in order_agg.columns else 0
    logistics_cost = order_agg['物流配送费'].sum() if '物流配送费' in order_agg.columns else 0
    platform_cost = order_agg['平台佣金'].sum() if '平台佣金' in order_agg.columns else 0
    marketing_cost = order_agg['商家活动成本'].sum() if '商家活动成本' in order_agg.columns else 0
    
    product_cost_rate = (product_cost / total_sales * 100) if total_sales > 0 else 0
    logistics_cost_rate = (logistics_cost / total_sales * 100) if total_sales > 0 else 0
    platform_cost_rate = (platform_cost / total_sales * 100) if total_sales > 0 else 0
    marketing_cost_rate = (marketing_cost / total_sales * 100) if total_sales > 0 else 0
    
    # ✨ 新增: 计算商品角色占比(基于毛利率的简单分类)
    # 从GLOBAL_DATA获取商品级数据来分类
    try:
        if GLOBAL_DATA is not None and '商品名称' in GLOBAL_DATA.columns:
            df = GLOBAL_DATA.copy()
            
            # 计算每个商品的毛利率
            if '商品实售价' in df.columns and '商品采购成本' in df.columns:
                # 按商品聚合
                product_stats = df.groupby('商品名称').agg({
                    '商品实售价': 'sum',
                    '商品采购成本': 'sum',
                    '月售': 'sum'
                }).reset_index()
                
                # 计算毛利率
                product_stats['毛利率'] = (
                    (product_stats['商品实售价'] - product_stats['商品采购成本']) / 
                    product_stats['商品实售价'] * 100
                ).fillna(0)
                
                # 商品角色分类(基于业务规则)
                # 流量品: 毛利率<15%
                # 利润品: 毛利率>30%
                # 形象品: 15% <= 毛利率 <= 30%
                total_products = len(product_stats)
                流量品数 = len(product_stats[product_stats['毛利率'] < 15])
                利润品数 = len(product_stats[product_stats['毛利率'] > 30])
                形象品数 = len(product_stats[(product_stats['毛利率'] >= 15) & (product_stats['毛利率'] <= 30)])
                
                流量品占比 = (流量品数 / total_products * 100) if total_products > 0 else 0
                利润品占比 = (利润品数 / total_products * 100) if total_products > 0 else 0
                形象品占比 = (形象品数 / total_products * 100) if total_products > 0 else 0
                
                # 🔍 调试日志
                print(f"\n{'='*80}")
                print(f"📊 商品角色分类统计")
                print(f"{'='*80}")
                print(f"总商品数: {total_products}")
                print(f"流量品: {流量品数} 个 ({流量品占比:.1f}%) - 毛利率<15%")
                print(f"利润品: {利润品数} 个 ({利润品占比:.1f}%) - 毛利率>30%")
                print(f"形象品: {形象品数} 个 ({形象品占比:.1f}%) - 毛利率15-30%")
                print(f"{'='*80}\n")
            else:
                流量品占比 = 0
                利润品占比 = 0
                形象品占比 = 0
        else:
            流量品占比 = 0
            利润品占比 = 0
            形象品占比 = 0
    except Exception as e:
        print(f"⚠️ 商品角色分类计算失败: {e}")
        流量品占比 = 0
        利润品占比 = 0
        形象品占比 = 0
    
    # 构建指标字典(包含商品角色占比)
    metrics = {
        '利润率': profit_rate,
        '商品成本占比': product_cost_rate,
        '履约成本占比': logistics_cost_rate,
        '平台成本占比': platform_cost_rate,
        '营销成本占比': marketing_cost_rate,
        '流量品占比': 流量品占比,
        '利润品占比': 利润品占比,
        '形象品占比': 形象品占比
    }
    
    # 调用业务上下文模块获取预警
    try:
        warnings = get_health_warnings(metrics)
    except Exception as e:
        print(f"⚠️ 健康度预警计算失败: {e}")
        warnings = []
    
    # 如果无预警,返回健康状态卡片
    if not warnings:
        return [dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2", style={'fontSize': '1.2rem'}),
            html.Strong("✅ 经营健康度良好"),
            html.Br(),
            html.Small(f"利润率 {profit_rate:.1f}% 处于健康范围 (8-15%)", className="text-muted")
        ], color="success", className="mb-4")]
    
    # 有预警时,生成预警卡片
    warning_cards = []
    
    # 预警标题
    warning_cards.append(dbc.Alert([
        html.I(className="bi bi-exclamation-triangle-fill me-2", style={'fontSize': '1.3rem'}),
        html.Strong(f"⚠️ 发现 {len(warnings)} 项经营风险", style={'fontSize': '1.1rem'}),
        html.Br(),
        html.Small("请立即关注以下指标异常,采取措施恢复健康状态", className="mt-2")
    ], color="warning", className="mb-3"))
    
    # 预警详情
    for idx, warning in enumerate(warnings, 1):
        # ✨ 修复: 使用正确的键名映射(来自ai_business_context.py)
        severity = warning.get('级别', '警告')
        indicator = warning.get('指标', '未知指标')
        current_value = warning.get('当前值', 'N/A')
        threshold = warning.get('阈值', 'N/A')
        problem = warning.get('问题', '未知问题')
        suggestion = warning.get('建议', '请咨询运营专家')
        
        severity_color = {
            '严重': 'danger',
            '警告': 'warning',
            '提示': 'info'
        }.get(severity, 'warning')
        
        severity_icon = {
            '严重': 'bi-x-circle-fill',
            '警告': 'bi-exclamation-triangle-fill',
            '提示': 'bi-info-circle-fill'
        }.get(severity, 'bi-exclamation-triangle-fill')
        
        warning_cards.append(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {severity_icon} me-2", style={'fontSize': '1.1rem'}),
                    html.Strong(f"{idx}. {indicator}", style={'fontSize': '1rem'})
                ], className="mb-2"),
                html.Div([
                    html.Span("当前: ", className="text-muted small me-1"),
                    html.Span(current_value, className="text-danger fw-bold small me-3"),
                    html.Span("基准: ", className="text-muted small me-1"),
                    html.Span(threshold, className="text-success small")
                ], className="mb-2"),
                html.P(problem, className="mb-2 text-muted small"),
                html.Div([
                    html.Strong("💡 建议: ", className="me-1"),
                    html.Span(suggestion, className="small")
                ])
            ])
        ], color=severity_color, outline=True, className="mb-2"))
    
    return warning_cards


# ==================== 成本优化分析核心函数 ====================
def analyze_cost_optimization(df_raw: pd.DataFrame, order_agg: pd.DataFrame) -> Dict[str, Any]:
    """
    成本优化分析：针对3项成本预警提供深度分析
    
    Args:
        df_raw: 原始订单数据（包含商品名称等字段）
        order_agg: 订单聚合数据（用于计算总体指标）
        
    Returns:
        包含成本分析结果的字典
    """
    if df_raw is None or len(df_raw) == 0:
        return {
            'product_cost_analysis': None,
            'logistics_cost_analysis': None,
            'marketing_cost_analysis': None
        }
    
    df = df_raw.copy()
    
    # ========== 1. 商品成本分析 ==========
    product_cost_analysis = {}
    
    # 按商品聚合
    product_stats = df.groupby('商品名称').agg({
        '商品实售价': 'sum',
        '商品采购成本': 'sum',
        '月售': 'sum'
    }).reset_index()
    
    # 计算毛利率和成本占比
    product_stats['毛利率'] = (
        (product_stats['商品实售价'] - product_stats['商品采购成本']) / 
        product_stats['商品实售价'] * 100
    )
    product_stats['成本占比'] = (
        product_stats['商品采购成本'] / product_stats['商品实售价'] * 100
    )
    
    # 识别高成本低毛利商品（成本占比>70%且销量较高）
    high_cost_products = product_stats[
        (product_stats['成本占比'] > 70) & 
        (product_stats['月售'] > product_stats['月售'].quantile(0.5))
    ].sort_values('商品实售价', ascending=False).head(20)
    
    product_cost_analysis['high_cost_products'] = high_cost_products
    product_cost_analysis['avg_cost_rate'] = product_stats['成本占比'].mean()
    product_cost_analysis['total_products'] = len(product_stats)
    product_cost_analysis['problem_products'] = len(high_cost_products)
    
    # ========== 2. 履约成本分析 ==========
    logistics_cost_analysis = {}
    
    # 计算履约成本相关指标
    total_sales = df['商品实售价'].sum()
    
    # 计算履约净成本: 用户支付配送费 - 配送费减免 - 物流配送费
    # 如果字段缺失,则使用物流配送费作为近似值
    has_full_data = all(field in df.columns for field in ['用户支付配送费', '配送费减免金额', '物流配送费'])
    
    if has_full_data:
        # 完整公式: 净成本 = 收入 - 支出
        total_logistics = (
            df['用户支付配送费'].sum() - 
            df['配送费减免金额'].sum() - 
            df['物流配送费'].sum()
        )
        logistics_cost_field = '物流配送费'  # 用于后续分组分析
    else:
        # 降级: 仅使用物流配送费
        logistics_cost_field = None
        for field in ['物流配送费', '配送成本', '物流成本']:
            if field in df.columns:
                logistics_cost_field = field
                break
        total_logistics = df[logistics_cost_field].sum() if logistics_cost_field else 0
    
    # 按配送距离分析
    if '配送距离' in df.columns and logistics_cost_field:
        df['距离分组'] = pd.cut(
            df['配送距离'], 
            bins=[0, 1, 3, 5, 10, 100],
            labels=['<1km', '1-3km', '3-5km', '5-10km', '>10km']
        )
        
        # 计算每个距离段的配送净成本
        if has_full_data:
            # 使用完整公式
            agg_dict = {
                '用户支付配送费': 'sum',
                '配送费减免金额': 'sum',
                '物流配送费': 'sum',
                '商品实售价': 'sum',
                '订单ID': 'count'
            }
            distance_stats = df.groupby('距离分组').agg(agg_dict).reset_index()
            # 计算净成本
            distance_stats['配送成本'] = (
                distance_stats['用户支付配送费'] - 
                distance_stats['配送费减免金额'] - 
                distance_stats['物流配送费']
            )
            distance_stats['销售额'] = distance_stats['商品实售价']
            distance_stats['订单数'] = distance_stats['订单ID']
        else:
            # 降级: 仅使用物流配送费
            distance_stats = df.groupby('距离分组').agg({
                logistics_cost_field: 'sum',
                '商品实售价': 'sum',
                '订单ID': 'count'
            }).reset_index()
            distance_stats.columns = ['距离分组', '配送成本', '销售额', '订单数']
        
        distance_stats['成本占比'] = (
            distance_stats['配送成本'] / distance_stats['销售额'] * 100
        )
        distance_stats['平均客单价'] = distance_stats['销售额'] / distance_stats['订单数']
        
        logistics_cost_analysis['distance_stats'] = distance_stats[
            ['距离分组', '配送成本', '销售额', '订单数', '成本占比', '平均客单价']
        ]
    else:
        logistics_cost_analysis['distance_stats'] = None
    
    logistics_cost_analysis['total_logistics_cost'] = total_logistics
    logistics_cost_analysis['logistics_cost_rate'] = (total_logistics / total_sales * 100) if total_sales > 0 else 0
    logistics_cost_analysis['has_logistics_data'] = logistics_cost_field is not None
    logistics_cost_analysis['use_full_formula'] = has_full_data  # 标识是否使用完整公式
    
    # ========== 3. 营销成本分析 ==========
    marketing_cost_analysis = {}
    
    # 计算各类营销成本
    total_marketing = 0
    marketing_breakdown = {}
    
    if '满减' in df.columns:
        manjian = df['满减'].sum()
        total_marketing += manjian
        marketing_breakdown['满减'] = manjian
    
    if '商品减免' in df.columns:
        goods_discount = df['商品减免'].sum()
        total_marketing += goods_discount
        marketing_breakdown['商品减免'] = goods_discount
    
    if '代金券' in df.columns:
        voucher = df['代金券'].sum()
        total_marketing += voucher
        marketing_breakdown['代金券'] = voucher
    
    if '配送费减免' in df.columns:
        delivery_discount = df['配送费减免'].sum()
        total_marketing += delivery_discount
        marketing_breakdown['配送费减免'] = delivery_discount
    
    # 计算营销ROI（销售额 / 营销成本）
    marketing_roi = (total_sales / total_marketing) if total_marketing > 0 else 0
    
    marketing_cost_analysis['total_marketing_cost'] = total_marketing
    marketing_cost_analysis['marketing_cost_rate'] = (total_marketing / total_sales * 100) if total_sales > 0 else 0
    marketing_cost_analysis['marketing_roi'] = marketing_roi
    marketing_cost_analysis['marketing_breakdown'] = marketing_breakdown
    
    # 按渠道分析营销效率
    if '渠道' in df.columns:
        # 构建聚合字典,只包含存在的字段
        agg_dict = {'商品实售价': 'sum', '订单ID': 'count'}
        
        # 添加存在的营销字段
        marketing_fields = []
        if '满减' in df.columns:
            agg_dict['满减'] = 'sum'
            marketing_fields.append('满减')
        if '商品减免' in df.columns:
            agg_dict['商品减免'] = 'sum'
            marketing_fields.append('商品减免')
        if '代金券' in df.columns:
            agg_dict['代金券'] = 'sum'
            marketing_fields.append('代金券')
        
        if marketing_fields:  # 只有有营销字段时才分析
            channel_stats = df.groupby('渠道').agg(agg_dict).reset_index()
            
            # 计算营销成本总和
            channel_stats['营销成本'] = channel_stats[marketing_fields].sum(axis=1)
            channel_stats['营销成本占比'] = (
                channel_stats['营销成本'] / channel_stats['商品实售价'] * 100
            )
            channel_stats['营销ROI'] = (
                channel_stats['商品实售价'] / channel_stats['营销成本']
            ).replace([np.inf, -np.inf], 0)
            
            marketing_cost_analysis['channel_stats'] = channel_stats
        else:
            marketing_cost_analysis['channel_stats'] = None
    else:
        marketing_cost_analysis['channel_stats'] = None
    
    return {
        'product_cost_analysis': product_cost_analysis,
        'logistics_cost_analysis': logistics_cost_analysis,
        'marketing_cost_analysis': marketing_cost_analysis
    }


# ==================== 页面布局 ====================
app.layout = dbc.Container([
    # URL 路由组件（用于页面加载检测）
    dcc.Location(id='url', refresh=False),
    
    # 隐藏的数据更新触发器
    dcc.Store(id='data-update-trigger', data=0),
    dcc.Store(id='data-metadata', data={}),  # 存储数据元信息
    dcc.Store(id='page-init-trigger', data={'loaded': False}),  # 页面初始化触发器
    dcc.Store(id='pandasai-history-store', data=[]),
    dcc.Store(id='rag-auto-summary-store', data={}),
    
    # 头部
    html.Div([
        html.H1("🏪 智能门店经营看板", style={'margin': 0, 'fontSize': '2.5rem'}),
        html.P("Dash版 - 流畅交互，无页面跳转", 
               style={'margin': '10px 0 0 0', 'opacity': 0.9, 'fontSize': '1.1rem'})
    ], className='main-header'),
    
    # 全局数据信息卡片
    html.Div(id='global-data-info-card'),
    
    # ========== 数据源选择区域 ==========
    dbc.Card([
        dbc.CardHeader([
            html.H4("📂 数据源选择", className="mb-0 d-inline-block"),
            html.Span(" | 当前数据: ", className="ms-3 text-muted small"),
            html.Span(id='current-data-label', children="默认数据", className="text-primary small fw-bold")
        ]),
        dbc.CardBody([
            dcc.Tabs(id='data-source-tabs', value='default-data', children=[
                # Tab 1: 使用默认数据
                dcc.Tab(label='📊 使用默认数据', value='default-data', children=[
                    html.Div([
                        dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            "当前使用系统默认数据（门店数据/订单数据-本店.xlsx）"
                        ], color="info", className="mb-0 mt-3")
                    ])
                ]),
                
                # Tab 1.5: 从数据库加载
                dcc.Tab(label='🗄️ 数据库数据', value='database-data', 
                        disabled=not DATABASE_AVAILABLE,  # DEBUG: DATABASE_AVAILABLE = {DATABASE_AVAILABLE}
                        children=[
                    html.Div([
                        dbc.Alert([
                            html.I(className="bi bi-database me-2"),
                            "从PostgreSQL数据库加载订单数据"
                        ], color="primary", className="mb-3 mt-3"),
                        
                        # 数据库过滤器
                        dbc.Row([
                            dbc.Col([
                                html.Label("🏪 选择门店:"),
                                dcc.Dropdown(
                                    id='db-store-filter',
                                    placeholder='全部门店',
                                    clearable=True
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("📅 起始日期:"),
                                dcc.DatePickerSingle(
                                    id='db-start-date',
                                    placeholder='起始日期（可选）',
                                    display_format='YYYY-MM-DD'
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("📅 结束日期:"),
                                dcc.DatePickerSingle(
                                    id='db-end-date',
                                    placeholder='结束日期（可选）',
                                    display_format='YYYY-MM-DD'
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label(html.Br()),
                                dbc.Button(
                                    [html.I(className="bi bi-download me-1"), "加载数据"],
                                    id='load-from-database-btn',
                                    color="primary",
                                    className="w-100"
                                )
                            ], md=2)
                        ], className="mb-3"),
                        
                        # 数据库统计信息
                        html.Div(id='database-stats'),
                        
                        # 加载状态
                        html.Div(id='database-load-status', className="mt-3")
                    ], className="p-3")
                ] if DATABASE_AVAILABLE else [html.Div([
                    dbc.Alert([
                        html.I(className="bi bi-exclamation-triangle me-2"),
                        "数据库功能未启用。请安装必要的依赖： pip install psycopg2-binary sqlalchemy"
                    ], color="warning", className="mt-3")
                ])]),
                
                # Tab 2: 上传新数据
                dcc.Tab(label='📤 上传新数据', value='upload-data', children=[
                    html.Div([
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                html.I(className="bi bi-cloud-upload", style={'fontSize': '3rem', 'color': '#667eea'}),
                                html.Br(),
                                html.B('拖拽文件到这里 或 点击选择文件', style={'fontSize': '1.1rem', 'marginTop': '10px'}),
                                html.Br(),
                                html.Span('支持 .xlsx / .xls 格式，可同时上传多个文件', 
                                         style={'fontSize': '0.9rem', 'color': '#666', 'marginTop': '5px'})
                            ]),
                            style={
                                'width': '100%',
                                'height': '150px',
                                'lineHeight': '150px',
                                'borderWidth': '2px',
                                'borderStyle': 'dashed',
                                'borderRadius': '10px',
                                'borderColor': '#667eea',
                                'textAlign': 'center',
                                'background': '#f8f9ff',
                                'cursor': 'pointer',
                                'transition': 'all 0.3s'
                            },
                            multiple=True  # 支持多文件上传
                        ),
                        html.Div(id='upload-status', className="mt-3"),
                        html.Div(id='upload-debug-info', className="text-muted small mt-2"),
                        
                        # 文件格式说明
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.Div([
                                    html.H6("📋 必需字段：", className="mb-2"),
                                    html.Ul([
                                        html.Li("订单ID: 订单唯一标识"),
                                        html.Li("商品名称: 商品名称"),
                                        html.Li("商品实售价: 商品售价"),
                                        html.Li("销量: 商品数量"),
                                        html.Li("下单时间: 订单时间"),
                                        html.Li("门店名称: 门店标识"),
                                        html.Li("渠道: 销售渠道（如美团、饿了么）"),
                                    ]),
                                    html.H6("✨ 推荐字段（用于完整分析）：", className="mb-2 mt-3"),
                                    html.Ul([
                                        html.Li("物流配送费、平台佣金、配送距离"),
                                        html.Li("美团一级分类、美团三级分类"),
                                        html.Li("收货地址、配送费减免、满减、商品减免、代金券"),
                                        html.Li("用户支付配送费、订单零售额、打包费"),
                                    ])
                                ])
                            ], title="📋 订单数据格式要求")
                        ], start_collapsed=True, className="mt-3")
                    ], className="p-3")
                ]),
                
                # Tab 3: 加载历史数据
                dcc.Tab(label='📂 加载历史数据', value='history-data', children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.H5([html.I(className="bi bi-clock-history me-2"), "历史数据管理"], className="mb-0")
                            ], md=6),
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="bi bi-trash3 me-1"), "清理重复缓存"],
                                    id='clean-duplicate-cache-btn',
                                    color="warning",
                                    size="sm",
                                    outline=True,
                                    className="float-end"
                                )
                            ], md=6)
                        ], className="mb-3"),
                        html.Div(id='clean-cache-result'),
                        html.Div(id='history-data-list', className="mt-3"),
                        dcc.Store(id='selected-history-path')  # 存储选中的历史数据路径
                    ], className="p-3")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # 主内容区 - 使用顶层Tabs组织所有功能模块
    dbc.Row([
        dbc.Col([
            # 使用提示
            dbc.Alert([
                html.H5("👋 欢迎使用智能门店经营看板！", className="mb-2"),
                html.P("👇 选择功能模块开始数据分析", className="mb-0")
            ], color="info", className="mb-4"),
            
            # 顶层功能Tabs
            dcc.Tabs(id='main-tabs', value='tab-1', children=[
                
                # ========== Tab 1: 订单数据概览 ==========
                dcc.Tab(label='📊 订单数据概览', value='tab-1', children=[
                    html.Div(id='tab-1-content', className="p-3")
                ]),
                
                # ========== Tab 2: 商品分析 ==========
                dcc.Tab(label='📦 商品分析', value='tab-2', children=[
                    html.Div(id='tab-2-content', className="p-3")
                ]),
                
                # ========== Tab 3: 价格对比分析 ==========
                dcc.Tab(label='💰 价格对比分析', value='tab-3', children=[
                    html.Div(id='tab-3-content', className="p-3")
                ]),
                
                # ========== Tab 3.5: 成本优化分析 ==========
                dcc.Tab(label='💡 成本优化分析', value='tab-cost-optimization', children=[
                    html.Div(id='tab-cost-content', className="p-3")
                ]),
                
                # ========== Tab 4: AI智能助手 ==========
                dcc.Tab(label='🤖 AI智能助手', value='tab-4', children=[
                    html.Div([
                        # 数据信息占位符（由全局回调更新）
                        html.Div(id='tab4-data-info', className="mb-3"),
                        
                        # ========== AI智能助手（阶段2/阶段3）==========
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("🤖 AI智能助手", className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    # 左侧：PandasAI 自然语言分析（阶段2）
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardHeader([
                                                html.H5([
                                                    html.I(className="bi bi-chat-dots me-2"),
                                                    "阶段2: PandasAI 自然语言分析"
                                                ], className="mb-0"),
                                                dbc.Badge(PANDAS_STATUS_TEXT, color=PANDAS_STATUS_COLOR, className="ms-2")
                                            ]),
                                            dbc.CardBody([
                                                # 数据范围选择
                                                html.Div([
                                                    html.Label("📊 数据范围", className="fw-bold mb-2"),
                                                    dcc.RadioItems(
                                                        id='ai-data-scope',
                                                        options=[
                                                            {'label': ' 全部数据', 'value': 'all'},
                                                            {'label': ' 当前诊断结果', 'value': 'diagnostic'}
                                                        ],
                                                        value='all',
                                                        inline=True,
                                                        className="mb-3",
                                                        labelStyle={'margin-right': '20px'}
                                                    )
                                                ]),
                                                
                                                # 模板查询选择
                                                html.Div([
                                                    html.Label("🎯 快速模板", className="fw-bold mb-2"),
                                                    dcc.Dropdown(
                                                        id='pandasai-template-selector',
                                                        options=[],  # 从PANDAS_AI_TEMPLATES动态加载
                                                        placeholder="选择预设查询模板...",
                                                        style={'fontSize': '14px'},
                                                        className="mb-2"
                                                    )
                                                ]),
                                                
                                                # 自定义查询输入
                                                html.Div([
                                                    html.Label("💬 自定义问题", className="fw-bold mb-2"),
                                                    dbc.Textarea(
                                                        id='pandasai-query-input',
                                                        placeholder="用自然语言描述你想了解的数据问题，例如：\n- 哪些商品的毛利率最高？\n- 低客单价订单有哪些？\n- 哪些商品滞销了？",
                                                        style={'minHeight': '100px', 'fontSize': '14px'},
                                                        className="mb-3"
                                                    )
                                                ]),
                                                
                                                # 执行按钮
                                                dbc.Button(
                                                    [html.I(className="bi bi-send-fill me-2"), "执行查询"],
                                                    id='pandasai-run-button',
                                                    color='success',
                                                    disabled=not PANDAS_AI_ANALYZER,
                                                    className='w-100 mb-3'
                                                ),
                                                
                                                # 结果展示
                                                html.Div(id='pandasai-run-status', className="text-muted small mt-2"),
                                                dcc.Loading(html.Div(id='pandasai-result'), className="mt-3")
                                            ])
                                        ], className="h-100")
                                    ], md=6),
                                    
                                    # 右侧：RAG 历史案例检索（阶段3）
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardHeader([
                                                html.H5([
                                                    html.I(className="bi bi-book me-2"),
                                                    "阶段3: RAG 历史案例检索"
                                                ], className="mb-0"),
                                                dbc.Badge(RAG_STATUS_TEXT, color=RAG_STATUS_COLOR, className="ms-2")
                                            ]),
                                            dbc.CardBody([
                                                # 问题描述
                                                html.Div([
                                                    html.Label("🔍 问题描述", className="fw-bold mb-2"),
                                                    dbc.Textarea(
                                                        id='rag-query-input',
                                                        placeholder="描述当前业务问题，系统将检索相似历史案例并给出建议...\n例如：销量下滑如何应对？",
                                                        style={'minHeight': '120px', 'fontSize': '14px'},
                                                        className="mb-3"
                                                    )
                                                ]),
                                                
                                                # 执行按钮
                                                dbc.Button(
                                                    [html.I(className="bi bi-search me-2"), "搜索案例"],
                                                    id='rag-run-button',
                                                    color='info',
                                                    disabled=not RAG_ANALYZER_INSTANCE,
                                                    className='w-100 mb-3'
                                                ),
                                                
                                                # 结果展示
                                                html.Div(id='rag-run-status', className="text-muted small mt-2"),
                                                dcc.Loading(dcc.Markdown(id='rag-analysis-output'), className="mt-3"),
                                                html.Hr(),
                                                html.Div([
                                                    html.Span("知识库概览：", className="fw-bold"),
                                                    html.Span(KB_STATS_TEXT, className="ms-2 text-muted")
                                                ], className="small")
                                            ])
                                        ], className="h-100")
                                    ], md=6)
                                ], className="gy-4")
                            ])
                        ], className="mt-3")
                    ], className="p-3")
                ]),

                # ========== Tab 5: 时段场景分析 ==========
                dcc.Tab(label='⏰ 时段场景分析', value='tab-5', children=[
                    html.Div(id='tab-5-content', className="p-3")
                ]),
                
                # ========== Tab 6: 成本利润分析 ==========
                dcc.Tab(label='💵 成本利润分析', value='tab-6', children=[
                    html.Div(id='tab-6-content', className="p-3")
                ]),
                
                # ========== Tab 7: 高级功能 ==========
                dcc.Tab(label='⚙️ 高级功能', value='tab-7', children=[
                    html.Div(id='tab-7-content', className="p-3")
                ])
                
            ])  # main-tabs结束（顶层Tabs）
            
        ], width=12)
    ]),
    
    # 商品详情Modal弹窗（Tab 4.1使用）
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("📦 商品详细信息", id='modal-product-title')),
        dbc.ModalBody([
            dbc.Row([
                # 左侧：商品基础信息
                dbc.Col([
                    html.H5("📋 基础信息", className="mb-3"),
                    html.Div(id='product-basic-info')
                ], md=6),
                # 右侧：对比数据
                dbc.Col([
                    html.H5("📊 周期对比数据", className="mb-3"),
                    html.Div(id='product-comparison-data')
                ], md=6)
            ], className="mb-4"),
            # 历史趋势图
            dbc.Row([
                dbc.Col([
                    html.H5("📈 销量趋势", className="mb-3"),
                    dcc.Loading(dcc.Graph(id='product-trend-chart'))
                ], md=12)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("关闭", id='close-product-modal', className="ms-auto")
        ])
    ], id='product-detail-modal', size='xl', is_open=False),
    
    # 数据存储组件
    dcc.Store(id='current-data-store', data=[]),  # 存储当前诊断结果
    dcc.Store(id='uploaded-data-metadata', data=None),  # 上传数据的元信息
    dcc.Store(id='upload-timestamp', data=None),  # 上传时间戳
    dcc.Store(id='global-data-info', data={}),  # 全局数据统计信息
    
    # 调试输出（可选）
    html.Div(id='debug-output', style={'display': 'none'})
], fluid=True, className="p-4")


# ==================== 辅助函数 ====================

def get_available_months(df):
    """提取数据中所有的月份，用于月度选择器"""
    if df is None or '日期' not in df.columns:
        return []
    try:
        df_temp = df.copy()
        df_temp['日期'] = pd.to_datetime(df_temp['日期'], errors='coerce')
        min_date = df_temp['日期'].min()
        max_date = df_temp['日期'].max()
        return min_date, max_date
    except Exception as e:
        print(f"❌ 获取日期范围失败: {e}")
        return None, None


# 📊 动态周期选择器回调

# ============================================================================
# 旧Tab 4的动态周期选择器回调已删除（引用已删除的UI组件）
# 新Tab 4采用智能驱动模式，不需要手动选择周期
# ============================================================================

# ==================== 数据库数据源回调函数 ====================

@app.callback(
    [Output('db-store-filter', 'options'),
     Output('database-stats', 'children')],
    Input('data-source-tabs', 'value')
)
def update_database_info(tab_value):
    """当切换到数据库Tab时，加载门店列表和统计信息"""
    if tab_value != 'database-data' or not DATABASE_AVAILABLE or DATA_SOURCE_MANAGER is None:
        return [], html.Div()
    
    try:
        # 获取门店列表
        stores = DATA_SOURCE_MANAGER.get_available_stores()
        store_options = [{'label': store, 'value': store} for store in stores]
        
        # 获取数据库统计
        stats = DATA_SOURCE_MANAGER.get_database_stats()
        
        stats_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H3(f"{stats.get('orders', 0):,}", className="mb-0 text-primary"),
                            html.Small("订单数量", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{stats.get('products', 0):,}", className="mb-0 text-success"),
                            html.Small("商品种类", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{stats.get('stores', 0):,}", className="mb-0 text-info"),
                            html.Small("门店数量", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(stats.get('start_date', '--') + " ~ " + stats.get('end_date', '--'), 
                                   className="mb-0 text-secondary small"),
                            html.Small("数据时间范围", className="text-muted")
                        ])
                    ], md=3)
                ])
            ])
        ], className="mb-3")
        
        return store_options, stats_card
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            f"数据库连接失败: {str(e)}"
        ], color="danger")
        return [], error_msg


@app.callback(
    [Output('current-data-label', 'children', allow_duplicate=True),
     Output('data-update-trigger', 'data', allow_duplicate=True),
     Output('database-load-status', 'children'),
     Output('database-stats', 'children', allow_duplicate=True)],  # 添加统计卡片更新
    Input('load-from-database-btn', 'n_clicks'),
    [State('db-store-filter', 'value'),
     State('db-start-date', 'date'),
     State('db-end-date', 'date')],
    prevent_initial_call=True
)
def load_from_database(n_clicks, store_name, start_date, end_date):
    """从数据库加载数据"""
    if not n_clicks or not DATABASE_AVAILABLE or DATA_SOURCE_MANAGER is None:
        return no_update, no_update, "", no_update
    
    global GLOBAL_DATA
    
    try:
        # 转换日期
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # 从数据库加载
        df = DATA_SOURCE_MANAGER.load_from_database(
            store_name=store_name,
            start_date=start_dt,
            end_date=end_dt
        )
        
        if df.empty:
            return no_update, no_update, dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "未找到符合条件的数据"
            ], color="warning"), no_update
        
        # 应用场景和时段字段
        df = add_scene_and_timeslot_fields(df)
        
        # 更新全局数据
        GLOBAL_DATA = df
        
        # 计算实际加载数据的统计信息
        actual_start = df['日期'].min().strftime('%Y-%m-%d') if '日期' in df.columns else '--'
        actual_end = df['日期'].max().strftime('%Y-%m-%d') if '日期' in df.columns else '--'
        unique_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
        unique_stores = df['门店名称'].nunique() if '门店名称' in df.columns else 0
        
        # 生成更新后的统计卡片
        stats_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H3(f"{len(df):,}", className="mb-0 text-primary"),
                            html.Small("订单数量", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{unique_products:,}", className="mb-0 text-success"),
                            html.Small("商品种类", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{unique_stores:,}", className="mb-0 text-info"),
                            html.Small("门店数量", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{actual_start} ~ {actual_end}", 
                                   className="mb-0 text-secondary small"),
                            html.Small("数据时间范围", className="text-muted")
                        ])
                    ], md=3)
                ])
            ])
        ], className="mb-3")
        
        # 生成数据标签
        label_parts = []
        if store_name:
            label_parts.append(f"门店:{store_name}")
        if start_date and end_date:
            label_parts.append(f"{start_date}~{end_date}")
        elif start_date:
            label_parts.append(f"从{start_date}")
        label = " | ".join(label_parts) if label_parts else "数据库全部数据"
        
        success_msg = dbc.Alert([
            html.I(className="bi bi-check-circle me-2"),
            f"成功加载 {len(df):,} 条数据"
        ], color="success")
        
        return f"数据库: {label}", datetime.now().timestamp(), success_msg, stats_card
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            f"加载失败: {str(e)}"
        ], color="danger")
        return no_update, no_update, error_msg, no_update


# ============================================================================

@app.callback(
    Output('debug-output', 'children'),
    Input('current-data-store', 'data')
)
def debug_stored_data(data):
    """调试回调：检查存储的数据"""
    if not data:
        print("⚠️ current-data-store 中没有数据")
        return ""
    
    df = pd.DataFrame(data)
    print(f"✅ current-data-store 数据加载成功")
    print(f"   - 数据行数: {len(df)}")
    print(f"   - 字段列表: {list(df.columns)}")
    
    # 检查关键字段
    if '场景' in df.columns:
        print(f"   ✓ 包含'场景'字段，唯一值: {df['场景'].unique()[:5]}")
    else:
        print(f"   ✗ 缺少'场景'字段")
    
    if '时段' in df.columns:
        print(f"   ✓ 包含'时段'字段，唯一值: {df['时段'].unique()[:5]}")
    else:
        print(f"   ✗ 缺少'时段'字段")
    
    return ""


# ==================== 可视化图表回调函数 ====================

# 辅助函数：创建空图表
def wrap_chart_component(component, height='450px'):
    """
    统一包装图表组件，确保ECharts/Plotly/空态提示都有一致的容器
    
    参数:
        component: DashECharts / go.Figure / html.Div
        height: 固定高度，避免布局抖动
    
    返回:
        html.Div - 统一的容器组件
    """
    # 如果是 Plotly Figure 对象，转换为 dcc.Graph
    if isinstance(component, go.Figure):
        component = dcc.Graph(
            figure=component,
            config={'displayModeBar': False},
            style={'height': '100%', 'width': '100%'}
        )
    
    # 统一包装在固定高度容器中
    return html.Div(
        component,
        style={
            'height': height,
            'width': '100%',
            'minHeight': height,  # 防止塌陷
            'overflow': 'hidden'   # 防止内容溢出
        }
    )


def create_empty_figure(title="暂无数据", message="请点击上方'🔍 开始诊断'按钮加载数据"):
    """创建友好的空数据图表（返回HTML div用于ECharts容器）"""
    return html.Div([
        html.Div(title, style={
            'textAlign': 'center',
            'fontSize': '18px',
            'fontWeight': 'bold',
            'color': '#666',
            'paddingTop': '80px'
        }),
        html.Div(message, style={
            'textAlign': 'center',
            'fontSize': '14px',
            'color': '#999',
            'paddingTop': '20px'
        })
    ], style={'height': '100%', 'width': '100%'})


def create_empty_plotly_figure(title="暂无数据", message="请点击上方'🔍 开始诊断'按钮加载数据"):
    """创建空态 Plotly Figure（用于 Output(..., 'figure') 的回调）
    
    返回一个带有友好提示的空白 go.Figure 对象，避免类型警告
    """
    fig = go.Figure()
    
    # 添加文本注释显示提示信息
    fig.add_annotation(
        text=f"<b>{title}</b><br><br>{message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#999"),
        align="center"
    )
    
    # 配置布局
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=400
    )
    
    return fig

# 回调1: 分时段下滑分布图
@app.callback(
    Output('chart-slot-distribution', 'children'),
    Input('current-data-store', 'data')
)
def update_slot_distribution_chart(data):
    """分时段销量对比图（ECharts分组柱状图）- 显示当前周期 vs 对比周期"""
    # 🔧 文件日志
    import datetime
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_slot_distribution_chart', ...)
    print(f"\n🎨 [分时段图表] 回调触发", flush=True)
    print(f"   数据类型: {type(data)}", flush=True)
    print(f"   数据长度: {len(data) if data else 0}", flush=True)
    
    if not data or len(data) == 0:
        print("   ⚠️ 数据为空，返回提示信息", flush=True)
        return html.Div([
            html.Div([
                html.I(className="bi bi-search", style={'fontSize': '48px', 'color': '#667eea', 'marginBottom': '15px'}),
                html.H5("⏰ 分时段销量对比", className="mb-3", style={'color': '#667eea'}),
                html.P("请点击上方🔍 开始诊断按钮加载数据", className="text-muted", style={'fontSize': '14px'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 20px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        ])
    
    df = pd.DataFrame(data)
    print(f"   DataFrame形状: {df.shape}", flush=True)
    print(f"   字段列表: {list(df.columns)}", flush=True)
    
    # 🔧 详细日志：检查关键字段
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_slot_distribution_chart', ...)
    # 检查必需字段
    if '时段' not in df.columns:
        print("   ❌ 缺少'时段'字段", flush=True)
        return html.Div([
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                "数据中缺少'时段'字段，请检查数据源"
            ], color="warning")
        ])
    
    # 检查销量字段（支持多种命名）
    # 查找模式：第X周销量、第X期销量、当前周期销量等
    current_qty_col = None
    compare_qty_col = None
    qty_cols = [col for col in df.columns if '销量' in col]
    
    # 🔧 添加详细日志：检查所有销量字段
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('unknown', ...)
    print(f"   🔍 包含'销量'的列: {qty_cols}", flush=True)
    
    if len(qty_cols) >= 2:
        # 假设前两个销量列分别是当前周期和对比周期
        current_qty_col = qty_cols[0]
        compare_qty_col = qty_cols[1]
        print(f"   ✅ 找到销量字段: {current_qty_col}, {compare_qty_col}", flush=True)
        use_fallback = False
    else:
        print(f"   ⚠️ 缺少销量对比字段（需要至少2列），尝试降级方案", flush=True)
        use_fallback = True
    
    # 🔧 清洗时段数据：提取纯时段（去除场景混合）
    # 示例：'下午(14-18点)休闲零食' → '下午(14-18点)'
    #       '晚间(21-24点), 深夜(0-3点)' → '晚间(21-24点)'
    df['纯时段'] = df['时段'].apply(lambda x: str(x).split(',')[0].strip() if pd.notnull(x) else x)
    # 进一步提取：如果有中文后跟时间段，只保留时间段部分
    import re
    df['纯时段'] = df['纯时段'].apply(lambda x: re.search(r'[^a-zA-Z]*\([0-9-]+点\)', str(x)).group() if re.search(r'\([0-9-]+点\)', str(x)) else x)
    
    # 🎯 **新逻辑：分组柱状图对比（当前周期 vs 对比周期）**
    if not use_fallback:
        # 方案A：有销量数据 → 显示销量对比
        slot_stats = df.groupby('纯时段').agg({
            current_qty_col: 'sum',
            compare_qty_col: 'sum'
        }).reset_index()
        
        slot_stats.columns = ['时段', '当前周期销量', '对比周期销量']
        slot_stats = slot_stats.sort_values('当前周期销量', ascending=False)
        
        # 提取周期标签（从列名中提取，如"第40周销量" → "第40周"）
        current_label = current_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in current_qty_col else "当前周期"
        compare_label = compare_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in compare_qty_col else "对比周期"
        
        print(f"   📊 对比模式: {current_label} vs {compare_label}", flush=True)
        print(f"   统计结果: {len(slot_stats)} 个时段", flush=True)
        print(f"   时段数据预览:\n{slot_stats.head()}", flush=True)
        
        if len(slot_stats) == 0:
            return create_empty_figure("⏰ 分时段销量对比", "没有时段数据")
        
        # 🎨 使用 ECharts 分组柱状图
        if ECHARTS_AVAILABLE:
            # 📏 响应式高度计算
            num_slots = len(slot_stats)
            if num_slots <= 5:
                chart_height = 400
                font_size = 11
            elif num_slots <= 8:
                chart_height = 500
                font_size = 11
            else:
                chart_height = 550
                font_size = 10
            
            print(f"   📏 响应式配置: {num_slots}个时段 → 高度{chart_height}px, 字体{font_size}px", flush=True)
            
            option = {
                'title': {
                    'text': f'⏰ 分时段销量对比（{current_label} vs {compare_label}）',
                    'left': 'center',
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'shadow'}
                },
                'legend': {
                    'data': [current_label, compare_label],
                    'top': 35,
                    'textStyle': {'fontSize': 12}
                },
                'grid': {
                    'left': '3%',
                    'right': '4%',
                    'bottom': '10%',
                    'top': '80px',
                    'containLabel': True
                },
                'xAxis': {
                    'type': 'category',
                    'data': slot_stats['时段'].tolist(),
                    'axisLabel': {'interval': 0, 'rotate': 30, 'fontSize': font_size}
                },
                'yAxis': {
                    'type': 'value',
                    'name': '销量',
                    'axisLabel': {'fontSize': 11}
                },
                'series': [
                    {
                        'name': current_label,
                        'type': 'bar',
                        'data': slot_stats['当前周期销量'].tolist(),
                        'itemStyle': {'color': '#ef5350'},  # 红色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    },
                    {
                        'name': compare_label,
                        'type': 'bar',
                        'data': slot_stats['对比周期销量'].tolist(),
                        'itemStyle': {'color': '#42a5f5'},  # 蓝色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    }
                ]
            }
            
            print(f"   ✅ ECharts图表配置生成成功", flush=True)
            
            return DashECharts(
                option=option,
                id='echarts-slot-distribution',
                style={'height': f'{chart_height}px', 'width': '100%'}
            )
    
    # 降级方案：统计下滑商品数
    slot_stats = df.groupby('纯时段').size().reset_index(name='下滑商品数')
    slot_stats.columns = ['时段', '下滑商品数']
    slot_stats = slot_stats.sort_values('下滑商品数', ascending=False)
    
    print(f"   ⚠️ 使用降级方案：统计下滑商品数", flush=True)
    print(f"   统计结果: {len(slot_stats)} 个时段", flush=True)
    
    if len(slot_stats) == 0:
        return create_empty_figure("⏰ 分时段下滑分布", "没有时段数据")
    
    # Plotly柱状图（降级方案）
    fig = go.Figure(data=[
        go.Bar(
            x=slot_stats['时段'],
            y=slot_stats['下滑商品数'],
            marker_color='indianred',
            text=slot_stats['下滑商品数'],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='⏰ 分时段下滑商品分布',
        xaxis_title='时段',
        yaxis_title='下滑商品数',
        height=450,
        margin=dict(l=60, r=60, t=80, b=80)
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    return wrap_chart_component(fig, height='450px')


# 回调2: 分场景下滑分布（饼图）
@app.callback(
    Output('chart-scene-distribution', 'children'),
    Input('current-data-store', 'data')
)
def update_scene_distribution_chart(data):
    """分场景销量对比图（ECharts分组柱状图）- 显示当前周期 vs 对比周期"""
    # 🔧 文件日志
    import datetime
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_scene_distribution_chart', ...)
    if not data or len(data) == 0:
        return html.Div([
            html.Div([
                html.I(className="bi bi-search", style={'fontSize': '48px', 'color': '#667eea', 'marginBottom': '15px'}),
                html.H5("🎭 分场景销量对比", className="mb-3", style={'color': '#667eea'}),
                html.P("请点击上方🔍 开始诊断按钮加载数据", className="text-muted", style={'fontSize': '14px'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 20px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        ])
    
    df = pd.DataFrame(data)
    print(f"\n🎨 [分场景图表] 数据字段: {list(df.columns)}", flush=True)
    
    # 检查必需字段
    if '场景' not in df.columns:
        return html.Div([
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                "数据中缺少'场景'字段，请检查数据源"
            ], color="warning")
        ])
    
    # 🔧 清洗场景数据：提取第一个场景（去除组合场景）
    # 示例：'休闲零食, 早餐' → '休闲零食'
    #       '社交娱乐, 夜间社交' → '社交娱乐'
    df['纯场景'] = df['场景'].apply(lambda x: str(x).split(',')[0].strip() if pd.notnull(x) else x)
    
    # 检查销量字段（支持多种命名）
    # 查找模式：第X周销量、第X期销量、当前周期销量等
    current_qty_col = None
    compare_qty_col = None
    qty_cols = [col for col in df.columns if '销量' in col]
    
    print(f"   🔍 包含'销量'的列: {qty_cols}", flush=True)
    
    if len(qty_cols) >= 2:
        # 假设前两个销量列分别是当前周期和对比周期
        current_qty_col = qty_cols[0]
        compare_qty_col = qty_cols[1]
        print(f"   ✅ 找到销量字段: {current_qty_col}, {compare_qty_col}", flush=True)
        use_fallback = False
    else:
        print(f"   ⚠️ 缺少销量对比字段（需要至少2列），使用降级方案", flush=True)
        use_fallback = True
    
    # 🎯 **新逻辑：分组柱状图对比（当前周期 vs 对比周期）**
    if not use_fallback:
        # 方案A：有销量数据 → 显示销量对比
        scene_stats = df.groupby('纯场景').agg({
            current_qty_col: 'sum',
            compare_qty_col: 'sum'
        }).reset_index()
        
        scene_stats.columns = ['场景', '当前周期销量', '对比周期销量']
        scene_stats = scene_stats.sort_values('当前周期销量', ascending=False)
        
        # 提取周期标签
        current_label = current_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in current_qty_col else "当前周期"
        compare_label = compare_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in compare_qty_col else "对比周期"
        
        print(f"   📊 对比模式: {current_label} vs {compare_label}", flush=True)
        print(f"   统计结果: {len(scene_stats)} 个场景", flush=True)
        print(f"   场景数据预览:\n{scene_stats.head()}", flush=True)
        
        if len(scene_stats) == 0:
            return create_empty_figure("🎭 分场景销量对比", "没有场景数据")
        
        # 🎨 使用 ECharts 分组柱状图
        if ECHARTS_AVAILABLE:
            # 📏 响应式高度计算
            num_scenes = len(scene_stats)
            if num_scenes <= 5:
                chart_height = 400
                font_size = 11
            elif num_scenes <= 8:
                chart_height = 500
                font_size = 11
            else:
                chart_height = 600
                font_size = 10
            
            print(f"   📏 响应式配置: {num_scenes}个场景 → 高度{chart_height}px, 字体{font_size}px", flush=True)
            
            option = {
                'title': {
                    'text': f'🎭 分场景销量对比（{current_label} vs {compare_label}）',
                    'left': 'center',
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'shadow'}
                },
                'legend': {
                    'data': [current_label, compare_label],
                    'top': 35,
                    'textStyle': {'fontSize': 12}
                },
                'grid': {
                    'left': '3%',
                    'right': '4%',
                    'bottom': '10%',
                    'top': '80px',
                    'containLabel': True
                },
                'xAxis': {
                    'type': 'category',
                    'data': scene_stats['场景'].tolist(),
                    'axisLabel': {'interval': 0, 'rotate': 30, 'fontSize': font_size}
                },
                'yAxis': {
                    'type': 'value',
                    'name': '销量',
                    'axisLabel': {'fontSize': 11}
                },
                'series': [
                    {
                        'name': current_label,
                        'type': 'bar',
                        'data': scene_stats['当前周期销量'].tolist(),
                        'itemStyle': {'color': '#ef5350'},  # 红色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    },
                    {
                        'name': compare_label,
                        'type': 'bar',
                        'data': scene_stats['对比周期销量'].tolist(),
                        'itemStyle': {'color': '#42a5f5'},  # 蓝色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    }
                ]
            }
            
            print(f"   ✅ ECharts图表配置生成成功", flush=True)
            
            return DashECharts(
                option=option,
                id='echarts-scene-distribution',
                style={'height': f'{chart_height}px', 'width': '100%'}
            )
    
    # 降级方案：统计下滑商品数
    scene_stats = df.groupby('纯场景').size().reset_index(name='下滑商品数')
    scene_stats.columns = ['场景', '下滑商品数']
    scene_stats = scene_stats.sort_values('下滑商品数', ascending=False)
    
    print(f"   ⚠️ 使用降级方案：统计下滑商品数", flush=True)
    print(f"   场景统计: {len(scene_stats)} 个场景", flush=True)
    
    if len(scene_stats) == 0:
        return create_empty_figure("🎭 分场景下滑分布", "没有场景数据")
    
    # Plotly饼图（降级方案）
    fig = go.Figure(go.Pie(
        labels=scene_stats['场景'],
        values=scene_stats['下滑商品数'],
        hole=0.4,
        marker=dict(colors=['#d32f2f', '#f57c00', '#fbc02d', '#388e3c', '#1976d2']),
        textinfo='label+percent'
    ))
    
    fig.update_layout(
        title='🎭 各场景下滑商品占比',
        height=450,
        margin=dict(l=60, r=60, t=80, b=80)
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    return wrap_chart_component(fig, height='450px')


# 回调3: 周期对比图（ECharts版本）
@app.callback(
    Output('chart-period-comparison', 'children'),
    Input('current-data-store', 'data')
)
def update_period_comparison_chart(data):
    """周期对比图（支持动态周期字段）- ECharts版本
    
    ✨ 新增功能：
    - 动态高度计算：根据商品数量自动调整图表高度
    - 响应式布局：配合 echarts_responsive.js 实现自适应
    """
    print(f"\n📊 [周期对比图-ECharts] 回调触发", flush=True)
    
    if not data or len(data) == 0:
        print("   ⚠️ 数据为空", flush=True)
        return html.Div([
            dbc.Alert([
                html.H6("暂无数据", className="mb-1"),
                html.P("请先点击「开始诊断」按钮生成诊断数据", className="mb-0")
            ], color="info", className="mt-3")
        ])
    
    df = pd.DataFrame(data)
    print(f"   数据行数: {len(df)}", flush=True)
    print(f"   字段列表: {list(df.columns)}", flush=True)
    
    # 🔧 动态查找周期字段（支持"第X周销量"、"第X天销量"等格式）
    sales_cols = [col for col in df.columns if '销量' in col and ('周' in col or '天' in col or '月' in col)]
    print(f"   找到销量字段: {sales_cols}", flush=True)
    
    if len(sales_cols) < 2:
        print("   ❌ 销量字段数量不足", flush=True)
        return html.Div([
            dbc.Alert("数据中缺少周期对比字段", color="warning", className="mt-3")
        ])
    
    # 假设第一个是当前周期，第二个是对比周期
    current_col = sales_cols[0]
    compare_col = sales_cols[1]
    
    print(f"   当前周期: {current_col}", flush=True)
    print(f"   对比周期: {compare_col}", flush=True)
    
    # 检查必需字段
    if '商品名称' not in df.columns:
        print("   ❌ 缺少商品名称字段", flush=True)
        return html.Div([
            dbc.Alert("数据中缺少'商品名称'字段", color="warning", className="mt-3")
        ])
    
    # 🔧 过滤掉当前周期销量为0的商品（已停售商品对对比图意义不大）
    df_filtered = df[df[current_col] > 0].copy()
    print(f"   过滤前商品数: {len(df)}, 过滤后: {len(df_filtered)}", flush=True)
    
    if len(df_filtered) == 0:
        print("   ⚠️ 所有商品当前周期销量为0", flush=True)
        return html.Div([
            dbc.Alert([
                html.H6("暂无可对比商品", className="mb-1"),
                html.P("所有下滑商品当前周期销量为0（可能已停售）", className="mb-0")
            ], color="warning", className="mt-3")
        ])
    
    # 取TOP10下滑商品（按变化幅度排序，只选仍在销售的商品）
    if '变化幅度%' in df_filtered.columns and '_变化幅度_数值' in df_filtered.columns:
        top_products = df_filtered.nsmallest(10, '_变化幅度_数值')[['商品名称', current_col, compare_col]].copy()
    elif '销量变化' in df_filtered.columns:
        top_products = df_filtered.nsmallest(10, '销量变化')[['商品名称', current_col, compare_col]].copy()
    else:
        top_products = df_filtered.head(10)[['商品名称', current_col, compare_col]].copy()
    
    print(f"   TOP10商品数: {len(top_products)}", flush=True)
    
    if len(top_products) == 0:
        return html.Div([
            dbc.Alert("没有符合条件的商品", color="info", className="mt-3")
        ])
    
    # 🔧 确保销量列是数值类型
    top_products[current_col] = pd.to_numeric(top_products[current_col], errors='coerce').fillna(0)
    top_products[compare_col] = pd.to_numeric(top_products[compare_col], errors='coerce').fillna(0)
    
    print(f"   销量数据样本:\n{top_products.head(3)}", flush=True)
    print(f"   {current_col} 数据类型: {top_products[current_col].dtype}", flush=True)
    print(f"   {current_col} 样本值: {top_products[current_col].tolist()[:3]}", flush=True)
    print(f"   {compare_col} 样本值: {top_products[compare_col].tolist()[:3]}", flush=True)
    
    # 提取周期标签（去掉"销量"两字）
    current_label = current_col.replace('销量', '').strip()
    compare_label = compare_col.replace('销量', '').strip()
    
    # 准备ECharts数据 - 确保转换为Python原生类型
    products = [str(name) for name in top_products['商品名称'].tolist()]
    current_values = [int(v) if pd.notna(v) else 0 for v in top_products[current_col].tolist()]
    compare_values = [int(v) if pd.notna(v) else 0 for v in top_products[compare_col].tolist()]
    
    print(f"   产品列表: {products[:3]}", flush=True)
    print(f"   {current_label} 值: {current_values[:3]}", flush=True)
    print(f"   {compare_label} 值: {compare_values[:3]}", flush=True)
    
    # 🎨 创建ECharts配置
    option = {
        'title': {
            'text': 'TOP10下滑商品周期对比',
            'left': 'center',
            'top': 5,
            'textStyle': {
                'fontSize': 14,
                'fontWeight': '600',
                'color': '#333'
            }
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow'
            }
        },
        'legend': {
            'data': [compare_label, current_label],
            'top': 35,
            'left': 'center',
            'itemGap': 20,
            'textStyle': {'fontSize': 12}
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '20%',
            'top': '80px',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': products,
            'axisLabel': {
                'rotate': 45,
                'fontSize': 10,
                'interval': 0,
                'overflow': 'truncate',
                'width': 60
            },
            'axisLine': {'lineStyle': {'color': '#ccc'}},
            'axisTick': {'alignWithLabel': True}
        },
        'yAxis': {
            'type': 'value',
            'name': '销量',
            'nameTextStyle': {'fontSize': 11},
            'axisLine': {'lineStyle': {'color': '#ccc'}},
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': '#eee'}}
        },
        'series': [
            {
                'name': compare_label,
                'type': 'bar',
                'data': compare_values,
                'itemStyle': {
                    'color': '#1976d2',
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 10
                },
                'barMaxWidth': 30
            },
            {
                'name': current_label,
                'type': 'bar',
                'data': current_values,
                'itemStyle': {
                    'color': '#d32f2f',
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 10
                },
                'barMaxWidth': 30
            }
        ]
    }
    
    print(f"   ✅ ECharts图表配置生成成功", flush=True)
    
    # 📏 使用工具函数动态计算高度和配置
    num_products = len(top_products)
    responsive_config = create_responsive_echarts_config(
        data_count=num_products,
        chart_type='bar',
        include_height=True,
        include_grid=True,
        include_font=True
    )
    
    dynamic_height = responsive_config['height']
    print(f"   📏 响应式配置: {num_products}个商品 → 高度{dynamic_height}px, 字体{responsive_config['fontSize']}px", flush=True)
    
    # 更新grid配置（如果数据量大，调整底部空间）
    if num_products > 10:
        option['grid'] = responsive_config['grid']
        print(f"   🎯 已应用动态grid配置: bottom={option['grid']['bottom']}", flush=True)
    
    # 返回ECharts组件 - 使用动态计算的高度
    return DashECharts(
        option=option,
        id='echarts-period-comparison',
        style={'height': f'{dynamic_height}px', 'width': '100%'}  # 动态高度
    )


# 回调4: 分类损失排名图
@app.callback(
    Output('chart-category-loss', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_loss_chart(data):
    """分类收入损失排名图"""
    print(f"\n📉 [分类损失图] 回调触发", flush=True)
    
    if not data or len(data) == 0:
        print("   ⚠️ 数据为空", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "请先点击「开始诊断」按钮")
    
    df = pd.DataFrame(data)
    print(f"   数据行数: {len(df)}", flush=True)
    print(f"   字段列表: {list(df.columns)[:15]}...", flush=True)
    
    # 检查必需字段
    if '一级分类名' not in df.columns:
        print("   ❌ 缺少'一级分类名'字段", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "数据中缺少'一级分类名'字段")
    
    if '商品名称' not in df.columns:
        print("   ❌ 缺少'商品名称'字段", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "数据中缺少'商品名称'字段")
    
    # 检查收入变化字段
    if '收入变化' not in df.columns:
        print("   ❌ 缺少'收入变化'字段", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "数据中缺少'收入变化'字段")
    
    # 确保收入变化是数值类型
    df['收入变化'] = pd.to_numeric(df['收入变化'], errors='coerce').fillna(0)
    
    # 按分类汇总收入损失
    try:
        category_loss = df.groupby('一级分类名').agg({
            '收入变化': 'sum',
            '商品名称': 'count'
        }).reset_index()
        
        category_loss.columns = ['分类', '收入损失', '下滑商品数']
        category_loss['收入损失'] = -category_loss['收入损失']  # 转换为正数（损失）
        category_loss = category_loss.sort_values('收入损失', ascending=False).head(5)  # TOP5损失最大的
        
        print(f"   统计结果: {len(category_loss)} 个分类", flush=True)
        print(f"   TOP分类:\n{category_loss}", flush=True)
        
    except Exception as e:
        print(f"   ❌ 聚合失败: {e}", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", f"数据聚合失败: {str(e)}")
    
    if len(category_loss) == 0:
        return create_empty_plotly_figure("📉 分类损失排名", "没有分类数据")
    
    # 创建Plotly横向柱状图
    fig = go.Figure(data=[
        go.Bar(
            y=category_loss['分类'],
            x=category_loss['收入损失'],
            orientation='h',
            marker_color='#d32f2f',
            text=category_loss['收入损失'].apply(lambda x: f'¥{x:,.0f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>收入损失: ¥%{x:,.0f}<br>下滑商品数: %{customdata}<extra></extra>',
            customdata=category_loss['下滑商品数']
        )
    ])
    
    fig.update_layout(
        title='📉 分类收入损失排名（TOP5）',
        xaxis_title='收入损失（元）',
        yaxis_title='',
        height=320,
        margin=dict(l=100, r=50, t=60, b=50),
        font=dict(family='Microsoft YaHei', size=11),
        template='plotly_white'
    )
    
    print(f"   ✅ 图表生成成功", flush=True)
    return fig  # 直接返回Figure对象，不要包装


# 回调4: 分类TOP商品图
@app.callback(
    Output('chart-category-top-products', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_top_products_chart(data):
    """各分类下滑TOP商品"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("🔻 各分类TOP商品")
    
    df = pd.DataFrame(data)
    
    if '一级分类名' not in df.columns or '销量变化' not in df.columns:
        return create_empty_plotly_figure("🔻 各分类TOP商品", "数据中缺少'一级分类名'或'销量变化'字段")
    
    # 每个分类取TOP3下滑商品
    top_products_list = []
    for category in df['一级分类名'].unique()[:5]:  # 只显示前5个分类
        category_df = df[df['一级分类名'] == category].nlargest(3, '销量变化')
        for _, row in category_df.iterrows():
            top_products_list.append({
                '分类_商品': f"{category[:4]}_{row['商品名称'][:8]}",
                '销量变化': row['销量变化'],
                '分类': category
            })
    
    if not top_products_list:
        return create_empty_plotly_figure("🔻 各分类TOP商品", "没有符合条件的商品数据")
    
    top_df = pd.DataFrame(top_products_list)
    
    # 按分类分组颜色
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    category_colors = {cat: colors[i % len(colors)] for i, cat in enumerate(top_df['分类'].unique())}
    top_df['颜色'] = top_df['分类'].map(category_colors)
    
    fig = go.Figure(data=[
        go.Bar(
            y=top_df['分类_商品'],
            x=top_df['销量变化'],
            orientation='h',
            marker_color=top_df['颜色'],
            text=top_df['销量变化'].apply(lambda x: f'{x:.0f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>销量变化: %{x:.2f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='🔻 各分类下滑TOP商品（每类TOP3）',
        xaxis_title='销量变化',
        yaxis_title='',
        height=450,
        margin=dict(l=150, r=50, t=80, b=50),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig  # 直接返回Figure对象，不要包装


# 回调5: 四维散点图
@app.callback(
    Output('chart-scatter-4d', 'figure'),
    Input('current-data-store', 'data')
)
def update_scatter_4d_chart(data):
    """四维散点图：销量×利润×售价×毛利率"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("💰 四维分析")
    
    df = pd.DataFrame(data)
    
    required_cols = ['销量变化', '利润变化', '商品实售价', '平均毛利率%']
    if not all(col in df.columns for col in required_cols):
        return create_empty_plotly_figure("💰 四维分析", "数据中缺少必要字段（销量变化、利润变化、商品实售价、平均毛利率%）")
    
    # 🔧 将百分比字符串转换为数值
    def parse_percentage(val):
        """将 '44.5%' 转换为 44.5"""
        if isinstance(val, str) and val.endswith('%'):
            try:
                return float(val.replace('%', ''))
            except:
                return 0
        return float(val) if val else 0
    
    # 🔧 将价格字符串转换为数值
    def parse_price(val):
        """将 '¥23.5' 或 '¥23.5¥23.5' 转换为 23.5"""
        if isinstance(val, str):
            # 移除所有 ¥ 符号和空格
            cleaned = val.replace('¥', '').replace(' ', '')
            # 如果重复了（如 "23.523.5"），取第一个数字
            try:
                # 尝试直接转换
                return float(cleaned)
            except:
                # 如果失败，可能是重复格式，提取第一个数字
                import re
                match = re.search(r'(\d+\.?\d*)', cleaned)
                if match:
                    return float(match.group(1))
                return 10.0  # 默认值
        return float(val) if val else 10.0
    
    # 取TOP30避免过于拥挤
    scatter_df = df.nlargest(30, '销量变化').copy()
    scatter_df['毛利率_数值'] = scatter_df['平均毛利率%'].apply(parse_percentage)
    scatter_df['售价_数值'] = scatter_df['商品实售价'].apply(parse_price)  # 🔧 解析价格
    
    fig = go.Figure(data=[
        go.Scatter(
            x=scatter_df['销量变化'],
            y=scatter_df['利润变化'],
            mode='markers',
            marker=dict(
                size=scatter_df['售价_数值'] * 2,  # 🔧 使用数值版本的售价
                color=scatter_df['毛利率_数值'],  # 🔧 使用数值版本的毛利率
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title='毛利率%'),
                line=dict(width=1, color='white')
            ),
            text=scatter_df['商品名称'],
            customdata=scatter_df['售价_数值'],  # 🔧 传递数值版本的售价用于悬停
            hovertemplate='<b>%{text}</b><br>销量变化: %{x:.2f}<br>利润变化: %{y:.2f}<br>售价: ¥%{customdata:.2f}<br>毛利率: %{marker.color:.1f}%<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='💰 销量×利润×售价×毛利率 四维分析',
        xaxis_title='销量变化',
        yaxis_title='利润变化（元）',
        height=400,
        margin=dict(l=50, r=150, t=80, b=50),
        hovermode='closest'
    )
    
    return fig  # 直接返回Figure对象，不要包装


# 回调7: 价格分布图（按分类）
@app.callback(
    Output('chart-price-distribution', 'figure'),
    Input('current-data-store', 'data')
)
def update_price_distribution_chart(data):
    """按分类显示商品价格分布箱线图"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("💵 商品价格分布")
    
    df = pd.DataFrame(data)
    
    if '商品实售价' not in df.columns:
        return create_empty_plotly_figure("💵 商品价格分布", "数据中缺少'商品实售价'字段")
    
    # 检查是否有分类字段
    if '一级分类名' in df.columns:
        # 按分类显示价格分布
        categories = sorted(df['一级分类名'].dropna().unique())
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
        
        for i, category in enumerate(categories):
            category_data = df[df['一级分类名'] == category]['商品实售价']
            
            fig.add_trace(go.Box(
                y=category_data,
                name=category,
                marker_color=colors[i % len(colors)],
                boxmean='sd',  # 显示均值和标准差
                hovertemplate='<b>%{fullData.name}</b><br>价格: ¥%{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='💵 各分类商品价格分布',
            yaxis_title='实售价（元）',
            xaxis_title='商品分类',
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=False
        )
    else:
        # 没有分类，显示整体分布
        fig = go.Figure(data=[
            go.Box(
                y=df['商品实售价'],
                name='价格分布',
                marker_color='lightseagreen',
                boxmean='sd',
                hovertemplate='价格: ¥%{y:.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='💵 商品价格分布',
            yaxis_title='实售价（元）',
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=False
        )
    
    return fig  # 直接返回Figure对象，不要包装


# 回调8: 收入损失TOP10（瀑布图）
@app.callback(
    Output('chart-revenue-top10', 'children'),
    Input('current-data-store', 'data')
)
def update_revenue_top10_chart(data):
    """收入对比TOP10商品（ECharts分组柱状图）- 显示当前周期 vs 对比周期"""
    # 🔧 文件日志
    import datetime
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_revenue_top10_chart', ...)
    if not data or len(data) == 0:
        print("⚠️ [收入TOP10] 没有数据", flush=True)
        return html.Div([
            html.Div([
                html.I(className="bi bi-search", style={'fontSize': '48px', 'color': '#667eea', 'marginBottom': '15px'}),
                html.H5("💸 收入对比TOP10", className="mb-3", style={'color': '#667eea'}),
                html.P("请点击上方🔍 开始诊断按钮加载数据", className="text-muted", style={'fontSize': '14px'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 20px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        ])
    
    df = pd.DataFrame(data)
    print(f"\n🔍 [收入TOP10] 数据字段: {list(df.columns)}", flush=True)
    print(f"   数据行数: {len(df)}", flush=True)
    
    # 检查必需字段
    if '商品名称' not in df.columns:
        return create_empty_plotly_figure("💸 收入对比TOP10", "数据中缺少'商品名称'字段")
    
    # 查找当前周期和对比周期的收入字段
    # 查找模式：第X周预计收入、第X周收入、当前周期收入等
    current_revenue_col = None
    compare_revenue_col = None
    revenue_cols = [col for col in df.columns if '收入' in col and '变化' not in col and '损失' not in col]
    
    print(f"   🔍 包含'收入'的列: {revenue_cols}", flush=True)
    
    if len(revenue_cols) >= 2:
        # 假设前两个收入列分别是当前周期和对比周期
        current_revenue_col = revenue_cols[0]
        compare_revenue_col = revenue_cols[1]
        print(f"   ✅ 找到收入字段: {current_revenue_col}, {compare_revenue_col}", flush=True)
        use_fallback = False
    else:
        print(f"   ⚠️ 缺少收入对比字段（需要至少2列），尝试降级方案", flush=True)
        use_fallback = True
    
    if use_fallback:
        # 降级方案：使用收入变化
        if '收入变化' not in df.columns:
            return create_empty_plotly_figure("💸 收入对比TOP10", "数据中缺少收入相关字段")
        
        # 计算收入损失并使用瀑布图
        df['收入损失'] = -df['收入变化']
        top10_revenue = df.nlargest(10, '收入损失')[['商品名称', '收入变化']].copy()
        
        # Plotly瀑布图（降级方案）
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative"] * len(top10_revenue),
            x=top10_revenue['商品名称'].tolist(),
            y=top10_revenue['收入损失'].tolist(),
            decreasing={"marker": {"color": "#d32f2f"}},
            text=[f"¥{abs(val):,.0f}" for val in top10_revenue['收入变化'].tolist()],
            textposition="outside"
        ))
        
        fig.update_layout(
            title='💸 收入损失TOP10商品',
            yaxis_title='收入损失（元）',
            height=450,
            margin=dict(l=70, r=60, t=80, b=120),
            xaxis={'tickangle': -45}
        )
        
        # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
        
        return wrap_chart_component(fig, height='450px')
    
    # 🎯 **新逻辑：分组柱状图对比（当前周期 vs 对比周期）**
    print(f"   ✅ 找到收入字段: {current_revenue_col}, {compare_revenue_col}", flush=True)
    
    # 确保数值型
    df[current_revenue_col] = pd.to_numeric(df[current_revenue_col], errors='coerce').fillna(0)
    df[compare_revenue_col] = pd.to_numeric(df[compare_revenue_col], errors='coerce').fillna(0)
    
    # 计算收入变化，按损失排序
    df['收入变化'] = df[current_revenue_col] - df[compare_revenue_col]
    df['收入损失'] = -df['收入变化']
    
    # 获取TOP10损失最大的商品
    top10_revenue = df.nlargest(10, '收入损失')[['商品名称', current_revenue_col, compare_revenue_col]].copy()
    top10_revenue.columns = ['商品名称', '当前周期收入', '对比周期收入']
    top10_revenue = top10_revenue.sort_values('对比周期收入', ascending=False)  # 按对比周期降序排列
    
    # 提取周期标签
    current_label = current_revenue_col.replace('收入', '').replace('(', '').replace(')', '') if '(' in current_revenue_col else "当前周期"
    compare_label = compare_revenue_col.replace('收入', '').replace('(', '').replace(')', '') if '(' in compare_revenue_col else "对比周期"
    
    print(f"   📊 对比模式: {current_label} vs {compare_label}", flush=True)
    print(f"   TOP10数据预览:\n{top10_revenue.head()}", flush=True)
    
    if len(top10_revenue) == 0:
        return create_empty_plotly_figure("💸 收入对比TOP10", "没有收入数据")
    
    # 🎨 使用 ECharts 分组柱状图
    if ECHARTS_AVAILABLE:
        # 📏 响应式高度计算
        num_products = len(top10_revenue)
        if num_products <= 5:
            chart_height = 400
            font_size = 11
        elif num_products <= 8:
            chart_height = 550
            font_size = 10
        else:
            chart_height = 650
            font_size = 10
        
        print(f"   📏 响应式配置: {num_products}个商品 → 高度{chart_height}px, 字体{font_size}px", flush=True)
        
        option = {
            'title': {
                'text': f'💸 收入对比TOP10（{current_label} vs {compare_label}）',
                'left': 'center',
                'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'}
            },
            'legend': {
                'data': [current_label, compare_label],
                'top': 35,
                'textStyle': {'fontSize': 12}
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '25%',
                'top': '80px',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': top10_revenue['商品名称'].tolist(),
                'axisLabel': {'interval': 0, 'rotate': 45, 'fontSize': font_size}
            },
            'yAxis': {
                'type': 'value',
                'name': '收入（元）',
                'axisLabel': {'fontSize': 11, 'formatter': '¥{value}'}
            },
            'series': [
                {
                    'name': current_label,
                    'type': 'bar',
                    'data': top10_revenue['当前周期收入'].tolist(),
                    'itemStyle': {'color': '#ef5350'},  # 红色
                    'label': {
                        'show': True,
                        'position': 'top',
                        'fontSize': 9,
                        'formatter': '¥{c}'
                    }
                },
                {
                    'name': compare_label,
                    'type': 'bar',
                    'data': top10_revenue['对比周期收入'].tolist(),
                    'itemStyle': {'color': '#42a5f5'},  # 蓝色
                    'label': {
                        'show': True,
                        'position': 'top',
                        'fontSize': 9,
                        'formatter': '¥{c}'
                    }
                }
            ]
        }
        
        print(f"   ✅ ECharts图表配置生成成功", flush=True)
        
        return DashECharts(
            option=option,
            id='echarts-revenue-top10',
            style={'height': f'{chart_height}px', 'width': '100%'}
        )
    
    # 降级方案：Plotly分组柱状图
    fig = go.Figure(data=[
        go.Bar(
            name=current_label,
            x=top10_revenue['商品名称'],
            y=top10_revenue['当前周期收入'],
            marker_color='#ef5350',
            text=[f"¥{val:,.0f}" for val in top10_revenue['当前周期收入']],
            textposition='outside'
        ),
        go.Bar(
            name=compare_label,
            x=top10_revenue['商品名称'],
            y=top10_revenue['对比周期收入'],
            marker_color='#42a5f5',
            text=[f"¥{val:,.0f}" for val in top10_revenue['对比周期收入']],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=f'💸 收入对比TOP10（{current_label} vs {compare_label}）',
        xaxis_title='',
        yaxis_title='收入（元）',
        barmode='group',
        height=450,
        margin=dict(l=70, r=60, t=80, b=120),
        xaxis={'tickangle': -45},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    
    return wrap_chart_component(fig, height='450px')


# 回调9: 分类树状图
@app.callback(
    Output('chart-category-treemap', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_treemap_chart(data):
    """显示三级分类收入损失树状图"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("🌳 分类树状图")
    
    df = pd.DataFrame(data)
    
    # 检查必需字段
    required_cols = ['一级分类名', '三级分类名', '商品名称', '收入变化']
    if not all(col in df.columns for col in required_cols):
        return create_empty_plotly_figure("🌳 分类树状图", "数据中缺少必需字段")
    
    # 计算收入损失和变化幅度
    treemap_df = df.copy()
    treemap_df['收入损失绝对值'] = treemap_df['收入变化'].abs()
    
    # 计算变化幅度%
    if '变化幅度%' not in treemap_df.columns:
        if '本期销量' in treemap_df.columns and '上期销量' in treemap_df.columns:
            treemap_df['变化幅度%'] = ((treemap_df['本期销量'] - treemap_df['上期销量']) / treemap_df['上期销量'] * 100).fillna(0)
        else:
            treemap_df['变化幅度%'] = -50  # 默认值
    
    # 填充缺失值
    treemap_df['一级分类名'] = treemap_df['一级分类名'].fillna('未分类')
    treemap_df['三级分类名'] = treemap_df['三级分类名'].fillna('其他')
    
    # 创建树状图
    fig = px.treemap(
        treemap_df,
        path=['一级分类名', '三级分类名', '商品名称'],
        values='收入损失绝对值',
        color='变化幅度%',
        color_continuous_scale='Reds',
        color_continuous_midpoint=0,
        hover_data={
            '收入损失绝对值': ':,.0f',
            '变化幅度%': ':.1f'
        },
        labels={
            '收入损失绝对值': '收入损失（元）',
            '变化幅度%': '变化幅度（%）'
        }
    )
    
    fig.update_traces(
        textposition="middle center",
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>收入损失: ¥%{value:,.0f}<br>变化幅度: %{color:.1f}%<extra></extra>'
    )
    
    fig.update_layout(
        title='🌳 三级分类收入损失树状图',
        height=500,
        margin=dict(l=10, r=10, t=60, b=10)
    )
    
    return fig  # 直接返回Figure对象，不要包装


# 回调10: 时段×场景热力图
@app.callback(
    Output('chart-slot-scene-heatmap', 'figure'),
    Input('current-data-store', 'data')
)
def update_slot_scene_heatmap_chart(data):
    """显示时段×场景下滑商品数热力图"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("🔥 时段×场景热力图")
    
    df = pd.DataFrame(data)
    
    # 检查必需字段（注意：字段名是"时段"和"场景"，不是"诊断时段"和"诊断场景"）
    if '时段' not in df.columns or '场景' not in df.columns:
        return create_empty_plotly_figure("🔥 时段×场景热力图", "数据中缺少时段或场景字段")
    
    # 创建交叉透视表：统计每个(时段, 场景)组合的下滑商品数
    heatmap_df = df.groupby(['场景', '时段']).size().reset_index(name='下滑商品数')
    
    # 转换为矩阵格式
    heatmap_matrix = heatmap_df.pivot(index='场景', columns='时段', values='下滑商品数').fillna(0)
    
    if heatmap_matrix.empty:
        return create_empty_plotly_figure("🔥 时段×场景热力图", "没有足够的数据生成热力图")
    
    # 创建热力图
    fig = px.imshow(
        heatmap_matrix,
        labels=dict(x="时段", y="场景", color="下滑商品数"),
        x=heatmap_matrix.columns.tolist(),
        y=heatmap_matrix.index.tolist(),
        color_continuous_scale='Reds',
        aspect="auto",
        text_auto=True
    )
    
    fig.update_traces(
        hovertemplate='<b>场景:</b> %{y}<br><b>时段:</b> %{x}<br><b>下滑商品数:</b> %{z}<extra></extra>',
        textfont={"size": 14}
    )
    
    fig.update_layout(
        title='🔥 时段×场景下滑商品数热力图',
        height=500,
        margin=dict(l=100, r=50, t=80, b=80),
        xaxis_title='诊断时段',
        yaxis_title='诊断场景'
    )
    
    # 调整坐标轴
    fig.update_xaxes(side="bottom")
    fig.update_yaxes(side="left")
    
    return fig  # 直接返回Figure对象，不要包装


# 回调11: 热力图详细数据表格
@app.callback(
    [Output('heatmap-detail-table', 'columns'),
     Output('heatmap-detail-table', 'data')],
    Input('current-data-store', 'data')
)
def update_heatmap_detail_table(data):
    """生成时段×场景交叉分析的详细数据表格"""
    if not data or len(data) == 0:
        return [], []
    
    df = pd.DataFrame(data)
    
    # 检查必需字段（注意：字段名是"时段"和"场景"）
    if '时段' not in df.columns or '场景' not in df.columns:
        return [], []
    
    # 创建交叉分析表
    # 方式1：统计每个(场景, 时段)组合的下滑商品数
    agg_dict = {
        '商品名称': 'count',  # 下滑商品数
    }
    
    # 动态添加存在的字段
    if '销量变化' in df.columns:
        agg_dict['销量变化'] = 'sum'  # 总销量损失
    if '收入变化' in df.columns:
        agg_dict['收入变化'] = 'sum'  # 总收入损失
    if '_变化幅度_数值' in df.columns:
        agg_dict['_变化幅度_数值'] = 'mean'  # 平均下滑幅度
    
    cross_df = df.groupby(['场景', '时段']).agg(agg_dict).reset_index()
    
    # 重命名列（根据实际存在的列）
    column_mapping = {
        '场景': '场景',
        '时段': '时段',
        '商品名称': '下滑商品数'
    }
    
    if '销量变化' in cross_df.columns:
        column_mapping['销量变化'] = '总销量损失'
    if '收入变化' in cross_df.columns:
        column_mapping['收入变化'] = '总收入损失'
    if '_变化幅度_数值' in cross_df.columns:
        column_mapping['_变化幅度_数值'] = '平均下滑幅度%'
    
    cross_df = cross_df.rename(columns=column_mapping)
    
    # 格式化数值（只格式化存在的列）
    if '总销量损失' in cross_df.columns:
        cross_df['总销量损失'] = cross_df['总销量损失'].apply(lambda x: int(x))
    if '总收入损失' in cross_df.columns:
        cross_df['总收入损失'] = cross_df['总收入损失'].apply(lambda x: f"¥{x:,.0f}")
    if '平均下滑幅度%' in cross_df.columns:
        cross_df['平均下滑幅度%'] = cross_df['平均下滑幅度%'].apply(lambda x: f"{x:.1f}%")
    
    # 按下滑商品数降序排列
    cross_df = cross_df.sort_values('下滑商品数', ascending=False)
    
    # 定义表格列（根据实际存在的列动态生成）
    columns = [
        {'name': '场景', 'id': '场景'},
        {'name': '时段', 'id': '时段'},
        {'name': '下滑商品数', 'id': '下滑商品数', 'type': 'numeric'}
    ]
    
    # 添加存在的列
    if '总销量损失' in cross_df.columns:
        columns.append({'name': '总销量损失', 'id': '总销量损失', 'type': 'numeric'})
    if '总收入损失' in cross_df.columns:
        columns.append({'name': '总收入损失', 'id': '总收入损失'})
    if '平均下滑幅度%' in cross_df.columns:
        columns.append({'name': '平均下滑幅度', 'id': '平均下滑幅度%'})
    
    return columns, cross_df.to_dict('records')


# ==================== Modal弹窗回调函数 ====================

# 打开/关闭Modal
@app.callback(
    Output('product-modal', 'is_open'),
    [Input('detail-table', 'active_cell'),
     Input('close-modal', 'n_clicks')],
    State('product-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_modal(active_cell, close_clicks, is_open):
    """切换Modal显示状态"""
    ctx = callback_context
    
    if not ctx.triggered:
        return is_open
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 点击表格单元格打开Modal
    if trigger_id == 'detail-table' and active_cell:
        return True
    
    # 点击关闭按钮关闭Modal
    if trigger_id == 'close-modal':
        return False
    
    return is_open


# 更新Modal内容
@app.callback(
    [Output('modal-product-title', 'children'),
     Output('product-basic-info', 'children'),
     Output('product-comparison-data', 'children'),
     Output('product-trend-chart', 'figure')],
    Input('detail-table', 'active_cell'),
    [State('detail-table', 'data'),
     State('current-data-store', 'data')],
    prevent_initial_call=True
)
def update_modal_content(active_cell, table_data, store_data):
    """更新Modal弹窗内容"""
    if not active_cell or not table_data:
        return "商品详情", "请选择商品", "无数据", create_empty_plotly_figure("暂无趋势数据")
    
    row_index = active_cell['row']
    if row_index >= len(table_data):
        return "商品详情", "数据错误", "无数据", create_empty_plotly_figure("暂无趋势数据")
    
    # 获取选中的商品数据
    product_row = table_data[row_index]
    product_name = product_row.get('商品名称', '未知商品')
    
    # 基础信息
    basic_info = dbc.ListGroup([
        dbc.ListGroupItem([
            html.Strong("商品名称: "),
            html.Span(product_name)
        ]),
        dbc.ListGroupItem([
            html.Strong("场景: "),
            html.Span(product_row.get('场景', '-'))
        ]),
        dbc.ListGroupItem([
            html.Strong("时段: "),
            html.Span(product_row.get('时段', '-'))
        ]),
        dbc.ListGroupItem([
            html.Strong("一级分类: "),
            html.Span(product_row.get('一级分类名', '-'))
        ]),
        dbc.ListGroupItem([
            html.Strong("商品实售价: "),
            html.Span(product_row.get('商品实售价', '-'))
        ])
    ])
    
    # 对比数据
    comparison_data = dbc.Table([
        html.Thead(html.Tr([
            html.Th("指标"),
            html.Th("对比周期"),
            html.Th("当前周期"),
            html.Th("变化")
        ])),
        html.Tbody([
            html.Tr([
                html.Td("销量"),
                html.Td(product_row.get('对比周期销量', '-') if '对比周期销量' in product_row else '-'),
                html.Td(product_row.get('当前周期销量', '-') if '当前周期销量' in product_row else '-'),
                html.Td(product_row.get('销量变化', '-'), style={'color': 'red' if str(product_row.get('销量变化', '0')).replace('-', '').replace('.', '').isdigit() and float(product_row.get('销量变化', 0)) < 0 else 'green'})
            ]),
            html.Tr([
                html.Td("收入"),
                html.Td(product_row.get('对比周期收入', '-') if '对比周期收入' in product_row else '-'),
                html.Td(product_row.get('当前周期收入', '-') if '当前周期收入' in product_row else '-'),
                html.Td(product_row.get('收入变化', '-'))
            ]),
            html.Tr([
                html.Td("利润"),
                html.Td(product_row.get('对比周期利润', '-') if '对比周期利润' in product_row else '-'),
                html.Td(product_row.get('当前周期利润', '-') if '当前周期利润' in product_row else '-'),
                html.Td(product_row.get('利润变化', '-'))
            ])
        ])
    ], bordered=True, hover=True, striped=True, size='sm')
    
    # 创建简单的趋势图（模拟数据，实际应该从历史数据获取）
    trend_fig = go.Figure()
    
    # 如果有完整数据，绘制对比柱状图
    if '对比周期销量' in product_row and '当前周期销量' in product_row:
        try:
            compare_val = float(str(product_row.get('对比周期销量', '0')).replace('¥', '').replace(',', ''))
            current_val = float(str(product_row.get('当前周期销量', '0')).replace('¥', '').replace(',', ''))
            
            trend_fig.add_trace(go.Bar(
                name='对比周期',
                x=['销量'],
                y=[compare_val],
                marker_color='lightblue'
            ))
            
            trend_fig.add_trace(go.Bar(
                name='当前周期',
                x=['销量'],
                y=[current_val],
                marker_color='coral'
            ))
            
            trend_fig.update_layout(
                title=f'{product_name} - 周期对比',
                barmode='group',
                height=300,
                margin=dict(l=50, r=50, t=80, b=50)
            )
        except:
            trend_fig = create_empty_figure("趋势数据", "数据格式错误，无法绘制")
    else:
        trend_fig = create_empty_figure("趋势数据", "缺少历史对比数据")
    
    return f"📦 {product_name}", basic_info, comparison_data, trend_fig



# ==================== 辅助函数：图表生成 ====================

def create_category_cost_chart_echarts(df):
    """创建商品成本分类分析图表 - ECharts版本"""
    if '一级分类名' not in df.columns or '商品采购成本' not in df.columns:
        return html.Div("⚠️ 缺少必要字段", className="text-center text-muted p-5")
    
    # 按一级分类统计商品成本
    category_cost = df.groupby('一级分类名').agg({
        '商品采购成本': 'sum',
        '商品名称': 'count'
    }).reset_index()
    category_cost.columns = ['分类', '总成本', '商品数量']
    category_cost = category_cost.sort_values('总成本', ascending=False).head(10)
    
    # 格式化数据
    formatted_costs = [format_number(v) for v in category_cost['总成本'].tolist()]
    formatted_counts = [format_number(v) for v in category_cost['商品数量'].tolist()]
    
    # 预处理标签数据（用于显示）
    cost_labels = [f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}' for x in category_cost['总成本']]
    
    # 📏 响应式高度计算
    num_categories = len(category_cost)
    if num_categories <= 5:
        chart_height = 380
        font_size = 11
    elif num_categories <= 8:
        chart_height = 420
        font_size = 11
    else:
        chart_height = 480
        font_size = 10
    
    # ECharts 配置
    option = {
        'title': {
            'text': '🏆 TOP 10 分类成本排行',
            'left': 'center',
            'top': '3%',
            'textStyle': {
                'fontSize': 18,
                'fontWeight': 'bold',
                'color': '#1a1a1a'
            }
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'},
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'borderWidth': 1,
            'textStyle': {'color': '#333'},
            'formatter': '{b}<br/>💰 总成本: ¥{c0}<br/>📦 商品数量: {c1}'
        },
        'legend': {
            'data': ['总成本', '商品数量'],
            'top': '8%',
            'textStyle': {'fontSize': 12}
        },
        'grid': {
            'left': '8%',
            'right': '8%',
            'top': '20%',
            'bottom': '15%',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': category_cost['分类'].tolist(),
            'axisLabel': {
                'rotate': 35,
                'fontSize': font_size,
                'color': '#2c3e50',
                'interval': 0
            },
            'axisLine': {'lineStyle': {'color': 'rgba(0,0,0,0.1)'}},
            'axisTick': {'show': False}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '💰 总成本 (¥)',
                'nameTextStyle': {'color': '#2E5C8A', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {'fontSize': 10, 'color': '#2c3e50'},
                'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
            },
            {
                'type': 'value',
                'name': '📦 商品数量',
                'nameTextStyle': {'color': '#FF6B6B', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {'fontSize': 10, 'color': '#2c3e50'},
                'splitLine': {'show': False}
            }
        ],
        'series': [
            {
                'name': '总成本',
                'type': 'bar',
                'data': [{'value': v, 'label': l} for v, l in zip(formatted_costs, cost_labels)],
                'yAxisIndex': 0,
                'barWidth': '50%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': '#4A90E2'},
                            {'offset': 0.5, 'color': '#2E5C8A'},
                            {'offset': 1, 'color': '#1A3A5C'}
                        ]
                    },
                    'borderRadius': [8, 8, 0, 0],
                    'shadowColor': 'rgba(0,0,0,0.2)',
                    'shadowBlur': 10
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{@label}',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowColor': 'rgba(0,0,0,0.5)',
                        'shadowBlur': 20
                    }
                },
                'animationDelay': '{dataIndex} * 50'
            },
            {
                'name': '商品数量',
                'type': 'line',
                'data': formatted_counts,
                'yAxisIndex': 1,
                'smooth': True,
                'symbol': 'circle',
                'symbolSize': 10,
                'lineStyle': {'width': 4, 'color': '#FF6B6B'},
                'itemStyle': {'color': '#FF6B6B', 'borderWidth': 3, 'borderColor': '#fff'},
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': 'rgba(255,107,107,0.3)'},
                            {'offset': 1, 'color': 'rgba(255,107,107,0.05)'}
                        ]
                    }
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#FF6B6B'
                }
            }
        ],
        'animationEasing': 'elasticOut',
        'animationDuration': 1000
    }
    
    return DashECharts(
        option=option,
        id='category-cost-chart-echarts',
        style={'height': f'{chart_height}px', 'width': '100%'}
    )


def create_category_cost_chart(df):
    """创建商品成本分类分析图表 - 智能选择版本"""
    if ECHARTS_AVAILABLE:
        return create_category_cost_chart_echarts(df)
    
    # Plotly 备份方案（保持原有代码）
    if '一级分类名' not in df.columns or '商品采购成本' not in df.columns:
        return go.Figure().update_layout(
            title="⚠️ 缺少必要字段",
            annotations=[dict(text="数据中缺少'一级分类名'或'商品采购成本'字段", 
                            showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
        )
    
    # 按一级分类统计商品成本
    category_cost = df.groupby('一级分类名').agg({
        '商品采购成本': 'sum',
        '商品名称': 'count'  # 统计商品数量
    }).reset_index()
    category_cost.columns = ['分类', '总成本', '商品数量']
    category_cost = category_cost.sort_values('总成本', ascending=False).head(10)
    
    # 创建双轴柱状图 - 优化版
    fig = go.Figure()
    
    # 主轴：成本（柱状图 - 渐变色效果）
    fig.add_trace(go.Bar(
        name='总成本',
        x=category_cost['分类'],
        y=category_cost['总成本'],
        yaxis='y',
        marker=dict(
            color=category_cost['总成本'],  # 使用数值映射颜色
            colorscale=[
                [0, '#4A90E2'],      # 浅蓝
                [0.5, '#2E5C8A'],    # 中蓝
                [1, '#1A3A5C']       # 深蓝
            ],
            showscale=False,
            line=dict(color='rgba(255,255,255,0.3)', width=1.5),
            # 添加圆角效果（通过调整bar的corner radius）
        ),
        text=category_cost['总成本'].apply(lambda x: f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}'),
        textposition='outside',  # 改为外部显示，避免遮挡
        textfont=dict(color='#2c3e50', size=11, family='Arial'),
        hovertemplate='<b>%{x}</b><br>💰 总成本: ¥%{y:,.2f}<extra></extra>',
        width=0.65,
        opacity=0.9  # 添加透明度
    ))
    
    # 次轴：商品数量（折线图 - 优化样式）
    fig.add_trace(go.Scatter(
        name='商品数量',
        x=category_cost['分类'],
        y=category_cost['商品数量'],
        yaxis='y2',
        mode='lines+markers+text',
        marker=dict(
            color='#FF6B6B',
            size=12,
            symbol='circle',
            line=dict(color='white', width=3),
            gradient=dict(type='radial', color=['#FF6B6B', '#FF8E8E'])
        ),
        line=dict(color='#FF6B6B', width=4, shape='spline'),  # 平滑曲线
        text=category_cost['商品数量'],
        textposition='top center',
        textfont=dict(size=11, color='#FF6B6B', family='Arial', weight='bold'),
        hovertemplate='<b>%{x}</b><br>📦 商品数量: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='🏆 TOP 10 分类成本排行',
            font=dict(size=16, color='#1a1a1a', family='Arial, sans-serif', weight='bold'),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        xaxis=dict(
            title='',
            tickangle=-35,
            tickfont=dict(size=11, color='#2c3e50', family='Arial'),
            showline=True,
            linewidth=2,
            linecolor='rgba(0,0,0,0.1)',
            mirror=False
        ),
        yaxis=dict(
            title=dict(
                text='💰 总成本 (¥)',
                font=dict(size=12, color='#2E5C8A', family='Arial', weight='bold')
            ),
            side='left',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        yaxis2=dict(
            title=dict(
                text='📦 商品数量',
                font=dict(size=12, color='#FF6B6B', family='Arial', weight='bold')
            ),
            side='right',
            overlaying='y',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=False
        ),
        height=380,  # 增加高度以容纳外部文本
        margin=dict(l=70, r=70, t=70, b=80),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.25,
            xanchor='center',
            x=0.5,
            font=dict(size=11, family='Arial'),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        bargap=0.3,
        plot_bgcolor='rgba(248,250,252,0.8)',  # 更柔和的背景
        paper_bgcolor='white',
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(255,255,255,0.95)',
            font=dict(size=12, family='Arial'),
            bordercolor='rgba(0,0,0,0.1)'
        ),
        # 添加动画效果
        transition=dict(duration=500, easing='cubic-in-out')
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    
    return wrap_chart_component(fig, height='450px')


def create_marketing_activity_chart_echarts(order_agg):
    """创建商家活动补贴分析图表 - ECharts版本"""
    required_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    
    # 检查必要字段
    missing_fields = [f for f in required_fields if f not in order_agg.columns]
    if missing_fields:
        return html.Div(f"⚠️ 缺少必要字段: {', '.join(missing_fields)}", className="text-center text-muted p-5")
    
    # 统计各类补贴
    subsidy_data = {
        '满减优惠': {
            '总金额': order_agg['满减金额'].sum(),
            '参与订单数': (order_agg['满减金额'] > 0).sum()
        },
        '商品折扣': {
            '总金额': order_agg['商品减免金额'].sum(),
            '参与订单数': (order_agg['商品减免金额'] > 0).sum()
        },
        '代金券': {
            '总金额': order_agg['商家代金券'].sum(),
            '参与订单数': (order_agg['商家代金券'] > 0).sum()
        },
        '商家承担券': {
            '总金额': order_agg['商家承担部分券'].sum(),
            '参与订单数': (order_agg['商家承担部分券'] > 0).sum()
        }
    }
    
    activities = list(subsidy_data.keys())
    amounts = [subsidy_data[k]['总金额'] for k in activities]
    orders = [subsidy_data[k]['参与订单数'] for k in activities]
    
    # 格式化数据
    formatted_amounts = [format_number(v) for v in amounts]
    formatted_orders = [format_number(v) for v in orders]
    
    # 预处理标签数据（用于显示）
    amount_labels = [f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}' for x in amounts]
    
    # ECharts 配置
    option = {
        'title': {
            'text': '🎁 各类补贴活动力度与参与度',
            'left': 'center',
            'top': '3%',
            'textStyle': {
                'fontSize': 18,
                'fontWeight': 'bold',
                'color': '#1a1a1a'
            }
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'},
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'borderWidth': 1,
            'textStyle': {'color': '#333'}
        },
        'legend': {
            'data': ['补贴总金额', '参与订单数'],
            'top': '8%',
            'textStyle': {'fontSize': 12}
        },
        'grid': {
            'left': '8%',
            'right': '8%',
            'top': '20%',
            'bottom': '12%',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': activities,
            'axisLabel': {
                'fontSize': 12,
                'color': '#2c3e50',
                'interval': 0
            },
            'axisLine': {'lineStyle': {'color': 'rgba(0,0,0,0.1)'}},
            'axisTick': {'show': False}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '💳 补贴金额 (¥)',
                'nameTextStyle': {'color': '#E74C3C', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {'fontSize': 10, 'color': '#2c3e50'},
                'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
            },
            {
                'type': 'value',
                'name': '📋 参与订单数',
                'nameTextStyle': {'color': '#2ECC71', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {'fontSize': 10, 'color': '#2c3e50'},
                'splitLine': {'show': False}
            }
        ],
        'series': [
            {
                'name': '补贴总金额',
                'type': 'bar',
                'data': [{'value': v, 'label': l} for v, l in zip(formatted_amounts, amount_labels)],
                'yAxisIndex': 0,
                'barWidth': '45%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': '#FF6B6B'},
                            {'offset': 0.5, 'color': '#E74C3C'},
                            {'offset': 1, 'color': '#C0392B'}
                        ]
                    },
                    'borderRadius': [8, 8, 0, 0],
                    'shadowColor': 'rgba(231,76,60,0.3)',
                    'shadowBlur': 10
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{@label}',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowColor': 'rgba(231,76,60,0.6)',
                        'shadowBlur': 20,
                        'scale': True
                    }
                },
                'animationDelay': '{dataIndex} * 100'
            },
            {
                'name': '参与订单数',
                'type': 'line',
                'data': formatted_orders,
                'yAxisIndex': 1,
                'smooth': True,
                'symbol': 'diamond',
                'symbolSize': 12,
                'lineStyle': {'width': 4, 'color': '#2ECC71'},
                'itemStyle': {
                    'color': '#2ECC71',
                    'borderWidth': 3,
                    'borderColor': '#fff'
                },
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': 'rgba(46,204,113,0.4)'},
                            {'offset': 1, 'color': 'rgba(46,204,113,0.05)'}
                        ]
                    }
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#2ECC71'
                },
                'emphasis': {
                    'scale': True,
                    'focus': 'series'
                }
            }
        ],
        'animationEasing': 'elasticOut',
        'animationDuration': 1200
    }
    
    return DashECharts(
        option=option,
        id='marketing-activity-chart-echarts',
        style={'height': '420px', 'width': '100%'}
    )


def create_marketing_activity_chart(order_agg):
    """创建商家活动补贴分析图表 - 智能选择版本"""
    if ECHARTS_AVAILABLE:
        return create_marketing_activity_chart_echarts(order_agg)
    
    # Plotly 备份方案（保持原有代码）
    """创建商家活动补贴分析图表"""
    required_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    
    # 检查必要字段
    missing_fields = [f for f in required_fields if f not in order_agg.columns]
    if missing_fields:
        return go.Figure().update_layout(
            title="⚠️ 缺少必要字段",
            annotations=[dict(text=f"数据中缺少字段: {', '.join(missing_fields)}", 
                            showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
        )
    
    # 统计各类补贴
    subsidy_data = {
        '满减优惠': {
            '总金额': order_agg['满减金额'].sum(),
            '参与订单数': (order_agg['满减金额'] > 0).sum()
        },
        '商品折扣': {
            '总金额': order_agg['商品减免金额'].sum(),
            '参与订单数': (order_agg['商品减免金额'] > 0).sum()
        },
        '代金券': {
            '总金额': order_agg['商家代金券'].sum(),
            '参与订单数': (order_agg['商家代金券'] > 0).sum()
        },
        '商家承担券': {
            '总金额': order_agg['商家承担部分券'].sum(),
            '参与订单数': (order_agg['商家承担部分券'] > 0).sum()
        }
    }
    
    # 构造数据
    activities = list(subsidy_data.keys())
    amounts = [subsidy_data[k]['总金额'] for k in activities]
    orders = [subsidy_data[k]['参与订单数'] for k in activities]
    
    # 创建双轴柱状图 - 优化版
    fig = go.Figure()
    
    # 主轴：补贴金额（柱状图 - 渐变红色）
    fig.add_trace(go.Bar(
        name='补贴总金额',
        x=activities,
        y=amounts,
        yaxis='y',
        marker=dict(
            color=amounts,  # 使用数值映射颜色
            colorscale=[
                [0, '#FF6B6B'],      # 浅红
                [0.5, '#E74C3C'],    # 中红
                [1, '#C0392B']       # 深红
            ],
            showscale=False,
            line=dict(color='rgba(255,255,255,0.4)', width=2),
        ),
        text=[f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}' for x in amounts],
        textposition='outside',  # 改为外部显示
        textfont=dict(color='#2c3e50', size=11, family='Arial'),
        width=0.5,
        hovertemplate='<b>%{x}</b><br>💳 补贴金额: ¥%{y:,.2f}<extra></extra>',
        opacity=0.9
    ))
    
    # 次轴：参与订单数（折线图 - 优化样式）
    fig.add_trace(go.Scatter(
        name='参与订单数',
        x=activities,
        y=orders,
        yaxis='y2',
        mode='lines+markers+text',
        marker=dict(
            color='#2ECC71',
            size=14,
            symbol='diamond',
            line=dict(color='white', width=3)
        ),
        line=dict(color='#2ECC71', width=4, shape='spline'),  # 平滑曲线
        text=[f'{int(x)}' for x in orders],
        textposition='top center',
        textfont=dict(size=11, color='#2ECC71', family='Arial'),
        hovertemplate='<b>%{x}</b><br>📋 参与订单: %{y:,}单<extra></extra>',
        fill='tonexty',
        fillcolor='rgba(46,204,113,0.1)'  # 添加区域填充
    ))
    
    fig.update_layout(
        title=dict(
            text='🎁 各类补贴活动力度与参与度',
            font=dict(size=16, color='#1a1a1a', family='Arial, sans-serif', weight='bold'),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        xaxis=dict(
            title='',
            tickfont=dict(size=11, color='#2c3e50', family='Arial'),
            showline=True,
            linewidth=2,
            linecolor='rgba(0,0,0,0.1)',
            mirror=False
        ),
        yaxis=dict(
            title=dict(
                text='💳 补贴金额 (¥)',
                font=dict(size=12, color='#E74C3C', family='Arial', weight='bold')
            ),
            side='left',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.05)',
            range=[0, max(amounts) * 1.2] if amounts else [0, 1000],
            zeroline=False
        ),
        yaxis2=dict(
            title=dict(
                text='📋 参与订单数',
                font=dict(size=12, color='#2ECC71', family='Arial', weight='bold')
            ),
            side='right',
            overlaying='y',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=False,
            range=[0, max(orders) * 1.25] if orders else [0, 100]
        ),
        height=380,  # 增加高度
        margin=dict(l=70, r=70, t=70, b=80),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.22,
            xanchor='center',
            x=0.5,
            font=dict(size=11, family='Arial'),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        bargap=0.4,  # 调整间距
        plot_bgcolor='rgba(248,250,252,0.8)',
        paper_bgcolor='white',
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(255,255,255,0.95)',
            font=dict(size=12, family='Arial'),
            bordercolor='rgba(0,0,0,0.1)'
        ),
        # 添加动画效果
        transition=dict(duration=500, easing='cubic-in-out')
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    
    return wrap_chart_component(fig, height='450px')


# ==================== 数值格式化工具函数 ====================

def format_number(value):
    """
    智能数值格式化：整数显示整数，有小数则保留一位
    
    Args:
        value: 数值
    
    Returns:
        格式化后的数值（整数或保留一位小数）
    """
    if value == int(value):
        return int(value)
    else:
        return round(value, 1)


# ==================== 更多 ECharts 图表函数 ====================

def create_sales_trend_chart_echarts(daily_sales):
    """创建销售趋势分析图表 - ECharts版本"""
    
    # 格式化数据
    formatted_sales = [format_number(v) for v in daily_sales['销售额'].tolist()]
    formatted_profit = [format_number(v) for v in daily_sales['总利润'].tolist()]
    formatted_orders = [format_number(v) for v in daily_sales['订单数'].tolist()]
    
    # 计算订单数的范围，用于优化右Y轴显示
    order_min = daily_sales['订单数'].min()
    order_max = daily_sales['订单数'].max()
    # 给订单数轴留出20%的上下空间，让曲线更饱满
    order_range = order_max - order_min
    order_axis_min = max(0, order_min - order_range * 0.2)
    order_axis_max = order_max + order_range * 0.2
    
    option = {
        'title': {
            'text': '📈 销售趋势分析',
            'left': 'center',
            'top': '3%',
            'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'},
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'borderWidth': 1
        },
        'legend': {
            'data': ['销售额', '总利润', '订单数'],
            'top': '8%'
        },
        'grid': {'left': '8%', 'right': '8%', 'top': '20%', 'bottom': '15%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'data': [str(d) for d in daily_sales['日期'].tolist()],
            'axisLabel': {'rotate': 30, 'fontSize': 10}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '金额 (¥)',
                'nameTextStyle': {'color': '#333', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {'fontSize': 10},
                'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
            },
            {
                'type': 'value',
                'name': '订单数',
                'nameTextStyle': {'color': '#ff7f0e', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {'fontSize': 10},
                'min': int(order_axis_min),  # 动态设置最小值
                'max': int(order_axis_max),  # 动态设置最大值
                'splitLine': {'show': False}
            }
        ],
        'series': [
            {
                'name': '销售额',
                'type': 'line',
                'data': formatted_sales,
                'yAxisIndex': 0,
                'smooth': True,
                'symbol': 'circle',
                'symbolSize': 8,
                'lineStyle': {'width': 3, 'color': '#1f77b4'},
                'itemStyle': {'color': '#1f77b4', 'borderWidth': 2, 'borderColor': '#fff'},
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': 'rgba(31,119,180,0.3)'},
                            {'offset': 1, 'color': 'rgba(31,119,180,0.05)'}
                        ]
                    }
                }
            },
            {
                'name': '总利润',
                'type': 'line',
                'data': formatted_profit,
                'yAxisIndex': 0,
                'smooth': True,
                'symbol': 'triangle',
                'symbolSize': 8,
                'lineStyle': {'width': 3, 'color': '#2ca02c'},
                'itemStyle': {'color': '#2ca02c', 'borderWidth': 2, 'borderColor': '#fff'}
            },
            {
                'name': '订单数',
                'type': 'line',
                'data': formatted_orders,
                'yAxisIndex': 1,
                'smooth': True,
                'symbol': 'diamond',
                'symbolSize': 8,
                'lineStyle': {'width': 3, 'color': '#ff7f0e'},
                'itemStyle': {'color': '#ff7f0e', 'borderWidth': 2, 'borderColor': '#fff'}
            }
        ],
        'animationEasing': 'cubicOut',
        'animationDuration': 1000
    }
    
    return DashECharts(
        option=option,
        style={'height': '400px', 'width': '100%'}
    )


def analyze_daily_anomalies(df, daily_sales):
    """智能异常分析：识别销售趋势中的异常点并深度分析原因"""
    
    # 计算利润率
    daily_sales['利润率'] = (daily_sales['总利润'] / daily_sales['销售额'] * 100).round(2)
    daily_sales['单均销售额'] = (daily_sales['销售额'] / daily_sales['订单数']).round(2)
    daily_sales['单均利润'] = (daily_sales['总利润'] / daily_sales['订单数']).round(2)
    
    # 计算历史平均值（用于异常检测）
    avg_profit_rate = daily_sales['利润率'].mean()
    std_profit_rate = daily_sales['利润率'].std()
    
    # 识别异常点：利润率低于平均值-1个标准差
    daily_sales['异常标记'] = daily_sales['利润率'] < (avg_profit_rate - std_profit_rate)
    
    # 找出最佳日和最差日
    best_day = daily_sales.loc[daily_sales['利润率'].idxmax()]
    worst_day = daily_sales.loc[daily_sales['利润率'].idxmin()]
    
    # 识别所有异常日期
    anomaly_days = daily_sales[daily_sales['异常标记']].copy()
    
    # 分析每个异常日期的详细原因
    anomaly_details = []
    
    for idx, day_data in anomaly_days.iterrows():
        date = day_data['日期']
        
        # 获取该日期的订单数据
        day_df = df[df['日期'].dt.date == date].copy()
        
        # 按订单聚合
        day_orders = day_df.groupby('订单ID').agg({
            '商品实售价': 'sum',
            '利润额': 'sum',
            '物流配送费': 'first',
            '平台佣金': 'first',
            '满减金额': 'first',
            '商品减免金额': 'first',
            '商家代金券': 'first',
            '商家承担部分券': 'first'
        }).reset_index()
        
        # 计算成本结构
        day_orders['活动成本'] = (
            day_orders['满减金额'] + 
            day_orders['商品减免金额'] + 
            day_orders['商家代金券'] + 
            day_orders['商家承担部分券']
        )
        day_orders['订单实际利润'] = (
            day_orders['利润额'] - 
            day_orders['物流配送费'] - 
            day_orders['平台佣金']
        )
        
        # 成本占比分析
        total_sales = day_orders['商品实售价'].sum()
        total_delivery = day_orders['物流配送费'].sum()
        total_commission = day_orders['平台佣金'].sum()
        total_activity = day_orders['活动成本'].sum()
        
        delivery_rate = (total_delivery / total_sales * 100) if total_sales > 0 else 0
        commission_rate = (total_commission / total_sales * 100) if total_sales > 0 else 0
        activity_rate = (total_activity / total_sales * 100) if total_sales > 0 else 0
        
        # 商品级别分析：找出拉低利润的商品
        product_analysis = day_df.groupby('商品名称').agg({
            '商品实售价': 'sum',
            '利润额': 'sum',
            '月售': 'sum'
        }).reset_index()
        product_analysis['商品利润率'] = (
            product_analysis['利润额'] / product_analysis['商品实售价'] * 100
        ).round(2)
        product_analysis = product_analysis.sort_values('商品实售价', ascending=False)
        
        # 找出销售额Top5但利润率低的商品
        top_products = product_analysis.head(5)
        low_margin_products = top_products[top_products['商品利润率'] < avg_profit_rate]
        
        anomaly_details.append({
            '日期': str(date),
            '销售额': day_data['销售额'],
            '总利润': day_data['总利润'],
            '利润率': day_data['利润率'],
            '订单数': day_data['订单数'],
            '配送成本率': delivery_rate,
            '佣金率': commission_rate,
            '活动成本率': activity_rate,
            '问题商品数': len(low_margin_products),
            '问题商品': low_margin_products[['商品名称', '商品利润率', '商品实售价']].to_dict('records') if len(low_margin_products) > 0 else []
        })
    
    return {
        'summary': {
            '平均利润率': avg_profit_rate,
            '利润率标准差': std_profit_rate,
            '异常天数': len(anomaly_days),
            '总天数': len(daily_sales)
        },
        'best_day': {
            '日期': str(best_day['日期']),
            '销售额': best_day['销售额'],
            '利润率': best_day['利润率'],
            '订单数': best_day['订单数']
        },
        'worst_day': {
            '日期': str(worst_day['日期']),
            '销售额': worst_day['销售额'],
            '利润率': worst_day['利润率'],
            '订单数': worst_day['订单数']
        },
        'anomaly_details': anomaly_details
    }


def create_category_pie_chart_echarts(category_sales):
    """创建分类销售占比饼图 - ECharts版本"""
    
    # 格式化数据
    formatted_data = [
        {'name': k, 'value': format_number(v)} 
        for k, v in zip(category_sales.index, category_sales.values)
    ]
    
    option = {
        'title': {
            'text': '🏷️ 商品分类销售占比',
            'left': 'center',
            'top': '3%',
            'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: ¥{c} ({d}%)',
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'borderWidth': 1
        },
        'legend': {
            'orient': 'vertical',
            'left': '5%',
            'top': '15%',
            'textStyle': {'fontSize': 11}
        },
        'series': [
            {
                'name': '销售额',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'center': ['60%', '55%'],
                'data': formatted_data,
                'itemStyle': {
                    'borderRadius': 10,
                    'borderColor': '#fff',
                    'borderWidth': 2
                },
                'label': {
                    'show': True,
                    'formatter': '{b}\n{d}%',
                    'fontSize': 11,
                    'fontWeight': 'bold'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 20,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    },
                    'label': {
                        'show': True,
                        'fontSize': 14,
                        'fontWeight': 'bold'
                    }
                },
                'animationType': 'scale',
                'animationEasing': 'elasticOut',
                'animationDelay': '{dataIndex} * 50'
            }
        ]
    }
    
    return DashECharts(
        option=option,
        style={'height': '400px', 'width': '100%'}
    )


# ==================== 新增：利润分布直方图 (ECharts) ====================
def create_profit_histogram_chart(order_agg):
    """创建订单利润分布直方图 - ECharts 版本"""
    import numpy as np
    
    profit_values = order_agg['订单实际利润'].values
    hist_counts, hist_bins = np.histogram(profit_values, bins=50)
    
    # 格式化数据
    formatted_counts = [format_number(v) for v in hist_counts.tolist()]
    
    # 生成 bin 标签
    bin_labels = [f'{hist_bins[i]:.0f}' for i in range(len(hist_counts))]
    
    option = {
        'title': {'text': '📊 订单利润分布', 'left': 'center', 'textStyle': {'fontSize': 16, 'fontWeight': 'bold', 'color': '#2c3e50'}},
        'tooltip': {
            'trigger': 'axis',
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'textStyle': {'color': '#333'},
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {'left': '10%', 'right': '10%', 'top': '15%', 'bottom': '15%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'data': bin_labels,
            'name': '订单实际利润 (¥)',
            'axisLabel': {'rotate': 45, 'fontSize': 9}
        },
        'yAxis': {
            'type': 'value',
            'name': '订单数量',
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
        },
        'series': [{
            'name': '订单数量',
            'type': 'bar',
            'data': formatted_counts,
            'barWidth': '90%',
            'itemStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': '#2ECC71'},
                        {'offset': 1, 'color': '#27AE60'}
                    ]
                },
                'borderRadius': [4, 4, 0, 0]
            },
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(46,204,113,0.5)'}},
            'animationDelay': '{dataIndex} * 20'
        }],
        'animationEasing': 'elasticOut',
        'animationDuration': 1000
    }
    
    return DashECharts(option=option, style={'height': '100%', 'width': '100%'})


# ==================== 新增：利润区间分布图 (ECharts) ====================
def create_profit_range_chart(order_agg):
    """创建利润区间分布柱状图 - 更直观的分析"""
    import numpy as np
    
    profit_values = order_agg['订单实际利润'].values
    
    # 定义利润区间
    bins = [-np.inf, -100, -50, -20, 0, 20, 50, 100, np.inf]
    labels = ['重度亏损\n(<-100)', '中度亏损\n(-100~-50)', '轻度亏损\n(-50~-20)', 
              '微亏损\n(-20~0)', '微盈利\n(0~20)', '良好盈利\n(20~50)', 
              '优秀盈利\n(50~100)', '超级盈利\n(>100)']
    
    # 统计各区间订单数
    counts, _ = np.histogram(profit_values, bins=bins)
    formatted_counts = [format_number(v) for v in counts.tolist()]
    
    # 根据盈亏设置颜色
    colors = ['#C0392B', '#E74C3C', '#FF6B6B', '#FFA07A',  # 亏损区间：深红到浅红
              '#98FB98', '#2ECC71', '#27AE60', '#229954']  # 盈利区间：浅绿到深绿
    
    # ========== ECharts 版本 ==========
    if ECHARTS_AVAILABLE:
        option = {
        'title': {
            'text': '💰 订单利润区间分布分析',
            'subtext': f'总订单: {len(profit_values)} 笔',
            'left': 'center',
            'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#2c3e50'}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'formatter': '{b}<br/>订单数: {c} 笔<br/>占比: {d}%'
        },
        'grid': {'left': '8%', 'right': '8%', 'top': '20%', 'bottom': '15%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'data': labels,
            'axisLabel': {
                'fontSize': 10,
                'color': '#2c3e50',
                'interval': 0,
                'rotate': 0
            },
            'axisTick': {'show': False},
            'axisLine': {'lineStyle': {'color': '#e0e0e0'}}
        },
        'yAxis': {
            'type': 'value',
            'name': '订单数量',
            'axisLabel': {'fontSize': 11},
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': '#e0e0e0'}}
        },
        'series': [{
            'name': '订单数量',
            'type': 'bar',
            'data': [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(formatted_counts, colors)],
            'barWidth': '70%',
            'label': {
                'show': True,
                'position': 'top',
                'formatter': '{c}',
                'fontSize': 11,
                'fontWeight': 'bold',
                'color': '#333'
            },
            'itemStyle': {
                'borderRadius': [6, 6, 0, 0],
                'shadowColor': 'rgba(0,0,0,0.1)',
                'shadowBlur': 5
            },
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 15,
                    'shadowColor': 'rgba(0,0,0,0.3)'
                }
            }
        }],
        'animationEasing': 'elasticOut',
        'animationDuration': 1200
    }
    
        return DashECharts(option=option, style={'height': '100%', 'width': '100%'})
    
    # ========== Plotly 后备方案 ==========
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labels,
        y=counts.tolist(),
        marker=dict(color=colors),
        text=formatted_counts,
        textposition='outside',
        textfont=dict(size=11, color='#333'),
        hovertemplate='<b>%{x}</b><br>订单数: %{y} 笔<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f'💰 订单利润区间分布分析<br><sub>总订单: {len(profit_values)} 笔</sub>',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            tickangle=0,
            tickfont=dict(size=10, color='#2c3e50')
        ),
        yaxis=dict(
            title='订单数量',
            tickfont=dict(size=11),
            showgrid=True,
            gridcolor='rgba(224,224,224,0.5)'
        ),
        height=380,
        margin=dict(l=60, r=40, t=80, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x'
    )
    
    return wrap_chart_component(fig, height='450px')


# ==================== 新增：通用横向排行榜 (ECharts) ====================
def create_horizontal_ranking_chart(data_df, name_field, value_field, title='排行榜', color_scheme='blue', limit=20):
    """
    创建通用横向柱状图排行榜 - ECharts 版本
    
    Args:
        data_df: DataFrame 数据
        name_field: 名称字段
        value_field: 数值字段
        title: 图表标题
        color_scheme: 颜色方案 (blue/green/red/orange/purple)
        limit: 显示前N名
    """
    # 取前N名
    top_data = data_df.nlargest(limit, value_field)
    
    # 颜色方案
    colors = {
        'blue': ['#4A90E2', '#2E5C8A'],
        'green': ['#2ECC71', '#27AE60'],
        'red': ['#FF6B6B', '#E74C3C'],
        'orange': ['#FF7F0E', '#E67E22'],
        'purple': ['#9B59B6', '#8E44AD']
    }
    color_pair = colors.get(color_scheme, colors['blue'])
    
    option = {
        'title': {'text': title, 'left': 'center', 'textStyle': {'fontSize': 16, 'fontWeight': 'bold', 'color': '#2c3e50'}},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'textStyle': {'color': '#333'}
        },
        'grid': {'left': '25%', 'right': '10%', 'top': '12%', 'bottom': '8%', 'containLabel': False},
        'xAxis': {
            'type': 'value',
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}},
            'axisLabel': {'fontSize': 10}
        },
        'yAxis': {
            'type': 'category',
            'data': top_data[name_field].tolist()[::-1],
            'axisLabel': {'fontSize': 10, 'interval': 0}
        },
        'series': [{
            'name': value_field,
            'type': 'bar',
            'data': top_data[value_field].tolist()[::-1],
            'barWidth': '60%',
            'itemStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                    'colorStops': [
                        {'offset': 0, 'color': color_pair[0]},
                        {'offset': 1, 'color': color_pair[1]}
                    ]
                },
                'borderRadius': [0, 8, 8, 0],
                'shadowColor': f'rgba({int(color_pair[0][1:3], 16)},{int(color_pair[0][3:5], 16)},{int(color_pair[0][5:7], 16)},0.3)',
                'shadowBlur': 10
            },
            'label': {
                'show': True,
                'position': 'right',
                'formatter': '{c}',
                'fontSize': 10,
                'fontWeight': 'bold',
                'color': '#2c3e50'
            },
            'emphasis': {'itemStyle': {'shadowBlur': 20}},
            'animationDelay': '{dataIndex} * 50'
        }],
        'animationEasing': 'elasticOut',
        'animationDuration': 1200
    }
    
    return DashECharts(option=option, style={'height': f'{max(400, limit * 25)}px', 'width': '100%'})


# ==================== 公共计算函数 ====================

def calculate_order_metrics(df):
    """
    统一的订单指标计算函数（Tab 1和Tab 2共用）
    
    核心计算逻辑:
    1. 订单级聚合（订单级字段用first，商品级字段用sum）
    2. 计算商家活动成本
    3. 计算订单总收入
    4. 计算订单实际利润 = 利润额 - 物流配送费 - 平台佣金
    
    Args:
        df: 原始数据DataFrame（必须包含订单ID字段）
        
    Returns:
        order_agg: 订单级聚合数据（包含订单实际利润等计算字段）
    """
    if '订单ID' not in df.columns:
        raise ValueError("数据缺少订单ID字段")
    
    # ===== Step 1: 订单级聚合 =====
    order_agg = df.groupby('订单ID').agg({
        '商品实售价': 'sum',              # 商品销售额
        '商品采购成本': 'sum',            # 商品成本
        '利润额': 'sum',                  # ✅ 原始利润额（未扣除配送成本和平台佣金）
        '月售': 'sum',                    # 销量
        '用户支付配送费': 'first',        # 订单级字段
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',        # 🔧 新增字段
        '平台佣金': 'first',
        '打包袋金额': 'first'
    }).reset_index()
    
    # ===== Step 2: 计算商家活动成本 =====
    order_agg['商家活动成本'] = (
        order_agg['满减金额'] + 
        order_agg['商品减免金额'] + 
        order_agg['商家代金券'] +
        order_agg['商家承担部分券']  # 🔧 包含商家承担部分券
    )
    
    # ===== Step 3: 计算订单总收入 =====
    order_agg['订单总收入'] = (
        order_agg['商品实售价'] + 
        order_agg['打包袋金额'] + 
        order_agg['用户支付配送费']
    )
    
    # ===== Step 4: 计算订单实际利润（核心公式）=====
    # 公式: 订单实际利润 = 利润额 - 物流配送费 - 平台佣金
    # 说明: 利润额已包含（商品销售 - 成本 - 活动成本）
    order_agg['订单实际利润'] = (
        order_agg['利润额'] - 
        order_agg['物流配送费'] - 
        order_agg['平台佣金']
    )
    
    return order_agg


# ==================== Tab 1-7 内容回调 ====================

# Tab 1: 订单数据概览
@app.callback(
    Output('tab-1-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('data-update-trigger', 'data')]
)
def render_tab1_content(active_tab, trigger):
    """渲染Tab 1：订单数据概览（✅ 使用统一计算函数）"""
    if active_tab != 'tab-1':
        raise PreventUpdate
    
    # 添加数据信息卡片（通过全局回调更新）
    data_info_placeholder = html.Div(id='tab1-data-info')
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Container([
            data_info_placeholder,
            dbc.Alert("⚠️ 未找到数据，请检查数据文件", color="warning")
        ])
    
    df = GLOBAL_DATA.copy()
    
    # ========== 步骤1：使用统一计算函数 ==========
    try:
        order_agg = calculate_order_metrics(df)  # ✅ 调用公共函数
    except ValueError as e:
        return dbc.Container([
            data_info_placeholder,
            dbc.Alert(f"❌ {str(e)}", color="danger")
        ])
    
    # ========== 步骤2：计算汇总指标 ==========
    total_orders = len(order_agg)
    total_sales = order_agg['商品实售价'].sum()
    total_revenue = order_agg['订单总收入'].sum()
    total_profit = order_agg['订单实际利润'].sum()
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # ✅ 修正：动销商品数 = 有销量的商品（月售>0）
    if '商品名称' in df.columns and '月售' in df.columns:
        total_products = df[df['月售'] > 0]['商品名称'].nunique()
    else:
        total_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    # 盈利订单分析
    profitable_orders = (order_agg['订单实际利润'] > 0).sum()
    profitable_rate = (profitable_orders / total_orders * 100) if total_orders > 0 else 0
    
    return html.Div([
        # 数据信息占位符（由全局回调更新）
        data_info_placeholder,
        
        html.H3("📊 订单数据概览", className="mb-4"),
        
        # 关键指标卡片
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📦 订单总数", className="card-title"),
                        html.H2(f"{total_orders:,}", className="text-primary"),
                        html.P("笔", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💰 商品销售额", className="card-title"),
                        html.H2(f"¥{total_sales:,.0f}", className="text-success"),
                        html.P("商品实售价总和", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💵 订单总收入", className="card-title"),
                        html.H2(f"¥{total_revenue:,.0f}", className="text-info"),
                        html.P("含配送费+打包费", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💎 总利润", className="card-title"),
                        html.H2(f"¥{total_profit:,.0f}", className="text-warning"),
                        html.P("元", className="text-muted")
                    ])
                ], className="text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🛒 平均客单价", className="card-title"),
                        html.H2(f"¥{avg_order_value:.2f}", className="text-danger"),
                        html.P("商品销售额/订单数", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📈 盈利订单占比", className="card-title"),
                        html.H2(f"{profitable_rate:.1f}%", className="text-success"),
                        html.P(f"{profitable_orders:,}/{total_orders:,}", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🏷️ 动销商品数", className="card-title"),
                        html.H2(f"{total_products:,}", className="text-secondary"),
                        html.P("有销量的SKU", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=2)
        ], className="mb-4"),
        
        # ✨ 新增: 健康度预警组件(基于业务逻辑)
        html.Div(id='health-warning-container', children=(
            _create_health_warnings(total_sales, total_profit, order_agg) 
            if BUSINESS_CONTEXT_AVAILABLE else []
        )),
        
        dbc.Button(
            "📊 查看详细分析",
            id="btn-show-detail-analysis",
            color="primary",
            size="lg",
            className="w-100 mb-4"
        ),
        
        html.Div(id='tab1-detail-content', style={'display': 'none'})
    ])


# Tab 1 详细分析
@app.callback(
    [Output('tab1-detail-content', 'children'),
     Output('tab1-detail-content', 'style')],
    Input('btn-show-detail-analysis', 'n_clicks'),
    prevent_initial_call=True
)
def show_tab1_detail_analysis(n_clicks):
    """显示Tab 1详细分析"""
    if not n_clicks:
        raise PreventUpdate
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Alert("⚠️ 数据不可用", color="warning"), {'display': 'block'}
    
    df = GLOBAL_DATA.copy()
    charts = []
    
    # ========== 🔍 调试日志：检查原始数据 ==========
    print("\n" + "="*80)
    print("🔍 [调试] show_tab1_detail_analysis 函数调用")
    print(f"📊 GLOBAL_DATA 数据量: {len(df)} 行")
    print(f"📋 GLOBAL_DATA 字段: {df.columns.tolist()}")
    
    if '商品采购成本' in df.columns:
        print(f"✅ '商品采购成本' 字段存在")
        print(f"   数据类型: {df['商品采购成本'].dtype}")
        print(f"   总和: ¥{df['商品采购成本'].sum():,.2f}")
        print(f"   非零数量: {(df['商品采购成本'] > 0).sum()} / {len(df)}")
        print(f"   NaN数量: {df['商品采购成本'].isna().sum()}")
        print(f"   样本数据（前5行）:")
        print(df[['商品名称', '商品采购成本', '商品实售价']].head(5).to_string())
    else:
        print(f"❌ '商品采购成本' 字段不存在！")
    
    # ========== 🔍 调试：检查营销活动字段 ==========
    print("\n🔍 [调试] 营销活动字段检查（聚合前）:")
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    for field in marketing_fields:
        if field in df.columns:
            field_sum = df[field].fillna(0).sum()
            non_zero_count = (df[field].fillna(0) > 0).sum()
            print(f"   ✅ {field}: 总和=¥{field_sum:,.2f}, 非零行数={non_zero_count}/{len(df)}")
        else:
            print(f"   ❌ {field}: 字段不存在！")
    print("="*80 + "\n")
    
    # ========== 重新计算订单聚合数据（与render_tab1_content保持一致）==========
    order_agg = df.groupby('订单ID').agg({
        '商品实售价': 'sum',
        '商品采购成本': 'sum',
        '利润额': 'sum',  # ✅ 原始利润额（未扣除配送成本和平台佣金）
        '月售': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',  # 🔧 添加：商家承担部分券
        '平台佣金': 'first',
        '打包袋金额': 'first'
    }).reset_index()
    
    # 计算订单级成本和收入
    # 🔧 删除错误的配送成本计算，直接使用物流配送费
    # 物流配送费 = 商家实际支付给骑手的配送成本
    
    order_agg['商家活动成本'] = (
        order_agg['满减金额'] + 
        order_agg['商品减免金额'] + 
        order_agg['商家代金券'] +
        order_agg['商家承担部分券']  # 🔧 添加：商家承担部分券
    )
    
    order_agg['订单总收入'] = (
        order_agg['商品实售价'] + 
        order_agg['打包袋金额'] + 
        order_agg['用户支付配送费']
    )
    
    # 🔧 修改：使用利润额 - 物流配送费 - 平台佣金 计算实际利润
    # 利润额 = 商品销售额 - 商品成本 - 活动成本（已在原始表中计算）
    # 实际利润 = 利润额 - 物流配送费 - 平台佣金
    order_agg['订单实际利润'] = (
        order_agg['利润额'] - 
        order_agg['物流配送费'] - 
        order_agg['平台佣金']
    )
    
    # 计算汇总指标
    total_orders = len(order_agg)
    total_sales = order_agg['商品实售价'].sum()
    total_revenue = order_agg['订单总收入'].sum()
    total_profit = order_agg['订单实际利润'].sum()
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    profitable_orders = (order_agg['订单实际利润'] > 0).sum()
    profitable_rate = (profitable_orders / total_orders * 100) if total_orders > 0 else 0
    
    # ========== 🔍 调试日志：订单聚合后的数据 ==========
    print("\n" + "="*80)
    print("🔍 [调试] 订单聚合完成")
    print(f"📊 订单数: {total_orders}")
    print(f"💰 商品销售额: ¥{total_sales:,.2f}")
    print(f"💵 订单总收入: ¥{total_revenue:,.2f}")
    print(f"💎 总利润: ¥{total_profit:,.2f}")
    print(f"📈 利润率: {profit_rate:.2f}%")
    print(f"\n🔍 order_agg 字段: {order_agg.columns.tolist()}")
    
    if '商品采购成本' in order_agg.columns:
        product_cost_sum = order_agg['商品采购成本'].sum()
        print(f"\n✅ order_agg 中'商品采购成本'字段存在")
        print(f"   总和: ¥{product_cost_sum:,.2f}")
        print(f"   非零订单数: {(order_agg['商品采购成本'] > 0).sum()}")
        print(f"   样本数据（前5个订单）:")
        print(order_agg[['订单ID', '商品采购成本', '商品实售价', '订单实际利润']].head(5).to_string())
    else:
        print(f"\n❌ order_agg 中'商品采购成本'字段不存在！")
    print("="*80 + "\n")
    
    # 1. 日期趋势图
    if '日期' in df.columns:
        # 先按日期和订单ID聚合，计算每个订单的实际利润
        daily_order_agg = df.groupby([df['日期'].dt.date, '订单ID']).agg({
            '商品实售价': 'sum',
            '利润额': 'sum',
            '物流配送费': 'first',
            '平台佣金': 'first'
        }).reset_index()
        
        # 计算订单实际利润
        daily_order_agg['订单实际利润'] = (
            daily_order_agg['利润额'] - 
            daily_order_agg['物流配送费'] - 
            daily_order_agg['平台佣金']
        )
        
        # 再按日期聚合
        daily_sales = daily_order_agg.groupby('日期').agg({
            '商品实售价': 'sum',
            '订单实际利润': 'sum',
            '订单ID': 'nunique'
        }).reset_index()
        daily_sales.columns = ['日期', '销售额', '总利润', '订单数']
        
        if ECHARTS_AVAILABLE:
            # 使用 ECharts
            chart_component = create_sales_trend_chart_echarts(daily_sales)
        else:
            # Plotly 备份
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_sales['日期'],
                y=daily_sales['销售额'],
                mode='lines+markers',
                name='销售额',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31,119,180,0.2)',
                yaxis='y1'
            ))
            fig_trend.add_trace(go.Scatter(
                x=daily_sales['日期'],
                y=daily_sales['总利润'],
                mode='lines+markers',
                name='总利润',
                line=dict(color='#2ca02c', width=2),
                yaxis='y1'
            ))
            fig_trend.add_trace(go.Scatter(
                x=daily_sales['日期'],
                y=daily_sales['订单数'],
                mode='lines+markers',
                name='订单数',
                line=dict(color='#ff7f0e', width=2),
                yaxis='y2'
            ))
            
            # 计算订单数的范围，优化右Y轴显示
            order_min = daily_sales['订单数'].min()
            order_max = daily_sales['订单数'].max()
            order_range = order_max - order_min
            order_axis_min = max(0, order_min - order_range * 0.2)
            order_axis_max = order_max + order_range * 0.2
            
            fig_trend.update_layout(
                title='📈 销售趋势分析',
                xaxis_title='日期',
                yaxis=dict(title='金额 (¥)', side='left'),
                yaxis2=dict(
                    title='订单数', 
                    side='right', 
                    overlaying='y',
                    range=[order_axis_min, order_axis_max]  # 动态设置范围
                ),
                hovermode='x unified',
                height=400
            )
            chart_component = dcc.Graph(figure=fig_trend, config={'displayModeBar': False})
        
        # ========== 添加智能异常分析面板 ==========
        anomaly_analysis = analyze_daily_anomalies(df, daily_sales)
        
        # 调试输出
        print(f"🔍 异常分析结果: 异常天数={len(anomaly_analysis['anomaly_details'])}, 详情数量={len(anomaly_analysis.get('anomaly_details', []))}")
        if anomaly_analysis['anomaly_details']:
            print(f"   第一个异常日期: {anomaly_analysis['anomaly_details'][0]['日期']}")
        
        # 创建异常分析卡片
        anomaly_cards = []
        
        # 1. 概览卡片
        summary = anomaly_analysis['summary']
        best = anomaly_analysis['best_day']
        worst = anomaly_analysis['worst_day']
        
        anomaly_cards.append(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 利润率概览", className="card-title mb-3"),
                            html.Div([
                                html.P([
                                    html.Strong("平均利润率: "),
                                    html.Span(f"{summary['平均利润率']:.2f}%", className="text-primary")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("利润率波动: "),
                                    html.Span(f"±{summary['利润率标准差']:.2f}%", className="text-muted")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("异常天数: "),
                                    html.Span(
                                        f"{summary['异常天数']}/{summary['总天数']} 天", 
                                        className="text-danger" if summary['异常天数'] > summary['总天数'] * 0.3 else "text-warning"
                                    )
                                ], className="mb-0")
                            ])
                        ])
                    ], className="h-100")
                ], md=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🏆 最佳表现日", className="card-title mb-3 text-success"),
                            html.Div([
                                html.P([
                                    html.Strong("日期: "),
                                    html.Span(best['日期'])
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("利润率: "),
                                    html.Span(f"{best['利润率']:.2f}%", className="text-success fs-5")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("销售额: "),
                                    f"¥{best['销售额']:,.0f} ({best['订单数']:.0f}单)"
                                ], className="mb-0 small text-muted")
                            ])
                        ])
                    ], className="h-100 border-success")
                ], md=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("⚠️ 最差表现日", className="card-title mb-3 text-danger"),
                            html.Div([
                                html.P([
                                    html.Strong("日期: "),
                                    html.Span(worst['日期'])
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("利润率: "),
                                    html.Span(f"{worst['利润率']:.2f}%", className="text-danger fs-5")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("销售额: "),
                                    f"¥{worst['销售额']:,.0f} ({worst['订单数']:.0f}单)"
                                ], className="mb-0 small text-muted")
                            ])
                        ])
                    ], className="h-100 border-danger")
                ], md=4)
            ], className="mb-4")
        )
        
        # 2. 异常日期详细分析
        if anomaly_analysis['anomaly_details']:
            print(f"📊 准备渲染 {len(anomaly_analysis['anomaly_details'])} 个异常日期的折叠面板...")
            anomaly_cards.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🔍 异常日期深度分析", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("以下日期的利润率明显低于平均水平，需要重点关注：", className="text-muted mb-3"),
                        
                        # 为每个异常日期创建折叠面板
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.Div([
                                    # 基本指标
                                    dbc.Row([
                                        dbc.Col([
                                            html.Strong("📈 业绩指标:"),
                                            html.Ul([
                                                html.Li(f"销售额: ¥{detail['销售额']:,.0f}"),
                                                html.Li(f"总利润: ¥{detail['总利润']:,.0f}"),
                                                html.Li([
                                                    f"利润率: ",
                                                    html.Span(f"{detail['利润率']:.2f}%", className="text-danger fw-bold"),
                                                    f" (平均: {summary['平均利润率']:.2f}%)"
                                                ]),
                                                html.Li(f"订单数: {detail['订单数']:.0f}单")
                                            ])
                                        ], md=6),
                                        
                                        dbc.Col([
                                            html.Strong("💰 成本结构分析:"),
                                            html.Ul([
                                                html.Li([
                                                    f"配送成本率: ",
                                                    html.Span(
                                                        f"{detail['配送成本率']:.2f}%",
                                                        className="text-warning" if detail['配送成本率'] > 5 else "text-muted"
                                                    )
                                                ]),
                                                html.Li([
                                                    f"平台佣金率: ",
                                                    html.Span(f"{detail['佣金率']:.2f}%", className="text-muted")
                                                ]),
                                                html.Li([
                                                    f"活动成本率: ",
                                                    html.Span(
                                                        f"{detail['活动成本率']:.2f}%",
                                                        className="text-danger" if detail['活动成本率'] > 10 else "text-warning" if detail['活动成本率'] > 5 else "text-muted"
                                                    )
                                                ])
                                            ])
                                        ], md=6)
                                    ], className="mb-3"),
                                    
                                    # 问题商品分析
                                    html.Div([
                                        html.Strong("🎯 问题商品定位:"),
                                        html.Div([
                                            dbc.Alert([
                                                html.Strong(f"发现 {detail['问题商品数']} 个低利润率商品"),
                                                html.Br(),
                                                html.Small("这些商品销售额高但利润率低，拉低了整体盈利水平", className="text-muted")
                                            ], color="warning", className="mb-2") if detail['问题商品数'] > 0 else 
                                            dbc.Alert("未发现明显的问题商品", color="info", className="mb-2"),
                                            
                                            # 显示问题商品列表
                                            html.Div([
                                                dbc.Table([
                                                    html.Thead([
                                                        html.Tr([
                                                            html.Th("商品名称"),
                                                            html.Th("商品利润率"),
                                                            html.Th("销售额")
                                                        ])
                                                    ]),
                                                    html.Tbody([
                                                        html.Tr([
                                                            html.Td(prod['商品名称'][:30] + '...' if len(prod['商品名称']) > 30 else prod['商品名称']),
                                                            html.Td(f"{prod['商品利润率']:.2f}%", className="text-danger"),
                                                            html.Td(f"¥{prod['商品实售价']:,.0f}")
                                                        ]) for prod in detail['问题商品'][:5]  # 只显示前5个
                                                    ])
                                                ], bordered=True, hover=True, size="sm")
                                            ]) if detail['问题商品'] else None
                                        ])
                                    ], className="mt-3"),
                                    
                                    # 诊断建议
                                    html.Div([
                                        html.Strong("💡 诊断建议:"),
                                        html.Ul([
                                            item for item in [
                                                html.Li("活动成本过高，建议优化促销策略") if detail['活动成本率'] > 10 else None,
                                                html.Li("配送成本偏高，考虑优化配送策略或调整起送价") if detail['配送成本率'] > 5 else None,
                                                html.Li(f"有{detail['问题商品数']}个商品利润率低，建议调整定价或减少促销") if detail['问题商品数'] > 0 else None,
                                                html.Li("整体成本结构合理，可能是偶发性波动") if detail['活动成本率'] < 10 and detail['配送成本率'] < 5 and detail['问题商品数'] == 0 else None
                                            ] if item is not None
                                        ])
                                    ], className="mt-3")
                                ])
                            ], title=f"📅 {detail['日期']} - 利润率 {detail['利润率']:.2f}% ({'低' if detail['利润率'] < summary['平均利润率'] - summary['利润率标准差'] else '偏低'})")
                            for detail in anomaly_analysis['anomaly_details'][:10]  # 最多显示10个异常日期
                        ], start_collapsed=True, always_open=False)
                    ])
                ], className="mb-4")
            )
        else:
            anomaly_cards.append(
                dbc.Alert([
                    html.H5("✅ 利润率表现稳定", className="alert-heading"),
                    html.P("未检测到明显的利润率异常，整体经营状况良好！")
                ], color="success", className="mb-4")
            )
        
        charts.append(dbc.Card([
            dbc.CardBody([chart_component])
        ], className="mb-4"))
        
        # 添加异常分析卡片
        charts.extend(anomaly_cards)
    
    # 2. 分类销售占比
    if '一级分类名' in df.columns:
        category_sales = df.groupby('一级分类名')['商品实售价'].sum().sort_values(ascending=False)
        
        if ECHARTS_AVAILABLE:
            # 使用 ECharts
            chart_component = create_category_pie_chart_echarts(category_sales)
        else:
            # Plotly 备份
            fig_category = go.Figure(data=[go.Pie(
                labels=category_sales.index,
                values=category_sales.values,
                hole=0.4,
                textinfo='label+percent',
                textposition='outside'
            )])
            fig_category.update_layout(
                title='🏷️ 商品分类销售占比',
                height=400
            )
            chart_component = dcc.Graph(figure=fig_category, config={'displayModeBar': False})
        
        charts.append(dbc.Card([
            dbc.CardHeader(html.H5("🏷️ 商品分类销售占比", className="mb-0")),
            dbc.CardBody([chart_component])
        ], className="mb-4 shadow-sm"))
    
    # ==================== 4. 成本结构分析（使用订单级聚合，业务逻辑公式）====================
    
    # 使用订单聚合数据计算成本（避免重复）
    product_cost = order_agg['商品采购成本'].sum()
    delivery_cost = order_agg['物流配送费'].sum()  # 🔧 改为使用物流配送费
    marketing_cost = order_agg['商家活动成本'].sum()
    platform_commission = order_agg['平台佣金'].sum()
    
    # ========== 🔍 调试日志：成本结构计算 ==========
    print("\n" + "="*80)
    print("🔍 [调试] 成本结构分析")
    print(f"💰 商品成本: ¥{product_cost:,.2f}")
    print(f"🚚 物流配送费: ¥{delivery_cost:,.2f}")
    print(f"🎁 活动营销成本: ¥{marketing_cost:,.2f}")
    print(f"💳 平台佣金: ¥{platform_commission:,.2f}")
    print(f"\n🔍 成本详细检查:")
    print(f"   order_agg['商品采购成本'].fillna(0).sum() = ¥{order_agg['商品采购成本'].fillna(0).sum():,.2f}")
    print(f"   order_agg['物流配送费'].fillna(0).sum() = ¥{order_agg['物流配送费'].fillna(0).sum():,.2f}")
    print(f"   order_agg['商家活动成本'].fillna(0).sum() = ¥{order_agg['商家活动成本'].fillna(0).sum():,.2f}")
    print(f"   order_agg['平台佣金'].fillna(0).sum() = ¥{order_agg['平台佣金'].fillna(0).sum():,.2f}")
    print("="*80 + "\n")
    
    # 成本结构卡片
    cost_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📦 商品成本", className="card-title text-muted"),
                    html.H3(f"¥{product_cost:,.2f}", className="text-primary"),
                    html.P("采购成本总额", className="text-muted small")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🚚 物流配送费", className="card-title text-muted"),
                    html.H3(f"¥{delivery_cost:,.2f}", className="text-warning"),
                    html.P("支付给骑手的配送费", className="text-muted small"),
                    html.Small("(商家实际配送成本)", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🎁 商家活动", className="card-title text-muted"),
                    html.H3(f"¥{marketing_cost:,.2f}", className="text-danger"),
                    html.P("促销活动支出", className="text-muted small"),
                    html.Small("(满减+代金券等)", className="text-muted")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💼 平台佣金", className="card-title text-muted"),
                    html.H3(f"¥{platform_commission:,.2f}", className="text-info"),
                    html.P("平台服务费", className="text-muted small")
                ])
            ], className="text-center shadow-sm")
        ], md=3)
    ], className="mb-4")
    
    # 成本结构饼图 - 统一使用 Plotly
    cost_structure_chart = dcc.Graph(
        figure=go.Figure(data=[go.Pie(
            labels=['商品成本', '物流配送费', '商家活动', '平台佣金'],
            values=[product_cost, delivery_cost, marketing_cost, platform_commission],
            hole=0.4,
            textinfo='label+percent+value',
            texttemplate='%{label}<br>¥%{value:,.0f}<br>(%{percent})',
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#d62728', '#2ca02c'])
        )]).update_layout(
            title='成本构成占比',
            height=400,
            showlegend=True
        ),
        config={'displayModeBar': False}
    )
    
    charts.append(dbc.Card([
        dbc.CardHeader(html.H4("💸 成本结构分析 (标准业务逻辑)", className="mb-0")),
        dbc.CardBody([
            cost_cards,
            # 成本占比饼图
            cost_structure_chart,
            
            # ========== 新增:商品成本分类分析 和 商家活动补贴分析 ==========
            html.Hr(className="my-4"),
            html.H5("📊 成本细分分析", className="mb-4 text-center", style={'color': '#2c3e50', 'fontWeight': 'bold', 'fontSize': '1.3rem'}),
            dbc.Row([
                # 左侧：商品成本分类分析
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6("📦 商品成本分类排行", className="mb-0", style={'color': '#2E5C8A', 'fontWeight': 'bold'})
                        ], style={'background': 'linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)', 'border': 'none', 'borderRadius': '12px 12px 0 0'}),
                        dbc.CardBody([
                            # 智能选择：ECharts 或 Plotly（函数内部已处理返回完整组件）
                            create_category_cost_chart(df)
                        ], style={'padding': '1.5rem', 'background': 'white'})
                    ], className="shadow-lg h-100", style={
                        'border': 'none',
                        'borderRadius': '12px',
                        'overflow': 'hidden',
                        'transition': 'transform 0.3s ease, box-shadow 0.3s ease'
                    })
                ], md=6, className="mb-4"),
                # 右侧：商家活动补贴分析
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6("🎁 商家活动补贴分析", className="mb-0", style={'color': '#E74C3C', 'fontWeight': 'bold'})
                        ], style={'background': 'linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)', 'border': 'none', 'borderRadius': '12px 12px 0 0'}),
                        dbc.CardBody([
                            # 智能选择：ECharts 或 Plotly（函数内部已处理返回完整组件）
                            create_marketing_activity_chart(order_agg)
                        ], style={'padding': '1.5rem', 'background': 'white'})
                    ], className="shadow-lg h-100", style={
                        'border': 'none',
                        'borderRadius': '12px',
                        'overflow': 'hidden',
                        'transition': 'transform 0.3s ease, box-shadow 0.3s ease'
                    })
                ], md=6, className="mb-4")
            ], className="g-4")  # 增大栅格间距
        ])
    ], className="mb-4"))
    
    # ==================== 5. 利润率详细分析（使用订单聚合数据）====================
    
    # 使用订单聚合数据
    profit_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💎 总利润额", className="card-title text-muted"),
                    html.H3(f"¥{total_profit:,.2f}", className="text-success"),
                    html.P("订单实际利润总和", className="text-muted small")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📊 利润率", className="card-title text-muted"),
                    html.H3(f"{profit_rate:.2f}%", className="text-warning"),
                    html.P("利润/销售额", className="text-muted small")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📈 盈利订单数", className="card-title text-muted"),
                    html.H3(f"{profitable_orders:,}", className="text-info"),
                    html.P(f"占比 {profitable_rate:.1f}%", className="text-muted small")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💰 平均订单利润", className="card-title text-muted"),
                    html.H3(f"¥{total_profit/total_orders:.2f}", className="text-primary"),
                    html.P("总利润/订单数", className="text-muted small")
                ])
            ], className="text-center shadow-sm")
        ], md=3)
    ], className="mb-4")
    
    charts.append(dbc.Card([
        dbc.CardHeader(html.H4("💰 利润率详细分析 (标准业务逻辑)", className="mb-0")),
        dbc.CardBody([
            profit_cards,
            # 利润区间分布图 - 智能选择（函数内部已处理 ECharts/Plotly 切换）
            create_profit_range_chart(order_agg) if order_agg is not None and len(order_agg) > 0 else html.Div(
                dbc.Alert("暂无订单利润数据", color="info"),
                style={'padding': '2rem', 'textAlign': 'center'}
            )
        ])
    ], className="mb-4"))
    
    # ==================== 6. 业务逻辑说明（与Streamlit版一致）====================
    business_logic_explanation = dbc.Card([
        dbc.CardHeader(html.H5("📄 标准业务逻辑说明", className="mb-0")),
        dbc.CardBody([
            html.H6("本看板采用的标准业务逻辑:", className="text-primary mb-3"),
            html.Ol([
                html.Li([
                    html.Strong("预估订单收入 = "),
                    "(订单零售额 + 打包费 - 商家活动支出 - 平台佣金 + 用户支付配送费)"
                ]),
                html.Li([
                    html.Strong("商家活动支出 = "),
                    "(配送费减免金额 + 满减金额 + 商品减免金额 + 商家代金券)"
                ]),
                html.Li([
                    html.Strong("物流配送费 = "),
                    "商家支付给骑手的配送费用",
                    html.Br(),
                    html.Small("说明：这是商家在配送环节的实际支出", className="text-muted")
                ]),
                html.Li([
                    html.Strong("订单实际利润 = "),
                    "利润额（原始表）- 物流配送费 - 平台佣金",
                    html.Br(),
                    html.Small("说明：利润额已包含商品销售额 - 商品成本 - 活动成本", className="text-muted text-primary")
                ])
            ], className="mb-3"),
            html.Hr(),
            html.H6("字段含义:", className="text-primary mb-2"),
            html.Ul([
                html.Li([html.Strong("商品实售价:"), " 商品在前端展示的原价"]),
                html.Li([html.Strong("用户支付金额:"), " 用户实际支付价格 (考虑各种补贴活动)"]),
                html.Li([html.Strong("利润额:"), " 原始表中的利润字段，已扣除商品成本和活动成本，但未扣除配送费和佣金"]),
                html.Li([html.Strong("同一订单ID多行:"), " 每行代表一个商品SKU，订单级字段会重复显示"])
            ])
        ])
    ], className="mb-4")
    
    charts.append(business_logic_explanation)
    
    return html.Div(charts), {'display': 'block'}


# ==================== Tab 2: 商品分析（完整功能）====================

def generate_quadrant_scatter_chart(product_agg, profit_threshold, sales_threshold):
    """生成四象限散点图"""
    try:
        print("\n🎨 [生成四象限散点图] 开始...")
        print(f"   商品总数: {len(product_agg)}")
        print(f"   利润率范围: {product_agg['利润率'].min():.2f} ~ {product_agg['利润率'].max():.2f}")
        print(f"   动销指数范围: {product_agg['动销指数'].min():.3f} ~ {product_agg['动销指数'].max():.3f}")
        print(f"   销售额范围: {product_agg['销售额'].min():.0f} ~ {product_agg['销售额'].max():.0f}")
        
        # 按象限分组准备数据
        quadrant_colors = {
            '🌟 高利润高动销': '#28a745',
            '⚠️ 高利润低动销': '#ffc107',
            '🚀 低利润高动销': '#17a2b8',
            '❌ 低利润低动销': '#dc3545'
        }
        
        # 为每个象限创建一个系列
        series_list = []
        for quadrant, color in quadrant_colors.items():
            df_quadrant = product_agg[product_agg['象限分类'] == quadrant]
            if len(df_quadrant) > 0:
                scatter_data = []
                for _, row in df_quadrant.iterrows():
                    # ✅ 跳过无效数据和极端值
                    # 1. 检查是否为有限数值
                    # 2. 销售额必须>0
                    # 3. 利润率在合理范围内（-100% ~ 200%）
                    if (
                        np.isfinite(row['动销指数']) and 
                        np.isfinite(row['利润率']) and 
                        np.isfinite(row['销售额']) and
                        row['销售额'] > 0 and
                        -100 <= row['利润率'] <= 200  # ✅ 过滤极端利润率
                    ):
                        # ✅ 构建包含健康度信息的数据点
                        health_status = row.get('盈利健康度', '未知')
                        profit_order_ratio = row.get('盈利订单占比', 0)
                        
                        scatter_data.append({
                            'name': f"{row['商品名称']}\n{health_status} ({profit_order_ratio:.0f}%订单盈利)",
                            'value': [
                                round(float(row['动销指数']), 3),
                                round(float(row['利润率']), 2),
                                round(float(row['销售额']), 0),
                                round(float(profit_order_ratio), 1)  # 第4个值：盈利订单占比
                            ],
                            'itemStyle': {
                                'borderWidth': 2 if health_status == '🔴 依赖大单' else 0,
                                'borderColor': '#ff0000' if health_status == '🔴 依赖大单' else None
                            }
                        })
                
                print(f"   {quadrant}: {len(scatter_data)} 个有效商品 (原始: {len(df_quadrant)}个)")
                if len(scatter_data) > 0:
                    print(f"      样例数据: {scatter_data[0]}")
                
                # ✅ 只有当有数据时才添加series
                if len(scatter_data) > 0:
                    series_list.append({
                        'name': quadrant,
                        'type': 'scatter',
                        'data': scatter_data,
                        'symbolSize': 15,  # ✅ 临时使用固定大小测试
                        'itemStyle': {'color': color},
                        'emphasis': {
                            'focus': 'series',
                            'label': {
                                'show': True,
                                'formatter': '{b}',
                                'position': 'top'
                            }
                        }
                    })
        
        if not ECHARTS_AVAILABLE or len(series_list) == 0:
            print(f"   ⚠️ 无法生成图表: ECHARTS_AVAILABLE={ECHARTS_AVAILABLE}, series数量={len(series_list)}")
            return html.Div("暂无数据或ECharts不可用")
        
        print(f"   ✅ 成功生成 {len(series_list)} 个系列")
        print(f"   📊 每个系列的数据点数量: {[len(s['data']) for s in series_list]}")
        if len(series_list) > 0 and len(series_list[0]['data']) > 0:
            print(f"   🔍 第一个系列的前3个数据点:")
            for i, point in enumerate(series_list[0]['data'][:3]):
                print(f"      [{i}] {point}")
        
        # 添加阈值线到第一个系列
        if len(series_list) > 0:
            series_list[0]['markLine'] = {
                'silent': True,
                'lineStyle': {
                    'color': '#999',
                    'type': 'solid',
                    'width': 2
                },
                'data': [
                    {'xAxis': sales_threshold, 'label': {'formatter': '动销阈值', 'position': 'end'}},
                    {'yAxis': profit_threshold, 'label': {'formatter': '利润阈值', 'position': 'end'}}
                ]
            }
        
        option = {
            'title': {
                'text': '商品四象限分布图',
                'subtext': f'利润率阈值: {profit_threshold}% | 动销指数阈值: {sales_threshold:.3f}',
                'left': 'center'
            },
            'legend': {
                'data': list(quadrant_colors.keys()),
                'top': '8%',
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'item',
                'backgroundColor': 'rgba(255,255,255,0.95)',
                'borderColor': '#ccc',
                'textStyle': {'color': '#333'},
                'confine': True,
                'formatter': "{b}<br/>动销指数: {c0}<br/>利润率: {c1}%<br/>销售额: ¥{c2}"
            },
            'grid': {
                'left': '10%',
                'right': '10%',
                'top': '18%',
                'bottom': '10%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'value',
                'name': '动销指数',
                'nameLocation': 'middle',
                'nameGap': 30,
                'splitLine': {'show': True, 'lineStyle': {'type': 'dashed'}},
                'axisLine': {'onZero': False}
            },
            'yAxis': {
                'type': 'value',
                'name': '利润率 (%)',
                'nameLocation': 'middle',
                'nameGap': 50,
                'splitLine': {'show': True, 'lineStyle': {'type': 'dashed'}},
                'axisLine': {'onZero': False}
            },
            'series': series_list
        }
        
        return html.Div([
            html.H5('四象限可视化分布', className="text-center mb-3"),
            DashECharts(
                id='quadrant-scatter-echart',  # ✅ 添加ID便于调试
                option=option,
                style={'height': '500px', 'width': '100%'}
            )
        ])
        
    except Exception as e:
        print(f"❌ [生成四象限散点图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"图表生成错误: {e}")


def calculate_time_period_quadrants(df, period='week', profit_threshold=30.0, start_date=None, end_date=None):
    """
    计算不同时间周期的四象限分类
    
    Parameters:
    -----------
    df : DataFrame
        原始数据,需包含日期、商品名称等字段
    period : str
        时间周期: 'day'(日) / 'week'(自然周) / 'month'(月)
    profit_threshold : float
        利润率阈值
    start_date : str or datetime, optional
        开始日期,用于筛选数据范围
    end_date : str or datetime, optional
        结束日期,用于筛选数据范围
        
    Returns:
    --------
    dict : {
        'periods': [周期列表],
        'period_label': '周期单位',
        'quadrant_data': {商品名称: [各周期的象限分类]},
        'trend_alerts': [预警商品列表]
    }
    """
    try:
        # 确保日期字段存在
        if '日期' not in df.columns:
            return None
        
        # 转换日期格式
        df = df.copy()
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        
        # 日期范围筛选
        if start_date is not None:
            start_date = pd.to_datetime(start_date)
            df = df[df['日期'] >= start_date]
        if end_date is not None:
            end_date = pd.to_datetime(end_date)
            df = df[df['日期'] <= end_date]
        
        if len(df) == 0:
            return None
        
        # 按周期分组
        if period == 'day':
            # 按日统计 - 直接使用日期作为周期
            df['周期'] = df['日期'].dt.strftime('%Y-%m-%d')
            period_label = '日'
        elif period == 'week':
            # 按自然周统计 - 计算从周一开始的自然周
            df['周期'] = df['日期'].dt.to_period('W-MON').astype(str)
            period_label = '周'
        elif period == 'month':
            df['周期'] = df['日期'].dt.to_period('M').astype(str)
            period_label = '月'
        else:
            return None
        
        periods = sorted(df['周期'].unique())
        
        # 为每个周期计算四象限
        period_quadrants = {}
        
        for p in periods:
            period_df = df[df['周期'] == p].copy()
            
            # 商品聚合(简化版,只计算关键指标)
            product_agg = period_df.groupby('商品名称').agg({
                '预计订单收入': 'sum',
                '实收价格': 'sum' if '实收价格' in period_df.columns else lambda x: period_df['预计订单收入'].sum(),
                '利润额': 'sum',
                '月售': 'sum',
                '库存': 'last',
                '订单ID': 'nunique'
            }).reset_index()
            
            product_agg.columns = ['商品名称', '销售额', '实收价格_sum', '实际利润', '总销量', '库存', '订单数']
            
            # 计算利润率
            if '实收价格' in period_df.columns:
                product_agg['利润率'] = (product_agg['实际利润'] / product_agg['实收价格_sum'].replace(0, np.nan) * 100).fillna(0).replace([np.inf, -np.inf], 0)
            else:
                product_agg['利润率'] = (product_agg['实际利润'] / product_agg['销售额'].replace(0, np.nan) * 100).fillna(0).replace([np.inf, -np.inf], 0)
            
            # 计算周转率
            product_agg['库存周转率'] = (product_agg['总销量'] / product_agg['库存'].replace(0, np.nan)).fillna(0).replace([np.inf, -np.inf], 0)
            
            # 标准化动销指数
            min_sales = product_agg['总销量'].min()
            max_sales = product_agg['总销量'].max()
            min_turnover = product_agg['库存周转率'].min()
            max_turnover = product_agg['库存周转率'].max()
            min_orders = product_agg['订单数'].min()
            max_orders = product_agg['订单数'].max()
            
            sales_range = max_sales - min_sales if max_sales > min_sales else 1
            turnover_range = max_turnover - min_turnover if max_turnover > min_turnover else 1
            orders_range = max_orders - min_orders if max_orders > min_orders else 1
            
            product_agg['标准化销量'] = (product_agg['总销量'] - min_sales) / sales_range
            product_agg['标准化周转率'] = (product_agg['库存周转率'] - min_turnover) / turnover_range
            product_agg['标准化订单数'] = (product_agg['订单数'] - min_orders) / orders_range
            
            product_agg['动销指数'] = (
                0.5 * product_agg['标准化销量'] + 
                0.3 * product_agg['标准化周转率'] + 
                0.2 * product_agg['标准化订单数']
            )
            
            # 四象限判定
            sales_threshold = product_agg['动销指数'].median()
            
            def classify_quadrant(row):
                high_profit = row['利润率'] > profit_threshold
                high_sales = row['动销指数'] > sales_threshold
                
                if high_profit and high_sales:
                    return '🌟 高利润高动销'
                elif high_profit and not high_sales:
                    return '⚠️ 高利润低动销'
                elif not high_profit and high_sales:
                    return '🚀 低利润高动销'
                else:
                    return '❌ 低利润低动销'
            
            product_agg['象限'] = product_agg.apply(classify_quadrant, axis=1)
            
            # 保存到字典
            period_quadrants[p] = product_agg[['商品名称', '象限', '销售额', '实际利润', '利润率', '动销指数']].set_index('商品名称')['象限'].to_dict()
        
        # 重构数据: 商品 -> [各周期象限]
        all_products = set()
        for p_data in period_quadrants.values():
            all_products.update(p_data.keys())
        
        quadrant_data = {}
        for product in all_products:
            quadrant_data[product] = [period_quadrants[p].get(product, '无数据') for p in periods]
        
        # 分析趋势预警
        trend_alerts = analyze_quadrant_trends(quadrant_data, periods)
        
        return {
            'periods': periods,
            'period_label': period_label,
            'quadrant_data': quadrant_data,
            'trend_alerts': trend_alerts
        }
        
    except Exception as e:
        print(f"❌ [时间维度四象限计算] 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_quadrant_trends(quadrant_data, periods):
    """
    分析商品的象限迁移趋势，识别需要预警的商品
    
    Returns:
    --------
    list of dict: [
        {
            'product': 商品名称,
            'trend': 趋势描述,
            'alert_level': 'critical'/'warning'/'info',
            'from_quadrant': 起始象限,
            'to_quadrant': 当前象限,
            'recommendation': 建议
        }
    ]
    """
    alerts = []
    
    # 象限优先级(越小越好)
    quadrant_priority = {
        '🌟 高利润高动销': 1,
        '⚠️ 高利润低动销': 2,
        '🚀 低利润高动销': 3,
        '❌ 低利润低动销': 4,
        '无数据': 5
    }
    
    for product, quadrant_list in quadrant_data.items():
        if len(quadrant_list) < 2:
            continue
        
        # 过滤无数据
        valid_quadrants = [q for q in quadrant_list if q != '无数据']
        if len(valid_quadrants) < 2:
            continue
        
        first_quadrant = valid_quadrants[0]
        last_quadrant = valid_quadrants[-1]
        
        # 计算趋势
        first_priority = quadrant_priority.get(first_quadrant, 5)
        last_priority = quadrant_priority.get(last_quadrant, 5)
        
        if first_priority < last_priority:
            # 恶化趋势
            trend_desc = f"{first_quadrant} → {last_quadrant}"
            
            if first_priority == 1 and last_priority == 4:
                # 明星 → 淘汰 (最严重)
                alert_level = 'critical'
                recommendation = "🚨 紧急处理: 曾是明星产品,现已沦为淘汰品,需立即调查原因!"
            elif first_priority == 1:
                # 明星下滑
                alert_level = 'critical'
                recommendation = "⚠️ 重点关注: 明星产品表现下滑,建议检查库存、定价、竞品"
            elif last_priority == 4:
                # 滑向淘汰
                alert_level = 'warning'
                recommendation = "📉 考虑清仓: 产品持续恶化,可能需要下架或促销清仓"
            else:
                alert_level = 'warning'
                recommendation = "💡 需要优化: 产品表现下滑,建议调整策略"
            
            alerts.append({
                'product': product,
                'trend': trend_desc,
                'alert_level': alert_level,
                'from_quadrant': first_quadrant,
                'to_quadrant': last_quadrant,
                'recommendation': recommendation
            })
        
        elif first_priority > last_priority and last_priority <= 2:
            # 改善趋势(且当前表现不错)
            trend_desc = f"{first_quadrant} → {last_quadrant}"
            alert_level = 'info'
            recommendation = "✅ 持续优化: 产品表现改善,保持当前策略"
            
            alerts.append({
                'product': product,
                'trend': trend_desc,
                'alert_level': alert_level,
                'from_quadrant': first_quadrant,
                'to_quadrant': last_quadrant,
                'recommendation': recommendation
            })
    
    # 按严重程度排序
    alert_priority = {'critical': 1, 'warning': 2, 'info': 3}
    alerts.sort(key=lambda x: alert_priority.get(x['alert_level'], 99))
    
    return alerts


def create_category_trend_chart(df, periods, period_label, quadrant_data, view_mode='all'):
    """创建一级分类趋势图 - 支持切换查看不同象限
    
    Args:
        view_mode: 'all'(全部堆叠) / 'star'(明星) / 'problem'(问题) / 'traffic'(引流) / 'eliminate'(淘汰)
    """
    try:
        print(f"\n📈 [分类趋势图] 开始生成... (视图模式: {view_mode})")
        
        # 判断是按日还是按周
        is_daily = '日' in period_label or 'Day' in period_label
        
        # 获取商品的分类信息
        product_category = df[['商品名称', '一级分类名']].drop_duplicates().set_index('商品名称')['一级分类名'].to_dict()
        
        # 按分类统计每个周期的象限分布
        category_trends = {}
        
        for product, quadrants in quadrant_data.items():
            category = product_category.get(product, '未分类')
            if category not in category_trends:
                category_trends[category] = {
                    '🌟 高利润高动销': [0] * len(periods),
                    '⚠️ 高利润低动销': [0] * len(periods),
                    '🚀 低利润高动销': [0] * len(periods),
                    '❌ 低利润低动销': [0] * len(periods)
                }
            
            for i, q in enumerate(quadrants):
                if q and q != '无数据':
                    category_trends[category][q][i] += 1
        
        # 选择TOP 5分类(按商品总数)
        top_categories = sorted(
            category_trends.items(),
            key=lambda x: sum(sum(counts) for counts in x[1].values()),
            reverse=True
        )[:5]
        
        print(f"   📊 TOP5分类: {[cat[0] for cat in top_categories]}")
        
        # 生成折线图 (ECharts)
        if not ECHARTS_AVAILABLE:
            return html.Div()
        
        # X轴标签：按日显示日期，按周/月显示序号
        if is_daily:
            # periods已经是字符串格式 '2025-09-01',转换显示为 '09-01'
            x_labels = [pd.to_datetime(p).strftime('%m-%d') if isinstance(p, str) else p.strftime('%m-%d') for p in periods]
        else:
            x_labels = [f'第{i+1}{period_label}' for i in range(len(periods))]  # 例如: 第1周, 第2周
        
        # 准备数据 - 根据视图模式生成不同的系列
        series_data = []
        
        # 象限配置
        quadrant_config = {
            'star': ('🌟 高利润高动销', '#52c41a', '明星商品'),
            'problem': ('⚠️ 高利润低动销', '#faad14', '问题商品'),
            'traffic': ('🚀 低利润高动销', '#1890ff', '引流商品'),
            'eliminate': ('❌ 低利润低动销', '#f5222d', '淘汰商品')
        }
        
        if view_mode == 'all':
            # 全部堆叠模式
            quadrant_info = [
                ('🌟 高利润高动销', '#52c41a', '明星'),
                ('⚠️ 高利润低动销', '#faad14', '问题'),
                ('🚀 低利润高动销', '#1890ff', '引流'),
                ('❌ 低利润低动销', '#f5222d', '淘汰')
            ]
            
            for quadrant_full, color, quadrant_short in quadrant_info:
                for category, quadrants_dict in top_categories:
                    series_data.append({
                        'name': f'{category}-{quadrant_short}',
                        'type': 'line',
                        'stack': category,
                        'areaStyle': {'opacity': 0.7},
                        'emphasis': {'focus': 'series'},
                        'lineStyle': {'width': 0},
                        'data': quadrants_dict[quadrant_full],
                        'itemStyle': {'color': color}
                    })
            
            title_text = '一级分类 - 四象限商品结构趋势'
            subtitle_text = '堆叠面积图展示每个分类的商品结构变化(颜色表示象限)'
            y_axis_name = '商品数量'
            show_legend = True  # 显示图例说明象限颜色
            legend_type = 'quadrant'  # 图例类型:象限
            
        else:
            # 单象限折线模式
            quadrant_full, color, quadrant_name = quadrant_config[view_mode]
            
            for category, quadrants_dict in top_categories:
                series_data.append({
                    'name': category,
                    'type': 'line',
                    'smooth': True,
                    'data': quadrants_dict[quadrant_full],
                    'lineStyle': {'width': 3},
                    'emphasis': {'focus': 'series'}
                })
            
            title_text = f'一级分类 - {quadrant_name}数量趋势'
            subtitle_text = f'折线图展示TOP5分类的{quadrant_name}变化'
            y_axis_name = f'{quadrant_name}数量'
            show_legend = True
            legend_type = 'category'  # 图例类型:分类
        
        # ECharts配置
        option = {
            'title': {
                'text': title_text,
                'subtext': subtitle_text,
                'left': 'center',
                'textStyle': {'fontSize': 16}
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'cross'}
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '3%',
                'top': '18%' if legend_type == 'quadrant' else '22%',  # 堆叠模式图例较小,需要的空间少一些
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'boundaryGap': False,
                'data': x_labels
            },
            'yAxis': {
                'type': 'value',
                'name': y_axis_name
            },
            'series': series_data
        }
        
        # 配置图例
        if show_legend:
            if legend_type == 'quadrant':
                # 堆叠模式:显示象限图例
                option['legend'] = {
                    'top': '12%',
                    'left': 'center',
                    'orient': 'horizontal',
                    'data': [
                        {'name': '明星', 'icon': 'rect', 'itemStyle': {'color': '#52c41a'}},
                        {'name': '问题', 'icon': 'rect', 'itemStyle': {'color': '#faad14'}},
                        {'name': '引流', 'icon': 'rect', 'itemStyle': {'color': '#1890ff'}},
                        {'name': '淘汰', 'icon': 'rect', 'itemStyle': {'color': '#f5222d'}}
                    ],
                    'textStyle': {'fontSize': 13},
                    'itemWidth': 30,
                    'itemHeight': 14
                }
            else:
                # 单象限模式:显示分类图例
                option['legend'] = {
                    'top': '15%',
                    'left': 'center',
                    'orient': 'horizontal',
                    'data': [cat[0] for cat in top_categories]
                }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="category-trend-chart" style="width: 100%; height: 400px;"></div>
            <script>
                var chartDom = document.getElementById('category-trend-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{
                    myChart.resize();
                }});
            </script>
        </body>
        </html>
        '''
        
        period_desc = "每日" if is_daily else "每周"
        view_desc = {
            'all': '堆叠面积图展示TOP5分类的四象限商品结构',
            'star': '🟢明星商品（高利润高动销），重点维护对象',
            'problem': '🟡问题商品（高利润低动销），警惕库存积压',
            'traffic': '🔵引流商品（低利润高动销），关联销售机会',
            'eliminate': '🔴淘汰商品（低利润低动销），考虑清仓下架'
        }
        
        return html.Div([
            html.H6("📈 分类趋势分析", className="mb-2"),
            dcc.Markdown(f"💡 **说明**: {view_desc[view_mode]}，{period_desc}变化趋势", className="text-muted small mb-3"),
            html.Div(
                html.Iframe(
                    srcDoc=chart_html,
                    style={'width': '100%', 'height': '450px', 'border': 'none'}
                )
            )
        ], className="mb-4")
        
    except Exception as e:
        print(f"❌ [分类趋势图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div()


def create_quadrant_migration_sankey_enhanced(quadrant_data, periods, period_label):
    """创建增强版象限迁移桑基图 - 显示所有迁移路径,线条粗细表示商品数量"""
    try:
        if not ECHARTS_AVAILABLE or len(periods) < 2:
            return html.Div()
        
        print(f"\n📊 [增强桑基图] 开始生成...")
        
        # 判断是按日还是按周
        is_daily = '日' in period_label or 'Day' in period_label
        
        # 统计所有迁移路径
        migrations = {}
        migration_details = []
        
        for product, quadrant_list in quadrant_data.items():
            valid_quadrants = [q for q in quadrant_list if q != '无数据']
            if len(valid_quadrants) >= 2:
                from_q = valid_quadrants[0]
                to_q = valid_quadrants[-1]
                key = (from_q, to_q)
                migrations[key] = migrations.get(key, 0) + 1
                migration_details.append({
                    'product': product,
                    'from': from_q,
                    'to': to_q,
                    'changed': from_q != to_q
                })
        
        # 打印统计信息
        print(f"   📊 总商品数: {len(migration_details)}")
        print(f"   🔄 迁移路径数: {len(migrations)}")
        total_changed = sum(1 for d in migration_details if d['changed'])
        print(f"   ✨ 发生变化: {total_changed}个商品")
        
        # 构建桑基图数据
        nodes = []
        links = []
        node_set = set()
        
        # 添加节点和连接
        for (from_q, to_q), count in migrations.items():
            if count > 0:
                # 象限名称映射(带emoji和详细说明)
                quadrant_map = {
                    '🌟 高利润高动销': {'short': '明星', 'emoji': '🌟', 'desc': '高利润高动销'},
                    '⚠️ 高利润低动销': {'short': '金牛', 'emoji': '⚠️', 'desc': '高利润低动销'},
                    '🚀 低利润高动销': {'short': '引流', 'emoji': '🚀', 'desc': '低利润高动销'},
                    '❌ 低利润低动销': {'short': '淘汰', 'emoji': '❌', 'desc': '低利润低动销'}
                }
                
                from_info = quadrant_map.get(from_q, {'short': from_q, 'emoji': '', 'desc': from_q})
                to_info = quadrant_map.get(to_q, {'short': to_q, 'emoji': '', 'desc': to_q})
                
                # 象限颜色映射(鲜明配色)
                color_map = {
                    '明星': '#52c41a',  # 绿色 - 明星商品
                    '金牛': '#faad14',  # 黄色 - 金牛商品
                    '引流': '#1890ff',  # 蓝色 - 引流商品
                    '淘汰': '#f5222d'   # 红色 - 淘汰商品
                }
                
                # 节点标签：增强标识(期初/期末 + emoji + 象限名 + 时间)
                if is_daily:
                    # periods是字符串列表,需要转换
                    first_date = pd.to_datetime(periods[0]).strftime("%m-%d") if isinstance(periods[0], str) else periods[0].strftime("%m-%d")
                    last_date = pd.to_datetime(periods[-1]).strftime("%m-%d") if isinstance(periods[-1], str) else periods[-1].strftime("%m-%d")
                    source_node = f'【期初】{from_info["emoji"]} {from_info["short"]}\n{first_date}'
                    target_node = f'【期末】{to_info["emoji"]} {to_info["short"]}\n{last_date}'
                else:
                    source_node = f'【期初】{from_info["emoji"]} {from_info["short"]}\n第1{period_label}'
                    target_node = f'【期末】{to_info["emoji"]} {to_info["short"]}\n第{len(periods)}{period_label}'
                
                if source_node not in node_set:
                    nodes.append({
                        'name': source_node,
                        'itemStyle': {'color': color_map.get(from_info['short'], '#999')}
                    })
                    node_set.add(source_node)
                
                if target_node not in node_set:
                    nodes.append({
                        'name': target_node,
                        'itemStyle': {'color': color_map.get(to_info['short'], '#999')}
                    })
                    node_set.add(target_node)
                
                # 添加连接(线条粗细由value决定，附带详细信息)
                links.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count,
                    'lineStyle': {
                        'color': color_map.get(from_info['short'], '#999'),
                        'opacity': 0.3
                    }
                })
                
                print(f"   {from_info['short']} → {to_info['short']}: {count}个商品")
        
        # 桑基图标题：按日显示日期范围，按周显示周数范围
        if is_daily:
            first_date = pd.to_datetime(periods[0]).strftime("%m-%d") if isinstance(periods[0], str) else periods[0].strftime("%m-%d")
            last_date = pd.to_datetime(periods[-1]).strftime("%m-%d") if isinstance(periods[-1], str) else periods[-1].strftime("%m-%d")
            title_text = f'象限迁移可视化 (所有商品)'
            subtitle_text = f'分析周期: {first_date} → {last_date}, 线条粗细表示商品数量'
        else:
            title_text = f'象限迁移可视化 (所有商品)'
            subtitle_text = f'分析周期: 第1{period_label} → 第{len(periods)}{period_label}, 线条粗细表示商品数量'
        
        # 生成ECharts桑基图
        option = {
            'title': {
                'text': title_text,
                'subtext': subtitle_text,
                'left': 'center',
                'top': '2%'
            },
            'legend': {
                'data': [
                    {'name': '🌟 明星商品 (高利润高动销)', 'icon': 'circle', 'itemStyle': {'color': '#52c41a'}},
                    {'name': '⚠️ 金牛商品 (高利润低动销)', 'icon': 'circle', 'itemStyle': {'color': '#faad14'}},
                    {'name': '🚀 引流商品 (低利润高动销)', 'icon': 'circle', 'itemStyle': {'color': '#1890ff'}},
                    {'name': '❌ 淘汰商品 (低利润低动销)', 'icon': 'circle', 'itemStyle': {'color': '#f5222d'}}
                ],
                'top': '8%',
                'left': 'center',
                'orient': 'horizontal',
                'textStyle': {'fontSize': 12}
            },
            'tooltip': {
                'trigger': 'item',
                'triggerOn': 'mousemove',
                'confine': True
            },
            'grid': {
                'top': '18%'
            },
            'series': [{
                'type': 'sankey',
                'data': nodes,
                'links': links,
                'top': '18%',
                'bottom': '5%',
                'left': '5%',
                'right': '15%',
                'nodeWidth': 30,
                'nodeGap': 15,
                'layoutIterations': 32,
                'orient': 'horizontal',
                'draggable': False,
                'label': {
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#333'
                },
                'lineStyle': {
                    'color': 'source',
                    'curveness': 0.5
                },
                'emphasis': {
                    'focus': 'adjacency',
                    'lineStyle': {
                        'opacity': 0.6
                    }
                }
            }]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="sankey-chart" style="width: 100%; height: 550px;"></div>
            <script>
                var chartDom = document.getElementById('sankey-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                
                // 自定义tooltip formatter
                option.tooltip.formatter = function(params) {{
                    if (params.dataType === 'edge') {{
                        var source = params.data.source.split('\\n')[0];
                        var target = params.data.target.split('\\n')[0];
                        return source + ' → ' + target + '<br/>迁移商品数: ' + params.value + '个';
                    }} else {{
                        return params.name.replace('\\n', '<br/>') + '<br/>商品数: ' + params.value + '个';
                    }}
                }};
                
                myChart.setOption(option);
                window.addEventListener('resize', function() {{
                    myChart.resize();
                }});
            </script>
        </body>
        </html>
        '''
        
        # 迁移统计表
        migration_stats = []
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            trend = ("📉 恶化" if from_q=='🌟 高利润高动销' and to_q=='❌ 低利润低动销'
                     else "📈 改善" if to_q=='🌟 高利润高动销' and from_q!='🌟 高利润高动销'
                     else "🔄 变化" if from_q!=to_q
                     else "➡️ 稳定")
            migration_stats.append({
                '起始象限': from_q,
                '当前象限': to_q,
                '趋势': trend,
                '商品数': count,
                '占比': f"{count/len(migration_details)*100:.1f}%"
            })
        
        stats_df = pd.DataFrame(migration_stats)
        
        return html.Div([
            html.H6("📊 象限迁移可视化", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div(
                        html.Iframe(
                            srcDoc=chart_html,
                            style={'width': '100%', 'height': '550px', 'border': 'none'}
                        )
                    )
                ], md=8),
                dbc.Col([
                    html.H6("迁移统计", className="mb-2"),
                    html.Small(f"💡 共{len(migration_details)}个商品, {total_changed}个发生迁移", className="text-muted d-block mb-3"),
                    dash_table.DataTable(
                        data=stats_df.to_dict('records'),
                        columns=[{'name': c, 'id': c} for c in stats_df.columns],
                        style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{趋势} contains "恶化"'},
                                'backgroundColor': '#ffe6e6'
                            },
                            {
                                'if': {'filter_query': '{趋势} contains "改善"'},
                                'backgroundColor': '#e6ffe6'
                            }
                        ]
                    )
                ], md=4)
            ])
        ], className="mb-4")
        
    except Exception as e:
        print(f"❌ [增强桑基图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div()


def generate_trend_analysis_content(df, period='week', alert_level='warning', view_mode='all', start_date=None, end_date=None):
    """生成趋势分析内容（用于Tab 2直接渲染）
    
    Args:
        period: 'day'(按日) / 'week'(按自然周) / 'month'(按月)
        view_mode: 'all'(全部堆叠) / 'star'(明星) / 'problem'(问题) / 'traffic'(引流) / 'eliminate'(淘汰)
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        print(f"\n📊 [生成趋势分析] 周期:{period}, 级别:{alert_level}, 视图:{view_mode}, 日期:{start_date} ~ {end_date}")
        
        # 计算时间维度四象限
        trend_data = calculate_time_period_quadrants(df, period=period, start_date=start_date, end_date=end_date)
        
        if not trend_data:
            return dbc.Alert("暂无足够数据进行趋势分析", color="info", className="mb-4")
        
        periods = trend_data['periods']
        period_label = trend_data['period_label']
        quadrant_data = trend_data['quadrant_data']
        alerts = trend_data['trend_alerts']
        
        print(f"   📊 总预警数: {len(alerts)}")
        
        # 筛选预警级别
        if alert_level == 'critical':
            filtered_alerts = [a for a in alerts if a['alert_level'] == 'critical']
            alert_level_text = '🔴 紧急预警'
        elif alert_level == 'warning':
            filtered_alerts = [a for a in alerts if a['alert_level'] in ['critical', 'warning']]
            alert_level_text = '🟡 重点关注'
        else:
            filtered_alerts = alerts
            alert_level_text = '🟢 全部趋势'
        
        print(f"   🎯 过滤后预警数: {len(filtered_alerts)} ({alert_level_text})")
        
        # ===== 1. 一级分类趋势图 (支持象限选择) =====
        category_trend_chart = create_category_trend_chart(df, periods, period_label, quadrant_data, view_mode)
        
        # ===== 2. 趋势预警卡片 =====
        alert_cards = []
        display_alerts = filtered_alerts[:20]  # 最多显示20个
        
        for alert in display_alerts:
            if alert['alert_level'] == 'critical':
                color = 'danger'
                icon = '🚨'
            elif alert['alert_level'] == 'warning':
                color = 'warning'
                icon = '⚠️'
            else:
                color = 'success'
                icon = '✅'
            
            alert_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6([icon, f" {alert['product']}"], className="card-title"),
                            html.P(alert['trend'], className="mb-1", style={'fontSize': '0.9rem'}),
                            html.Small(alert['recommendation'], className="text-muted")
                        ])
                    ], color=color, outline=True)
                ], md=6, className="mb-3")
            )
        
        # 标题
        total_count = len(filtered_alerts)
        display_count = len(display_alerts)
        title = f"📢 商品趋势预警 ({alert_level_text} · 共{total_count}个"
        if total_count > display_count:
            title += f", 显示前{display_count}个)"
        else:
            title += ")"
        
        alert_section = html.Div([
            html.H6(title, className="mb-3"),
            dbc.Row(alert_cards) if alert_cards else dbc.Alert(f"暂无{alert_level_text}商品", color="success")
        ], className="mb-4")
        
        # ===== 3. 象限迁移可视化 (优化:显示所有迁移路径,线条粗细表示商品数量) =====
        migration_chart = create_quadrant_migration_sankey_enhanced(quadrant_data, periods, period_label)
        
        return html.Div([
            category_trend_chart,  # 新增:分类趋势图
            alert_section,
            migration_chart
        ])
        
    except Exception as e:
        print(f"❌ [生成趋势分析] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"趋势分析生成错误: {e}", color="danger", className="mb-4")


@app.callback(
    Output('tab-2-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab2_content(active_tab):
    """Tab 2: 商品分析 - 商品销售排行、分类分析、库存周转、滞销预警
    
    ✅ 使用统一计算标准（与Tab 1一致）
    """
    if active_tab != 'tab-2':
        raise PreventUpdate
    
    if GLOBAL_DATA is None:
        return dbc.Alert("⚠️ 未加载数据，请重启应用", color="warning", className="text-center")
    
    df = GLOBAL_DATA.copy()
    
    # ==================== 📐 标准计算流程（✅ 使用统一函数）====================
    try:
        print("\n" + "="*80)
        print("🔍 [Tab 2] 开始计算，使用统一标准")
        print("="*80)
        
        # ===== Step 0: 识别并剔除异常订单 =====
        # 异常订单定义：0销量 AND 0利润额 AND 0成本（同时满足三个条件）
        original_count = len(df)
        
        # 识别异常订单（需要同时满足三个条件）
        abnormal_mask = (
            (df['月售'] == 0) & 
            (df['利润额'] == 0) & 
            (df['商品采购成本'] == 0)
        )
        
        abnormal_count = abnormal_mask.sum()
        
        if abnormal_count > 0:
            # 剔除异常订单
            df = df[~abnormal_mask].copy()
            print(f"⚠️  [数据清洗] 识别到 {abnormal_count} 条异常订单（0销量&0利润&0成本），已自动剔除")
            print(f"   原始数据: {original_count} 行 → 清洗后: {len(df)} 行")
        else:
            print(f"✅ [数据清洗] 未发现异常订单，数据质量良好（{original_count} 行）")
        
        # ===== Step 1: 调用统一订单计算函数 =====
        order_agg = calculate_order_metrics(df)  # ✅ 使用公共函数，与Tab 1保持一致
        
        print("✅ 订单级聚合完成（使用统一函数）")
        print(f"   订单数: {len(order_agg)}")
        print(f"   订单总利润: ¥{order_agg['订单实际利润'].sum():,.2f}")
        
        # ===== Step 2: 商品维度数据准备 =====
        # 保留商品信息到订单聚合数据（用于后续商品聚合）
        order_product_map = df.groupby('订单ID').agg({
            '商品名称': lambda x: ','.join(x.unique()),  # 订单包含的商品
            '一级分类名': lambda x: ','.join(x.unique()) if '一级分类名' in df.columns else ''
        }).reset_index()
        
        # 合并商品信息
        order_agg = order_agg.merge(order_product_map, on='订单ID', how='left')
        
        # ===== Step 4: 将订单利润分配到商品 =====
        # 为每个商品明细行添加订单实际利润
        df_with_profit = df.merge(
            order_agg[['订单ID', '订单实际利润']],
            on='订单ID',
            how='left'
        )
        
        # 计算每个订单的商品总销售额（用于分配利润）
        order_sales_sum = df.groupby('订单ID')['商品实售价'].sum().reset_index()
        order_sales_sum.columns = ['订单ID', '订单商品总额']
        
        df_with_profit = df_with_profit.merge(order_sales_sum, on='订单ID', how='left')
        
        # 按商品销售额比例分配订单利润
        df_with_profit['商品分配利润'] = (
            df_with_profit['订单实际利润'] * 
            df_with_profit['商品实售价'] / 
            df_with_profit['订单商品总额']
        ).fillna(0)
        
        # ===== Step 5: 商品维度聚合 =====
        # 检查是否存在实收价格字段
        has_actual_price = '实收价格' in df.columns
        if not has_actual_price:
            print("⚠️ [四象限分析] 未找到'实收价格'字段，将使用'预计订单收入'计算利润率")
        else:
            print("✅ [四象限分析] 检测到'实收价格'字段，将用于计算实收利润率")
        
        agg_dict = {
            '预计订单收入': 'sum',         # ✅ 销售额（使用Y列预计订单收入，更真实）
            '商品采购成本': 'sum',         # 成本
            '利润额': 'sum',               # ✅ 实际利润（直接使用N列利润额，商品级已计算好）
            '月售': 'sum',                 # 销量（整个周期累计）
            '库存': 'last',                # ✅ 库存（取最后一天的库存，反映当前状态）
            '订单ID': 'nunique',            # 订单数
            '店内码': 'first',              # ✅ 新增：店内码
            '一级分类名': 'first',          # ✅ 新增：一级分类
            '三级分类名': 'first'           # ✅ 新增：三级分类
        }
        
        # 如果存在实收价格字段，添加到聚合中
        if has_actual_price:
            agg_dict['实收价格'] = 'sum'   # ✅ W列实收价格（排除补贴/折扣，更真实）
        
        product_agg = df.groupby('商品名称').agg(agg_dict).reset_index()
        
        # 设置列名
        if has_actual_price:
            product_agg.columns = ['商品名称', '销售额', '成本', '实际利润', '总销量', '库存', '订单数', '店内码', '一级分类名', '三级分类名', '实收价格']
        else:
            product_agg.columns = ['商品名称', '销售额', '成本', '实际利润', '总销量', '库存', '订单数', '店内码', '一级分类名', '三级分类名']
        
        # 计算衍生指标
        product_agg['平均售价'] = (product_agg['销售额'] / product_agg['总销量']).fillna(0)
        product_agg['平均成本'] = (product_agg['成本'] / product_agg['总销量']).fillna(0)
        
        # ✅ 修复利润率计算：优先使用实收价格（W列），避免除以0产生inf
        if has_actual_price:
            # 使用实收价格计算实收利润率（排除补贴/折扣影响）
            product_agg['利润率'] = (
                product_agg['实际利润'] / product_agg['实收价格'].replace(0, np.nan) * 100
            ).fillna(0).replace([np.inf, -np.inf], 0)
            print(f"✅ [利润率计算] 使用'实收价格'计算，平均实收利润率: {product_agg['利润率'].mean():.2f}%")
        else:
            # 回退方案：使用预计订单收入
            product_agg['利润率'] = (
                product_agg['实际利润'] / product_agg['销售额'].replace(0, np.nan) * 100
            ).fillna(0).replace([np.inf, -np.inf], 0)
            print(f"✅ [利润率计算] 使用'预计订单收入'计算，平均利润率: {product_agg['利润率'].mean():.2f}%")
        
        # ✅ 优化库存周转率计算：智能处理0库存情况
        def calculate_smart_turnover(row):
            """智能计算库存周转率，区分售罄和滞销"""
            sales = row['总销量']
            stock = row['库存']
            
            if stock == 0:
                if sales > 0:
                    # 情况1：0库存但有销量 = 售罄商品（动销很好）
                    # 使用销量作为估算周转率（假设平均库存为1）
                    return float(sales)  # 高周转率
                else:
                    # 情况2：0库存0销量 = 已下架商品
                    return 0.0
            else:
                # 正常计算
                return float(sales / stock)
        
        product_agg['库存周转率'] = product_agg.apply(calculate_smart_turnover, axis=1)
        product_agg['库存周转率'] = product_agg['库存周转率'].replace([np.inf, -np.inf], 0)
        
        # 统计0库存商品情况
        zero_stock_with_sales = ((product_agg['库存'] == 0) & (product_agg['总销量'] > 0)).sum()
        zero_stock_no_sales = ((product_agg['库存'] == 0) & (product_agg['总销量'] == 0)).sum()
        print(f"📦 [库存分析] 0库存商品: {zero_stock_with_sales}个售罄, {zero_stock_no_sales}个无销量")
        
        # ===== Step 6: 四象限分析 =====
        # 计算动销指数（综合指标：销量+周转率+订单数）
        # 先进行标准化处理（Min-Max标准化到0-1区间）
        min_sales = product_agg['总销量'].min()
        max_sales = product_agg['总销量'].max()
        min_turnover = product_agg['库存周转率'].min()
        max_turnover = product_agg['库存周转率'].max()
        min_orders = product_agg['订单数'].min()
        max_orders = product_agg['订单数'].max()
        
        # 避免除以0
        sales_range = max_sales - min_sales if max_sales > min_sales else 1
        turnover_range = max_turnover - min_turnover if max_turnover > min_turnover else 1
        orders_range = max_orders - min_orders if max_orders > min_orders else 1
        
        product_agg['标准化销量'] = (product_agg['总销量'] - min_sales) / sales_range
        product_agg['标准化周转率'] = (product_agg['库存周转率'] - min_turnover) / turnover_range
        product_agg['标准化订单数'] = (product_agg['订单数'] - min_orders) / orders_range
        
        # 动销指数 = 0.5×销量 + 0.3×周转率 + 0.2×订单数
        product_agg['动销指数'] = (
            0.5 * product_agg['标准化销量'] + 
            0.3 * product_agg['标准化周转率'] + 
            0.2 * product_agg['标准化订单数']
        )
        
        # 计算阈值（默认值）
        profit_threshold = 30.0  # 利润率阈值：30%
        sales_threshold = product_agg['动销指数'].median()  # 动销指数阈值：中位数
        
        # 四象限判定
        def classify_quadrant(row):
            high_profit = row['利润率'] > profit_threshold
            high_sales = row['动销指数'] > sales_threshold
            
            if high_profit and high_sales:
                return '🌟 高利润高动销'
            elif high_profit and not high_sales:
                return '⚠️ 高利润低动销'
            elif not high_profit and high_sales:
                return '🚀 低利润高动销'
            else:
                return '❌ 低利润低动销'
        
        product_agg['象限分类'] = product_agg.apply(classify_quadrant, axis=1)
        
        # ===== Step 6.5: 订单级盈利健康度分析 ✅ 新增 =====
        print("🔍 [订单级盈利分析] 开始计算...")
        
        # 准备订单级利润数据（每个商品的每个订单的利润）
        order_profit_detail = df_with_profit.groupby(['商品名称', '订单ID']).agg({
            '订单实际利润': 'first'  # 每个订单的实际利润
        }).reset_index()
        
        # 计算每个商品的盈利订单统计
        profit_health = order_profit_detail.groupby('商品名称').agg(
            总订单数=('订单ID', 'count'),
            盈利订单数=('订单实际利润', lambda x: (x > 0).sum()),
            亏损订单数=('订单实际利润', lambda x: (x <= 0).sum()),
            订单平均利润=('订单实际利润', 'mean'),
            订单利润标准差=('订单实际利润', 'std')
        ).reset_index()
        
        # 计算盈利订单占比
        profit_health['盈利订单占比'] = (
            profit_health['盈利订单数'] / profit_health['总订单数'] * 100
        ).fillna(0)
        
        # 判定健康度
        def get_health_status(ratio):
            if ratio >= 70:
                return '🟢 稳定盈利'
            elif ratio >= 40:
                return '🟡 波动盈利'
            elif ratio > 0:
                return '🔴 依赖大单'
            else:
                return '⚫ 全部亏损'
        
        profit_health['盈利健康度'] = profit_health['盈利订单占比'].apply(get_health_status)
        
        # 合并到商品聚合数据
        product_agg = product_agg.merge(
            profit_health[['商品名称', '盈利订单数', '亏损订单数', '盈利订单占比', '订单平均利润', '盈利健康度']], 
            on='商品名称', 
            how='left'
        )
        
        print(f"✅ [订单级盈利分析] 完成")
        print(f"   盈利健康度分布:")
        print(f"   {product_agg['盈利健康度'].value_counts().to_dict()}")
        
        # 智能经营建议（增强版，考虑盈利健康度）
        # 智能经营建议（增强版，考虑盈利健康度）
        def get_recommendation(row):
            quadrant = row['象限分类']
            stock = row['库存']
            turnover = row['库存周转率']
            health = row['盈利健康度']
            profit_ratio = row['盈利订单占比']
            
            # 基础建议
            base_rec = ""
            if quadrant == '🌟 高利润高动销':
                if turnover > 5:
                    base_rec = "明星商品，建议增加库存确保不断货"
                else:
                    base_rec = "优质商品，保持现有策略"
            elif quadrant == '⚠️ 高利润低动销':
                if stock > 10:
                    base_rec = "库存过高，建议促销或减少采购"
                else:
                    base_rec = "观察需求，谨慎补货"
            elif quadrant == '🚀 低利润高动销':
                base_rec = "流量商品，可适当提价或配合高利润品销售"
            else:
                base_rec = "建议清仓或下架"
            
            # 根据盈利健康度补充建议
            health_rec = ""
            if health == '🔴 依赖大单' and quadrant in ['🌟 高利润高动销', '⚠️ 高利润低动销']:
                health_rec = f" | ⚠️ 注意：{profit_ratio:.0f}%订单盈利，建议设置起购量或调整小单定价"
            elif health == '🟡 波动盈利':
                health_rec = f" | 💡 {profit_ratio:.0f}%订单盈利，盈利稳定性一般"
            elif health == '⚫ 全部亏损':
                health_rec = " | 🚨 所有订单都亏损，立即优化或下架"
            
            return base_rec + health_rec
        
        product_agg['经营建议'] = product_agg.apply(get_recommendation, axis=1)
        
        # 统计各象限商品数量
        quadrant_stats = product_agg['象限分类'].value_counts().to_dict()
        
        print(f"✅ 四象限分析完成")
        print(f"   利润率阈值: {profit_threshold}%")
        print(f"   动销指数阈值: {sales_threshold:.3f}")
        print(f"   🌟 高利润高动销: {quadrant_stats.get('🌟 高利润高动销', 0)} 个")
        print(f"   ⚠️ 高利润低动销: {quadrant_stats.get('⚠️ 高利润低动销', 0)} 个")
        print(f"   🚀 低利润高动销: {quadrant_stats.get('🚀 低利润高动销', 0)} 个")
        print(f"   ❌ 低利润低动销: {quadrant_stats.get('❌ 低利润低动销', 0)} 个")
        
        # ===== Step 8: 分类分析（如果有分类字段）=====
        if '一级分类名' in df.columns:
            # ✅ 直接基于源数据聚合（与商品聚合保持一致）
            category_sales = df.groupby('一级分类名').agg({
                '预计订单收入': 'sum',      # ✅ Y列：销售额
                '月售': 'sum',              # 销量
                '利润额': 'sum',            # ✅ N列：实际利润
                '订单ID': 'nunique'         # 订单数
            }).reset_index()
            
            category_sales.columns = ['分类', '销售额', '销量', '实际利润', '订单数']
            category_sales['利润率'] = (
                (category_sales['实际利润'] / category_sales['销售额'] * 100).fillna(0)
            )
            category_sales = category_sales.sort_values('销售额', ascending=False)
            
            print(f"✅ 分类分析完成: {len(category_sales)} 个分类")
        else:
            category_sales = None
            
    except Exception as e:
        print(f"[ERROR] Tab2 指标计算失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"❌ 数据处理失败: {e}", color="danger")
    
    # ==================== 页面布局 ====================
    # 构建content列表
    content = [
        # 标题
        html.H2("📦 商品分析", className="mb-4"),
        
        # ========== 1. 四象限智能分析 ==========
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H4("🎯 商品四象限智能分析", className="mb-0")
            ], md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "📥 导出分析数据"],
                    id='btn-export-quadrant',
                    color='primary',
                    size='sm',
                    className='float-end'
                )
            ], md=4)
        ], className="mb-3"),
        
        # 象限统计卡片
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🌟 高利润高动销", className="card-title text-success"),
                        html.H3(f"{quadrant_stats.get('🌟 高利润高动销', 0)}", className="text-success mb-0"),
                        html.Small("明星产品", className="text-muted")
                    ])
                ], className="text-center shadow-sm border-success")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("⚠️ 高利润低动销", className="card-title text-warning"),
                        html.H3(f"{quadrant_stats.get('⚠️ 高利润低动销', 0)}", className="text-warning mb-0"),
                        html.Small("问题产品", className="text-muted")
                    ])
                ], className="text-center shadow-sm border-warning")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🚀 低利润高动销", className="card-title text-info"),
                        html.H3(f"{quadrant_stats.get('🚀 低利润高动销', 0)}", className="text-info mb-0"),
                        html.Small("引流产品", className="text-muted")
                    ])
                ], className="text-center shadow-sm border-info")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("❌ 低利润低动销", className="card-title text-danger"),
                        html.H3(f"{quadrant_stats.get('❌ 低利润低动销', 0)}", className="text-danger mb-0"),
                        html.Small("淘汰产品", className="text-muted")
                    ])
                ], className="text-center shadow-sm border-danger")
            ], md=3),
        ], className="mb-4"),
        
        # ========== 📈 时间维度趋势分析 ==========
        html.Hr(),
        
        # 标题行
        dbc.Row([
            dbc.Col([
                html.H5("📈 四象限趋势分析", className="mb-0")
            ], md=12),
        ], className="mb-3"),
        
        # 控制面板:日期范围 + 象限选择 + 粒度选择
        dbc.Row([
            # 日期范围选择
            dbc.Col([
                html.Label("📅 日期范围", className="fw-bold mb-2", style={'fontSize': '14px'}),
                dcc.DatePickerRange(
                    id='trend-date-range',
                    start_date=None,  # 将在callback中设置
                    end_date=None,
                    display_format='YYYY-MM-DD',
                    style={'fontSize': '13px'}
                ),
                html.Div([
                    dbc.Button("全部", id='btn-date-all', size='sm', color='link', className='p-0 me-2'),
                    dbc.Button("最近7天", id='btn-date-7d', size='sm', color='link', className='p-0 me-2'),
                    dbc.Button("最近14天", id='btn-date-14d', size='sm', color='link', className='p-0')
                ], className="mt-1")
            ], md=4),
            
            # 象限选择
            dbc.Col([
                html.Label("🎯 象限选择", className="fw-bold mb-2", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='quadrant-view-selector',
                    options=[
                        {'label': '📊 全部象限（堆叠）', 'value': 'all'},
                        {'label': '🟢 明星商品', 'value': 'star'},
                        {'label': '🟡 问题商品', 'value': 'problem'},
                        {'label': '🔵 引流商品', 'value': 'traffic'},
                        {'label': '🔴 淘汰商品', 'value': 'eliminate'}
                    ],
                    value='all',
                    clearable=False,
                    style={'fontSize': '14px'}
                )
            ], md=4),
            
            # 粒度选择
            dbc.Col([
                html.Label("📊 时间粒度", className="fw-bold mb-2", style={'fontSize': '14px'}),
                dbc.ButtonGroup([
                    dbc.Button("按日", id='btn-trend-day', color='primary', size='sm', outline=True),
                    dbc.Button("按自然周", id='btn-trend-week', color='primary', size='sm', active=True),
                    dbc.Button("按月", id='btn-trend-month', color='primary', size='sm', outline=True)
                ], size='sm', className='d-flex')
            ], md=4)
        ], className="mb-4"),
        
        # 趋势分析内容容器 (动态更新)
        html.Div(id='trend-analysis-container'),
        
        html.Hr(),
        html.H5("📊 当前四象限分布", className="mb-3"),
        
        # ✅ 四象限定义说明标签
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6("📊 四象限分析定义说明", className="alert-heading mb-3"),
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Strong("📐 分析维度："),
                                html.Ul([
                                    html.Li([html.Strong("实收利润率"), f" = 实际利润 ÷ 实收价格 × 100%（阈值：{profit_threshold}%，实收价格=客户实付，排除补贴/折扣）"]),
                                    html.Li([
                                        html.Strong("动销指数"), 
                                        f" = 0.5×标准化销量 + 0.3×标准化周转率 + 0.2×标准化订单数（阈值：{sales_threshold:.3f}，取中位数）"
                                    ]),
                                    html.Li([
                                        html.Strong("库存周转率"), 
                                        " = 总销量 ÷ 库存（",
                                        html.Span("特殊处理", style={'color': '#ff6b00', 'fontWeight': 'bold'}),
                                        "：0库存有销量=售罄商品，周转率=销量；0库存0销量=下架商品，周转率=0）"
                                    ]),
                                    html.Li([
                                        html.Span("⚠️ 异常订单剔除", style={'color': '#dc3545', 'fontWeight': 'bold'}),
                                        "：自动识别并剔除",
                                        html.Strong(" 0销量 & 0利润 & 0成本 "),
                                        "的异常订单（数据源问题，不参与分析）"
                                    ]),
                                ], className="mb-2"),
                            ], md=6),
                            dbc.Col([
                                html.Strong("🎯 象限定义："),
                                html.Ul([
                                    html.Li([html.Span("🌟 高利润高动销", className="text-success"), "：利润率>30% 且 动销指数>中位数 → ", html.Strong("明星产品，重点维护")]),
                                    html.Li([html.Span("⚠️ 高利润低动销", className="text-warning"), "：利润率>30% 但 动销指数≤中位数 → ", html.Strong("优化库存或促销")]),
                                    html.Li([html.Span("🚀 低利润高动销", className="text-info"), "：利润率≤30% 但 动销指数>中位数 → ", html.Strong("引流品，关联销售")]),
                                    html.Li([html.Span("❌ 低利润低动销", className="text-danger"), "：利润率≤30% 且 动销指数≤中位数 → ", html.Strong("考虑清仓下架")]),
                                ], className="mb-2"),
                            ], md=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Strong("💡 盈利健康度分析（订单级）："),
                                html.Ul([
                                    html.Li([html.Span("🟢 稳定盈利", className="text-success"), "：≥70%订单盈利"]),
                                    html.Li([html.Span("🟡 波动盈利", className="text-warning"), "：40-70%订单盈利"]),
                                    html.Li([html.Span("🔴 依赖大单", className="text-danger"), "：<40%订单盈利但总体盈利（需关注定价策略）"]),
                                    html.Li([html.Span("⚫ 全部亏损", className="text-dark"), "：0%订单盈利（立即处理）"]),
                                ], className="mb-2"),
                                html.Div([
                                    html.Strong("📌 大单/小单定义说明：", style={'color': '#0066cc'}),
                                    html.Ul([
                                        html.Li([
                                            html.Strong("大单"), 
                                            "：指该商品的",
                                            html.Span("盈利订单", style={'color': '#28a745', 'fontWeight': 'bold'}),
                                            "（多为购买数量多或金额高的订单）"
                                        ]),
                                        html.Li([
                                            html.Strong("小单"), 
                                            "：指该商品的",
                                            html.Span("亏损订单", style={'color': '#dc3545', 'fontWeight': 'bold'}),
                                            "（多为购买数量少或金额低的订单，配送成本>利润）"
                                        ]),
                                        html.Li([
                                            "⚠️ ",
                                            html.Strong("依赖大单"), 
                                            "的商品：虽然总体盈利，但",
                                            html.Span(">60%订单亏损", style={'color': '#dc3545'}),
                                            "，盈利完全靠少数大单支撑 → 建议设置起购量或调整小单定价"
                                        ]),
                                    ], className="mb-0", style={'fontSize': '0.85rem', 'color': '#555'}),
                                ], style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '5px', 'marginTop': '8px'}),
                            ], md=12),
                        ]),
                    ], style={'fontSize': '0.9rem'})
                ], color="info", className="mb-3", style={'backgroundColor': '#e7f3ff'})
            ], md=12)
        ]),
        
        # 四象限散点图 - 直接在渲染时生成
        dbc.Row([
            dbc.Col([
                generate_quadrant_scatter_chart(product_agg, profit_threshold, sales_threshold)
            ], md=12)
        ], className="mb-4"),
        
        # 象限筛选和表格
        dbc.Row([
            dbc.Col([
                html.Label("筛选象限:"),
                dcc.Dropdown(
                    id='quadrant-filter',
                    options=[
                        {'label': '📊 全部商品', 'value': 'all'},
                        {'label': '🌟 高利润高动销（明星产品）', 'value': '🌟 高利润高动销'},
                        {'label': '⚠️ 高利润低动销（问题产品）', 'value': '⚠️ 高利润低动销'},
                        {'label': '🚀 低利润高动销（引流产品）', 'value': '🚀 低利润高动销'},
                        {'label': '❌ 低利润低动销（淘汰产品）', 'value': '❌ 低利润低动销'}
                    ],
                    value='all',
                    clearable=False,
                    className="mb-3"
                )
            ], md=4)
        ]),
        
        html.Div(id='quadrant-product-table', className="mt-3"),
        
        # 下载组件
        dcc.Download(id='download-quadrant-data'),
        
        # ========== 3. 商品销售排行 ==========
        html.Hr(),
        html.H4("🏆 商品销售排行", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Label("排序维度:"),
                dcc.Dropdown(
                    id='product-rank-dimension',
                    options=[
                        {'label': '💰 销售额', 'value': '销售额'},
                        {'label': '💵 实际利润', 'value': '实际利润'},
                        {'label': '📈 利润率', 'value': '利润率'},
                        {'label': '📦 销量', 'value': '总销量'},
                        {'label': '📊 订单数', 'value': '订单数'}
                    ],
                    value='销售额',
                    clearable=False,
                    className="mb-3"
                )
            ], md=3),
            
            dbc.Col([
                html.Label("显示数量:"),
                dcc.Dropdown(
                    id='product-rank-limit',
                    options=[
                        {'label': 'TOP 10', 'value': 10},
                        {'label': 'TOP 20', 'value': 20},
                        {'label': 'TOP 30', 'value': 30},
                        {'label': 'TOP 50', 'value': 50}
                    ],
                    value=20,
                    clearable=False,
                    className="mb-3"
                )
            ], md=3)
        ]),
        
        html.Div(id='product-ranking-chart'),
        
        html.Div(id='product-ranking-table', className="mt-3"),
        
        # ========== 4. 分类分析 ==========
        html.Hr(),
        html.H4("📂 分类分析", className="mb-3"),
        
        # 销售分布 - 独占一行
        dbc.Row([
            dbc.Col([
                html.Div(id='category-sales-chart')
            ], md=12)
        ], className="mb-4"),
        
        # 利润分析 - 独占一行
        dbc.Row([
            dbc.Col([
                html.Div(id='category-profit-chart')
            ], md=12)
        ]),
        
        # ========== 5. 商品结构分析 ==========
        html.Hr(),
        html.H4("🔍 商品结构分析", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div(id='price-range-chart')
            ], md=6),
            
            dbc.Col([
                html.Div(id='abc-analysis-chart')
            ], md=6)
        ]),
        
        # ========== 6. 库存预警 ==========
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H4("⚠️ 库存与滞销预警", className="mb-0")
            ], md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "📥 导出预警数据"],
                    id='btn-export-inventory-warnings',
                    color='success',
                    size='sm',
                    className='float-end'
                )
            ], md=4)
        ], className="mb-3"),
        
        html.Div(id='inventory-warning-section'),
        
        # ========== 🤖 AI智能分析工作流 ==========
        html.Hr(),
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="bi bi-robot me-2"),
                    html.H4("🤖 AI智能商品分析工作流", className="d-inline mb-0"),
                    html.Small(" - 全面分析7大板块数据", className="text-muted ms-2")
                ], className="d-flex align-items-center")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        # 分析模式选择
                        html.H6("📋 选择分析范围:", className="mb-2"),
                        dbc.RadioItems(
                            id='ai-analysis-mode',
                            options=[
                                {'label': ' 🎯 快速分析 (仅四象限)', 'value': 'quick'},
                                {'label': ' 🔍 标准分析 (四象限+趋势+排行)', 'value': 'standard'},
                                {'label': ' 📊 全面分析 (所有7大板块+综合报告)', 'value': 'comprehensive'}
                            ],
                            value='quick',
                            className="mb-3"
                        ),
                        
                        dbc.Alert([
                            html.I(className="bi bi-info-circle-fill me-2"),
                            html.Div(id='ai-mode-description')
                        ], color="info", className="mb-3"),
                        
                        dbc.Button(
                            [
                                html.I(className="bi bi-stars me-2"),
                                "🚀 开始AI智能分析"
                            ],
                            id='ai-tab2-analyze-btn',
                            color="primary",
                            size="lg",
                            className="w-100 mb-3"
                        ),
                        
                        # 分析进度显示
                        html.Div(id='ai-analysis-progress', className="mb-3"),
                        
                        # AI分析结果显示区域
                        dcc.Loading(
                            id="loading-ai-tab2-analysis",
                            type="default",
                            children=[
                                html.Div(id='ai-tab2-analysis-result', className="mt-3")
                            ]
                        )
                    ], md=12)
                ])
            ])
        ], className="mb-4"),
        
        # 下载组件
        dcc.Download(id='download-inventory-warnings'),
        
        # 隐藏数据存储 - 增强版,支持多板块分析
        dcc.Store(id='product-agg-data', data=product_agg.to_dict('records')),
        dcc.Store(id='category-sales-data', data=category_sales.to_dict('records') if category_sales is not None else None),
        # 新增:存储趋势分析和其他板块数据
        dcc.Store(id='tab2-all-data', data={
            'product_agg': product_agg.to_dict('records'),
            'category_agg': category_sales.to_dict('records') if category_sales is not None else None,
            'quadrant_stats': quadrant_stats,
            'profit_threshold': profit_threshold,
            'sales_threshold': sales_threshold
        })
    ]
    
    return html.Div(content)


# ==================== Tab 2 新增回调: AI分析模式描述 ====================
@app.callback(
    Output('ai-mode-description', 'children'),
    Input('ai-analysis-mode', 'value')
)
def update_ai_mode_description(mode):
    """更新AI分析模式描述"""
    descriptions = {
        'quick': [
            html.Strong("快速分析模式："),
            html.Br(),
            "• 分析范围: 四象限数据",
            html.Br(),
            "• 耗时约: 5-8秒",
            html.Br(),
            "• 适用场景: 快速查看商品组合优化建议"
        ],
        'standard': [
            html.Strong("标准分析模式："),
            html.Br(),
            "• 分析范围: 四象限 + 趋势分析 + 商品排行",
            html.Br(),
            "• 耗时约: 15-20秒",
            html.Br(),
            "• 适用场景: 全面了解商品表现和趋势变化"
        ],
        'comprehensive': [
            html.Strong("全面分析模式："),
            html.Br(),
            "• 分析范围: 7大板块(四象限/趋势/排行/分类/结构/库存) + 综合报告",
            html.Br(),
            "• 耗时约: 30-40秒",
            html.Br(),
            "• 适用场景: 制定完整的商品运营策略和执行计划",
            html.Br(),
            "• 输出: 分板块分析 + 整合性策略建议"
        ]
    }
    return descriptions.get(mode, [])


# ==================== Tab 2 子回调: 四象限散点图（已废弃 - 改为直接渲染）====================
# @app.callback(
#     Output('quadrant-scatter-chart', 'children'),
#     Input('product-agg-data', 'data')
# )
# def update_quadrant_scatter(product_data):
#     """更新四象限散点图（✅ ECharts版）"""
#     # 此回调已废弃，四象限图现在在render_tab2_content中直接生成
#     pass


# ==================== Tab 2 子回调: 趋势分析周期切换 ====================
@app.callback(
    [Output('trend-analysis-container', 'children'),
     Output('btn-trend-day', 'active'),
     Output('btn-trend-week', 'active'),
     Output('btn-trend-month', 'active'),
     Output('trend-date-range', 'start_date'),
     Output('trend-date-range', 'end_date')],
    [Input('btn-trend-day', 'n_clicks'),
     Input('btn-trend-week', 'n_clicks'),
     Input('btn-trend-month', 'n_clicks'),
     Input('quadrant-view-selector', 'value'),
     Input('trend-date-range', 'start_date'),
     Input('trend-date-range', 'end_date'),
     Input('btn-date-all', 'n_clicks'),
     Input('btn-date-7d', 'n_clicks'),
     Input('btn-date-14d', 'n_clicks')],
    [State('btn-trend-day', 'active'),
     State('btn-trend-week', 'active'),
     State('btn-trend-month', 'active')],
    prevent_initial_call=False
)
def update_trend_analysis(day_clicks, week_clicks, month_clicks, view_mode, 
                         start_date, end_date, all_clicks, d7_clicks, d14_clicks,
                         day_active, week_active, month_active):
    """切换趋势分析周期（按日/按自然周/按月）、象限视图和日期范围"""
    try:
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("请先上传数据", color="warning"), False, True, False, None, None
        
        # 获取数据的日期范围
        data_dates = pd.to_datetime(GLOBAL_DATA['日期'], errors='coerce')
        data_min_date = data_dates.min().date()
        data_max_date = data_dates.max().date()
        
        # 判断触发源
        ctx = callback_context
        if not ctx.triggered:
            # 初始加载，默认按周，全部日期
            period = 'week'
            day_active = False
            week_active = True
            month_active = False
            view_mode = view_mode or 'all'
            start_date = data_min_date
            end_date = data_max_date
        else:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # 处理粒度切换
            if trigger_id == 'btn-trend-day':
                period = 'day'
                day_active, week_active, month_active = True, False, False
            elif trigger_id == 'btn-trend-week':
                period = 'week'
                day_active, week_active, month_active = False, True, False
            elif trigger_id == 'btn-trend-month':
                period = 'month'
                day_active, week_active, month_active = False, False, True
            # 处理日期快捷按钮
            elif trigger_id == 'btn-date-all':
                start_date = data_min_date
                end_date = data_max_date
                # 全部数据时,保持当前粒度
                if day_active:
                    period = 'day'
                elif month_active:
                    period = 'month'
                else:
                    period = 'week'
            elif trigger_id == 'btn-date-7d':
                start_date = data_max_date - pd.Timedelta(days=6)  # 最近7天
                end_date = data_max_date
                # 最近7天自动切换到按日模式
                period = 'day'
                day_active, week_active, month_active = True, False, False
            elif trigger_id == 'btn-date-14d':
                start_date = data_max_date - pd.Timedelta(days=13)  # 最近14天
                end_date = data_max_date
                # 最近14天自动切换到按日模式
                period = 'day'
                day_active, week_active, month_active = True, False, False
            else:
                # 日期选择器或象限选择器触发，保持当前粒度
                if day_active:
                    period = 'day'
                elif month_active:
                    period = 'month'
                else:
                    period = 'week'
                
                # 如果日期为None,使用全部数据
                if start_date is None:
                    start_date = data_min_date
                if end_date is None:
                    end_date = data_max_date
        
        print(f"\n🔄 [趋势分析] period={period}, view={view_mode}, 日期:{start_date} ~ {end_date}")
        
        # 生成趋势分析内容
        content = generate_trend_analysis_content(
            GLOBAL_DATA, 
            period=period, 
            alert_level='warning', 
            view_mode=view_mode,
            start_date=start_date,
            end_date=end_date
        )
        
        return content, day_active, week_active, month_active, start_date, end_date
        
    except Exception as e:
        print(f"❌ [趋势分析回调] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"趋势分析加载失败: {str(e)}", color="danger"), False, True, False, None, None


def create_quadrant_migration_sankey(top_products, periods, period_label):
    """创建象限迁移桑基图"""
    try:
        if not ECHARTS_AVAILABLE or len(periods) < 2:
            return html.Div()
        
        # 简化: 只看首周期 -> 末周期
        first_period = periods[0]
        last_period = periods[-1]
        
        # 统计迁移流量
        migrations = {}
        migration_details = []  # 记录迁移详情
        
        for product, quadrant_list in top_products:
            valid_quadrants = [q for q in quadrant_list if q != '无数据']
            if len(valid_quadrants) >= 2:
                from_q = valid_quadrants[0]
                to_q = valid_quadrants[-1]
                key = (from_q, to_q)
                migrations[key] = migrations.get(key, 0) + 1
                migration_details.append({
                    'product': product,
                    'from': from_q,
                    'to': to_q,
                    'changed': from_q != to_q
                })
        
        # 打印调试信息
        print(f"\n📊 [桑基图] 迁移统计:")
        print(f"   总商品数: {len(migration_details)}")
        print(f"   迁移类型数: {len(migrations)}")
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            status = "→" if from_q != to_q else "="
            print(f"   {from_q} {status} {to_q}: {count}个")
        
        # 构建桑基图节点和链接
        nodes = []
        links = []
        node_set = set()  # 用于去重
        
        # 只添加实际出现的节点
        for (from_q, to_q), count in migrations.items():
            if count > 0:
                source_node = f'{from_q}\n(第1{period_label})'
                target_node = f'{to_q}\n(第{len(periods)}{period_label})'
                
                if source_node not in node_set:
                    nodes.append({'name': source_node})
                    node_set.add(source_node)
                
                if target_node not in node_set:
                    nodes.append({'name': target_node})
                    node_set.add(target_node)
                
                links.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count
                })
        
        if not links:
            return dbc.Alert("暂无商品象限迁移数据", color="info", className="mb-3")
        
        # 创建迁移统计表格
        migration_stats = []
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            if from_q != to_q:
                trend = "📉 恶化" if from_q.startswith('🌟') and to_q.startswith('❌') else "📈 改善" if to_q.startswith('🌟') else "🔄 变化"
            else:
                trend = "➡️ 稳定"
            
            migration_stats.append({
                '起始象限': from_q,
                '当前象限': to_q,
                '趋势': trend,
                '商品数': count
            })
        
        stats_df = pd.DataFrame(migration_stats)
        
        option = {
            'tooltip': {
                'trigger': 'item',
                'triggerOn': 'mousemove'
            },
            'series': [{
                'type': 'sankey',
                'emphasis': {
                    'focus': 'adjacency'
                },
                'nodeWidth': 20,
                'nodeGap': 15,
                'layoutIterations': 32,
                'orient': 'horizontal',
                'draggable': False,
                'data': nodes,
                'links': links,
                'lineStyle': {
                    'color': 'gradient',
                    'curveness': 0.5
                },
                'label': {
                    'fontSize': 11,
                    'color': '#000'
                }
            }]
        }
        
        return html.Div([
            html.H6(f"📊 象限迁移可视化 (TOP 20商品)", className="mb-3"),
            html.Small(f"分析周期: 第1{period_label} → 第{len(periods)}{period_label}，线条粗细表示迁移商品数量", className="text-muted d-block mb-2"),
            
            dbc.Row([
                dbc.Col([
                    DashECharts(
                        option=option,
                        style={'height': '500px', 'width': '100%'}
                    )
                ], md=8),
                
                dbc.Col([
                    html.H6("迁移统计", className="mb-2"),
                    dbc.Table.from_dataframe(
                        stats_df,
                        striped=True,
                        bordered=True,
                        hover=True,
                        size='sm'
                    )
                ], md=4)
            ]),
            
            html.Small(f"💡 提示: 稳定在同一象限的商品说明表现一致，跨象限迁移的商品需要重点关注", className="text-muted d-block mt-2")
        ])
        
    except Exception as e:
        print(f"❌ [桑基图生成] 错误: {e}")
        return html.Div()


# ==================== Tab 2 子回调: 四象限商品表格 ====================
@app.callback(
    Output('quadrant-product-table', 'children'),
    [Input('quadrant-filter', 'value'),
     Input('product-agg-data', 'data')]
)
def update_quadrant_table(quadrant_filter, product_data):
    """更新四象限商品列表"""
    if not product_data:
        return html.Div("暂无数据")
    
    try:
        df = pd.DataFrame(product_data)
        
        # 筛选
        if quadrant_filter != 'all':
            df_filtered = df[df['象限分类'] == quadrant_filter].copy()
        else:
            df_filtered = df.copy()
        
        # 按销售额排序
        df_filtered = df_filtered.sort_values('销售额', ascending=False).head(50)
        
        # 准备表格数据（✅ 增加盈利健康度字段）
        table_df = df_filtered[[
            '商品名称', '象限分类', '盈利健康度', '盈利订单占比', '利润率', '动销指数', 
            '销售额', '实际利润', '总销量', '库存', '经营建议'
        ]].copy()
        
        # 格式化
        table_df['盈利订单占比'] = table_df['盈利订单占比'].apply(lambda x: f'{x:.0f}%')
        table_df['利润率'] = table_df['利润率'].apply(lambda x: f'{x:.1f}%')
        table_df['动销指数'] = table_df['动销指数'].apply(lambda x: f'{x:.3f}')
        table_df['销售额'] = table_df['销售额'].apply(lambda x: f'¥{x:,.0f}')
        table_df['实际利润'] = table_df['实际利润'].apply(lambda x: f'¥{x:,.0f}')
        table_df['总销量'] = table_df['总销量'].apply(lambda x: f'{int(x)}件')
        table_df['库存'] = table_df['库存'].apply(lambda x: f'{int(x)}件')
        
        # 重命名列
        table_df.columns = ['商品名称', '象限', '盈利健康度', '盈利订单%', '利润率', '动销指数', 
                           '销售额', '实际利润', '销量', '库存', '💡 经营建议']
        
        table = dbc.Table.from_dataframe(
            table_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        )
        
        return html.Div([
            html.H5(f'商品列表（共 {len(df_filtered)} 个商品）', className="mb-3"),
            table
        ])
        
    except Exception as e:
        print(f"❌ [四象限表格] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"数据处理错误: {e}")


# ==================== Tab 2 子回调: 导出四象限数据 ====================
@app.callback(
    Output('download-quadrant-data', 'data'),
    Input('btn-export-quadrant', 'n_clicks'),
    State('product-agg-data', 'data'),
    prevent_initial_call=True
)
def export_quadrant_data(n_clicks, product_data):
    """导出四象限分析数据到Excel"""
    if not n_clicks or not product_data:
        return None
    
    try:
        df = pd.DataFrame(product_data)
        
        # 创建Excel写入器
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Sheet 1: 全部数据
            full_data = df[[
                '商品名称', '店内码', '一级分类名', '三级分类名', '象限分类',
                '利润率', '动销指数', '销售额', '实际利润', '总销量', 
                '库存', '库存周转率', '订单数', '经营建议'
            ]].copy()
            full_data.columns = [
                '商品名称', '店内码', '一级分类', '三级分类', '象限分类',
                '利润率(%)', '动销指数', '销售额(元)', '实际利润(元)', '总销量', 
                '库存', '库存周转率', '订单数', '经营建议'
            ]
            full_data.to_excel(writer, sheet_name='全部商品', index=False)
            
            # Sheet 2-5: 各象限数据
            quadrants = [
                ('🌟 高利润高动销', '明星产品'),
                ('⚠️ 高利润低动销', '问题产品'),
                ('🚀 低利润高动销', '引流产品'),
                ('❌ 低利润低动销', '淘汰产品')
            ]
            
            for quadrant, sheet_name in quadrants:
                quad_data = df[df['象限分类'] == quadrant][[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '利润率', '动销指数', '销售额', '实际利润', '总销量', 
                    '库存', '库存周转率', '经营建议'
                ]].copy()
                
                if len(quad_data) > 0:
                    quad_data.columns = [
                        '商品名称', '店内码', '一级分类', '三级分类',
                        '利润率(%)', '动销指数', '销售额(元)', '实际利润(元)', '总销量', 
                        '库存', '库存周转率', '经营建议'
                    ]
                    quad_data = quad_data.sort_values('销售额(元)', ascending=False)
                    quad_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"✅ {sheet_name}: {len(quad_data)} 个商品")
        
        output.seek(0)
        
        return dcc.send_bytes(
            output.getvalue(),
            f"商品四象限分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
    except Exception as e:
        print(f"❌ 四象限数据导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== Tab 2 子回调: 商品排行图表 ====================
@app.callback(
    [Output('product-ranking-chart', 'children'),
     Output('product-ranking-table', 'children')],
    [Input('product-rank-dimension', 'value'),
     Input('product-rank-limit', 'value'),
     Input('product-agg-data', 'data')]
)
def update_product_ranking(dimension, limit, product_data):
    """更新商品排行图表和表格（✅ ECharts升级版）"""
    if not product_data:
        return html.Div("暂无数据"), html.Div()
    
    try:
        df = pd.DataFrame(product_data)
        
        # 调试信息
        print(f"\n🔍 [商品排行] 数据检查:")
        print(f"   DataFrame行数: {len(df)}")
        print(f"   DataFrame列: {df.columns.tolist()}")
        print(f"   选择维度: {dimension}")
        print(f"   显示数量: {limit}")
        
        # 检查维度是否存在
        if dimension not in df.columns:
            available_cols = df.columns.tolist()
            return html.Div([
                html.H5("⚠️ 数据字段错误", className="text-warning"),
                html.P(f"未找到字段: {dimension}"),
                html.P(f"可用字段: {', '.join(available_cols)}")
            ]), html.Div()
        
        # 检查是否有数据
        if len(df) == 0:
            return html.Div("暂无商品数据"), html.Div()
        
        # 排序并取前N名
        top_products = df.nlargest(min(limit, len(df)), dimension)
        print(f"   排序后商品数: {len(top_products)}")
        
    except Exception as e:
        print(f"❌ [商品排行] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"数据处理错误: {e}"), html.Div()
    
    # 准备数据（保留1位小数）
    product_names = top_products['商品名称'].tolist()[::-1]  # 倒序显示，最高在上
    values = [round(float(x), 1) for x in top_products[dimension].tolist()[::-1]]
    
    # 截断过长的商品名称
    product_names_display = [name[:30] + '...' if len(name) > 30 else name for name in product_names]
    
    # 维度配置
    dimension_config = {
        '销售额': {'unit': '¥', 'color': ['#4A90E2', '#7BA7D6'], 'suffix': ''},
        '实际利润': {'unit': '¥', 'color': ['#2ECC71', '#5FD68A'], 'suffix': ''},
        '利润率': {'unit': '', 'color': ['#F39C12', '#F5B041'], 'suffix': '%'},
        '总销量': {'unit': '', 'color': ['#9B59B6', '#BB8FCE'], 'suffix': '件'},
        '订单数': {'unit': '', 'color': ['#E74C3C', '#EC7063'], 'suffix': '单'}
    }
    
    config = dimension_config.get(dimension, {'unit': '', 'color': ['#4A90E2', '#7BA7D6'], 'suffix': ''})
    
    # 创建 ECharts 图表
    if ECHARTS_AVAILABLE:
        option = {
            'grid': {
                'left': '5%',
                'right': '15%',
                'top': '3%',
                'bottom': '3%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'value',
                'axisLabel': {
                    'formatter': f'{config["unit"]}{{value}}{config["suffix"]}',
                    'fontSize': 11
                },
                'splitLine': {
                    'lineStyle': {
                        'type': 'dashed',
                        'color': '#e0e0e0'
                    }
                }
            },
            'yAxis': {
                'type': 'category',
                'data': product_names_display,
                'axisLabel': {
                    'fontSize': 10,
                    'interval': 0
                },
                'axisTick': {'show': False},
                'axisLine': {'show': False}
            },
            'series': [{
                'type': 'bar',
                'data': values,
                'barWidth': '70%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                        'colorStops': [
                            {'offset': 0, 'color': config['color'][0]},
                            {'offset': 1, 'color': config['color'][1]}
                        ]
                    },
                    'borderRadius': [0, 4, 4, 0]
                },
                'label': {
                    'show': True,
                    'position': 'right',
                    'formatter': f'{config["unit"]}{{c}}{config["suffix"]}',
                    'fontSize': 10,
                    'color': '#333'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 15,
                        'shadowColor': 'rgba(0,0,0,0.3)'
                    }
                }
            }],
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'},
                'formatter': '{b}<br/>{a0}: ' + f'{config["unit"]}{{c}}{config["suffix"]}'
            },
            'animationEasing': 'elasticOut',
            'animationDuration': 1000
        }
        
        # 用 html.Div 包装 ECharts
        # 动态计算高度：每个商品35px + 上下边距80px，但最大不超过800px
        chart_height = min(len(top_products) * 35 + 80, 800)
        
        fig = html.Div([
            html.H5(f'TOP {limit} 商品 - 按{dimension}排序', className="text-center mb-3"),
            html.Div([
                DashECharts(
                    option=option,
                    style={'height': f'{chart_height}px', 'width': '100%'}
                )
            ], style={
                'maxHeight': '800px',
                'overflowY': 'auto' if len(top_products) > 20 else 'visible'
            })
        ])
    else:
        # Plotly 备份
        plotly_fig = go.Figure()
        
        plotly_fig.add_trace(go.Bar(
            y=product_names_display,
            x=values,
            orientation='h',
            marker=dict(
                color=values,
                colorscale='Blues',
                showscale=False
            ),
            text=[f"{config['unit']}{v:.2f}{config['suffix']}" for v in values],
            textposition='outside'
        ))
        
        plotly_fig.update_layout(
            title=f'TOP {limit} 商品 - 按{dimension}排序',
            xaxis_title=f'{dimension} ({config["unit"]}{config["suffix"]})',
            yaxis_title='',
            height=max(400, limit * 25),
            margin=dict(l=200, r=50, t=50, b=50),
            hovermode='closest'
        )
        
        fig = dcc.Graph(figure=plotly_fig)
    
    # 创建详细数据表
    table_df = top_products[[
        '商品名称', '总销量', '销售额', '实际利润', '利润率', 
        '平均售价', '库存', '库存周转率', '订单数'
    ]].copy()
    
    # 格式化数值（统一保留1位小数）
    table_df['销售额'] = table_df['销售额'].apply(lambda x: f'¥{x:,.1f}')
    table_df['实际利润'] = table_df['实际利润'].apply(lambda x: f'¥{x:,.1f}')
    table_df['利润率'] = table_df['利润率'].apply(lambda x: f'{x:.1f}%')
    table_df['平均售价'] = table_df['平均售价'].apply(lambda x: f'¥{x:.1f}')
    table_df['库存周转率'] = table_df['库存周转率'].apply(lambda x: f'{x:.1f}')
    table_df['总销量'] = table_df['总销量'].apply(lambda x: f'{int(x)}件')
    table_df['订单数'] = table_df['订单数'].apply(lambda x: f'{int(x)}单')
    table_df['库存'] = table_df['库存'].apply(lambda x: f'{int(x)}件')
    
    # 重命名列
    table_df.columns = ['商品名称', '销量', '销售额', '实际利润', '利润率', 
                        '平均售价', '库存', '库存周转率', '订单数']
    
    table = dbc.Table.from_dataframe(
        table_df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size='sm',
        className="mt-3"
    )
    
    return fig, table


# ==================== Tab 2 子回调: 分类分析图表 ====================
@app.callback(
    [Output('category-sales-chart', 'children'),
     Output('category-profit-chart', 'children')],
    Input('category-sales-data', 'data')
)
def update_category_charts(category_data):
    """更新分类分析图表（✅ ECharts升级版）"""
    if not category_data:
        # 无分类数据时显示空提示
        empty_div = html.Div([
            html.P("暂无分类数据", className="text-center text-muted", style={'padding': '50px'})
        ])
        return empty_div, empty_div
    
    df = pd.DataFrame(category_data)
    
    # ===== 1. 销售额分布饼图 =====
    if ECHARTS_AVAILABLE:
        # 准备数据（保留1位小数）
        pie_data = [
            {'value': round(float(row['销售额']), 1), 'name': row['分类']} 
            for _, row in df.iterrows()
        ]
        
        option_sales = {
            'tooltip': {
                'trigger': 'item',
                'formatter': '{b}<br/>销售额: ¥{c}<br/>占比: {d}%'
            },
            'legend': {
                'orient': 'vertical',
                'left': 'left',
                'top': 'middle',
                'textStyle': {'fontSize': 11},
                'itemGap': 8,
                'itemWidth': 20,
                'itemHeight': 14
            },
            'series': [{
                'name': '销售额',
                'type': 'pie',
                'radius': ['45%', '75%'],
                'center': ['60%', '50%'],
                'avoidLabelOverlap': True,
                'itemStyle': {
                    'borderRadius': 8,
                    'borderColor': '#fff',
                    'borderWidth': 3
                },
                'label': {
                    'show': True,
                    'position': 'outside',
                    'formatter': '{d}%',
                    'fontSize': 12,
                    'fontWeight': 'bold',
                    'color': '#333'
                },
                'labelLine': {
                    'show': True,
                    'length': 15,
                    'length2': 10,
                    'smooth': True
                },
                'emphasis': {
                    'label': {
                        'show': True,
                        'fontSize': 16,
                        'fontWeight': 'bold'
                    },
                    'itemStyle': {
                        'shadowBlur': 20,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0,0,0,0.5)'
                    }
                },
                'data': pie_data
            }],
            'color': ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
        }
        
        fig_sales = html.Div([
            html.H5('分类销售额分布', className="text-center mb-3"),
            DashECharts(option=option_sales, style={'height': '550px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig = go.Figure(data=[go.Pie(
            labels=df['分类'],
            values=df['销售额'],
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Set3),
            textinfo='label+percent'
        )])
        plotly_fig.update_layout(title='分类销售额分布', height=400)
        fig_sales = dcc.Graph(figure=plotly_fig)
    
    # ===== 2. 实际利润对比柱状图 =====
    if ECHARTS_AVAILABLE:
        categories = df['分类'].tolist()
        # 保留1位小数
        profits = [round(float(x), 1) for x in df['实际利润'].tolist()]
        profit_rates = [round(float(x), 1) for x in df['利润率'].tolist()]
        
        option_profit = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'},
                'formatter': '{b0}<br/>实际利润: ¥{c0}<br/>利润率: {c1}%'
            },
            'legend': {
                'data': ['实际利润', '利润率'],
                'top': '5%'
            },
            'grid': {
                'left': '3%',
                'right': '8%',
                'bottom': '3%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': categories,
                'axisLabel': {
                    'rotate': 30,
                    'fontSize': 11
                }
            },
            'yAxis': [
                {
                    'type': 'value',
                    'name': '实际利润 (¥)',
                    'position': 'left',
                    'axisLabel': {'formatter': '¥{value}'}
                },
                {
                    'type': 'value',
                    'name': '利润率 (%)',
                    'position': 'right',
                    'axisLabel': {'formatter': '{value}%'}
                }
            ],
            'series': [
                {
                    'name': '实际利润',
                    'type': 'bar',
                    'data': profits,
                    'barWidth': '60%',
                    'itemStyle': {
                        'color': {
                            'type': 'linear',
                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                            'colorStops': [
                                {'offset': 0, 'color': '#2ECC71'},
                                {'offset': 1, 'color': '#5FD68A'}
                            ]
                        },
                        'borderRadius': [4, 4, 0, 0]
                    },
                    'label': {
                        'show': True,
                        'position': 'top',
                        'formatter': '¥{c}',
                        'fontSize': 10
                    }
                },
                {
                    'name': '利润率',
                    'type': 'line',
                    'yAxisIndex': 1,
                    'data': profit_rates,
                    'itemStyle': {'color': '#E74C3C'},
                    'lineStyle': {'width': 2},
                    'symbol': 'circle',
                    'symbolSize': 8,
                    'label': {
                        'show': True,
                        'position': 'top',
                        'formatter': '{c}%',
                        'fontSize': 10
                    }
                }
            ]
        }
        
        fig_profit = html.Div([
            html.H5('分类利润分析', className="text-center mb-3"),
            DashECharts(option=option_profit, style={'height': '500px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig_profit = go.Figure(data=[go.Bar(
            x=df['分类'],
            y=df['实际利润'],
            marker=dict(color=df['实际利润'], colorscale='Greens'),
            text=df['实际利润'].round(2),
            textposition='outside'
        )])
        plotly_fig_profit.update_layout(
            title='分类实际利润对比',
            xaxis_title='商品分类',
            yaxis_title='实际利润 (元)',
            height=400
        )
        fig_profit = dcc.Graph(figure=plotly_fig_profit)
    
    return fig_sales, fig_profit


# ==================== Tab 2 子回调: 商品结构分析 ====================
@app.callback(
    [Output('price-range-chart', 'children'),
     Output('abc-analysis-chart', 'children')],
    Input('product-agg-data', 'data')
)
def update_structure_charts(product_data):
    """更新商品结构分析图表（✅ ECharts升级版）"""
    if not product_data:
        empty_div = html.Div("暂无数据")
        return empty_div, empty_div
    
    df = pd.DataFrame(product_data)
    
    # ===== 1. 价格区间分析 =====
    price_bins = [0, 5, 10, 20, 50, 100, 500, float('inf')]
    price_labels = ['0-5元', '5-10元', '10-20元', '20-50元', '50-100元', '100-500元', '500元以上']
    
    df['价格区间'] = pd.cut(df['平均售价'], bins=price_bins, labels=price_labels, include_lowest=True)
    price_dist = df['价格区间'].value_counts().sort_index()
    
    if ECHARTS_AVAILABLE:
        option_price = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'},
                'formatter': '{b}<br/>商品数量: {c}个'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '10%',
                'top': '10%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': price_dist.index.astype(str).tolist(),
                'axisLabel': {
                    'rotate': 30,
                    'fontSize': 11
                }
            },
            'yAxis': {
                'type': 'value',
                'name': '商品数量',
                'axisLabel': {'formatter': '{value}个'}
            },
            'series': [{
                'type': 'bar',
                'data': price_dist.values.tolist(),
                'barWidth': '60%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': '#4A90E2'},
                            {'offset': 1, 'color': '#A8D5FF'}
                        ]
                    },
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}',
                    'fontSize': 11
                }
            }]
        }
        
        fig_price = html.Div([
            html.H5('商品价格区间分布', className="text-center mb-3"),
            DashECharts(option=option_price, style={'height': '400px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig_price = go.Figure(data=[go.Bar(
            x=price_dist.index.astype(str),
            y=price_dist.values,
            marker=dict(color='lightblue'),
            text=price_dist.values,
            textposition='outside'
        )])
        plotly_fig_price.update_layout(
            title='商品价格区间分布',
            xaxis_title='价格区间',
            yaxis_title='商品数量',
            height=400
        )
        fig_price = dcc.Graph(figure=plotly_fig_price)
    
    # ===== 2. ABC分类（帕累托分析） =====
    # 按销售额排序
    df_sorted = df.sort_values('销售额', ascending=False).reset_index(drop=True)
    df_sorted['累计销售额'] = df_sorted['销售额'].cumsum()
    df_sorted['累计占比'] = df_sorted['累计销售额'] / df_sorted['销售额'].sum() * 100
    
    # ABC分类
    df_sorted['ABC分类'] = 'C'
    df_sorted.loc[df_sorted['累计占比'] <= 80, 'ABC分类'] = 'A'
    df_sorted.loc[(df_sorted['累计占比'] > 80) & (df_sorted['累计占比'] <= 95), 'ABC分类'] = 'B'
    
    abc_counts = df_sorted['ABC分类'].value_counts()
    
    if ECHARTS_AVAILABLE:
        # 准备ABC数据
        abc_data = []
        for label in ['A', 'B', 'C']:
            if label in abc_counts.index:
                abc_data.append({
                    'value': int(abc_counts[label]),
                    'name': f'{label}类商品'
                })
        
        option_abc = {
            'tooltip': {
                'trigger': 'item',
                'formatter': '{b}<br/>数量: {c}<br/>占比: {d}%'
            },
            'legend': {
                'orient': 'vertical',
                'right': '5%',
                'top': 'center',
                'textStyle': {'fontSize': 12}
            },
            'series': [{
                'name': 'ABC分类',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'center': ['40%', '50%'],
                'avoidLabelOverlap': True,
                'itemStyle': {
                    'borderRadius': 8,
                    'borderColor': '#fff',
                    'borderWidth': 2
                },
                'label': {
                    'show': True,
                    'formatter': '{b}\n{c}个\n({d}%)',
                    'fontSize': 11
                },
                'emphasis': {
                    'label': {
                        'show': True,
                        'fontSize': 14,
                        'fontWeight': 'bold'
                    },
                    'itemStyle': {
                        'scale': 1.1,
                        'shadowBlur': 15,
                        'shadowColor': 'rgba(0,0,0,0.3)'
                    }
                },
                'data': abc_data
            }],
            'color': ['#2ECC71', '#F39C12', '#E74C3C']  # A绿色, B橙色, C红色
        }
        
        fig_abc = html.Div([
            html.H5('ABC分类法（帕累托分析）', className="text-center mb-3"),
            html.P('A类: 80%销售额 | B类: 80-95%销售额 | C类: 95-100%销售额', 
                   className="text-center text-muted small mb-3"),
            DashECharts(option=option_abc, style={'height': '400px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig_abc = go.Figure(data=[go.Pie(
            labels=[f'{label}类商品' for label in abc_counts.index],
            values=abc_counts.values,
            hole=0.3,
            marker=dict(colors=['#2ECC71', '#F39C12', '#E74C3C']),
            textinfo='label+value+percent'
        )])
        plotly_fig_abc.update_layout(
            title='ABC分类法（帕累托分析）',
            height=400
        )
        fig_abc = dcc.Graph(figure=plotly_fig_abc)
    
    return fig_price, fig_abc


# ==================== Tab 2 子回调: 库存预警 ====================
@app.callback(
    Output('inventory-warning-section', 'children'),
    Input('product-agg-data', 'data')
)
def update_inventory_warnings(product_data):
    """更新库存与滞销预警"""
    if not product_data:
        return html.Div()
    
    df = pd.DataFrame(product_data)
    
    warnings = []
    
    # 1. 缺货预警
    out_of_stock = df[df['库存'] <= 0]
    if len(out_of_stock) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("🔴 缺货预警", className="alert-heading"),
                html.P(f"发现 {len(out_of_stock)} 个商品缺货，可能影响销售"),
                html.Hr(),
                html.P("缺货商品列表:", className="mb-2"),
                html.Ul([html.Li(f"{row['商品名称']} (历史销量: {row['总销量']}件)") 
                        for _, row in out_of_stock.nlargest(10, '总销量').iterrows()])
            ], color="danger")
        )
    
    # 2. 滞销预警（库存高但销量低）
    df['滞销指数'] = df['库存'] / (df['总销量'] + 1)  # 避免除零
    slow_moving = df[(df['库存'] > 10) & (df['滞销指数'] > 5)].nlargest(10, '滞销指数')
    
    if len(slow_moving) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("⚠️ 滞销预警", className="alert-heading"),
                html.P(f"发现 {len(slow_moving)} 个商品存在滞销风险（库存高、销量低）"),
                html.Hr(),
                html.P("滞销商品列表:", className="mb-2"),
                html.Ul([html.Li(f"{row['商品名称']} - 库存:{int(row['库存'])} / 销量:{int(row['总销量'])} (滞销指数:{row['滞销指数']:.1f})") 
                        for _, row in slow_moving.iterrows()])
            ], color="warning")
        )
    
    # 3. 低周转率预警
    low_turnover = df[(df['库存'] > 0) & (df['库存周转率'] < 0.5) & (df['库存周转率'] > 0)]
    if len(low_turnover) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("📊 低周转率预警", className="alert-heading"),
                html.P(f"发现 {len(low_turnover)} 个商品周转率过低（<0.5）"),
                html.Hr(),
                html.P("建议: 考虑促销或优化库存策略", className="text-muted")
            ], color="info")
        )
    
    # 4. 畅销但库存不足
    hot_low_stock = df[(df['总销量'] > df['总销量'].quantile(0.75)) & (df['库存'] < df['库存'].quantile(0.25))]
    if len(hot_low_stock) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("🔥 畅销品库存不足", className="alert-heading"),
                html.P(f"发现 {len(hot_low_stock)} 个畅销商品库存不足，建议及时补货"),
                html.Hr(),
                html.Ul([html.Li(f"{row['商品名称']} - 销量:{int(row['总销量'])} / 库存:{int(row['库存'])}") 
                        for _, row in hot_low_stock.iterrows()])
            ], color="success")
        )
    
    if not warnings:
        warnings.append(
            dbc.Alert("✅ 库存状态良好，未发现明显异常", color="success")
        )
    
    return html.Div(warnings)


# ==================== Tab 2 子回调: 导出库存预警数据 ====================
@app.callback(
    Output('download-inventory-warnings', 'data'),
    Input('btn-export-inventory-warnings', 'n_clicks'),
    State('product-agg-data', 'data'),
    prevent_initial_call=True
)
def export_inventory_warnings(n_clicks, product_data):
    """导出库存与滞销预警数据到Excel（分Sheet）"""
    if not n_clicks or not product_data:
        return None
    
    try:
        df = pd.DataFrame(product_data)
        
        # 创建Excel写入器
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # ===== Sheet 1: 缺货预警 =====
            out_of_stock = df[df['库存'] <= 0].copy()
            if len(out_of_stock) > 0:
                out_of_stock_export = out_of_stock[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '总销量', '库存', '销售额', '实际利润', 
                    '利润率', '订单数', '平均售价'
                ]].sort_values('总销量', ascending=False)
                out_of_stock_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '历史销量', '当前库存', '销售额(元)', '实际利润(元)',
                    '利润率(%)', '订单数', '平均售价(元)'
                ]
                out_of_stock_export.to_excel(writer, sheet_name='缺货预警', index=False)
                print(f"✅ 缺货预警: {len(out_of_stock)} 个商品")
            
            # ===== Sheet 2: 滞销预警 =====
            df['滞销指数'] = df['库存'] / (df['总销量'] + 1)
            slow_moving = df[(df['库存'] > 10) & (df['滞销指数'] > 5)].copy()
            if len(slow_moving) > 0:
                slow_moving_export = slow_moving[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '库存', '总销量', '滞销指数', '销售额', 
                    '实际利润', '利润率', '库存周转率'
                ]].sort_values('滞销指数', ascending=False)
                slow_moving_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '当前库存', '累计销量', '滞销指数', '销售额(元)',
                    '实际利润(元)', '利润率(%)', '库存周转率'
                ]
                slow_moving_export.to_excel(writer, sheet_name='滞销预警', index=False)
                print(f"✅ 滞销预警: {len(slow_moving)} 个商品")
            
            # ===== Sheet 3: 低周转率预警 =====
            low_turnover = df[(df['库存'] > 0) & (df['库存周转率'] < 0.5) & (df['库存周转率'] > 0)].copy()
            if len(low_turnover) > 0:
                low_turnover_export = low_turnover[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '库存周转率', '库存', '总销量', '销售额',
                    '实际利润', '利润率'
                ]].sort_values('库存周转率')
                low_turnover_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '库存周转率', '当前库存', '累计销量', '销售额(元)',
                    '实际利润(元)', '利润率(%)'
                ]
                low_turnover_export.to_excel(writer, sheet_name='低周转率预警', index=False)
                print(f"✅ 低周转率预警: {len(low_turnover)} 个商品")
            
            # ===== Sheet 4: 畅销缺货预警 =====
            hot_low_stock = df[
                (df['总销量'] > df['总销量'].quantile(0.75)) & 
                (df['库存'] < df['库存'].quantile(0.25))
            ].copy()
            if len(hot_low_stock) > 0:
                hot_low_stock_export = hot_low_stock[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '总销量', '库存', '库存周转率', '销售额',
                    '实际利润', '利润率', '订单数'
                ]].sort_values('总销量', ascending=False)
                hot_low_stock_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '累计销量', '当前库存', '库存周转率', '销售额(元)',
                    '实际利润(元)', '利润率(%)', '订单数'
                ]
                hot_low_stock_export.to_excel(writer, sheet_name='畅销缺货预警', index=False)
                print(f"✅ 畅销缺货预警: {len(hot_low_stock)} 个商品")
            
            # ===== Sheet 5: 完整商品库存数据 =====
            full_inventory = df[[
                '商品名称', '店内码', '一级分类名', '三级分类名',
                '库存', '总销量', '库存周转率', '滞销指数',
                '销售额', '成本', '实际利润', '利润率', '订单数', '平均售价', '平均成本'
            ]].copy()
            full_inventory.columns = [
                '商品名称', '店内码', '一级分类', '三级分类',
                '当前库存', '累计销量', '库存周转率', '滞销指数',
                '销售额(元)', '成本(元)', '实际利润(元)', '利润率(%)', 
                '订单数', '平均售价(元)', '平均成本(元)'
            ]
            full_inventory = full_inventory.sort_values('库存周转率', ascending=False)
            full_inventory.to_excel(writer, sheet_name='完整库存数据', index=False)
            print(f"✅ 完整库存数据: {len(full_inventory)} 个商品")
        
        output.seek(0)
        
        return dcc.send_bytes(
            output.getvalue(),
            f"库存与滞销预警_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
    except Exception as e:
        print(f"❌ 库存预警导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== Tab 5: 时段场景分析 辅助函数 ====================

def extract_time_features_for_scenario(df: pd.DataFrame) -> pd.DataFrame:
    """
    提取时间特征用于场景分析
    ✅ 使用统一的scene_inference模块（与Tab 4保持一致）
    """
    df = df.copy()
    
    # ✅ 调用统一的场景推断模块（与Tab 4、数据加载时保持完全一致）
    if '时段' not in df.columns or '场景' not in df.columns:
        df = add_scene_and_timeslot_fields(df)
    
    return df


def calculate_period_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """计算时段指标（与Tab 1/Tab 2保持一致的计算逻辑）"""
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    
    metrics = []
    for period in period_order:
        period_df = df[df['时段'] == period]
        if len(period_df) == 0:
            continue
        
        order_count = period_df['订单ID'].nunique()
        item_count = len(period_df)
        
        # 🔧 修复: 按订单ID分组汇总,避免多商品订单重复计算
        # 销售额: 按订单汇总后再求和
        if '实收价格' in period_df.columns:
            order_sales = period_df.groupby('订单ID')['实收价格'].sum()
            total_sales = order_sales.sum()
            avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        else:
            order_sales = period_df.groupby('订单ID')['商品实售价'].sum()
            total_sales = order_sales.sum()
            avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        
        # 利润额: 按订单汇总
        if '实际利润' in period_df.columns:
            total_profit = period_df.groupby('订单ID')['实际利润'].sum().sum()
        elif '利润额' in period_df.columns:
            total_profit = period_df.groupby('订单ID')['利润额'].sum().sum()
        else:
            total_profit = 0
        
        # 利润率计算
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        metrics.append({
            '时段': period,
            '订单量': order_count,
            '商品数': item_count,
            '销售额': total_sales,
            '平均客单价': avg_order_value,
            '利润额': total_profit,
            '利润率': profit_rate
        })
    
    return pd.DataFrame(metrics)


def calculate_scenario_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """计算场景指标(🔧 修复:按订单ID分组避免重复计算)"""
    
    metrics = []
    for scenario in df['场景'].unique():
        scenario_df = df[df['场景'] == scenario]
        
        order_count = scenario_df['订单ID'].nunique()
        product_count = scenario_df['商品名称'].nunique()
        item_count = len(scenario_df)
        
        # 🔧 修复: 按订单ID分组汇总销售额
        if '实收价格' in scenario_df.columns:
            order_sales = scenario_df.groupby('订单ID')['实收价格'].sum()
            total_sales = order_sales.sum()
            avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        else:
            order_sales = scenario_df.groupby('订单ID')['商品实售价'].sum()
            total_sales = order_sales.sum()
            avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        
        # 🔧 修复: 按订单ID分组汇总利润额
        if '实际利润' in scenario_df.columns:
            total_profit = scenario_df.groupby('订单ID')['实际利润'].sum().sum()
        elif '利润额' in scenario_df.columns:
            total_profit = scenario_df.groupby('订单ID')['利润额'].sum().sum()
        else:
            total_profit = 0
        
        # 利润率计算
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        metrics.append({
            '场景': scenario,
            '订单量': order_count,
            '商品数': item_count,
            '销售额': total_sales,
            '平均客单价': avg_order_value,
            '利润额': total_profit,
            '利润率': profit_rate
        })
    
    scenario_metrics = pd.DataFrame(metrics)
    
    return scenario_metrics.sort_values('销售额', ascending=False)


# ==================== Tab 3-7 占位符 ====================


@app.callback(
    Output('tab-3-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab3_content(active_tab):
    if active_tab != 'tab-3':
        raise PreventUpdate
    return dbc.Alert("💰 价格对比分析功能开发中...", color="info", className="text-center")


# Tab 3.5: 成本优化分析
@app.callback(
    Output('tab-cost-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('data-update-trigger', 'data')]
)
def render_cost_optimization_tab(active_tab, trigger):
    """渲染成本优化分析Tab"""
    if active_tab != 'tab-cost-optimization':
        raise PreventUpdate
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Container([
            dbc.Alert("⚠️ 未找到数据，请检查数据文件", color="warning")
        ])
    
    df = GLOBAL_DATA.copy()
    
    # 计算订单指标
    try:
        order_agg = calculate_order_metrics(df)
    except ValueError as e:
        return dbc.Container([
            dbc.Alert(f"❌ {str(e)}", color="danger")
        ])
    
    # 执行成本优化分析
    cost_analysis = analyze_cost_optimization(df, order_agg)
    
    # 计算总体成本占比
    total_sales = order_agg['商品实售价'].sum()
    total_profit = order_agg['订单实际利润'].sum()
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    product_cost_rate = cost_analysis['product_cost_analysis']['avg_cost_rate']
    logistics_cost_rate = cost_analysis['logistics_cost_analysis']['logistics_cost_rate']
    marketing_cost_rate = cost_analysis['marketing_cost_analysis']['marketing_cost_rate']
    
    return html.Div([
        html.H3("💡 成本优化分析", className="mb-4"),
        html.P("深度分析成本结构,识别优化机会,提升盈利能力", className="text-muted mb-4"),
        
        # 成本结构概览
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 综合利润率", className="card-title"),
                        html.H3(f"{profit_rate:.2f}%", className="text-primary mb-2"),
                        html.P("利润 / 商品销售额", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📦 商品成本占比", className="card-title"),
                        html.H3(f"{product_cost_rate:.2f}%", 
                               className="text-danger" if product_cost_rate > 70 else "text-success"),
                        html.P(f"基准: ≤70%", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🚚 履约成本占比", className="card-title"),
                        html.H3(f"{logistics_cost_rate:.2f}%", 
                               className="text-danger" if logistics_cost_rate > 15 else "text-success"),
                        html.P(f"基准: ≤15%", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📢 营销成本占比", className="card-title"),
                        html.H3(f"{marketing_cost_rate:.2f}%", 
                               className="text-danger" if marketing_cost_rate > 10 else "text-success"),
                        html.P(f"基准: ≤10%", className="text-muted small")
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
        ], className="mb-4"),
        
        # 三个优化分析子模块
        dbc.Tabs([
            # 1. 商品成本优化
            dbc.Tab(label="📦 商品成本优化", children=[
                html.Div([
                    render_product_cost_optimization(cost_analysis['product_cost_analysis'])
                ], className="p-3")
            ]),
            
            # 2. 履约成本优化
            dbc.Tab(label="🚚 履约成本优化", children=[
                html.Div([
                    render_logistics_cost_optimization(cost_analysis['logistics_cost_analysis'])
                ], className="p-3")
            ]),
            
            # 3. 营销成本优化
            dbc.Tab(label="📢 营销成本优化", children=[
                html.Div([
                    render_marketing_cost_optimization(cost_analysis['marketing_cost_analysis'])
                ], className="p-3")
            ]),
        ])
    ])


def render_product_cost_optimization(analysis: Dict):
    """渲染商品成本优化分析"""
    if analysis is None:
        return dbc.Alert("暂无商品成本数据", color="info")
    
    high_cost_products = analysis['high_cost_products']
    avg_cost_rate = analysis['avg_cost_rate']
    problem_products = analysis['problem_products']
    
    return html.Div([
        html.H5("📦 商品成本优化分析", className="mb-3"),
        
        # 问题概述
        dbc.Alert([
            html.H6("🎯 优化目标", className="alert-heading"),
            html.Hr(),
            html.P(f"平均商品成本占比: {avg_cost_rate:.2f}%", className="mb-1"),
            html.P(f"发现 {problem_products} 个高成本商品（成本占比>70%且销量较高）", className="mb-1"),
            html.P("建议: 优化采购价格、调整售价或替换供应商", className="mb-0 fw-bold text-danger")
        ], color="warning" if avg_cost_rate > 70 else "success"),
        
        # 高成本商品列表
        html.H6("🔍 高成本商品明细（Top 20）", className="mt-4 mb-3"),
        
        dbc.Table.from_dataframe(
            high_cost_products[[
                '商品名称', '商品实售价', '商品采购成本', '成本占比', '毛利率', '月售'
            ]].round(2),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if not high_cost_products.empty else dbc.Alert("✅ 暂无高成本商品", color="success"),
        
        # 优化建议
        dbc.Card([
            dbc.CardHeader("💡 优化建议"),
            dbc.CardBody([
                html.Ul([
                    html.Li("优先优化销量高、成本占比高的商品"),
                    html.Li("与供应商协商批量采购折扣"),
                    html.Li("考虑提高售价（基于竞品定价）"),
                    html.Li("寻找替代供应商或商品"),
                    html.Li("适当减少高成本低毛利商品的备货")
                ])
            ])
        ], className="mt-3")
    ])


def render_logistics_cost_optimization(analysis: Dict):
    """渲染履约成本优化分析"""
    if analysis is None:
        return dbc.Alert("暂无履约成本数据", color="info")
    
    # 检查是否有履约数据
    if not analysis.get('has_logistics_data', False):
        return dbc.Alert([
            html.H6("📊 履约成本数据缺失", className="alert-heading"),
            html.Hr(),
            html.P("当前数据中未找到履约成本相关字段（配送费成本/物流配送费等）", className="mb-0"),
            html.P("建议: 上传包含完整配送费用数据的订单明细", className="mb-0 mt-2")
        ], color="warning")
    
    logistics_cost_rate = analysis['logistics_cost_rate']
    total_logistics_cost = analysis['total_logistics_cost']
    distance_stats = analysis['distance_stats']
    use_full_formula = analysis.get('use_full_formula', False)
    
    return html.Div([
        html.H5("🚚 履约成本优化分析", className="mb-3"),
        
        # 成本概况
        dbc.Alert([
            html.H6("📊 履约成本概况", className="alert-heading"),
            html.Hr(),
            html.P(f"履约净成本: ¥{total_logistics_cost:,.2f}", className="mb-1"),
            html.P(f"履约成本占比: {logistics_cost_rate:.2f}%", className="mb-1"),
            html.P(f"健康基准: ≤15%", className="mb-1"),
            html.Hr(),
            html.Small([
                "📐 计算公式: ",
                html.Code("用户支付配送费 - 配送费减免 - 物流配送费" if use_full_formula else "物流配送费"),
                html.Br(),
                html.I("(反映商家在配送环节的实际收支)" if use_full_formula else "(仅统计配送支出,未扣除用户支付)")
            ], className="text-muted"),
            html.P("建议: 提高起送金额、优化配送范围、减少低客单价订单", 
                  className="mb-0 fw-bold text-danger mt-2") if logistics_cost_rate > 15 else None
        ], color="warning" if logistics_cost_rate > 15 else "success"),
        
        # 配送距离分析
        html.H6("📍 按配送距离分析", className="mt-4 mb-3"),
        
        dbc.Table.from_dataframe(
            distance_stats[[
                '距离分组', '订单数', '销售额', '配送成本', '成本占比', '平均客单价'
            ]].round(2),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if distance_stats is not None and not distance_stats.empty else dbc.Alert("暂无配送距离数据", color="info"),
        
        # 优化建议
        dbc.Card([
            dbc.CardHeader("💡 优化建议"),
            dbc.CardBody([
                html.Ul([
                    html.Li("提高起送金额（建议≥30元），减少低客单价订单"),
                    html.Li("优化配送范围，限制远距离低客单价订单"),
                    html.Li("设置配送费阶梯（距离越远配送费越高）"),
                    html.Li("引导用户自提或合并订单"),
                    html.Li("与第三方配送平台协商降低配送费")
                ])
            ])
        ], className="mt-3")
    ])


def render_marketing_cost_optimization(analysis: Dict):
    """渲染营销成本优化分析"""
    if analysis is None:
        return dbc.Alert("暂无营销成本数据", color="info")
    
    marketing_cost_rate = analysis['marketing_cost_rate']
    marketing_roi = analysis['marketing_roi']
    marketing_breakdown = analysis['marketing_breakdown']
    channel_stats = analysis['channel_stats']
    
    return html.Div([
        html.H5("📢 营销成本优化分析", className="mb-3"),
        
        # 营销成本概况
        dbc.Alert([
            html.H6("📊 营销成本概况", className="alert-heading"),
            html.Hr(),
            html.P(f"营销成本占比: {marketing_cost_rate:.2f}%", className="mb-1"),
            html.P(f"营销ROI: {marketing_roi:.2f}x (每投入1元产生{marketing_roi:.2f}元销售额)", className="mb-1"),
            html.P(f"健康基准: ≤10%, ROI≥10x", className="mb-0"),
            html.P("建议: 停止低ROI活动、提高活动门槛、精准投放", 
                  className="mb-0 fw-bold text-danger mt-2") if marketing_cost_rate > 10 or marketing_roi < 10 else None
        ], color="warning" if marketing_cost_rate > 10 else "success"),
        
        # 营销成本构成
        html.H6("💰 营销成本构成", className="mt-4 mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(key, className="card-title"),
                        html.H4(f"¥{value:,.2f}", className="text-primary")
                    ])
                ], className="text-center shadow-sm mb-2")
            ], md=3) for key, value in marketing_breakdown.items()
        ]),
        
        # 按渠道分析
        html.H6("📱 按渠道营销效率分析", className="mt-4 mb-3"),
        
        dbc.Table.from_dataframe(
            channel_stats[[
                '渠道', '销售额', '营销成本', '营销成本占比', '营销ROI', '订单数'
            ]].round(2),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if channel_stats is not None and not channel_stats.empty else dbc.Alert("暂无渠道数据", color="info"),
        
        # 优化建议
        dbc.Card([
            dbc.CardHeader("💡 优化建议"),
            dbc.CardBody([
                html.Ul([
                    html.Li("立即停止ROI<10的营销活动"),
                    html.Li("提高满减门槛（建议满50减5，而非满30减5）"),
                    html.Li("减少商品折扣，改为赠品或积分"),
                    html.Li("代金券设置使用门槛（如满80可用）"),
                    html.Li("精准投放：针对高价值客户发券"),
                    html.Li("A/B测试不同营销策略的效果")
                ])
            ])
        ], className="mt-3")
    ])


@app.callback(
    Output('tab-5-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab5_content(active_tab):
    """Tab 5: 时段场景分析"""
    if active_tab != 'tab-5':
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        
        if df is None or len(df) == 0:
            return dbc.Alert("📊 暂无数据，请先上传数据", color="warning", className="text-center")
        
        # 提取时间特征
        df = extract_time_features_for_scenario(df)
        
        # 创建布局
        layout = html.Div([
            # 页面标题
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="bi bi-clock-history me-2"),
                        "时段场景营销分析"
                    ], className="text-primary mb-4"),
                    html.P("通过时段、场景、客单价等多维度分析,发现黄金销售时段,优化营销策略", 
                          className="text-muted")
                ])
            ], className="mb-4"),
            
            # Tab导航
            dbc.Tabs([
                # 1. 时段分析
                dbc.Tab(label="⏰ 时段订单分析", tab_id="period-analysis", children=[
                    html.Div(id='period-analysis-content', className="p-3")
                ]),
                
                # 2. 场景分析
                dbc.Tab(label="🎯 消费场景分析", tab_id="scenario-analysis", children=[
                    html.Div(id='scenario-analysis-content', className="p-3")
                ]),
                
                
                # 4. AI智能建议
                dbc.Tab(label="🤖 AI营销建议", tab_id="ai-suggestions", children=[
                    html.Div(id='ai-suggestions-content', className="p-3")
                ]),
                
                # ========== 新增扩展子Tab ==========
                # 4. 场景利润矩阵 (时段热力图 + 四象限分析)
                dbc.Tab(label="� 场景利润矩阵", tab_id="heatmap-profit", children=[
                    html.Div(id='heatmap-profit-content', className="p-3")
                ]),
                
                # 5. 时段销量趋势 + 客单价探索
                dbc.Tab(label="📈 趋势&客单价", tab_id="trend-price", children=[
                    html.Div(id='trend-price-content', className="p-3")
                ]),
                
                # 6. 商品场景关联网络
                dbc.Tab(label="🕸️ 商品场景关联", tab_id="product-network", children=[
                    html.Div(id='product-network-content', className="p-3")
                ]),
                
                # 7. 商品场景画像
                dbc.Tab(label="🏷️ 商品场景画像", tab_id="product-profile", children=[
                    html.Div(id='product-profile-content', className="p-3")
                ])
            ], id='tab5-subtabs', active_tab='period-analysis'),
            
            # 子Tab内容容器
            html.Div(id='tab5-subtab-content')
        ])
        
        return layout
        
    except Exception as e:
        print(f"❌ Tab 5渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染失败: {str(e)}", color="danger")


# ==================== Tab 5 子Tab回调 ====================

@app.callback(
    Output('tab5-subtab-content', 'children'),
    Input('tab5-subtabs', 'active_tab'),
    Input('main-tabs', 'value')
)
def render_tab5_subtab_content(active_subtab, main_tab):
    """渲染Tab 5的子Tab内容"""
    if main_tab != 'tab-5':
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        if df is None or len(df) == 0:
            return dbc.Alert("暂无数据", color="warning")
        
        print(f"🔍 Tab5 渲染: active_subtab={active_subtab}, 数据行数={len(df)}")
        
        df = extract_time_features_for_scenario(df)
        print(f"   时间特征提取后: 数据行数={len(df)}, 字段={list(df.columns)}")
        
        # 原有4个基础子Tab
        if active_subtab == 'period-analysis':
            print("   → 进入 period-analysis 分支")
            result = render_period_analysis(df)
            print(f"   ← period-analysis 返回: {type(result)}")
            return result
        elif active_subtab == 'scenario-analysis':
            print("   → 进入 scenario-analysis 分支")
            result = render_scenario_analysis(df)
            print(f"   ← scenario-analysis 返回: {type(result)}")
            return result
        elif active_subtab == 'ai-suggestions':
            return render_ai_marketing_suggestions(df)
        
        # 新增4个扩展子Tab (需要Tab 5扩展渲染模块)
        elif active_subtab == 'heatmap-profit':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_heatmap_profit_matrix(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("热力图和利润矩阵功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        elif active_subtab == 'trend-price':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_trend_price_analysis(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("趋势和客单价分析功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        elif active_subtab == 'product-network':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_product_scene_network(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("商品场景关联网络功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        elif active_subtab == 'product-profile':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_product_scene_profile(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("商品场景画像功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        return html.Div()
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        print("=" * 80)
        print(f"❌ Tab 5子Tab渲染失败: {type(e).__name__}: {e}")
        print("=" * 80)
        print(error_trace)
        print("=" * 80)
        
        return dbc.Alert([
            html.H4("⚠️ Tab 5 渲染失败", className="alert-heading"),
            html.P([
                html.Strong("错误类型: "), f"{type(e).__name__}"
            ]),
            html.P([
                html.Strong("错误信息: "), str(e)
            ]),
            html.P([
                html.Strong("当前子Tab: "), active_subtab
            ]),
            html.Hr(),
            html.Details([
                html.Summary("📋 点击查看完整错误堆栈", style={'cursor': 'pointer', 'color': '#721c24'}),
                html.Pre(error_trace, style={
                    'fontSize': '11px',
                    'maxHeight': '400px',
                    'overflow': 'auto',
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'marginTop': '10px'
                })
            ])
        ], color="danger")


def render_period_analysis(df: pd.DataFrame):
    """1. 时段订单分析"""
    print(f"  🕒 render_period_analysis 开始: df.shape={df.shape}")
    
    try:
        period_metrics = calculate_period_metrics(df)
        print(f"     period_metrics 计算成功: {len(period_metrics)} 行")
    except Exception as e:
        print(f"     ❌ period_metrics 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"时段指标计算失败: {str(e)}", color="danger")
    
    # 时段顺序
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    
    # 按时段订单量排序
    order_by_period = df.groupby('时段')['订单ID'].nunique().reindex(period_order, fill_value=0)
    
    # 按时段客单价
    period_avg_price = period_metrics.set_index('时段')['平均客单价'].reindex(period_order, fill_value=0)
    
    # 找出峰谷
    peak_period = order_by_period.idxmax()
    peak_orders = order_by_period.max()
    low_period = order_by_period.idxmin()
    low_orders = order_by_period.min()
    
    high_value_period = period_avg_price.idxmax()
    high_value = period_avg_price.max()
    
    layout = html.Div([
        # 关键指标卡片
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🔥 高峰时段", className="text-primary mb-2"),
                        html.H4(peak_period, className="mb-1"),
                        html.P(f"{peak_orders:,} 订单", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-primary")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📉 低谷时段", className="text-warning mb-2"),
                        html.H4(low_period, className="mb-1"),
                        html.P(f"{low_orders:,} 订单", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-warning")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("💰 高价值时段", className="text-success mb-2"),
                        html.H4(high_value_period, className="mb-1"),
                        html.P(f"¥{high_value:.2f} 客单价", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-success")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 峰谷差异", className="text-info mb-2"),
                        html.H4(f"{(peak_orders/low_orders - 1)*100:.0f}%", className="mb-1"),
                        html.P(f"相差 {peak_orders - low_orders:,} 单", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-info")
            ], md=3)
        ], className="mb-4"),
        
        # 图表行
        dbc.Row([
            # 左侧: 订单量分布
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 分时段订单量分布"),
                    dbc.CardBody([
                        render_period_orders_chart(order_by_period) if ECHARTS_AVAILABLE
                        else render_period_orders_chart_plotly(order_by_period)
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            # 右侧: 客单价趋势
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💰 分时段平均客单价趋势"),
                    dbc.CardBody([
                        render_period_price_chart(period_avg_price) if ECHARTS_AVAILABLE
                        else render_period_price_chart_plotly(period_avg_price)
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-4"),
        
        # 详细数据表
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 分时段营销指标详情"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=period_metrics.to_dict('records'),
                            columns=[
                                {'name': '时段', 'id': '时段'},
                                {'name': '订单量', 'id': '订单量', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '商品数', 'id': '商品数', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '销售额', 'id': '销售额', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                                {'name': '平均客单价', 'id': '平均客单价', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                                {'name': '利润率', 'id': '利润率', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                            ],
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{订单量} = ' + str(int(period_metrics['订单量'].max()))},
                                    'backgroundColor': '#d4edda',
                                    'fontWeight': 'bold'
                                }
                            ],
                            style_cell={'textAlign': 'center'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
                        )
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),
        
        # 营销建议
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5([html.I(className="bi bi-lightbulb me-2"), "🎯 营销建议"], className="mb-3"),
                    html.Ul([
                        html.Li([html.Strong("低峰时段促销: "), f"在 {low_period} 加大折扣力度，推出'限时特惠'吸引订单"]),
                        html.Li([html.Strong("高峰时段提价: "), f"在 {peak_period} 减少促销，提升利润率，可推出高价值套餐"]),
                        html.Li([html.Strong("高价值时段: "), f"在 {high_value_period} 推荐高利润商品，提升客单价"]),
                        html.Li([html.Strong("定时推送: "), "提前30分钟推送下一时段优惠券，引导提前下单"])
                    ])
                ], color="info", className="shadow-sm")
            ])
        ])
    ])
    
    return layout


def render_scenario_analysis(df: pd.DataFrame):
    """2. 消费场景分析"""
    print(f"  🎯 render_scenario_analysis 开始: df.shape={df.shape}")
    
    try:
        scenario_metrics = calculate_scenario_metrics(df)
        print(f"     scenario_metrics 计算成功: {len(scenario_metrics)} 行")
    except Exception as e:
        print(f"     ❌ scenario_metrics 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"场景指标计算失败: {str(e)}", color="danger")
    
    # 场景订单分布
    scenario_orders = df.groupby('场景')['订单ID'].nunique().sort_values(ascending=False)
    
    # 找出主要场景
    top_scenario = scenario_orders.idxmax()
    top_scenario_orders = scenario_orders.max()
    top_scenario_ratio = (top_scenario_orders / scenario_orders.sum() * 100)
    
    layout = html.Div([
        # 场景定义说明
        dbc.Alert([
            html.H5([html.I(className="bi bi-info-circle me-2"), "📖 消费场景定义说明"], className="mb-3"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Strong("🍳 早餐: "),
                        html.Span("豆浆、油条、包子、粥、煎饼、鸡蛋、面包、牛奶、燕麦等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🍱 午餐: "),
                        html.Span("便当、盒饭、套餐、炒饭、炒面、拉面、米饭等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("🍽️ 晚餐: "),
                        html.Span("晚饭、炒菜、烧烤等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🌙 夜宵: "),
                        html.Span("宵夜、烧烤、串串、小龙虾、啤酒等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("☕ 下午茶: "),
                        html.Span("咖啡、奶茶、蛋糕、甜品、冰淇淋、饮料等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🍿 休闲零食: "),
                        html.Span("薯片、饼干、糖果、巧克力、坚果、果冻、瓜子等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("🧻 日用补充: "),
                        html.Span("纸巾、洗衣液、洗洁精、牙膏、香皂、洗发水等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🆘 应急购买: "),
                        html.Span("电池、充电器、雨伞、口罩、创可贴等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("💊 营养补充: "),
                        html.Span("维生素、蛋白粉、钙片、保健品等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🛒 日常购物: "),
                        html.Span("未匹配上述关键词的通用商品", className="text-muted")
                    ], md=6)
                ])
            ]),
            html.Hr(),
            html.Small([
                html.I(className="bi bi-lightbulb me-1"),
                "场景识别优先级: 商品名称关键词 > 商品分类映射 > 默认分类"
            ], className="text-muted")
        ], color="info", className="mb-4"),
        
        # 关键指标
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🎯 主要场景", className="text-primary mb-2"),
                        html.H4(top_scenario, className="mb-1"),
                        html.P(f"{top_scenario_ratio:.1f}% 订单占比", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-primary")
            ], md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 场景数量", className="text-info mb-2"),
                        html.H4(f"{len(scenario_orders)}", className="mb-1"),
                        html.P("个消费场景", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-info")
            ], md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("💰 场景客单价", className="text-success mb-2"),
                        html.H4(f"¥{scenario_metrics['平均客单价'].mean():.2f}", className="mb-1"),
                        html.P("平均值", className="text-muted mb-0")
                    ])
                ], className="shadow-sm border-success")
            ], md=4)
        ], className="mb-4"),
        
        # 图表
        dbc.Row([
            # 场景订单分布
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🎯 消费场景订单分布"),
                    dbc.CardBody([
                        render_scenario_orders_chart(scenario_orders) if ECHARTS_AVAILABLE
                        else render_scenario_orders_chart_plotly(scenario_orders)
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            # 场景销售额对比
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💰 各场景销售额对比"),
                    dbc.CardBody([
                        render_scenario_sales_chart(scenario_metrics) if ECHARTS_AVAILABLE
                        else render_scenario_sales_chart_plotly(scenario_metrics)
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-4"),
        
        # 详细数据表
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 消费场景详细指标"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=scenario_metrics.to_dict('records'),
                            columns=[
                                {'name': '场景', 'id': '场景'},
                                {'name': '订单量', 'id': '订单量', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '商品数', 'id': '商品数', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '销售额', 'id': '销售额', 'type': 'numeric', 'format': {'specifier': ',.1f'}},
                                {'name': '平均客单价', 'id': '平均客单价', 'type': 'numeric', 'format': {'specifier': ',.1f'}},
                                {'name': '利润率', 'id': '利润率', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                            ],
                            style_cell={'textAlign': 'center'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                            style_data_conditional=[
                                {
                                    'if': {'column_id': '利润率', 'filter_query': '{利润率} >= 30'},
                                    'backgroundColor': '#d4edda',
                                    'color': '#155724'
                                },
                                {
                                    'if': {'column_id': '利润率', 'filter_query': '{利润率} < 20'},
                                    'backgroundColor': '#f8d7da',
                                    'color': '#721c24'
                                }
                            ]
                        )
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])
    
    return layout


def render_cross_analysis(df: pd.DataFrame):
    """3. 时段×场景交叉分析"""
    # 创建交叉透视表
    cross_orders = pd.pivot_table(
        df,
        values='订单ID',
        index='时段',
        columns='场景',
        aggfunc='nunique',
        fill_value=0
    )
    
    # 时段顺序
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    cross_orders = cross_orders.reindex(period_order, fill_value=0)
    
    # 找出最热组合
    max_combo = cross_orders.stack().idxmax()
    max_combo_orders = cross_orders.stack().max()
    
    layout = html.Div([
        # 关键洞察
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5([html.I(className="bi bi-star me-2"), "🔥 黄金组合"], className="mb-3"),
                    html.H4(f"{max_combo[0]} × {max_combo[1]}", className="text-primary"),
                    html.P(f"{int(max_combo_orders):,} 订单", className="text-muted mb-0")
                ], color="warning", className="shadow-sm")
            ], md=12)
        ], className="mb-4"),
        
        # 热力图
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔥 时段×场景交叉热力图"),
                    dbc.CardBody([
                        render_cross_heatmap(cross_orders) if ECHARTS_AVAILABLE
                        else render_cross_heatmap_plotly(cross_orders)
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])
    
    return layout


def render_ai_marketing_suggestions(df: pd.DataFrame):
    """4. AI智能营销建议"""
    layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([html.I(className="bi bi-robot me-2"), "AI智能营销建议"], className="text-primary mb-4")
            ])
        ]),
        
        # AI分析按钮
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("基于时段场景分析数据，AI将为您生成精准营销策略建议", className="mb-3"),
                        dbc.Button([
                            html.I(className="bi bi-stars me-2"),
                            "🚀 开始AI智能分析"
                        ], id='ai-scenario-analyze-btn', color="primary", size="lg", className="w-100")
                    ])
                ], className="shadow-sm")
            ], md=12)
        ], className="mb-4"),
        
        # AI分析结果
        dbc.Row([
            dbc.Col([
                html.Div(id='ai-scenario-analysis-result')
            ])
        ])
    ])
    
    return layout


@app.callback(
    Output('ai-scenario-analysis-result', 'children'),
    Input('ai-scenario-analyze-btn', 'n_clicks'),
    prevent_initial_call=True
)
def run_ai_scenario_analysis(n_clicks):
    """运行AI场景营销分析"""
    if n_clicks is None:
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        if df is None or len(df) == 0:
            return dbc.Alert("暂无数据", color="warning")
        
        df = extract_time_features_for_scenario(df)
        period_metrics = calculate_period_metrics(df)
        scenario_metrics = calculate_scenario_metrics(df)
        
        # 构建分析上下文
        analysis_context = {
            'period_metrics': period_metrics.to_dict('records'),
            'scenario_metrics': scenario_metrics.to_dict('records'),
            'total_orders': df['订单ID'].nunique(),
            'total_sales': df['实收价格'].sum() if '实收价格' in df.columns else df['商品实售价'].sum()
        }
        
        # 构建prompt
        prompt = f"""
你是一位资深零售运营顾问,专注于O2O场景营销分析。请基于以下真实数据提供精准营销建议:

📊 **时段分析数据**:
{chr(10).join([f"- {m['时段']}: {int(m['订单量'])}单, 客单价¥{m['平均客单价']:.2f}, 利润率{m['利润率']:.1f}%" for m in analysis_context['period_metrics']])}

🎯 **场景分析数据**:
{chr(10).join([f"- {m['场景']}: {int(m['订单量'])}单, 销售额¥{m['销售额']:,.0f}, 利润率{m['利润率']:.1f}%" for m in analysis_context['scenario_metrics']])}

📈 **总体概况**:
- 总订单数: {analysis_context['total_orders']:,}单
- 总销售额: ¥{analysis_context['total_sales']:,.2f}

请提供以下分析:

## 🔍 核心洞察
[3-5个关键发现，基于时段和场景数据]

## 🎯 精准营销策略
### 1. 时段营销
- 低峰时段促销: [具体时段和策略]
- 高峰时段优化: [具体建议]

### 2. 场景营销
- 主力场景深耕: [针对top场景的策略]
- 潜力场景培育: [挖掘低频场景]

### 3. 商品推荐
- 时段商品匹配: [不同时段推荐不同商品]
- 场景套餐设计: [组合营销建议]

## 📅 执行计划
1. 本周: [具体行动]
2. 本月: [目标KPI]

## ⚠️ 风险提示
[可能的风险和应对措施]
"""
        
        # 调用AI
        from ai_analyzer import get_ai_analyzer
        scenario_analyzer = get_ai_analyzer(model_type='glm')
        
        if scenario_analyzer is None or not scenario_analyzer.is_ready():
            return dbc.Alert("AI分析器未就绪，请检查API配置", color="warning")
        
        print(f"\n{'='*60}")
        print(f"🤖 Tab 5 AI场景营销分析开始...")
        
        analysis_result = scenario_analyzer._generate_content(prompt)
        
        print(f"   ✅ AI分析完成")
        print(f"{'='*60}\n")
        
        if not analysis_result:
            return dbc.Alert("AI分析返回空结果，请稍后重试", color="warning")
        
        # 格式化结果
        return dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-stars me-2"),
                html.H5("AI场景营销智能分析报告", className="d-inline mb-0")
            ]),
            dbc.CardBody([
                dcc.Markdown(
                    analysis_result,
                    className="ai-analysis-content",
                    style={
                        'fontFamily': 'Microsoft YaHei',
                        'fontSize': '14px',
                        'lineHeight': '1.6'
                    }
                ),
                html.Hr(),
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    html.Small([
                        "此分析基于时段场景数据。",
                        "AI分析仅供参考，请结合实际情况执行。"
                    ])
                ], color="info", className="mb-0")
            ])
        ], className="shadow-sm", style={'border': '2px solid #667eea'})
        
    except Exception as e:
        print(f"❌ AI场景分析失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"分析失败: {str(e)}", color="danger")


# ==================== Tab 6: 成本利润分析辅助函数 ====================

def calculate_cost_profit_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """计算成本利润指标"""
    metrics = {}
    
    # 基础指标
    metrics['total_orders'] = df['订单ID'].nunique() if '订单ID' in df.columns else len(df)
    metrics['total_sales'] = df['商品实售价'].sum() if '商品实售价' in df.columns else 0
    
    # 成本计算
    cost_fields = []
    if '商品成本' in df.columns:
        cost_fields.append('商品成本')
    if '配送费成本' in df.columns:
        cost_fields.append('配送费成本')
    if '营销费用' in df.columns:
        cost_fields.append('营销费用')
    
    if cost_fields:
        metrics['total_cost'] = df[cost_fields].sum().sum()
    else:
        # 如果没有成本字段,估算为销售额的60%
        metrics['total_cost'] = metrics['total_sales'] * 0.6
    
    # 利润计算
    if '利润额' in df.columns:
        metrics['total_profit'] = df['利润额'].sum()
    else:
        metrics['total_profit'] = metrics['total_sales'] - metrics['total_cost']
    
    # 比率计算
    if metrics['total_sales'] > 0:
        metrics['cost_rate'] = (metrics['total_cost'] / metrics['total_sales']) * 100
        metrics['profit_rate'] = (metrics['total_profit'] / metrics['total_sales']) * 100
    else:
        metrics['cost_rate'] = 0
        metrics['profit_rate'] = 0
    
    # 平均值
    if metrics['total_orders'] > 0:
        metrics['avg_order_value'] = metrics['total_sales'] / metrics['total_orders']
        metrics['avg_profit_per_order'] = metrics['total_profit'] / metrics['total_orders']
    else:
        metrics['avg_order_value'] = 0
        metrics['avg_profit_per_order'] = 0
    
    # 成本结构
    cost_breakdown = {}
    if '商品成本' in df.columns:
        cost_breakdown['商品成本'] = df['商品成本'].sum()
    if '配送费成本' in df.columns:
        cost_breakdown['配送费成本'] = df['配送费成本'].sum()
    if '营销费用' in df.columns:
        cost_breakdown['营销费用'] = df['营销费用'].sum()
    
    # 如果没有详细成本,创建估算
    if not cost_breakdown:
        cost_breakdown = {
            '商品成本': metrics['total_cost'] * 0.7,
            '配送费成本': metrics['total_cost'] * 0.2,
            '营销费用': metrics['total_cost'] * 0.1
        }
    
    metrics['cost_breakdown'] = cost_breakdown
    
    return metrics


def render_cost_structure_chart(metrics: Dict[str, Any]):
    """渲染成本结构饼图 - ECharts版本"""
    cost_breakdown = metrics['cost_breakdown']
    
    option = {
        'title': {
            'text': '成本结构',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 14, 'fontWeight': 'normal'}
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: ¥{c}<br/>占比: {d}%'
        },
        'legend': {
            'orient': 'vertical',
            'left': 'left',
            'top': 'middle'
        },
        'series': [{
            'name': '成本结构',
            'type': 'pie',
            'radius': ['40%', '70%'],
            'center': ['60%', '55%'],
            'avoidLabelOverlap': True,
            'itemStyle': {
                'borderRadius': 10,
                'borderColor': '#fff',
                'borderWidth': 2
            },
            'label': {
                'show': True,
                'formatter': '{b}\n¥{c}\n{d}%'
            },
            'emphasis': {
                'label': {'show': True, 'fontSize': 16, 'fontWeight': 'bold'}
            },
            'data': [
                {'value': v, 'name': k, 'itemStyle': {'color': color}}
                for (k, v), color in zip(cost_breakdown.items(), 
                                        ['#FF6B6B', '#4ECDC4', '#FFE66D'])
            ]
        }]
    }
    
    return DashECharts(
        option=option,
        id='cost-structure-chart',
        style={'height': '400px'}
    )


def render_cost_structure_chart_plotly(metrics: Dict[str, Any]):
    """渲染成本结构饼图 - Plotly版本(后备)"""
    cost_breakdown = metrics['cost_breakdown']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(cost_breakdown.keys()),
        values=list(cost_breakdown.values()),
        hole=0.4,
        marker_colors=['#FF6B6B', '#4ECDC4', '#FFE66D'],
        textinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>金额: ¥%{value:,.2f}<br>占比: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        height=400,
        showlegend=True,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_profit_source_chart(metrics: Dict[str, Any]):
    """渲染利润来源柱状图 - ECharts版本"""
    total_sales = metrics['total_sales']
    total_cost = metrics['total_cost']
    total_profit = metrics['total_profit']
    
    option = {
        'title': {
            'text': '销售额与成本利润对比',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 14, 'fontWeight': 'normal'}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'legend': {
            'data': ['销售额', '成本', '利润'],
            'top': 40
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '3%',
            'top': 80,
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': ['总体']
        },
        'yAxis': {
            'type': 'value',
            'name': '金额(元)',
            'axisLabel': {'formatter': '¥{value}'}
        },
        'series': [
            {
                'name': '销售额',
                'type': 'bar',
                'data': [total_sales],
                'itemStyle': {'color': '#5470C6'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': f'¥{total_sales:,.0f}'
                }
            },
            {
                'name': '成本',
                'type': 'bar',
                'data': [total_cost],
                'itemStyle': {'color': '#EE6666'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': f'¥{total_cost:,.0f}'
                }
            },
            {
                'name': '利润',
                'type': 'bar',
                'data': [total_profit],
                'itemStyle': {'color': '#91CC75'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': f'¥{total_profit:,.0f}'
                }
            }
        ]
    }
    
    return DashECharts(
        option=option,
        id='profit-source-chart',
        style={'height': '400px'}
    )


def render_profit_source_chart_plotly(metrics: Dict[str, Any]):
    """渲染利润来源柱状图 - Plotly版本(后备)"""
    total_sales = metrics['total_sales']
    total_cost = metrics['total_cost']
    total_profit = metrics['total_profit']
    
    fig = go.Figure(data=[
        go.Bar(name='销售额', x=['总体'], y=[total_sales], marker_color='#5470C6',
               text=[f'¥{total_sales:,.0f}'], textposition='auto'),
        go.Bar(name='成本', x=['总体'], y=[total_cost], marker_color='#EE6666',
               text=[f'¥{total_cost:,.0f}'], textposition='auto'),
        go.Bar(name='利润', x=['总体'], y=[total_profit], marker_color='#91CC75',
               text=[f'¥{total_profit:,.0f}'], textposition='auto')
    ])
    
    fig.update_layout(
        height=400,
        barmode='group',
        yaxis_title='金额(元)',
        showlegend=True,
        margin=dict(t=30, b=30, l=50, r=30)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_product_profit_chart(df: pd.DataFrame):
    """渲染商品利润率分析 - ECharts版本"""
    # 按商品汇总
    product_metrics = df.groupby('商品名称').agg({
        '商品实售价': 'sum',
        '利润额': 'sum' if '利润额' in df.columns else lambda x: 0
    }).reset_index()
    
    # 如果没有利润额,估算
    if '利润额' not in df.columns:
        product_metrics['利润额'] = product_metrics['商品实售价'] * 0.3
    
    # 计算利润率
    product_metrics['利润率'] = (product_metrics['利润额'] / product_metrics['商品实售价'] * 100).round(1)
    
    # 取Top 20
    product_metrics = product_metrics.nlargest(20, '商品实售价')
    product_metrics = product_metrics.sort_values('利润率')
    
    # 颜色映射
    colors = ['#91CC75' if r >= 30 else '#FAC858' if r >= 20 else '#EE6666' 
              for r in product_metrics['利润率']]
    
    option = {
        'title': {
            'text': 'Top 20 商品利润率',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 14, 'fontWeight': 'normal'}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {
            'left': '3%',
            'right': '10%',
            'bottom': '3%',
            'top': 50,
            'containLabel': True
        },
        'xAxis': {
            'type': 'value',
            'name': '销售额(元)'
        },
        'yAxis': {
            'type': 'category',
            'data': product_metrics['商品名称'].tolist(),
            'axisLabel': {
                'interval': 0,
                'fontSize': 11
            }
        },
        'series': [
            {
                'name': '销售额',
                'type': 'bar',
                'data': [
                    {'value': row['商品实售价'], 'itemStyle': {'color': color}}
                    for (_, row), color in zip(product_metrics.iterrows(), colors)
                ],
                'label': {
                    'show': True,
                    'position': 'right',
                    'formatter': '{c}%'
                }
            }
        ]
    }
    
    return DashECharts(
        option=option,
        id='product-profit-chart',
        style={'height': '600px'}
    )


def render_product_profit_chart_plotly(df: pd.DataFrame):
    """渲染商品利润率分析 - Plotly版本(后备)"""
    # 按商品汇总
    product_metrics = df.groupby('商品名称').agg({
        '商品实售价': 'sum',
        '利润额': 'sum' if '利润额' in df.columns else lambda x: 0
    }).reset_index()
    
    # 如果没有利润额,估算
    if '利润额' not in df.columns:
        product_metrics['利润额'] = product_metrics['商品实售价'] * 0.3
    
    # 计算利润率
    product_metrics['利润率'] = (product_metrics['利润额'] / product_metrics['商品实售价'] * 100).round(1)
    
    # 取Top 20
    product_metrics = product_metrics.nlargest(20, '商品实售价')
    product_metrics = product_metrics.sort_values('利润率')
    
    # 颜色映射
    colors = ['#91CC75' if r >= 30 else '#FAC858' if r >= 20 else '#EE6666' 
              for r in product_metrics['利润率']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=product_metrics['商品实售价'],
            y=product_metrics['商品名称'],
            orientation='h',
            marker_color=colors,
            text=[f"{r:.1f}%" for r in product_metrics['利润率']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>销售额: ¥%{x:,.2f}<br>利润率: %{text}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        height=600,
        xaxis_title='销售额(元)',
        showlegend=False,
        margin=dict(t=30, b=30, l=150, r=80)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_cost_optimization_suggestions(metrics: Dict[str, Any]):
    """渲染成本优化建议"""
    suggestions = []
    
    # 基于利润率给建议
    profit_rate = metrics['profit_rate']
    
    if profit_rate < 20:
        suggestions.append({
            'icon': 'exclamation-triangle',
            'color': 'danger',
            'title': '⚠️ 利润率偏低',
            'content': f"当前利润率仅 {profit_rate:.1f}%，低于行业平均水平(25-35%)。建议优化成本结构或提升定价策略。"
        })
    elif profit_rate < 30:
        suggestions.append({
            'icon': 'info-circle',
            'color': 'warning',
            'title': '💡 利润率一般',
            'content': f"当前利润率 {profit_rate:.1f}%，处于中等水平。可通过优化商品组合和控制履约成本进一步提升。"
        })
    else:
        suggestions.append({
            'icon': 'check-circle',
            'color': 'success',
            'title': '✅ 利润率健康',
            'content': f"当前利润率 {profit_rate:.1f}%，处于良好水平。继续保持成本控制和定价策略。"
        })
    
    # 成本结构建议
    cost_breakdown = metrics['cost_breakdown']
    total_cost = metrics['total_cost']
    
    for cost_type, cost_value in cost_breakdown.items():
        cost_pct = (cost_value / total_cost * 100) if total_cost > 0 else 0
        
        if cost_type == '商品成本' and cost_pct > 70:
            suggestions.append({
                'icon': 'box',
                'color': 'info',
                'title': '📦 商品成本优化',
                'content': f"商品成本占比 {cost_pct:.1f}%，建议优化供应链、批量采购降低单位成本，或调整商品结构增加高毛利品。"
            })
        
        if cost_type == '配送费成本' and cost_pct > 25:
            suggestions.append({
                'icon': 'truck',
                'color': 'info',
                'title': '🚚 履约成本优化',
                'content': f"配送费成本占比 {cost_pct:.1f}%，建议提升订单客单价、优化配送路线或调整配送策略。"
            })
        
        if cost_type == '营销费用' and cost_pct > 15:
            suggestions.append({
                'icon': 'megaphone',
                'color': 'info',
                'title': '📢 营销成本优化',
                'content': f"营销费用占比 {cost_pct:.1f}%，建议优化营销ROI、精准投放或提升自然流量。"
            })
    
    # 渲染建议卡片
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-lightbulb me-2"),
            "💡 成本优化建议"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H6([
                            html.I(className=f"bi bi-{sug['icon']} me-2"),
                            sug['title']
                        ], className="mb-2"),
                        html.P(sug['content'], className="mb-0")
                    ], color=sug['color'], className="mb-3")
                ], md=6)
                for sug in suggestions
            ])
        ])
    ], className="shadow-sm")


# ==================== Tab 6回调 ====================

@app.callback(
    Output('tab-6-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab6_content(active_tab):
    """Tab 6: 成本利润分析 - 使用ECharts可视化"""
    if active_tab != 'tab-6':
        raise PreventUpdate
    
    global GLOBAL_DATA
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "暂无数据，请先上传数据或加载历史数据"
        ], color="warning", className="text-center")
    
    try:
        df = GLOBAL_DATA.copy()
        
        # 计算成本利润指标
        cost_profit_metrics = calculate_cost_profit_metrics(df)
        
        # 创建布局
        layout = html.Div([
            # 标题
            html.H3([
                html.I(className="bi bi-currency-dollar me-2"),
                "💵 成本利润分析"
            ], className="mb-4"),
            
            # 关键指标卡片
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💰 总销售额", className="text-primary mb-2"),
                            html.H4(f"¥{cost_profit_metrics['total_sales']:,.2f}", className="mb-1"),
                            html.P(f"订单数: {cost_profit_metrics['total_orders']:,}", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="shadow-sm border-primary h-100")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("📦 总成本", className="text-danger mb-2"),
                            html.H4(f"¥{cost_profit_metrics['total_cost']:,.2f}", className="mb-1"),
                            html.P(f"成本率: {cost_profit_metrics['cost_rate']:.1f}%", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="shadow-sm border-danger h-100")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💎 总利润", className="text-success mb-2"),
                            html.H4(f"¥{cost_profit_metrics['total_profit']:,.2f}", className="mb-1"),
                            html.P(f"利润率: {cost_profit_metrics['profit_rate']:.1f}%", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="shadow-sm border-success h-100")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("📊 平均客单价", className="text-info mb-2"),
                            html.H4(f"¥{cost_profit_metrics['avg_order_value']:.2f}", className="mb-1"),
                            html.P(f"单利润: ¥{cost_profit_metrics['avg_profit_per_order']:.2f}", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="shadow-sm border-info h-100")
                ], md=3)
            ], className="mb-4"),
            
            # 成本结构分析 (使用ECharts)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-pie-chart me-2"),
                            "📊 成本结构分析"
                        ]),
                        dbc.CardBody([
                            render_cost_structure_chart(cost_profit_metrics) if ECHARTS_AVAILABLE
                            else render_cost_structure_chart_plotly(cost_profit_metrics)
                        ])
                    ], className="shadow-sm")
                ], md=6),
                
                # 利润来源分析 (使用ECharts)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-bar-chart me-2"),
                            "💎 利润来源分析"
                        ]),
                        dbc.CardBody([
                            render_profit_source_chart(cost_profit_metrics) if ECHARTS_AVAILABLE
                            else render_profit_source_chart_plotly(cost_profit_metrics)
                        ])
                    ], className="shadow-sm")
                ], md=6)
            ], className="mb-4"),
            
            # 商品级成本利润分析 (使用ECharts)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-graph-up me-2"),
                            "🏷️ 商品利润率分析 (Top 20)"
                        ]),
                        dbc.CardBody([
                            render_product_profit_chart(df) if ECHARTS_AVAILABLE
                            else render_product_profit_chart_plotly(df)
                        ])
                    ], className="shadow-sm")
                ])
            ], className="mb-4"),
            
            # 成本优化建议
            dbc.Row([
                dbc.Col([
                    render_cost_optimization_suggestions(cost_profit_metrics)
                ])
            ])
        ])
        
        return layout
        
    except Exception as e:
        print(f"❌ Tab 6渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染失败: {str(e)}", color="danger")


@app.callback(
    Output('tab-7-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab7_content(active_tab):
    if active_tab != 'tab-7':
        raise PreventUpdate
    return dbc.Alert("⚙️ 高级功能开发中...", color="info", className="text-center")


# ==================== 全局数据信息更新回调 ====================
@app.callback(
    [Output('global-data-info-card', 'children'),
     Output('data-metadata', 'data')],
    [Input('data-update-trigger', 'data'),
     Input('main-tabs', 'value')],
    prevent_initial_call=False
)
def update_global_data_info(trigger, active_tab):
    """更新全局数据信息卡片"""
    global GLOBAL_DATA
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "⚠️ 未加载数据，请上传数据或检查默认数据文件"
        ], color="warning", className="mb-3"), {}
    
    try:
        from datetime import datetime
        
        # 计算数据统计信息
        total_records = len(GLOBAL_DATA)
        
        # 获取时间范围
        if '日期' in GLOBAL_DATA.columns:
            date_col = pd.to_datetime(GLOBAL_DATA['日期'], errors='coerce')
            min_date = date_col.min()
            max_date = date_col.max()
            
            # 检查是否为有效日期
            if pd.isna(min_date) or pd.isna(max_date):
                date_range_text = "日期数据异常"
            else:
                date_range_text = f"{min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}"
        else:
            date_range_text = "无日期字段"
        
        # 获取数据文件名（从全局变量或默认值）
        data_filename = "实际数据/订单明细.xlsx"  # 默认值
        
        # 订单数量
        order_count = 0
        if '订单ID' in GLOBAL_DATA.columns:
            order_count = GLOBAL_DATA['订单ID'].nunique()
        
        # 商品数量
        product_count = 0
        if '商品名称' in GLOBAL_DATA.columns:
            product_count = GLOBAL_DATA['商品名称'].nunique()
        
        # 获取当前时间
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建元数据
        metadata = {
            'total_records': total_records,
            'date_range': date_range_text,
            'order_count': order_count,
            'product_count': product_count,
            'update_time': update_time,
            'filename': data_filename
        }
        
        # 创建信息卡片
        info_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # 数据状态指示器
                    dbc.Col([
                        html.Div([
                            html.I(className="bi bi-database-check me-2", 
                                   style={'fontSize': '1.2rem', 'color': '#28a745'}),
                            html.Span("数据已加载", className="fw-bold", 
                                     style={'color': '#28a745'})
                        ], className="d-flex align-items-center")
                    ], width=2),
                    
                    # 数据文件名
                    dbc.Col([
                        html.Small("📁 数据文件:", className="text-muted me-2"),
                        html.Span(data_filename, className="fw-bold", 
                                 style={'fontSize': '0.9rem'})
                    ], width=3),
                    
                    # 数据时间范围
                    dbc.Col([
                        html.Small("📅 时间范围:", className="text-muted me-2"),
                        html.Span(date_range_text, className="fw-bold",
                                 style={'fontSize': '0.9rem'})
                    ], width=3),
                    
                    # 数据量统计
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.Small("📊 订单数:", className="text-muted me-1"),
                                html.Span(f"{order_count:,}", className="fw-bold text-primary",
                                         style={'fontSize': '0.9rem'})
                            ]),
                            html.Div([
                                html.Small("🏷️ 商品数:", className="text-muted me-1"),
                                html.Span(f"{product_count:,}", className="fw-bold text-success",
                                         style={'fontSize': '0.9rem'})
                            ])
                        ])
                    ], width=2),
                    
                    # 最后更新时间
                    dbc.Col([
                        html.Small("🕐 更新时间:", className="text-muted me-2"),
                        html.Span(update_time, className="text-muted small")
                    ], width=2)
                ], align="center")
            ])
        ], className="mb-3", style={
            'borderLeft': '4px solid #28a745',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
            'background': '#f8fff9'
        })
        
        return info_card, metadata
        
    except Exception as e:
        print(f"❌ 更新数据信息失败: {e}")
        import traceback
        traceback.print_exc()
        
        return dbc.Alert([
            html.I(className="bi bi-exclamation-circle me-2"),
            f"❌ 数据信息更新失败: {str(e)}"
        ], color="danger", className="mb-3"), {}


# 为各个Tab更新数据信息
@app.callback(
    Output('tab4-data-info', 'children'),
    [Input('data-metadata', 'data'),
     Input('main-tabs', 'value')],
    prevent_initial_call=False
)
def update_tab_data_info(metadata, active_tab):
    """为Tab-4更新数据信息提示"""
    if not metadata:
        return html.Div()
    
    # 创建简化的数据信息条
    info_bar = dbc.Alert([
        html.I(className="bi bi-info-circle me-2"),
        html.Span("当前分析数据: ", className="fw-bold"),
        html.Span(f"{metadata.get('date_range', '未知')} | ", className="me-2"),
        html.Span(f"订单数: {metadata.get('order_count', 0):,} | ", className="me-2"),
        html.Span(f"商品数: {metadata.get('product_count', 0):,}", className="me-2"),
        html.Span(f" (更新于 {metadata.get('update_time', '--')})", className="text-muted small")
    ], color="info", className="mb-3", style={'padding': '0.75rem'})
    
    return info_bar



# ==================== AI分析回调 ====================
# 初始化AI分析器（全局单例）
AI_ANALYZER = None

def init_ai_analyzer():
    """初始化AI分析器 - 支持多种AI模型"""
    global AI_ANALYZER
    if AI_ANALYZER is None:
        # 从环境变量获取模型类型和API密钥
        model_type = os.getenv('AI_MODEL_TYPE', 'glm')  # 默认使用智谱GLM
        
        # 根据模型类型获取对应的API密钥
        if model_type == 'glm':
            api_key = os.getenv('ZHIPU_API_KEY')
            key_name = 'ZHIPU_API_KEY'
        elif model_type == 'qwen':
            api_key = os.getenv('DASHSCOPE_API_KEY')
            key_name = 'DASHSCOPE_API_KEY'
        else:  # gemini
            api_key = os.getenv('GEMINI_API_KEY')
            key_name = 'GEMINI_API_KEY'
        
        AI_ANALYZER = get_ai_analyzer(api_key, model_type)
        if AI_ANALYZER:
            model_names = {'glm': '智谱GLM-4.6', 'qwen': '通义千问', 'gemini': 'Gemini'}
            print(f"✅ AI分析器初始化成功 (使用{model_names.get(model_type, model_type)})")
        else:
            print(f"⚠️ AI分析器初始化失败,请设置{key_name}环境变量")
    return AI_ANALYZER


# ==================== Tab 2 AI分析回调 - 增强版多板块工作流 ====================
@app.callback(
    [Output('ai-tab2-analysis-result', 'children'),
     Output('ai-analysis-progress', 'children')],
    Input('ai-tab2-analyze-btn', 'n_clicks'),
    [State('ai-analysis-mode', 'value'),
     State('tab2-all-data', 'data')],
    prevent_initial_call=True
)
def run_tab2_ai_analysis_workflow(n_clicks, analysis_mode, all_data):
    """Tab 2 - AI智能分析工作流 (支持快速/标准/全面三种模式)"""
    if not n_clicks or n_clicks == 0:
        return html.Div(), html.Div()
    
    if not all_data or 'product_agg' not in all_data:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "请先查看商品分析数据后再进行AI分析"
        ], color="warning"), html.Div()
    
    # 初始化AI分析器
    analyzer = init_ai_analyzer()
    if not analyzer:
        model_type = os.getenv('AI_MODEL_TYPE', 'glm')
        key_names = {'glm': 'ZHIPU_API_KEY', 'qwen': 'DASHSCOPE_API_KEY', 'gemini': 'GEMINI_API_KEY'}
        key_name = key_names.get(model_type, 'ZHIPU_API_KEY')
        
        return dbc.Alert([
            html.I(className="bi bi-x-circle me-2"),
            html.Div([
                html.Strong("AI分析器未就绪"),
                html.Br(),
                html.Small(f"请在.env文件中设置 {key_name}")
            ])
        ], color="danger"), html.Div()
    
    try:
        # 转换数据
        df = pd.DataFrame(all_data['product_agg'])
        
        if len(df) == 0:
            return dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "商品数据为空,无法进行AI分析"
            ], color="info"), html.Div()
        
        print(f"\n{'='*60}")
        print(f"🤖 Tab 2 AI智能分析工作流启动...")
        print(f"   分析模式: {analysis_mode}")
        print(f"   商品总数: {len(df)}")
        
        # 根据模式执行不同的分析流程
        if analysis_mode == 'quick':
            # 快速模式: 仅四象限分析
            result = run_quick_analysis(df, all_data, analyzer)
            progress = create_progress_indicator(['四象限分析'], [True])
            
        elif analysis_mode == 'standard':
            # 标准模式: 四象限 + 趋势 + 排行
            result = run_standard_analysis(df, all_data, analyzer)
            progress = create_progress_indicator(['四象限分析', '趋势分析', '商品排行'], [True, True, True])
            
        else:  # comprehensive
            # 全面模式: 所有板块 + 综合报告
            result = run_comprehensive_analysis(df, all_data, analyzer)
            progress = create_progress_indicator(
                ['四象限', '趋势', '排行', '分类', '结构', '库存', '综合报告'],
                [True] * 7
            )
        
        return result, progress
        
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        import traceback
        traceback.print_exc()
        
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("AI分析出错"),
                html.Br(),
                html.Small(f"错误信息: {str(e)}")
            ])
        ], color="danger"), html.Div()


def create_progress_indicator(steps: List[str], completed: List[bool]) -> html.Div:
    """创建分析进度指示器"""
    items = []
    for i, (step, done) in enumerate(zip(steps, completed)):
        icon = "✅" if done else "⏳"
        color = "success" if done else "secondary"
        items.append(
            dbc.Badge(f"{icon} {step}", color=color, className="me-2 mb-2")
        )
    
    return html.Div([
        html.Small("分析进度:", className="text-muted me-2"),
        html.Div(items, className="d-inline-flex flex-wrap")
    ])


def run_quick_analysis(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """快速分析模式 - 仅四象限"""
    print("   📊 执行快速分析 (四象限)...")
    
    # 准备四象限数据
    quadrant_stats = all_data.get('quadrant_stats', {})
    high_profit = df[df['象限分类'].isin(['🌟 高利润高动销', '⚠️ 高利润低动销'])].nlargest(3, '实际利润')
    low_profit = df[df['象限分类'] == '❌ 低利润低动销'].nlargest(3, '销售额')
    
    analysis_context = {
        'total_products': len(df),
        'total_sales': df['销售额'].sum(),
        'total_profit': df['实际利润'].sum(),
        'avg_profit_rate': df['利润率'].mean(),
        'quadrant_stats': quadrant_stats,
        'top_profit_products': high_profit[['商品名称', '销售额', '实际利润', '利润率', '总销量', '平均售价', '象限分类']].to_dict('records') if len(high_profit) > 0 else [],
        'problem_products': low_profit[['商品名称', '销售额', '实际利润', '利润率', '总销量', '平均售价', '象限分类']].to_dict('records') if len(low_profit) > 0 else []
    }
    
    # 构建AI提示词
    prompt = f"""
你是一位资深零售运营顾问。**请严格基于以下真实数据和看板计算逻辑进行分析**:

📋 **看板核心计算逻辑** (AI分析必须遵循):

1. **利润率计算**:
   - 利润率 = (实收价格 - 成本) / 实收价格 × 100%
   - 使用实收价格(排除补贴/折扣后的真实收入)

2. **四象限划分标准**:
   - 利润率阈值: 30% (高于30%为高利润)
   - 动销指数阈值: {df['动销指数'].median():.3f} (高于中位数为高动销)
   - 🌟 高利润高动销: 利润率>30% 且 动销指数>阈值
   - ⚠️ 高利润低动销: 利润率>30% 但 动销指数≤阈值
   - 🚀 低利润高动销: 利润率≤30% 但 动销指数>阈值
   - ❌ 低利润低动销: 利润率≤30% 且 动销指数≤阈值

3. **动销指数计算**:
   - 动销指数 = 0.5×标准化销量 + 0.3×标准化周转率 + 0.2×标准化订单数
   - 综合评价商品的销售活跃度

4. **盈利健康度判定**:
   - 🟢 稳定盈利: ≥70%订单盈利
   - 🟡 波动盈利: 40%-70%订单盈利
   - 🔴 依赖大单: <40%订单盈利但有盈利
   - ⚫ 全部亏损: 0%订单盈利

5. **数据字段说明**:
   - 销售额 = 单价 × 销量 (累计值)
   - 利润 = 销售额 - 成本 (累计值)
   - 平均售价 = 销售额 / 销量 (单价)

---

📊 **总体数据**(统计周期内汇总):
- 商品总数: {analysis_context['total_products']}个
- 总销售额: ¥{analysis_context['total_sales']:,.2f} (所有商品累计销售额)
- 总利润: ¥{analysis_context['total_profit']:,.2f} (所有商品累计利润)
- 平均利润率: {analysis_context['avg_profit_rate']:.1f}%

🎯 **四象限分布**:
{chr(10).join([f"- {k}: {v}个 ({v/analysis_context['total_products']*100:.1f}%)" for k, v in analysis_context['quadrant_stats'].items()])}

🌟 **高利润商品TOP3** (必须在分析中引用):
**注意:销售额是累计值,平均售价是单价**
"""
    # 修复 f-string 反斜杠问题：提取到变量
    newline = '\n'
    top_products_text = chr(10).join([
        f"{i+1}. **{p['商品名称']}**{newline}"
        f"   - 累计销售额: ¥{p['销售额']:,.2f}{newline}"
        f"   - 累计利润: ¥{p['实际利润']:,.2f}{newline}"
        f"   - 利润率: {p['利润率']:.1f}%{newline}"
        f"   - 销量: {p['总销量']}件{newline}"
        f"   - 单价: ¥{p['平均售价']:.2f}/件"
        for i, p in enumerate(analysis_context['top_profit_products'])
    ])
    
    problem_products_text = chr(10).join([
        f"{i+1}. **{p['商品名称']}**{newline}"
        f"   - 累计销售额: ¥{p['销售额']:,.2f}{newline}"
        f"   - 累计利润: ¥{p['实际利润']:,.2f}{newline}"
        f"   - 利润率: {p['利润率']:.1f}%{newline}"
        f"   - 销量: {p['总销量']}件{newline}"
        f"   - 单价: ¥{p['平均售价']:.2f}/件"
        for i, p in enumerate(analysis_context['problem_products'])
    ])
    
    user_prompt = f"""
你是专业的新零售数据分析师,正在分析门店O2O业务数据。

📋 **字段含义**:
   - 销售额 = 单价 × 销量 (累计值)
   - 利润 = 销售额 - 成本 (累计值)
   - 平均售价 = 销售额 / 销量 (单价)

---

📊 **总体数据**(统计周期内汇总):
- 商品总数: {analysis_context['total_products']}个
- 总销售额: ¥{analysis_context['total_sales']:,.2f} (所有商品累计销售额)
- 总利润: ¥{analysis_context['total_profit']:,.2f} (所有商品累计利润)
- 平均利润率: {analysis_context['avg_profit_rate']:.1f}%

🎯 **四象限分布**:
{chr(10).join([f"- {k}: {v}个 ({v/analysis_context['total_products']*100:.1f}%)" for k, v in analysis_context['quadrant_stats'].items()])}

🌟 **高利润商品TOP3** (必须在分析中引用):
**注意:销售额是累计值,平均售价是单价**
{top_products_text}

⚠️ **问题商品TOP3** (必须在分析中引用):
**注意:销售额是累计值,平均售价是单价**
{problem_products_text}

---

**分析要求**:
1. 必须使用上述真实商品名称和数据,不要编造
2. 调价建议基于"平均售价",调幅5%-15%为宜
3. 基于四象限逻辑给建议(如:高利润低动销→加强推广)
4. 所有预期效果需基于真实数据计算

请提供结构化分析报告:

## 📊 核心洞察
[基于四象限分布和盈利健康度的3-5个关键发现]

## 💡 优化策略
### 1. 商品组合优化
- 重点推广: [从高利润TOP3选择,说明当前单价¥X和销量]
- 优化调整: [从问题商品选择,基于象限分类给建议]
- 预期效果: [基于当前数据估算收益]

### 2. 定价策略  
- 调价商品: [商品名,当前¥X→建议¥Y,调幅Z%]
- 调价依据: [基于利润率和市场定位]
- 预期收益: [销量变化×利润变化]

### 3. 库存优化
- 补货优先级: [基于销量和象限分类]
- 清仓方案: [针对低利润低动销商品]

## 📈 执行计划
1. 本周: [具体商品的具体操作]
2. 本月: [目标和KPI]
3. 季度: [长期策略]

## ⚠️ 风险提示
[基于数据的潜在风险]
"""
    
    # 调用AI (阶段1优化: Few-Shot + CoT + 数据验证)
    model_names = {'glm': '智谱GLM-4', 'qwen': '通义千问', 'gemini': 'Gemini'}
    model_name = model_names.get(analyzer.model_type, 'AI')
    print(f"\n   调用{model_name} API...")
    
    if BUSINESS_CONTEXT_AVAILABLE:
        print(f"   ✅ 启用GLM-4.6阶段1优化")
        print(f"   ✓ Few-Shot示例库自动匹配")
        print(f"   ✓ CoT思维链6步引导")
        print(f"   ✓ 数据验证规则注入")
        
        # 构建数据摘要
        data_summary = {
            '商品总数': analysis_context['total_products'],
            '总销售额': f"¥{analysis_context['total_sales']:,.2f}",
            '总利润': f"¥{analysis_context['total_profit']:,.2f}",
            '平均利润率': f"{analysis_context['avg_profit_rate']:.1f}%",
            '四象限分布': analysis_context['quadrant_stats'],
            '高利润商品': [p['商品名称'] for p in analysis_context['top_profit_products']],
            '问题商品': [p['商品名称'] for p in analysis_context['problem_products']]
        }
        
        # 生成增强Prompt
        enhanced_prompt = get_analysis_prompt(
            task_name="商品四象限分析",
            data_summary=data_summary,
            specific_question=prompt,
            use_cot=True,
            use_examples=True
        )
        
        print(f"   📋 增强Prompt前500字: {enhanced_prompt[:500]}...")
        analysis_result = analyzer._generate_content(enhanced_prompt)
    else:
        print(f"   ⚠️ 使用基础分析 (未启用阶段1优化)")
        print(f"   📋 Prompt前500字: {prompt[:500]}...")
        analysis_result = analyzer._generate_content(prompt)
    
    print(f"   ✅ AI分析完成")
    print(f"   📝 结果长度: {len(analysis_result) if analysis_result else 0} 字符")
    if analysis_result:
        print(f"   📝 前200字: {analysis_result[:200]}...")
    
    # 检查结果是否为空
    if not analysis_result or len(analysis_result.strip()) == 0:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("AI分析返回空结果"),
                html.Br(),
                html.Small("请稍后重试或联系技术支持")
            ])
        ], color="warning")
    
    # 格式化结果
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-stars me-2"),
            html.H5("🎯 四象限智能分析报告", className="d-inline mb-0"),
            html.Small(f" - 基于{analysis_context['total_products']}个商品", className="text-muted ms-2")
        ]),
        dbc.CardBody([
            dcc.Markdown(
                analysis_result,
                className="ai-analysis-content",
                style={
                    'fontFamily': 'Microsoft YaHei',
                    'fontSize': '14px',
                    'lineHeight': '1.6'
                }
            ),
            html.Hr(),
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Small([
                    "此分析基于商品四象限数据。",
                    "AI分析仅供参考,请结合实际情况执行。",
                    f"使用模型: {model_name}"
                ])
            ], color="info", className="mb-0")
        ])
    ], className="shadow-sm", style={'border': '2px solid #667eea'})


# ==================== Tab 2 AI分析辅助函数 (多板块工作流) ====================

def run_standard_analysis(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """标准分析模式 - 四象限 + 趋势 + 排行"""
    print("   📊 执行标准分析 (四象限 + 趋势 + 排行)...")
    
    results = []
    
    # 1. 四象限分析
    quadrant_result = analyze_quadrant_module(df, all_data, analyzer)
    results.append(quadrant_result)
    
    # 2. 趋势分析 (简化版)
    trend_result = analyze_trend_module(df, analyzer)
    results.append(trend_result)
    
    # 3. 商品排行分析
    ranking_result = analyze_ranking_module(df, analyzer)
    results.append(ranking_result)
    
    # 返回组合结果
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-stars me-2"),
                html.H5("AI标准分析报告", className="d-inline mb-0"),
                html.Small(f" - 基于{len(df)}个商品的多维度分析", className="text-muted ms-2")
            ]),
            dbc.CardBody(results)
        ])
    ])


def run_comprehensive_analysis(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """全面分析模式 - 所有7大板块 + 综合报告"""
    print("   📊 执行全面分析 (7大板块 + 综合报告)...")
    
    results = []
    
    try:
        # 7. 综合报告 (优先生成,最重要)
        print("   ✅ 生成综合报告...")
        summary = generate_summary_report(df, all_data, analyzer)
        if summary:
            results.append(summary)
            print("   ✅ 综合报告完成")
        
        # 1-6. 各板块分析(如果前面成功才继续)
        modules = [
            ("🎯 四象限分析", analyze_quadrant_module),
            ("📈 趋势分析", analyze_trend_module),
            ("📊 商品排行", analyze_ranking_module),
            ("📂 分类分析", analyze_category_module),
            ("🔄 结构分析", analyze_structure_module),
            ("⚠️ 库存预警", analyze_inventory_module)
        ]
        
        for title, func in modules:
            try:
                print(f"   ✅ 生成{title}...")
                if title == "🎯 四象限分析":
                    content = func(df, all_data, analyzer)
                else:
                    content = func(df, analyzer)
                
                if content:
                    results.append(
                        dbc.Accordion([
                            dbc.AccordionItem([content], title=title)
                        ], start_collapsed=True, className="mb-3")
                    )
                    print(f"   ✅ {title}完成")
            except Exception as e:
                print(f"   ⚠️ {title}失败: {e}")
                results.append(
                    dbc.Alert(f"{title} 生成失败: {str(e)}", color="warning", className="mb-3")
                )
        
        if not results:
            return dbc.Alert("AI分析未返回结果,请稍后重试", color="warning")
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="bi bi-stars me-2"),
                    html.H5("AI全面分析报告", className="d-inline mb-0"),
                    html.Small(f" - 基于{len(df)}个商品的深度洞察", className="text-muted ms-2")
                ]),
                dbc.CardBody(results)
            ])
        ])
        
    except Exception as e:
        print(f"   ❌ 全面分析失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"AI分析失败: {str(e)}", color="danger")


def analyze_quadrant_module(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """四象限板块分析"""
    quadrant_stats = all_data.get('quadrant_stats', {})
    high_profit = df[df['象限分类'].isin(['🌟 高利润高动销', '⚠️ 高利润低动销'])].nlargest(3, '实际利润')
    low_profit = df[df['象限分类'] == '❌ 低利润低动销'].nlargest(3, '销售额')
    
    prompt = f"""
基于商品四象限分析,提供深度洞察(限500字):

**数据**: 商品{len(df)}个, 平均利润率{df['利润率'].mean():.1f}%
**分布**: {quadrant_stats}
**TOP3高利润**: {[p['商品名称'] for p in high_profit.to_dict('records')]}
**TOP3问题**: {[p['商品名称'] for p in low_profit.to_dict('records')]}

分析: 1)四象限分布健康度 2)高利润低动销激活策略 3)具体商品优化建议
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'商品数': len(df), '四象限': quadrant_stats}
        enhanced_prompt = get_analysis_prompt("商品四象限分析", data_summary, prompt, use_cot=True, use_examples=True)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_trend_module(df: pd.DataFrame, analyzer) -> html.Div:
    """趋势分析板块"""
    prompt = f"""
基于商品数据,分析趋势(限300字):

**商品总数**: {len(df)}
**平均利润率**: {df['利润率'].mean():.1f}%
**高动销占比**: {(df['动销指数'] > df['动销指数'].median()).sum() / len(df) * 100:.1f}%

分析: 1)主要趋势 2)预警商品 3)拐点识别
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'商品数': len(df), '平均利润率': f"{df['利润率'].mean():.1f}%"}
        enhanced_prompt = get_analysis_prompt("商品趋势分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_ranking_module(df: pd.DataFrame, analyzer) -> html.Div:
    """商品排行板块分析"""
    top5 = df.nlargest(5, '销售额')[['商品名称', '销售额', '利润率']].to_dict('records')
    bottom5 = df.nsmallest(5, '销售额')[['商品名称', '销售额', '利润率']].to_dict('records')
    
    prompt = f"""
基于商品排行,识别明星/淘汰商品(限300字):

**TOP5**: {[p['商品名称'] for p in top5]}
**BOTTOM5**: {[p['商品名称'] for p in bottom5]}

分析: 1)明星商品成功因素 2)淘汰商品改进方向
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'TOP5': [p['商品名称'] for p in top5], 'BOTTOM5': [p['商品名称'] for p in bottom5]}
        enhanced_prompt = get_analysis_prompt("商品排行分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_category_module(df: pd.DataFrame, analyzer) -> html.Div:
    """分类分析板块"""
    if '一级分类名' in df.columns:
        category_sales = df.groupby('一级分类名')['销售额'].sum().nlargest(5).to_dict()
        prompt = f"""
基于分类数据,优化品类结构(限300字):

**TOP5分类销售额**: {category_sales}

分析: 1)品类结构合理性 2)加强/削弱建议 3)跨品类组合
"""
        if BUSINESS_CONTEXT_AVAILABLE:
            data_summary = {'TOP5分类': category_sales}
            enhanced_prompt = get_analysis_prompt("商品分类分析", data_summary, prompt, use_cot=True, use_examples=False)
            result = analyzer._generate_content(enhanced_prompt)
        else:
            result = analyzer._generate_content(prompt)
    else:
        prompt = "分类数据不足,无法分析。"
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_structure_module(df: pd.DataFrame, analyzer) -> html.Div:
    """结构分析板块"""
    prompt = f"""
基于商品结构,分析生命周期(限300字):

**四象限分布**: {df['象限分类'].value_counts().to_dict()}

分析: 1)商品生命周期阶段 2)迁移干预建议
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'四象限分布': df['象限分类'].value_counts().to_dict()}
        enhanced_prompt = get_analysis_prompt("商品结构分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_inventory_module(df: pd.DataFrame, analyzer) -> html.Div:
    """库存预警板块"""
    zero_stock = df[df['库存'] == 0]
    low_stock = df[(df['库存'] > 0) & (df['库存'] < df['总销量'] * 0.1)]
    
    prompt = f"""
基于库存数据,制定补货/清仓策略(限300字):

**0库存商品**: {len(zero_stock)}个
**低库存商品**: {len(low_stock)}个

分析: 1)补货优先级 2)清仓方案 3)周转优化
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'0库存': len(zero_stock), '低库存': len(low_stock)}
        enhanced_prompt = get_analysis_prompt("库存预警分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def generate_summary_report(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """生成综合报告"""
    prompt = f"""
基于7大板块分析,生成综合执行计划(限800字):

**总览**: {len(df)}个商品, 总销售额¥{df['销售额'].sum():,.2f}, 总利润¥{df['实际利润'].sum():,.2f}
**四象限**: {all_data.get('quadrant_stats', {})}

请整合给出:
## 📊 核心发现 (3-5条)
## 💡 优先级策略 (本周/本月/本季度)
## 📈 预期效果 (数据化目标)
## ⚠️ 风险提示
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {
            '商品数': len(df),
            '销售额': f"¥{df['销售额'].sum():,.2f}",
            '利润': f"¥{df['实际利润'].sum():,.2f}",
            '四象限': all_data.get('quadrant_stats', {})
        }
        enhanced_prompt = get_analysis_prompt("综合商品分析报告", data_summary, prompt, use_cot=True, use_examples=True)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-file-text me-2"),
            html.H5("📋 综合执行报告", className="d-inline mb-0")
        ], style={'background-color': '#f8f9fa'}),
        dbc.CardBody([
            dcc.Markdown(result, className="ai-analysis-content"),
            html.Hr(),
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Small([
                    "此报告整合了四象限、趋势、排行、分类、结构、库存等7大板块分析。",
                    html.Br(),
                    "建议结合实际情况执行,定期复盘效果。使用模型: 智谱GLM-4.6"
                ])
            ], color="info")
        ])
    ], className="mb-3", style={'border': '2px solid #0d6efd'})


# ==================== 运行应用 ====================
# ==================== Tab 5 场景营销 - ECharts图表渲染函数 ====================

def render_period_orders_chart(order_by_period):
    """时段订单量柱状图 - ECharts版本"""
    option = {
        'title': {'text': '分时段订单量', 'left': 'center', 'top': 10},
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 50, 'containLabel': True},
        'xAxis': {'type': 'category', 'data': order_by_period.index.tolist(), 'axisLabel': {'rotate': 45, 'interval': 0}},
        'yAxis': {'type': 'value', 'name': '订单量'},
        'series': [{
            'name': '订单量',
            'type': 'bar',
            'data': order_by_period.values.tolist(),
            'itemStyle': {'color': '#5470C6'},
            'label': {'show': True, 'position': 'top'}
        }]
    }
    return DashECharts(option=option, id='period-orders-chart', style={'height': '400px'})


def render_period_orders_chart_plotly(order_by_period):
    """时段订单量柱状图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Bar(
        x=order_by_period.index,
        y=order_by_period.values,
        marker_color='lightblue',
        text=order_by_period.values,
        textposition='auto'
    )])
    fig.update_layout(xaxis_title='时段', yaxis_title='订单量', height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_period_price_chart(period_avg_price):
    """时段客单价折线图 - ECharts版本"""
    option = {
        'title': {'text': '分时段客单价趋势', 'left': 'center', 'top': 10},
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 50, 'containLabel': True},
        'xAxis': {'type': 'category', 'data': period_avg_price.index.tolist(), 'axisLabel': {'rotate': 45, 'interval': 0}},
        'yAxis': {'type': 'value', 'name': '客单价(元)', 'axisLabel': {'formatter': '¥{value}'}},
        'series': [{
            'name': '平均客单价',
            'type': 'line',
            'data': [round(v, 1) for v in period_avg_price.values.tolist()],
            'smooth': True,
            'itemStyle': {'color': '#EE6666'},
            'lineStyle': {'width': 3},
            'areaStyle': {'opacity': 0.3},
            'label': {'show': True, 'formatter': '¥{c}'}
        }]
    }
    return DashECharts(option=option, id='period-price-chart', style={'height': '400px'})


def render_period_price_chart_plotly(period_avg_price):
    """时段客单价折线图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Scatter(
        x=period_avg_price.index,
        y=period_avg_price.values,
        mode='lines+markers',
        line=dict(color='orange', width=3),
        marker=dict(size=10)
    )])
    fig.update_layout(xaxis_title='时段', yaxis_title='平均客单价(元)', height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_scenario_orders_chart(scenario_orders):
    """场景订单分布饼图 - ECharts版本"""
    option = {
        'title': {'text': '消费场景订单分布', 'left': 'center', 'top': 10},
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
        'legend': {'orient': 'vertical', 'left': 'left', 'top': 'middle'},
        'series': [{
            'name': '订单量',
            'type': 'pie',
            'radius': ['40%', '70%'],
            'center': ['60%', '55%'],
            'data': [{'value': v, 'name': k} for k, v in scenario_orders.items()],
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowOffsetX': 0, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}},
            'label': {'formatter': '{b}\n{c}\n({d}%)'}
        }]
    }
    return DashECharts(option=option, id='scenario-orders-chart', style={'height': '400px'})


def render_scenario_orders_chart_plotly(scenario_orders):
    """场景订单分布饼图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Pie(
        labels=scenario_orders.index,
        values=scenario_orders.values,
        hole=0.4,
        textinfo='label+percent'
    )])
    fig.update_layout(height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_scenario_sales_chart(scenario_metrics):
    """场景销售额柱状图 - ECharts版本"""
    option = {
        'title': {'text': '各场景销售额对比', 'left': 'center', 'top': 10},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'formatter': "{b}<br/>销售额: ¥{c}"
        },
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 50, 'containLabel': True},
        'xAxis': {'type': 'category', 'data': scenario_metrics['场景'].tolist()},
        'yAxis': {'type': 'value', 'name': '销售额(元)', 'axisLabel': {'formatter': '¥{value}'}},
        'series': [{
            'name': '销售额',
            'type': 'bar',
            'data': [round(v, 1) for v in scenario_metrics['销售额'].tolist()],
            'itemStyle': {'color': '#91CC75'},
            'label': {
                'show': True,
                'position': 'top',
                'formatter': '¥{c}'
            }
        }]
    }
    return DashECharts(option=option, id='scenario-sales-chart', style={'height': '400px'})


def render_scenario_sales_chart_plotly(scenario_metrics):
    """场景销售额柱状图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Bar(
        x=scenario_metrics['场景'],
        y=scenario_metrics['销售额'],
        marker_color='lightgreen',
        text=[f'¥{v:,.0f}' for v in scenario_metrics['销售额']],
        textposition='auto'
    )])
    fig.update_layout(xaxis_title='消费场景', yaxis_title='销售额(元)', height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_cross_heatmap(cross_orders):
    """时段×场景交叉热力图 - ECharts版本"""
    # 准备热力图数据 [[x, y, value], ...]
    heatmap_data = []
    for i, period in enumerate(cross_orders.index):
        for j, scenario in enumerate(cross_orders.columns):
            heatmap_data.append([j, i, float(cross_orders.iloc[i, j])])
    
    option = {
        'title': {'text': '时段×场景交叉热力图', 'left': 'center', 'top': 10},
        'tooltip': {'position': 'top'},
        'grid': {'height': '70%', 'top': '15%'},
        'xAxis': {
            'type': 'category',
            'data': cross_orders.columns.tolist(),
            'splitArea': {'show': True}
        },
        'yAxis': {
            'type': 'category',
            'data': cross_orders.index.tolist(),
            'splitArea': {'show': True}
        },
        'visualMap': {
            'min': 0,
            'max': float(cross_orders.values.max()),
            'calculable': True,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': '5%',
            'inRange': {'color': ['#FFFFCC', '#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026']}
        },
        'series': [{
            'name': '订单量',
            'type': 'heatmap',
            'data': heatmap_data,
            'label': {'show': True},
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}}
        }]
    }
    return DashECharts(option=option, id='cross-heatmap-chart', style={'height': '500px'})


def render_cross_heatmap_plotly(cross_orders):
    """时段×场景交叉热力图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Heatmap(
        z=cross_orders.values,
        x=cross_orders.columns.tolist(),
        y=cross_orders.index.tolist(),
        colorscale='YlOrRd',
        text=cross_orders.values,
        texttemplate='%{z}'
    )])
    fig.update_layout(xaxis_title='消费场景', yaxis_title='时段', height=500)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    import sys
    
    # 强制刷新输出，确保日志实时显示
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🏪 智能门店经营看板 - Dash版                  ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  ✅ 解决Streamlit页面跳转问题                                 ║
    ║  ✅ 流畅的交互体验                                            ║
    ║  ✅ 只更新需要更新的部分                                       ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  📍 访问地址: http://localhost:8050                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """, flush=True)
    
    # 🆕 测试AI功能
    print("🤖 检查AI分析功能...", flush=True)
    try:
        from ai_analyzer import get_ai_analyzer
        test_analyzer = get_ai_analyzer(model_type='glm')
        if test_analyzer and test_analyzer.is_ready():
            print(f"   ✅ AI分析器就绪 (智谱GLM-4.6)", flush=True)
        else:
            print(f"   ⚠️ AI分析器未就绪,AI功能将不可用", flush=True)
    except Exception as e:
        print(f"   ⚠️ AI初始化异常: {e}", flush=True)
    
    print("🚀 准备启动应用服务器...", flush=True)
    print(f"📊 数据状态: {len(GLOBAL_DATA) if GLOBAL_DATA is not None else 0} 行数据已加载", flush=True)
    print(f"⚙️ 配置: host=0.0.0.0, port=8050, debug=False", flush=True)
    print("", flush=True)
    
    try:
        # 使用debug=True临时查看详细错误
        app.run(
            debug=True,  # 暂时启用Debug查看错误
            host='0.0.0.0',
            port=8050,
            use_reloader=False  # 禁用自动重载
        )
        print("⚠️ 应用服务器已停止", flush=True)
    except KeyboardInterrupt:
        print("\n✋ 用户中断 (Ctrl+C)", flush=True)
    except Exception as e:
        print(f"\n❌ 应用启动失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

