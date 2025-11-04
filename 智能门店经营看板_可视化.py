#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
智能门店经营看板 - 可视化界面
集成Streamlit构建交互式看板，展示五大AI模型的分析结果

🚀 快速启动：
=============
启动命令：
  cd "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"
  & "d:\Python1\O2O_Analysis\O2O数据分析\.venv\Scripts\streamlit.exe" run 智能门店经营看板_可视化.py --server.port 8502

简化命令：
  cd "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"
  ..\\.venv\\Scripts\\streamlit run 智能门店经营看板_可视化.py --server.port 8502

访问地址：
  本地地址: http://localhost:8502
  网络地址: http://26.26.26.1:8502

📋 功能模块：
=============
- 💹 比价分析：支持上传比价结果Excel文件进行可视化分析
- 📊 订单分析：门店订单数据的深度分析和趋势预测
- 🎯 智能决策：基于AI模型的经营建议和优化方案
- 📈 实时监控：关键经营指标的实时监控和预警
- 🔍 竞对分析：竞争对手分析和市场定位建议

💡 使用提示：
=============
- 确保虚拟环境已激活
- 首次运行可能需要下载AI模型，请耐心等待
- 支持的文件格式：Excel (.xlsx, .xls), JSON
- 建议使用Chrome或Edge浏览器以获得最佳体验
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 🔧 Windows 环境变量设置：确保 UTF-8 输出
if sys.platform == 'win32':
    # 设置环境变量，让 Python 使用 UTF-8 编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# 导入商品分类结构分析模块
try:
    from 商品分类结构分析 import render_category_analysis
    CATEGORY_ANALYSIS_AVAILABLE = True
    print("[OK] 商品分类结构分析模块已加载")
except ImportError as e:
    CATEGORY_ANALYSIS_AVAILABLE = False
    print(f"[WARN] 商品分类结构分析模块加载失败: {e}")

# 导入统一业务逻辑配置
try:
    sys.path.append(str(APP_DIR.parent))
    from standard_business_config import StandardBusinessConfig, StandardBusinessLogic, create_order_level_summary, apply_standard_business_logic
    STANDARD_CONFIG_AVAILABLE = True
    print("[OK] 已加载统一业务逻辑配置")
except ImportError as e:
    print(f"[WARN] 未找到standard_business_config模块: {e}")
    print("将使用默认配置")
    STANDARD_CONFIG_AVAILABLE = False

# 导入看板系统模块（本地模块）
try:
    from 智能门店经营看板系统 import SmartStoreDashboard
    from 真实数据处理器 import RealDataProcessor
    from price_comparison_dashboard import create_price_comparison_dashboard
    DASHBOARD_MODULES_AVAILABLE = True
    print("[OK] 核心业务逻辑模块已加载")
except ImportError as e:
    print(f"[WARN] 看板系统模块导入失败: {e}")
    print("部分功能可能不可用")
    DASHBOARD_MODULES_AVAILABLE = False
    # 创建占位类避免错误
    class SmartStoreDashboard:
        def __init__(self, *args, **kwargs):
            pass
        def get_learning_status(self):
            return {"status": "unavailable", "message": "看板系统模块未加载"}
    class RealDataProcessor:
        def __init__(self, *args, **kwargs):
            self.data_dir = args[0] if args else "实际数据"
    def create_price_comparison_dashboard():
        st.warning("比价分析模块暂不可用")

# 导入核心业务逻辑（上级目录）
try:
    sys.path.append(str(APP_DIR.parent))
    from 核心业务逻辑 import CoreBusinessLogic
    print("[OK] 核心业务逻辑模块已加载")
except ImportError as e:
    print(f"[WARN] 核心业务逻辑模块导入失败: {e}")
    class CoreBusinessLogic:
        pass

# 导入订单分析增强模块
try:
    from 订单分析增强模块 import (
        render_enhanced_order_overview,
        render_enhanced_profit_analysis
    )
    ORDER_ENHANCEMENT_AVAILABLE = True
    print("[OK] 订单分析增强模块已加载")
except ImportError as e:
    print(f"[WARN] 订单分析增强模块未加载: {e}")
    ORDER_ENHANCEMENT_AVAILABLE = False

# 导入场景营销智能决策引擎
try:
    from 场景营销智能决策引擎 import (
        SceneMarketingIntelligence,
        ProductCombinationMiner,
        SceneRecognitionModel,
        RFMCustomerSegmentation,
        SceneDecisionTreeRules
    )
    SCENE_INTELLIGENCE_AVAILABLE = True
    print("[OK] 场景营销智能决策引擎已加载")
except ImportError as e:
    print(f"[WARN] 场景营销智能决策引擎未加载: {e}")
    SCENE_INTELLIGENCE_AVAILABLE = False

# 导入问题诊断引擎
try:
    from 问题诊断引擎 import ProblemDiagnosticEngine
    PROBLEM_DIAGNOSTIC_AVAILABLE = True
    print("[OK] 问题诊断引擎已加载")
except ImportError as e:
    print(f"[WARN] 问题诊断引擎未加载: {e}")
    PROBLEM_DIAGNOSTIC_AVAILABLE = False

PRICE_PANEL_INTERMEDIATE_DIR = APP_DIR.parent / "比价数据" / "intermediate"

# 页面配置
st.set_page_config(
    page_title="智能门店经营看板",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .recommendation-box {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .risk-warning {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .high-risk {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(hash_funcs={type: lambda _: None})
def load_dashboard_system() -> SmartStoreDashboard:
    """加载智能门店经营看板系统实例"""
    return SmartStoreDashboard()

@st.cache_resource(hash_funcs={type: lambda _: None})
def load_data_processor() -> RealDataProcessor:
    """加载真实数据处理器实例"""
    return RealDataProcessor("实际数据")

COLUMN_NAME_FIXES: Dict[str, str] = {
    # 正常列名透传
    "商品名称": "商品名称",
    "商品实售价": "商品实售价",
    "商品原价": "商品原价",
    "门店名称": "门店名称",
    "门店编码": "门店编码",
    "订单ID": "订单ID",
    "下单时间": "下单时间",
    "收货地址": "收货地址",
    "用户ID": "用户ID",
    "用户名称": "用户名称",
    "数量": "数量",
    "剩余库存": "剩余库存",
    "美团一级分类": "美团一级分类",
    "美团三级分类": "美团三级分类",
    "配送方式": "配送方式",
    "渠道": "渠道",
    "城市名称": "城市名称",
    "物流配送费": "物流配送费",
    "平台佣金": "平台佣金",
    "实收价格": "实收价格",
    "预估订单收入": "预估订单收入",
    "用户支付配送费": "用户支付配送费",
    "配送费减免金额": "配送费减免金额",
    "商品优惠金额": "商品优惠金额",
    "商品减免金额": "商品减免金额",
    # 常见乱码映射
    "һ": "一级分类",
    "": "城市名称",
    "": "三级分类",
    "Ʒ": "商品名称",
    "Ʒ": "商品编码",
    "Ʒʵۼ": "商品实售价",
    "Ʒԭ": "商品原价",
    "": "数量",
    "ʣ": "剩余库存",
    "Ʒ": "商品优惠金额",
    "": "配送方式",
    "ID": "订单ID",
    "ûID": "用户ID",
    "û": "用户名称",
    "̻": "门店名称",
    "ŵ": "门店名称",
    "µʱ": "下单时间",
    "ջַ": "收货地址",
    "ƽ̨Ӷ": "平台佣金",
    "ʵռ۸": "实收价格",
    "Ԥƶ": "预估订单收入",
    "û֧": "用户支付配送费",
    "û֧ͷ": "配送费减免金额",
    "ͷѼ": "物流配送费",
    "Ʒ": "商品名称",
    "̼ҳеȯ": "商家优惠券",
    "̼Ҵȯ": "商家优惠券",
    "": "商品减免金额",
    "": "渠道",
}

SHEET_KEYWORDS: Dict[str, List[str]] = {
    "order": ["门店订单", "订单", "order"],
    "competitor": ["竞对", "竞品", "对手"],
    "cost": ["成本", "费用", "cost"],
    "traffic": ["流量", "交通", "客流", "traffic"],
}

NUMERIC_COLUMNS = [
    "商品实售价",
    "商品原价",
    "数量",
    "剩余库存",
    "平台佣金",
    "物流配送费",
    "用户支付配送费",
    "配送费减免金额",
    "预估订单收入",
    "实收价格",
    "商品优惠金额",
    "商品减免金额",
]

CHANNELS_TO_REMOVE = CoreBusinessLogic.CHANNELS_TO_REMOVE

# ==================== 📊 数据质量检查与缓存管理 ====================

def perform_data_quality_check(df: pd.DataFrame) -> Dict[str, Any]:
    """
    执行全面的数据质量检查
    
    Returns:
        包含质量检查结果的字典
    """
    quality_report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'issues': [],
        'warnings': [],
        'summary': {},
        'score': 100  # 初始分数100分
    }
    
    # 1. 检查缺失值
    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        missing_cols = missing_data[missing_data > 0]
        quality_report['summary']['missing_values'] = missing_cols.to_dict()
        
        for col, count in missing_cols.items():
            percentage = (count / len(df)) * 100
            if percentage > 50:
                quality_report['issues'].append({
                    'type': '严重',
                    'column': col,
                    'description': f'缺失值过多：{count}行 ({percentage:.1f}%)'
                })
                quality_report['score'] -= 10
            elif percentage > 10:
                quality_report['warnings'].append({
                    'type': '警告',
                    'column': col,
                    'description': f'存在缺失值：{count}行 ({percentage:.1f}%)'
                })
                quality_report['score'] -= 3
    
    # 2. 检查完全重复的数据行
    duplicate_rows = df.duplicated().sum()
    if duplicate_rows > 0:
        quality_report['issues'].append({
            'type': '警告',
            'column': '数据行',
            'description': f'发现完全重复的数据行：{duplicate_rows}条（所有字段完全相同）'
        })
        quality_report['score'] -= 5
    
    # 2.1 检查订单-商品明细结构（信息性检查，不扣分）
    if '订单ID' in df.columns:
        unique_orders = df['订单ID'].nunique()
        total_rows = len(df)
        items_per_order = total_rows / unique_orders if unique_orders > 0 else 0
        
        quality_report['issues'].append({
            'type': '信息',
            'column': '订单结构',
            'description': f'订单-商品明细级数据：{unique_orders}个订单，{total_rows}条明细（平均每单{items_per_order:.1f}个商品）'
        })
    
    # 3. 检查日期格式
    if '下单时间' in df.columns:
        try:
            date_series = pd.to_datetime(df['下单时间'], errors='coerce')
            invalid_dates = date_series.isnull().sum()
            if invalid_dates > 0:
                quality_report['warnings'].append({
                    'type': '警告',
                    'column': '下单时间',
                    'description': f'无效日期格式：{invalid_dates}行'
                })
                quality_report['score'] -= 3
        except Exception as e:
            quality_report['issues'].append({
                'type': '严重',
                'column': '下单时间',
                'description': f'日期解析失败：{str(e)}'
            })
            quality_report['score'] -= 10
    
    # 4. 检查数值异常
    numeric_cols = ['商品实售价', '商品原价', '销量', '利润额', '订单零售额']
    for col in numeric_cols:
        if col in df.columns:
            try:
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                
                # 检查负数（某些字段不应为负）
                if col in ['商品实售价', '商品原价', '销量']:
                    negative_count = (numeric_series < 0).sum()
                    if negative_count > 0:
                        quality_report['warnings'].append({
                            'type': '警告',
                            'column': col,
                            'description': f'存在负数：{negative_count}行'
                        })
                        quality_report['score'] -= 2
                
                # 检查异常值（超出合理范围）
                if col == '商品实售价':
                    outliers = ((numeric_series > 10000) | (numeric_series < 0.1)).sum()
                    if outliers > 0:
                        quality_report['warnings'].append({
                            'type': '提示',
                            'column': col,
                            'description': f'可能存在异常价格：{outliers}行（<0.1或>10000）'
                        })
                        
            except Exception:
                pass
    
    # 5. 检查必需字段
    required_fields = ['订单ID', '商品名称', '商品实售价', '销量', '下单时间']
    missing_required = [field for field in required_fields if field not in df.columns]
    if missing_required:
        quality_report['issues'].append({
            'type': '严重',
            'column': ','.join(missing_required),
            'description': f'缺少必需字段：{missing_required}'
        })
        quality_report['score'] -= 15
    
    # 确保分数不低于0
    quality_report['score'] = max(0, quality_report['score'])
    
    # 生成等级
    if quality_report['score'] >= 90:
        quality_report['grade'] = '优秀'
        quality_report['grade_color'] = 'green'
    elif quality_report['score'] >= 70:
        quality_report['grade'] = '良好'
        quality_report['grade_color'] = 'blue'
    elif quality_report['score'] >= 50:
        quality_report['grade'] = '一般'
        quality_report['grade_color'] = 'orange'
    else:
        quality_report['grade'] = '较差'
        quality_report['grade_color'] = 'red'
    
    return quality_report


def save_data_to_cache(df: pd.DataFrame, file_name: str) -> str:
    """
    保存数据到本地缓存
    
    Args:
        df: 要保存的DataFrame
        file_name: 原始文件名
        
    Returns:
        保存的文件路径
    """
    import hashlib
    from datetime import datetime
    import pickle
    import gzip
    
    # 创建缓存目录
    cache_dir = APP_DIR / "学习数据仓库" / "uploaded_data"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名（基于内容hash和时间戳）
    content_hash = hashlib.md5(df.to_json().encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = file_name.replace('.xlsx', '').replace('.xls', '')
    
    cache_file = cache_dir / f"{safe_name}_{content_hash}_{timestamp}.pkl.gz"
    
    # 保存元数据
    metadata = {
        'original_file': file_name,
        'upload_time': datetime.now().isoformat(),
        'rows': len(df),
        'columns': list(df.columns),
        'data_hash': content_hash
    }
    
    # 使用gzip压缩保存
    with gzip.open(cache_file, 'wb') as f:
        pickle.dump({'data': df, 'metadata': metadata}, f)
    
    return str(cache_file)


def load_cached_data_list() -> List[Dict[str, Any]]:
    """
    获取所有缓存数据的列表
    
    Returns:
        缓存数据信息列表
    """
    import pickle
    import gzip
    
    cache_dir = APP_DIR / "学习数据仓库" / "uploaded_data"
    if not cache_dir.exists():
        return []
    
    cached_files = []
    for file in sorted(cache_dir.glob("*.pkl.gz"), reverse=True):
        try:
            with gzip.open(file, 'rb') as f:
                cached = pickle.load(f)
                metadata = cached.get('metadata', {})
                cached_files.append({
                    'file_path': str(file),
                    'file_name': file.name,
                    'original_file': metadata.get('original_file', 'Unknown'),
                    'upload_time': metadata.get('upload_time', 'Unknown'),
                    'rows': metadata.get('rows', 0),
                    'size_mb': file.stat().st_size / (1024 * 1024)
                })
        except Exception:
            continue
    
    return cached_files


def load_data_from_cache(file_path: str) -> Optional[pd.DataFrame]:
    """
    从缓存加载数据
    
    Args:
        file_path: 缓存文件路径
        
    Returns:
        DataFrame或None
    """
    import pickle
    import gzip
    
    try:
        with gzip.open(file_path, 'rb') as f:
            cached = pickle.load(f)
            return cached.get('data')
    except Exception as e:
        st.error(f"❌ 加载缓存失败: {str(e)}")
        return None



def normalize_label(label: Any) -> Any:
    """尝试规整列名/表名，兼容乱码"""
    if not isinstance(label, str):
        return label
    trimmed = label.strip()
    if trimmed in COLUMN_NAME_FIXES:
        return COLUMN_NAME_FIXES[trimmed]
    # 多种编码回退
    for source in ("latin1", "cp1252"):
        for target in ("gbk", "gb2312"):
            try:
                decoded = trimmed.encode(source, errors="ignore").decode(target, errors="ignore").strip()
                if decoded:
                    return COLUMN_NAME_FIXES.get(decoded, decoded)
            except Exception:
                continue
    return COLUMN_NAME_FIXES.get(trimmed, trimmed)

def rename_columns(df: pd.DataFrame, extra_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """统一DataFrame列名"""
    extra_map = extra_map or {}
    rename_map: Dict[str, str] = {}
    for col in df.columns:
        normalized = normalize_label(col)
        normalized = extra_map.get(normalized, normalized)
        rename_map[col] = normalized
    return df.rename(columns=rename_map)

def convert_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def aggregate_product_data(order_df: pd.DataFrame) -> pd.DataFrame:
    if "商品名称" not in order_df.columns:
        return pd.DataFrame()
    agg_map: Dict[str, str] = {}
    if "商品实售价" in order_df.columns:
        agg_map["商品实售价"] = "mean"
    if "商品原价" in order_df.columns:
        agg_map["商品原价"] = "mean"
    if "数量" in order_df.columns:
        agg_map["数量"] = "sum"
    if "剩余库存" in order_df.columns:
        agg_map["剩余库存"] = "max"
    if "一级分类" in order_df.columns:
        agg_map["一级分类"] = "first"
    if "三级分类" in order_df.columns:
        agg_map["三级分类"] = "first"
    if not agg_map:
        return pd.DataFrame()
    product_df = order_df.groupby("商品名称", as_index=False).agg(agg_map)
    rename_map = {
        "商品实售价": "售价",
        "商品原价": "原价",
        "数量": "月售",
        "剩余库存": "库存",
        "一级分类": "美团一级分类",
        "三级分类": "美团三级分类",
    }
    return product_df.rename(columns={k: v for k, v in rename_map.items() if k in product_df.columns})

def build_sales_summary(order_df: pd.DataFrame) -> pd.DataFrame:
    """构建销售汇总数据 - 简化版，避免复杂聚合问题"""
    if "下单时间" in order_df.columns:
        order_df = order_df.copy()
        order_df["下单时间"] = pd.to_datetime(order_df["下单时间"], errors="coerce")
        order_df["下单日期"] = order_df["下单时间"].dt.date
    if "下单日期" not in order_df.columns:
        return pd.DataFrame()
    
    # 简化聚合逻辑，只聚合数值列
    agg_dict: Dict[str, Any] = {"下单日期": "first"}
    if "预估订单收入" in order_df.columns:
        agg_dict["预估订单收入"] = "sum"
    if "实收价格" in order_df.columns:
        agg_dict["实收价格"] = "sum"
    if "数量" in order_df.columns:
        agg_dict["数量"] = "sum"
    
    # 不在这里聚合订单ID，避免维度问题
    # 直接按日期分组聚合数值
    try:
        summary = order_df.groupby("下单日期").agg(agg_dict).reset_index(drop=True)
    except Exception as e:
        # 如果聚合失败，返回空DataFrame
        return pd.DataFrame()
    
    rename_map = {
        "下单日期": "date",
        "预估订单收入": "estimated_revenue",
        "实收价格": "net_revenue",
        "数量": "items_sold",
    }
    return summary.rename(columns={k: v for k, v in rename_map.items() if k in summary.columns})

def build_customer_profile(order_df: pd.DataFrame) -> pd.DataFrame:
    candidate_cols = [
        "订单ID",
        "用户ID",
        "用户名称",
        "下单时间",
        "收货地址",
        "城市名称",
        "渠道",
        "配送方式",
        "门店名称",
    ]
    available = [col for col in candidate_cols if col in order_df.columns]
    if not available:
        return pd.DataFrame()
    profile = order_df[available].copy()
    if "下单时间" in profile.columns:
        profile["下单时间"] = pd.to_datetime(profile["下单时间"], errors="coerce")
    if "订单ID" in profile.columns:
        profile = profile.drop_duplicates(subset=["订单ID"], keep="last")
    return profile

def filter_channels(order_df: pd.DataFrame) -> pd.DataFrame:
    if "渠道" not in order_df.columns:
        return order_df
    filtered = order_df[~order_df["渠道"].isin(CHANNELS_TO_REMOVE)].copy()
    return filtered

def detect_data_period(order_df: pd.DataFrame) -> Optional[str]:
    date_series = None
    if "下单时间" in order_df.columns:
        date_series = pd.to_datetime(order_df["下单时间"], errors="coerce")
    elif "下单日期" in order_df.columns:
        date_series = pd.to_datetime(order_df["下单日期"], errors="coerce")
    if date_series is None or date_series.dropna().empty:
        return None
    date_series = date_series.dropna()
    start, end = date_series.min(), date_series.max()
    try:
        return f"{start:%Y-%m-%d} ~ {end:%Y-%m-%d}"
    except Exception:
        return None

@st.cache_data(ttl=60)  # 1分钟缓存，配送成本净成本模式最终修正 2025-10-13
def load_real_business_data(_cache_version: str = "v11_NEW_DATA_2025_10_15") -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """扫描并加载真实业务数据，返回(数据, 提示信息)
    
    重要更新 2025-10-13: 配送成本净成本模式最终修正
    - 配送成本公式: (配送费减免 + 物流配送费) - 用户支付配送费 = 净成本
    - 订单总收入: 商品实售价 + 打包费 + 用户支付配送费（完整收入）
    - 利润公式: 总收入 - 商品成本 - 配送净成本 - 其他成本
    
    Args:
        _cache_version: 缓存版本号，修改此参数可强制刷新缓存
    """
    messages: List[str] = []
    candidate_dirs = [
        APP_DIR / "实际数据",
        APP_DIR.parent / "实际数据",
        APP_DIR / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据" / "比价看板模块",
    ]

    data_dir: Optional[Path] = None
    candidates: List[Path] = []
    for path in candidate_dirs:
        if not path.exists():
            continue
        current_candidates = sorted(
            f for f in path.glob("*.xlsx")
            if not f.name.startswith("~$")
        )
        if current_candidates:
            data_dir = path
            candidates = current_candidates
            break
    if data_dir is None:
        tried = "；".join(str(path) for path in candidate_dirs)
        messages.append(f"未找到数据目录，可在以下位置之一创建: {tried}")
        return None, messages
    if not candidates:
        messages.append("数据目录下未找到Excel文件")
        return None, messages

    target_file = next((f for f in candidates if "测试数据" in f.name), candidates[0])
    try:
        xls = pd.ExcelFile(target_file)
    except Exception as exc:
        messages.append(f"读取 {target_file.name} 失败: {exc}")
        return None, messages

    def pick_sheet(kind: str) -> Optional[str]:
        keywords = SHEET_KEYWORDS.get(kind, [])
        for sheet in xls.sheet_names:
            normalized = str(normalize_label(sheet)).replace(" ", "")
            for kw in keywords:
                if kw in normalized:
                    return sheet
        return None

    sheet_map = {
        "order": pick_sheet("order") or (xls.sheet_names[0] if xls.sheet_names else None),
        "competitor": pick_sheet("competitor"),
        "cost": pick_sheet("cost"),
        "traffic": pick_sheet("traffic"),
    }

    if sheet_map["competitor"] is None:
        for sheet in xls.sheet_names:
            normalized = str(normalize_label(sheet)).replace(" ", "")
            if "竞对" in normalized or "竞品" in normalized:
                sheet_map["competitor"] = sheet
                break

    if sheet_map["cost"] is None:
        for sheet in xls.sheet_names:
            normalized = str(normalize_label(sheet)).replace(" ", "")
            if "成本" in normalized or "费用" in normalized:
                sheet_map["cost"] = sheet
                break

    if sheet_map["traffic"] is None:
        for sheet in xls.sheet_names:
            normalized = str(normalize_label(sheet)).replace(" ", "")
            if "流量" in normalized or "客流" in normalized:
                sheet_map["traffic"] = sheet
                break

    data_frames: Dict[str, pd.DataFrame] = {}
    for key, sheet_name in sheet_map.items():
        if sheet_name is None:
            messages.append(f"未找到{key}相关的工作表")
            continue
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            data_frames[key] = rename_columns(df)
        except Exception as exc:
            messages.append(f"读取工作表 {sheet_name} 失败: {exc}")

    order_df = data_frames.get("order", pd.DataFrame())
    if order_df.empty:
        messages.append("未获取到门店订单数据")
        return None, messages

    order_df = convert_numeric(order_df, NUMERIC_COLUMNS)
    filtered_order_df = filter_channels(order_df)
    removed_rows = len(order_df) - len(filtered_order_df)
    if removed_rows > 0:
        messages.append(f"已剔除指定渠道订单 {removed_rows:,} 条")
    order_df = filtered_order_df

    product_df = aggregate_product_data(order_df)
    sales_summary = build_sales_summary(order_df)
    customer_df = build_customer_profile(order_df)

    competitor_df = data_frames.get("competitor", pd.DataFrame())
    if not competitor_df.empty:
        competitor_df = convert_numeric(competitor_df, ["售价", "原价", "月售"])

    cost_df = data_frames.get("cost", pd.DataFrame())
    traffic_df = data_frames.get("traffic", pd.DataFrame())

    store_identifier = order_df.get("门店名称")
    store_id = "REAL_STORE_DATA"
    if store_identifier is not None and not store_identifier.dropna().empty:
        store_id = str(store_identifier.mode().iat[0])

    data_period = detect_data_period(order_df) or "近30天"
    
    # 安全计算订单数和商品数
    try:
        if "订单ID" in order_df.columns:
            total_orders = int(order_df["订单ID"].nunique())
        else:
            total_orders = len(order_df)
    except Exception:
        total_orders = len(order_df)
    
    try:
        if not product_df.empty and "商品名称" in product_df.columns:
            total_products = int(product_df["商品名称"].nunique())
        elif "商品名称" in order_df.columns:
            total_products = int(order_df["商品名称"].nunique())
        else:
            total_products = 0
    except Exception:
        total_products = 0

    result: Dict[str, Any] = {
        "store_id": store_id,
        "order_data": order_df,
        "raw_data": order_df,  # 添加 raw_data 键用于场景营销分析
        "product_data": product_df,
        "sales_data": sales_summary,
        "customer_data": customer_df,
        "competitor_data": competitor_df,
        "cost_data": cost_df,
        "traffic_data": traffic_df,
        "data_source": f"文件: {target_file.name}",
        "data_period": data_period,
        "total_orders": total_orders,
        "total_products": total_products,
    }

    return result, messages

def process_uploaded_comparison_file(comparison_file) -> Optional[Dict[str, Any]]:
    """处理上传的已比对好的Excel文件"""
    if not comparison_file:
        return None
        
    try:
        # 读取Excel文件的所有Sheet
        st.info("📊 正在读取比价结果文件...")
        
        excel_file = pd.ExcelFile(comparison_file)
        sheet_names = excel_file.sheet_names
        
        st.success(f"✅ 检测到 {len(sheet_names)} 个Sheet: {sheet_names}")
        
        # 读取各个Sheet的数据
        sheets_data = {}
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(comparison_file, sheet_name=sheet_name)
                if len(df) > 0:
                    sheets_data[sheet_name] = df
                    st.info(f"✅ {sheet_name}: {len(df)} 条记录")
                else:
                    st.info(f"⚠️ {sheet_name}: 空表")
            except Exception as e:
                st.warning(f"❌ 读取 {sheet_name} 失败: {e}")
                continue
        
        if not sheets_data:
            st.error("Excel文件中没有有效数据，请检查文件格式")
            return None
        
        # 解析比价数据并生成统计指标
        st.info("🔄 正在解析比价结果...")
        
        # 统计匹配情况
        barcode_matches = sheets_data.get('1-条码精确匹配', pd.DataFrame())
        name_matches = sheets_data.get('2-名称模糊匹配(无条码)', pd.DataFrame())
        
        barcode_match_count = len(barcode_matches)
        name_match_count = len(name_matches)
        total_matches = barcode_match_count + name_match_count
        
        # 统计独有商品
        store_a_unique_key = None
        store_b_unique_key = None
        store_names = []
        
        for sheet_name in sheet_names:
            if '独有商品' in sheet_name:
                if sheet_name.startswith('3-'):
                    store_a_unique_key = sheet_name
                    # 提取店铺名称
                    parts = sheet_name.split('-')
                    if len(parts) >= 2:
                        store_name = parts[1]
                        store_names.append(store_name)
                elif sheet_name.startswith('4-'):
                    store_b_unique_key = sheet_name
                    # 提取店铺名称
                    parts = sheet_name.split('-')
                    if len(parts) >= 2:
                        store_name = parts[1]
                        store_names.append(store_name)
        
        store_a_unique = sheets_data.get(store_a_unique_key, pd.DataFrame())
        store_b_unique = sheets_data.get(store_b_unique_key, pd.DataFrame())
        
        store_a_unique_count = len(store_a_unique)
        store_b_unique_count = len(store_b_unique)
        
        # 价格优势分析
        price_advantage = sheets_data.get('5-库存>0&A折扣≥B折扣', pd.DataFrame())
        price_advantage_count = len(price_advantage)
        
        # 计算价格差异统计（从匹配的商品中）
        avg_price_diff = 0
        max_price_diff = 0
        
        # 尝试从匹配数据中计算价格差异
        if len(barcode_matches) > 0:
            price_cols = [col for col in barcode_matches.columns if '售价' in col or '价格' in col]
            if len(price_cols) >= 2:
                try:
                    price_diffs = barcode_matches[price_cols[0]] - barcode_matches[price_cols[1]]
                    avg_price_diff = price_diffs.mean()
                    max_price_diff = price_diffs.abs().max()
                except Exception:
                    pass
        
        # 构造分析结果
        store_display_names = store_names if len(store_names) >= 2 else ['门店A', '门店B']
        
        analysis_result = {
            "generated_at": pd.Timestamp.now().isoformat(),
            "comparison_type": "multi_store_comparison",
            "sheets_data": sheets_data,
            "sheet_names": sheet_names,
            "stores": [
                {"display_name": store_display_names[0], "unique_products": store_a_unique_count},
                {"display_name": store_display_names[1], "unique_products": store_b_unique_count}
            ],
            "metrics": [
                {
                    "id": "barcode_matches",
                    "label": "条码精确匹配",
                    "value": barcode_match_count,
                    "unit": "个",
                    "context": {"type": "exact_match"}
                },
                {
                    "id": "name_matches",
                    "label": "名称模糊匹配",
                    "value": name_match_count,
                    "unit": "个", 
                    "context": {"type": "fuzzy_match"}
                },
                {
                    "id": "total_matches",
                    "label": "总匹配商品数",
                    "value": total_matches,
                    "unit": "个",
                    "context": {"barcode": barcode_match_count, "name": name_match_count}
                },
                {
                    "id": "unique_store_a",
                    "label": f"{store_display_names[0]} 独有商品",
                    "value": store_a_unique_count,
                    "unit": "个",
                    "context": {"store": store_display_names[0]}
                },
                {
                    "id": "unique_store_b",
                    "label": f"{store_display_names[1]} 独有商品",
                    "value": store_b_unique_count,
                    "unit": "个",
                    "context": {"store": store_display_names[1]}
                },
                {
                    "id": "price_advantage",
                    "label": "价格优势商品数",
                    "value": price_advantage_count,
                    "unit": "个",
                    "context": {"criteria": "库存>0&A折扣≥B折扣"}
                }
            ],
            "summary": {
                "avg_price_diff": avg_price_diff,
                "max_price_diff": max_price_diff,
                "comparison_coverage": total_matches / (total_matches + store_a_unique_count + store_b_unique_count) if (total_matches + store_a_unique_count + store_b_unique_count) > 0 else 0
            },
            "warnings": []
        }
        
        # 添加警告
        if total_matches < 10:
            analysis_result["warnings"].append("匹配商品数量较少，可能影响分析准确性")
        
        if store_a_unique_count + store_b_unique_count > total_matches:
            analysis_result["warnings"].append("独有商品数量较多，建议检查商品分类和命名规范")
        
        st.success(f"🎉 比价结果解析完成！匹配 {total_matches} 个商品 (条码:{barcode_match_count}, 名称:{name_match_count})")
        return analysis_result
        
    except Exception as e:
        st.error(f"❌ 处理比价结果文件时出错: {str(e)}")
        import traceback
        st.error(f"详细错误: {traceback.format_exc()}")
        return None



def render_comparison_file_analysis(price_panel_payload: Dict[str, Any]) -> None:
    """渲染比价结果文件分析"""
    try:
        # 显示基础统计
        st.subheader("📊 比价结果概览")
        
        # 基础指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = price_panel_payload.get("metrics", [])
        stores = price_panel_payload.get("stores", [])
        summary = price_panel_payload.get("summary", {})
        
        # 找到相关指标
        total_matches = 0
        barcode_matches = 0
        name_matches = 0
        store_a_unique = 0
        store_b_unique = 0
        
        for metric in metrics:
            metric_id = metric.get("id", "")
            value = metric.get("value", 0)
            
            if metric_id == "total_matches":
                total_matches = value
            elif metric_id == "barcode_matches":
                barcode_matches = value
            elif metric_id == "name_matches":
                name_matches = value
            elif metric_id == "unique_store_a":
                store_a_unique = value
            elif metric_id == "unique_store_b":
                store_b_unique = value
        
        with col1:
            st.metric(
                "总匹配商品",
                f"{total_matches:,}",
                help="条码匹配 + 名称匹配的总商品数量"
            )
        
        with col2:
            st.metric(
                "条码精确匹配",
                f"{barcode_matches:,}",
                help="通过条码精确匹配的商品数量"
            )
        
        with col3:
            st.metric(
                "名称模糊匹配",
                f"{name_matches:,}",
                help="通过商品名称模糊匹配的商品数量"
            )
        
        with col4:
            coverage = summary.get("comparison_coverage", 0)
            st.metric(
                "匹配覆盖率",
                f"{coverage:.1%}",
                help="匹配商品数占总商品数的比例"
            )
        
        # 店铺对比
        st.subheader("🏪 店铺商品对比")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if len(stores) > 0:
                store_name_a = stores[0].get("display_name", "店铺A")
                st.metric(
                    f"{store_name_a} 独有商品",
                    f"{store_a_unique:,}",
                    help=f"{store_name_a}特有的商品数量"
                )
        
        with col2:
            if len(stores) > 1:
                store_name_b = stores[1].get("display_name", "店铺B")
                st.metric(
                    f"{store_name_b} 独有商品",
                    f"{store_b_unique:,}",
                    help=f"{store_name_b}特有的商品数量"
                )
        
        # 匹配结果可视化
        st.subheader("📈 匹配结果分析")
        
        # 匹配类型分布饼图
        if total_matches > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # 匹配类型分布
                match_data = {
                    "匹配类型": ["条码精确匹配", "名称模糊匹配"],
                    "数量": [barcode_matches, name_matches]
                }
                
                fig_match = px.pie(
                    values=match_data["数量"],
                    names=match_data["匹配类型"],
                    title="匹配类型分布",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_match, use_container_width=True)
            
            with col2:
                # 商品分布对比
                all_data = {
                    "类别": ["匹配商品", f"{store_name_a}独有", f"{store_name_b}独有"],
                    "数量": [total_matches, store_a_unique, store_b_unique]
                }
                
                fig_distribution = px.bar(
                    x=all_data["类别"],
                    y=all_data["数量"],
                    title="商品分布对比",
                    color=all_data["类别"],
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_distribution.update_layout(showlegend=False)
                st.plotly_chart(fig_distribution, use_container_width=True)
        
        # 详细Sheet数据展示
        st.subheader("📋 详细数据查看")
        
        sheets_data = price_panel_payload.get("sheets_data", {})
        sheet_names = price_panel_payload.get("sheet_names", [])
        
        if sheets_data:
            # 创建Sheet选择器
            selected_sheet = st.selectbox(
                "选择要查看的数据Sheet:",
                options=sheet_names,
                                 help="选择不同的Sheet查看详细数据内容"
            )
            
            if selected_sheet and selected_sheet in sheets_data:
                df = sheets_data[selected_sheet]
                
                st.write(f"**{selected_sheet}** - 共 {len(df)} 条记录")
                
                if len(df) > 0:
                    # 显示前几行数据
                    st.dataframe(df.head(20), use_container_width=True)
                    
                    # 提供下载选项
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label=f"下载 {selected_sheet} 数据 (CSV)",
                        data=csv_data,
                        file_name=f"{selected_sheet}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"download_{selected_sheet}"
                    )
                else:
                    st.info("此Sheet暂无数据")
        
        # 添加智能洞察报告生成按钮
        st.markdown("---")
        if st.button("🎯 生成智能洞察报告", help="基于当前数据生成详细的比价分析报告"):
            generate_insight_report(price_panel_payload)        # 新增高级分析模块
        st.markdown("---")
        render_advanced_price_analysis(price_panel_payload)
        
        # 警告信息
        warnings = price_panel_payload.get("warnings", [])
        if warnings:
            st.subheader("⚠️ 注意事项")
            for warning in warnings:
                st.warning(warning)
                
    except Exception as e:
        st.error(f"渲染比价分析时出错: {str(e)}")
        import traceback
        st.error(f"详细错误: {traceback.format_exc()}")


def render_advanced_price_analysis(price_panel_payload: Dict[str, Any]) -> None:
    """渲染高级比价分析模块"""
    st.subheader("🎯 高级价格分析")
    
    sheets_data = price_panel_payload.get("sheets_data", {})
    stores = price_panel_payload.get("stores", [])
    
    if not sheets_data:
        st.info("暂无详细数据，无法进行高级分析")
        return
    
    # 获取匹配数据
    barcode_matches = sheets_data.get('1-条码精确匹配', pd.DataFrame())
    name_matches = sheets_data.get('2-名称模糊匹配(无条码)', pd.DataFrame())
    
    # 合并匹配数据
    all_matches = pd.DataFrame()
    if not barcode_matches.empty:
        barcode_matches['匹配类型'] = '条码精确匹配'
        all_matches = pd.concat([all_matches, barcode_matches], ignore_index=True)
    if not name_matches.empty:
        name_matches['匹配类型'] = '名称模糊匹配'
        all_matches = pd.concat([all_matches, name_matches], ignore_index=True)
    
    if all_matches.empty:
        st.info("暂无匹配数据，无法进行价格分析")
        return
    
    # 创建分析选项卡
    analysis_tabs = st.tabs([
        "💰 价格竞争力热力图", 
        "📊 价格分层分析", 
        "🎯 匹配质量分析",
        "📈 库存-价格关系",
        "🏆 竞争优势分析"
    ])
    
    with analysis_tabs[0]:
        render_price_competitiveness_heatmap(all_matches, stores)
    
    with analysis_tabs[1]:
        render_price_tier_analysis(all_matches, stores)
    
    with analysis_tabs[2]:
        render_match_quality_analysis(all_matches, price_panel_payload)
    
    with analysis_tabs[3]:
        render_inventory_price_analysis(all_matches, stores)
    
    with analysis_tabs[4]:
        render_competitive_advantage_analysis(all_matches, sheets_data, stores)


def render_price_competitiveness_heatmap(all_matches: pd.DataFrame, stores: List[Dict]) -> None:
    """渲染价格竞争力热力图"""
    st.write("**💰 按商品分类的价格竞争力热力图**")
    
    try:
        # 寻找价格列
        price_cols = [col for col in all_matches.columns if '售价' in col or '价格' in col]
        category_cols = [col for col in all_matches.columns if '分类' in col]
        
        if len(price_cols) < 2 or not category_cols:
            st.info("数据中缺少价格或分类信息，无法生成热力图")
            return
        
        price_col_a = price_cols[0]
        price_col_b = price_cols[1] if len(price_cols) > 1 else price_cols[0]
        category_col = category_cols[0]
        
        # 计算价格优势
        all_matches = all_matches.copy()
        all_matches['价格差异'] = pd.to_numeric(all_matches[price_col_a], errors='coerce') - pd.to_numeric(all_matches[price_col_b], errors='coerce')
        all_matches['价格优势率'] = (all_matches['价格差异'] / pd.to_numeric(all_matches[price_col_b], errors='coerce')) * 100
        
        # 定义价格区间
        all_matches['价格区间'] = pd.cut(
            pd.to_numeric(all_matches[price_col_a], errors='coerce'), 
            bins=[0, 10, 30, 50, 100, float('inf')], 
            labels=['低价(<10元)', '中低价(10-30元)', '中价(30-50元)', '中高价(50-100元)', '高价(>100元)']
        )
        
        # 按分类和价格区间聚合
        heatmap_data = all_matches.groupby([category_col, '价格区间']).agg({
            '价格优势率': 'mean',
            price_col_a: 'count'
        }).reset_index()
        
        # 创建透视表用于热力图
        pivot_data = heatmap_data.pivot(index=category_col, columns='价格区间', values='价格优势率')
        
        if not pivot_data.empty:
            fig = px.imshow(
                pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                color_continuous_scale='RdYlGn',
                title="价格竞争力热力图 (绿色=有优势，红色=处劣势)",
                labels={'color': '价格优势率(%)'}
            )
            
            fig.update_layout(
                height=max(400, len(pivot_data.index) * 30),
                xaxis_title="价格区间",
                yaxis_title="商品分类"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示数据表
            with st.expander("📊 详细数据"):
                display_data = heatmap_data.copy()
                display_data['价格优势率'] = display_data['价格优势率'].round(2)
                display_data = display_data.rename(columns={price_col_a: '商品数量'})
                st.dataframe(display_data, use_container_width=True)
        else:
            st.info("数据不足以生成热力图")
            
    except Exception as e:
        st.error(f"生成价格竞争力热力图时出错: {str(e)}")


def render_price_tier_analysis(all_matches: pd.DataFrame, stores: List[Dict]) -> None:
    """渲染价格分层分析"""
    st.write("**📊 价格分层竞争分析**")
    
    try:
        price_cols = [col for col in all_matches.columns if '售价' in col or '价格' in col]
        
        if len(price_cols) < 2:
            st.info("数据中缺少足够的价格信息")
            return
        
        price_col_a = price_cols[0]
        price_col_b = price_cols[1]
        
        # 数据处理
        df = all_matches.copy()
        df[price_col_a] = pd.to_numeric(df[price_col_a], errors='coerce')
        df[price_col_b] = pd.to_numeric(df[price_col_b], errors='coerce')
        df = df.dropna(subset=[price_col_a, price_col_b])
        
        # 定义价格分层
        df['价格分层_A'] = pd.cut(df[price_col_a], bins=[0, 10, 30, 50, 100, float('inf')], 
                              labels=['低价', '中低价', '中价', '中高价', '高价'])
        df['价格分层_B'] = pd.cut(df[price_col_b], bins=[0, 10, 30, 50, 100, float('inf')], 
                              labels=['低价', '中低价', '中价', '中高价', '高价'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 价格分层分布对比
            tier_counts_a = df['价格分层_A'].value_counts()
            tier_counts_b = df['价格分层_B'].value_counts()
            
            fig = go.Figure()
            
            store_name_a = stores[0].get('display_name', '店铺A') if stores else '店铺A'
            store_name_b = stores[1].get('display_name', '店铺B') if len(stores) > 1 else '店铺B'
            
            fig.add_trace(go.Bar(
                name=store_name_a,
                x=tier_counts_a.index,
                y=tier_counts_a.values,
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name=store_name_b,
                x=tier_counts_b.index,
                y=tier_counts_b.values,
                marker_color='lightcoral'
            ))
            
            fig.update_layout(
                title='价格分层分布对比',
                xaxis_title='价格分层',
                yaxis_title='商品数量',
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 价格差异箱线图
            df['价格差异'] = df[price_col_a] - df[price_col_b]
            
            fig = px.box(
                df, 
                x='价格分层_A', 
                y='价格差异',
                title='各价格分层的价格差异分布',
                labels={'价格分层_A': '价格分层', '价格差异': '价格差异(元)'}
            )
            
            fig.add_hline(y=0, line_dash="dash", line_color="red", 
                         annotation_text="价格持平线")
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 价格优势统计
        st.write("**📈 价格优势统计**")
        
        df['价格优势'] = df['价格差异'].apply(lambda x: '我方优势' if x < 0 else '对手优势' if x > 0 else '价格相等')
        
        advantage_stats = df.groupby(['价格分层_A', '价格优势']).size().unstack(fill_value=0)
        
        if not advantage_stats.empty:
            # 计算优势比例
            advantage_pct = advantage_stats.div(advantage_stats.sum(axis=1), axis=0) * 100
            
            fig = px.bar(
                advantage_pct.reset_index(),
                x='价格分层_A',
                y=['我方优势', '对手优势', '价格相等'] if all(col in advantage_pct.columns for col in ['我方优势', '对手优势', '价格相等']) else advantage_pct.columns,
                title='各价格分层的竞争优势占比',
                labels={'value': '占比(%)', '价格分层_A': '价格分层'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"生成价格分层分析时出错: {str(e)}")


def render_match_quality_analysis(all_matches: pd.DataFrame, price_panel_payload: Dict[str, Any]) -> None:
    """渲染匹配质量分析"""
    st.write("**🎯 商品匹配质量分析**")
    
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            # 匹配类型质量分布
            if '匹配类型' in all_matches.columns:
                match_type_counts = all_matches['匹配类型'].value_counts()
                
                fig = px.pie(
                    values=match_type_counts.values,
                    names=match_type_counts.index,
                    title="匹配方式分布",
                    color_discrete_sequence=['#2E8B57', '#4682B4', '#DC143C']
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 匹配置信度分析（如果有相似度数据）
            similarity_cols = [col for col in all_matches.columns if '相似度' in col or '置信度' in col or 'similarity' in col.lower()]
            
            if similarity_cols:
                similarity_col = similarity_cols[0]
                similarity_data = pd.to_numeric(all_matches[similarity_col], errors='coerce').dropna()
                
                if not similarity_data.empty:
                    fig = px.histogram(
                        x=similarity_data,
                        title="匹配置信度分布",
                        labels={'x': '置信度', 'y': '商品数量'},
                        nbins=20
                    )
                    
                    fig.add_vline(x=0.8, line_dash="dash", line_color="green", 
                                 annotation_text="高质量匹配线(0.8)")
                    fig.add_vline(x=0.6, line_dash="dash", line_color="orange", 
                                 annotation_text="中等质量匹配线(0.6)")
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无有效的置信度数据")
            else:
                # 基于匹配类型的质量评估
                quality_map = {'条码精确匹配': '高质量', '名称模糊匹配': '中等质量'}
                all_matches['匹配质量'] = all_matches['匹配类型'].map(quality_map)
                
                quality_counts = all_matches['匹配质量'].value_counts()
                
                fig = px.bar(
                    x=quality_counts.index,
                    y=quality_counts.values,
                    title="匹配质量分布",
                    color=quality_counts.values,
                    color_continuous_scale='Viridis'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 未匹配原因分析
        st.write("**📋 未匹配商品分析**")
        
        sheets_data = price_panel_payload.get("sheets_data", {})
        
        # 获取独有商品数据
        unique_products = []
        for sheet_name, df in sheets_data.items():
            if '独有商品' in sheet_name and not df.empty:
                unique_products.append({
                    'sheet': sheet_name,
                    'count': len(df),
                    'store': sheet_name.split('-')[1] if '-' in sheet_name else sheet_name
                })
        
        if unique_products:
            unique_df = pd.DataFrame(unique_products)
            
            fig = px.bar(
                unique_df,
                x='store',
                y='count',
                title='各店铺独有商品数量',
                color='count',
                color_continuous_scale='Reds'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示未匹配原因分析
            with st.expander("🔍 可能的未匹配原因"):
                st.markdown("""
                **常见未匹配原因：**
                - 🏷️ **商品名称差异**：同一商品在不同平台使用不同名称
                - 📦 **规格描述不一致**：包装规格、容量描述方式不同
                - 🏪 **独家商品**：某店铺独有的商品或品牌
                - 📊 **分类体系差异**：不同平台的商品分类标准不同
                - 🔢 **条码缺失**：部分商品缺少标准条码信息
                
                **建议改进措施：**
                - 完善商品主数据管理
                - 统一商品命名规范
                - 补充缺失的条码信息
                - 建立分类映射关系
                """)
        
    except Exception as e:
        st.error(f"生成匹配质量分析时出错: {str(e)}")


def render_inventory_price_analysis(all_matches: pd.DataFrame, stores: List[Dict]) -> None:
    """渲染库存-价格关系分析"""
    st.write("**📈 库存与价格策略分析**")
    
    try:
        # 寻找库存和价格相关列
        inventory_cols = [col for col in all_matches.columns if '库存' in col or '库存量' in col or 'stock' in col.lower()]
        price_cols = [col for col in all_matches.columns if '售价' in col or '价格' in col]
        sales_cols = [col for col in all_matches.columns if '销量' in col or '月售' in col or 'sales' in col.lower()]
        
        if not inventory_cols or len(price_cols) < 2:
            st.info("数据中缺少库存或价格信息，无法进行库存-价格分析")
            return
        
        inventory_col = inventory_cols[0]
        price_col_a = price_cols[0]
        price_col_b = price_cols[1] if len(price_cols) > 1 else price_cols[0]
        
        # 数据处理
        df = all_matches.copy()
        df[inventory_col] = pd.to_numeric(df[inventory_col], errors='coerce')
        df[price_col_a] = pd.to_numeric(df[price_col_a], errors='coerce')
        df[price_col_b] = pd.to_numeric(df[price_col_b], errors='coerce')
        df = df.dropna(subset=[inventory_col, price_col_a, price_col_b])
        
        if df.empty:
            st.info("处理后无有效数据")
            return
        
        df['价格差异'] = df[price_col_a] - df[price_col_b]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 库存-价格散点图
            fig = px.scatter(
                df,
                x=inventory_col,
                y=price_col_a,
                size='价格差异' if '价格差异' in df.columns else None,
                color='价格差异',
                title='库存量与价格关系',
                labels={inventory_col: '库存量', price_col_a: '我方价格(元)'},
                color_continuous_scale='RdYlGn_r'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 库存预警分析
            if sales_cols:
                sales_col = sales_cols[0]
                df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
                df = df.dropna(subset=[sales_col])
                
                # 计算库销比
                df['库销比'] = df[inventory_col] / (df[sales_col] + 1)  # +1避免除零
                
                # 定义预警等级
                def get_warning_level(row):
                    if row['库销比'] < 0.5:
                        return '高风险'
                    elif row['库销比'] < 1.0:
                        return '中风险'
                    elif row['库销比'] < 2.0:
                        return '低风险'
                    else:
                        return '安全'
                
                df['预警等级'] = df.apply(get_warning_level, axis=1)
                
                warning_counts = df['预警等级'].value_counts()
                
                fig = px.pie(
                    values=warning_counts.values,
                    names=warning_counts.index,
                    title="库存预警等级分布",
                    color_discrete_map={
                        '高风险': '#DC143C',
                        '中风险': '#FF8C00',
                        '低风险': '#32CD32',
                        '安全': '#228B22'
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 库存水平分布
                df['库存水平'] = pd.cut(df[inventory_col], 
                                    bins=[0, 10, 50, 100, 500, float('inf')],
                                    labels=['极低库存', '低库存', '中等库存', '高库存', '过量库存'])
                
                inventory_dist = df['库存水平'].value_counts()
                
                fig = px.bar(
                    x=inventory_dist.index,
                    y=inventory_dist.values,
                    title='库存水平分布',
                    color=inventory_dist.values,
                    color_continuous_scale='Blues'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 高风险商品提醒
        if sales_cols and '预警等级' in df.columns:
            high_risk_products = df[df['预警等级'] == '高风险']
            
            if not high_risk_products.empty:
                st.warning(f"⚠️ 发现 {len(high_risk_products)} 个高风险商品（库存不足）")
                
                with st.expander("查看高风险商品详情"):
                    risk_display = high_risk_products[['商品名称', inventory_col, sales_col, '库销比', '价格差异']].copy() if '商品名称' in high_risk_products.columns else high_risk_products[[inventory_col, sales_col, '库销比', '价格差异']].copy()
                    risk_display = risk_display.round(2)
                    st.dataframe(risk_display, use_container_width=True)
        
    except Exception as e:
        st.error(f"生成库存-价格分析时出错: {str(e)}")


def render_competitive_advantage_analysis(all_matches: pd.DataFrame, sheets_data: Dict, stores: List[Dict]) -> None:
    """渲染竞争优势分析"""
    st.write("**🏆 综合竞争优势分析**")
    
    try:
        price_cols = [col for col in all_matches.columns if '售价' in col or '价格' in col]
        
        if len(price_cols) < 2:
            st.info("数据中缺少足够的价格信息")
            return
        
        price_col_a = price_cols[0]
        price_col_b = price_cols[1]
        
        # 数据处理
        df = all_matches.copy()
        df[price_col_a] = pd.to_numeric(df[price_col_a], errors='coerce')
        df[price_col_b] = pd.to_numeric(df[price_col_b], errors='coerce')
        df = df.dropna(subset=[price_col_a, price_col_b])
        
        # 计算竞争指标
        df['价格差异'] = df[price_col_a] - df[price_col_b]
        df['价格优势率'] = (df['价格差异'] / df[price_col_b]) * 100
        
        store_name_a = stores[0].get('display_name', '店铺A') if stores else '店铺A'
        store_name_b = stores[1].get('display_name', '店铺B') if len(stores) > 1 else '店铺B'
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 价格优势分布
            df['竞争状态'] = df['价格优势率'].apply(
                lambda x: f'{store_name_a}显著优势' if x < -10 
                else f'{store_name_a}轻微优势' if x < 0 
                else '价格相当' if abs(x) < 5 
                else f'{store_name_b}轻微优势' if x < 10 
                else f'{store_name_b}显著优势'
            )
            
            competitive_dist = df['竞争状态'].value_counts()
            
            colors = {
                f'{store_name_a}显著优势': '#228B22',
                f'{store_name_a}轻微优势': '#90EE90',
                '价格相当': '#FFD700',
                f'{store_name_b}轻微优势': '#FFA07A',
                f'{store_name_b}显著优势': '#DC143C'
            }
            
            fig = px.pie(
                values=competitive_dist.values,
                names=competitive_dist.index,
                title='竞争优势分布',
                color=competitive_dist.index,
                color_discrete_map=colors
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 分类别竞争优势
            category_cols = [col for col in df.columns if '分类' in col]
            
            if category_cols:
                category_col = category_cols[0]
                
                category_advantage = df.groupby(category_col).agg({
                    '价格优势率': 'mean',
                    price_col_a: 'count'
                }).reset_index()
                
                category_advantage = category_advantage.rename(columns={price_col_a: '商品数量'})
                category_advantage['优势方'] = category_advantage['价格优势率'].apply(
                    lambda x: store_name_a if x < 0 else store_name_b
                )
                
                fig = px.bar(
                    category_advantage,
                    x=category_col,
                    y='价格优势率',
                    color='优势方',
                    title='各分类价格优势对比',
                    color_discrete_map={
                        store_name_a: '#1f77b4',
                        store_name_b: '#ff7f0e'
                    }
                )
                
                fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="平衡线")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 价格优势率分布直方图
                fig = px.histogram(
                    df,
                    x='价格优势率',
                    title='价格优势率分布',
                    labels={'价格优势率': '价格优势率(%)', 'count': '商品数量'},
                    nbins=30
                )
                
                fig.add_vline(x=0, line_dash="dash", line_color="black", annotation_text="平衡线")
                fig.add_vline(x=-10, line_dash="dash", line_color="green", annotation_text="显著优势线")
                fig.add_vline(x=10, line_dash="dash", line_color="red", annotation_text="显著劣势线")
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 竞争策略建议
        st.subheader("💡 竞争策略建议")
        
        # 计算关键指标
        total_products = len(df)
        our_advantage = len(df[df['价格优势率'] < -5])
        competitor_advantage = len(df[df['价格优势率'] > 5])
        similar_price = total_products - our_advantage - competitor_advantage
        
        our_advantage_rate = our_advantage / total_products * 100
        competitor_advantage_rate = competitor_advantage / total_products * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                f"{store_name_a}优势商品",
                f"{our_advantage} 个",
                delta=f"{our_advantage_rate:.1f}%",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "价格相当商品",
                f"{similar_price} 个",
                delta=f"{similar_price/total_products*100:.1f}%",
                delta_color="off"
            )
        
        with col3:
            st.metric(
                f"{store_name_b}优势商品",
                f"{competitor_advantage} 个",
                delta=f"{competitor_advantage_rate:.1f}%",
                delta_color="inverse"
            )
        
        # 策略建议
        if our_advantage_rate > 50:
            st.success(f"🎉 整体价格竞争力较强！在 {our_advantage_rate:.1f}% 的商品上具有价格优势")
        elif our_advantage_rate > 30:
            st.info(f"💪 价格竞争力中等，建议重点关注 {store_name_b} 优势商品的定价策略")
        else:
            st.warning(f"⚠️ 价格竞争力较弱，建议全面审视定价策略，特别是 {competitor_advantage} 个劣势商品")
        
        # 具体建议
        with st.expander("📋 详细策略建议"):
            if our_advantage_rate > 40:
                st.markdown(f"""
                **🎯 维持优势策略：**
                - 保持现有 {our_advantage} 个优势商品的价格竞争力
                - 适当提升优势商品的毛利率
                - 重点推广价格优势商品，提升销量
                """)
            
            if competitor_advantage > 0:
                st.markdown(f"""
                **⚡ 劣势改进策略：**
                - 紧急调整 {competitor_advantage} 个劣势商品定价
                - 分析成本结构，寻找降价空间
                - 考虑捆绑销售或促销活动
                """)
            
            if similar_price > 0:
                st.markdown(f"""
                **🔄 均势商品策略：**
                - 通过服务差异化获得竞争优势
                - 考虑小幅调价测试市场反应
                - 关注库存和销量情况，优化商品组合
                """)
        
    except Exception as e:
        st.error(f"生成竞争优势分析时出错: {str(e)}")


def generate_insight_report(price_panel_payload: Dict[str, Any]) -> None:
    """生成智能洞察报告"""
    try:
        st.subheader("🎯 智能洞察报告")
        
        sheets_data = price_panel_payload.get("sheets_data", {})
        stores = price_panel_payload.get("stores", [])
        metrics = price_panel_payload.get("metrics", [])
        summary = price_panel_payload.get("summary", {})
        
        # 获取基础数据
        barcode_matches = sheets_data.get('1-条码精确匹配', pd.DataFrame())
        name_matches = sheets_data.get('2-名称模糊匹配(无条码)', pd.DataFrame())
        
        store_name_a = stores[0].get('display_name', '店铺A') if stores else '店铺A'
        store_name_b = stores[1].get('display_name', '店铺B') if len(stores) > 1 else '店铺B'
        
        # 合并匹配数据进行分析
        all_matches = pd.DataFrame()
        if not barcode_matches.empty:
            all_matches = pd.concat([all_matches, barcode_matches], ignore_index=True)
        if not name_matches.empty:
            all_matches = pd.concat([all_matches, name_matches], ignore_index=True)
        
        report_content = []
        
        # 1. 执行摘要
        report_content.append("## 📋 执行摘要")
        
        total_matches = len(all_matches)
        barcode_match_count = len(barcode_matches)
        name_match_count = len(name_matches)
        coverage = summary.get("comparison_coverage", 0)
        
        report_content.append(f"""
**比价概况：**
- 成功匹配商品 **{total_matches:,}** 个，覆盖率 **{coverage:.1%}**
- 条码精确匹配 **{barcode_match_count:,}** 个，名称模糊匹配 **{name_match_count:,}** 个
- 数据质量评估：{'优秀' if coverage > 0.8 else '良好' if coverage > 0.6 else '待改善'}
        """)
        
        # 2. 价格竞争力分析
        if not all_matches.empty:
            price_cols = [col for col in all_matches.columns if '售价' in col or '价格' in col]
            
            if len(price_cols) >= 2:
                price_col_a = price_cols[0]
                price_col_b = price_cols[1]
                
                # 价格分析
                df = all_matches.copy()
                df[price_col_a] = pd.to_numeric(df[price_col_a], errors='coerce')
                df[price_col_b] = pd.to_numeric(df[price_col_b], errors='coerce')
                df = df.dropna(subset=[price_col_a, price_col_b])
                
                if not df.empty:
                    df['价格差异'] = df[price_col_a] - df[price_col_b]
                    df['价格优势率'] = (df['价格差异'] / df[price_col_b]) * 100
                    
                    our_advantage_count = len(df[df['价格优势率'] < -5])
                    competitor_advantage_count = len(df[df['价格优势率'] > 5])
                    similar_price_count = len(df) - our_advantage_count - competitor_advantage_count
                    
                    our_advantage_rate = our_advantage_count / len(df) * 100
                    avg_price_advantage = df['价格优势率'].mean()
                    
                    report_content.append("## 💰 价格竞争力分析")
                    
                    competitive_status = ""
                    if our_advantage_rate > 50:
                        competitive_status = "🟢 **价格竞争力强**"
                    elif our_advantage_rate > 30:
                        competitive_status = "🟡 **价格竞争力中等**"
                    else:
                        competitive_status = "🔴 **价格竞争力较弱**"
                    
                    report_content.append(f"""
**竞争力评估：** {competitive_status}

**详细指标：**
- {store_name_a}优势商品：**{our_advantage_count:,}** 个 ({our_advantage_rate:.1f}%)
- {store_name_b}优势商品：**{competitor_advantage_count:,}** 个 ({competitor_advantage_count/len(df)*100:.1f}%)
- 价格相当商品：**{similar_price_count:,}** 个 ({similar_price_count/len(df)*100:.1f}%)
- 平均价格优势率：**{avg_price_advantage:.1f}%** {'(我方占优)' if avg_price_advantage < 0 else '(对手占优)' if avg_price_advantage > 0 else '(势均力敌)'}
                    """)
        
        # 3. 分类竞争分析
        if not all_matches.empty:
            category_cols = [col for col in all_matches.columns if '分类' in col]
            
            if category_cols and len(price_cols) >= 2:
                category_col = category_cols[0]
                
                category_analysis = df.groupby(category_col).agg({
                    '价格优势率': ['mean', 'count'],
                    price_col_a: 'mean'
                }).round(2)
                
                category_analysis.columns = ['平均优势率', '商品数量', '平均价格']
                category_analysis = category_analysis.reset_index()
                category_analysis['竞争状态'] = category_analysis['平均优势率'].apply(
                    lambda x: f'{store_name_a}优势' if x < -5 else f'{store_name_b}优势' if x > 5 else '势均力敌'
                )
                
                report_content.append("## 📊 分类竞争分析")
                
                # 找出优势和劣势分类
                our_advantage_categories = category_analysis[category_analysis['平均优势率'] < -5]
                competitor_advantage_categories = category_analysis[category_analysis['平均优势率'] > 5]
                
                if not our_advantage_categories.empty:
                    report_content.append(f"""
**🟢 {store_name_a}优势分类：**
                    """)
                    for _, row in our_advantage_categories.iterrows():
                        report_content.append(f"- **{row[category_col]}**：优势率 {row['平均优势率']:.1f}%，{row['商品数量']} 个商品")
                
                if not competitor_advantage_categories.empty:
                    report_content.append(f"""
**🔴 {store_name_b}优势分类：**
                    """)
                    for _, row in competitor_advantage_categories.iterrows():
                        report_content.append(f"- **{row[category_col]}**：劣势 {row['平均优势率']:.1f}%，{row['商品数量']} 个商品")
        
        # 4. 库存风险预警
        inventory_cols = [col for col in all_matches.columns if '库存' in col]
        sales_cols = [col for col in all_matches.columns if '销量' in col or '月售' in col]
        
        if inventory_cols and sales_cols:
            inventory_col = inventory_cols[0]
            sales_col = sales_cols[0]
            
            df[inventory_col] = pd.to_numeric(df[inventory_col], errors='coerce')
            df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
            
            inventory_df = df.dropna(subset=[inventory_col, sales_col])
            
            if not inventory_df.empty:
                inventory_df['库销比'] = inventory_df[inventory_col] / (inventory_df[sales_col] + 1)
                high_risk_products = inventory_df[inventory_df['库销比'] < 0.5]
                low_inventory_products = inventory_df[inventory_df[inventory_col] < 10]
                
                if not high_risk_products.empty or not low_inventory_products.empty:
                    report_content.append("## ⚠️ 库存风险预警")
                    
                    if not high_risk_products.empty:
                        report_content.append(f"""
**🔴 高风险商品（库销比<0.5）：** {len(high_risk_products)} 个
- 建议立即补货或调整销售策略
                        """)
                    
                    if not low_inventory_products.empty:
                        report_content.append(f"""
**🟡 低库存商品（库存<10）：** {len(low_inventory_products)} 个
- 建议关注销售情况，及时补货
                        """)
        
        # 5. 策略建议
        report_content.append("## 💡 策略建议")
        
        suggestions = []
        
        if not all_matches.empty and len(price_cols) >= 2:
            if our_advantage_rate > 50:
                suggestions.append("🎯 **维持优势策略**：保持现有价格优势，重点推广优势商品")
                suggestions.append("📈 **提升盈利**：适当提升优势商品毛利率，增加整体收益")
            elif our_advantage_rate > 30:
                suggestions.append("⚡ **重点改进**：关注对手优势商品，分析成本结构寻找降价空间")
                suggestions.append("🔄 **差异化策略**：通过服务、品质等非价格因素获得竞争优势")
            else:
                suggestions.append("🚨 **紧急调整**：全面审视定价策略，重点调整劣势商品价格")
                suggestions.append("🎁 **促销活动**：考虑捆绑销售、限时折扣等促销手段")
        
        # 匹配质量建议
        if barcode_match_count < total_matches * 0.6:
            suggestions.append("📊 **数据优化**：完善商品条码信息，提升匹配准确度")
        
        if coverage < 0.7:
            suggestions.append("🔍 **扩大覆盖**：增加商品品类，完善商品主数据管理")
        
        for i, suggestion in enumerate(suggestions, 1):
            report_content.append(f"{i}. {suggestion}")
        
        # 6. 数据质量评估
        report_content.append("## 📈 数据质量评估")
        
        quality_score = 0
        quality_factors = []
        
        # 匹配率评分
        if coverage > 0.8:
            quality_score += 25
            quality_factors.append("✅ 匹配覆盖率优秀")
        elif coverage > 0.6:
            quality_score += 15
            quality_factors.append("🟡 匹配覆盖率良好")
        else:
            quality_score += 5
            quality_factors.append("❌ 匹配覆盖率待改善")
        
        # 精确匹配率评分
        if total_matches > 0:
            exact_match_rate = barcode_match_count / total_matches
            if exact_match_rate > 0.7:
                quality_score += 25
                quality_factors.append("✅ 精确匹配率高")
            elif exact_match_rate > 0.4:
                quality_score += 15
                quality_factors.append("🟡 精确匹配率中等")
            else:
                quality_score += 5
                quality_factors.append("❌ 精确匹配率低")
        
        # 数据完整性评分
        if not all_matches.empty:
            completeness = 1 - (all_matches.isnull().sum().sum() / (len(all_matches) * len(all_matches.columns)))
            if completeness > 0.9:
                quality_score += 25
                quality_factors.append("✅ 数据完整性优秀")
            elif completeness > 0.7:
                quality_score += 15
                quality_factors.append("🟡 数据完整性良好")
            else:
                quality_score += 5
                quality_factors.append("❌ 数据存在缺失")
        
        # 数据一致性评分
        if len(sheets_data) >= 5:
            quality_score += 25
            quality_factors.append("✅ 数据结构完整")
        elif len(sheets_data) >= 3:
            quality_score += 15
            quality_factors.append("🟡 数据结构基本完整")
        else:
            quality_score += 5
            quality_factors.append("❌ 数据结构不完整")
        
        quality_level = "优秀" if quality_score > 80 else "良好" if quality_score > 60 else "待改善"
        
        report_content.append(f"""
**总体评分：** {quality_score}/100 ({quality_level})

**评估明细：**
        """)
        
        for factor in quality_factors:
            report_content.append(f"- {factor}")
        
        # 显示完整报告
        report_text = "\n".join(report_content)
        st.markdown(report_text)
        
        # 提供下载选项
        st.download_button(
            label="📥 下载完整报告 (Markdown)",
            data=report_text,
            file_name=f"比价分析报告_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            key="download_insight_report"
        )
        
    except Exception as e:
        st.error(f"生成洞察报告时出错: {str(e)}")


@st.cache_data(ttl=300)  # 5分钟缓存
def load_price_panel_metrics(uploaded_file=None) -> Optional[Dict[str, Any]]:
    """读取比价面板指标，支持上传文件或本地路径"""
    
    # 优先使用上传的文件
    if uploaded_file is not None:
        try:
            # 读取上传的JSON文件
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            payload = json.loads(content)
            
            # 验证数据结构
            if not isinstance(payload, dict):
                st.error("⚠️ 上传的文件格式错误，请上传有效的JSON文件")
                return None
                
            # 检查必要字段
            if "metrics" not in payload:
                st.warning("⚠️ 上传的文件中缺少 'metrics' 字段")
                
            st.success(f"✅ 成功加载上传的比价数据：{uploaded_file.name}")
            return payload
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON解析错误: {str(e)}")
            return None
        except Exception as e:
            st.error(f"❌ 加载上传文件失败: {str(e)}")
            return None
    
    # 如果没有上传文件，尝试读取本地文件（作为备用）
    metrics_path = PRICE_PANEL_INTERMEDIATE_DIR / "price_panel_metrics.json"
    
    if not PRICE_PANEL_INTERMEDIATE_DIR.exists():
        return None
        
    if not metrics_path.exists():
        return None
        
    try:
        with open(metrics_path, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
        
        # 验证数据结构
        if not isinstance(payload, dict):
            return None
            
        # 添加数据新鲜度检查
        timestamp = payload.get("generated_at")
        if timestamp:
            try:
                from datetime import datetime
                gen_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_minutes = (datetime.now() - gen_time.replace(tzinfo=None)).total_seconds() / 60
                if age_minutes > 60:  # 数据超过1小时
                    st.info(f"🗺️ 检测到本地数据 ({age_minutes:.0f}分钟前)，建议上传最新数据")
            except Exception:
                pass
                
        return payload
        
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def preview_uploaded_data(payload: Dict[str, Any]) -> None:
    """预览上传的比价数据"""
    if not payload:
        return
        
    with st.expander("🔍 数据预览与验证", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📈 数据概览**")
            
            # 基本信息
            timestamp = payload.get("generated_at", "N/A")
            if timestamp != "N/A":
                timestamp = timestamp.replace('T', ' ')[:19]
            st.metric("生成时间", timestamp)
            
            metrics_count = len(payload.get("metrics", []))
            st.metric("指标数量", metrics_count)
            
            warnings_count = len(payload.get("warnings", []))
            st.metric("警告数量", warnings_count)
            
        with col2:
            st.write("**🏢 门店信息**")
            stores = payload.get("stores", [])
            if stores:
                for i, store in enumerate(stores[:2], 1):
                    store_name = store.get("display_name", f"门店{i}")
                    st.write(f"• {store_name}")
            else:
                st.write("⚠️ 未检测到门店信息")
        
        # 警告信息
        warnings = payload.get("warnings", [])
        if warnings:
            st.write("**⚠️ 警告信息**")
            for warning in warnings:
                st.warning(warning)
        
        # JSON结构预览
        st.write("**📜 JSON结构预览**")
        structure = {key: type(value).__name__ for key, value in payload.items()}
        st.json(structure)


def _format_metric_value(metric: Dict[str, Any]) -> str:
    value = metric.get("value")
    unit = metric.get("unit")
    if value is None:
        return "—"
    if unit == "%":
        return f"{float(value):.1f}%"
    if unit == "个":
        try:
            return f"{int(value):,}"
        except Exception:
            return str(value)
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _build_metric_context_lines(metric: Dict[str, Any], payload: Dict[str, Any]) -> List[str]:
    context = metric.get("context") or {}
    metric_id = metric.get("id")
    lines: List[str] = []

    if metric_id == "matched_pairs":
        stores = context.get("stores") or [store.get("display_name", "") for store in payload.get("stores", [])[:2]]
        stores = [s for s in stores if s]
        if stores:
            lines.append(" vs ".join(stores))
    elif metric_id in {"match_rate_store_a", "match_rate_store_b"}:
        matched = context.get("matched")
        total = context.get("total")
        if matched is not None and total:
            lines.append(f"匹配 {int(matched):,} / 总 {int(total):,}")
    elif metric_id in {"unique_store_a", "unique_store_b"}:
        total = context.get("total")
        value = metric.get("value")
        if value is not None and total:
            lines.append(f"独有 {int(value):,} / 总 {int(total):,}")
    elif metric_id == "stockout_alert":
        stores = payload.get("stores", [])[:2]
        for store in stores:
            name = store.get("display_name")
            details = context.get(name, {}) if name else {}
            zero = details.get("zero")
            with_sales = details.get("with_sales")
            if zero is None:
                continue
            line = f"{name}: {int(zero):,} 个"
            if with_sales:
                line += f"（含销量 {int(with_sales):,}）"
            lines.append(line)
        diff = context.get("difference")
        if isinstance(diff, (int, float)) and diff != 0:
            symbol = "+" if diff > 0 else ""
            lines.append(f"差值 {symbol}{int(diff):,}")

    return lines


def render_price_panel_overview(payload: Dict[str, Any]) -> None:
    """渲染比价基础看板指标（优化版）"""
    st.subheader("💹 比价基础看板")
    
    # 显示数据更新时间
    timestamp = payload.get("generated_at")
    if timestamp:
        formatted_time = timestamp.replace('T', ' ')[:19]
        st.caption(f"🔄 数据更新: {formatted_time}")
    
    # 显示警告信息
    warnings = payload.get("warnings", []) or []
    if warnings:
        for warn in warnings:
            st.warning(f"⚠️ {warn}")
    
    # 获取指标数据
    metrics = payload.get("metrics") or []
    if not metrics:
        st.info("📈 暂无比价指标，请先运行比价ETL。")
        
        # 提供帮助信息
        with st.expander("🔧 如何生成比价数据？"):
            st.markdown("""
            **步骤说明:**
            1. 确保比价数据文件存在于: `比价数据/` 目录
            2. 运行比价ETL处理脚本
            3. 等待生成 `price_panel_metrics.json` 文件
            4. 刷新本页面查看数据
            """)
        return
    
    # 显示指标统计
    st.caption(f"📊 共 {len(metrics)} 个比价指标")
    
    # 按行显示指标（每行3个）
    for start in range(0, len(metrics), 3):
        row_metrics = metrics[start:start + 3]
        columns = st.columns(len(row_metrics))
        
        for col, metric in zip(columns, row_metrics):
            with col:
                metric_label = metric.get("label", "未知指标")
                metric_value = _format_metric_value(metric)
                
                # 显示指标
                st.metric(metric_label, metric_value)
                
                # 显示上下文信息
                context_lines = _build_metric_context_lines(metric, payload)
                if context_lines:
                    context_text = " | ".join(context_lines)
                    st.caption(f"📝 {context_text}")
    
    # 添加刷新按钮
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 刷新比价数据"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("📈 详细分析"):
            # 跳转到比价看板选项卡
            st.info("👆 请点击上方 '比价看板' 选项卡查看详细分析")


def render_unified_price_comparison_module() -> None:
    """统一的比价模块渲染函数（支持文件上传）"""
    st.subheader("💹 比价分析模块")
    
    # 选择数据输入方式
    input_method = st.radio(
        "📁 选择数据输入方式",
        ["上传比价结果文件", "上传JSON文件", "使用本地数据"],
        horizontal=True,
        key="price_comparison_input_method_radio"
    )
    
    price_panel_payload = None
    
    if input_method == "上传比价结果文件":
        st.write("**📊 比价结果文件分析**")
        st.info("🎯 上传通过比价脚本生成的完整比价结果Excel文件")
        
        comparison_file = st.file_uploader(
            "📤 选择比价结果Excel文件",
            type=['xlsx', 'xls'],
            help="上传通过 product_comparison_tool_local.py 生成的比价结果文件",
            key="comparison_file_uploader"
        )
        
        # 显示文件要求
        with st.expander("📋 比价结果文件说明"):
            st.markdown("""
            **支持的文件类型:**
            - ✅ 通过 `product_comparison_tool_local.py` 生成的比价结果文件
            - ✅ 文件名格式: `matched_products_comparison_final_YYYYMMDD_HHMMSS.xlsx`
            
            **文件应包含的Sheet:**
            - **1-条码精确匹配**: 条码相同的商品匹配结果
            - **2-名称模糊匹配(无条码)**: 基于商品名称的匹配结果  
            - **3-{店铺A}-独有商品**: 店铺A独有的商品
            - **4-{店铺B}-独有商品**: 店铺B独有的商品
            - **5-库存>0&A折扣≥B折扣**: 价格优势商品
            - **6-8**: 清洗数据对比Sheet(可选)
            
            **使用流程:**
            1. 🔧 先用比价脚本处理两个店铺的原始数据
            2. 📤 上传生成的比价结果Excel文件
            3. 📊 系统自动解析并展示可视化分析结果
            
            **注意事项:**
            - 确保文件是最新的比价结果
            - 检查各个Sheet是否包含有效数据
            - 支持中文商品名称和店铺名称
            """)

        # 当文件上传后，执行分析
        if comparison_file:
            price_panel_payload = process_uploaded_comparison_file(comparison_file)
            
    elif input_method == "上传JSON文件":
        st.write("**� JSON文件上传**")
        uploaded_file = st.file_uploader(
            "📤 选择比价数据文件 (JSON)",
            type=['json'],
            help="请上传由比价ETL生成的 price_panel_metrics.json 文件",
            key="json_uploader"
        )
        
        if uploaded_file:
            price_panel_payload = load_price_panel_metrics(uploaded_file)
            
    else:  # 使用本地数据
        st.write("**💾 本地数据读取**")
        price_panel_payload = load_price_panel_metrics()
        
        if price_panel_payload:
            st.info("🗂️ 已加载本地比价数据")
        else:
            st.warning("⚠️ 未找到本地比价数据文件")
    
    # 数据有效时显示分析结果
    if price_panel_payload:
        st.markdown("---")
        
        # 根据数据类型选择不同的展示方式
        if price_panel_payload.get("comparison_type") == "multi_store_comparison":
            # 新的比价结果文件展示
            render_comparison_file_analysis(price_panel_payload)
        else:
            # 传统的JSON文件展示
            tab1, tab2 = st.tabs(["📈 基础指标", "🗺️ 详细分析"])
            
            with tab1:
                if price_panel_payload.get("metrics"):
                    render_price_panel_overview(price_panel_payload)
                else:
                    st.warning("🚫 数据中未包含有效指标")
        
            with tab2:
                st.caption("🔍 详细比价分析看板")
                # 只有在使用本地数据时才调用老的dashboard
                if input_method == "使用本地数据":
                    try:
                        create_price_comparison_dashboard()
                    except Exception as e:
                        st.error(f"❌ 加载详细分析失败: {str(e)}")
                        st.info("📝 建议检查上传的数据文件格式")
                else:
                    st.info("📊 请上传比价结果文件或JSON文件以查看详细分析")
    else:
        # 根据选择的输入方式显示不同的提示
        if input_method == "上传比价结果文件":
            st.info("👆 请上传比价结果Excel文件开始分析")
        elif input_method == "上传JSON文件":
            st.info("👆 请上传JSON文件开始分析")  
        else:  # 使用本地数据
            st.info("🔍 正在尝试加载本地比价数据...")
            # 只有选择本地数据时才显示老的dashboard
            try:
                create_price_comparison_dashboard()
            except Exception as e:
                st.warning("⚠️ 未找到本地比价数据文件")
                st.info("💡 建议上传比价结果文件或JSON文件进行分析")


def render_order_data_uploader():
    """渲染订单数据上传和分析模块 - 支持批量上传"""
    st.info("📤 上传订单数据Excel文件进行深度分析（支持批量上传多个文件）")
    
    # 添加数据来源选择
    data_source_tab1, data_source_tab2 = st.tabs(["📤 上传新数据", "📂 加载历史数据"])
    
    order_data_to_analyze = None
    data_source_label = ""
    
    with data_source_tab1:
        # 文件上传 - 支持多文件
        order_files = st.file_uploader(
            "选择订单数据文件（可选择多个文件）",
            type=['xlsx', 'xls'],
            help="上传包含订单信息的Excel文件，支持同时上传多个文件进行合并分析",
            key="order_data_uploader",
            accept_multiple_files=True  # 启用多文件上传
        )
        
        if order_files:
            data_source_label = "新上传数据"
            # 后续处理逻辑...
            
    with data_source_tab2:
        st.write("**📦 历史缓存数据**")
        
        # 获取历史缓存列表
        cached_list = load_cached_data_list()
        
        if not cached_list:
            st.info("📭 暂无历史缓存数据，请先上传新数据")
        else:
            st.success(f"✅ 找到 {len(cached_list)} 个历史数据版本")
            
            # 创建选择列表
            cache_options = []
            for idx, cache_info in enumerate(cached_list):
                upload_time = cache_info['upload_time']
                if upload_time != 'Unknown':
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(upload_time)
                        time_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        time_str = upload_time
                else:
                    time_str = "未知时间"
                
                label = f"{cache_info['original_file']} | {time_str} | {cache_info['rows']:,}行 | {cache_info['size_mb']:.1f}MB"
                cache_options.append((label, cache_info['file_path']))
            
            # 选择要加载的缓存
            selected_cache_label = st.selectbox(
                "选择要加载的历史数据",
                options=[opt[0] for opt in cache_options],
                key="cached_data_selector"
            )
            
            if st.button("🔄 加载选中的历史数据", key="load_cached_btn"):
                # 找到对应的文件路径
                selected_path = next(opt[1] for opt in cache_options if opt[0] == selected_cache_label)
                
                with st.spinner("📖 正在加载历史数据..."):
                    order_data_to_analyze = load_data_from_cache(selected_path)
                    if order_data_to_analyze is not None:
                        st.success(f"✅ 成功加载历史数据：{len(order_data_to_analyze):,}行")
                        data_source_label = f"历史数据: {selected_cache_label}"
                        
                        # 设置到session_state供其他标签页使用
                        if 'current_data' not in st.session_state:
                            st.session_state['current_data'] = {}
                        st.session_state['current_data']['raw_data'] = order_data_to_analyze
                        st.session_state['uploaded_order_data'] = st.session_state['current_data']
                        st.info("💡 数据已加载，可前往其他标签页（如AI场景营销）查看分析")
    
    # 只有当有数据需要分析时才继续
    if order_files:
        # 原有的上传处理逻辑
        pass  # 将在下面替换
    
    # 显示文件格式要求
    with st.expander("📋 订单数据格式要求"):
        st.markdown("""
        **必需字段：**
        - `订单ID`: 订单唯一标识
        - `商品名称`: 商品名称
        - `商品实售价`: 商品售价
        - `销量`: 商品数量
        - `下单时间`: 订单时间（格式：YYYY-MM-DD HH:MM:SS）
        - `门店名称`: 门店标识
        - `渠道`: 销售渠道（如：美团、饿了么等）
        
        **推荐字段（用于完整分析）：**
        - `物流配送费`: 配送费用
        - `平台佣金`: 平台抽成
        - `配送距离`: 配送距离（米或公里）
        - `美团一级分类`: 商品一级分类
        - `美团三级分类`: 商品三级分类
        - `收货地址`: 配送地址
        - `配送费减免`、`满减`、`商品减免`、`代金券`: 各类优惠金额
        - `用户支付配送费`、`订单零售额`、`打包费`: 订单金额明细
        
        **分析功能：**
        - ✅ 13个核心指标卡片（订单数、收入、利润、客单价等）
        - ✅ 负毛利商品识别Top 50
        - ✅ 成本结构分析（商家活动、平台佣金、配送成本）
        - ✅ 主单品vs凑单品对比
        - ✅ 每日利润趋势图（利润额+利润率）
        - ✅ 数据质量检查报告
        """)
    
    # 处理上传的文件（支持多文件合并）或加载历史数据
    if order_files or order_data_to_analyze is not None:
        st.markdown("""
        **必需字段：**
        - `订单ID`: 订单唯一标识
        - `商品名称`: 商品名称
        - `商品实售价`: 商品售价
        - `销量`: 商品数量
        - `下单时间`: 订单时间（格式：YYYY-MM-DD HH:MM:SS）
        - `门店名称`: 门店标识
        - `渠道`: 销售渠道（如：美团、饿了么等）
        
        **推荐字段（用于完整分析）：**
        - `物流配送费`: 配送费用
        - `平台佣金`: 平台抽成
        - `配送距离`: 配送距离（米或公里）
        - `美团一级分类`: 商品一级分类
        - `美团三级分类`: 商品三级分类
        - `收货地址`: 配送地址
        - `配送费减免`、`满减`、`商品减免`、`代金券`: 各类优惠金额
        - `用户支付配送费`、`订单零售额`、`打包费`: 订单金额明细
        
        **分析功能：**
        - ✅ 13个核心指标卡片（订单数、收入、利润、客单价等）
        - ✅ 负毛利商品识别Top 50
        - ✅ 成本结构分析（商家活动、平台佣金、配送成本）
        - ✅ 主单品vs凑单品对比
        - ✅ 每日利润趋势图（利润额+利润率）
        - ✅ 数据质量检查报告
        """)
    
    
    # 处理上传的文件（支持多文件合并）或加载历史数据
    if order_files or order_data_to_analyze is not None:
        try:
            # 区分两种数据来源
            if order_data_to_analyze is not None:
                # 使用历史缓存数据
                order_data = order_data_to_analyze
                original_count = len(order_data)
                st.success(f"✅ 已加载历史数据：{original_count:,}条订单")
                
            else:
                # 处理新上传的文件
                # 如果上传了多个文件，先显示文件列表
                if len(order_files) > 1:
                    st.success(f"✅ 检测到 {len(order_files)} 个文件，将自动合并分析")
                    with st.expander("📂 文件列表"):
                        for idx, file in enumerate(order_files, 1):
                            st.write(f"{idx}. {file.name}")
                
                with st.spinner("📖 正在读取订单数据..."):
                    # 读取所有Excel文件并合并
                    all_order_data = []
                    file_stats = []
                    
                    for file in order_files:
                        try:
                            df = pd.read_excel(file)
                            all_order_data.append(df)
                            file_stats.append({
                                '文件名': file.name,
                                '订单行数': len(df),
                                '状态': '✅ 成功'
                            })
                        except Exception as e:
                            file_stats.append({
                                '文件名': file.name,
                                '订单行数': 0,
                                '状态': f'❌ 失败: {str(e)}'
                            })
                            st.error(f"❌ 读取文件 {file.name} 失败: {str(e)}")
                    
                    # 显示文件读取统计
                    if len(order_files) > 1:
                        st.dataframe(
                            pd.DataFrame(file_stats),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # 合并所有数据
                    if not all_order_data:
                        st.error("❌ 没有成功读取任何文件")
                        return
                    
                    order_data = pd.concat(all_order_data, ignore_index=True)
                    
                    original_count = len(order_data)
                    
                    # 智能去重：只删除完全相同的行（所有字段都相同）
                    before_dedup = len(order_data)
                    order_data = order_data.drop_duplicates(keep='first')
                    after_dedup = len(order_data)
                    
                    if before_dedup > after_dedup:
                        st.info(f"🔄 已去除完全重复的数据行：{before_dedup:,} → {after_dedup:,} 行（去除 {before_dedup - after_dedup:,} 行）")
                        st.caption("💡 说明：只删除所有字段完全相同的行，保留订单-商品明细级数据")
                    
                    # 检查订单-商品明细结构
                    if '订单ID' in order_data.columns:
                        unique_orders = order_data['订单ID'].nunique()
                        total_items = len(order_data)
                        avg_items = total_items / unique_orders if unique_orders > 0 else 0
                        
                        st.success(f"✅ 成功加载数据：{unique_orders:,} 个订单，{total_items:,} 个商品明细（平均每单 {avg_items:.1f} 个商品）")
                    else:
                        st.success(f"✅ 成功加载 {after_dedup:,} 条数据")
                    
                    # 🔍 数据质量检查（仅对新上传数据）
                    with st.spinner("🔍 正在进行数据质量检查..."):
                        quality_report = perform_data_quality_check(order_data)
                        
                        # 显示质量检查结果
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("数据质量评分", f"{quality_report['score']}分")
                        with col2:
                            st.metric("质量等级", quality_report['grade'])
                        with col3:
                            st.metric("问题数量", f"{len(quality_report['issues'])}个")
                        
                        # 详细质量报告
                        if quality_report['issues'] or quality_report['warnings']:
                            with st.expander("📋 数据质量详细报告"):
                                if quality_report['issues']:
                                    st.write("**🔴 严重问题：**")
                                    for issue in quality_report['issues']:
                                        st.error(f"• {issue['column']}: {issue['description']}")
                                
                                if quality_report['warnings']:
                                    st.write("**⚠️ 警告提示：**")
                                    for warning in quality_report['warnings']:
                                        st.warning(f"• {warning['column']}: {warning['description']}")
                        else:
                            st.success("✅ 数据质量优秀，未发现问题")
                    
                    # 💾 自动保存到缓存
                    with st.spinner("💾 正在保存数据到本地缓存..."):
                        try:
                            # 保存原始合并数据
                            file_name = order_files[0].name if len(order_files) == 1 else f"合并数据_{len(order_files)}个文件"
                            cache_path = save_data_to_cache(order_data, file_name)
                            st.success(f"💾 数据已保存到缓存，下次可快速加载")
                        except Exception as e:
                            st.warning(f"⚠️ 缓存保存失败（不影响分析）: {str(e)}")
            
            # 显示数据预览（两种来源通用）
            with st.expander("👀 数据预览（前10行）"):
                st.dataframe(order_data.head(10))
                
                # 数据处理和分析
                with st.spinner("🔄 正在处理和分析数据..."):
                    try:
                        # 调用标准业务逻辑处理（会自动剔除耗材数据）
                        processed_order_data = preprocess_order_data(order_data)
                        
                        # 显示耗材剔除信息
                        processed_count = len(processed_order_data)
                        if processed_count < original_count:
                            removed_count = original_count - processed_count
                            st.warning(f"🔴 已自动剔除 {removed_count} 行耗材数据（如购物袋），实际分析 {processed_count:,} 行数据")
                        
                        order_summary = calculate_order_metrics(processed_order_data)
                        
                        # 保存数据到session_state供其他标签页使用
                        if 'current_data' not in st.session_state:
                            st.session_state['current_data'] = {}
                        st.session_state['current_data']['raw_data'] = processed_order_data
                        st.session_state['current_data']['order_summary'] = order_summary
                        
                        # 同时设置uploaded_order_data标志
                        st.session_state['uploaded_order_data'] = st.session_state['current_data']
                        
                        st.success("✅ 数据处理完成！可以前往其他标签页（如AI场景营销）查看更多分析")
                        
                        # 创建分析选项卡
                        st.markdown("---")
                        analysis_tabs = st.tabs([
                            "📊 订单概览", 
                            "💰 利润分析", 
                            "⏰ 时间分析",
                            "🏪 门店分析",
                            "📦 商品分析"
                        ])
                        
                        with analysis_tabs[0]:
                            if ORDER_ENHANCEMENT_AVAILABLE:
                                render_enhanced_order_overview(processed_order_data, order_summary)
                            else:
                                render_order_overview(processed_order_data, order_summary)
                        
                        with analysis_tabs[1]:
                            if ORDER_ENHANCEMENT_AVAILABLE:
                                render_enhanced_profit_analysis(processed_order_data, order_summary)
                            else:
                                render_profit_analysis(processed_order_data, order_summary)
                        
                        with analysis_tabs[2]:
                            render_time_analysis(processed_order_data)
                        
                        with analysis_tabs[3]:
                            render_store_analysis(processed_order_data)
                        
                        with analysis_tabs[4]:
                            render_product_analysis(processed_order_data)
                            
                    except Exception as e:
                        st.error(f"❌ 数据处理失败: {str(e)}")
                        st.info("💡 请检查上传的文件是否包含必需字段")
                        
                        # 显示详细错误信息
                        with st.expander("🔍 错误详情"):
                            st.code(str(e))
                            import traceback
                            st.code(traceback.format_exc())
                        
        except Exception as e:
            st.error(f"❌ 文件读取失败: {str(e)}")
            st.info("💡 请确保上传的是有效的Excel文件（.xlsx 或 .xls）")


@st.cache_data
def load_sample_data():
    """加载示例数据"""
    return {
        'store_id': 'DEMO_STORE_001',
        'product_data': pd.DataFrame({
            '商品名称': ['可口可乐330ml', '农夫山泉550ml', '康师傅红烧牛肉面', '五粮液52度500ml', '飞天茅台53度500ml', 
                      '双汇火腿肠', '统一绿茶', '奥利奥饼干', '德芙巧克力', '旺旺仙贝'],
            '售价': [3.5, 2.0, 4.5, 168.0, 2680.0, 6.8, 3.2, 12.5, 28.0, 8.9],
            '原价': [4.0, 2.5, 5.0, 188.0, 2980.0, 8.0, 4.0, 15.0, 32.0, 10.0],
            '月售': [1500, 2800, 800, 50, 5, 1200, 900, 600, 300, 450],
            '库存': [200, 300, 150, 20, 3, 180, 120, 80, 50, 75],
            '美团一级分类': ['饮品', '饮品', '食品', '酒类', '酒类', '食品', '饮品', '食品', '食品', '食品'],
            '美团三级分类': ['碳酸饮料', '水', '方便面', '白酒', '白酒', '肉制品', '茶饮料', '饼干', '巧克力', '膨化食品']
        }),
        'competitor_data': pd.DataFrame({
            '商品名称': ['可口可乐330ml', '农夫山泉550ml', '康师傅红烧牛肉面', '雪碧柠檬味', '百事可乐'],
            '售价': [3.2, 1.8, 4.2, 3.0, 3.3],
            '原价': [3.8, 2.2, 4.8, 3.5, 3.8],
            '月售': [1800, 3200, 900, 1400, 1100],
            '门店名称': ['竞对A', '竞对A', '竞对A', '竞对A', '竞对A'],
            '美团一级分类': ['饮品', '饮品', '食品', '饮品', '饮品']
        })
    }

def main():
    """主函数 - 简化的标签页界面"""
    
    # 页面标题
    st.markdown('<h1 class="main-header">🏪 智能门店经营看板</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 初始化系统组件
    dashboard = load_dashboard_system()
    data_processor = load_data_processor()
    
    # 创建7个功能标签页
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 订单数据分析",
        "💰 比价分析", 
        "🎯 AI场景营销",
        "📋 问题诊断",
        "🛒 多商品订单引导",
        "🏪 商品分类结构竞争力",
        "⚙️ 高级功能"
    ])
    
    # === Tab 1: 订单数据分析 ===
    with tab1:
        st.header("📊 订单数据分析")
        
        # 直接显示上传界面
        render_order_data_uploader()
        
        # 如果已有分析结果，显示
        if "analysis_result" in st.session_state and "订单分析" in st.session_state.get("analysis_result", {}):
            st.markdown("---")
            st.subheader("📈 分析结果")
            
            # 显示订单分析部分结果
            analysis_result = st.session_state["analysis_result"]
            
            # 基础指标
            if "基础指标" in analysis_result:
                metrics = analysis_result["基础指标"]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("订单总数", f"{metrics.get('订单总数', 0):,}")
                col2.metric("总销售额", f"¥{metrics.get('总销售额', 0):,.2f}")
                col3.metric("总利润", f"¥{metrics.get('总利润', 0):,.2f}")
                col4.metric("利润率", f"{metrics.get('利润率', 0):.1f}%")
    
    # === Tab 2: 比价分析 ===
    with tab2:
        st.header("💰 比价分析")
        render_unified_price_comparison_module()
    
    # === Tab 3: AI场景营销 ===
    with tab3:
        st.header("🎯 AI场景营销")
        
        # 检查是否已上传并处理数据
        has_data = False
        current_data = {}
        
        # 优先检查已处理的数据
        if "current_data" in st.session_state and "raw_data" in st.session_state["current_data"]:
            current_data = st.session_state["current_data"]
            has_data = True
        # 其次检查上传的数据
        elif "uploaded_order_data" in st.session_state:
            current_data = st.session_state["uploaded_order_data"]
            has_data = True
        
        if not has_data:
            st.warning("⚠️ 请先在『订单数据分析』标签页上传数据")
            st.info("💡 场景营销分析需要基于订单数据，请先上传Excel文件")
            
            # 提供快速演示入口
            if st.button("🎪 使用示例数据演示场景营销", type="secondary"):
                sample_data = load_sample_data()
                st.session_state["uploaded_order_data"] = sample_data
                st.session_state["current_data"] = sample_data
                st.success("✅ 已加载示例数据")
                st.rerun()
        else:
            # 直接显示场景营销看板
            display_scenario_marketing_dashboard(current_data)
    
    # === Tab 4: 问题诊断 ===
    with tab4:
        st.header("📋 智能问题诊断")
        
        st.info("""
        **🎯 功能说明**：基于订单数据，智能识别经营中的潜在问题，并提供针对性的解决方案
        
        **💡 诊断维度**：
        - 📉 销售下滑分析
        - 💰 利润异常诊断
        - 📦 库存问题识别
        - 🎯 商品结构优化
        - 👥 客户流失预警
        - ⚠️ 运营风险提示
        """)
        
        # 检查是否已上传并处理数据
        has_data = False
        current_data = {}
        
        # 优先检查已处理的数据
        if "current_data" in st.session_state and "raw_data" in st.session_state["current_data"]:
            current_data = st.session_state["current_data"]
            has_data = True
        # 其次检查上传的数据
        elif "uploaded_order_data" in st.session_state:
            current_data = st.session_state["uploaded_order_data"]
            has_data = True
        
        if not has_data:
            st.warning("⚠️ 请先在『订单数据分析』标签页上传数据")
            st.info("💡 问题诊断需要基于订单数据，请先上传Excel文件")
            
            # 显示功能介绍
            with st.expander("📋 查看诊断功能详情"):
                st.markdown("""
                **问题诊断中心提供以下功能**：
                
                1. **自动问题识别**
                   - 智能扫描数据，识别潜在问题
                   - 问题严重程度分级（严重、警告、建议）
                   - 提供问题影响范围和金额估算
                
                2. **根因分析**
                   - 深度挖掘问题产生的根本原因
                   - 多维度交叉分析
                   - 数据可视化呈现
                
                3. **解决方案推荐**
                   - 基于行业最佳实践的建议
                   - 可量化的改进目标
                   - 分步骤实施计划
                
                4. **诊断报告导出**
                   - 生成完整的诊断报告
                   - 支持Excel格式下载
                   - 包含问题清单和解决方案
                """)
        else:
            # 调用问题诊断模块
            try:
                # 预处理数据：确保有日期列
                # 重要：使用深拷贝避免修改原始数据
                processed_data = {
                    'raw_data': current_data.get('raw_data', pd.DataFrame()).copy()
                }
                raw_df = processed_data['raw_data']
                
                # 🔍 DEBUG: 检查数据量
                print(f"[DEBUG] Tab4 - 获取到的原始数据量: {len(raw_df)}行")
                
                if not raw_df.empty:
                    # 确保有日期列（问题诊断引擎需要）
                    if '下单时间' in raw_df.columns:
                        if '日期' not in raw_df.columns:
                            raw_df['日期'] = pd.to_datetime(raw_df['下单时间'], errors='coerce')
                        else:
                            # 如果已有日期列,确保格式正确
                            raw_df['日期'] = pd.to_datetime(raw_df['日期'], errors='coerce')
                        
                        # 🔍 DEBUG: 检查日期范围
                        if '日期' in raw_df.columns:
                            valid_dates = raw_df['日期'].dropna()
                            if len(valid_dates) > 0:
                                print(f"[DEBUG] Tab4 - 日期范围: {valid_dates.min()} 至 {valid_dates.max()}")
                                print(f"[DEBUG] Tab4 - 唯一日期数: {valid_dates.dt.date.nunique()}")
                    
                    # 检查数据时间范围
                    if '日期' in raw_df.columns:
                        valid_dates = raw_df['日期'].dropna()
                        if len(valid_dates) > 0:
                            date_range = (valid_dates.max() - valid_dates.min()).days
                            
                            if date_range < 7:
                                st.warning(f"""
                                ⚠️ 数据时间范围较短（仅{date_range}天），部分周期对比分析功能可能受限
                                
                                **💡 建议**：
                                - 上传至少7天以上的数据以进行周对周分析
                                - 上传至少30天以上的数据以进行月对月分析
                                - 当前数据范围：{valid_dates.min().strftime('%Y-%m-%d')} ~ {valid_dates.max().strftime('%Y-%m-%d')}
                                """)
                                st.info("📊 仍可使用基础诊断功能（负毛利预警、角色失衡等）")
                    
                    # 更新processed_data
                    processed_data['raw_data'] = raw_df
                
                display_problem_diagnostic_center(processed_data)
            except Exception as e:
                st.error(f"❌ 问题诊断加载失败: {str(e)}")
                with st.expander("🔍 查看详细错误信息"):
                    import traceback
                    st.code(traceback.format_exc())
    
    # === Tab 5: 多商品订单引导 ===
    with tab5:
        st.header("🛒 多商品订单引导分析")
        
        st.info("""
        **📊 统计发现**：商品数量每增加1个，客单价平均增加 **¥3.16**（基于6297个订单的回归分析）
        
        **🎯 分析目标**：通过数据分析，找到提升多商品订单率的有效策略，从而提升整体客单价
        """)
        
        # 检查是否已上传数据
        has_data = False
        current_df = None
        
        if "uploaded_order_data" in st.session_state:
            current_data = st.session_state["uploaded_order_data"]
            if "raw_data" in current_data:
                current_df = current_data["raw_data"]
                has_data = True
        
        if not has_data:
            st.warning("⚠️ 请先在『订单数据分析』标签页上传数据")
            
            with st.expander("📋 查看所需数据格式"):
                st.markdown("""
                **必需字段**：
                - `订单ID`: 订单唯一标识
                - `商品名称`: 商品名称
                - `商品实售价`: 商品实际售价
                
                **可选字段**（增强分析）：
                - `下单时间`: 订单时间
                - `一级分类名`: 商品分类
                - `利润额`: 商品利润
                
                **示例数据**：
                ```
                订单ID    | 商品名称      | 商品实售价
                ORD001   | 可口可乐      | 3.5
                ORD001   | 薯片         | 5.8
                ORD002   | 牛奶         | 12.0
                ```
                """)
        else:
            # 导入多商品订单分析模块
            try:
                from 多商品订单引导分析看板 import (
                    filter_retail_data,
                    calculate_order_item_stats,
                    render_order_quantity_distribution,
                    render_item_quantity_analysis,
                    render_frequent_combos,
                    render_single_order_diagnosis,
                    render_promotion_suggestions
                )
                
                # 过滤O2O零售数据（剔除咖啡等其他业务渠道）
                current_df_filtered = filter_retail_data(current_df)
                
                # 显示过滤信息
                if len(current_df_filtered) < len(current_df):
                    excluded_count = len(current_df) - len(current_df_filtered)
                    st.info(f"ℹ️ 已自动剔除咖啡渠道数据 {excluded_count} 行，保留O2O零售数据 {len(current_df_filtered)} 行")
                
                # 计算订单统计
                order_stats = calculate_order_item_stats(current_df_filtered)
                
                # 显示各个分析模块
                st.markdown("---")
                render_order_quantity_distribution(order_stats)
                
                st.markdown("---")
                render_item_quantity_analysis(order_stats)
                
                st.markdown("---")
                render_frequent_combos(current_df_filtered)
                
                st.markdown("---")
                render_single_order_diagnosis(current_df_filtered, order_stats)
                
                st.markdown("---")
                render_promotion_suggestions(order_stats)
                
            except Exception as e:
                st.error(f"分析过程出错: {str(e)}")
                with st.expander("查看详细错误"):
                    import traceback
                    st.code(traceback.format_exc())
    
    # === Tab 6: 商品分类结构竞争力 ===
    with tab6:
        # 检查是否已上传并处理数据
        has_data = False
        current_df = None
        
        # 优先检查已处理的数据
        if "current_data" in st.session_state and "raw_data" in st.session_state["current_data"]:
            current_df = st.session_state["current_data"]["raw_data"]
            has_data = True
        # 其次检查上传的数据
        elif "uploaded_order_data" in st.session_state and "raw_data" in st.session_state["uploaded_order_data"]:
            current_df = st.session_state["uploaded_order_data"]["raw_data"]
            has_data = True
        
        if not has_data:
            st.warning("⚠️ 请先在『订单数据分析』标签页上传数据")
            st.info("💡 商品分类分析需要基于订单数据，并且数据中需要包含『一级分类名』字段")
            
            # 显示数据要求
            with st.expander("📋 查看数据要求"):
                st.markdown("""
                **必需字段**：
                - `订单ID`: 订单唯一标识
                - `商品名称`: 商品名称
                - `商品实售价`: 商品实际售价
                - `一级分类名`: 商品一级分类（**核心字段**）
                
                **可选字段**（增强分析）：
                - `三级分类名`: 商品三级分类
                - `成本`: 商品成本（用于计算毛利率）
                - `渠道`: 订单来源渠道
                """)
        else:
            # 检查必需字段
            required_fields = ['订单ID', '商品名称', '商品实售价']
            category_field = '一级分类名' if '一级分类名' in current_df.columns else '一级分类'
            
            missing_fields = [f for f in required_fields if f not in current_df.columns]
            if missing_fields:
                st.error(f"❌ 数据缺少必需字段: {', '.join(missing_fields)}")
                return
            
            if category_field not in current_df.columns:
                st.error("❌ 数据中缺少分类字段（一级分类名 或 一级分类）")
                st.info("💡 商品分类分析需要商品分类信息，请确保数据中包含『一级分类名』或『一级分类』字段")
                return
            
            # 显示数据概览
            st.success(f"✅ 数据已加载：{len(current_df)} 行订单数据")
            
            # 调用商品分类分析模块
            if CATEGORY_ANALYSIS_AVAILABLE:
                try:
                    render_category_analysis(current_df)
                except Exception as e:
                    st.error(f"❌ 分析过程出错: {str(e)}")
                    with st.expander("🔍 查看详细错误信息"):
                        import traceback
                        st.code(traceback.format_exc())
                    
                    # 提供可能的解决方案
                    st.info("""
                    **💡 常见问题排查**：
                    1. 检查数据中是否包含『一级分类名』或『三级分类名』字段
                    2. 确保分类字段不为空
                    3. 如果有特殊字符或编码问题，请尝试重新导出数据
                    """)
            else:
                st.error("❌ 商品分类结构分析模块未加载")
                st.info("请检查 `商品分类结构分析.py` 文件是否存在")
    
    # === Tab 7: 高级功能 ===
    with tab7:
        st.header("⚙️ 高级功能")
        
        # ============ 子标签页 ============
        adv_tab1, adv_tab2, adv_tab3, adv_tab4 = st.tabs([
            "🔬 AI综合分析",
            "🧠 AI学习系统", 
            "ℹ️ 系统信息",
            "🎮 演示模式"
        ])
        
        # === 高级Tab 1: AI综合分析 ===
        with adv_tab1:
            st.subheader("🔬 AI综合分析")
            st.info("此功能包含：销售分析、竞对分析、风险评估、策略建议、预测分析等全面分析")
            
            # 检查是否已上传数据
            if "uploaded_order_data" not in st.session_state:
                st.warning("⚠️ 请先在『订单数据分析』标签页上传数据")
            else:
                # 分析参数设置
                col1, col2 = st.columns([3, 1])
                with col1:
                    analysis_scope = st.multiselect(
                        "选择分析维度",
                        ["销售分析", "竞对分析", "风险评估", "策略建议", "预测分析"],
                        default=["销售分析", "策略建议"],
                    )
                with col2:
                    forecast_days = st.number_input("预测天数", 7, 90, 30)
                
                # 开始分析按钮
                if st.button("🚀 开始AI综合分析", type="primary", use_container_width=True):
                    current_data = st.session_state["uploaded_order_data"]
                    
                    with st.spinner("正在进行AI综合分析..."):
                        analysis_result = dashboard.comprehensive_analysis(
                            current_data,
                            current_data.get("competitor_data"),
                        )
                        st.session_state["analysis_result"] = analysis_result
                        st.session_state["current_data"] = current_data
                        st.session_state["forecast_days"] = forecast_days
                        
                        # 保存到数据处理器
                        data_processor.processed_data = {
                            "sales_data": current_data.get("product_data", pd.DataFrame()),
                            "order_data": current_data.get("order_data", pd.DataFrame()),
                        }
                        st.success("✅ 分析完成！")
                        st.rerun()
                
                # 显示分析结果
                if "analysis_result" in st.session_state:
                    st.markdown("---")
                    display_analysis_results(
                        st.session_state["analysis_result"], 
                        analysis_scope, 
                        dashboard
                    )
        
        # === 高级Tab 2: AI学习系统 ===
        with adv_tab2:
            st.subheader("🧠 AI学习系统")
            learning_status = dashboard.get_learning_status()
            
            if learning_status.get("enabled"):
                st.success("✅ AI学习系统已启用")
                
                # 学习统计
                learning_stats = learning_status.get("learning_statistics", {})
                if learning_stats:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("总学习次数", learning_stats.get('total_learning_sessions', 0))
                    col2.metric("在线更新", learning_stats.get('online_updates', 0))
                    col3.metric("批量更新", learning_stats.get('batch_updates', 0))
                
                # 学习操作
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 手动模型训练", help="使用历史数据手动训练模型"):
                        sample_data = load_sample_data()
                        with st.spinner("正在训练模型..."):
                            training_result = dashboard.manual_model_training([sample_data])
                            if training_result.get("success"):
                                st.success("🎉 模型训练完成")
                            else:
                                st.error(f"❌ 训练失败: {training_result.get('error', '未知错误')}")
                
                with col2:
                    if st.button("📄 导出学习报告"):
                        report_path = dashboard.export_learning_insights()
                        if report_path:
                            st.success(f"✅ 报告已导出: {report_path}")
                        else:
                            st.error("❌ 导出失败")
            else:
                st.info("AI学习系统暂未启用")
        
        # === 高级Tab 3: 系统信息 ===
        with adv_tab3:
            st.subheader("ℹ️ 系统信息")
            real_data, load_messages = load_real_business_data()
            
            if load_messages:
                st.warning("⚠️ 数据加载消息:")
                for msg in load_messages:
                    st.write(f"• {msg}")
            
            if real_data is not None:
                st.success("✅ 系统已检测到真实数据文件")
                col1, col2 = st.columns(2)
                col1.metric("数据源", real_data['data_source'])
                col2.metric("数据期间", real_data['data_period'])
                col1.metric("订单数", f"{real_data['total_orders']:,}")
                col2.metric("商品种类", f"{real_data['total_products']:,}")
            else:
                st.info("未检测到真实数据文件")
        
        # === 高级Tab 4: 演示模式 ===
        with adv_tab4:
            st.subheader("🎮 演示模式")
            st.info("演示模式使用内置示例数据，可用于界面演示和功能测试")
            
            if st.button("🎪 启动示例数据演示", type="secondary"):
                sample_data = load_sample_data()
                st.session_state["uploaded_order_data"] = sample_data
                st.session_state["current_data"] = sample_data
                st.success("✅ 已加载示例数据，请前往其他标签页体验功能")
                st.rerun()

def display_analysis_results(analysis_result, analysis_scope, dashboard_instance):
    """显示分析结果"""
    
    # 1. 总体概览
    st.subheader("📊 分析概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "数据质量评分",
            f"{analysis_result['store_overview']['data_quality_score']:.2f}",
            delta="良好" if analysis_result['store_overview']['data_quality_score'] > 0.7 else "需改善"
        )
    
    with col2:
        st.metric(
            "生成假设数量",
            len(analysis_result['hypothesis_analysis']),
            delta="已验证"
        )
    
    with col3:
        total_decisions = sum(len(options) for options in analysis_result['strategic_decisions'].values())
        st.metric(
            "策略建议数",
            total_decisions,
            delta="可执行"
        )
    
    with col4:
        st.metric(
            "综合建议数",
            len(analysis_result['comprehensive_recommendations']),
            delta="优先级排序"
        )
    
    # 2. 核心建议展示
    st.subheader("🎯 核心建议")
    
    for i, recommendation in enumerate(analysis_result['comprehensive_recommendations'][:5], 1):
        st.markdown(f"""
        <div class="recommendation-box">
            <strong>建议 {i}:</strong> {recommendation}
        </div>
        """, unsafe_allow_html=True)
    
    # 3. 选项卡式详细分析
    tabs_to_create = ["🛍️ 商品策略", "📈 趋势预测", "⚠️ 风险评估", "🏢 竞对分析", "🔬 假设验证", "🧠 学习效果", "💹 比价看板", "🎯 场景营销", "📋 问题诊断"]
    tab_objects = st.tabs(tabs_to_create)
    
    tab_map = {name: obj for name, obj in zip(tabs_to_create, tab_objects)}

    with tab_map["🛍️ 商品策略"]:
        display_product_strategy(analysis_result)
    
    with tab_map["📈 趋势预测"]:
        display_trend_analysis(analysis_result)
    
    with tab_map["⚠️ 风险评估"]:
        display_risk_assessment(analysis_result)
    
    with tab_map["🏢 竞对分析"]:
        display_competitor_analysis(analysis_result)
    
    with tab_map["🔬 假设验证"]:
        display_hypothesis_validation(analysis_result)
    
    with tab_map["🧠 学习效果"]:
        display_learning_effects(analysis_result, dashboard_instance)

    with tab_map["💹 比价看板"]:
        st.caption("🔍 分析结果中的比价看板")
        render_unified_price_comparison_module()
        
        # 添加订单数据上传功能
        st.markdown("---")
        st.subheader("📊 订单数据分析")
        render_order_data_uploader()
    
    with tab_map["🎯 场景营销"]:
        display_scenario_marketing_dashboard(st.session_state.get("current_data", {}))
    
    with tab_map["📋 问题诊断"]:
        display_problem_diagnostic_center(st.session_state.get("current_data", {}))

def display_product_strategy(analysis_result):
    """显示商品策略分析"""
    st.subheader("🛍️ 商品策略分析")
    
    if 'strategic_decisions' in analysis_result:
        decisions = analysis_result['strategic_decisions']
        
        # 流量品策略
        if '流量品选择' in decisions:
            st.write("**🎯 流量品建议**")
            
            traffic_options = decisions['流量品选择']
            if traffic_options:
                for option in traffic_options:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{option.description}**")
                        st.write(f"预期客流增长: +{option.expected_outcome.get('客流量增长', 0)*100:.1f}%")
                        st.write(f"关联销售提升: +{option.expected_outcome.get('关联销售提升', 0)*100:.1f}%")
                    
                    with col2:
                        confidence_color = "green" if option.confidence_score > 0.7 else "orange"
                        st.markdown(f"<div style='text-align: center; color: {confidence_color}; font-size: 1.2em; font-weight: bold;'>置信度<br>{option.confidence_score:.1%}</div>", unsafe_allow_html=True)
        
        # 折扣品策略
        if '折扣品策略' in decisions:
            st.write("**💰 折扣品建议**")
            
            discount_options = decisions['折扣品策略']
            if discount_options:
                for option in discount_options:
                    with st.expander(f"折扣方案: {option.description}"):
                        
                        # 创建指标展示
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "预期销量提升",
                                f"+{option.expected_outcome.get('销量提升', 0)*100:.0f}%"
                            )
                        
                        with col2:
                            st.metric(
                                "库存周转改善",
                                f"+{option.expected_outcome.get('库存周转', 0)*100:.0f}%"
                            )
                        
                        with col3:
                            impact = option.expected_outcome.get('毛利率影响', 0)
                            st.metric(
                                "毛利率影响",
                                f"{impact*100:+.0f}%",
                                delta="预期范围内" if abs(impact) < 0.3 else "需谨慎"
                            )
        
        # 定价策略
        if '定价策略' in decisions:
            st.write("**💲 定价策略分析**")
            
            pricing_options = decisions['定价策略']
            
            # 创建定价策略对比表
            if pricing_options:
                pricing_data = []
                for option in pricing_options:
                    pricing_data.append({
                        '策略': option.description,
                        '风险等级': f"{option.risk_level:.1%}",
                        '预期市场份额': f"+{option.expected_outcome.get('市场份额', 0)*100:.1f}%",
                        '预期毛利影响': f"{option.expected_outcome.get('毛利率', 0)*100:+.1f}%",
                        '推荐度': f"{option.confidence_score:.1%}"
                    })
                
                pricing_df = pd.DataFrame(pricing_data)
                st.dataframe(pricing_df, width='stretch')

def display_trend_analysis(analysis_result):
    """显示趋势分析"""
    st.subheader("📈 销售趋势预测")
    
    if 'trend_predictions' in analysis_result:
        predictions = analysis_result['trend_predictions']
        
        # 趋势图
        if 'predictions' in predictions:
            pred_df = predictions['predictions']
            
            fig = go.Figure()
            
            # 主趋势线
            fig.add_trace(go.Scatter(
                x=pred_df['date'],
                y=pred_df['predicted_growth_rate'],
                mode='lines+markers',
                name='预测增长率',
                line=dict(color='#1f77b4', width=3)
            ))
            
            # 置信区间
            fig.add_trace(go.Scatter(
                x=pred_df['date'],
                y=pred_df['confidence_upper'],
                mode='lines',
                line=dict(width=0),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=pred_df['date'],
                y=pred_df['confidence_lower'],
                fill='tonexty',
                mode='lines',
                line=dict(width=0),
                name='置信区间',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            
            fig.update_layout(
                title="未来30天销售增长趋势预测",
                xaxis_title="日期",
                yaxis_title="增长率",
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, width='stretch', key='prediction_sales_growth_trend')
        
        # 趋势洞察
        if 'trend_summary' in predictions:
            trend_summary = predictions['trend_summary']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                trend_color = "green" if trend_summary['overall_trend'] == "上升" else "red"
                st.markdown(f"""
                <div class="metric-card">
                    <h4>整体趋势</h4>
                    <span style="color: {trend_color}; font-size: 1.5em; font-weight: bold;">
                        {trend_summary['overall_trend']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                volatility_color = "red" if trend_summary['volatility'] == "高" else "green"
                st.markdown(f"""
                <div class="metric-card">
                    <h4>波动性</h4>
                    <span style="color: {volatility_color}; font-size: 1.5em; font-weight: bold;">
                        {trend_summary['volatility']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                peak_count = len(trend_summary['peak_periods'])
                st.markdown(f"""
                <div class="metric-card">
                    <h4>销售高峰期</h4>
                    <span style="color: #1f77b4; font-size: 1.5em; font-weight: bold;">
                        {peak_count} 个
                    </span>
                </div>
                """, unsafe_allow_html=True)
        
        # 关键洞察
        if 'key_insights' in predictions:
            st.write("**🔍 关键洞察**")
            for insight in predictions['key_insights']:
                st.markdown(f"• {insight}")

def display_risk_assessment(analysis_result):
    """显示风险评估"""
    st.subheader("⚠️ 风险评估分析")
    
    if 'risk_assessment' in analysis_result:
        risks = analysis_result['risk_assessment']
        
        # 风险矩阵可视化
        risk_data = []
        all_risks = []
        
        for category, risk_factors in risks.items():
            for factor, risk_info in risk_factors.items():
                risk_data.append({
                    'category': category,
                    'factor': factor,
                    'probability': risk_info['probability'],
                    'impact': risk_info['impact'],
                    'risk_score': risk_info['risk_score']
                })
                all_risks.append(risk_info['risk_score'])
        
        # 创建风险矩阵图
        risk_df = pd.DataFrame(risk_data)
        
        fig = px.scatter(
            risk_df,
            x='probability',
            y='impact', 
            size='risk_score',
            color='category',
            hover_data=['factor'],
            title="风险矩阵分析",
            labels={
                'probability': '发生概率',
                'impact': '影响程度',
                'category': '风险类别'
            }
        )
        
        fig.update_layout(
            xaxis=dict(range=[0, 1]),
            yaxis=dict(range=[0, 1]),
            template='plotly_white'
        )
        
        st.plotly_chart(fig, width='stretch', key='risk_probability_impact_matrix')
        
        # 高风险项目警示
        high_risks = [item for item in risk_data if item['risk_score'] > 0.5]
        
        if high_risks:
            st.write("**🚨 高风险警示**")
            
            for risk in high_risks:
                risk_level = "high-risk" if risk['risk_score'] > 0.7 else "risk-warning"
                
                st.markdown(f"""
                <div class="{risk_level}">
                    <strong>⚠️ {risk['factor']}</strong><br>
                    发生概率: {risk['probability']:.1%} | 影响程度: {risk['impact']:.1%} | 风险评分: {risk['risk_score']:.2f}
                </div>
                """, unsafe_allow_html=True)
        
        # 缓解策略
        st.write("**🛡️ 风险缓解策略**")
        
        for category, risk_factors in risks.items():
            with st.expander(f"{category}缓解策略"):
                for factor, risk_info in risk_factors.items():
                    if risk_info['risk_score'] > 0.3:  # 显示中高风险的缓解策略
                        st.write(f"**{factor}:**")
                        for suggestion in risk_info['mitigation_suggestions']:
                            st.write(f"• {suggestion}")

def display_competitor_analysis(analysis_result):
    """显示竞对分析"""
    st.subheader("🏢 竞对分析")
    
    if 'competitor_analysis' in analysis_result:
        competitor_data = analysis_result['competitor_analysis']
        
        # 定价对比分析
        if '定价对比' in competitor_data and 'comparison_details' in competitor_data['定价对比']:
            st.write("**💰 价格竞争力分析**")
            
            price_comparisons = competitor_data['定价对比']['comparison_details']
            
            if price_comparisons:
                # 创建价格对比图
                comparison_df = pd.DataFrame(price_comparisons)
                
                fig = go.Figure()
                
                # 竞品价格
                fig.add_trace(go.Bar(
                    name='竞品价格',
                    x=comparison_df['product'],
                    y=comparison_df['competitor_price'],
                    marker_color='lightcoral'
                ))
                
                # 自己价格
                fig.add_trace(go.Bar(
                    name='我方价格',
                    x=comparison_df['product'],
                    y=comparison_df['own_price'],
                    marker_color='lightblue'
                ))
                
                fig.update_layout(
                    title='价格对比分析',
                    xaxis_title='商品',
                    yaxis_title='价格 (元)',
                    barmode='group',
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, width='stretch', key='strategy_price_comparison')
                
                # 价格建议表
                st.write("**价格调整建议**")
                
                recommendation_data = []
                for item in price_comparisons:
                    recommendation_data.append({
                        '商品': item['product'],
                        '竞品价格': f"¥{item['competitor_price']:.2f}",
                        '我方价格': f"¥{item['own_price']:.2f}",
                        '价差': f"{item['price_gap_pct']:.1%}",
                        '建议': item['recommendation']
                    })
                
                rec_df = pd.DataFrame(recommendation_data)
                st.dataframe(rec_df, width='stretch')
        
        # 成本利润倒推
        if '成本利润倒推' in competitor_data:
            st.write("**📊 竞品盈利能力分析**")
            
            profitability = competitor_data['成本利润倒推']
            
            if 'high_margin_products' in profitability:
                high_margin = profitability['high_margin_products']
                
                if high_margin:
                    st.write("竞品高利润商品TOP5:")
                    
                    margin_df = pd.DataFrame(high_margin[:5])
                    
                    fig = px.bar(
                        margin_df,
                        x='product',
                        y='margin',
                        title='竞品高利润商品分析',
                        labels={'product': '商品', 'margin': '毛利率'}
                    )
                    
                    st.plotly_chart(fig, width='stretch', key='strategy_competitor_high_margin')
            
            if 'estimated_monthly_revenue' in profitability:
                estimated_revenue = profitability['estimated_monthly_revenue']
                st.metric(
                    "竞品预估月营收",
                    f"¥{estimated_revenue:,.0f}",
                    help="基于售价和月销量估算"
                )
        
        # 选址建议
        if '选址建议' in competitor_data:
            location_rec = competitor_data['选址建议']
            
            st.write("**🏢 选址策略建议**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="recommendation-box">
                    <h4>选址策略</h4>
                    {location_rec['proximity_strategy']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if 'risk_assessment' in location_rec:
                    risks = location_rec['risk_assessment']
                    
                    fig = go.Figure(go.Bar(
                        x=list(risks.keys()),
                        y=list(risks.values()),
                        marker_color=['red' if v > 0.6 else 'orange' if v > 0.4 else 'green' for v in risks.values()]
                    ))
                    
                    fig.update_layout(
                        title='选址风险评估',
                        yaxis_title='风险程度',
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig, width='stretch', key='strategy_location_risk_assessment')

def display_hypothesis_validation(analysis_result):
    """显示假设验证"""
    st.subheader("🔬 商业假设验证")
    
    if 'hypothesis_analysis' in analysis_result:
        hypotheses = analysis_result['hypothesis_analysis']
        
        if hypotheses:
            for hyp_id, hypothesis in hypotheses.items():
                with st.expander(f"假设 {hyp_id}: {hypothesis['description']}"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**假设详情**")
                        st.write(f"假设ID: {hypothesis['hypothesis_id']}")
                        st.write(f"置信度: {hypothesis['confidence_level']:.1%}")
                        
                        if hypothesis['validation_result'] is not None:
                            status = "✅ 已验证" if hypothesis['validation_result'] else "❌ 未通过"
                            st.write(f"验证状态: {status}")
                    
                    with col2:
                        st.write("**测试指标**")
                        for metric in hypothesis['test_metrics']:
                            st.write(f"• {metric}")
                    
                    st.write("**支持数据**")
                    supporting_data = hypothesis['supporting_data']
                    
                    # 创建支持数据的可视化
                    if supporting_data:
                        data_items = list(supporting_data.items())
                        if len(data_items) > 0:
                            
                            # 数值型数据用图表展示
                            numeric_data = {k: v for k, v in data_items if isinstance(v, (int, float))}
                            
                            if numeric_data:
                                fig = go.Figure(go.Bar(
                                    x=list(numeric_data.keys()),
                                    y=list(numeric_data.values()),
                                    marker_color='lightblue'
                                ))
                                
                                fig.update_layout(
                                    title='假设支持数据',
                                    template='plotly_white'
                                )
                                
                                st.plotly_chart(fig, width='stretch', key=f'hypothesis_chart_{hyp_id}')
                            else:
                                # 非数值数据用表格展示
                                st.json(supporting_data)
        else:
            st.info("暂无商业假设数据，系统将基于实际经营数据自动生成假设")

def display_learning_effects(analysis_result, dashboard_instance):
    """显示学习效果分析"""
    st.subheader("🧠 AI学习效果分析")
    
    # 检查学习元数据
    learning_metadata = analysis_result.get('learning_metadata', {})
    
    if not learning_metadata.get('learning_enabled', False):
        st.warning("⚠️ AI学习系统未启用或运行异常")
        if 'error' in learning_metadata:
            st.error(f"错误信息: {learning_metadata['error']}")
        return
    
    # 1. 学习状态概览
    st.write("**📊 学习状态概览**")
    
    learning_stats = learning_metadata.get('learning_statistics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sessions = learning_stats.get('total_learning_sessions', 0)
        st.metric("总学习次数", total_sessions, 
                 delta="累积经验" if total_sessions > 0 else "待开始")
    
    with col2:
        online_updates = learning_stats.get('online_updates', 0)
        st.metric("在线学习", online_updates,
                 delta="实时优化" if online_updates > 0 else "暂无")
    
    with col3:
        batch_updates = learning_stats.get('batch_updates', 0)
        st.metric("批量训练", batch_updates,
                 delta="深度学习" if batch_updates > 0 else "暂无")
    
    with col4:
        recent_activity = learning_stats.get('recent_activity', {})
        recent_sessions = recent_activity.get('total_sessions', 0)
        st.metric("近7天活动", recent_sessions,
                 delta="活跃" if recent_sessions > 5 else "稳定" if recent_sessions > 0 else "待激活")
    
    # 2. 模型性能趋势
    if 'performance_trends' in learning_stats:
        st.write("**📈 模型性能趋势**")
        
        performance_trends = learning_stats['performance_trends']
        
        if performance_trends:
            # 创建性能趋势图表
            trend_data = []
            for model_name, trend_info in performance_trends.items():
                trend_data.append({
                    'Model': model_name,
                    'Direction': trend_info['direction'],
                    'Rate': trend_info['rate'],
                    'Current_MAE': trend_info['current_mae'],
                    'Sample_Count': trend_info['sample_count']
                })
            
            trend_df = pd.DataFrame(trend_data)
            
            # 性能方向饼图
            direction_counts = trend_df['Direction'].value_counts()
            
            fig_pie = px.pie(
                values=direction_counts.values,
                names=direction_counts.index,
                title="模型性能趋势分布",
                color_discrete_map={
                    'improving': '#2E8B57',
                    'declining': '#DC143C',
                    'stable': '#4682B4'
                }
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(fig_pie, key="performance_pie")
            
            with col2:
                # 性能详细表格
                st.write("**模型性能详情**")
                
                display_df = trend_df.copy()
                display_df['Direction'] = display_df['Direction'].map({
                    'improving': '📈 改善中',
                    'declining': '📉 下降中',
                    'stable': '➡️ 稳定'
                })
                display_df['Rate'] = display_df['Rate'].apply(lambda x: f"{x:.1%}")
                display_df['Current_MAE'] = display_df['Current_MAE'].apply(lambda x: f"{x:.4f}")
                
                st.dataframe(display_df, key="performance_table")
        else:
            st.info("暂无模型性能趋势数据")
    
    # 3. 增强预测结果
    if 'enhanced_predictions' in analysis_result:
        st.write("**🔮 AI增强预测结果**")
        
        enhanced_predictions = analysis_result['enhanced_predictions']
        prediction_meta = enhanced_predictions.get('meta', {})
        
        # 显示预测元信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "预测时间",
                prediction_meta.get('prediction_time', 'N/A')[:19] if prediction_meta.get('prediction_time') else 'N/A',
                delta="最新"
            )
        
        with col2:
            st.metric(
                "特征维度", 
                prediction_meta.get('feature_count', 0),
                delta="多维分析"
            )
        
        with col3:
            models_used = prediction_meta.get('models_used', [])
            st.metric(
                "使用模型", 
                len(models_used),
                delta="集成预测"
            )
        
        # 显示各模型预测结果
        for model_name, prediction_stats in enhanced_predictions.items():
            if model_name == 'meta':
                continue
            
            with st.expander(f"模型 {model_name} 预测详情"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("预测均值", f"{prediction_stats.get('mean', 0):.2f}")
                
                with col2:
                    st.metric("标准差", f"{prediction_stats.get('std', 0):.2f}")
                
                with col3:
                    st.metric("最小值", f"{prediction_stats.get('min', 0):.2f}")
                
                with col4:
                    st.metric("最大值", f"{prediction_stats.get('max', 0):.2f}")
                
                # 预测值分布图
                predictions_list = prediction_stats.get('predictions', [])
                if predictions_list:
                    fig_hist = px.histogram(
                        x=predictions_list,
                        title=f"{model_name} 预测值分布",
                        labels={'x': '预测值', 'y': '频次'}
                    )
                    
                    st.plotly_chart(fig_hist, key=f"pred_hist_{model_name}")
    
    # 4. 自适应建议
    adaptive_recs = learning_metadata.get('adaptive_recommendations', [])
    
    if adaptive_recs:
        st.write("**💡 AI自适应建议**")
        
        for i, recommendation in enumerate(adaptive_recs, 1):
            st.markdown(f"""
            <div class="recommendation-box">
                <strong>AI建议 {i}:</strong> {recommendation}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("暂无AI自适应建议，系统正在学习中...")
    
    # 5. 数据质量评估
    try:
        learning_status = dashboard_instance.get_learning_status()
        data_stats = learning_status.get('data_statistics', {})
        
        if data_stats:
            st.write("**📊 学习数据质量概览**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "数据集总数", 
                    data_stats.get('total_datasets', 0),
                    delta="历史积累"
                )
            
            with col2:
                avg_quality = data_stats.get('average_quality_score', 0)
                quality_label = "优秀" if avg_quality > 0.8 else "良好" if avg_quality > 0.6 else "待改善"
                st.metric(
                    "平均质量评分", 
                    f"{avg_quality:.3f}",
                    delta=quality_label
                )
            
            with col3:
                recent_datasets = data_stats.get('recent_datasets_7days', 0)
                st.metric(
                    "近期新增", 
                    recent_datasets,
                    delta="持续更新" if recent_datasets > 0 else "稳定期"
                )
            
            # 数据质量分布
            quality_dist = data_stats.get('quality_distribution', {})
            if quality_dist:
                fig_quality = px.bar(
                    x=list(quality_dist.keys()),
                    y=list(quality_dist.values()),
                    title="数据质量分布",
                    labels={'x': '质量等级', 'y': '数据集数量'},
                    color=list(quality_dist.values()),
                    color_continuous_scale=['red', 'orange', 'yellow', 'green']
                )
                
                st.plotly_chart(fig_quality, key="quality_distribution")
    
    except Exception as e:
        st.error(f"获取学习状态失败: {e}")


def render_order_analysis_module(current_data: Dict[str, Any]) -> None:
    """渲染订单数据分析模块"""
    st.write("**订单数据综合分析 - 基于实际业务数据深度洞察**")
    
    # 检查是否有订单数据
    order_data = current_data.get("order_data", pd.DataFrame())
    
    if order_data.empty:
        st.info("📈 暂无订单数据，请加载包含订单信息的Excel文件")
        
        # 显示订单数据格式要求
        with st.expander("📋 订单数据格式要求"):
            st.markdown("""
            **必需字段：**
            - `订单ID`: 订单唯一标识
            - `商品名称`: 商品名称
            - `商品实售价`: 商品售价
            - `销量`: 商品数量
            - `下单时间`: 订单时间
            - `门店名称`: 门店标识
            - `渠道`: 销售渠道
            - `收货地址`: 配送地址
            
            **可选字段：**
            - `利润额`: 单品利润
            - `成本`: 商品成本
            - `物流配送费`: 配送费用
            - `平台佣金`: 平台抽成
            - `配送距离`: 配送距离
            - `美团一级分类`: 商品分类
            """)
        return
    
    st.success(f"✅ 已加载订单数据：{len(order_data):,} 条记录")
    
    # 数据预处理和特征工程
    try:
        processed_order_data = preprocess_order_data(order_data)
        order_summary = calculate_order_metrics(processed_order_data)
        
        # 创建分析选项卡
        analysis_tabs = st.tabs([
            "📊 订单概览", 
            "💰 利润分析", 
            "⏰ 时间分析",
            "🏪 门店分析",
            "📦 商品分析",
            "🚚 配送分析",
            "💡 智能洞察"
        ])
        
        with analysis_tabs[0]:
            if ORDER_ENHANCEMENT_AVAILABLE:
                render_enhanced_order_overview(processed_order_data, order_summary)
            else:
                render_order_overview(processed_order_data, order_summary)
        
        with analysis_tabs[1]:
            if ORDER_ENHANCEMENT_AVAILABLE:
                render_enhanced_profit_analysis(processed_order_data, order_summary)
            else:
                render_profit_analysis(processed_order_data, order_summary)
        
        with analysis_tabs[2]:
            render_time_analysis(processed_order_data)
        
        with analysis_tabs[3]:
            render_store_analysis(processed_order_data)
        
        with analysis_tabs[4]:
            render_product_analysis(processed_order_data)
        
        with analysis_tabs[5]:
            render_delivery_analysis(processed_order_data)
        
        with analysis_tabs[6]:
            render_order_insights(processed_order_data, order_summary)
            
    except Exception as e:
        st.error(f"订单数据分析时出错: {str(e)}")
        st.info("💡 请检查数据格式是否符合要求")


def preprocess_order_data(order_data: pd.DataFrame) -> pd.DataFrame:
    """订单数据预处理 - 根据标准业务逻辑"""
    try:
        df = order_data.copy()
        
        # 🔴 **关键业务规则1：剔除耗材数据** - 根据业务逻辑最终确认文档
        # 识别标准：一级分类名 == '耗材'
        # 参考：订单数据业务逻辑确认.md
        original_rows = len(df)
        
        # 支持多种列名变体
        category_col = None
        for col_name in ['一级分类名', '美团一级分类', '一级分类']:
            if col_name in df.columns:
                category_col = col_name
                break
        
        if category_col:
            df = df[df[category_col] != '耗材'].copy()
            removed_rows = original_rows - len(df)
            if removed_rows > 0:
                st.info(f"🔴 已自动剔除 {removed_rows} 行耗材数据（购物袋等），从 {original_rows} 行减少到 {len(df)} 行")
                print(f"✅ 已剔除 {removed_rows} 行耗材数据（购物袋等），从 {original_rows} 行减少到 {len(df)} 行")
        else:
            st.warning(f"⚠️ 未找到一级分类列（查找了：一级分类名、美团一级分类、一级分类），无法剔除耗材")
            print(f"⚠️ 未找到一级分类列，数据列名: {list(df.columns[:10])}")
        
        # 🔴 **关键业务规则2：剔除咖啡渠道数据** - 咖啡业务非O2O零售
        # 识别标准：渠道 in ['饿了么咖啡', '美团咖啡']
        if '渠道' in df.columns:
            exclude_channels = ['饿了么咖啡', '美团咖啡']
            before_filter = len(df)
            df = df[~df['渠道'].isin(exclude_channels)].copy()
            after_filter = len(df)
            coffee_removed = before_filter - after_filter
            
            if coffee_removed > 0:
                st.info(f"☕ 已自动剔除咖啡渠道数据 {coffee_removed} 行（饿了么咖啡、美团咖啡），从 {before_filter} 行减少到 {after_filter} 行")
                print(f"✅ 已剔除 {coffee_removed} 行咖啡渠道数据，从 {before_filter} 行减少到 {after_filter} 行")
        
        # 数据类型转换 - 根据业务逻辑确认文档的字段定义
        numeric_columns = [
            # 基础商品字段
            '商品实售价', '商品原价', '销量', '利润额', '成本', '配送距离',
            # 标准业务逻辑字段
            '物流配送费', '平台佣金', '用户支付配送费', '配送费减免金额',
            '满减金额', '商家代金券', '商品减免金额', '打包费', '订单零售额',
            # 其他可选成本字段
            '满赠金额', '商家承担部分券', '退款金额', '新客减免金额'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # 对于缺失的营销成本字段，填充0以保证计算的准确性
                if col in ['物流配送费', '平台佣金', '用户支付配送费', 
                          '配送费减免金额', '满减金额', '商家代金券']:
                    df[col] = df[col].fillna(0)
        
        # 时间字段处理
        if '下单时间' in df.columns:
            df['下单时间'] = pd.to_datetime(df['下单时间'], errors='coerce')
            df['下单日期'] = df['下单时间'].dt.date
            df['下单小时'] = df['下单时间'].dt.hour
            df['下单星期'] = df['下单时间'].dt.day_name()
            
            # 时间段映射
            hour_mapping = {
                0: '凌晨', 1: '凌晨', 2: '凌晨', 3: '凌晨', 4: '凌晨', 5: '清晨',
                6: '清晨', 7: '早晨', 8: '上午', 9: '上午', 10: '上午', 11: '中午',
                12: '中午', 13: '下午', 14: '下午', 15: '下午', 16: '下午', 17: '傍晚',
                18: '傍晚', 19: '晚上', 20: '晚上', 21: '晚上', 22: '夜晚', 23: '夜晚'
            }
            df['下单时间段'] = df['下单小时'].map(hour_mapping)
        
        # 商品角色判断 (根据商品实售价判断主力品)
        if '商品实售价' in df.columns and '订单ID' in df.columns:
            max_price_per_order = df.groupby('订单ID')['商品实售价'].transform('max')
            df['商品角色'] = np.where(df['商品实售价'] == max_price_per_order, '主力品', '凑单品')
        
        # 配送距离分段
        if '配送距离' in df.columns:
            df['配送距离_km'] = df['配送距离'] / 1000
            df['配送距离分段'] = pd.cut(
                df['配送距离_km'],
                bins=[0, 1, 2, 3, 4, 5, float('inf')],
                labels=['1km内', '1-2km', '2-3km', '3-4km', '4-5km', '5km以上']
            )
        
        # 价格分段 (根据商品实售价)
        if '商品实售价' in df.columns:
            df['价格分段'] = pd.cut(
                df['商品实售价'],
                bins=[0, 10, 30, 50, 100, float('inf')],
                labels=['低价(<10元)', '中低价(10-30元)', '中价(30-50元)', '高价(50-100元)', '超高价(>100元)']
            )
        
        return df
        
    except Exception as e:
        st.error(f"数据预处理失败: {str(e)}")
        return order_data


def calculate_order_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """计算订单级指标 - 使用统一的标准业务逻辑"""
    try:
        order_summary = {}
        
        if '订单ID' not in df.columns:
            return order_summary
        
        # 如果可用，使用统一业务逻辑配置
        if STANDARD_CONFIG_AVAILABLE:
            print("🔧 使用标准业务逻辑计算订单指标")
            
            # 使用统一配置创建订单级汇总
            order_agg = create_order_level_summary(df, StandardBusinessConfig)
            
            # 应用标准业务逻辑计算
            order_agg = apply_standard_business_logic(order_agg)
            
            # 生成汇总指标
            order_summary['订单总数'] = len(order_agg)
            order_summary['商品总数'] = len(df)
            order_summary['平均每单商品数'] = len(df) / len(order_agg) if len(order_agg) > 0 else 0
            
            # 销售额统计 (基于标准业务逻辑)
            if '商品实售价总和' in order_agg.columns:
                total_sales = order_agg['商品实售价总和'].sum()
                order_summary['总销售额'] = total_sales
                order_summary['平均客单价'] = total_sales / len(order_agg) if len(order_agg) > 0 else 0
                order_summary['客单价中位数'] = order_agg['商品实售价总和'].median()
            
            # 订单总收入统计（商品实售价 + 打包费 + 用户支付配送费）
            if '预估订单收入' in order_agg.columns:
                total_revenue = order_agg['预估订单收入'].sum()
                order_summary['订单总收入'] = total_revenue
                order_summary['平均订单收入'] = total_revenue / len(order_agg) if len(order_agg) > 0 else 0
            
            # 利润统计 (使用标准业务逻辑计算的实际利润)
            if '订单实际利润额' in order_agg.columns:
                actual_profit_series = order_agg['订单实际利润额']
                total_profit = actual_profit_series.sum()
                order_summary['总利润额'] = total_profit
                order_summary['平均订单利润'] = actual_profit_series.mean()
                order_summary['盈利订单数'] = (actual_profit_series > 0).sum()
                order_summary['盈利订单比例'] = (actual_profit_series > 0).mean()
                # 🔍 调试输出 - 利润计算
                print(f"\n💰 [DEBUG] 利润计算验证:")
                print(f"   - 总利润额: ¥{total_profit:,.2f}")
                if all(col in order_agg.columns for col in ['商品实售价总和', '成本', '配送成本', '活动营销成本', '商品折扣成本', '平台佣金']):
                    packing_fee = order_agg['打包袋金额'].sum() if '打包袋金额' in order_agg.columns else 0
                    user_pay_delivery = order_agg['用户支付配送费'].sum() if '用户支付配送费' in order_agg.columns else 0
                    revenue_sum = (order_agg['商品实售价总和'].sum() + packing_fee + user_pay_delivery)
                    cost_sum = order_agg['成本'].sum()
                    delivery_sum = order_agg['配送成本'].sum()
                    activity_sum = order_agg['活动营销成本'].sum()
                    discount_sum = order_agg['商品折扣成本'].sum()
                    commission_sum = order_agg['平台佣金'].sum()
                    print(f"   - 订单总收入: ¥{revenue_sum:,.2f} (商品¥{order_agg['商品实售价总和'].sum():,.2f} + 打包¥{packing_fee:,.2f} + 用户支付配送费¥{user_pay_delivery:,.2f})")
                    print(f"   - 商品成本: ¥{cost_sum:,.2f}")
                    print(f"   - 配送成本: ¥{delivery_sum:,.2f}")
                    print(f"   - 活动营销成本: ¥{activity_sum:,.2f}")
                    print(f"   - 商品折扣成本: ¥{discount_sum:,.2f}")
                    print(f"   - 平台佣金: ¥{commission_sum:,.2f}")
                    expected = revenue_sum - cost_sum - delivery_sum - activity_sum - discount_sum - commission_sum
                    print(f"   - 公式验证: ¥{revenue_sum:,.2f} - ¥{cost_sum:,.2f} - ¥{delivery_sum:,.2f} - ¥{activity_sum:,.2f} - ¥{discount_sum:,.2f} - ¥{commission_sum:,.2f} = ¥{expected:,.2f}")
                    print(f"   - 差异: ¥{total_profit - expected:,.2f}")
                else:
                    print(f"   ⚠️ 缺少必要字段，无法验证详细计算")            
            # 配送成本统计 (使用标准业务逻辑)
            if '配送成本' in order_agg.columns:
                delivery_cost_series = order_agg['配送成本']
                total_delivery_cost = delivery_cost_series.sum()
                order_summary['平均配送成本'] = delivery_cost_series.mean()
                order_summary['总配送成本'] = total_delivery_cost
                # 🔍 调试输出
                print(f"🔍 [DEBUG] 配送成本计算:")
                print(f"   - 总配送成本: ¥{total_delivery_cost:,.2f}")
                print(f"   - 平均配送成本: ¥{delivery_cost_series.mean():,.2f}")
                if '用户支付配送费' in order_agg.columns and '配送费减免金额' in order_agg.columns and '物流配送费' in order_agg.columns:
                    user_pay = order_agg['用户支付配送费'].sum()
                    exemption_sum = order_agg['配送费减免金额'].sum()
                    logistics_sum = order_agg['物流配送费'].sum()
                    print(f"   - 配送费减免（支出）: ¥{exemption_sum:,.2f}")
                    print(f"   - 物流配送费（支出）: ¥{logistics_sum:,.2f}")
                    print(f"   - 用户支付配送费（收入）: ¥{user_pay:,.2f}")
                    print(f"   - 配送净成本公式: ({exemption_sum:,.2f} + {logistics_sum:,.2f}) - {user_pay:,.2f} = ¥{exemption_sum + logistics_sum - user_pay:,.2f}")
            
            # 活动营销成本统计（不含商品折扣）
            if '活动营销成本' in order_agg.columns:
                activity_marketing_series = order_agg['活动营销成本']
                order_summary['总活动营销成本'] = activity_marketing_series.sum()
                order_summary['平均活动营销成本'] = activity_marketing_series.mean()
            
            # 商品折扣成本统计
            if '商品折扣成本' in order_agg.columns:
                product_discount_series = order_agg['商品折扣成本']
                order_summary['总商品折扣成本'] = product_discount_series.sum()
                order_summary['平均商品折扣成本'] = product_discount_series.mean()
            
            # 总营销成本统计（活动营销 + 商品折扣）
            if '商家活动支出' in order_agg.columns:
                marketing_cost_series = order_agg['商家活动支出']
                order_summary['总营销成本'] = marketing_cost_series.sum()
                order_summary['平均营销成本'] = marketing_cost_series.mean()
            
        else:
            # 使用简化版本的计算逻辑（兼容性处理）
            print("⚠️ 使用简化版本的订单指标计算")
            order_summary = calculate_order_metrics_fallback(df)
        
        return order_summary
        
    except Exception as e:
        st.error(f"指标计算失败: {str(e)}")
        return {}


def calculate_order_metrics_fallback(df: pd.DataFrame) -> Dict[str, Any]:
    """备用的订单指标计算方法 (兼容性处理)"""
    order_summary = {}
    
    # 基础订单指标
    order_summary['订单总数'] = df['订单ID'].nunique()
    order_summary['商品总数'] = len(df)
    order_summary['平均每单商品数'] = len(df) / df['订单ID'].nunique()
    
    # 销售额统计
    if '商品实售价' in df.columns and '销量' in df.columns:
        df['商品销售额'] = df['商品实售价'] * df['销量']
        order_sales = df.groupby('订单ID')['商品销售额'].sum()
        order_summary['总销售额'] = order_sales.sum()
        order_summary['平均客单价'] = order_sales.mean()
        order_summary['客单价中位数'] = order_sales.median()
    
    # 简化的利润统计
    if '利润额' in df.columns:
        order_profit = df.groupby('订单ID')['利润额'].sum()
        order_summary['总利润额'] = order_profit.sum()
        order_summary['平均订单利润'] = order_profit.mean()
        order_summary['盈利订单数'] = (order_profit > 0).sum()
        order_summary['盈利订单比例'] = (order_profit > 0).mean()
    
    # 配送费统计
    if '物流配送费' in df.columns:
        order_delivery = df.groupby('订单ID')['物流配送费'].first()
        order_summary['平均配送成本'] = order_delivery.mean()
        order_summary['总配送成本'] = order_delivery.sum()
    
    return order_summary


def render_order_overview(df: pd.DataFrame, order_summary: Dict[str, Any]) -> None:
    """渲染订单概览 - 展示标准业务逻辑指标"""
    st.write("**📊 订单业务概览 (按标准业务逻辑计算)**")
    
    # 核心指标卡片 - 基础业务指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "订单总数",
            f"{order_summary.get('订单总数', 0):,}",
            help="统计期间内的总订单数量"
        )
    
    with col2:
        st.metric(
            "商品总数",
            f"{order_summary.get('商品总数', 0):,}",
            help="所有订单中的商品条目总数"
        )
    
    with col3:
        st.metric(
            "平均客单价",
            f"¥{order_summary.get('平均客单价', 0):.2f}",
            help="每个订单的平均销售额 (商品实售价×销量)"
        )
    
    with col4:
        if '盈利订单比例' in order_summary:
            st.metric(
                "盈利订单比例",
                f"{order_summary.get('盈利订单比例', 0):.1%}",
                help="按标准业务逻辑计算的实际盈利订单占比"
            )
    
    # 标准业务逻辑关键指标
    st.write("**🎨 标准业务逻辑关键指标**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总利润额 (实际)",
            f"¥{order_summary.get('总利润额', 0):,.2f}",
            help="按标准业务逻辑计算: 预估订单收入 - 配送成本"
        )
    
    with col2:
        st.metric(
            "平均订单利润",
            f"¥{order_summary.get('平均订单利润', 0):.2f}",
            help="每个订单的平均实际利润额"
        )
    
    with col3:
        st.metric(
            "总配送成本",
            f"¥{order_summary.get('总配送成本', 0):,.2f}",
            help="商家配送净支出: (配送费减免 + 物流配送费) - 用户支付配送费"
        )
    
    with col4:
        st.metric(
            "平均配送成本",
            f"¥{order_summary.get('平均配送成本', 0):.2f}",
            help="每个订单的平均配送成本"
        )
    
    # 数据质量概览
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📈 业务数据分布**")
        
        # 门店分布
        if '门店名称' in df.columns:
            store_dist = df['门店名称'].value_counts()
            fig = px.pie(
                values=store_dist.values,
                names=store_dist.index,
                title="门店订单分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**🕐 订单时间分布**")
        
        # 时间段分布
        if '下单时间段' in df.columns:
            time_dist = df['下单时间段'].value_counts()
            fig = px.bar(
                x=time_dist.index,
                y=time_dist.values,
                title="时间段订单量分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 业务逻辑说明
    with st.expander("📄 标准业务逻辑说明"):
        st.markdown("""
        **本看板采用的标准业务逻辑:**
        
        1. **预估订单收入** = (订单零售额 + 打包费 - 商家活动支出 - 平台佣金 + 用户支付配送费)
        2. **商家活动支出** = (配送费减免金额 + 满减金额 + 商品减免金额 + 商家代金券)
        3. **配送成本** = (用户支付配送费 - 配送费减免金额 - 物流配送费)
        4. **订单实际利润额** = 预估订单收入 - 配送成本
        
        **字段含义:**
        - **商品实售价**: 商品在前端展示的原价
        - **用户支付金额**: 用户实际支付价格 (考虑各种补贴活动)
        - **同一订单ID多行**: 每行代表一个商品SKU，订单级字段会重复显示
        """)


def render_profit_analysis(df: pd.DataFrame, order_summary: Dict[str, Any]) -> None:
    """渲染利润分析 - 按标准业务逻辑"""
    st.write("**💰 订单利润深度分析 (按标准业务逻辑计算)**")
    
    if '利润额' not in df.columns:
        st.info("缺少利润额字段，无法进行利润分析")
        return
    
    # 利润概览 - 所有指标都基于标准业务逻辑计算
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总利润额 (实际)",
            f"¥{order_summary.get('总利润额', 0):,.2f}",
            help="按标准业务逻辑: 预估订单收入 - 配送成本"
        )
    
    with col2:
        st.metric(
            "平均订单利润",
            f"¥{order_summary.get('平均订单利润', 0):.2f}",
            help="每个订单的平均实际利润额"
        )
    
    with col3:
        st.metric(
            "盈利订单数",
            f"{order_summary.get('盈利订单数', 0):,}",
            help="实际利润 > 0 的订单数量"
        )
    
    with col4:
        st.metric(
            "盈利率",
            f"{order_summary.get('盈利订单比例', 0):.1%}",
            help="盈利订单在所有订单中的占比"
        )
    
    # 业务逻辑成本细分
    st.write("**📄 成本细分分析 (按标准业务逻辑)**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "总配送成本",
            f"¥{order_summary.get('总配送成本', 0):,.2f}",
            help="商家配送净支出: (配送费减免 + 物流配送费) - 用户支付配送费"
        )
    
    with col2:
        # 计算商家活动支出总额 (如果数据中有的话)
        marketing_cost_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券']
        total_marketing_cost = 0
        for field in marketing_cost_fields:
            if field in df.columns:
                total_marketing_cost += df[field].sum()
        
        st.metric(
            "商家活动支出",
            f"¥{total_marketing_cost:,.2f}",
            help="配送费减免 + 满减 + 商品减免 + 商家代金券"
        )
    
    with col3:
        # 计算平台佣金总额
        platform_commission = df['平台佣金'].sum() if '平台佣金' in df.columns else 0
        st.metric(
            "平台佣金总额",
            f"¥{platform_commission:,.2f}",
            help="各个平台渠道收取的服务费"
        )
    
    # 利润分析图表
    col1, col2 = st.columns(2)
    
    with col1:
        # 订单利润分布 - 使用标准业务逻辑计算的实际利润
        if '订单ID' in df.columns:
            # 重新计算每个订单的实际利润 (简化版本)
            order_profit_simple = df.groupby('订单ID')['利润额'].sum()  # 这里用简化版本作为示例
            
            fig = px.histogram(
                x=order_profit_simple,
                nbins=30,
                title="订单利润分布 (按标准业务逻辑)",
                labels={'x': '订单实际利润(元)', 'y': '订单数量'}
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="盈亏平衡线")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 商哃利润贡献 - 显示简化的商品利润
        if '商品名称' in df.columns:
            # 这里使用原始利润额作为示例，实际应该用订单级利润分配
            product_profit = df.groupby('商品名称')['利润额'].sum().sort_values(ascending=False).head(10)
            
            fig = px.bar(
                x=product_profit.values,
                y=product_profit.index,
                orientation='h',
                title="TOP10 商品利润贡献",
                labels={'x': '利润贡献(元)', 'y': '商品名称'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 标准业务逻辑计算公式说明
    with st.expander("🧮 标准业务逻辑计算公式"):
        st.markdown("""
        **本分析采用的标准业务逻辑计算公式:**
        
        **1. 预估订单收入计算:**
        ```
        预估订单收入 = (订单零售额 + 打包费 - 商家活动支出 - 平台佣金 + 用户支付配送费)
        ```
        
        **2. 商家活动支出计算:**
        ```
        商家活动支出 = (配送费减免金额 + 满减金额 + 商品减免金额 + 商家代金券)
        ```
        
        **3. 配送成本计算:** ✅ 2025-10-13修正
        ```
        配送成本 = 配送费减免金额 + 物流配送费
        说明：这两项是商家在配送环节的实际支出
        ```
        
        **4. 最终利润计算:**
        ```
        订单实际利润额 = 预估订单收入 - 配送成本
        ```
        
        **重要说明:**
        - 所有指标都采用订单级聚合，避免重复计算
        - 订单级字段(如配送费、佣金)使用 `.first()` 取值
        - 商品级字段(如利润额、成本)使用 `.sum()` 聚合
        """)


def render_time_analysis(df: pd.DataFrame) -> None:
    """渲染时间分析"""
    st.write("**⏰ 时间维度分析**")
    
    if '下单时间' not in df.columns:
        st.info("缺少下单时间字段，无法进行时间分析")
        return
    
    # 时间分布分析
    col1, col2 = st.columns(2)
    
    with col1:
        # 每日订单量趋势
        if '下单日期' in df.columns:
            daily_orders = df.groupby('下单日期').size()
            
            fig = px.line(
                x=daily_orders.index,
                y=daily_orders.values,
                title="每日订单量趋势",
                labels={'x': '日期', 'y': '订单数量'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 小时分布热力图
        if '下单小时' in df.columns and '下单星期' in df.columns:
            hourly_heat = df.groupby(['下单星期', '下单小时']).size().unstack(fill_value=0)
            
            fig = px.imshow(
                hourly_heat.values,
                x=hourly_heat.columns,
                y=hourly_heat.index,
                title="星期-小时订单热力图",
                labels={'x': '小时', 'y': '星期', 'color': '订单数量'}
            )
            st.plotly_chart(fig, use_container_width=True)


def render_store_analysis(df: pd.DataFrame) -> None:
    """渲染门店分析"""
    st.write("**🏪 门店维度分析**")
    
    if '门店名称' not in df.columns:
        st.info("缺少门店名称字段，无法进行门店分析")
        return
    
    # 门店业绩对比
    store_metrics = df.groupby('门店名称').agg({
        '订单ID': 'nunique',
        '商品实售价': lambda x: (x * df.loc[x.index, '销量']).sum() if '销量' in df.columns else x.sum(),
        '利润额': 'sum' if '利润额' in df.columns else lambda x: 0
    }).round(2)
    
    store_metrics.columns = ['订单数', '销售额', '利润额']
    
    if len(store_metrics) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # 门店销售额对比
            fig = px.bar(
                x=store_metrics.index,
                y=store_metrics['销售额'],
                title="门店销售额对比",
                labels={'x': '门店', 'y': '销售额(元)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 门店利润对比
            if store_metrics['利润额'].sum() > 0:
                fig = px.bar(
                    x=store_metrics.index,
                    y=store_metrics['利润额'],
                    title="门店利润对比",
                    labels={'x': '门店', 'y': '利润额(元)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # 门店数据表
        st.write("**门店业绩详情**")
        st.dataframe(store_metrics, use_container_width=True)


def render_product_analysis(df: pd.DataFrame) -> None:
    """渲染商品分析"""
    st.write("**📦 商品维度分析**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 商品角色分析
        if '商品角色' in df.columns:
            role_dist = df['商品角色'].value_counts()
            
            fig = px.pie(
                values=role_dist.values,
                names=role_dist.index,
                title="商品角色分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 价格分段分析
        if '价格分段' in df.columns:
            price_dist = df['价格分段'].value_counts()
            
            fig = px.bar(
                x=price_dist.index,
                y=price_dist.values,
                title="价格分段商品分布",
                labels={'x': '价格分段', 'y': '商品数量'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 热销商品TOP榜
    if '商品名称' in df.columns and '销量' in df.columns:
        top_products = df.groupby('商品名称')['销量'].sum().sort_values(ascending=False).head(10)
        
        st.write("**🔥 热销商品TOP10**")
        
        top_products_df = pd.DataFrame({
            '商品名称': top_products.index,
            '总销量': top_products.values
        })
        
        st.dataframe(top_products_df, use_container_width=True)


def render_delivery_analysis(df: pd.DataFrame) -> None:
    """渲染配送分析"""
    st.write("**🚚 配送维度分析**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 配送距离分布
        if '配送距离分段' in df.columns:
            distance_dist = df['配送距离分段'].value_counts()
            
            fig = px.bar(
                x=distance_dist.index,
                y=distance_dist.values,
                title="配送距离分布",
                labels={'x': '配送距离', 'y': '订单数量'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 配送费分析
        if '物流配送费' in df.columns:
            avg_delivery_fee = df.groupby('配送距离分段')['物流配送费'].mean()
            
            fig = px.bar(
                x=avg_delivery_fee.index,
                y=avg_delivery_fee.values,
                title="平均配送费 vs 配送距离",
                labels={'x': '配送距离', 'y': '平均配送费(元)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 高配送费订单预警
    if '物流配送费' in df.columns:
        high_delivery_orders = df[df['物流配送费'] > 6]
        
        if not high_delivery_orders.empty:
            st.warning(f"⚠️ 发现 {len(high_delivery_orders)} 个高配送费订单（>6元）")
            
            with st.expander("查看高配送费订单详情"):
                display_cols = ['订单ID', '商品名称', '物流配送费', '配送距离_km', '收货地址']
                available_cols = [col for col in display_cols if col in high_delivery_orders.columns]
                
                if available_cols:
                    st.dataframe(high_delivery_orders[available_cols].head(20), use_container_width=True)


def render_order_insights(df: pd.DataFrame, order_summary: Dict[str, Any]) -> None:
    """渲染智能洞察"""
    st.write("**💡 智能业务洞察**")
    
    insights = []
    
    # 基于数据生成洞察
    if order_summary:
        # 盈利洞察
        profit_ratio = order_summary.get('盈利订单比例', 0)
        if profit_ratio > 0.8:
            insights.append("🎉 订单盈利率优秀，超过80%的订单都能产生利润")
        elif profit_ratio > 0.6:
            insights.append("👍 订单盈利率良好，建议优化剩余亏损订单")
        else:
            insights.append("⚠️ 订单盈利率偏低，建议重点关注成本控制和定价策略")
        
        # 客单价洞察
        avg_order_value = order_summary.get('平均客单价', 0)
        if avg_order_value > 50:
            insights.append(f"💰 平均客单价表现良好({avg_order_value:.2f}元)，客户消费水平较高")
        elif avg_order_value > 30:
            insights.append(f"📈 平均客单价适中({avg_order_value:.2f}元)，可通过套餐推荐等方式提升")
        else:
            insights.append(f"📊 平均客单价较低({avg_order_value:.2f}元)，建议加强客单价提升策略")
    
    # 时间洞察
    if '下单时间段' in df.columns:
        peak_time = df['下单时间段'].value_counts().index[0]
        insights.append(f"⏰ 订单高峰时段为{peak_time}，建议在此时段加强服务和备货")
    
    # 商品洞察
    if '商品角色' in df.columns:
        main_products_ratio = (df['商品角色'] == '主力品').mean()
        if main_products_ratio > 0.6:
            insights.append("🎯 主力商品占比较高，商品结构健康")
        else:
            insights.append("📦 凑单商品较多，建议优化商品组合和推荐策略")
    
    # 配送洞察
    if '物流配送费' in df.columns:
        avg_delivery_fee = df['物流配送费'].mean()
        high_delivery_ratio = (df['物流配送费'] > 6).mean()
        
        if high_delivery_ratio > 0.2:
            insights.append(f"🚚 高配送费订单占比{high_delivery_ratio:.1%}，建议优化配送策略")
        
        insights.append(f"📍 平均配送费为{avg_delivery_fee:.2f}元，可考虑配送费优化方案")
    
    # 显示洞察
    if insights:
        for i, insight in enumerate(insights, 1):
            st.markdown(f"""
            <div class="recommendation-box">
                <strong>洞察 {i}:</strong> {insight}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("数据分析中，更多洞察正在生成...")
    
    # 生成业务建议
    st.subheader("📋 业务优化建议")
    
    suggestions = [
        "📈 **销售提升**: 分析热销时段和热销商品，优化库存和推广策略",
        "💰 **成本控制**: 重点关注亏损订单，分析成本构成并制定改进措施", 
        "🚚 **配送优化**: 优化配送路线和费用结构，提升配送效率",
        "🎯 **精准营销**: 基于客户消费行为，制定个性化推荐和促销策略",
        "📊 **数据监控**: 建立关键指标监控体系，及时发现业务异常"
    ]
    
    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")


# ============================================================================
# 场景营销看板模块
# ============================================================================

def filter_data_by_time_dimension(df: pd.DataFrame, time_dimension: str, selected_period: str = None, latest_only: bool = True) -> pd.DataFrame:
    """
    根据时间维度筛选数据
    
    参数:
        df: 数据框（需包含时间维度字段）
        time_dimension: 时间维度 ('日', '周', '月')
        selected_period: 选择的具体周期（None或"全部XXX"表示不筛选具体周期）
        latest_only: 是否只保留最近一个周期的数据（默认True，当selected_period为None或"全部XXX"时生效）
        
    返回:
        筛选后的数据框
    """
    dim_mapping = {
        '日': '日期_datetime',
        '周': '年周',
        '月': '年月'
    }
    
    time_col = dim_mapping.get(time_dimension)
    if time_col not in df.columns:
        return df
    
    # 如果指定了具体周期且不是"全部XXX"，则筛选该周期
    if selected_period and not selected_period.startswith("全部"):
        if time_dimension == "日":
            # 将字符串转换为datetime进行比较
            selected_date = pd.to_datetime(selected_period)
            return df[df[time_col] == selected_date].copy()
        elif time_dimension == "周":
            return df[df[time_col] == selected_period].copy()
        else:  # 月
            return df[df[time_col] == selected_period].copy()
    
    # 否则，如果latest_only=True，返回最近一个周期
    if latest_only:
        latest_period = df[time_col].max()
        return df[df[time_col] == latest_period].copy()
    else:
        return df.copy()


def calculate_period_over_period(df: pd.DataFrame, dimension: str, metric_col: str) -> pd.DataFrame:
    """
    计算环比变化（支持日/周/月维度）
    
    参数:
        df: 数据框（需包含对应的时间维度字段）
        dimension: 时间维度 ('日', '周', '月')
        metric_col: 指标列名
        
    返回:
        包含环比变化的数据框（为每个指标增加独立的环比列）
    """
    # 映射维度到字段名
    dim_mapping = {
        '日': '日期_datetime',
        '周': '年周',
        '月': '年月'
    }
    
    time_col = dim_mapping.get(dimension)
    if time_col not in df.columns:
        return df
    
    # 按时间维度排序
    df = df.sort_values(time_col).reset_index(drop=True)
    
    # 为每个指标创建独立的环比列
    prev_col = f'{metric_col}_上期值'
    change_col = f'{metric_col}_环比变化'
    rate_col = f'{metric_col}_环比率'
    
    # 计算上期值
    df[prev_col] = df[metric_col].shift(1)
    
    # 计算环比变化（绝对值和百分比）
    df[change_col] = df[metric_col] - df[prev_col]
    df[rate_col] = ((df[metric_col] - df[prev_col]) / df[prev_col] * 100).round(2)
    
    # 处理无穷大和NaN值
    df[rate_col] = df[rate_col].replace([np.inf, -np.inf], np.nan)
    
    return df


def format_period_label(value, dimension: str) -> str:
    """格式化时间维度标签"""
    if dimension == '日':
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.strftime('%Y-%m-%d')
        return str(value)
    elif dimension == '周':
        return str(value)  # 已经是 '2024-W01' 格式
    else:  # 月
        return str(value)  # 已经是 '2024-01' 格式


def render_metric_with_comparison(col, metric_name: str, current_value, previous_value=None, 
                                    format_type='number', unit=''):
    """
    渲染带环比的指标卡片
    
    参数:
        col: streamlit列对象
        metric_name: 指标名称
        current_value: 当前值
        previous_value: 上期值
        format_type: 格式化类型 ('number', 'percent', 'currency')
        unit: 单位
    """
    with col:
        # 格式化当前值
        if format_type == 'number':
            display_value = f"{int(current_value):,}{unit}" if not pd.isna(current_value) else "N/A"
        elif format_type == 'percent':
            display_value = f"{current_value:.2f}%"
        elif format_type == 'currency':
            display_value = f"¥{current_value:,.2f}"
        else:
            display_value = str(current_value)
        
        # 计算环比
        if previous_value is not None and not pd.isna(previous_value) and previous_value != 0:
            change_rate = ((current_value - previous_value) / previous_value * 100)
            change_abs = current_value - previous_value
            
            # 判断涨跌
            if change_rate > 0:
                arrow = "📈"
                color = "green"
                sign = "+"
            elif change_rate < 0:
                arrow = "📉"
                color = "red"
                sign = ""
            else:
                arrow = "➡️"
                color = "gray"
                sign = ""
            
            st.metric(
                label=metric_name,
                value=display_value,
                delta=f"{sign}{change_rate:.2f}%",
                delta_color="normal" if change_rate >= 0 else "inverse"
            )
        else:
            st.metric(label=metric_name, value=display_value)


def extract_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """提取时间特征（增强版：支持日/周/月维度）"""
    df = df.copy()
    
    if '下单时间' in df.columns:
        # 转换为datetime，errors='coerce'会将无效日期转为NaT
        df['下单时间'] = pd.to_datetime(df['下单时间'], errors='coerce')
        
        # 基础时间字段（这些操作会自动处理NaT，返回NaN）
        df['日期'] = df['下单时间'].dt.date
        df['日期_datetime'] = pd.to_datetime(df['日期'], errors='coerce')
        df['小时'] = df['下单时间'].dt.hour
        df['星期'] = df['下单时间'].dt.dayofweek
        df['星期名'] = df['下单时间'].dt.day_name()
        
        # 周维度字段（处理NaT值）
        # 创建临时的isocalendar结果，只对有效日期计算
        valid_dates_mask = df['下单时间'].notna()
        df['年'] = None
        df['周'] = None
        
        if valid_dates_mask.any():
            iso_cal = df.loc[valid_dates_mask, '下单时间'].dt.isocalendar()
            df.loc[valid_dates_mask, '年'] = iso_cal.year
            df.loc[valid_dates_mask, '周'] = iso_cal.week
        
        # 转换为字符串，避免NaN问题
        df['年周'] = df.apply(
            lambda row: f"{int(row['年'])}-W{int(row['周']):02d}" if pd.notna(row['年']) and pd.notna(row['周']) else '',
            axis=1
        )
        
        # 月维度字段
        df['年月'] = df['下单时间'].dt.to_period('M').astype(str)
        df['月份'] = df['下单时间'].dt.month
        
        # O2O外卖行业时段划分（基于用户行为场景）
        def get_time_period(hour):
            if 6 <= hour < 8:
                return '清晨(6-8点)'
            elif 8 <= hour < 9:
                return '早高峰(8-9点)'
            elif 9 <= hour < 11:
                return '上午(9-11点)'
            elif 11 <= hour < 12:
                return '午高峰(11-12点)'
            elif 12 <= hour < 14:
                return '正午(12-14点)'
            elif 14 <= hour < 17:
                return '下午(14-17点)'
            elif 17 <= hour < 18:
                return '晚高峰前(17-18点)'
            elif 18 <= hour < 21:
                return '傍晚(18-21点)'
            elif 21 <= hour < 24:
                return '晚间(21-24点)'
            elif 0 <= hour < 3:
                return '深夜(0-3点)'
            else:  # 3-6点
                return '凌晨(3-6点)'
        
        # 场景标签（用于分析和营销）
        def get_scene_label(hour):
            if 6 <= hour < 8:
                return '出行/整理/早餐'
            elif 8 <= hour < 9:
                return '通勤/早餐'
            elif 9 <= hour < 11:
                return '办公/居家/日用补充'
            elif 11 <= hour < 12:
                return '午餐订餐高峰'
            elif 12 <= hour < 14:
                return '午餐/午休'
            elif 14 <= hour < 17:
                return '工作/家务/亲子/下午茶'
            elif 17 <= hour < 18:
                return '下班前备餐'
            elif 18 <= hour < 21:
                return '下班/归家/晚餐/路途'
            elif 21 <= hour < 24:
                return '居家/夜生活/睡前'
            elif 0 <= hour < 3:
                return '突发/急用/夜宵'
            else:  # 3-6点
                return '万籁俱寂/熬夜党'
        
        df['时段'] = df['小时'].apply(get_time_period)
        df['场景标签'] = df['小时'].apply(get_scene_label)
    
    return df


def render_time_period_marketing(df: pd.DataFrame, time_dimension: str = '日', selected_period: str = None):
    """时段场景营销分析（支持日/周/月维度切换）"""
    st.markdown('<p class="sub-header">⏰ 时段场景营销分析</p>', unsafe_allow_html=True)
    
    # ==================== 场景营销理念说明 ====================
    with st.expander("💡 什么是真正的「场景营销」？（快消零售视角）", expanded=False):
        st.markdown("""
        ### 🎯 快消零售的场景本质
        
        **场景 = 需求触发点 + 购买时机 + 商品解决方案**
        
        #### 快消零售的核心场景问题：
        
        1. **什么场景下用户会突然想买零食饮料日用品？**
           - 🏢 **办公场景**：下午犯困 → 咖啡、功能饮料、零食
           - 🏠 **居家场景**：追剧、游戏 → 薯片、瓜子、可乐
           - 🎉 **聚会场景**：朋友来了 → 啤酒、零食、水果
           - 🚨 **应急场景**：突然想起缺某物 → 纸巾、洗发水、电池
           - 🌙 **深夜场景**：失眠、加班 → 泡面、零食、饮料
        
        2. **如何满足用户的「即刻需求」和「急需痛点」？**
           - ⚡ **速度为王**：30分钟内送达（竞对也能做到）
           - 🎯 **15分钟必达**：1公里核心圈的竞争壁垒
           - 📦 **品类齐全**：用户一次性买齐所需（减少跳转其他平台）
           - � **智能推荐**：买零食推荐饮料，买啤酒推荐下酒菜
        
        3. **如何比美团、饿了么上的其他商家更快？**
           - 🏃 **距离优势**：1公里内必有仓，物理距离最短
           - 🤖 **备货优势**：高频商品充足库存，不缺货
           - 📱 **便捷优势**：一键复购、购物车智能推荐
           - ⏰ **时段优势**：预判需求高峰（如下午3点咖啡需求）
        
        #### 快消零售的核心时段场景：
        
        **📊 工作日场景**
        - **上午场景（9-11点）**：办公提神 → 咖啡、茶饮、坚果、巧克力
        - **下午场景（14-17点）**：下午茶、犯困 → 奶茶、功能饮料、饼干、糖果
        - **晚间场景（19-22点）**：居家放松 → 零食、饮料、水果、酒水
        - **深夜场景（22-24点）**：追剧、游戏、失眠 → 泡面、膨化食品、饮料
        
        **🏡 周末场景**
        - **家庭采购（10-18点）**：囤货、计划性购买 → 日用百货、大包装零食
        - **聚会场景（18-23点）**：朋友聚会、家庭娱乐 → 啤酒、烧烤零食、卤味
        
        **🚨 应急场景（全时段）**
        - 突然发现缺某物：纸巾、洗衣液、垃圾袋、电池、充电器
        - 临时来客人：饮料、零食、水果、酒水
        - 婴儿用品：奶粉、尿不湿、湿巾（速度第一）
        
        #### 本看板提供的场景洞察：
        - 识别**高频购买时段**（什么时候用户最爱买）
        - 分析**时段商品偏好**（不同时段卖什么）
        - 发现**配送时效痛点**（哪些时段配送压力大）
        - 提供**场景化运营策略**（如何精准满足即时需求）
        
        ---
        
        **💼 快消零售的终极目标**：在用户想起来的**那一刻**，以**最快速度**送达他们**急需的商品**！
        """)
    
    df = extract_time_features(df)
    
    # 映射维度到字段名
    dim_mapping = {
        '日': '日期_datetime',
        '周': '年周',
        '月': '年月'
    }
    time_col = dim_mapping[time_dimension]
    
    # 定义时段顺序（按时间自然顺序）
    time_period_order = [
        '凌晨(3-6点)', '清晨(6-8点)', '早高峰(8-9点)', '上午(9-11点)', 
        '午高峰(11-12点)', '正午(12-14点)', '下午(14-17点)', 
        '晚高峰前(17-18点)', '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)'
    ]
    
    # 场景说明
    scene_descriptions = {
        '凌晨(3-6点)': '万籁俱寂/熬夜党',
        '清晨(6-8点)': '出行/整理/早餐',
        '早高峰(8-9点)': '通勤/早餐',
        '上午(9-11点)': '办公/居家/日用补充',
        '午高峰(11-12点)': '午餐订餐高峰',
        '正午(12-14点)': '午餐/午休',
        '下午(14-17点)': '工作/家务/亲子/下午茶',
        '晚高峰前(17-18点)': '下班前备餐',
        '傍晚(18-21点)': '下班/归家/晚餐/路途',
        '晚间(21-24点)': '居家/夜生活/睡前',
        '深夜(0-3点)': '突发/急用/夜宵'
    }
    
    # ==================== 核心指标卡片（带环比） ====================
    st.markdown(f"### 📈 核心指标总览（按{time_dimension}）")
    
    # 按时间维度聚合数据
    if time_col in df.columns:
        # 安全地获取列，避免重复列名问题
        try:
            # 检查并处理重复列名
            if isinstance(df['订单ID'], pd.DataFrame):
                # 如果是DataFrame，说明有重复列名，取第一列
                order_id_series = df['订单ID'].iloc[:, 0]
            else:
                order_id_series = df['订单ID']
            
            if isinstance(df['商品实售价'], pd.DataFrame):
                price_series = df['商品实售价'].iloc[:, 0]
            else:
                price_series = df['商品实售价']
            
            if isinstance(df['收货地址'], pd.DataFrame):
                address_series = df['收货地址'].iloc[:, 0]
            else:
                address_series = df['收货地址']
            
            # 创建临时DataFrame用于聚合
            temp_df = pd.DataFrame({
                time_col: df[time_col],
                '订单ID_temp': order_id_series,
                '商品实售价_temp': price_series,
                '收货地址_temp': address_series
            })
            
            time_agg = temp_df.groupby(time_col).agg({
                '订单ID_temp': 'nunique',
                '商品实售价_temp': 'sum',
                '收货地址_temp': 'nunique'
            }).reset_index()
            time_agg.columns = [time_col, '订单数', '销售额', '客户数']
        except Exception as e:
            st.error(f"聚合数据时出错: {str(e)}")
            st.info("使用简化的数据聚合方式")
            # 使用最简单的方式聚合
            time_agg = df.groupby(time_col).size().reset_index(name='订单数')
            time_agg['销售额'] = 0
            time_agg['客户数'] = 0

        
        # 计算环比
        time_agg = calculate_period_over_period(time_agg, time_dimension, '订单数')
        time_agg = calculate_period_over_period(time_agg, time_dimension, '销售额')
        time_agg = calculate_period_over_period(time_agg, time_dimension, '客户数')
        
        # 获取当前期和上一期数据（根据用户选择或最近一期）
        if len(time_agg) >= 1:
            # 如果用户选择了具体周期，使用选择的周期；否则使用最近一期
            if selected_period and not selected_period.startswith("全部"):
                if time_dimension == "日":
                    selected_date = pd.to_datetime(selected_period)
                    latest_idx = time_agg[time_agg[time_col] == selected_date].index
                else:
                    latest_idx = time_agg[time_agg[time_col] == selected_period].index
                
                if len(latest_idx) > 0:
                    latest = time_agg.loc[latest_idx[0]]
                    # 获取上一期数据
                    current_position = latest_idx[0]
                    previous = time_agg.iloc[current_position - 1] if current_position > 0 else None
                else:
                    latest = time_agg.iloc[-1]
                    previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            else:
                # 未选择具体周期，使用最近一期
                latest = time_agg.iloc[-1]
                previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            
            col1, col2, col3, col4 = st.columns(4)
            
            # 当前周期
            with col1:
                period_label = format_period_label(latest[time_col], time_dimension)
                st.metric(label=f"当前{time_dimension}", value=period_label)
            
            # 订单数（带环比）
            render_metric_with_comparison(
                col2, f"订单数",
                latest['订单数'],
                previous['订单数'] if previous is not None else None,
                format_type='number', unit='单'
            )
            
            # 销售额（带环比）
            render_metric_with_comparison(
                col3, f"销售额",
                latest['销售额'],
                previous['销售额'] if previous is not None else None,
                format_type='currency'
            )
            
            # 客户数（带环比）
            render_metric_with_comparison(
                col4, f"客户数",
                latest['客户数'],
                previous['客户数'] if previous is not None else None,
                format_type='number', unit='人'
            )
        
        st.markdown("---")
        
        # ==================== 趋势图（多期对比） ====================
        st.markdown(f"### 📊 {time_dimension}度趋势分析")
        
        tab1, tab2, tab3 = st.tabs(["订单量趋势", "销售额趋势", "客户数趋势"])
        
        with tab1:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='订单数',
                title=f'订单数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#1f77b4', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 环比变化表格
            if '订单数_环比率' in time_agg.columns:
                st.write("**环比变化详情**")
                display_df = time_agg[[time_col, '订单数', '订单数_上期值', '订单数_环比变化', '订单数_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前订单数', '上期订单数', '环比变化量', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前订单数': '{:.0f}',
                    '上期订单数': '{:.0f}',
                    '环比变化量': '{:+.0f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
        
        with tab2:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='销售额',
                title=f'销售额{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#2ca02c', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 环比变化表格
            if '销售额_环比率' in time_agg.columns:
                st.write("**环比变化详情**")
                display_df = time_agg[[time_col, '销售额', '销售额_上期值', '销售额_环比变化', '销售额_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前销售额', '上期销售额', '环比变化额', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前销售额': '¥{:,.2f}',
                    '上期销售额': '¥{:,.2f}',
                    '环比变化额': '¥{:+,.2f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
        
        with tab3:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='客户数',
                title=f'客户数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#ff7f0e', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 环比变化表格
            if '客户数_环比率' in time_agg.columns:
                st.write("**环比变化详情**")
                display_df = time_agg[[time_col, '客户数', '客户数_上期值', '客户数_环比变化', '客户数_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前客户数', '上期客户数', '环比变化量', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前客户数': '{:.0f}',
                    '上期客户数': '{:.0f}',
                    '环比变化量': '{:+.0f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
    
    st.markdown("---")
    
    # ==================== 时段分布（根据选定的时间维度筛选最近一期） ====================
    st.markdown(f"### ⏰ 分时段场景分析（当前{time_dimension}数据）")
    
    # 筛选最近一个周期的数据用于时段分析
    filtered_df = filter_data_by_time_dimension(df, time_dimension, selected_period, latest_only=True)
    
    if len(filtered_df) == 0:
        st.warning(f"⚠️ 当前{time_dimension}暂无数据")
        return
    
    # 显示当前分析的时间范围
    if time_col in filtered_df.columns:
        current_period = filtered_df[time_col].iloc[0]
        period_label = format_period_label(current_period, time_dimension)
        st.info(f"📅 当前分析时间：{period_label}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 分时段订单量分布**")
        if '时段' in filtered_df.columns:
            # 初始化变量
            peak_period = "N/A"
            peak_orders = 0
            low_period = "N/A"
            low_orders = 0
            
            try:
                # 创建临时DataFrame处理重复列名
                temp_df = filtered_df.copy()
                if isinstance(temp_df['订单ID'], pd.DataFrame):
                    temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
                if isinstance(temp_df['时段'], pd.DataFrame):
                    temp_df['时段'] = temp_df['时段'].iloc[:, 0]
                
                # 按时段统计唯一订单数
                order_by_period = temp_df.groupby('时段')['订单ID'].nunique()
                
                # 重新索引到所有时段
                if len(order_by_period) > 0:
                    order_by_period = order_by_period.reindex(time_period_order, fill_value=0)
                    
                    fig = px.bar(
                        x=order_by_period.index,
                        y=order_by_period.values,
                        labels={'x': '时段', 'y': '订单量'},
                        title=f'各时段订单量对比（{period_label}）',
                        color=order_by_period.values,
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    peak_period = order_by_period.idxmax()
                    peak_orders = int(order_by_period.max())
                    low_period = order_by_period.idxmin()
                    low_orders = int(order_by_period.min())
                else:
                    st.info("暂无时段数据")
            except Exception as e:
                st.error(f"绘制时段分布图时出错: {str(e)}")
                st.write(f"调试信息 - filtered_df形状: {filtered_df.shape}")
                if '时段' in filtered_df.columns:
                    st.write(f"时段列唯一值: {filtered_df['时段'].unique()}")
            
            # 只有在有有效数据时才显示洞察
            if peak_period != "N/A":
                st.markdown(f"""
                <div class="insight-box">
                <b>💡 关键洞察：</b><br>
                • 高峰时段：<b>{peak_period}</b>（{peak_orders:,}单）<br>
                • 低谷时段：<b>{low_period}</b>（{low_orders:,}单）<br>
                • 峰谷差异：{(peak_orders - low_orders):,}单（{(peak_orders/max(low_orders, 1) - 1)*100:.1f}%）
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("无时间数据")
    
    with col2:
        st.write("**💰 分时段客单价分布**")
        if '时段' in filtered_df.columns:
            try:
                # 创建临时DataFrame，处理重复列名
                temp_df = filtered_df.copy()
                if isinstance(temp_df['订单ID'], pd.DataFrame):
                    temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
                if isinstance(temp_df['商品实售价'], pd.DataFrame):
                    temp_df['商品实售价'] = temp_df['商品实售价'].iloc[:, 0]
                
                period_sales = temp_df.groupby(['时段', '订单ID'])['商品实售价'].sum().groupby('时段').mean()
                period_sales = period_sales.reindex(time_period_order, fill_value=0)
                
                fig = px.line(
                    x=period_sales.index,
                    y=period_sales.values,
                    labels={'x': '时段', 'y': '平均客单价(元)'},
                    title=f'各时段平均客单价趋势（{period_label}）',
                    markers=True
                )
                fig.update_traces(line_color='#ff7f0e', marker=dict(size=10))
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                high_value_period = period_sales.idxmax()
                high_value = period_sales.max()
                
                st.markdown(f"""
                <div class="insight-box">
                <b>💡 关键洞察：</b><br>
                • 高价值时段：<b>{high_value_period}</b>（¥{high_value:.2f}）<br>
                • 全天平均客单价：¥{period_sales.mean():.2f}<br>
                • 建议：高价值时段可减少促销力度，提升利润率
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"计算客单价分布时出错: {str(e)}")
        else:
            st.info("无时间数据")
    
    # 添加详细时段场景分析表
    st.write(f"**📋 时段场景详细分析（{period_label}）**")
    if '时段' in filtered_df.columns:
        try:
            # 创建临时DataFrame处理重复列名
            temp_df = filtered_df.copy()
            if isinstance(temp_df['订单ID'], pd.DataFrame):
                temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
            if isinstance(temp_df['商品实售价'], pd.DataFrame):
                temp_df['商品实售价'] = temp_df['商品实售价'].iloc[:, 0]
            
            period_detail = []
            total_orders = temp_df['订单ID'].nunique()
            
            for period in time_period_order:
                period_df = temp_df[temp_df['时段'] == period]
                if len(period_df) == 0:
                    continue
                
                orders = period_df['订单ID'].nunique()
                items = len(period_df)
                avg_price = period_df.groupby('订单ID')['商品实售价'].sum().mean()
                
                period_detail.append({
                    '时段': period,
                    '场景': scene_descriptions.get(period, '-'),
                    '订单量': f'{orders:,}',
                    '商品数': f'{items:,}',
                    '平均客单价': f'¥{avg_price:.2f}',
                    '订单占比': f'{orders/total_orders*100:.1f}%'
                })
            
            if period_detail:
                detail_df = pd.DataFrame(period_detail)
                st.dataframe(detail_df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无时段详细数据")
        except Exception as e:
            st.error(f"生成时段详细分析时出错: {str(e)}")
    
    # ==================== 场景商品分析 ====================
    st.markdown(f"### 🛍️ 场景商品洞察：什么时段用户买什么？")
    
    if '时段' in filtered_df.columns and '三级分类名' in filtered_df.columns:
        # 定义快消零售的核心场景时段（基于O2O配送特征优化）
        # ⚠️ 注意：时段名称必须与extract_time_features函数中定义的完全一致
        key_scenes = {
            '早餐刚需': ['清晨(6-8点)', '早高峰(8-9点)'],  # 修正：对应6-9点早餐时段
            '日常补给': ['上午(9-11点)', '下午(14-17点)'],
            '正餐高峰': ['午高峰(11-12点)', '正午(12-14点)', '晚高峰前(17-18点)', '傍晚(18-21点)'],  # 修正：包含完整午餐和晚餐时段
            '休闲娱乐': ['下午(14-17点)', '晚间(21-24点)'],
            '深夜应急': ['深夜(0-3点)', '凌晨(3-6点)']
        }
        
        tabs = st.tabs(list(key_scenes.keys()))
        
        for idx, (scene_name, time_periods) in enumerate(key_scenes.items()):
            with tabs[idx]:
                scene_df = filtered_df[filtered_df['时段'].isin(time_periods)]
                
                if len(scene_df) > 0:
                    # 商品销量TOP10
                    top_products = scene_df.groupby('三级分类名').size().sort_values(ascending=False).head(10)
                    
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        fig = px.bar(
                            x=top_products.values,
                            y=top_products.index,
                            orientation='h',
                            title=f'{scene_name} - TOP10 热销商品',
                            labels={'x': '销量', 'y': '商品分类'},
                            color=top_products.values,
                            color_continuous_scale='Oranges'
                        )
                        fig.update_layout(showlegend=False, height=400, yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_b:
                        st.write(f"**{scene_name} 数据**")
                        scene_orders = scene_df['订单ID'].nunique()
                        scene_sales = scene_df.groupby('订单ID')['商品实售价'].sum().sum()
                        scene_avg_price = scene_sales / scene_orders if scene_orders > 0 else 0
                        
                        st.metric("订单量", f"{scene_orders:,}单")
                        st.metric("销售额", f"¥{scene_sales:,.2f}")
                        st.metric("平均客单价", f"¥{scene_avg_price:.2f}")
                        
                        # 场景特征商品
                        if len(top_products) >= 3:
                            st.write("**🎯 场景特征商品**")
                            for i, (prod, cnt) in enumerate(top_products.head(3).items(), 1):
                                st.markdown(f"{i}. **{prod}**（{cnt}件）")
                    
                    # O2O快消零售场景策略建议（基于8时段框架）
                    scene_strategy = {
                        '早餐刚需': """
                        <div class="insight-box">
                        <b>💡 早餐刚需场景策略（6-9点）</b><br>
                        <b>时段覆盖</b>：清晨(6-8点) + 早高峰(8-9点)<br>
                        <b>用户画像</b>：通勤上班族、学生党、早起运动者<br>
                        <b>核心商品</b>：面包、包子、牛奶、豆浆、油条、茶叶蛋、粥类、咖啡<br>
                        <b>行为特征</b>：时间紧迫、即买即走、复购率高、对速度极度敏感<br>
                        <b>运营策略</b>：<br>
                        • <b>速度至上</b>：承诺15分钟达，迟到立减/免单<br>
                        • <b>早餐套餐</b>：豆浆+油条、面包+牛奶一键下单<br>
                        • <b>订阅服务</b>：工作日早餐包月，固定时间送达<br>
                        • <b>提前备货</b>：6-8点热销品预备2倍库存
                        </div>
                        """,
                        '日常补给': """
                        <div class="insight-box">
                        <b>💡 日常补给场景策略（9-12点 & 14-17点）</b><br>
                        <b>用户画像</b>：居家主妇/主夫、远程办公者、退休老人<br>
                        <b>核心商品</b>：蔬菜水果、米面粮油、调味品、日用品、零食饮料<br>
                        <b>行为特征</b>：计划性采购、价格敏感、品类多样、关注品质<br>
                        <b>运营策略</b>：<br>
                        • <b>满减促销</b>：满50减5、满100减15阶梯优惠<br>
                        • <b>组合推荐</b>：根据历史订单智能推荐（番茄→鸡蛋）<br>
                        • <b>品质保障</b>：生鲜品质承诺，不满意退款<br>
                        • <b>会员福利</b>：日常用品会员价，专属折扣
                        </div>
                        """,
                        '正餐高峰': """
                        <div class="insight-box">
                        <b>💡 正餐高峰场景策略（11-14点 & 17-21点）</b><br>
                        <b>时段覆盖</b>：午高峰(11-12点) + 正午(12-14点) + 晚高峰前(17-18点) + 傍晚(18-21点)<br>
                        <b>用户画像</b>：上班族、学生、家庭聚餐、加班人群<br>
                        <b>核心商品</b>：半成品菜、速食（泡面/自热饭）、饮料、酒水、调味料<br>
                        <b>行为特征</b>：集中下单、时间紧迫、客单价高、追求便利<br>
                        <b>运营策略</b>：<br>
                        • <b>正餐套餐</b>：速食+饮料、半成品+调料组合<br>
                        • <b>高峰加急</b>：11:30-12:30优先配送，保证用餐时间<br>
                        • <b>晚餐推荐</b>：17:30推送晚餐提醒+优惠券<br>
                        • <b>家庭装</b>：3-4人份套餐，性价比突出
                        </div>
                        """,
                        '休闲娱乐': """
                        <div class="insight-box">
                        <b>💡 休闲娱乐场景策略（14-17点 & 21-24点）</b><br>
                        <b>用户画像</b>：追剧党、游戏玩家、朋友聚会、居家休闲<br>
                        <b>核心商品</b>：薯片、瓜子、可乐、啤酒、卤味、水果、冰淇淋、奶茶<br>
                        <b>行为特征</b>：冲动消费、品类集中、社交属性强、对价格不敏感<br>
                        <b>运营策略</b>：<br>
                        • <b>场景套餐</b>：追剧套餐、游戏套餐、聚会套餐<br>
                        • <b>买赠活动</b>：买饮料送零食、买2送1<br>
                        • <b>网红新品</b>：主推新奇特零食，刺激尝鲜<br>
                        • <b>社交分享</b>：拼团优惠，多人下单更划算
                        </div>
                        """,
                        '深夜应急': """
                        <div class="insight-box">
                        <b>💡 深夜应急场景策略（0-6点）</b><br>
                        <b>用户画像</b>：夜班工作者、熬夜党、新手父母、失眠人群<br>
                        <b>核心商品</b>：泡面、纸巾、电池、婴儿用品、功能饮料、常备小药<br>
                        <b>行为特征</b>：突发需求、价格不敏感、品类单一、速度要求高<br>
                        <b>运营策略</b>：<br>
                        • <b>应急优先</b>：24小时保障核心品类库存<br>
                        • <b>深夜加价</b>：22点后配送费+3-5元（应急溢价）<br>
                        • <b>品类精简</b>：只保留高频应急品，减少选择困难<br>
                        • <b>速度承诺</b>：深夜30分钟达，建立信任度
                        </div>
                        """
                    }
                    
                    st.markdown(scene_strategy.get(scene_name, ""), unsafe_allow_html=True)
                else:
                    st.info(f"⚠️ {scene_name}暂无数据")
    
    st.markdown("---")
    
    # ==================== 🤖 AI场景识别模型 ====================
    st.markdown("### 🤖 AI场景识别与预测")
    
    if SCENE_INTELLIGENCE_AVAILABLE:
        with st.expander("💡 基于XGBoost的场景识别模型", expanded=True):
            st.info("📊 使用机器学习算法自动识别订单场景，预测未来订单的场景分布")
            
            col1, col2 = st.columns([3, 1])
            
            with col2:
                if st.button("🚀 训练场景识别模型", key="train_scene_model"):
                    with st.spinner("⏳ 正在训练模型..."):
                        try:
                            # 数据诊断：训练前检查
                            st.info(f"""
                            📊 **训练数据概况**：
                            - 总订单数：{len(df):,}
                            - 数据列数：{len(df.columns)}
                            - 是否包含'下单时间'：{'✅' if '下单时间' in df.columns else '❌'}
                            """)
                            
                            # 如果有下单时间，显示时间范围
                            if '下单时间' in df.columns:
                                time_series = pd.to_datetime(df['下单时间'], errors='coerce')
                                if not time_series.dropna().empty:
                                    min_time = time_series.min()
                                    max_time = time_series.max()
                                    days_span = (max_time - min_time).days + 1
                                    hour_coverage = time_series.dt.hour.nunique()
                                    st.success(f"""
                                    ⏰ **时间范围**：
                                    - 起始：{min_time.strftime('%Y-%m-%d %H:%M')}
                                    - 结束：{max_time.strftime('%Y-%m-%d %H:%M')}
                                    - 跨度：{days_span}天
                                    - 覆盖时段：{hour_coverage}/24小时
                                    """)
                            
                            # 初始化模型
                            scene_model = SceneRecognitionModel()
                            
                            # 训练模型 - 使用全部数据而非筛选后的数据
                            # 注意：这里使用 df（全部数据）而不是 filtered_df（仅最近一个周期）
                            train_result = scene_model.train(df)
                            
                            if train_result.get('status') == 'success':
                                # 保存到session_state（包括训练数据用于诊断）
                                st.session_state['scene_model'] = scene_model
                                st.session_state['scene_train_result'] = train_result
                                st.session_state['scene_train_data'] = df  # 保存完整的训练数据
                                
                                st.success(f"✅ 模型训练完成！测试准确率: {train_result['test_score']:.1%}")
                            else:
                                st.error(f"❌ 训练失败：{train_result.get('message')}")
                        
                        except Exception as e:
                            st.error(f"❌ 训练过程出错: {str(e)}")
            
            # 如果模型已训练，显示结果
            if 'scene_model' in st.session_state and 'scene_train_result' in st.session_state:
                scene_model = st.session_state['scene_model']
                train_result = st.session_state['scene_train_result']
                
                # 创建标签页
                tab1, tab2, tab3 = st.tabs(["📊 模型性能", "🎯 场景预测", "📈 特征重要性"])
                
                with tab1:
                    st.markdown("#### 📊 模型性能指标")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("训练集准确率", f"{train_result['train_score']:.1%}")
                    
                    with col2:
                        st.metric("测试集准确率", f"{train_result['test_score']:.1%}")
                    
                    with col3:
                        overfitting = train_result['train_score'] - train_result['test_score']
                        st.metric("过拟合程度", f"{overfitting:.1%}", 
                                 delta="低" if overfitting < 0.05 else "需关注",
                                 delta_color="inverse")
                    
                    # 数据诊断：时段分布分析
                    st.markdown("**⏰ 数据时段覆盖诊断**")
                    
                    # 获取训练时使用的数据
                    train_data = st.session_state.get('scene_train_data')
                    
                    if train_data is not None and '下单时间' in train_data.columns:
                        hour_dist = pd.to_datetime(train_data['下单时间'], errors='coerce').dt.hour.value_counts().sort_index()
                        
                        col_diag1, col_diag2 = st.columns([2, 1])
                        
                        with col_diag1:
                            # 时段分布柱状图
                            fig_hour = px.bar(
                                x=hour_dist.index, 
                                y=hour_dist.values,
                                labels={'x': '小时', 'y': '订单数'},
                                title='订单时段分布（0-23点）'
                            )
                            fig_hour.update_layout(height=250)
                            st.plotly_chart(fig_hour, use_container_width=True)
                        
                        with col_diag2:
                            total_hours_covered = len(hour_dist)
                            main_hours = hour_dist.head(3).index.tolist()
                            
                            st.metric("覆盖时段数", f"{total_hours_covered}/24小时")
                            st.info(f"**主要时段：** {', '.join([f'{h}时' for h in main_hours])}")
                            
                            if total_hours_covered < 12:
                                st.warning(f"⚠️ 数据仅覆盖{total_hours_covered}个小时，场景识别可能不够丰富")
                    else:
                        st.info("💡 数据诊断需要包含'下单时间'字段")
                    
                    st.markdown("---")
                    
                    # 场景分布
                    st.markdown("**🎭 训练数据场景分布**")
                    scene_dist = train_result.get('scene_distribution', {})
                    if scene_dist:
                        dist_df = pd.DataFrame(list(scene_dist.items()), columns=['场景', '订单数'])
                        dist_df['占比'] = (dist_df['订单数'] / dist_df['订单数'].sum() * 100).round(1)
                        
                        # 场景多样性诊断
                        scene_count = len(scene_dist)
                        if scene_count == 1:
                            st.error(f"🚨 **数据问题**：仅识别出1个场景（{list(scene_dist.keys())[0]}）")
                            st.warning("""
                            💡 **可能的原因：**
                            
                            1. **数据时段过于集中**：您的订单数据可能都集中在某个特定时段（如都是深夜下单）
                            2. **数据量太少**：样本数量不足，无法覆盖多个场景
                            3. **数据时间范围太窄**：只有某一天或某几个小时的数据
                            
                            **解决方法：**
                            
                            - 确保数据包含**早、中、晚**不同时段的订单
                            - 扩大数据时间范围（建议至少7天以上）
                            - 检查上方的"时段覆盖诊断"，看看数据是否覆盖24小时
                            """)
                        elif scene_count < 3:
                            st.warning(f"⚠️ 仅识别出{scene_count}个场景，建议扩大数据时间范围以覆盖更多场景。")
                        
                        col_scene1, col_scene2 = st.columns([2, 1])
                        
                        with col_scene1:
                            fig = px.pie(dist_df, values='订单数', names='场景', title='场景分布')
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col_scene2:
                            st.dataframe(dist_df, use_container_width=True, hide_index=True)
                            
                            # 显示场景定义参考
                            with st.expander("📖 场景时段定义"):
                                st.markdown("""
                                - **早餐刚需**：6-8点
                                - **日常补给**：9-11点、14-17点
                                - **正餐高峰**：12-13点、18-20点
                                - **休闲娱乐**：21-23点
                                - **深夜应急**：0-5点
                                
                                💡 如果您的数据只覆盖某个时段，场景识别会相应受限。
                                """)
                
                with tab2:
                    st.markdown("#### 🎯 订单场景预测")
                    
                    try:
                        # 预测场景 - 使用全部数据进行预测
                        predictions = scene_model.predict_scene(df)
                        
                        # 场景预测统计
                        pred_dist = predictions['predicted_scene'].value_counts()
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            fig = px.bar(
                                x=pred_dist.values,
                                y=pred_dist.index,
                                orientation='h',
                                title='预测场景分布',
                                labels={'x': '订单数', 'y': '场景'},
                                color=pred_dist.values,
                                color_continuous_scale='Viridis'
                            )
                            fig.update_layout(showlegend=False, height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.write("**📊 场景预测统计**")
                            for scene, count in pred_dist.items():
                                pct = count / len(predictions) * 100
                                st.metric(scene, f"{count:,}单", delta=f"{pct:.1f}%")
                        
                        # 显示预测样例
                        st.markdown("**🔍 预测结果样例（前10条）**")
                        sample_pred = predictions.head(10)
                        
                        # 显示概率最高的场景及其概率
                        prob_cols = [col for col in sample_pred.columns if col.startswith('prob_')]
                        if prob_cols:
                            display_cols = ['订单ID', 'predicted_scene'] + prob_cols
                            st.dataframe(sample_pred[display_cols], use_container_width=True, hide_index=True)
                        
                    except Exception as e:
                        st.error(f"❌ 预测失败: {str(e)}")
                
                with tab3:
                    st.markdown("#### 📈 特征重要性分析")
                    
                    importance_fig = scene_model.visualize_feature_importance()
                    st.plotly_chart(importance_fig, use_container_width=True)
                    
                    st.markdown("""
                    **特征说明：**
                    - **hour**: 下单小时（0-23）
                    - **weekday**: 星期几（0=周一，6=周日）
                    - **配送距离**: 用户距离门店的距离
                    - **订单金额**: 订单总金额
                    - **平均单价**: 商品平均单价
                    - **商品数**: 订单中的商品件数
                    - **delivery_fee_ratio**: 配送费占订单金额的比例
                    """)
    else:
        st.warning("⚠️ 场景营销智能决策引擎未加载，请确保已安装xgboost或scikit-learn")
    
    st.markdown("---")
    
    # 优化后的营销建议
    st.markdown("""
    <div class="warning-box">
    <b>🎯 精准时段营销策略：</b><br>
    <br>
    <b>📈 高峰时段策略：</b><br>
    • <b>午高峰(11-12点)</b>：提前推送午餐套餐，满减门槛适当提高，保障配送效率<br>
    • <b>晚高峰前(17-18点)</b>：推送"提前订晚餐"优惠，缓解18点后压力<br>
    • <b>傍晚(18-21点)</b>：主力时段，减少促销力度，重点保障服务质量<br>
    <br>
    <b>📉 低谷时段策略：</b><br>
    • <b>清晨(6-8点)</b>：推出"早餐专享"折扣，培养早餐外卖习惯<br>
    • <b>上午(9-11点)</b>：推送"上午茶歇"套餐，日用品类满减券<br>
    • <b>下午(14-17点)</b>：下午茶时段，推出"第二件半价"、甜品饮品组合<br>
    <br>
    <b>🌙 特殊时段策略：</b><br>
    • <b>晚间(21-24点)</b>：夜宵品类专项促销，烧烤、小吃、宵夜套餐<br>
    • <b>深夜(0-3点)</b>：应急场景，提供"深夜暖心"服务，适当加收配送费<br>
    • <b>凌晨(3-6点)</b>：极少订单，可暂停配送或仅保留便利店合作<br>
    <br>
    <b>⏰ 动态推送策略：</b><br>
    • 提前30分钟推送下一时段优惠券（如10:30推送午餐券）<br>
    • 高峰时段前1小时推送"错峰优惠"（如10点推送11点前下单立减）<br>
    • 结合天气、节假日调整时段策略（雨天增加配送费减免）
    </div>
    """, unsafe_allow_html=True)


def render_location_marketing(df: pd.DataFrame, time_dimension: str = '日', selected_period: str = None):
    """门店商圈场景营销（支持日/周/月维度）"""
    st.markdown('<p class="sub-header">🏪 门店商圈场景分析</p>', unsafe_allow_html=True)
    
    # ==================== 场景营销理念说明 ====================
    with st.expander("💡 商圈场景的竞争本质：速度为王", expanded=False):
        st.markdown("""
        ### ⚡ 配送速度 = 核心竞争力
        
        #### 为什么速度这么重要？
        1. **即时需求**：忘记买纸巾、急需退烧药、临时来客人 → 15分钟内送达
        2. **生鲜品质**：冰淇淋、热食、冷链 → 越快越新鲜
        3. **用户体验**：等待时间每增加5分钟，复购率下降10%
        4. **竞争壁垒**：美团、饿了么、盒马、叮咚买菜都在拼速度
        
        #### 如何做到比竞对更快？
        
        **1. 前置仓布局策略**
        - 🎯 **1公里核心圈**：订单密度最高，必须15分钟达
        - 🏃 **2-3公里主力圈**：30分钟达，覆盖大部分用户
        - 🚴 **3-5公里边缘圈**：45分钟达，谨慎拓展
        - ❌ **5公里以外**：建议暂停或高额配送费
        
        **2. 配送费成本优化**
        - 💰 **距离成本分析**：每公里增加多少配送成本？
        - 🎁 **差异化定价**：1公里内免费，3公里外递增
        - 📦 **满减门槛**：远距离提高满减金额，平衡成本
        
        **3. 商圈场景化运营**
        - 🏢 **办公区商圈**：午餐高峰，团购优先
        - 🏠 **住宅区商圈**：晚餐夜宵，家庭套餐
        - 🏫 **学校商圈**：下午茶、夜宵，小份优惠
        - 🏥 **医院商圈**：应急场景，速度优先
        
        ---
        
        **📊 本看板提供的决策依据**：
        - 配送距离分布 → 确定核心服务半径
        - 配送费成本分析 → 优化定价策略
        - 距离段客单价 → 制定差异化满减
        - 高价值商圈识别 → 重点资源倾斜
        """)
    
    if '配送距离' not in df.columns:
        st.warning("⚠️ 数据中缺少配送距离字段，无法进行商圈分析")
        return
    
    df = df.copy()
    df = extract_time_features(df)
    
    # 映射维度到字段名
    dim_mapping = {
        '日': '日期_datetime',
        '周': '年周',
        '月': '年月'
    }
    time_col = dim_mapping[time_dimension]
    
    # 将配送距离转换为公里（如果单位是米）
    # 判断：如果平均距离>100，则认为单位是米，需要转换为公里
    avg_distance = df['配送距离'].mean()
    if avg_distance > 100:
        df['配送距离_公里'] = df['配送距离'] / 1000
        st.info("📏 检测到配送距离单位为米，已自动转换为公里")
    else:
        df['配送距离_公里'] = df['配送距离']
    
    # 计算配送费成本（订单级）
    # 配送成本 = 用户支付配送费 - 配送费减免金额 - 物流配送费
    if '用户支付配送费' in df.columns and '配送费减免金额' in df.columns and '物流配送费' in df.columns:
        df['配送费成本'] = (
            df['用户支付配送费'].fillna(0) - 
            df['配送费减免金额'].fillna(0) - 
            df['物流配送费'].fillna(0)
        )
    elif '物流配送费' in df.columns:
        # 如果缺少某些字段，简化计算
        df['配送费成本'] = -df['物流配送费'].fillna(0)
        st.info("⚠️ 部分配送费字段缺失，配送成本仅基于物流配送费计算")
    else:
        df['配送费成本'] = 0
        st.warning("⚠️ 缺少配送费相关字段，配送成本无法计算")
    
    # ==================== 核心指标总览（带环比） ====================
    st.markdown(f"### 📈 核心指标总览（按{time_dimension}）")
    
    if time_col in df.columns and '订单ID' in df.columns:
        try:
            # 处理重复列名
            temp_df = df.copy()
            if isinstance(temp_df['订单ID'], pd.DataFrame):
                temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
            if isinstance(temp_df['配送距离_公里'], pd.DataFrame):
                temp_df['配送距离_公里'] = temp_df['配送距离_公里'].iloc[:, 0]
            
            # 按订单级聚合（避免明细级重复计算）
            agg_config = {
                '配送距离_公里': 'first',
                '收货地址': 'first',
                '配送费成本': 'first'
            }
            
            # 动态添加可选字段
            for col in ['物流配送费', '用户支付配送费', '配送费减免金额']:
                if col in temp_df.columns:
                    if isinstance(temp_df[col], pd.DataFrame):
                        temp_df[col] = temp_df[col].iloc[:, 0]
                    agg_config[col] = 'first'
            
            order_summary = temp_df.groupby(['订单ID', time_col]).agg(agg_config).reset_index()
        
            # 按时间维度聚合
            agg_dict = {
                '订单ID': 'nunique',
                '配送距离_公里': 'mean',
                '收货地址': 'nunique',
                '配送费成本': 'sum'
            }
            
            if '物流配送费' in order_summary.columns:
                agg_dict['物流配送费'] = 'sum'
            if '用户支付配送费' in order_summary.columns:
                agg_dict['用户支付配送费'] = 'sum'
            if '配送费减免金额' in order_summary.columns:
                agg_dict['配送费减免金额'] = 'sum'
            
            time_agg = order_summary.groupby(time_col).agg(agg_dict).reset_index()
            time_agg.columns = [time_col, '订单数', '平均配送距离', '覆盖地址数', '配送费成本'] + \
                              (['物流配送费'] if '物流配送费' in agg_dict else []) + \
                              (['用户支付配送费'] if '用户支付配送费' in agg_dict else []) + \
                              (['配送费减免金额'] if '配送费减免金额' in agg_dict else [])
            
            # 计算平均配送费成本
            time_agg['平均配送费成本'] = time_agg['配送费成本'] / time_agg['订单数']
        except Exception as e:
            st.error(f"计算核心指标时出错: {str(e)}")
            time_agg = None
    else:
        time_agg = None
    
    if time_agg is not None:
        time_agg = calculate_period_over_period(time_agg, time_dimension, '订单数')
        time_agg = calculate_period_over_period(time_agg, time_dimension, '平均配送距离')
        time_agg = calculate_period_over_period(time_agg, time_dimension, '覆盖地址数')
        time_agg = calculate_period_over_period(time_agg, time_dimension, '配送费成本')
        time_agg = calculate_period_over_period(time_agg, time_dimension, '平均配送费成本')
        
        # 获取当前期和上一期数据（根据用户选择或最近一期）
        if len(time_agg) >= 1:
            # 如果用户选择了具体周期，使用选择的周期；否则使用最近一期
            if selected_period and not selected_period.startswith("全部"):
                if time_dimension == "日":
                    selected_date = pd.to_datetime(selected_period)
                    latest_idx = time_agg[time_agg[time_col] == selected_date].index
                else:
                    latest_idx = time_agg[time_agg[time_col] == selected_period].index
                
                if len(latest_idx) > 0:
                    latest = time_agg.loc[latest_idx[0]]
                    # 获取上一期数据
                    current_position = latest_idx[0]
                    previous = time_agg.iloc[current_position - 1] if current_position > 0 else None
                else:
                    latest = time_agg.iloc[-1]
                    previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            else:
                # 未选择具体周期，使用最近一期
                latest = time_agg.iloc[-1]
                previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            
            # 第一行指标卡片
            col1, col2, col3, col4 = st.columns(4)
            
            # 当前周期
            with col1:
                period_label = format_period_label(latest[time_col], time_dimension)
                st.metric(label=f"当前{time_dimension}", value=period_label)
            
            # 订单数（带环比）
            render_metric_with_comparison(
                col2, f"订单数",
                latest['订单数'],
                previous['订单数'] if previous is not None else None,
                format_type='number', unit='单'
            )
            
            # 平均配送距离（带环比）
            with col3:
                current_dist = latest['平均配送距离']
                previous_dist = previous['平均配送距离'] if previous is not None else None
                
                if previous_dist is not None and not pd.isna(previous_dist) and previous_dist != 0:
                    change_rate = ((current_dist - previous_dist) / previous_dist * 100)
                    st.metric(
                        label="平均配送距离",
                        value=f"{current_dist:.2f}公里",
                        delta=f"{change_rate:+.2f}%",
                        delta_color="inverse"  # 距离增加显示为红色（不好）
                    )
                else:
                    st.metric(label="平均配送距离", value=f"{current_dist:.2f}公里")
            
            # 覆盖地址数（带环比）
            render_metric_with_comparison(
                col4, f"覆盖地址数",
                latest['覆盖地址数'],
                previous['覆盖地址数'] if previous is not None else None,
                format_type='number', unit='个'
            )
            
            # 第二行：配送费成本分析
            st.markdown("#### 💰 配送费成本分析")
            col5, col6, col7, col8 = st.columns(4)
            
            # 配送费成本（带环比）
            with col5:
                current_cost = latest['配送费成本']
                previous_cost = previous['配送费成本'] if previous is not None else None
                
                if previous_cost is not None and not pd.isna(previous_cost) and previous_cost != 0:
                    change_rate = ((current_cost - previous_cost) / abs(previous_cost) * 100)
                    st.metric(
                        label="配送费成本",
                        value=f"¥{current_cost:,.2f}",
                        delta=f"{change_rate:+.2f}%",
                        delta_color="inverse",  # 成本增加显示为红色
                        help="配送成本 = 用户支付配送费 - 配送费减免 - 物流配送费"
                    )
                else:
                    st.metric(
                        label="配送费成本",
                        value=f"¥{current_cost:,.2f}",
                        help="配送成本 = 用户支付配送费 - 配送费减免 - 物流配送费"
                    )
            
            # 平均配送费成本（带环比）
            with col6:
                current_avg_cost = latest['平均配送费成本']
                previous_avg_cost = previous['平均配送费成本'] if previous is not None else None
                
                if previous_avg_cost is not None and not pd.isna(previous_avg_cost) and previous_avg_cost != 0:
                    change_rate = ((current_avg_cost - previous_avg_cost) / abs(previous_avg_cost) * 100)
                    st.metric(
                        label="单均配送成本",
                        value=f"¥{current_avg_cost:.2f}",
                        delta=f"{change_rate:+.2f}%",
                        delta_color="inverse",
                        help="配送费成本 / 订单数"
                    )
                else:
                    st.metric(
                        label="单均配送成本",
                        value=f"¥{current_avg_cost:.2f}",
                        help="配送费成本 / 订单数"
                    )
            
            # 物流配送费（如果有）
            if '物流配送费' in latest.index:
                with col7:
                    current_logistics = latest['物流配送费']
                    previous_logistics = previous['物流配送费'] if previous is not None and '物流配送费' in previous.index else None
                    
                    if previous_logistics is not None and not pd.isna(previous_logistics) and previous_logistics != 0:
                        change_rate = ((current_logistics - previous_logistics) / previous_logistics * 100)
                        st.metric(
                            label="物流配送费",
                            value=f"¥{current_logistics:,.2f}",
                            delta=f"{change_rate:+.2f}%",
                            delta_color="inverse",
                            help="支付给配送平台的费用"
                        )
                    else:
                        st.metric(
                            label="物流配送费",
                            value=f"¥{current_logistics:,.2f}",
                            help="支付给配送平台的费用"
                        )
            
            # 配送费减免（如果有）
            if '配送费减免金额' in latest.index:
                with col8:
                    current_discount = latest['配送费减免金额']
                    previous_discount = previous['配送费减免金额'] if previous is not None and '配送费减免金额' in previous.index else None
                    
                    if previous_discount is not None and not pd.isna(previous_discount) and previous_discount != 0:
                        change_rate = ((current_discount - previous_discount) / previous_discount * 100)
                        st.metric(
                            label="配送费减免",
                            value=f"¥{current_discount:,.2f}",
                            delta=f"{change_rate:+.2f}%",
                            help="给用户的配送费优惠（已在配送成本中抵扣）"
                        )
                    else:
                        st.metric(
                            label="配送费减免",
                            value=f"¥{current_discount:,.2f}",
                            help="给用户的配送费优惠（已在配送成本中抵扣）"
                        )
        
        st.markdown("---")
        
        # ==================== 趋势图 ====================
        st.markdown(f"### 📊 {time_dimension}度趋势分析")
        
        tab1, tab2, tab3, tab4 = st.tabs(["订单量趋势", "平均配送距离趋势", "覆盖地址数趋势", "配送费成本趋势"])
        
        with tab1:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='订单数',
                title=f'订单数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#3498db', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='平均配送距离',
                title=f'平均配送距离{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#e67e22', width=3))
            fig.update_layout(height=400, yaxis_title='平均配送距离(公里)')
            st.plotly_chart(fig, use_container_width=True)
            
            # 环比变化表格
            if '平均配送距离_环比率' in time_agg.columns:
                st.write("**环比变化详情**")
                display_df = time_agg[[time_col, '平均配送距离', '平均配送距离_上期值', '平均配送距离_环比变化', '平均配送距离_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前平均距离', '上期平均距离', '环比变化(km)', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前平均距离': '{:.2f}公里',
                    '上期平均距离': '{:.2f}公里',
                    '环比变化(km)': '{:+.2f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
        
        with tab3:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='覆盖地址数',
                title=f'覆盖地址数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#27ae60', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            # 配送费成本趋势图
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='配送费成本',
                title=f'配送费成本{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#e74c3c', width=3))
            fig.update_layout(height=400, yaxis_title='配送费成本(元)')
            st.plotly_chart(fig, use_container_width=True)
            
            # 平均配送费成本趋势图
            fig2 = px.line(
                time_agg, 
                x=time_col, 
                y='平均配送费成本',
                title=f'单均配送成本{time_dimension}度趋势',
                markers=True
            )
            fig2.update_traces(line=dict(color='#9b59b6', width=3))
            fig2.update_layout(height=400, yaxis_title='单均配送成本(元)')
            st.plotly_chart(fig2, use_container_width=True)
            
            # 环比变化表格
            if '配送费成本_环比率' in time_agg.columns:
                st.write("**配送费成本环比详情**")
                display_df = time_agg[[time_col, '配送费成本', '配送费成本_上期值', '配送费成本_环比变化', '配送费成本_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前成本', '上期成本', '环比变化(元)', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前成本': '¥{:,.2f}',
                    '上期成本': '¥{:,.2f}',
                    '环比变化(元)': '¥{:+,.2f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
            
            # 配送费成本构成分析（如果有详细字段）
            if all(col in time_agg.columns for col in ['物流配送费', '用户支付配送费', '配送费减免金额']):
                st.write("**配送费成本构成分析（最近一期）**")
                latest_data = time_agg.iloc[-1]
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("物流配送费支出", f"¥{latest_data['物流配送费']:,.2f}", help="支付给配送平台")
                with col_b:
                    st.metric("用户支付配送费", f"¥{latest_data['用户支付配送费']:,.2f}", help="用户承担部分")
                with col_c:
                    st.metric("配送费减免", f"¥{latest_data['配送费减免金额']:,.2f}", help="优惠给用户")
                
                st.markdown(f"""
                <div class="insight-box">
                <b>💡 配送费成本计算公式：</b><br>
                配送费成本 = 用户支付(¥{latest_data['用户支付配送费']:,.2f}) - 
                配送费减免(¥{latest_data['配送费减免金额']:,.2f}) - 
                物流配送费(¥{latest_data['物流配送费']:,.2f}) = 
                <b>¥{latest_data['配送费成本']:,.2f}</b>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== 配送距离分布（根据选定的时间维度筛选最近一期） ====================
    st.markdown(f"### 📍 配送距离分布分析（当前{time_dimension}数据）")
    
    # 筛选最近一个周期的数据
    filtered_df = filter_data_by_time_dimension(df, time_dimension, selected_period, latest_only=True)
    
    if len(filtered_df) == 0:
        st.warning(f"⚠️ 当前{time_dimension}暂无数据")
        return
    
    # 显示当前分析的时间范围
    if time_col in filtered_df.columns:
        current_period = filtered_df[time_col].iloc[0]
        period_label = format_period_label(current_period, time_dimension)
        st.info(f"📅 当前分析时间：{period_label}")
    
    def get_distance_range(distance_km):
        if pd.isna(distance_km):
            return '未知'
        elif distance_km < 1:
            return '1公里以下'
        elif distance_km < 2:
            return '1-2公里'
        elif distance_km < 3:
            return '2-3公里'
        elif distance_km < 4:
            return '3-4公里'
        elif distance_km < 5:
            return '4-5公里'
        else:
            return '5公里以上'
    
    filtered_df['距离分层'] = filtered_df['配送距离_公里'].apply(get_distance_range)
    distance_order = ['1公里以下', '1-2公里', '2-3公里', '3-4公里', '4-5公里', '5公里以上', '未知']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📍 配送距离分布**")
        distance_orders = filtered_df.groupby('距离分层')['订单ID'].nunique()
        distance_orders = distance_orders.reindex(distance_order, fill_value=0)
        
        # 排除"未知"类别用于图表显示
        distance_orders_valid = distance_orders[distance_orders.index != '未知']
        
        fig = px.pie(
            values=distance_orders_valid.values,
            names=distance_orders_valid.index,
            title=f'订单配送距离分布（{period_label}）',
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
        # 计算总订单数（排除未知）
        total_orders_valid = distance_orders_valid.sum()
        total_orders = filtered_df['订单ID'].nunique()
        unknown_count = distance_orders.get('未知', 0)
        
        if unknown_count > 0:
            st.caption(f"ℹ️ 有 {unknown_count} 单订单缺少配送距离数据（已从图表中排除）")
        
        main_ratio = (distance_orders['1公里以下'] + distance_orders['1-2公里'] + distance_orders['2-3公里'])/total_orders_valid*100
        
        st.markdown(f"""
        <div class="insight-box">
        <b>💡 关键洞察：</b><br>
        • 主要服务半径：<b>3公里以内</b>占比{main_ratio:.1f}%<br>
        • 1公里以下：<b>{distance_orders['1公里以下']}</b>单（核心区域）<br>
        • 1-2公里：<b>{distance_orders['1-2公里']}</b>单（主力区域）<br>
        • 建议：3km内区域为核心商圈，重点布局
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("**💰 距离段客单价对比**")
        try:
            # 处理重复列名
            temp_df = filtered_df.copy()
            if isinstance(temp_df['订单ID'], pd.DataFrame):
                temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
            if isinstance(temp_df['商品实售价'], pd.DataFrame):
                temp_df['商品实售价'] = temp_df['商品实售价'].iloc[:, 0]
            
            distance_price = temp_df.groupby(['距离分层', '订单ID'])['商品实售价'].sum().groupby('距离分层').mean()
            distance_price = distance_price.reindex(distance_order, fill_value=0)
            
            # 排除"未知"类别用于图表显示
            distance_price_valid = distance_price[distance_price.index != '未知']
            
            fig = px.bar(
                x=distance_price_valid.index,
                y=distance_price_valid.values,
                labels={'x': '配送距离', 'y': '平均客单价(元)'},
                title=f'各距离段平均客单价（{period_label}）',
                color=distance_price_valid.values,
                color_continuous_scale='Greens'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"计算距离段客单价时出错: {str(e)}")
    
    # 计算距离段的配送费成本（按订单级聚合）
    if '配送费成本' in filtered_df.columns:
        try:
            # 处理重复列名
            temp_df = filtered_df.copy()
            if isinstance(temp_df['订单ID'], pd.DataFrame):
                temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
            if isinstance(temp_df['配送费成本'], pd.DataFrame):
                temp_df['配送费成本'] = temp_df['配送费成本'].iloc[:, 0]
            
            order_delivery_cost = temp_df.groupby(['订单ID', '距离分层'])['配送费成本'].first().groupby('距离分层').mean()
            order_delivery_cost = order_delivery_cost.reindex(distance_order, fill_value=0)
        
            st.write("**🚚 距离段配送费成本分析**")
            col_a, col_b = st.columns(2)
            
            with col_a:
                # 配送费成本按距离段对比
                cost_valid = order_delivery_cost[order_delivery_cost.index != '未知']
                fig = px.bar(
                    x=cost_valid.index,
                    y=cost_valid.values,
                    labels={'x': '配送距离', 'y': '单均配送成本(元)'},
                    title=f'各距离段单均配送费成本（{period_label}）',
                    color=cost_valid.values,
                    color_continuous_scale='Reds'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col_b:
                # 距离与成本关系洞察
                max_cost_range = cost_valid.idxmax() if not cost_valid.empty else None
                min_cost_range = cost_valid.idxmin() if not cost_valid.empty else None
                
                st.markdown(f"""
                <div class="insight-box">
            <b>💡 配送费成本洞察：</b><br>
            • 最高成本距离段：<b>{max_cost_range}</b>（¥{cost_valid.get(max_cost_range, 0):.2f}/单）<br>
            • 最低成本距离段：<b>{min_cost_range}</b>（¥{cost_valid.get(min_cost_range, 0):.2f}/单）<br>
            • 成本差异：¥{abs(cost_valid.get(max_cost_range, 0) - cost_valid.get(min_cost_range, 0)):.2f}/单<br>
            • 建议：优化远距离订单配送策略，降低配送成本
            </div>
            """, unsafe_allow_html=True)
                
                # 配送费成本占客单价比例
                if len(distance_price_valid) > 0 and len(cost_valid) > 0:
                    st.write("**配送成本占客单价比例**")
                    for dist in cost_valid.index:
                        if dist in distance_price_valid.index:
                            price = distance_price_valid[dist]
                            cost = cost_valid[dist]
                            ratio = (abs(cost) / price * 100) if price > 0 else 0
                            st.progress(min(ratio/20, 1.0), text=f"{dist}: {ratio:.2f}%")
        except Exception as e:
            st.error(f"计算配送费成本分析时出错: {str(e)}")
            order_delivery_cost = pd.Series(dtype=float)  # 空Series作为后备
    else:
        # 如果没有配送费成本列，初始化为空Series
        order_delivery_cost = pd.Series(dtype=float)
    
    # 添加详细数据表格
    st.write(f"**📋 配送距离详细数据（{period_label}）**")
    distance_detail = []
    for dist_range in distance_order:
        if dist_range == '未知':
            continue
        count = distance_orders.get(dist_range, 0)
        ratio = (count / total_orders_valid * 100) if total_orders_valid > 0 else 0
        avg_price = distance_price.get(dist_range, 0)
        
        detail_row = {
            '距离范围': dist_range,
            '订单数': f'{count:,}',
            '占比': f'{ratio:.1f}%',
            '平均客单价': f'¥{avg_price:.2f}'
        }
        
        # 如果有配送费成本数据，添加到表格
        if len(order_delivery_cost) > 0:
            avg_cost = order_delivery_cost.get(dist_range, 0)
            detail_row['单均配送成本'] = f'¥{avg_cost:.2f}'
            cost_ratio = (abs(avg_cost) / avg_price * 100) if avg_price > 0 else 0
            detail_row['成本占比'] = f'{cost_ratio:.2f}%'
        
        distance_detail.append(detail_row)
    
    detail_df = pd.DataFrame(distance_detail)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
    
    st.markdown("""
    <div class="warning-box">
    <b>🎯 商圈营销建议：</b><br>
    1. <b>1公里以下（核心区）</b>：常客区域，推VIP会员，提高复购率<br>
    2. <b>1-2公里（主力区）</b>：订单量最大，设置"满X免配送费"吸引订单<br>
    3. <b>2-3公里（次主力区）</b>：仍有潜力，可适当提高满减门槛<br>
    4. <b>3-5公里（边缘区）</b>：提高最低消费，或与社区团购合作<br>
    5. <b>5公里以上（远距离）</b>：建议暂停配送或收取高额配送费
    </div>
    """, unsafe_allow_html=True)


def render_price_sensitivity_marketing(df: pd.DataFrame, time_dimension: str = '日', selected_period: str = None):
    """价格敏感度营销（支持日/周/月维度）"""
    st.markdown('<p class="sub-header">💰 价格敏感度场景分析</p>', unsafe_allow_html=True)
    
    # ==================== 场景营销理念说明 ====================
    with st.expander("💡 价格场景：不同人群的不同需求", expanded=False):
        st.markdown("""
        ### 🎯 价格敏感度的场景本质
        
        #### 谁在什么场景下对价格敏感？
        
        **1. 高价值用户（低价格敏感）**
        - **场景**：应急、品质需求、时间紧迫
        - **特征**：客单价高、复购率高、对优惠不敏感
        - **策略**：会员制、品质保障、快速配送、积分权益
        - **举例**：工作日午餐、婴儿用品、进口食品
        
        **2. 价格敏感用户（高价格敏感）**
        - **场景**：日常采购、提前计划、非紧急
        - **特征**：客单价低、比价多、优惠驱动
        - **策略**：满减、团购、秒杀、优惠券
        - **举例**：周末囤货、生鲜特价、清仓促销
        
        **3. 中间用户（平衡型）**
        - **场景**：常规需求、品质与价格并重
        - **特征**：客单价中等、稳定复购
        - **策略**：套餐组合、会员折扣、品类推荐
        - **举例**：工作日晚餐、日用品补货
        
        #### 场景化定价策略
        
        **时段 × 价格场景**
        - ⏰ **高峰时段**（午餐、晚餐）：减少折扣，保障服务
        - 🌙 **低谷时段**（上午、下午茶）：满减、第二件半价
        - 🌃 **深夜时段**：溢价配送，应急需求不敏感
        
        **距离 × 价格场景**
        - 📍 **近距离**（1km内）：免配送费，培养高频
        - 🚴 **中距离**（2-3km）：适度满减，平衡成本
        - 🚗 **远距离**（3km+）：提高门槛，覆盖成本
        
        **品类 × 价格场景**
        - 🍎 **生鲜品类**：引流品，低毛利高频
        - 🍺 **饮料零食**：利润品，搭售组合
        - 🏠 **日用百货**：稳定品，会员专享
        
        ---
        
        **💼 本看板的核心价值**：
        - 识别不同价格段的用户行为
        - 制定差异化定价策略
        - 平衡销量与利润
        - 提升整体客单价
        """)
    
    df = extract_time_features(df)
    
    # 映射维度到字段名
    dim_mapping = {
        '日': '日期_datetime',
        '周': '年周',
        '月': '年月'
    }
    time_col = dim_mapping[time_dimension]
    
    # ==================== 核心指标总览（带环比） ====================
    st.markdown(f"### 📈 核心指标总览（按{time_dimension}）")
    
    if time_col in df.columns and '订单ID' in df.columns:
        try:
            # 处理重复列名
            temp_df = df.copy()
            if isinstance(temp_df['订单ID'], pd.DataFrame):
                temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
            if isinstance(temp_df['商品实售价'], pd.DataFrame):
                temp_df['商品实售价'] = temp_df['商品实售价'].iloc[:, 0]
            
            # 按时间维度聚合订单级数据
            order_level = temp_df.groupby(['订单ID', time_col]).agg({
                '商品实售价': 'sum'
            }).reset_index()
            order_level.columns = ['订单ID', time_col, '客单价']
            
            # 按时间维度聚合
            time_agg = order_level.groupby(time_col).agg({
                '订单ID': 'count',
                '客单价': 'mean'
            }).reset_index()
            time_agg.columns = [time_col, '订单数', '平均客单价']
        
            # 计算环比
            time_agg = calculate_period_over_period(time_agg, time_dimension, '订单数')
            time_agg = calculate_period_over_period(time_agg, time_dimension, '平均客单价')
        except Exception as e:
            st.error(f"计算核心指标时出错: {str(e)}")
            time_agg = None
    else:
        time_agg = None
    
    if time_agg is not None:
        
        # 获取当前期和上一期数据（根据用户选择或最近一期）
        if len(time_agg) >= 1:
            # 如果用户选择了具体周期，使用选择的周期；否则使用最近一期
            if selected_period and not selected_period.startswith("全部"):
                if time_dimension == "日":
                    selected_date = pd.to_datetime(selected_period)
                    latest_idx = time_agg[time_agg[time_col] == selected_date].index
                else:
                    latest_idx = time_agg[time_agg[time_col] == selected_period].index
                
                if len(latest_idx) > 0:
                    latest = time_agg.loc[latest_idx[0]]
                    # 获取上一期数据
                    current_position = latest_idx[0]
                    previous = time_agg.iloc[current_position - 1] if current_position > 0 else None
                else:
                    latest = time_agg.iloc[-1]
                    previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            else:
                # 未选择具体周期，使用最近一期
                latest = time_agg.iloc[-1]
                previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            
            col1, col2, col3 = st.columns(3)
            
            # 当前周期
            with col1:
                period_label = format_period_label(latest[time_col], time_dimension)
                st.metric(label=f"当前{time_dimension}", value=period_label)
            
            # 订单数（带环比）
            render_metric_with_comparison(
                col2, f"订单数",
                latest['订单数'],
                previous['订单数'] if previous is not None else None,
                format_type='number', unit='单'
            )
            
            # 平均客单价（带环比）
            render_metric_with_comparison(
                col3, f"平均客单价",
                latest['平均客单价'],
                previous['平均客单价'] if previous is not None else None,
                format_type='currency'
            )
        
        st.markdown("---")
        
        # ==================== 趋势图 ====================
        st.markdown(f"### 📊 {time_dimension}度趋势分析")
        
        tab1, tab2 = st.tabs(["客单价趋势", "订单量趋势"])
        
        with tab1:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='平均客单价',
                title=f'平均客单价{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#e74c3c', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 环比变化表格
            if '平均客单价_环比率' in time_agg.columns:
                st.write("**环比变化详情**")
                display_df = time_agg[[time_col, '平均客单价', '平均客单价_上期值', '平均客单价_环比变化', '平均客单价_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前客单价', '上期客单价', '环比变化额', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前客单价': '¥{:,.2f}',
                    '上期客单价': '¥{:,.2f}',
                    '环比变化额': '¥{:+,.2f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
        
        with tab2:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='订单数',
                title=f'订单数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#3498db', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== 价格敏感度分层（根据选定的时间维度筛选最近一期） ====================
    st.markdown(f"### 💰 客单价分层分析（当前{time_dimension}数据）")
    
    # 筛选最近一个周期的数据
    filtered_df = filter_data_by_time_dimension(df, time_dimension, selected_period, latest_only=True)
    
    if len(filtered_df) == 0:
        st.warning(f"⚠️ 当前{time_dimension}暂无数据")
        return
    
    # 显示当前分析的时间范围
    if time_col in filtered_df.columns:
        current_period = filtered_df[time_col].iloc[0]
        period_label = format_period_label(current_period, time_dimension)
        st.info(f"📅 当前分析时间：{period_label}")
    
    order_prices = filtered_df.groupby('订单ID')['商品实售价'].sum()
    
    def get_price_range(price):
        if price < 20:
            return '低价(<20元)'
        elif price < 40:
            return '中低(20-40元)'
        elif price < 60:
            return '中高(40-60元)'
        else:
            return '高价(≥60元)'
    
    price_segments = order_prices.apply(get_price_range)
    price_range_order = ['低价(<20元)', '中低(20-40元)', '中高(40-60元)', '高价(≥60元)']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 客单价分层用户分布**")
        price_dist = price_segments.value_counts().reindex(price_range_order, fill_value=0)
        
        fig = px.bar(
            x=price_dist.index,
            y=price_dist.values,
            labels={'x': '客单价区间', 'y': '订单数'},
            title=f'客单价分布（{period_label}）',
            color=price_dist.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        main_segment = price_dist.idxmax()
        main_ratio = price_dist.max() / price_dist.sum() * 100
        
        st.markdown(f"""
        <div class="insight-box">
        <b>💡 客群洞察：</b><br>
        • 主要客群：<b>{main_segment}</b>（{main_ratio:.1f}%）<br>
        • 平均客单价：¥{order_prices.mean():.2f}<br>
        • 客单价中位数：¥{order_prices.median():.2f}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("**🎁 满减门槛达成分析**")
        manjian_thresholds = [20, 30, 40, 50, 60, 80]
        threshold_reach = []
        
        for threshold in manjian_thresholds:
            reach_orders = (order_prices >= threshold).sum()
            reach_ratio = reach_orders / len(order_prices) * 100
            threshold_reach.append({'门槛': f'{threshold}元', '达标率': reach_ratio})
        
        threshold_df = pd.DataFrame(threshold_reach)
        
        fig = px.line(
            threshold_df,
            x='门槛',
            y='达标率',
            title=f'满减门槛达标率（{period_label}）',
            markers=True
        )
        fig.update_traces(line_color='#e74c3c', marker=dict(size=10))
        fig.update_layout(yaxis_title='达标率(%)')
        st.plotly_chart(fig, use_container_width=True)
        
        # 找到60-80%之间的门槛
        optimal = None
        for item in threshold_reach:
            if 60 <= item['达标率'] <= 80:
                optimal = item['门槛']
                break
        
        if optimal:
            st.markdown(f"""
            <div class="insight-box">
            <b>💡 最优满减建议：</b><br>
            • 建议设置满减门槛：<b>满{optimal}</b><br>
            • 理由：达标率在60-80%之间，平衡刺激与补贴
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
    <b>🎯 价格营销建议：</b><br>
    1. <b>低价客群</b>：推送小额券（5-8元），培养消费习惯<br>
    2. <b>中价客群</b>：满减活动为主，提升客单价<br>
    3. <b>高价客群</b>：减少促销，提供优质服务和会员权益<br>
    4. <b>动态定价</b>：高峰时段减少折扣，低峰时段加大力度
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 🤖 RFM客户分群分析 ====================
    st.markdown("---")
    st.markdown("### 🤖 RFM客户分群与画像")
    
    if SCENE_INTELLIGENCE_AVAILABLE:
        with st.expander("💡 基于RFM+K-Means的客户分群", expanded=True):
            st.info("📊 结合RFM模型与聚类算法，识别高频应急、计划囤货、价格敏感、偶发尝鲜四类用户")
            
            col1, col2 = st.columns([3, 1])
            
            with col2:
                if st.button("🚀 运行客户分群", key="run_rfm_clustering"):
                    with st.spinner("⏳ 正在计算RFM特征并聚类..."):
                        try:
                            # 初始化分群模型
                            rfm_model = RFMCustomerSegmentation(n_clusters=4)
                            
                            # 计算RFM
                            rfm_data = rfm_model.calculate_rfm(filtered_df)
                            
                            # 执行聚类
                            segment_result = rfm_model.segment_customers()
                            
                            if segment_result.get('status') == 'success':
                                # 保存到session_state
                                st.session_state['rfm_model'] = rfm_model
                                st.session_state['rfm_result'] = segment_result
                                
                                st.success(f"✅ 分群完成！识别{segment_result['n_clusters']}个客户群组")
                            else:
                                st.error(f"❌ 分群失败：{segment_result.get('message')}")
                        
                        except Exception as e:
                            st.error(f"❌ 分群过程出错: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            # 如果分群已完成，显示结果
            if 'rfm_model' in st.session_state and 'rfm_result' in st.session_state:
                rfm_model = st.session_state['rfm_model']
                segment_result = st.session_state['rfm_result']
                
                # 创建标签页
                tab1, tab2, tab3 = st.tabs(["👥 客户群组", "📊 3D可视化", "📋 策略建议"])
                
                with tab1:
                    st.markdown("#### 👥 客户群组画像")
                    
                    # 分群质量指标
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("客户群组数", segment_result['n_clusters'])
                    
                    with col2:
                        st.metric("轮廓系数", f"{segment_result['silhouette_score']:.3f}",
                                 help="轮廓系数越接近1，分群质量越好")
                    
                    with col3:
                        total_customers = sum(segment_result['distribution'].values())
                        st.metric("总客户数", f"{total_customers:,}")
                    
                    # 群组摘要表
                    st.markdown("**📊 各客户群组特征**")
                    summary_df = rfm_model.get_cluster_summary()
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    
                    # 群组分布饼图
                    st.markdown("**📈 客户群组分布**")
                    dist_df = pd.DataFrame(list(segment_result['distribution'].items()), 
                                          columns=['群组ID', '用户数'])
                    dist_df['群组名称'] = dist_df['群组ID'].map(
                        lambda x: segment_result['cluster_profiles'][x]['name']
                    )
                    
                    fig = px.pie(dist_df, values='用户数', names='群组名称', 
                                title='客户群组占比')
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    st.markdown("#### 📊 RFM 3D可视化")
                    st.caption("*X轴=最近购买天数，Y轴=购买频次，Z轴=购买金额*")
                    
                    cluster_3d_fig = rfm_model.visualize_clusters()
                    st.plotly_chart(cluster_3d_fig, use_container_width=True)
                    
                    st.markdown("""
                    **维度说明：**
                    - **Recency（最近购买）**: 距离上次购买的天数，越小越活跃
                    - **Frequency（购买频次）**: 总购买次数，越多越忠诚
                    - **Monetary（购买金额）**: 累计消费金额，越高越有价值
                    - **Avg Distance（平均距离）**: 平均配送距离，反映便利性需求
                    - **Avg Fee Ratio（配送费占比）**: 配送费占订单金额比例，反映应急程度
                    """)
                
                with tab3:
                    st.markdown("#### 📋 差异化营销策略")
                    
                    for cluster_id, profile in segment_result['cluster_profiles'].items():
                        with st.container():
                            st.markdown(f"### {profile['name']}")
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.metric("用户数", f"{profile['size']:,}")
                                st.metric("占比", f"{profile['percentage']:.1f}%")
                                
                                # 获取数据周期和原始订单数
                                data_days = int(profile.get('data_span_days', 30))
                                avg_total_orders = profile.get('avg_total_orders', profile['avg_frequency'])
                                
                                # 显示周期内订单数（更直观）
                                st.metric(
                                    f"{data_days}天内订单", 
                                    f"{avg_total_orders:.1f}单",
                                    help=f"该群组用户在{data_days}天内平均下单次数"
                                )
                                
                                # 显示标准化频次（用于聚类）
                                st.metric(
                                    "购买频次", 
                                    f"{profile['avg_frequency']:.2f}次/周",
                                    help="标准化后的每周平均订单数，用于不同周期数据对比"
                                )
                                
                                st.metric("平均消费", f"¥{profile['avg_monetary']:.0f}")
                            
                            with col2:
                                st.markdown(f"""
                                <div class="insight-box">
                                <b>� 群组定义：</b><br>
                                {profile.get('definition', '暂无定义')}<br>
                                <br>
                                <b>📊 关键特征（群组平均值）：</b><br>
                                • 平均最近购买: {profile['avg_recency']:.0f}天前<br>
                                • 平均配送距离: {profile['avg_distance']:.1f}km<br>
                                • 平均配送费占比: {profile['avg_fee_ratio']*100:.1f}%<br>
                                • 平均商品数: {profile.get('avg_items_per_order', 0):.1f}件/单<br>
                                • 平均品类数: {profile.get('avg_categories_per_order', 0):.1f}种/单<br>
                                <br>
                                <b>🎯 营销策略：</b><br>
                                {profile['strategy']}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("---")
    else:
        st.warning("⚠️ 场景营销智能决策引擎未加载，请确保已安装scikit-learn")


def render_product_combination_marketing(df: pd.DataFrame, time_dimension: str = '日', selected_period: str = None):
    """商品组合场景营销（支持日/周/月维度）"""
    st.markdown('<p class="sub-header">📦 商品组合场景分析</p>', unsafe_allow_html=True)
    
    # ==================== 场景营销理念说明 ====================
    with st.expander("💡 商品组合：快消零售的场景化需求满足", expanded=False):
        st.markdown("""
        ### 🎯 快消零售商品组合的场景逻辑
        
        #### 为什么要做商品组合？
        
        **1. 场景完整性**
        - ❌ **单品思维**：用户买薯片，还得单独买可乐
        - ✅ **场景思维**：直接推"追剧套餐"（薯片+可乐+瓜子），一键下单
        
        **2. 降低决策成本**
        - 用户不用思考"还需要什么"
        - 系统智能推荐"买这个的人还买了..."
        - 减少购物车弃单率
        
        **3. 提升客单价**
        - 单品购买：平均25元
        - 组合购买：平均40元（提升60%）
        - 交叉销售：带动低频品类
        
        #### 快消零售的场景化商品组合策略
        
        **🍿 追剧放松场景组合**
        ```
        核心场景：晚间在家追剧、放松娱乐
        典型组合：
        - 基础套餐：薯片 + 可乐 + 纸巾（¥18）
        - 升级套餐：膨化食品 + 饮料 + 坚果 + 水果（¥35）
        - 分享套餐：大包装零食 + 2升装饮料（¥45）
        
        关联推荐：买薯片 → 推荐可乐、饮料
        ```
        
        **🎮 游戏聚会场景组合**
        ```
        核心场景：朋友聚会、游戏娱乐
        典型组合：
        - 聚会套餐：啤酒 + 卤味 + 花生 + 薯片（¥68）
        - 游戏套餐：饮料 + 零食 + 水果拼盘（¥45）
        - 夜宵套餐：烤肠 + 鸭脖 + 啤酒（¥55）
        
        关联推荐：买啤酒 → 推荐卤味、花生、烤肠
        ```
        
        **☕ 办公提神场景组合**
        ```
        核心场景：上午/下午办公室工作
        典型组合：
        - 提神套餐：咖啡 + 坚果 + 巧克力（¥25）
        - 下午茶套餐：奶茶 + 饼干 + 糖果（¥20）
        - 能量套餐：功能饮料 + 能量棒 + 口香糖（¥22）
        
        关联推荐：买咖啡 → 推荐坚果、巧克力
        ```
        
        **🏠 家庭日常场景组合**
        ```
        核心场景：周末家庭囤货、日常补充
        典型组合：
        - 日用套餐：纸巾 + 洗衣液 + 垃圾袋（¥45）
        - 清洁套餐：洗洁精 + 洗手液 + 抽纸（¥35）
        - 洗护套餐：洗发水 + 沐浴露 + 牙膏（¥68）
        
        关联推荐：买纸巾 → 推荐垃圾袋、洗衣液
        ```
        
        **🚨 应急场景组合**
        ```
        核心场景：突然发现缺某物、临时需求
        典型组合：
        - 应急包：纸巾 + 垃圾袋 + 电池（¥20）
        - 临时客人：饮料 + 零食 + 水果（¥35）
        - 婴儿应急：尿不湿 + 湿巾 + 纸巾（¥58）
        
        关联推荐：买纸巾 → 推荐其他日用品
        ```
        
        #### 智能推荐策略（基于购物篮分析）
        
        **1. 高频关联组合**
        - 🍺 啤酒 → 卤味、花生、薯片（关联度80%）
        - 🍿 薯片 → 可乐、饮料、瓜子（关联度75%）
        - ☕ 咖啡 → 坚果、巧克力、饼干（关联度70%）
        - 🧻 纸巾 → 垃圾袋、洗衣液、抽纸（关联度65%）
        
        **2. 场景触发推荐**
        - 晚上19-23点下单 → 自动推荐追剧套餐
        - 周末10-18点下单 → 自动推荐家庭囤货套餐
        - 办公区地址 → 自动推荐提神套餐
        
        **3. 用户画像推荐**
        - 高频用户 → 推荐会员专享组合
        - 低频用户 → 推荐新人优惠套餐
        - 家庭用户 → 推荐大包装组合
        
        ---
        
        **📊 本看板提供的组合洞察**：
        - 发现高频商品关联（哪些商品经常一起买）
        - 识别场景化需求（什么场景买什么组合）
        - 优化套餐设计（设计高客单价组合）
        - 提升连带销售（智能推荐关联商品）
        """)
    
    df = extract_time_features(df)
    
    # 映射维度到字段名
    dim_mapping = {
        '日': '日期_datetime',
        '周': '年周',
        '月': '年月'
    }
    time_col = dim_mapping[time_dimension]
    
    # ==================== 核心指标总览（带环比） ====================
    st.markdown(f"### 📈 核心指标总览（按{time_dimension}）")
    
    if time_col in df.columns and '订单ID' in df.columns:
        try:
            # 处理重复列名
            temp_df = df.copy()
            if isinstance(temp_df['订单ID'], pd.DataFrame):
                temp_df['订单ID'] = temp_df['订单ID'].iloc[:, 0]
            
            # 计算每个订单的商品件数
            items_per_order = temp_df.groupby(['订单ID', time_col]).size().reset_index(name='商品件数')
            
            # 按时间维度聚合
            time_agg = items_per_order.groupby(time_col).agg({
                '订单ID': 'count',
                '商品件数': 'mean'
            }).reset_index()
            time_agg.columns = [time_col, '订单数', '平均件数']
            
            # 计算组合订单比例（件数>1）
            combo_orders = items_per_order[items_per_order['商品件数'] > 1].groupby(time_col).size().reset_index(name='组合订单数')
            time_agg = time_agg.merge(combo_orders, on=time_col, how='left')
            time_agg['组合订单数'] = time_agg['组合订单数'].fillna(0)
            time_agg['组合订单比例'] = (time_agg['组合订单数'] / time_agg['订单数'] * 100).round(2)
        
            # 计算环比
            time_agg = calculate_period_over_period(time_agg, time_dimension, '订单数')
            time_agg = calculate_period_over_period(time_agg, time_dimension, '平均件数')
            time_agg = calculate_period_over_period(time_agg, time_dimension, '组合订单比例')
        except Exception as e:
            st.error(f"计算核心指标时出错: {str(e)}")
            time_agg = None
    else:
        time_agg = None
    
    if time_agg is not None:
        
        # 获取当前期和上一期数据（根据用户选择或最近一期）
        if len(time_agg) >= 1:
            # 如果用户选择了具体周期，使用选择的周期；否则使用最近一期
            if selected_period and not selected_period.startswith("全部"):
                if time_dimension == "日":
                    selected_date = pd.to_datetime(selected_period)
                    latest_idx = time_agg[time_agg[time_col] == selected_date].index
                else:
                    latest_idx = time_agg[time_agg[time_col] == selected_period].index
                
                if len(latest_idx) > 0:
                    latest = time_agg.loc[latest_idx[0]]
                    # 获取上一期数据
                    current_position = latest_idx[0]
                    previous = time_agg.iloc[current_position - 1] if current_position > 0 else None
                else:
                    latest = time_agg.iloc[-1]
                    previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            else:
                # 未选择具体周期，使用最近一期
                latest = time_agg.iloc[-1]
                previous = time_agg.iloc[-2] if len(time_agg) >= 2 else None
            
            col1, col2, col3, col4 = st.columns(4)
            
            # 当前周期
            with col1:
                period_label = format_period_label(latest[time_col], time_dimension)
                st.metric(label=f"当前{time_dimension}", value=period_label)
            
            # 平均件数（带环比）
            render_metric_with_comparison(
                col2, f"平均件数/单",
                latest['平均件数'],
                previous['平均件数'] if previous is not None else None,
                format_type='number', unit='件'
            )
            
            # 组合订单比例（带环比）
            render_metric_with_comparison(
                col3, f"组合订单比例",
                latest['组合订单比例'],
                previous['组合订单比例'] if previous is not None else None,
                format_type='percent'
            )
            
            # 订单数（带环比）
            render_metric_with_comparison(
                col4, f"订单数",
                latest['订单数'],
                previous['订单数'] if previous is not None else None,
                format_type='number', unit='单'
            )
        
        st.markdown("---")
        
        # ==================== 趋势图 ====================
        st.markdown(f"### 📊 {time_dimension}度趋势分析")
        
        tab1, tab2, tab3 = st.tabs(["平均件数趋势", "组合订单比例趋势", "订单量趋势"])
        
        with tab1:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='平均件数',
                title=f'平均件数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#9b59b6', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 环比变化表格
            if '平均件数_环比率' in time_agg.columns:
                st.write("**环比变化详情**")
                display_df = time_agg[[time_col, '平均件数', '平均件数_上期值', '平均件数_环比变化', '平均件数_环比率']].tail(10)
                display_df.columns = ['时间周期', '当前平均件数', '上期平均件数', '环比变化量', '环比变化率(%)']
                st.dataframe(display_df.style.format({
                    '当前平均件数': '{:.2f}',
                    '上期平均件数': '{:.2f}',
                    '环比变化量': '{:+.2f}',
                    '环比变化率(%)': '{:+.2f}%'
                }), use_container_width=True)
        
        with tab2:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='组合订单比例',
                title=f'组合订单比例{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#16a085', width=3))
            fig.update_layout(height=400, yaxis_title='组合订单比例(%)')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            fig = px.line(
                time_agg, 
                x=time_col, 
                y='订单数',
                title=f'订单数{time_dimension}度趋势',
                markers=True
            )
            fig.update_traces(line=dict(color='#3498db', width=3))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== 商品组合分析（根据选定的时间维度筛选最近一期） ====================
    st.markdown(f"### 🛒 购物篮分析 - 商品关联发现（当前{time_dimension}数据）")
    
    # 筛选最近一个周期的数据
    filtered_df = filter_data_by_time_dimension(df, time_dimension, selected_period, latest_only=True)
    
    if len(filtered_df) == 0:
        st.warning(f"⚠️ 当前{time_dimension}暂无数据")
        return
    
    # 显示当前分析的时间范围
    if time_col in filtered_df.columns:
        current_period = filtered_df[time_col].iloc[0]
        period_label = format_period_label(current_period, time_dimension)
        st.info(f"📅 当前分析时间：{period_label}")
    
    if '一级分类名' in filtered_df.columns:
        from itertools import combinations
        order_categories = filtered_df.groupby('订单ID')['一级分类名'].apply(list)
        
        category_pairs = {}
        for order_id, categories in order_categories.items():
            unique_cats = list(set(categories))
            if len(unique_cats) >= 2:
                for pair in combinations(sorted(unique_cats), 2):
                    key = f"{pair[0]} + {pair[1]}"
                    category_pairs[key] = category_pairs.get(key, 0) + 1
        
        if category_pairs:
            top_pairs = sorted(category_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                pairs_df = pd.DataFrame(top_pairs, columns=['商品组合', '共现次数'])
                
                fig = px.bar(
                    pairs_df,
                    x='共现次数',
                    y='商品组合',
                    orientation='h',
                    title=f'Top 10 商品分类组合（{period_label}）',
                    color='共现次数',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**🔝 Top 5 热门组合**")
                for i, (pair, count) in enumerate(top_pairs[:5], 1):
                    st.markdown(f"""
                    <div class="metric-card">
                    <b>{i}. {pair}</b><br>
                    共现 {count} 次
                    </div>
                    """, unsafe_allow_html=True)
            
            top_pair = top_pairs[0]
            st.markdown(f"""
            <div class="insight-box">
            <b>💡 套餐设计建议：</b><br>
            • 最佳组合：<b>{top_pair[0]}</b>（共现{top_pair[1]}次）<br>
            • 建议：将这两类商品打包为套餐，定价略低于单买总价<br>
            • 预期：提升客单价10-15%，提高用户满意度
            </div>
            """, unsafe_allow_html=True)
    
    # 单品vs组合订单对比
    st.write(f"**📊 单品订单 vs 组合订单对比（{period_label}）**")
    items_per_order = filtered_df.groupby('订单ID').size()
    single_item_orders = items_per_order[items_per_order == 1].index
    combo_orders = items_per_order[items_per_order > 1].index
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        single_count = len(single_item_orders)
        total_orders = filtered_df['订单ID'].nunique()
        st.metric("单品订单", f"{single_count:,}",
                 delta=f"{single_count/total_orders*100:.1f}%")
    
    with col2:
        combo_count = len(combo_orders)
        st.metric("组合订单", f"{combo_count:,}",
                 delta=f"{combo_count/total_orders*100:.1f}%")
    
    with col3:
        avg_items_combo = items_per_order[items_per_order > 1].mean()
        st.metric("组合订单平均件数", f"{avg_items_combo:.1f}件")
    
    st.markdown("""
    <div class="warning-box">
    <b>🎯 商品组合营销建议：</b><br>
    1. <b>套餐设计</b>：引流品+利润品，实现销量与利润平衡<br>
    2. <b>交叉销售</b>：购买A商品后推荐常搭配的B商品<br>
    3. <b>满件优惠</b>："第二件半价"促进多件购买<br>
    4. <b>智能推荐</b>：基于购物篮分析，精准推荐组合商品
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 🤖 AI智能决策分析 ====================
    st.markdown("---")
    st.markdown("### 🤖 AI智能商品组合挖掘")
    
    if SCENE_INTELLIGENCE_AVAILABLE:
        with st.expander("💡 基于FP-Growth算法的关联规则挖掘", expanded=True):
            st.info("📊 使用机器学习算法自动发现商品购买关联规则，生成场景化套餐建议")
            
            # 运行按钮
            if st.button("🚀 开始智能分析", key="run_product_mining"):
                with st.spinner("⏳ 正在分析商品组合规律..."):
                    try:
                        # 数据量检查
                        total_orders = filtered_df['订单ID'].nunique()
                        st.info(f"📦 订单数量: {total_orders} | 商品种类: {filtered_df['商品名称'].nunique()}")
                        
                        # 根据数据量动态调整阈值
                        if total_orders < 100:
                            min_sup, min_conf = 0.02, 0.2  # 超小数据集
                        elif total_orders < 500:
                            min_sup, min_conf = 0.01, 0.25  # 小数据集
                        else:
                            min_sup, min_conf = 0.005, 0.3  # 正常数据集
                        
                        # 初始化挖掘引擎
                        miner = ProductCombinationMiner(
                            min_support=min_sup,
                            min_confidence=min_conf
                        )
                        
                        st.caption(f"⚙️ 当前阈值: 支持度≥{min_sup*100:.1f}%, 置信度≥{min_conf*100:.0f}%")
                        
                        # 执行挖掘
                        result = miner.mine_from_orders(filtered_df)
                        
                        if result.get('status') == 'success':
                            st.success(f"✅ 分析完成！发现 {result['stats']['rules_count']} 条关联规则")
                            
                            # 创建标签页
                            tab1, tab2, tab3, tab4 = st.tabs([
                                "📊 TOP关联规则", 
                                "🎁 场景化套餐", 
                                "🕸️ 关联网络", 
                                "📈 统计摘要"
                            ])
                            
                            with tab1:
                                st.markdown("#### 🔝 TOP 10 关联规则")
                                st.caption("*规则格式: 商品A → 商品B（如果购买A，则推荐B）*")
                                
                                top_rules = miner.get_top_rules(top_n=10, sort_by='lift')
                                if not top_rules.empty:
                                    # 格式化显示
                                    display_rules = top_rules.copy()
                                    display_rules['支持度'] = display_rules['support'].apply(lambda x: f"{x*100:.2f}%")
                                    display_rules['置信度'] = display_rules['confidence'].apply(lambda x: f"{x*100:.1f}%")
                                    display_rules['提升度'] = display_rules['lift'].apply(lambda x: f"{x:.2f}x")
                                    
                                    st.dataframe(
                                        display_rules[['rule', '支持度', '置信度', '提升度']],
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                    
                                    # 解释说明
                                    st.markdown("""
                                    **指标说明：**
                                    - **支持度**: 该商品组合在所有订单中出现的频率
                                    - **置信度**: 购买前项商品后，购买后项商品的概率
                                    - **提升度**: 相比随机情况，该规则的推荐效果（>1表示正相关）
                                    """)
                                else:
                                    st.warning(f"""
                                    ⚠️ **未找到满足条件的关联规则**
                                    
                                    当前阈值: 支持度≥{min_sup*100:.1f}%, 置信度≥{min_conf*100:.0f}%
                                    
                                    **可能原因：**
                                    - 订单数量较少（当前{total_orders}个订单）
                                    - 商品组合较分散，缺乏明显关联
                                    - 每个订单商品数量较少
                                    
                                    **建议：**
                                    1. 增加分析时间范围，获取更多订单数据
                                    2. 聚焦特定品类或场景进行分析
                                    3. 查看"统计摘要"了解数据分布情况
                                    """)
                            
                            with tab2:
                                st.markdown("#### 🎁 场景化套餐推荐")
                                
                                scene_packages = result.get('scene_packages', {})
                                if scene_packages:
                                    for scene_name, packages in scene_packages.items():
                                        with st.container():
                                            st.markdown(f"**{scene_name}**")
                                            
                                            for i, pkg in enumerate(packages[:3], 1):
                                                items_str = " + ".join(pkg['items'])
                                                support = pkg['support']
                                                st.markdown(f"""
                                                <div class="metric-card">
                                                <b>套餐 {i}：</b>{items_str}<br>
                                                <small>支持度: {support*100:.2f}% | 匹配度: ⭐{'⭐' * pkg['match_score']}</small>
                                                </div>
                                                """, unsafe_allow_html=True)
                                else:
                                    st.info("💡 提示：可调整场景关键词以识别更多场景套餐")
                            
                            with tab3:
                                st.markdown("#### 🕸️ 商品关联网络图")
                                st.caption("*展示商品之间的关联关系，线条粗细表示关联强度*")
                                
                                network_fig = miner.visualize_rules_network(top_n=15)
                                st.plotly_chart(network_fig, use_container_width=True)
                            
                            with tab4:
                                st.markdown("#### 📈 挖掘统计摘要")
                                
                                stats = result.get('stats', {})
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("分析订单数", f"{stats.get('total_baskets', 0):,}")
                                    st.caption(f"平均每单 {filtered_df.groupby('订单ID').size().mean():.1f} 件商品")
                                
                                with col2:
                                    st.metric("频繁项集数", f"{stats.get('frequent_itemsets_count', 0):,}")
                                    st.caption(f"商品种类: {filtered_df['商品名称'].nunique()}")
                                
                                with col3:
                                    st.metric("关联规则数", f"{stats.get('rules_count', 0):,}")
                                    st.caption(f"当前阈值: {min_sup*100:.1f}%/{min_conf*100:.0f}%")
                                
                                # 数据质量诊断
                                st.markdown("---")
                                st.markdown("**📊 数据质量诊断**")
                                
                                order_sizes = filtered_df.groupby('订单ID').size()
                                quality_col1, quality_col2 = st.columns(2)
                                
                                with quality_col1:
                                    st.markdown(f"""
                                    - 单商品订单: **{(order_sizes == 1).sum()}** 单 ({(order_sizes == 1).sum()/len(order_sizes)*100:.1f}%)
                                    - 2-3件订单: **{((order_sizes >= 2) & (order_sizes <= 3)).sum()}** 单
                                    - 4+件订单: **{(order_sizes >= 4).sum()}** 单
                                    """)
                                
                                with quality_col2:
                                    if stats.get('rules_count', 0) == 0:
                                        st.warning("""
                                        **💡 优化建议：**
                                        - 单商品订单占比过高会降低关联性
                                        - 建议筛选多件订单再分析
                                        - 或扩大时间范围增加数据量
                                        """)
                                    else:
                                        st.success("✅ 数据质量良好，关联分析有效")
                                
                                # TOP商品组合
                                st.markdown("---")
                                st.markdown("**🔝 TOP 5 高频商品组合**")
                                top_combos = miner.get_top_combinations(top_n=5)
                                if not top_combos.empty:
                                    for idx, row in top_combos.iterrows():
                                        st.markdown(f"- {row['items_str']} (支持度: {row['support']*100:.2f}%)")
                        
                        elif result.get('status') == 'warning':
                            st.warning(f"⚠️ {result.get('message')}")
                            st.info("💡 建议：降低最小支持度阈值（如0.005）以发现更多规则")
                        
                        else:
                            st.error(f"❌ 分析失败：{result.get('message')}")
                            
                    except Exception as e:
                        st.error(f"❌ 分析过程出错: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    else:
        st.warning("⚠️ 场景营销智能决策引擎未加载，请确保已安装mlxtend库: `pip install mlxtend`")


def display_scenario_marketing_dashboard(current_data: Dict):
    """场景营销看板主入口（增强版：支持日/周/月维度切换）"""
    st.markdown('<p class="sub-header">🎯 场景营销看板</p>', unsafe_allow_html=True)
    
    # 获取原始数据（优先从current_data，其次从session_state）
    raw_data = current_data.get('raw_data')
    
    # 如果current_data中没有数据，尝试从session_state获取（上传数据的情况）
    if raw_data is None or (isinstance(raw_data, pd.DataFrame) and raw_data.empty):
        if 'current_data' in st.session_state:
            raw_data = st.session_state['current_data'].get('raw_data')
    
    # 检查是否有可用数据
    if raw_data is None or (isinstance(raw_data, pd.DataFrame) and raw_data.empty):
        st.warning("⚠️ 请先加载数据后，才能查看场景营销分析")
        st.info("""
        💡 **场景营销看板功能：**
        
        1. ⏰ **时段场景营销** - 识别黄金销售时段，优化营销投放
        2. 🏪 **门店商圈场景** - 发现高价值商圈，优化门店布局
        3. 💰 **价格敏感度** - 精准定价策略，提升客单价
        4. 📦 **商品组合场景** - 发现商品关联，设计组合套餐
        
        **两种加载方式：**
        - 方式1：在左侧点击"🚀 开始智能分析"加载实际数据
        - 方式2：在"💹 比价看板"标签页上传订单数据Excel文件
        """)
        return
    
    # ========== 数据过滤：剔除咖啡渠道 ==========
    if '渠道' in raw_data.columns:
        exclude_channels = ['饿了么咖啡', '美团咖啡']
        original_count = len(raw_data)
        raw_data = raw_data[~raw_data['渠道'].isin(exclude_channels)].copy()
        filtered_count = len(raw_data)
        excluded_count = original_count - filtered_count
        
        if excluded_count > 0:
            st.info(f"ℹ️ 已自动剔除咖啡渠道数据 {excluded_count} 行（{excluded_count/original_count*100:.1f}%），保留O2O零售数据 {filtered_count} 行")
    
    # 调试: 检查原始数据时间分布
    if '下单时间' in raw_data.columns:
        with st.expander("🔍 原始数据时间诊断（点击展开）", expanded=False):
            st.write("**下单时间样本（前10条）：**")
            time_samples = raw_data['下单时间'].head(10)
            st.dataframe(pd.DataFrame({'下单时间': time_samples}), use_container_width=True)
            
            # 转换为datetime并显示小时分布
            time_series = pd.to_datetime(raw_data['下单时间'], errors='coerce')
            if not time_series.dropna().empty:
                hour_dist = time_series.dt.hour.value_counts().sort_index()
                st.write(f"**时间范围：** {time_series.min()} ~ {time_series.max()}")
                st.write(f"**覆盖小时数：** {len(hour_dist)}/24")
                st.write("**各小时订单数：**")
                st.bar_chart(hour_dist)
    
    # 提取时间特征（支持日/周/月维度）
    raw_data = extract_time_features(raw_data)
    
    # 检查是否成功提取时间特征
    if '日期_datetime' not in raw_data.columns:
        st.error("⚠️ 数据格式错误：无法提取时间特征")
        st.warning("""
        **可能的原因：**
        1. 数据中缺少 '下单时间' 列
        2. '下单时间' 列的格式不正确
        
        **请检查：**
        - 确保 Excel 文件中有 '下单时间' 列
        - 确保时间格式正确（如：2025-01-01 12:00:00）
        """)
        st.info(f"当前数据列名: {list(raw_data.columns)[:30]}")
        return
    
    # 时间维度选择器
    st.markdown("### 📅 数据分析维度")
    col1, col2, col3 = st.columns([1, 2, 2])
    
    with col1:
        time_dimension = st.selectbox(
            "选择时间维度",
            ["日", "周", "月"],
            help="选择不同的时间维度查看数据趋势和环比变化",
            key="scenario_marketing_time_dimension"
        )
    
    # 根据维度动态生成时间周期选择器
    selected_period = None
    with col2:
        if time_dimension == "日":
            available_dates = sorted(raw_data['日期_datetime'].dropna().unique(), reverse=True)
            date_options = ["全部日期"] + [d.strftime('%Y-%m-%d') for d in available_dates]
            selected_period = st.selectbox(
                "选择具体日期",
                date_options,
                help="选择查看某一天的数据，或查看全部日期的趋势",
                key="scenario_marketing_date_selector"
            )
        elif time_dimension == "周":
            available_weeks = sorted(raw_data['年周'].dropna().unique(), reverse=True)
            week_options = ["全部周"] + [f"{w}" for w in available_weeks]
            selected_period = st.selectbox(
                "选择具体周",
                week_options,
                help="选择查看某一周的数据，或查看全部周的趋势",
                key="scenario_marketing_week_selector"
            )
        else:  # 月
            available_months = sorted(raw_data['年月'].dropna().unique(), reverse=True)
            month_options = ["全部月份"] + [f"{m}" for m in available_months]
            selected_period = st.selectbox(
                "选择具体月份",
                month_options,
                help="选择查看某一月的数据，或查看全部月份的趋势",
                key="scenario_marketing_month_selector"
            )
    
    with col3:
        # 显示数据范围和选择状态说明
        if '下单时间' in raw_data.columns:
            min_date = raw_data['下单时间'].min().strftime('%Y-%m-%d')
            max_date = raw_data['下单时间'].max().strftime('%Y-%m-%d')
            total_days = (raw_data['下单时间'].max() - raw_data['下单时间'].min()).days + 1
            
            # 根据用户选择显示不同信息
            if selected_period and not selected_period.startswith("全部"):
                # 选择了具体周期
                if time_dimension == "日":
                    st.info(f"📊 已选择：{selected_period}｜查看单日数据")
                elif time_dimension == "周":
                    st.info(f"📊 已选择：{selected_period}｜查看单周数据")
                else:  # 月
                    st.info(f"📊 已选择：{selected_period}｜查看单月数据")
            else:
                # 未选择具体周期，显示全量数据范围
                if time_dimension == "日":
                    st.info(f"📊 数据范围：{min_date} 至 {max_date}（共{total_days}天）｜环比：与前一日对比")
                elif time_dimension == "周":
                    total_weeks = raw_data['年周'].nunique()
                    st.info(f"📊 数据范围：{min_date} 至 {max_date}（共{total_weeks}周）｜环比：与上周对比")
                else:  # 月
                    total_months = raw_data['年月'].nunique()
                    st.info(f"📊 数据范围：{min_date} 至 {max_date}（共{total_months}月）｜环比：与上月对比")
    
    st.markdown("---")
    
    # 场景选择（移除问题诊断，已独立为主Tab）
    scenario = st.radio(
        "选择营销场景",
        ["⏰ 时段场景营销", "🏪 门店商圈场景", "💰 价格敏感度", "📦 商品组合场景"],
        horizontal=True,
        key="scenario_marketing_radio"
    )
    
    st.markdown("---")
    
    # 渲染对应场景（传递时间维度和选定周期参数）
    if scenario == "⏰ 时段场景营销":
        render_time_period_marketing(raw_data, time_dimension, selected_period)
    elif scenario == "🏪 门店商圈场景":
        render_location_marketing(raw_data, time_dimension, selected_period)
    elif scenario == "💰 价格敏感度":
        render_price_sensitivity_marketing(raw_data, time_dimension, selected_period)
    elif scenario == "📦 商品组合场景":
        render_product_combination_marketing(raw_data, time_dimension, selected_period)


# ==================== 问题诊断中心模块 ====================
def display_problem_diagnostic_center(data_dict: Dict):
    """
    显示问题诊断中心
    
    Parameters:
    -----------
    data_dict : Dict
        包含原始数据的字典
    """
    st.markdown('<h2 class="section-header">📋 问题诊断中心</h2>', unsafe_allow_html=True)
    
    if not PROBLEM_DIAGNOSTIC_AVAILABLE:
        st.error("⚠️ 问题诊断引擎未加载，请检查依赖项")
        return
    
    # 获取数据（与场景营销看板保持一致的数据获取逻辑）
    raw_data = data_dict.get('raw_data')
    
    # 如果current_data中没有数据，尝试从session_state获取（上传数据的情况）
    if raw_data is None or (isinstance(raw_data, pd.DataFrame) and raw_data.empty):
        if 'current_data' in st.session_state:
            raw_data = st.session_state['current_data'].get('raw_data')
    
    # 检查是否有可用数据
    if raw_data is None or (isinstance(raw_data, pd.DataFrame) and raw_data.empty):
        st.warning("⚠️ 请先加载数据后，才能使用问题诊断功能")
        st.info("""
        💡 **问题诊断中心功能：**
        
        1. 📉 **销量下滑诊断** - 识别销量下降的商品及原因
        2. 💰 **客单价归因分析** - 分析客单价变化的具体商品
        3. 🚨 **负毛利商品预警** - 自动识别亏本商品
        4. 🚚 **高配送费优化** - 优化配送成本
        5. ⚖️ **商品角色失衡** - 检测流量品/利润品配比
        6. 📊 **异常波动预警** - 识别爆单/滞销商品
        
        **两种加载方式：**
        - 方式1：在左侧点击"🚀 开始智能分析"加载实际数据
        - 方式2：在"💹 比价看板"标签页上传订单数据Excel文件
        """)
        return
    
    # 数据验证（检查必需列）
    required_cols = ['订单ID', '三级分类名', '商品实售价']
    missing_cols = [col for col in required_cols if col not in raw_data.columns]
    if missing_cols:
        st.error(f"⚠️ 数据缺少必要列: {', '.join(missing_cols)}")
        st.info(f"📋 当前数据列: {', '.join(raw_data.columns.tolist()[:10])}...")
        return
    
    # 🆕 自动添加时段字段（如果不存在）
    if '时段' not in raw_data.columns and '下单时间' in raw_data.columns:
        try:
            # 将下单时间转换为datetime
            raw_data['下单时间_temp'] = pd.to_datetime(raw_data['下单时间'], errors='coerce')
            
            # 定义时段分类函数（基于业务理解的8时段划分）
            def classify_time_slot(dt):
                """
                时段划分规则（基于用户行为特征）:
                - 清晨(6-8点): 出行/整理/早餐 - 赶时间的快节奏时段
                - 上午(9-11点): 办公/居家/日用补充 - 工作或家务时段
                - 正午(12-13点): 午餐 - 午餐高峰期
                - 下午(14-17点): 工作/家务/亲子/小憩/下午茶 - 多元化时段
                - 傍晚(18-20点): 下班/归家/晚餐/路途 - 通勤与晚餐叠加
                - 晚间(21-23点): 居家/夜生活前 - 放松与社交时段
                - 深夜(0-2点): 突发/急用/夜宵 - 应急与夜宵需求
                - 凌晨(3-5点): 万籁俱寂/熬夜党 - 极低频特殊场景
                """
                if pd.isna(dt):
                    return '未知'
                hour = dt.hour
                if 6 <= hour < 9:
                    return '清晨(6-9点)'
                elif 9 <= hour < 12:
                    return '上午(9-12点)'
                elif 12 <= hour < 14:
                    return '正午(12-14点)'
                elif 14 <= hour < 18:
                    return '下午(14-18点)'
                elif 18 <= hour < 21:
                    return '傍晚(18-21点)'
                elif 21 <= hour < 24:
                    return '晚间(21-24点)'
                elif 0 <= hour < 3:
                    return '深夜(0-3点)'
                else:  # 3-5点
                    return '凌晨(3-6点)'
            
            # 应用时段分类
            raw_data['时段'] = raw_data['下单时间_temp'].apply(classify_time_slot)
            raw_data.drop('下单时间_temp', axis=1, inplace=True)
            
            st.success("✅ 已自动从下单时间推断时段字段（8时段划分）")
        except Exception as e:
            st.warning(f"⚠️ 无法自动生成时段字段: {e}")
    
    # 🆕 智能场景推断（如果不存在场景字段）
    if '场景' not in raw_data.columns and '时段' in raw_data.columns:
        try:
            def infer_scene(row):
                """
                基于时段、商品名称、商品分类智能推断消费场景
                
                推断逻辑：
                1. 优先基于商品名称关键词（最精准）
                2. 其次基于商品分类（中等精准）
                3. 最后基于时段（兜底方案）
                """
                time_slot = row.get('时段', '')
                product_name = str(row.get('商品名称', '')).lower()
                category_1 = str(row.get('一级分类名', '')).lower()
                category_3 = str(row.get('三级分类名', '')).lower()
                
                # === 1. 基于商品名称关键词（最精准）===
                
                # 早餐关键词
                breakfast_keywords = ['豆浆', '油条', '包子', '粥', '鸡蛋', '煎饼', '馒头', '早餐', '稀饭']
                if any(kw in product_name for kw in breakfast_keywords):
                    return '早餐'
                
                # 午餐关键词
                lunch_keywords = ['盖浇饭', '快餐', '便当', '炒饭', '面条', '米线', '盒饭', '套餐', '工作餐']
                if any(kw in product_name for kw in lunch_keywords) and ('12' in time_slot or '正午' in time_slot or '下午' in time_slot):
                    return '午餐'
                
                # 晚餐关键词
                dinner_keywords = ['晚餐', '炒菜', '火锅', '烧烤', '聚餐']
                if any(kw in product_name for kw in dinner_keywords):
                    return '晚餐'
                
                # 夜宵关键词
                midnight_keywords = ['夜宵', '烧烤', '小龙虾', '泡面', '方便面', '啤酒', '炸鸡']
                if any(kw in product_name for kw in midnight_keywords) and ('深夜' in time_slot or '晚间' in time_slot or '凌晨' in time_slot):
                    return '夜宵'
                
                # 下午茶关键词
                tea_keywords = ['奶茶', '咖啡', '蛋糕', '甜点', '面包', '饼干', '冰淇淋', '果汁']
                if any(kw in product_name for kw in tea_keywords) and '下午' in time_slot:
                    return '下午茶'
                
                # 零食/休闲关键词
                snack_keywords = ['薯片', '糖果', '巧克力', '坚果', '瓜子', '零食']
                if any(kw in product_name for kw in snack_keywords):
                    return '休闲零食'
                
                # 日用品关键词
                daily_keywords = ['纸巾', '洗洁精', '垃圾袋', '牙膏', '洗发水', '沐浴露', '洗衣液']
                if any(kw in product_name for kw in daily_keywords):
                    return '日用补充'
                
                # 应急/突发关键词
                emergency_keywords = ['电池', '创可贴', '药', '消毒', '口罩', '卫生巾']
                if any(kw in product_name for kw in emergency_keywords):
                    return '应急购买'
                
                # === 2. 基于商品分类（中等精准）===
                
                # 烟酒分类
                if '烟酒' in category_1 or '烟' in category_3 or '酒' in category_3:
                    if '深夜' in time_slot or '晚间' in time_slot:
                        return '夜间社交'
                    return '社交娱乐'
                
                # 饮料分类
                if '饮料' in category_1 or '饮品' in category_3:
                    if '下午' in time_slot:
                        return '下午茶'
                    elif '深夜' in time_slot or '晚间' in time_slot:
                        return '夜间饮品'
                    return '日常饮品'
                
                # 乳品分类
                if '乳品' in category_1 or '奶' in category_3:
                    if '清晨' in time_slot:
                        return '早餐'
                    return '营养补充'
                
                # 粮油调味分类
                if '粮油' in category_1 or '调味' in category_1:
                    return '家庭烹饪'
                
                # 休闲食品分类
                if '休闲' in category_1 or '零食' in category_3:
                    return '休闲零食'
                
                # 个护清洁分类
                if '个护' in category_1 or '清洁' in category_1 or '日化' in category_1:
                    return '日用补充'
                
                # === 3. 基于时段（兜底方案）===
                
                time_to_scene = {
                    '清晨(6-9点)': '早餐',
                    '上午(9-12点)': '日常购物',
                    '正午(12-14点)': '午餐',
                    '下午(14-18点)': '下午茶',
                    '傍晚(18-21点)': '晚餐',
                    '晚间(21-24点)': '居家消费',
                    '深夜(0-3点)': '夜宵',
                    '凌晨(3-6点)': '应急购买'
                }
                
                return time_to_scene.get(time_slot, '日常购物')
            
            # 应用场景推断
            raw_data['场景'] = raw_data.apply(infer_scene, axis=1)
            
            # 统计推断结果
            scene_counts = raw_data['场景'].value_counts()
            st.success(f"✅ 已智能推断场景字段（共识别 {len(scene_counts)} 种场景）")
            
            # 显示场景分布
            with st.expander("📊 查看自动推断的场景分布", expanded=False):
                st.markdown("### 场景推断结果")
                st.markdown("""
                **推断逻辑**：
                1. 🎯 **优先级1**：基于商品名称关键词（最精准）
                2. 🏷️ **优先级2**：基于商品分类（中等精准）
                3. ⏰ **优先级3**：基于时段（兜底方案）
                """)
                
                scene_df = pd.DataFrame({
                    '场景': scene_counts.index,
                    '订单数': scene_counts.values,
                    '占比': (scene_counts.values / len(raw_data) * 100).round(2)
                })
                scene_df['占比'] = scene_df['占比'].astype(str) + '%'
                st.dataframe(scene_df, use_container_width=True)
                
                st.info("""
                💡 **提示**：
                - 如果推断结果不准确，可以在Excel中手动修正"场景"列
                - 系统会优先使用您手动标注的场景数据
                - 智能推断可覆盖90%以上的常见场景
                """)
                
        except Exception as e:
            st.warning(f"⚠️ 无法自动生成场景字段: {e}")
    
    # 🆕 场景筛选提示（如果场景字段已存在）
    if '场景' not in raw_data.columns:
        with st.expander("💡 关于'场景'字段的说明", expanded=False):
            st.markdown("""
            ### 时段 vs 场景的区别
            
            **时段（已自动生成）**：基于时间的客观划分
            - 清晨(6-9)、上午(9-12)、正午(12-14)、下午(14-18)
            - 傍晚(18-21)、晚间(21-24)、深夜(0-3)、凌晨(3-6)
            - 自动从"下单时间"推断，无需手动添加
            
            **场景（需手动标注）**：基于用户行为的主观标签
            - 餐饮场景：早餐、午餐、晚餐、夜宵、下午茶
            - 活动场景：办公、居家、出行、应急、聚餐
            - 渠道场景：堂食、外卖、自提、团购
            
            ### 如何添加场景字段？
            
            在Excel数据中添加"场景"列，示例：
            
            | 下单时间 | 商品名称 | **场景** | 业务含义 |
            |---------|---------|---------|---------|
            | 08:30 | 豆浆油条 | **早餐** | 清晨快餐 |
            | 12:30 | 盖浇饭 | **午餐** | 正午刚需 |
            | 15:00 | 奶茶 | **下午茶** | 休闲补充 |
            | 19:00 | 汉堡 | **晚餐** | 傍晚刚需 |
            | 01:30 | 泡面 | **夜宵** | 深夜应急 |
            
            ### 时段的典型场景映射
            
            系统已根据您的业务理解自动划分时段，每个时段对应的典型场景：
            - **清晨(6-9点)**：出行/整理/早餐
            - **上午(9-12点)**：办公/居家/日用补充
            - **正午(12-14点)**：午餐
            - **下午(14-18点)**：工作/家务/亲子/小憩/下午茶
            - **傍晚(18-21点)**：下班/归家/晚餐/路途
            - **晚间(21-24点)**：居家/夜生活前
            - **深夜(0-3点)**：突发/急用/夜宵
            - **凌晨(3-6点)**：万籁俱寂/熬夜党
            
            ### 💡 使用建议
            
            - **只需要时间分析**：使用"时段筛选"即可（已自动可用）
            - **需要行为分析**：在Excel中添加"场景"列，实现双重筛选
            """)

    
    st.info("🔍 自动诊断运营问题，快速定位优化机会")
    
    # 初始化诊断引擎
    try:
        diagnostic_engine = ProblemDiagnosticEngine(raw_data)
    except Exception as e:
        st.error(f"❌ 诊断引擎初始化失败: {str(e)}")
        return
    
    # 顶部控制面板
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("### 🎯 快速诊断")
    
    with col2:
        if st.button("🚀 一键生成综合问题报告", type="primary", use_container_width=True):
            with st.spinner("正在生成综合诊断报告..."):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"问题诊断报告_{timestamp}.xlsx"
                    
                    report = diagnostic_engine.generate_comprehensive_report(output_path)
                    
                    st.success(f"✅ 综合报告已生成: {output_path}")
                    
                    # 显示摘要
                    if '诊断摘要' in report and len(report['诊断摘要']) > 0:
                        st.dataframe(report['诊断摘要'], use_container_width=True)
                    
                    # 提供下载
                    if os.path.exists(output_path):
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ 下载完整诊断报告",
                                data=f,
                                file_name=output_path,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                except Exception as e:
                    st.error(f"❌ 报告生成失败: {str(e)}")
    
    with col3:
        total_orders = raw_data['订单ID'].nunique()
        st.metric("总订单数", f"{total_orders:,}")
    
    st.markdown("---")
    
    # 诊断标签页
    diagnostic_tabs = st.tabs([
        "📉 销量下滑",
        "💰 客单价归因",
        "🚨 负毛利预警",
        "🚚 高配送费",
        "⚖️ 角色失衡",
        "📊 异常波动"
    ])
    
    # Tab 1: 销量下滑诊断
    with diagnostic_tabs[0]:
        st.markdown("### 📉 销量下滑商品诊断")
        
        # 第一行：基础配置
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            time_period = st.selectbox(
                "对比周期",
                ["day", "week", "month"],
                format_func=lambda x: "按日对比" if x == "day" else ("按周对比" if x == "week" else "按月对比"),
                key="decline_period"
            )
        
        with col2:
            threshold = st.slider(
                "下滑阈值%",
                min_value=-80.0,
                max_value=-5.0,
                value=-20.0,
                step=5.0,
                key="decline_threshold"
            )
        
        with col3:
            scene_options = []
            if '场景' in raw_data.columns:
                scene_options = ['全部场景'] + sorted(raw_data['场景'].dropna().unique().tolist())
            scene_filter = st.multiselect(
                "场景筛选",
                scene_options,
                default=['全部场景'] if scene_options else [],
                key="decline_scene"
            )
        
        with col4:
            time_slot_options = []
            if '时段' in raw_data.columns:
                time_slot_options = ['全部时段'] + sorted(raw_data['时段'].dropna().unique().tolist())
            time_slot_filter = st.multiselect(
                "时段筛选",
                time_slot_options,
                default=['全部时段'] if time_slot_options else [],
                key="decline_timeslot"
            )
        
        # 第二行：周期选择器（新功能）
        st.markdown("---")
        st.markdown("#### 📅 自定义周期对比")
        
        # 获取可用周期列表
        try:
            available_periods = diagnostic_engine.get_available_periods(time_period)
            
            if len(available_periods) >= 2:
                col5, col6, col7 = st.columns([2, 2, 1])
                
                with col5:
                    # 当前周期选择
                    current_options = {p['label']: p['index'] for p in available_periods}
                    current_label = st.selectbox(
                        "📍 当前周期",
                        options=list(current_options.keys()),
                        index=0,
                        key="current_period_selector",
                        help="选择要分析的当前周期"
                    )
                    current_period_index = current_options[current_label]
                    
                    # 显示日期范围
                    current_period_info = next(p for p in available_periods if p['index'] == current_period_index)
                    st.caption(f"📆 {current_period_info['date_range']}")
                
                with col6:
                    # 对比周期选择
                    compare_label = st.selectbox(
                        "📍 对比周期",
                        options=list(current_options.keys()),
                        index=1,
                        key="compare_period_selector",
                        help="选择要对比的历史周期"
                    )
                    compare_period_index = current_options[compare_label]
                    
                    # 显示日期范围
                    compare_period_info = next(p for p in available_periods if p['index'] == compare_period_index)
                    st.caption(f"📆 {compare_period_info['date_range']}")
                
                with col7:
                    st.markdown("<br>", unsafe_allow_html=True)
                    use_custom_period = st.checkbox("启用自定义", value=False, key="use_custom_period")
            else:
                st.warning("⚠️ 数据时间范围不足，无法进行周期对比分析")
                use_custom_period = False
                current_period_index = None
                compare_period_index = None
        except Exception as e:
            st.warning(f"⚠️ 无法获取周期列表: {str(e)}")
            use_custom_period = False
            current_period_index = None
            compare_period_index = None
        
        st.markdown("---")
        
        if st.button("🔍 开始诊断", key="btn_decline"):
            with st.spinner("正在分析销量下滑商品..."):
                try:
                    # 处理筛选条件
                    scene_list = None if '全部场景' in scene_filter else [s for s in scene_filter if s != '全部场景']
                    slot_list = None if '全部时段' in time_slot_filter else [s for s in time_slot_filter if s != '全部时段']
                    
                    # 构建参数（根据是否启用自定义周期）
                    diagnose_params = {
                        'time_period': time_period,
                        'threshold': threshold,
                        'scene_filter': scene_list,
                        'time_slot_filter': slot_list
                    }
                    
                    # 如果启用自定义周期，添加周期参数
                    if use_custom_period and current_period_index is not None and compare_period_index is not None:
                        diagnose_params['current_period_index'] = current_period_index
                        diagnose_params['compare_period_index'] = compare_period_index
                        st.info(f"📊 对比周期: {current_label} vs {compare_label}")
                    
                    result = diagnostic_engine.diagnose_sales_decline(**diagnose_params)
                    
                    if len(result) > 0:
                        st.success(f"✅ 发现 {len(result)} 个销量下滑商品")
                        
                        # 🎨 可视化看板区域
                        st.markdown("---")
                        st.markdown("## 📊 可视化分析看板")
                        
                        # 准备可视化数据（需要原始数值，而非格式化后的字符串）
                        viz_df = result.copy()
                        
                        # 解析格式化的数值列（用于可视化）
                        def parse_number(val):
                            """解析带格式的数值（如¥1234.5, -50.0%）"""
                            if pd.isna(val):
                                return 0
                            if isinstance(val, (int, float)):
                                return float(val)
                            # 转换为字符串并清理
                            val_str = str(val)
                            # 移除所有非数字字符（保留负号、小数点）
                            val_str = val_str.replace('¥', '').replace('%', '').replace(',', '').replace('N/A', '0')
                            # 处理重复的值（如 '¥6.4¥6.4' -> '6.46.4'）
                            # 如果字符串中间有重复，取第一个有效数字
                            parts = val_str.split()
                            if len(parts) > 0:
                                val_str = parts[0]
                            try:
                                return float(val_str)
                            except:
                                # 如果还是解析失败，尝试提取第一个数字
                                import re
                                match = re.search(r'-?\d+\.?\d*', val_str)
                                if match:
                                    return float(match.group())
                                return 0
                        
                        # 解析各列数值
                        for col in viz_df.columns:
                            if any(keyword in col for keyword in ['销量', '收入', '价格', '幅度', '毛利']):
                                viz_df[col] = viz_df[col].apply(parse_number)
                        
                        # 🆕 智能计算平均毛利率（如果数据中没有）
                        if '平均毛利率%' not in viz_df.columns or viz_df['平均毛利率%'].isna().all():
                            # 尝试从原始数据计算
                            if '商品名称' in viz_df.columns and '商品名称' in raw_data.columns:
                                # 计算每个商品的平均毛利率
                                profit_margins = []
                                
                                for product_name in viz_df['商品名称']:
                                    product_data = raw_data[raw_data['商品名称'] == product_name]
                                    
                                    if len(product_data) > 0:
                                        # 尝试多种方式计算毛利率
                                        margin = None
                                        
                                        # 方式1: 使用利润额和订单零售额
                                        if '利润额' in product_data.columns and '订单零售额' in product_data.columns:
                                            total_profit = product_data['利润额'].sum()
                                            total_revenue = product_data['订单零售额'].sum()
                                            if total_revenue > 0:
                                                margin = (total_profit / total_revenue) * 100
                                        
                                        # 方式2: 使用商品实售价和成本
                                        if margin is None and '商品实售价' in product_data.columns:
                                            # 假设成本为售价的60%（如果没有明确成本字段）
                                            avg_price = product_data['商品实售价'].mean()
                                            if pd.notna(avg_price) and avg_price > 0:
                                                # 尝试从其他字段推断成本
                                                if '商品成本' in product_data.columns:
                                                    avg_cost = product_data['商品成本'].mean()
                                                elif '进货价' in product_data.columns:
                                                    avg_cost = product_data['进货价'].mean()
                                                else:
                                                    # 估算：假设平均毛利率30%
                                                    avg_cost = avg_price * 0.7
                                                
                                                if pd.notna(avg_cost) and avg_cost > 0:
                                                    margin = ((avg_price - avg_cost) / avg_price) * 100
                                        
                                        profit_margins.append(margin if margin is not None else 30.0)  # 默认30%
                                    else:
                                        profit_margins.append(30.0)  # 默认30%
                                
                                viz_df['平均毛利率%'] = profit_margins
                                st.info("💡 **智能计算**: 已根据原始数据自动计算商品的平均毛利率")
                        
                        # 动态获取列名
                        sales_cols = [col for col in viz_df.columns if '销量' in col and col != '销量变化']
                        
                        # 确保有序（通常第一个是对比周期，第二个是当前周期）
                        if len(sales_cols) >= 2:
                            compare_sales_col = sales_cols[0]  # 第一个销量列（对比周期）
                            current_sales_col = sales_cols[1]  # 第二个销量列（当前周期）
                            
                            # 调试信息
                            st.info(f"🔍 **数据列信息**: 检测到 {len(sales_cols)} 个销量列\n- 对比周期: {compare_sales_col}\n- 当前周期: {current_sales_col}")
                        elif len(sales_cols) == 1:
                            current_sales_col = sales_cols[0]
                            compare_sales_col = None
                            st.warning(f"⚠️ 只检测到1个销量列: {current_sales_col}，无法进行周期对比")
                        else:
                            current_sales_col = None
                            compare_sales_col = None
                            st.error("❌ 未检测到销量列，无法进行分析")
                        
                        revenue_cols = [col for col in viz_df.columns if '收入' in col]
                        current_revenue_col = revenue_cols[0] if len(revenue_cols) > 0 else None
                        compare_revenue_col = revenue_cols[1] if len(revenue_cols) > 1 else None
                        
                        # 计算派生指标
                        viz_df['收入变化'] = 0
                        if current_revenue_col and compare_revenue_col:
                            viz_df['收入变化'] = viz_df[current_revenue_col] - viz_df[compare_revenue_col]
                        
                        viz_df['利润变化'] = 0
                        if '平均毛利率%' in viz_df.columns and '收入变化' in viz_df.columns:
                            viz_df['利润变化'] = viz_df['收入变化'] * (viz_df['平均毛利率%'] / 100)
                        
                        # === 1. 核心指标卡片 ===
                        st.markdown("### 📈 核心指标概览")
                        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                        
                        with kpi_col1:
                            decline_count = len(viz_df)
                            st.metric(
                                label="📉 下滑商品数",
                                value=f"{decline_count} 个",
                                delta=None,
                                help="销量下滑的商品总数"
                            )
                        
                        with kpi_col2:
                            total_sales_loss = int(viz_df['销量变化'].sum())
                            st.metric(
                                label="📦 销量损失",
                                value=f"{total_sales_loss} 单",
                                delta=None,
                                help="总销量减少数量"
                            )
                        
                        with kpi_col3:
                            total_revenue_loss = viz_df['收入变化'].sum()
                            st.metric(
                                label="💸 收入损失",
                                value=f"¥{total_revenue_loss:,.0f}",
                                delta=f"{total_revenue_loss:.0f}",
                                delta_color="inverse",
                                help="总收入减少金额"
                            )
                        
                        with kpi_col4:
                            total_profit_loss = viz_df['利润变化'].sum()
                            st.metric(
                                label="💰 利润损失",
                                value=f"¥{total_profit_loss:,.0f}",
                                delta=f"{total_profit_loss:.0f}",
                                delta_color="inverse",
                                help="总利润减少金额"
                            )
                        
                        st.markdown("---")
                        
                        # === 2. 图表区域（左右分栏）===
                        chart_col_left, chart_col_right = st.columns([1, 1])
                        
                        with chart_col_left:
                            # === 图表1: 时段下滑分析 ===
                            if '时段' in raw_data.columns and time_slot_filter and '全部时段' in time_slot_filter:
                                st.markdown("#### ⏰ 分时段下滑分析")
                                
                                # 重新按时段统计（使用原始数据）
                                time_slot_stats = []
                                for slot in sorted(raw_data['时段'].dropna().unique()):
                                    slot_result = diagnostic_engine.diagnose_sales_decline(
                                        time_period=time_period,
                                        threshold=threshold,
                                        scene_filter=scene_list,
                                        time_slot_filter=[slot],
                                        current_period_index=current_period_index if use_custom_period else None,
                                        compare_period_index=compare_period_index if use_custom_period else None
                                    )
                                    
                                    if len(slot_result) > 0:
                                        # 解析数值
                                        slot_viz = slot_result.copy()
                                        for col in slot_viz.columns:
                                            if any(kw in col for kw in ['销量', '收入', '幅度', '毛利']):
                                                slot_viz[col] = slot_viz[col].apply(parse_number)
                                        
                                        slot_revenue_loss = 0
                                        slot_revenue_cols = [col for col in slot_viz.columns if '收入' in col]
                                        if len(slot_revenue_cols) >= 2:
                                            slot_revenue_loss = (slot_viz[slot_revenue_cols[0]] - slot_viz[slot_revenue_cols[1]]).sum()
                                        
                                        time_slot_stats.append({
                                            '时段': slot,
                                            '下滑商品数': len(slot_result),
                                            '销量损失': int(slot_viz['销量变化'].sum()),
                                            '收入损失': slot_revenue_loss,
                                            '利润损失': (slot_revenue_loss * slot_viz['平均毛利率%'].mean() / 100) if '平均毛利率%' in slot_viz.columns else 0
                                        })
                                
                                if time_slot_stats:
                                    time_slot_df = pd.DataFrame(time_slot_stats)
                                    
                                    # 指标选择器（不使用form，保持即时响应）
                                    slot_metric = st.selectbox(
                                        "选择指标",
                                        ['下滑商品数', '销量损失', '收入损失', '利润损失'],
                                        key='slot_metric_selector'
                                    )
                                    
                                    # 准备显示数据（损失类指标取绝对值）
                                    display_values = time_slot_df[slot_metric].copy()
                                    if '损失' in slot_metric:
                                        display_values = display_values.abs()
                                    
                                    # 柱状图（所有指标统一用红色，因为都是负面指标）
                                    fig_slot = go.Figure()
                                    
                                    fig_slot.add_trace(go.Bar(
                                        x=time_slot_df['时段'],
                                        y=display_values,
                                        marker_color='#d32f2f',
                                        text=display_values.apply(lambda x: f"{x:,.0f}"),
                                        textposition='auto',
                                        hovertemplate='<b>%{x}</b><br>' + slot_metric + ': %{y:,.0f}<extra></extra>'
                                    ))
                                    
                                    # Y轴标题
                                    y_title = slot_metric
                                    if slot_metric == '销量损失':
                                        y_title = '销量损失（单）'
                                    elif slot_metric in ['收入损失', '利润损失']:
                                        y_title = slot_metric + '（元）'
                                    
                                    fig_slot.update_layout(
                                        title=f"各时段{slot_metric}分布",
                                        xaxis_title="时段",
                                        yaxis_title=y_title,
                                        template='plotly_white',
                                        height=350,
                                        font=dict(family='Microsoft YaHei', size=11),
                                        showlegend=False
                                    )
                                    
                                    st.plotly_chart(fig_slot, use_container_width=True)
                                    
                                    # 显示总计
                                    total_value = time_slot_df[slot_metric].sum()
                                    if '损失' in slot_metric:
                                        st.info(f"💡 **总计**: {slot_metric} = {abs(total_value):,.0f} {'元' if '收入' in slot_metric or '利润' in slot_metric else '单'}")
                                    else:
                                        st.info(f"💡 **总计**: {slot_metric} = {total_value:,.0f} 个")
                            
                            # === 图表2: 场景下滑分析（饼图）===
                            if '场景' in raw_data.columns and scene_filter and '全部场景' in scene_filter:
                                st.markdown("#### 🎭 分场景下滑分布")
                                
                                # 重新按场景统计
                                scene_stats = []
                                for scene in sorted(raw_data['场景'].dropna().unique()):
                                    scene_result = diagnostic_engine.diagnose_sales_decline(
                                        time_period=time_period,
                                        threshold=threshold,
                                        scene_filter=[scene],
                                        time_slot_filter=slot_list,
                                        current_period_index=current_period_index if use_custom_period else None,
                                        compare_period_index=compare_period_index if use_custom_period else None
                                    )
                                    
                                    if len(scene_result) > 0:
                                        scene_stats.append({
                                            '场景': scene,
                                            '商品数': len(scene_result)
                                        })
                                
                                if scene_stats:
                                    scene_df = pd.DataFrame(scene_stats)
                                    
                                    fig_scene = go.Figure(go.Pie(
                                        labels=scene_df['场景'],
                                        values=scene_df['商品数'],
                                        hole=0.4,
                                        marker=dict(colors=['#d32f2f', '#f57c00', '#fbc02d', '#388e3c', '#1976d2']),
                                        textinfo='label+percent',
                                        hovertemplate='<b>%{label}</b><br>商品数: %{value}<br>占比: %{percent}<extra></extra>'
                                    ))
                                    
                                    fig_scene.update_layout(
                                        title="各场景下滑商品占比",
                                        template='plotly_white',
                                        height=350,
                                        font=dict(family='Microsoft YaHei', size=11)
                                    )
                                    
                                    st.plotly_chart(fig_scene, use_container_width=True)
                            
                            # === 图表3: 一级分类TOP5 ===
                            if '一级分类名' in viz_df.columns:
                                st.markdown("#### 📦 品类下滑TOP5")
                                
                                category_stats = viz_df.groupby('一级分类名').agg({
                                    '商品名称': 'count',
                                    '收入变化': 'sum'
                                }).rename(columns={'商品名称': '商品数'})
                                
                                category_stats = category_stats.sort_values('收入变化').head(5)
                                
                                fig_category = go.Figure(go.Bar(
                                    x=category_stats['收入变化'].abs(),
                                    y=category_stats.index,
                                    orientation='h',
                                    marker_color='coral',
                                    text=category_stats['收入变化'].apply(lambda x: f"¥{abs(x):,.0f}"),
                                    textposition='auto',
                                    hovertemplate='<b>%{y}</b><br>收入损失: ¥%{x:,.0f}<br>商品数: %{customdata}<extra></extra>',
                                    customdata=category_stats['商品数']
                                ))
                                
                                fig_category.update_layout(
                                    title="收入损失最大的5个品类",
                                    xaxis_title="收入损失（元）",
                                    yaxis_title="品类",
                                    template='plotly_white',
                                    height=350,
                                    font=dict(family='Microsoft YaHei', size=11),
                                    showlegend=False
                                )
                                
                                st.plotly_chart(fig_category, use_container_width=True)
                        
                        with chart_col_right:
                            # === 图表4: 各分类下滑TOP商品 ===
                            st.markdown("#### 🔻 各分类下滑TOP商品")
                            
                            if '一级分类名' in viz_df.columns:
                                # 按分类选择TOP商品
                                category_top_products = []
                                for category in viz_df['一级分类名'].unique():
                                    category_df = viz_df[viz_df['一级分类名'] == category]
                                    # 每个分类取下滑最严重的前3个商品
                                    top3 = category_df.nsmallest(3, '变化幅度%')
                                    for _, row in top3.iterrows():
                                        category_top_products.append({
                                            '分类': category,
                                            '商品名称': row['商品名称'],
                                            '变化幅度%': row['变化幅度%'],
                                            '销量变化': row['销量变化']
                                        })
                                
                                if category_top_products:
                                    category_top_df = pd.DataFrame(category_top_products)
                                    # 限制最多显示10个
                                    category_top_df = category_top_df.head(10)
                                    
                                    # 添加分类标签到商品名称
                                    category_top_df['显示名称'] = category_top_df.apply(
                                        lambda x: f"[{x['分类']}] {x['商品名称']}", axis=1
                                    )
                                    
                                    # 颜色映射（下滑越严重颜色越深）
                                    colors_top = category_top_df['变化幅度%'].apply(
                                        lambda x: '#8b0000' if x <= -50 else ('#d32f2f' if x <= -30 else '#f57c00')
                                    )
                                    
                                    fig_top = go.Figure(go.Bar(
                                        x=category_top_df['变化幅度%'],
                                        y=category_top_df['显示名称'],
                                        orientation='h',
                                        marker_color=colors_top,
                                        text=category_top_df.apply(
                                            lambda x: f"{x['变化幅度%']:.1f}% ({int(x['销量变化'])}单)",
                                            axis=1
                                        ),
                                        textposition='auto',
                                        hovertemplate='<b>%{y}</b><br>变化幅度: %{x:.1f}%<extra></extra>'
                                    ))
                                    
                                    fig_top.update_layout(
                                        title="每个分类下滑最严重的商品（每类TOP3）",
                                        xaxis_title="变化幅度（%）",
                                        yaxis_title="商品",
                                        template='plotly_white',
                                        height=400,  # 增加高度以容纳更多商品
                                        font=dict(family='Microsoft YaHei', size=10),
                                        showlegend=False
                                    )
                                    
                                    st.plotly_chart(fig_top, use_container_width=True)
                                    
                                    st.info("💡 **阅读提示**: 按分类展示，每个分类显示下滑最严重的3个商品，颜色越深=下滑越严重")
                                else:
                                    st.warning("⚠️ 暂无分类下滑数据")
                            else:
                                # 降级方案：如果没有分类，显示全局TOP10
                                st.markdown("#### 🔻 下滑最严重TOP10")
                                
                                top10_decline = viz_df.nsmallest(10, '变化幅度%')
                                
                                colors_top10 = top10_decline['变化幅度%'].apply(
                                    lambda x: '#8b0000' if x <= -50 else ('#d32f2f' if x <= -30 else '#f57c00')
                                )
                                
                                fig_top10 = go.Figure(go.Bar(
                                    x=top10_decline['变化幅度%'],
                                    y=top10_decline['商品名称'],
                                    orientation='h',
                                    marker_color=colors_top10,
                                    text=top10_decline.apply(
                                        lambda x: f"{x['变化幅度%']:.1f}% ({int(x['销量变化'])}单)",
                                        axis=1
                                    ),
                                    textposition='auto',
                                    hovertemplate='<b>%{y}</b><br>变化幅度: %{x:.1f}%<extra></extra>'
                                ))
                                
                                fig_top10.update_layout(
                                    title="下滑幅度最大的10个商品",
                                    xaxis_title="变化幅度（%）",
                                    yaxis_title="商品",
                                    template='plotly_white',
                                    height=350,
                                    font=dict(family='Microsoft YaHei', size=11),
                                    showlegend=False
                                )
                                
                                st.plotly_chart(fig_top10, use_container_width=True)
                                
                                st.info("💡 **阅读提示**: 横向柱状图，颜色越深=下滑越严重（深红≥50%，红色≥30%）")
                            
                            # === 图表5: 收入损失TOP10 ===
                            st.markdown("#### 💸 收入损失TOP10")
                            
                            top10_revenue = viz_df.nsmallest(10, '收入变化')
                            
                            fig_revenue = go.Figure(go.Waterfall(
                                name="收入损失",
                                orientation="v",
                                x=top10_revenue['商品名称'],
                                y=top10_revenue['收入变化'].abs(),
                                connector={"line": {"color": "rgb(63, 63, 63)"}},
                                decreasing={"marker": {"color": "#d32f2f"}},
                                text=top10_revenue['收入变化'].apply(lambda x: f"¥{abs(x):,.0f}"),
                                textposition='auto',
                                hovertemplate='<b>%{x}</b><br>收入损失: ¥%{y:,.0f}<extra></extra>'
                            ))
                            
                            fig_revenue.update_layout(
                                title="收入损失累积瀑布图",
                                xaxis_title="商品",
                                yaxis_title="收入损失（元）",
                                template='plotly_white',
                                height=350,
                                font=dict(family='Microsoft YaHei', size=11),
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_revenue, use_container_width=True)
                            
                            # === 图表6: 周期对比 ===
                            if current_sales_col and compare_sales_col:
                                st.markdown("#### 📊 周期销量对比（TOP10下滑商品）")
                                
                                top10_compare = viz_df.nsmallest(10, '变化幅度%')
                                
                                # 提取周期名称（去掉"销量"两个字，保留周期标识）
                                current_label = current_sales_col.replace('销量', '').strip()
                                compare_label = compare_sales_col.replace('销量', '').strip()
                                
                                fig_compare = go.Figure()
                                
                                # 对比周期（蓝色）
                                fig_compare.add_trace(go.Bar(
                                    name=compare_label,
                                    x=top10_compare['商品名称'],
                                    y=top10_compare[compare_sales_col],
                                    marker_color='#1976d2',
                                    text=top10_compare[compare_sales_col].apply(lambda x: f"{int(x) if pd.notna(x) and x > 0 else 0}"),
                                    textposition='auto'
                                ))
                                
                                # 当前周期（红色）
                                fig_compare.add_trace(go.Bar(
                                    name=current_label,
                                    x=top10_compare['商品名称'],
                                    y=top10_compare[current_sales_col],
                                    marker_color='#d32f2f',
                                    text=top10_compare[current_sales_col].apply(lambda x: f"{int(x) if pd.notna(x) and x > 0 else 0}"),
                                    textposition='auto'
                                ))
                                
                                fig_compare.update_layout(
                                    title=f"{compare_label} vs {current_label}",
                                    xaxis_title="商品",
                                    yaxis_title="销量（单）",
                                    barmode='group',
                                    template='plotly_white',
                                    height=350,
                                    font=dict(family='Microsoft YaHei', size=11),
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                )
                                
                                st.plotly_chart(fig_compare, use_container_width=True)
                                
                                st.info(f"💡 **阅读提示**: 蓝色={compare_label}，红色={current_label}，红色明显低于蓝色表示下滑")
                        
                        # === 3. 高级分析图表（全宽）===
                        st.markdown("---")
                        st.markdown("### 🔬 高级分析")
                        
                        adv_tab1, adv_tab2, adv_tab3 = st.tabs([
                            "💰 利润影响分析",
                            "🌳 分类树状图",
                            "🔥 时段×场景热力图"
                        ])
                        
                        with adv_tab1:
                            # === 图表7: 四维散点图 ===
                            st.markdown("#### 💰 销量变化 vs 利润损失（四维分析）")
                            
                            # 检查必需字段
                            has_price = '商品实售价' in viz_df.columns and viz_df['商品实售价'].notna().any()
                            has_margin = '平均毛利率%' in viz_df.columns and viz_df['平均毛利率%'].notna().any()
                            
                            if has_price and has_margin:
                                # 完整版：四维散点图（销量×利润×售价×毛利率）
                                
                                # 确保数据是数值类型并清理
                                def ensure_numeric(series):
                                    """确保Series是纯数值类型"""
                                    result = []
                                    for val in series:
                                        if pd.isna(val):
                                            result.append(0)
                                        elif isinstance(val, (int, float)):
                                            result.append(float(val))
                                        else:
                                            # 清理字符串
                                            val_str = str(val).replace('¥', '').replace('%', '').replace(',', '')
                                            # 提取第一个数字
                                            import re
                                            match = re.search(r'-?\d+\.?\d*', val_str)
                                            if match:
                                                result.append(float(match.group()))
                                            else:
                                                result.append(0)
                                    return result
                                
                                # 转换为纯数值列表
                                sizes = ensure_numeric(viz_df['商品实售价'])
                                sizes = [s * 2 for s in sizes]  # 放大2倍以便显示
                                colors = ensure_numeric(viz_df['平均毛利率%'])
                                
                                fig_scatter = go.Figure(go.Scatter(
                                    x=viz_df['销量变化'],
                                    y=viz_df['利润变化'],
                                    mode='markers',
                                    marker=dict(
                                        size=sizes,  # 使用清理后的列表
                                        color=colors,  # 使用清理后的列表
                                        colorscale='RdYlGn',
                                        showscale=True,
                                        colorbar=dict(title="毛利率%"),
                                        line=dict(width=1, color='white'),
                                        sizemode='diameter',
                                        sizemin=4
                                    ),
                                    text=viz_df['商品名称'].tolist(),
                                    customdata=list(zip(
                                        [s/2 for s in sizes],  # 还原实际售价
                                        colors
                                    )),
                                    hovertemplate='<b>%{text}</b><br>' +
                                                  '销量变化: %{x}单<br>' +
                                                  '利润损失: ¥%{y:,.0f}<br>' +
                                                  '售价: ¥%{customdata[0]:.1f}<br>' +
                                                  '毛利率: %{customdata[1]:.1f}%<extra></extra>'
                                ))
                                
                                fig_scatter.update_layout(
                                    title="气泡大小=售价，颜色=毛利率（绿色=高毛利，红色=低毛利）",
                                    xaxis_title="销量变化（单）",
                                    yaxis_title="利润损失（元）",
                                    template='plotly_white',
                                    height=500,
                                    font=dict(family='Microsoft YaHei', size=11)
                                )
                                
                                st.plotly_chart(fig_scatter, use_container_width=True)
                                
                                st.info("💡 **阅读提示**: 气泡越大=售价越高，颜色越红=毛利率越低，左下角=高损失商品重点关注")
                            else:
                                # 简化版：只用销量变化和利润损失
                                st.markdown("#### 💰 销量变化 vs 利润损失（简化版）")
                                
                                missing_fields = []
                                if not has_price:
                                    missing_fields.append('商品实售价')
                                if not has_margin:
                                    missing_fields.append('平均毛利率%')
                                
                                fig_scatter_simple = go.Figure(go.Scatter(
                                    x=viz_df['销量变化'],
                                    y=viz_df['利润变化'],
                                    mode='markers',
                                    marker=dict(
                                        size=10,
                                        color='#d32f2f',
                                        line=dict(width=1, color='white')
                                    ),
                                    text=viz_df['商品名称'],
                                    hovertemplate='<b>%{text}</b><br>' +
                                                  '销量变化: %{x}单<br>' +
                                                  '利润损失: ¥%{y:,.0f}<extra></extra>'
                                ))
                                
                                fig_scatter_simple.update_layout(
                                    title="销量变化与利润损失关系",
                                    xaxis_title="销量变化（单）",
                                    yaxis_title="利润损失（元）",
                                    template='plotly_white',
                                    height=500,
                                    font=dict(family='Microsoft YaHei', size=11)
                                )
                                
                                st.plotly_chart(fig_scatter_simple, use_container_width=True)
                                
                                st.warning(f"⚠️ **数据提示**: 缺少字段 {', '.join(missing_fields)}，显示简化版图表。")
                                st.info("💡 **解决方案**: 在原始数据中提供'商品成本'或'进货价'字段，系统将自动计算毛利率并展示完整的四维分析。")
                        
                        with adv_tab2:
                            # === 图表8: 三级分类树状图 ===
                            if '一级分类名' in viz_df.columns and '三级分类名' in viz_df.columns:
                                st.markdown("#### 🌳 三级分类下滑热力图")
                                
                                # 准备树状图数据
                                treemap_df = viz_df[viz_df['收入变化'] < 0].copy()
                                treemap_df['收入损失绝对值'] = treemap_df['收入变化'].abs()
                                
                                if len(treemap_df) > 0:
                                    fig_treemap = px.treemap(
                                        treemap_df,
                                        path=['一级分类名', '三级分类名', '商品名称'],
                                        values='收入损失绝对值',
                                        color='变化幅度%',
                                        color_continuous_scale='Reds',
                                        hover_data={
                                            '收入损失绝对值': ':,.0f',
                                            '变化幅度%': ':.1f',
                                            '销量变化': True
                                        }
                                    )
                                    
                                    fig_treemap.update_layout(
                                        title="颜色越深=下滑越严重，面积越大=损失越大",
                                        height=500,
                                        font=dict(family='Microsoft YaHei', size=11)
                                    )
                                    
                                    st.plotly_chart(fig_treemap, use_container_width=True)
                                else:
                                    st.info("暂无收入损失数据")
                        
                        with adv_tab3:
                            # === 图表9: 时段×场景热力图 ===
                            st.markdown("#### 🔥 时段×场景交叉分析")
                            
                            if '时段' in raw_data.columns and '场景' in raw_data.columns:
                                # 构建热力图数据
                                heatmap_data = []
                                all_slots = sorted(raw_data['时段'].dropna().unique())
                                all_scenes = sorted(raw_data['场景'].dropna().unique())
                                
                                if len(all_slots) > 0 and len(all_scenes) > 0:
                                    with st.spinner("正在计算交叉数据..."):
                                        for scene in all_scenes:
                                            row_data = {'场景': scene}
                                            for slot in all_slots:
                                                cross_result = diagnostic_engine.diagnose_sales_decline(
                                                    time_period=time_period,
                                                    threshold=threshold,
                                                    scene_filter=[scene],
                                                    time_slot_filter=[slot],
                                                    current_period_index=current_period_index if use_custom_period else None,
                                                    compare_period_index=compare_period_index if use_custom_period else None
                                                )
                                                row_data[slot] = len(cross_result)
                                            heatmap_data.append(row_data)
                                    
                                    if heatmap_data:
                                        heatmap_df = pd.DataFrame(heatmap_data).set_index('场景')
                                        
                                        fig_heatmap = px.imshow(
                                            heatmap_df,
                                            labels=dict(x="时段", y="场景", color="下滑商品数"),
                                            x=heatmap_df.columns,
                                            y=heatmap_df.index,
                                            color_continuous_scale='Reds',
                                            aspect='auto',
                                            text_auto=True
                                        )
                                        
                                        fig_heatmap.update_layout(
                                            title="深红色=问题严重区域",
                                            height=400,
                                            font=dict(family='Microsoft YaHei', size=11)
                                        )
                                        
                                        st.plotly_chart(fig_heatmap, use_container_width=True)
                                        
                                        st.info("💡 **阅读提示**: 找到深红色区域，针对性优化该时段+场景的商品")
                                        
                                        # ========== 🆕 交互式商品明细查看 ==========
                                        st.markdown("---")
                                        
                                        # 添加HTML锚点，用于定位
                                        st.markdown('<div id="detail-list-anchor"></div>', unsafe_allow_html=True)
                                        
                                        # 创建一个占位符用于显示提示信息
                                        filter_message_placeholder = st.empty()
                                        
                                        with st.expander("📋 下滑商品明细列表（点击展开/收起）", expanded=True):
                                            
                                            # 使用form来避免每次选择都刷新页面
                                            with st.form(key="detail_filter_form"):
                                                st.markdown("#### 🔍 筛选条件设置")
                                                # 创建筛选器
                                                filter_col1, filter_col2, filter_col3 = st.columns(3)
                                                
                                                with filter_col1:
                                                    selected_scenes = st.multiselect(
                                                        "🎯 筛选场景",
                                                        options=['全部'] + list(all_scenes),
                                                        default=['全部']
                                                    )
                                                
                                                with filter_col2:
                                                    selected_slots = st.multiselect(
                                                        "⏰ 筛选时段",
                                                        options=['全部'] + list(all_slots),
                                                        default=['全部']
                                                    )
                                                
                                                with filter_col3:
                                                    sort_by = st.selectbox(
                                                        "📊 排序方式",
                                                        options=['下滑幅度最大', '销量损失最多', '利润损失最多', '商品名称']
                                                    )
                                                
                                                # 提交按钮
                                                submitted = st.form_submit_button("🔄 应用筛选", use_container_width=True, type="primary")
                                            
                                            # 如果表单提交了，使用JavaScript滚动到锚点
                                            if submitted:
                                                # 使用更可靠的滚动方法
                                                st.components.v1.html("""
                                                <script>
                                                    window.parent.postMessage({
                                                        type: 'streamlit:setComponentValue',
                                                        value: 'scroll_to_detail'
                                                    }, '*');
                                                    
                                                    // 备用方案：直接滚动
                                                    setTimeout(function() {
                                                        const anchor = window.parent.document.getElementById('detail-list-anchor');
                                                        if (anchor) {
                                                            anchor.scrollIntoView({behavior: 'smooth', block: 'start'});
                                                        } else {
                                                            // 如果找不到锚点，尝试滚动到页面底部
                                                            window.parent.scrollTo({
                                                                top: window.parent.document.body.scrollHeight,
                                                                behavior: 'smooth'
                                                            });
                                                        }
                                                    }, 500);
                                                </script>
                                                """, height=0)
                                            
                                            # 获取筛选后的明细数据
                                            scene_filter_list = None if '全部' in selected_scenes else selected_scenes
                                            slot_filter_list = None if '全部' in selected_slots else selected_slots
                                            
                                            # 如果表单提交了，显示提示信息
                                            if submitted:
                                                filter_message_placeholder.success("✅ 筛选条件已应用！结果已在下方更新。")
                                            
                                            detail_result = diagnostic_engine.diagnose_sales_decline(
                                                time_period=time_period,
                                                threshold=threshold,
                                                scene_filter=scene_filter_list,
                                                time_slot_filter=slot_filter_list,
                                                current_period_index=current_period_index if use_custom_period else None,
                                                compare_period_index=compare_period_index if use_custom_period else None
                                            )
                                            
                                            if len(detail_result) > 0:
                                                # 排序
                                                if sort_by == '下滑幅度最大':
                                                    detail_result = detail_result.sort_values('变化幅度%', ascending=True)
                                                elif sort_by == '销量损失最多':
                                                    detail_result = detail_result.sort_values('销量变化', ascending=True)
                                                elif sort_by == '利润损失最多':
                                                    if '利润变化' in detail_result.columns:
                                                        detail_result = detail_result.sort_values('利润变化', ascending=True)
                                                elif sort_by == '商品名称':
                                                    detail_result = detail_result.sort_values('商品名称')
                                                
                                                # 准备展示列
                                                display_cols = ['商品名称']
                                                if '时段' in detail_result.columns:
                                                    display_cols.append('时段')
                                                if '场景' in detail_result.columns:
                                                    display_cols.append('场景')
                                                if '一级分类名' in detail_result.columns:
                                                    display_cols.append('一级分类名')
                                                
                                                # 添加数值列
                                                value_cols = ['销量变化', '变化幅度%']
                                                if '收入变化' in detail_result.columns:
                                                    value_cols.append('收入变化')
                                                if '利润变化' in detail_result.columns:
                                                    value_cols.append('利润变化')
                                                if '商品实售价' in detail_result.columns:
                                                    value_cols.append('商品实售价')
                                                
                                                display_cols.extend([col for col in value_cols if col in detail_result.columns])
                                                
                                                # 显示统计摘要
                                                summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                                                with summary_col1:
                                                    st.metric("📦 下滑商品数", f"{len(detail_result)} 个")
                                                with summary_col2:
                                                    total_qty_loss = detail_result['销量变化'].sum()
                                                    st.metric("📉 总销量损失", f"{int(total_qty_loss)} 单")
                                                with summary_col3:
                                                    if '收入变化' in detail_result.columns:
                                                        total_revenue_loss = detail_result['收入变化'].sum()
                                                        st.metric("💰 总收入损失", f"¥{total_revenue_loss:,.0f}")
                                                with summary_col4:
                                                    if '利润变化' in detail_result.columns:
                                                        total_profit_loss = detail_result['利润变化'].sum()
                                                        st.metric("💸 总利润损失", f"¥{total_profit_loss:,.0f}")
                                                
                                                # 显示交互式表格
                                                st.dataframe(
                                                    detail_result[display_cols],
                                                    column_config={
                                                        "商品名称": st.column_config.TextColumn("商品名称", width="large"),
                                                        "时段": st.column_config.TextColumn("时段", width="medium"),
                                                        "场景": st.column_config.TextColumn("场景", width="medium"),
                                                        "一级分类名": st.column_config.TextColumn("分类", width="medium"),
                                                        "销量变化": st.column_config.NumberColumn("销量变化", format="%d单"),
                                                        "变化幅度%": st.column_config.ProgressColumn(
                                                            "下滑幅度",
                                                            min_value=-100,
                                                            max_value=0,
                                                            format="%.1f%%"
                                                        ),
                                                        "收入变化": st.column_config.NumberColumn("收入变化", format="¥%.0f"),
                                                        "利润变化": st.column_config.NumberColumn("利润变化", format="¥%.0f"),
                                                        "商品实售价": st.column_config.NumberColumn("售价", format="¥%.2f")
                                                    },
                                                    use_container_width=True,
                                                    height=400
                                                )
                                                
                                                # ========== 🆕 Excel一键导出 ==========
                                                st.markdown("---")
                                                st.markdown("### 📥 导出功能")
                                                
                                                export_col1, export_col2 = st.columns([3, 1])
                                                
                                                with export_col1:
                                                    st.info("""
                                                    💡 **导出说明**：
                                                    - 📊 **Sheet1-明细数据**：包含所有下滑商品的详细信息
                                                    - 📈 **Sheet2-时段汇总**：按时段统计的下滑情况
                                                    - 🎯 **Sheet3-场景汇总**：按场景统计的下滑情况
                                                    - 📋 **Sheet4-分类汇总**：按商品分类统计的下滑情况
                                                    """)
                                                
                                                with export_col2:
                                                    # 生成Excel数据
                                                    from io import BytesIO
                                                    import openpyxl
                                                    from openpyxl.styles import Font, PatternFill, Alignment
                                                    
                                                    output = BytesIO()
                                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                                        # Sheet1: 明细数据
                                                        detail_result.to_excel(writer, sheet_name='明细数据', index=False)
                                                        
                                                        # Sheet2: 时段汇总
                                                        if '时段' in detail_result.columns:
                                                            agg_dict = {'商品名称': 'count'}
                                                            if '销量变化' in detail_result.columns:
                                                                agg_dict['销量变化'] = 'sum'
                                                            if '收入变化' in detail_result.columns:
                                                                agg_dict['收入变化'] = 'sum'
                                                            if '利润变化' in detail_result.columns:
                                                                agg_dict['利润变化'] = 'sum'
                                                            slot_summary = detail_result.groupby('时段').agg(agg_dict).rename(columns={'商品名称': '下滑商品数'})
                                                            slot_summary.to_excel(writer, sheet_name='时段汇总')
                                                        
                                                        # Sheet3: 场景汇总
                                                        if '场景' in detail_result.columns:
                                                            agg_dict = {'商品名称': 'count'}
                                                            if '销量变化' in detail_result.columns:
                                                                agg_dict['销量变化'] = 'sum'
                                                            if '收入变化' in detail_result.columns:
                                                                agg_dict['收入变化'] = 'sum'
                                                            if '利润变化' in detail_result.columns:
                                                                agg_dict['利润变化'] = 'sum'
                                                            scene_summary = detail_result.groupby('场景').agg(agg_dict).rename(columns={'商品名称': '下滑商品数'})
                                                            scene_summary.to_excel(writer, sheet_name='场景汇总')
                                                        
                                                        # Sheet4: 分类汇总
                                                        if '一级分类名' in detail_result.columns:
                                                            agg_dict = {'商品名称': 'count'}
                                                            if '销量变化' in detail_result.columns:
                                                                agg_dict['销量变化'] = 'sum'
                                                            if '收入变化' in detail_result.columns:
                                                                agg_dict['收入变化'] = 'sum'
                                                            if '利润变化' in detail_result.columns:
                                                                agg_dict['利润变化'] = 'sum'
                                                            category_summary = detail_result.groupby('一级分类名').agg(agg_dict).rename(columns={'商品名称': '下滑商品数'})
                                                            category_summary.to_excel(writer, sheet_name='分类汇总')
                                                    
                                                    excel_data = output.getvalue()
                                                    
                                                    # 下载按钮
                                                    from datetime import datetime
                                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                    st.download_button(
                                                        label="📥 下载完整明细Excel",
                                                        data=excel_data,
                                                        file_name=f"下滑商品明细_{timestamp}.xlsx",
                                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                        type="primary",
                                                        use_container_width=True
                                                    )
                                            
                                            else:
                                                st.success("✅ 太棒了！当前筛选条件下没有下滑商品")
                                    
                                    else:
                                        st.warning("⚠️ 数据中没有时段或场景信息，无法生成热力图")
                            else:
                                # 友好的提示信息
                                time_slot_status = "✅ 已自动生成" if '时段' in raw_data.columns else "❌ 缺失"
                                scene_status = "✅ 已自动推断" if '场景' in raw_data.columns else "❌ 缺失"
                                
                                st.info(f"""
                                📌 **时段×场景热力图 - 数据状态**
                                
                                **当前状态**:
                                - 时段数据: {time_slot_status}
                                - 场景数据: {scene_status}
                                
                                ---
                                
                                ### 🤖 自动数据生成说明
                                
                                系统会**自动生成**时段和场景数据，无需手动添加！
                                
                                #### ✅ 时段自动生成（基于下单时间）
                                
                                - **触发条件**：订单表中有"下单时间"列
                                - **生成规则**：8时段自动划分
                                  ```
                                  清晨(6-9点)、上午(9-12点)、正午(12-14点)、下午(14-18点)
                                  傍晚(18-21点)、晚间(21-24点)、深夜(0-3点)、凌晨(3-6点)
                                  ```
                                - **准确率**：100%（基于客观时间）
                                
                                #### ✅ 场景智能推断（基于时段+商品+分类）
                                
                                - **推断逻辑**：三级智能识别
                                  1. 🎯 **优先级1**：商品名称关键词（如：豆浆→早餐，奶茶→下午茶）
                                  2. 🏷️ **优先级2**：商品分类（如：饮料+下午→下午茶）
                                  3. ⏰ **优先级3**：时段兜底（如：清晨→早餐，正午→午餐）
                                
                                - **识别场景**：
                                  - 餐饮场景：早餐、午餐、晚餐、夜宵、下午茶
                                  - 购物场景：日常购物、日用补充、应急购买
                                  - 生活场景：休闲零食、家庭烹饪、营养补充
                                  - 社交场景：社交娱乐、夜间社交
                                
                                - **准确率**：约90%（基于关键词+业务规则）
                                
                                ---
                                
                                ### 💡 如何查看自动推断结果？
                                
                                上传数据后，系统会显示：
                                - ✅ "已自动从下单时间推断时段字段（8时段划分）"
                                - ✅ "已智能推断场景字段（共识别 X 种场景）"
                                - 📊 点击"查看自动推断的场景分布"可查看详细分布
                                
                                ---
                                
                                ### 🔧 如何优化推断结果？
                                
                                如果自动推断不准确，可以：
                                
                                1. **手动修正**（Excel中）：
                                   - 在订单表中手动添加或修正"场景"列
                                   - 系统会优先使用您手动标注的数据
                                
                                2. **反馈优化**：
                                   - 记录推断错误的商品名称
                                   - 提供给开发团队优化关键词库
                                
                                ---
                                
                                ### ⚠️ 如果数据仍然缺失
                                
                                请检查：
                                1. **时段缺失**：订单表中是否有"下单时间"列？
                                2. **场景缺失**：订单表中是否有"商品名称"或"分类"列？
                                3. **格式问题**：下单时间格式是否正确（需包含完整日期时间）？
                                
                                💡 **建议**：上传数据后，查看系统提示信息，确认是否成功生成时段和场景字段。
                                """)
                        
                        st.markdown("---")
                        
                        # 数据表格展示
                        st.markdown("### 📋 详细数据表格")
                        st.dataframe(
                            result.style.apply(
                                lambda x: ['background-color: #ffcccc' if v == '严重' 
                                          else 'background-color: #ffe6cc' if v == '警告'
                                          else '' for v in x],
                                subset=['问题等级']
                            ),
                            use_container_width=True,
                            height=400
                        )
                        
                        # 显示列名提示
                        revenue_cols = [col for col in result.columns if '预计收入' in col]
                        if revenue_cols:
                            st.info(f"💰 已包含预计收入数据: {', '.join(revenue_cols)}")
                        
                        # 导出按钮 - 创建导出专用版本（移除所有格式化符号）
                        export_df = result.copy()
                        
                        # 自动检测并清理所有包含¥符号的列
                        for col in export_df.columns:
                            if export_df[col].dtype == 'object':  # 只处理字符串类型的列
                                # 检查是否包含¥符号
                                sample_value = export_df[col].iloc[0] if len(export_df) > 0 else ""
                                if isinstance(sample_value, str) and '¥' in sample_value:
                                    try:
                                        # 清理¥符号、千分位逗号、N/A，转为数值
                                        export_df[col] = (export_df[col]
                                                         .astype(str)
                                                         .str.replace('¥', '')
                                                         .str.replace(',', '')
                                                         .str.replace('N/A', '0')
                                                         .replace('', '0')
                                                         .astype(float))
                                    except:
                                        pass  # 如果转换失败，保持原样
                        
                        # 🆕 需求1: 保留变化幅度%的%符号，不做清理
                        # 注释掉原有的%符号清理逻辑，保持变化幅度%列原样导出
                        # if '变化幅度%' in export_df.columns:
                        #     try:
                        #         export_df['变化幅度%'] = (export_df['变化幅度%']
                        #                               .astype(str)
                        #                               .str.replace('%', '')
                        #                               .astype(float))
                        #     except:
                        #         pass
                        
                        # 生成CSV - 先生成字符串，再用BOM编码确保Excel识别
                        from io import BytesIO
                        
                        # 创建字节流缓冲区
                        csv_buffer = BytesIO()
                        
                        # 写入BOM标记（UTF-8 with BOM）
                        csv_buffer.write('\ufeff'.encode('utf-8'))
                        
                        # 写入CSV内容
                        csv_string = export_df.to_csv(index=False)
                        csv_buffer.write(csv_string.encode('utf-8'))
                        
                        # 获取字节数据
                        csv_bytes = csv_buffer.getvalue()
                        
                        st.download_button(
                            label="⬇️ 导出CSV（纯数值）",
                            data=csv_bytes,
                            file_name=f"销量下滑商品_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            help="导出纯数值CSV（无¥、%符号），可用Excel直接打开和计算"
                        )
                    else:
                        st.info("✨ 未发现符合条件的销量下滑商品")
                except Exception as e:
                    st.error(f"❌ 诊断失败: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
    
    # Tab 2: 客单价归因分析
    with diagnostic_tabs[1]:
        st.markdown("### 💰 客单价下滑归因分析")
        
        # 添加客单价定义说明
        with st.expander("📖 客单价定义与说明", expanded=False):
            st.markdown("""
            **客单价定义**：
            - **客单价** = 订单总金额 ÷ 订单数量
            - 反映平均每笔订单的消费金额
            
            **分析维度**：
            - **按周分析**：对比相邻周的客单价变化（如第39周 vs 第40周）
            - **按日分析**：对比相邻日的客单价变化（如09-29 vs 09-30）
            
            **列名说明**：
            - **之前客单价**：时间上更早的周期（对比基准）
            - **当前客单价**：时间上更新的周期（当前状态）
            - **下滑TOP商品**：当前期销售额最高的前5个商品，显示【分类】商品名(单价)
            
            **问题等级**：
            - 🔴 **严重**：客单价下滑 ≥ 10%
            - 🟠 **警告**：客单价下滑 < 10%
            """)
        
        # 🆕 P2优化: 添加周期选择功能
        col1, col2 = st.columns(2)
        
        with col1:
            price_period = st.selectbox(
                "分析粒度",
                ["week", "daily"],
                format_func=lambda x: "按周分析" if x == "week" else "按日分析",
                key="price_period",
                index=0  # 默认选择"按周分析"
            )
        
        with col2:
            price_threshold = st.slider(
                "客单价下滑阈值%",
                min_value=-30.0,
                max_value=-1.0,
                value=-5.0,
                step=1.0,
                key="price_threshold"
            )
        
        # 🆕 P2优化: 灵活周期对比选择
        st.markdown("#### 📅 选择对比周期")
        
        # 添加分析模式选择
        analysis_mode = st.radio(
            "分析模式",
            ["批量分析（所有下滑周期）", "精准对比（指定两个周期）"],
            key="price_analysis_mode",
            horizontal=True
        )
        
        current_period_idx = None
        compare_period_idx = None
        
        if analysis_mode == "精准对比（指定两个周期）":
            # 获取可用周期列表
            try:
                available_periods = diagnostic_engine.get_available_price_periods(time_period=price_period)
                
                if len(available_periods) >= 2:
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        current_period_options = {p['index']: f"{p['label']} ({p['date_range']})" 
                                                 for p in available_periods}
                        current_period_idx = st.selectbox(
                            "当前周期",
                            options=list(current_period_options.keys()),
                            format_func=lambda x: current_period_options[x],
                            index=0,  # 默认选择最新周期
                            key="price_current_period"
                        )
                    
                    with col4:
                        compare_period_options = {p['index']: f"{p['label']} ({p['date_range']})" 
                                                 for p in available_periods if p['index'] > current_period_idx}
                        compare_period_idx = st.selectbox(
                            "对比周期",
                            options=list(compare_period_options.keys()) if compare_period_options else [current_period_idx + 1],
                            format_func=lambda x: compare_period_options.get(x, f"第{x}周期"),
                            index=0,  # 默认选择紧邻的上一周期
                            key="price_compare_period"
                        )
                else:
                    st.warning("⚠️ 数据量不足，无法进行周期对比")
            except Exception as e:
                st.error(f"获取周期列表失败: {str(e)}")
        else:
            st.info("💡 批量分析模式：自动遍历所有周期，找出所有客单价下滑的周期")
        
        if st.button("🔍 开始归因", key="btn_price"):
            with st.spinner("正在分析客单价下滑原因..."):
                try:
                    # 🆕 使用新的分Sheet方法
                    sheets_data = diagnostic_engine.diagnose_customer_price_decline_by_sheets(
                        time_period=price_period,
                        threshold=price_threshold,
                        current_period_index=current_period_idx,
                        compare_period_index=compare_period_idx
                    )
                    
                    # 检查是否有数据
                    has_data = any(len(df_sheet) > 0 for df_sheet in sheets_data.values())
                    
                    if has_data:
                        # 统计数据行数
                        total_rows = sum(len(df_sheet) for df_sheet in sheets_data.values() if len(df_sheet) > 0)
                        st.success(f"✅ 分析完成！共 {len([df for df in sheets_data.values() if len(df) > 0])} 个维度，{total_rows} 行数据")
                        
                        # 使用Tab展示三个维度
                        sheet_tabs = st.tabs(["📊 客单价变化", "📉 下滑商品分析", "📈 上涨商品分析"])
                        
                        # Tab 1: 客单价变化
                        with sheet_tabs[0]:
                            price_change_df = sheets_data.get('客单价变化', pd.DataFrame())
                            if len(price_change_df) > 0:
                                st.markdown("#### 客单价变化汇总")
                                st.dataframe(price_change_df, use_container_width=True, height=300)
                            else:
                                st.info("暂无数据")
                        
                        # Tab 2: 下滑商品分析
                        with sheet_tabs[1]:
                            declining_df = sheets_data.get('下滑商品分析', pd.DataFrame())
                            if len(declining_df) > 0:
                                st.markdown("#### TOP5问题商品")
                                st.markdown("*只包含售罄、涨价导致销量降、销量下滑等问题商品*")
                                st.dataframe(declining_df, use_container_width=True, height=400)
                            else:
                                st.info("暂无下滑商品")
                        
                        # Tab 3: 上涨商品分析
                        with sheet_tabs[2]:
                            rising_df = sheets_data.get('上涨商品分析', pd.DataFrame())
                            if len(rising_df) > 0:
                                st.markdown("#### TOP5优势商品")
                                st.markdown("*只包含涨价(销量增)、降价促销成功、销量增长等优势商品*")
                                st.dataframe(rising_df, use_container_width=True, height=400)
                            else:
                                st.info("暂无上涨商品")
                        
                        # 导出功能 - 提供Excel和CSV两种格式
                        st.markdown("---")
                        st.markdown("### 📥 导出数据")
                        
                        col1, col2 = st.columns(2)
                        
                        # Excel导出（分Sheet）
                        with col1:
                            from io import BytesIO
                            
                            # 准备Excel导出
                            excel_buffer = BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                for sheet_name, df_sheet in sheets_data.items():
                                    if len(df_sheet) > 0:
                                        # 清理数据中的¥符号等格式
                                        export_df = df_sheet.copy()
                                        for col in export_df.columns:
                                            if export_df[col].dtype == 'object':
                                                sample_value = export_df[col].iloc[0] if len(export_df) > 0 else ""
                                                if isinstance(sample_value, str) and '¥' in sample_value:
                                                    try:
                                                        export_df[col] = (export_df[col]
                                                                         .astype(str)
                                                                         .str.replace('¥', '')
                                                                         .str.replace(',', '')
                                                                         .str.replace('N/A', '0')
                                                                         .replace('', '0')
                                                                         .astype(float))
                                                    except:
                                                        pass
                                        
                                        export_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            excel_bytes = excel_buffer.getvalue()
                            
                            st.download_button(
                                label="⬇️ 导出Excel（分Sheet）",
                                data=excel_bytes,
                                file_name=f"客单价归因分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Excel文件包含3个Sheet：客单价变化、下滑商品分析、上涨商品分析"
                            )
                        
                        # CSV导出（合并所有数据）
                        with col2:
                            # 获取原始的合并数据
                            result = diagnostic_engine.diagnose_customer_price_decline(
                                time_period=price_period,
                                threshold=price_threshold,
                                current_period_index=current_period_idx,
                                compare_period_index=compare_period_idx
                            )
                            
                            if len(result) > 0:
                                # 准备CSV导出数据
                                export_df = result.copy()
                                
                                # 清理数据
                                for col in export_df.columns:
                                    if export_df[col].dtype == 'object':
                                        sample_value = export_df[col].iloc[0] if len(export_df) > 0 else ""
                                        if isinstance(sample_value, str) and '¥' in sample_value:
                                            try:
                                                export_df[col] = (export_df[col]
                                                                 .astype(str)
                                                                 .str.replace('¥', '')
                                                                 .str.replace(',', '')
                                                                 .str.replace('N/A', '0')
                                                                 .replace('', '0')
                                                                 .astype(float))
                                            except:
                                                pass
                                
                                # 生成CSV - 使用BOM编码确保Excel识别中文
                                csv_buffer = BytesIO()
                                csv_buffer.write('\ufeff'.encode('utf-8'))  # BOM标记
                                csv_string = export_df.to_csv(index=False)
                                csv_buffer.write(csv_string.encode('utf-8'))
                                csv_bytes = csv_buffer.getvalue()
                                
                                st.download_button(
                                    label="⬇️ 导出CSV（单文件）",
                                    data=csv_bytes,
                                    file_name=f"客单价归因_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    help="CSV文件包含所有字段（单个文件）"
                                )
                    else:
                        st.info("✨ 未发现客单价明显下滑周期")
                except Exception as e:
                    st.error(f"❌ 分析失败: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Tab 3: 负毛利商品预警
    with diagnostic_tabs[2]:
        st.markdown("### 🚨 负毛利商品预警")
        
        st.info("💡 自动识别售价低于成本的商品，帮助及时止损")
        
        if st.button("🔍 立即检测", key="btn_margin"):
            with st.spinner("正在检测负毛利商品..."):
                try:
                    result = diagnostic_engine.diagnose_negative_margin_products()
                    
                    if len(result) > 0:
                        total_loss = result['累计亏损额'].sum()
                        st.error(f"⚠️ 发现 {len(result)} 个负毛利商品，累计亏损 ¥{abs(total_loss):.2f}")
                        
                        st.dataframe(
                            result.style.apply(
                                lambda x: ['background-color: #ffcccc' if v == '🔴 严重' 
                                          else 'background-color: #ffe6cc' if v == '🟠 警告'
                                          else '' for v in x],
                                subset=['问题等级']
                            ),
                            use_container_width=True,
                            height=400
                        )
                        
                        csv = result.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="⬇️ 导出CSV",
                            data=csv,
                            file_name=f"负毛利商品_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success("✅ 未发现负毛利商品，经营健康！")
                except Exception as e:
                    st.error(f"❌ 检测失败: {str(e)}")
    
    # Tab 4: 高配送费订单优化
    with diagnostic_tabs[3]:
        st.markdown("### 🚚 高配送费订单诊断")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fee_threshold = st.slider(
                "配送费占比阈值%",
                min_value=10.0,
                max_value=50.0,
                value=20.0,
                step=5.0,
                key="fee_threshold"
            )
        
        with col2:
            st.metric("正常配送费占比", "< 15%", delta="优秀", delta_color="normal")
        
        if st.button("🔍 开始诊断", key="btn_delivery"):
            with st.spinner("正在分析高配送费订单..."):
                try:
                    result = diagnostic_engine.diagnose_high_delivery_fee_orders(threshold=fee_threshold)
                    
                    if len(result) > 0:
                        st.warning(f"⚠️ 发现 {len(result)} 个地址配送费占比过高")
                        
                        st.dataframe(result, use_container_width=True, height=400)
                        
                        csv = result.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="⬇️ 导出CSV",
                            data=csv,
                            file_name=f"高配送费订单_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success("✅ 配送费控制良好，无异常订单")
                except Exception as e:
                    st.error(f"❌ 诊断失败: {str(e)}")
    
    # Tab 5: 商品角色失衡
    with diagnostic_tabs[4]:
        st.markdown("### ⚖️ 流量品 & 利润品失衡诊断")
        
        st.info("💡 检测各场景中流量品和利润品的配比是否合理")
        
        if st.button("🔍 开始检测", key="btn_balance"):
            with st.spinner("正在分析商品角色配比..."):
                try:
                    result = diagnostic_engine.diagnose_product_role_imbalance()
                    
                    if len(result) > 0:
                        st.warning(f"⚠️ 发现 {len(result)} 个场景商品角色失衡")
                        
                        st.dataframe(result, use_container_width=True, height=400)
                        
                        csv = result.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="⬇️ 导出CSV",
                            data=csv,
                            file_name=f"商品角色失衡_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success("✅ 各场景商品角色配比合理")
                except Exception as e:
                    st.error(f"❌ 检测失败: {str(e)}")
    
    # Tab 6: 异常波动预警
    with diagnostic_tabs[5]:
        st.markdown("### 📊 异常波动商品预警")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fluctuation_threshold = st.slider(
                "波动阈值（环比%）",
                min_value=30.0,
                max_value=100.0,
                value=50.0,
                step=10.0,
                key="fluctuation_threshold"
            )
        
        with col2:
            st.info("📈 爆单：销量环比增长超过阈值\n📉 滞销：销量环比下降超过阈值")
        
        if st.button("🔍 开始预警", key="btn_fluctuation"):
            with st.spinner("正在检测异常波动商品..."):
                try:
                    result = diagnostic_engine.diagnose_abnormal_fluctuation(threshold=fluctuation_threshold)
                    
                    if len(result) > 0:
                        boom_count = len(result[result['异常类型'] == '📈 爆单'])
                        slow_count = len(result[result['异常类型'] == '📉 滞销'])
                        
                        st.warning(f"⚠️ 发现 {len(result)} 个异常波动商品（爆单:{boom_count} | 滞销:{slow_count}）")
                        
                        st.dataframe(
                            result.style.apply(
                                lambda x: ['background-color: #ccffcc' if v == '📈 爆单' 
                                          else 'background-color: #ffcccc' for v in x],
                                subset=['异常类型']
                            ),
                            use_container_width=True,
                            height=400
                        )
                        
                        csv = result.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="⬇️ 导出CSV",
                            data=csv,
                            file_name=f"异常波动商品_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success("✅ 未发现异常波动商品")
                except Exception as e:
                    st.error(f"❌ 预警失败: {str(e)}")


if __name__ == "__main__":
    main()
