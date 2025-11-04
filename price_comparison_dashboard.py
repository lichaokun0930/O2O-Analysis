import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime

from pathlib import Path

# 获取当前文件所在目录，并构建正确的报告目录路径
APP_DIR = Path(__file__).resolve().parent
REPORTS_DIR = APP_DIR.parent / "比价数据" / "reports"
FILE_KEYWORD = 'matched_products_comparison_final'

# 定义所需的工作表名称
SHEET_NAMES = {
    'barcode_match': '1-条码精确匹配',
    'fuzzy_match': '2-名称模糊匹配(无条码)',
    'unmatched_barcode': '3-有条码但未匹配商品',
    'store_a_unique': '4-店A-不明商品', # 根据实际错误报告修正
    'store_b_unique': '5-店B-不明商品', # 根据实际错误报告修正
    'comparison': '8-MK清洗数据对比', # 根据实际错误报告修正
}

@st.cache_data(ttl=3600)
def load_latest_comparison_data():
    """
    从 "比价数据/reports" 目录加载最新的比价报告文件,并读取所有需要的sheet。
    """
    try:
        # 找到所有匹配的报告文件
        report_files = glob.glob(os.path.join(REPORTS_DIR, f'{FILE_KEYWORD}_*.xlsx'))
        if not report_files:
            st.warning(f"在目录 '{REPORTS_DIR}' 中未找到比价报告文件。")
            return None, None

        # 解析文件名中的日期时间并找到最新的文件
        latest_file = max(report_files, key=lambda x: datetime.strptime(os.path.basename(x), f'{FILE_KEYWORD}_%Y%m%d_%H%M%S.xlsx'))

        # 加载所有需要的sheet
        xls = pd.ExcelFile(latest_file)
        dataframes = {}
        for key, sheet_name in SHEET_NAMES.items():
            if sheet_name in xls.sheet_names:
                dataframes[key] = pd.read_excel(xls, sheet_name=sheet_name)
            else:
                st.error(f"在文件 '{os.path.basename(latest_file)}' 中未找到工作表: '{sheet_name}'")
                dataframes[key] = pd.DataFrame() # 返回一个空的DataFrame

        return dataframes, os.path.basename(latest_file)

    except Exception as e:
        st.error(f"加载比价数据时出错: {e}")
        return None, None

def create_price_comparison_dashboard():
    """
    创建并显示比价看板的六个指标卡。
    """
    st.header("比价核心指标看板")

    data, filename = load_latest_comparison_data()

    if not data:
        st.warning("无法加载比价数据，看板无法显示。")
        return

    st.info(f"数据来源: `{filename}`")

    # 定义列布局
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    # --- 卡片1: 比对商品总数 ---
    with col1:
        barcode_match_df = data.get('barcode_match', pd.DataFrame())
        fuzzy_match_df = data.get('fuzzy_match', pd.DataFrame())

        barcode_match_count = len(barcode_match_df)
        
        # 对模糊匹配结果按'店A_商品名称'进行去重计算
        unique_fuzzy_match_count = 0
        if not fuzzy_match_df.empty and '店A_商品名称' in fuzzy_match_df.columns:
            unique_fuzzy_match_count = fuzzy_match_df['店A_商品名称'].nunique()

        total_matched_count = barcode_match_count + unique_fuzzy_match_count
        
        st.metric(
            label="1. 比对商品总数",
            value=f"{total_matched_count}",
            help=f"条码精确匹配: {barcode_match_count} | 名称模糊匹配(去重后): {unique_fuzzy_match_count}"
        )

    # --- 卡片2: 模糊匹配商品 ---
    with col2:
        fuzzy_match_count = len(data.get('fuzzy_match', pd.DataFrame()))
        total_compared_count = len(data.get('comparison', pd.DataFrame()))
        st.metric(
            label="2. 模糊匹配商品数 / 已比对总数",
            value=f"{fuzzy_match_count} / {total_compared_count}",
            help="名称模糊匹配上的商品数量，以及所有参与比对的商品总数。"
        )

    # --- 卡片3: 价格优势商品 (A店) ---
    with col3:
        comparison_df = data.get('comparison', pd.DataFrame())
        price_advantage_count = 0
        if not comparison_df.empty and '店A_价格' in comparison_df.columns and '店B_价格' in comparison_df.columns:
            # 确保价格列是数字类型，并填充NaN以便比较
            price_a = pd.to_numeric(comparison_df['店A_价格'], errors='coerce')
            price_b = pd.to_numeric(comparison_df['店B_价格'], errors='coerce')
            # 过滤掉价格无效的行
            valid_prices_df = comparison_df.dropna(subset=['店A_价格', '店B_价格'])
            price_advantage_count = len(valid_prices_df[valid_prices_df['店A_价格'] < valid_prices_df['店B_价格']])
        
        st.metric(
            label="3. A店价格优势商品数",
            value=f"{price_advantage_count}",
            help="在已比对的商品中，A店价格更低的商品数量。"
        )

    # --- 卡片4: 价格劣势商品 (A店) ---
    with col4:
        price_disadvantage_count = 0
        if not comparison_df.empty and '店A_价格' in comparison_df.columns and '店B_价格' in comparison_df.columns:
            # 重用之前的有效价格数据
            price_a = pd.to_numeric(comparison_df['店A_价格'], errors='coerce')
            price_b = pd.to_numeric(comparison_df['店B_价格'], errors='coerce')
            valid_prices_df = comparison_df.dropna(subset=['店A_价格', '店B_价格'])
            price_disadvantage_count = len(valid_prices_df[valid_prices_df['店A_价格'] > valid_prices_df['店B_价格']])

        st.metric(
            label="4. A店价格劣势商品数",
            value=f"{price_disadvantage_count}",
            help="在已比对的商品中，A店价格更高的商品数量。"
        )

    # --- 卡片5: 无条码但匹配商品 ---
    with col5:
        # 这个指标直接来自于 '2-名称模糊匹配(无条码)' sheet 的行数
        no_barcode_matched_count = len(data.get('fuzzy_match', pd.DataFrame()))
        st.metric(
            label="5. 无条码但匹配商品数",
            value=f"{no_barcode_matched_count}",
            help="没有条码，但通过名称模糊匹配成功的商品数量。"
        )

    # --- 卡片6: 需人工确认商品 ---
    with col6:
        # 根据之前的讨论，这个指标是“有条码但未匹配”+“模糊匹配中分数较低”
        # 我们将“有条码但未匹配”的数量作为基础
        unmatched_barcode_count = len(data.get('unmatched_barcode', pd.DataFrame()))
        
        # 假设模糊匹配分数低于0.8的需要人工确认
        fuzzy_df = data.get('fuzzy_match', pd.DataFrame())
        low_score_count = 0
        if not fuzzy_df.empty and 'score' in fuzzy_df.columns:
            low_score_count = len(fuzzy_df[fuzzy_df['score'] < 0.8])

        manual_check_count = unmatched_barcode_count + low_score_count
        st.metric(
            label="6. 需人工确认商品数",
            value=f"{manual_check_count}",
            delta=f"有条码未匹配: {unmatched_barcode_count}, 低分模糊匹配: {low_score_count}",
            delta_color="off",
            help="需要人工干预的商品总数。包括有条码但系统无法匹配的，以及模糊匹配得分较低(低于0.8)的商品。"
        )

    # --- 卡片7: 店B-独有商品 ---
    with col6:
        store_b_unique_count = len(data.get('store_b_unique', pd.DataFrame()))
        st.metric(
            label="6. 店B-独有商品",
            value=f"{store_b_unique_count}",
            help="店B独有的商品数量。"
        )

    # --- 卡片8: 合并清洗数据对比 ---
    with col6:
        comparison_count = len(data.get('comparison', pd.DataFrame()))
        st.metric(
            label="7. 合并清洗数据对比",
            value=f"{comparison_count}",
            help="合并清洗后的数据对比数量。"
        )

    # 在这里我们将逐一实现六个看板的逻辑
    # ...
