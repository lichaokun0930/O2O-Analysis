#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能门店经营看板 - 可视化界面
集成Streamlit构建交互式看板，展示五大AI模型的分析结果
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

from 智能门店经营看板系统 import SmartStoreDashboard
from 真实数据处理器 import RealDataProcessor
from 核心业务逻辑 import CoreBusinessLogic

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
    "һ��������": "一级分类",
    "�������": "城市名称",
    "����������": "三级分类",
    "��Ʒ����": "商品名称",
    "��Ʒ��": "商品编码",
    "��Ʒʵ�ۼ�": "商品实售价",
    "��Ʒԭ��": "商品原价",
    "����": "数量",
    "ʣ����": "剩余库存",
    "��Ʒ������": "商品优惠金额",
    "�������": "配送方式",
    "����ID": "订单ID",
    "�û�ID": "用户ID",
    "�û���": "用户名称",
    "�̻���": "门店名称",
    "�ŵ�����": "门店名称",
    "�µ�ʱ��": "下单时间",
    "�ջ���ַ": "收货地址",
    "ƽ̨Ӷ��": "平台佣金",
    "ʵ�ռ۸�": "实收价格",
    "Ԥ�ƶ�������": "预估订单收入",
    "�û�֧�����": "用户支付配送费",
    "�û�֧�����ͷ�": "配送费减免金额",
    "���ͷѼ�����": "物流配送费",
    "��Ʒ����": "商品名称",
    "�̼ҳе�����ȯ": "商家优惠券",
    "�̼Ҵ���ȯ": "商家优惠券",
    "�������": "商品减免金额",
    "��������": "渠道",
}

SHEET_KEYWORDS: Dict[str, List[str]] = {
    "order": ["门店订单", "订单", "order"],
    "competitor": ["竞对", "竞品", "对手"],
    "cost": ["成本", "cost"],
    "traffic": ["流量", "traffic"],
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

@st.cache_data
def load_price_panel_metrics() -> Optional[Dict[str, Any]]:
    """读取比价面板指标"""
    metrics_path = PRICE_PANEL_INTERMEDIATE_DIR / "price_panel_metrics.json"
    if not metrics_path.exists():
        return None
    try:
        with open(metrics_path, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
        return payload
    except Exception:
        return None


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
    """渲染比价基础看板指标"""
    st.subheader("💹 比价基础看板")
    timestamp = payload.get("generated_at")
    if timestamp:
        st.caption(f"数据更新: {timestamp.replace('T', ' ')[:19]}")

    for warn in payload.get("warnings", []) or []:
        st.warning(warn)

    metrics = payload.get("metrics") or []
    if not metrics:
        st.info("暂无比价指标，请先运行比价ETL。")
        return

    for start in range(0, len(metrics), 3):
        row_metrics = metrics[start:start + 3]
        columns = st.columns(len(row_metrics))
        for col, metric in zip(columns, row_metrics):
            with col:
                st.metric(metric.get("label", ""), _format_metric_value(metric))
                context_lines = _build_metric_context_lines(metric, payload)
                if context_lines:
                    st.caption(" | ".join(context_lines))


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

    price_panel_payload = load_price_panel_metrics()
    if price_panel_payload and price_panel_payload.get("metrics"):
        render_price_panel_overview(price_panel_payload)

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
        st.info("👆 请先在左侧点击“开始智能分析”")
        st.subheader("📋 数据预览")
        if not current_data:
            st.info("尚未加载真实数据。请在侧边栏放置 Excel 文件或开启示例数据演示模式。")
        else:
            if using_sample:
                st.caption("以下为内置示例数据，仅供界面演示；上传真实数据后将自动替换。")

            product_preview = current_data.get("product_data", pd.DataFrame())
            competitor_preview = current_data.get("competitor_data", pd.DataFrame())

            if "order_data" in current_data and not using_sample:
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
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**门店商品数据**")
                    st.dataframe(product_preview.head(), height=240)
                with col2:
                    st.write("**竞对商品数据**")
                    st.dataframe(competitor_preview.head(), height=240)

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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🛍️ 商品策略", "📈 趋势预测", "⚠️ 风险评估", "🏢 竞对分析", "🔬 假设验证", "🧠 学习效果"])
    
    with tab1:
        display_product_strategy(analysis_result)
    
    with tab2:
        display_trend_analysis(analysis_result)
    
    with tab3:
        display_risk_assessment(analysis_result)
    
    with tab4:
        display_competitor_analysis(analysis_result)
    
    with tab5:
        display_hypothesis_validation(analysis_result)
    
    with tab6:
        display_learning_effects(analysis_result, dashboard_instance)

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

if __name__ == "__main__":
    main()