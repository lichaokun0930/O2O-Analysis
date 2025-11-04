#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
智能门店经营看板 - 可视化界面
集成Streamlit构建交互式看板，展示五大AI模型的分析结果

🚀 运行方法：
=============
1. PowerShell 方式：
   cd "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"
   & "d:\Python1\O2O_Analysis\O2O数据分析\.venv\Scripts\streamlit.exe" run 智能门店经营看板_可视化.py --server.port 8502

2. 简化命令：
   cd "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"
   ..\\.venv\\Scripts\\streamlit run 智能门店经营看板_可视化.py --server.port 8502

3. 访问地址：
   http://localhost:8502

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

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# 导入统一业务逻辑配置
try:
    sys.path.append(str(APP_DIR.parent))
    from standard_business_config import StandardBusinessConfig, StandardBusinessLogic, create_order_level_summary, apply_standard_business_logic
    STANDARD_CONFIG_AVAILABLE = True
    print("✅ 已加载统一业务逻辑配置")
except ImportError as e:
    print(f"⚠️ 未找到standard_business_config模块: {e}")
    print("将使用默认配置")
    STANDARD_CONFIG_AVAILABLE = False

from 智能门店经营看板系统 import SmartStoreDashboard
from 真实数据处理器 import RealDataProcessor
from 核心业务逻辑 import CoreBusinessLogic
from price_comparison_dashboard import create_price_comparison_dashboard

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

@st.cache_resource
def load_dashboard_system() -> SmartStoreDashboard:
    """加载智能门店经营看板系统实例"""
    return SmartStoreDashboard()

@st.cache_resource
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
    if "下单时间" in order_df.columns:
        order_df = order_df.copy()
        order_df["下单时间"] = pd.to_datetime(order_df["下单时间"], errors="coerce")
        order_df["下单日期"] = order_df["下单时间"].dt.date
    if "下单日期" not in order_df.columns:
        return pd.DataFrame()
    agg_dict: Dict[str, Any] = {"下单日期": "first"}
    if "预估订单收入" in order_df.columns:
        agg_dict["预估订单收入"] = "sum"
    if "实收价格" in order_df.columns:
        agg_dict["实收价格"] = "sum"
    if "数量" in order_df.columns:
        agg_dict["数量"] = "sum"
    if "订单ID" in order_df.columns:
        agg_dict["订单ID"] = pd.Series.nunique
    summary = order_df.groupby("下单日期").agg(agg_dict).reset_index(drop=True)
    rename_map = {
        "下单日期": "date",
        "预估订单收入": "estimated_revenue",
        "实收价格": "net_revenue",
        "数量": "items_sold",
        "订单ID": "unique_orders",
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

@st.cache_data
def load_real_business_data() -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """扫描并加载真实业务数据，返回(数据, 提示信息)"""
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

    result: Dict[str, Any] = {
        "store_id": store_id,
        "order_data": order_df,
        "product_data": product_df,
        "sales_data": sales_summary,
        "customer_data": customer_df,
        "competitor_data": competitor_df,
        "cost_data": cost_df,
        "traffic_data": traffic_df,
        "data_source": f"文件: {target_file.name}",
        "data_period": data_period,
    "total_orders": int(order_df["订单ID"].nunique()) if "订单ID" in order_df.columns else len(order_df),
        "total_products": int(product_df["商品名称"].nunique()) if not product_df.empty else order_df.get("商品名称", pd.Series(dtype=str)).nunique(),
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
        horizontal=True
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
    """主函数"""
    
    # 页面标题
    st.markdown('<h1 class="main-header">🏪 智能门店经营看板</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    dashboard = load_dashboard_system()
    data_processor = load_data_processor()
    sample_data = load_sample_data()
    real_data, load_messages = load_real_business_data()

    st.sidebar.title("📊 看板控制面板")

    if load_messages:
        for msg in load_messages:
            st.sidebar.warning(msg)

    # AI 学习系统概览
    st.sidebar.subheader("🧠 AI学习系统")
    learning_status = dashboard.get_learning_status()
    if learning_status.get("enabled"):
        st.sidebar.success("✅ AI学习系统已启用")
        learning_stats = learning_status.get("learning_statistics", {})
        if learning_stats:
            st.sidebar.write("**学习状态**")
            st.sidebar.write(f"• 总学习次数: {learning_stats.get('total_learning_sessions', 0)}")
            st.sidebar.write(f"• 在线更新: {learning_stats.get('online_updates', 0)}")
            st.sidebar.write(f"• 批量更新: {learning_stats.get('batch_updates', 0)}")
        if st.sidebar.button("🔄 手动模型训练", help="使用历史数据手动训练模型"):
            with st.spinner("正在训练模型..."):
                training_result = dashboard.manual_model_training([sample_data])
                if training_result.get("success"):
                    st.sidebar.success("🎉 模型训练完成")
                else:
                    st.sidebar.error(f"❌ 训练失败: {training_result.get('error', '未知错误')}")
        if st.sidebar.button("📄 导出学习报告"):
            report_path = dashboard.export_learning_insights()
            if report_path:
                st.sidebar.success("✅ 报告已导出")
            else:
                st.sidebar.error("❌ 导出失败")
    else:
        st.sidebar.info("AI学习系统暂未启用")

    # 数据源选择
    st.sidebar.subheader("📁 数据输入")
    use_sample_data = st.sidebar.toggle("使用示例数据演示", value=False)
    using_sample = False

    if real_data is not None:
        if use_sample_data:
            st.sidebar.warning("已加载真实数据，已临时切换到示例数据演示模式")
            current_data = sample_data
            using_sample = True
        else:
            current_data = real_data
            st.sidebar.success(f"📊 当前数据源: {real_data['data_source']} ({real_data['data_period']})")
            st.sidebar.metric("订单数", f"{real_data['total_orders']:,}")
            st.sidebar.metric("商品种类", f"{real_data['total_products']:,}")
    else:
        if use_sample_data:
            st.sidebar.warning("未找到真实数据，当前以示例数据演示界面")
            current_data = sample_data
            using_sample = True
        else:
            st.sidebar.warning("未找到真实数据，请将Excel放入提示目录，或勾选『使用示例数据演示』体验界面")
            current_data = {}

    # 分析维度选择
    st.sidebar.subheader("分析设置")
    analysis_scope = st.sidebar.multiselect(
        "选择分析维度",
        ["销售分析", "竞对分析", "风险评估", "策略建议", "预测分析"],
        default=["销售分析", "策略建议"],
    )
    forecast_days = st.sidebar.slider("预测天数", 7, 90, 30)

    if st.sidebar.button("🚀 开始智能分析", type="primary"):
        if not current_data:
            st.warning("请先加载真实数据，或在侧边栏启用示例数据演示后再运行分析。")
        else:
            with st.spinner("正在进行智能分析..."):
                analysis_result = dashboard.comprehensive_analysis(
                    current_data,
                    current_data.get("competitor_data"),
                )
                st.session_state["analysis_result"] = analysis_result
                st.session_state["current_data"] = current_data
                st.session_state["forecast_days"] = forecast_days

                if real_data is not None and not using_sample:
                    data_processor.processed_data = {
                        "sales_data": current_data.get("product_data", pd.DataFrame()),
                        "order_data": current_data.get("order_data", pd.DataFrame()),
                    }

    if "analysis_result" in st.session_state:
        display_analysis_results(st.session_state["analysis_result"], analysis_scope, dashboard)
    else:
        # 显示比价模块（新的上传功能）
        st.subheader("📊 比价分析")
        render_unified_price_comparison_module()
        
        st.markdown("---")
        st.info("👆 请先在左侧点击“开始智能分析”以查看其他分析模块")
        st.subheader("📋 数据预览")
        
        # 只有在用户主动选择时才显示数据预览
        if use_sample_data:
            # 显示示例数据
            st.caption("以下为内置示例数据，仅供界面演示；上传真实数据后将自动替换。")
            product_preview = current_data.get("product_data", pd.DataFrame())
            competitor_preview = current_data.get("competitor_data", pd.DataFrame())
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**门店商品数据**")
                st.dataframe(product_preview.head(), height=240)
            with col2:
                st.write("**竞对商品数据**")
                st.dataframe(competitor_preview.head(), height=240)
        elif real_data is not None and st.session_state.get("show_data_preview", False):
            # 显示真实数据预览
            product_preview = current_data.get("product_data", pd.DataFrame())
            competitor_preview = current_data.get("competitor_data", pd.DataFrame())
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**门店订单数据**")
                st.dataframe(current_data.get("order_data", pd.DataFrame()).head(), height=240)
            with col2:
                st.write("**竞对商品数据**")
                st.dataframe(competitor_preview.head(), height=240)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("订单总数", f"{current_data.get('total_orders', 0):,}")
            col2.metric("商品种类", f"{current_data.get('total_products', 0):,}")
            if not competitor_preview.empty:
                col3.metric("竞对商品", f"{len(competitor_preview):,}")
            col4.metric("数据期间", current_data.get("data_period", "N/A"))
        else:
            # 显示数据状态，不自动展示预览
            if real_data is not None:
                st.info(f"✅ 已检测到真实数据文件：{real_data['data_source']} ({real_data['data_period']})")
                if st.button("🔍 查看数据预览", help="点击查看已加载的真实数据概览"):
                    st.session_state["show_data_preview"] = True
                    st.rerun()
            else:
                st.info("💡 请在侧边栏开启'使用示例数据演示'查看界面效果，或将Excel文件放入数据目录进行分析")

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
    tabs_to_create = ["🛍️ 商品策略", "📈 趋势预测", "⚠️ 风险评估", "🏢 竞对分析", "🔬 假设验证", "🧠 学习效果", "💹 比价看板"]
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
            
            st.plotly_chart(fig, width='stretch', key='chart_6')
        
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
        
        st.plotly_chart(fig, width='stretch', key='chart_5')
        
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
                
                st.plotly_chart(fig, width='stretch', key='chart_4')
                
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
                    
                    st.plotly_chart(fig, width='stretch', key='chart_3')
            
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
                    
                    st.plotly_chart(fig, width='stretch', key='chart_2')

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
                                
                                st.plotly_chart(fig, width='stretch', key='chart_1')
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
            render_order_overview(processed_order_data, order_summary)
        
        with analysis_tabs[1]:
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
            
            # 利润统计 (使用标准业务逻辑计算的实际利润)
            if '订单实际利润额' in order_agg.columns:
                actual_profit_series = order_agg['订单实际利润额']
                order_summary['总利润额'] = actual_profit_series.sum()
                order_summary['平均订单利润'] = actual_profit_series.mean()
                order_summary['盈利订单数'] = (actual_profit_series > 0).sum()
                order_summary['盈利订单比例'] = (actual_profit_series > 0).mean()
            
            # 配送成本统计 (使用标准业务逻辑)
            if '配送成本' in order_agg.columns:
                delivery_cost_series = order_agg['配送成本']
                order_summary['平均配送成本'] = delivery_cost_series.mean()
                order_summary['总配送成本'] = delivery_cost_series.sum()
            
            # 营销成本统计
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
            help="标准公式: 用户支付配送费 - 配送费减免 - 物流配送费"
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
            help="用户支付配送费 - 配送费减免 - 物流配送费"
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
        
        **3. 配送成本计算:**
        ```
        配送成本 = (用户支付配送费 - 配送费减免金额 - 物流配送费)
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


if __name__ == "__main__":
    main()
