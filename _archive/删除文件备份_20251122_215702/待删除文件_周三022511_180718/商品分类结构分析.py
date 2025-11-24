"""
商品分类结构竞争力分析模块
Phase 3: 深度整合方案

核心功能：
1. 品类结构总览（战略视角）
2. 各品类深度分析（运营视角）
3. 品类贡献度矩阵（决策支持）
4. 跨品类组合分析（与订单组合联动）
5. 结构优化建议（智能推荐）

作者：AI Assistant
日期：2025-10-16
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple

# ============================================================================
# 数据分析函数
# ============================================================================

def analyze_category_structure(df: pd.DataFrame) -> Dict:
    """
    商品分类结构综合分析
    
    Returns:
        包含所有分析结果的字典
    """
    results = {}
    
    # 计算毛利率（支持多种字段名）
    cost_col = None
    if '成本' in df.columns:
        cost_col = '成本'
    elif '商品成本' in df.columns:
        cost_col = '商品成本'
    
    if cost_col:
        df['毛利'] = df['商品实售价'] - df[cost_col]
        df['毛利率'] = (df['毛利'] / df['商品实售价'] * 100).fillna(0)
    else:
        df['毛利'] = 0
        df['毛利率'] = 0
    
    # 1. 一级分类分析（支持多种字段名）
    category_col = None
    if '一级分类名' in df.columns:
        category_col = '一级分类名'
    elif '一级分类' in df.columns:
        category_col = '一级分类'
    
    if category_col:
        level1_stats = df.groupby(category_col).agg({
            '商品名称': 'nunique',      # SKU数
            '订单ID': 'nunique',         # 订单数
            '商品实售价': ['sum', 'mean'],  # 销售额、均价
            '毛利': 'sum',               # 总毛利
            '毛利率': 'mean'             # 平均毛利率
        }).round(2)
        
        level1_stats.columns = ['SKU数', '订单数', '销售额', '平均售价', '总毛利', '平均毛利率']
        level1_stats = level1_stats.reset_index()
        level1_stats.rename(columns={category_col: '一级分类'}, inplace=True)
        level1_stats['销售占比%'] = (level1_stats['销售额'] / level1_stats['销售额'].sum() * 100).round(2)
        level1_stats = level1_stats.sort_values('销售额', ascending=False)
        
        results['level1'] = level1_stats
        
        # 计算品类集中度（HHI指数）
        sales_share = level1_stats['销售额'] / level1_stats['销售额'].sum()
        hhi = (sales_share ** 2).sum()
        results['hhi'] = hhi
    
    # 2. 三级分类分析（支持多种字段名）
    subcategory_col = None
    if '三级分类名' in df.columns:
        subcategory_col = '三级分类名'
    elif '三级分类' in df.columns:
        subcategory_col = '三级分类'
    
    if category_col and subcategory_col:
        level3_stats = df.groupby([category_col, subcategory_col]).agg({
            '商品名称': 'nunique',
            '订单ID': 'nunique',
            '商品实售价': ['sum', 'mean'],
            '毛利': 'sum',
            '毛利率': 'mean'
        }).round(2)
        
        level3_stats.columns = ['SKU数', '订单数', '销售额', '平均售价', '总毛利', '平均毛利率']
        level3_stats = level3_stats.reset_index()
        level3_stats.rename(columns={category_col: '一级分类', subcategory_col: '三级分类'}, inplace=True)
        
        results['level3'] = level3_stats
    
    # 3. 品类贡献度矩阵（用于战略决策）
    if 'level1' in results and '毛利率' in df.columns:
        contribution_matrix = level1_stats[['一级分类', '销售额', '平均毛利率', '订单数']].copy()
        
        # 定义象限
        sales_median = contribution_matrix['销售额'].median()
        profit_median = contribution_matrix['平均毛利率'].median()
        
        def categorize(row):
            if row['销售额'] >= sales_median and row['平均毛利率'] >= profit_median:
                return '🌟 明星品类'
            elif row['销售额'] < sales_median and row['平均毛利率'] >= profit_median:
                return '💎 高价值品类'
            elif row['销售额'] >= sales_median and row['平均毛利率'] < profit_median:
                return '🔥 引流品类'
            else:
                return '⚠️ 优化品类'
        
        contribution_matrix['品类定位'] = contribution_matrix.apply(categorize, axis=1)
        results['contribution_matrix'] = contribution_matrix
    
    # 4. 跨品类购买分析
    if category_col and '订单ID' in df.columns:
        from itertools import combinations
        from collections import Counter
        
        # 按订单分组，获取每个订单的品类列表
        order_categories = df.groupby('订单ID')[category_col].apply(list)
        
        # 统计品类组合
        category_pairs = Counter()
        for categories in order_categories:
            if len(categories) >= 2:
                unique_cats = list(set(categories))
                for pair in combinations(sorted(unique_cats), 2):
                    category_pairs[pair] += 1
        
        # 转换为DataFrame
        if category_pairs:
            cross_category = pd.DataFrame([
                {
                    '品类A': pair[0],
                    '品类B': pair[1],
                    '共同购买次数': count
                }
                for pair, count in category_pairs.most_common(20)
            ])
            
            results['cross_category'] = cross_category
    
    return results


def get_category_insights(results: Dict) -> List[str]:
    """
    基于分析结果生成智能洞察和建议
    """
    insights = []
    
    if 'level1' in results:
        level1 = results['level1']
        
        # 品类数量分析
        cat_count = len(level1)
        insights.append(f"📊 当前经营 **{cat_count}** 个一级品类")
        
        # 集中度分析
        if 'hhi' in results:
            hhi = results['hhi']
            if hhi > 0.25:
                insights.append(f"⚠️ 品类集中度较高（HHI={hhi:.3f}），建议丰富品类结构")
            elif hhi < 0.15:
                insights.append(f"✅ 品类分布均衡（HHI={hhi:.3f}），结构健康")
            else:
                insights.append(f"📈 品类集中度适中（HHI={hhi:.3f}）")
        
        # TOP品类识别
        if len(level1) > 0:
            top_cat = level1.iloc[0]
            insights.append(f"🏆 TOP品类：**{top_cat['一级分类']}**（销售额¥{top_cat['销售额']:.2f}，占比{top_cat['销售占比%']:.1f}%）")
        
        # SKU深度分析
        avg_sku = level1['SKU数'].mean()
        insights.append(f"📦 平均品类SKU数：{avg_sku:.0f}个")
        
        # 毛利率分析
        if '平均毛利率' in level1.columns:
            avg_margin = level1['平均毛利率'].mean()
            high_margin_cats = level1[level1['平均毛利率'] > avg_margin * 1.2]
            if len(high_margin_cats) > 0:
                insights.append(f"💰 高毛利品类：{', '.join(high_margin_cats['一级分类'].tolist())}")
    
    # 品类定位建议
    if 'contribution_matrix' in results:
        matrix = results['contribution_matrix']
        star_cats = matrix[matrix['品类定位'] == '🌟 明星品类']
        optimize_cats = matrix[matrix['品类定位'] == '⚠️ 优化品类']
        
        if len(star_cats) > 0:
            insights.append(f"🌟 明星品类（{len(star_cats)}个）：{', '.join(star_cats['一级分类'].tolist())}")
        
        if len(optimize_cats) > 0:
            insights.append(f"⚠️ 需优化品类（{len(optimize_cats)}个）：{', '.join(optimize_cats['一级分类'].tolist())}")
    
    return insights


# ============================================================================
# 可视化渲染函数
# ============================================================================

def render_category_analysis(df: pd.DataFrame):
    """渲染商品分类结构分析主界面"""
    
    st.markdown("### 🏪 商品分类结构竞争力分析")
    
    st.info("""
    **💡 核心理念**: 商品分类结构 = 门店供给能力 → 影响流量、客单价、复购率
    - ✅ **结构深度**：单一品类SKU越多，满足细分需求越好
    - ✅ **结构广度**：覆盖品类越多，一站式购物体验越好
    - ✅ **结构质量**：高毛利/高频/刚需品类占比越高，盈利能力越强
    """)
    
    # 执行分析
    results = analyze_category_structure(df)
    
    if not results:
        st.warning("⚠️ 数据中缺少分类字段，无法进行分类分析")
        return
    
    # 智能洞察
    st.markdown("#### 🎯 智能洞察")
    insights = get_category_insights(results)
    for insight in insights:
        st.markdown(f"- {insight}")
    
    st.markdown("---")
    
    # 创建Tab页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 品类结构总览",
        "🔍 品类深度分析",
        "💎 贡献度矩阵",
        "🔗 跨品类组合",
        "📋 完整数据"
    ])
    
    # === Tab1: 品类结构总览 ===
    with tab1:
        render_category_overview(results)
    
    # === Tab2: 品类深度分析 ===
    with tab2:
        render_category_detail(df, results)
    
    # === Tab3: 贡献度矩阵 ===
    with tab3:
        render_contribution_matrix(results)
    
    # === Tab4: 跨品类组合 ===
    with tab4:
        render_cross_category(results)
    
    # === Tab5: 完整数据 ===
    with tab5:
        render_full_data(results)


def render_category_overview(results: Dict):
    """Tab1: 品类结构总览"""
    st.markdown("#### 📊 一级品类结构总览")
    
    if 'level1' not in results:
        st.warning("暂无一级分类数据")
        return
    
    level1 = results['level1']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 销售额占比饼图
        fig = go.Figure(data=[
            go.Pie(
                labels=level1['一级分类'],
                values=level1['销售额'],
                hole=0.4,
                textinfo='label+percent',
                marker=dict(colors=px.colors.qualitative.Set3)
            )
        ])
        fig.update_layout(
            title="品类销售额占比",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # SKU数量分布
        fig = go.Figure(data=[
            go.Bar(
                x=level1['一级分类'],
                y=level1['SKU数'],
                text=level1['SKU数'],
                textposition='auto',
                marker_color='lightblue'
            )
        ])
        fig.update_layout(
            title="各品类SKU数量",
            xaxis_title="品类",
            yaxis_title="SKU数",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 综合指标对比
    st.markdown("#### 📈 品类综合对比")
    
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("销售额排行", "订单数排行", "平均毛利率")
    )
    
    # 销售额
    fig.add_trace(
        go.Bar(
            y=level1['一级分类'],
            x=level1['销售额'],
            orientation='h',
            name='销售额',
            marker_color='#3498db'
        ),
        row=1, col=1
    )
    
    # 订单数
    fig.add_trace(
        go.Bar(
            y=level1['一级分类'],
            x=level1['订单数'],
            orientation='h',
            name='订单数',
            marker_color='#2ecc71'
        ),
        row=1, col=2
    )
    
    # 毛利率
    if '平均毛利率' in level1.columns:
        fig.add_trace(
            go.Bar(
                y=level1['一级分类'],
                x=level1['平均毛利率'],
                orientation='h',
                name='毛利率%',
                marker_color='#f39c12'
            ),
            row=1, col=3
        )
    
    fig.update_layout(
        height=max(300, len(level1) * 30),
        showlegend=False
    )
    fig.update_yaxes(categoryorder='total ascending')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 三级分类概览（如果有三级分类数据）
    if 'level3' in results:
        st.markdown("---")
        st.markdown("#### 📦 三级分类结构概览")
        
        level3 = results['level3']
        
        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("三级分类总数", f"{level3['三级分类'].nunique()}个")
        with col2:
            top_category = level3.nlargest(1, '销售额')
            if not top_category.empty:
                st.metric("销售额最高", top_category.iloc[0]['三级分类'])
        with col3:
            if '平均毛利率' in level3.columns:
                top_margin = level3.nlargest(1, '平均毛利率')
                if not top_margin.empty:
                    st.metric("毛利率最高", top_margin.iloc[0]['三级分类'])
        
        # 展示TOP20三级分类
        st.markdown("##### 🏆 TOP20 三级分类（按销售额）")
        
        top20 = level3.nlargest(20, '销售额')[['一级分类', '三级分类', 'SKU数', '销售额', '订单数', '平均毛利率']]
        
        # 格式化显示
        st.dataframe(
            top20.style.format({
                'SKU数': '{:,.0f}',
                '销售额': '¥{:,.2f}',
                '订单数': '{:,.0f}',
                '平均毛利率': '{:.1f}%'
            }).background_gradient(subset=['销售额'], cmap='Blues'),
            use_container_width=True,
            height=400
        )
        
        # 三级分类销售额可视化
        col1, col2 = st.columns(2)
        
        with col1:
            # TOP15三级分类销售额
            top15_sales = level3.nlargest(15, '销售额')
            fig = go.Figure(data=[
                go.Bar(
                    y=top15_sales['三级分类'],
                    x=top15_sales['销售额'],
                    orientation='h',
                    text=top15_sales['销售额'].apply(lambda x: f'¥{x:,.0f}'),
                    textposition='auto',
                    marker_color='lightcoral'
                )
            ])
            fig.update_layout(
                title="TOP15 三级分类销售额",
                xaxis_title="销售额（元）",
                height=450,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 三级分类SKU数分布
            top15_sku = level3.nlargest(15, 'SKU数')
            fig = go.Figure(data=[
                go.Bar(
                    y=top15_sku['三级分类'],
                    x=top15_sku['SKU数'],
                    orientation='h',
                    text=top15_sku['SKU数'],
                    textposition='auto',
                    marker_color='lightgreen'
                )
            ])
            fig.update_layout(
                title="TOP15 三级分类SKU数",
                xaxis_title="SKU数量",
                height=450,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)


def render_category_detail(df: pd.DataFrame, results: Dict):
    """Tab2: 品类深度分析"""
    st.markdown("#### 🔍 选择品类查看详细分析")
    
    if 'level1' not in results:
        st.warning("暂无品类数据")
        return
    
    level1 = results['level1']
    
    # 检测字段名
    category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
    subcategory_col = '三级分类名' if '三级分类名' in df.columns else '三级分类'
    
    # 品类选择器
    selected_cat = st.selectbox(
        "选择品类",
        options=level1['一级分类'].tolist()
    )
    
    # 检查是否有三级分类字段
    if subcategory_col not in df.columns:
        st.warning("""
        ⚠️ 数据中缺少『三级分类名』或『三级分类』字段，无法进行深度分析
        
        **💡 建议**：
        - 如果原始数据中有三级分类信息，请确保字段名为『三级分类名』或『三级分类』
        - 可以在『品类结构总览』Tab查看一级分类汇总数据
        """)
        return
    
    if selected_cat:
        # 筛选该品类数据
        cat_data = df[df[category_col] == selected_cat]
        
        # 关键指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sku_count = cat_data['商品名称'].nunique()
            st.metric("SKU数量", f"{sku_count}个")
        
        with col2:
            total_sales = cat_data['商品实售价'].sum()
            st.metric("总销售额", f"¥{total_sales:.2f}")
        
        with col3:
            order_count = cat_data['订单ID'].nunique()
            st.metric("订单数", f"{order_count}单")
        
        with col4:
            if '毛利率' in cat_data.columns:
                avg_margin = cat_data['毛利率'].mean()
                st.metric("平均毛利率", f"{avg_margin:.1f}%")
        
        st.markdown("---")
        
        # 三级分类分析
        st.markdown(f"#### 📦 {selected_cat} - 三级分类明细")
        
        level3_data = cat_data.groupby(subcategory_col).agg({
            '商品名称': 'nunique',
            '商品实售价': ['sum', 'mean'],
            '订单ID': 'nunique'
        }).round(2)
        
        level3_data.columns = ['SKU数', '销售额', '平均售价', '订单数']
        level3_data = level3_data.reset_index()
        # 统一列名为'三级分类'，方便后续使用
        level3_data.rename(columns={subcategory_col: '三级分类'}, inplace=True)
        level3_data = level3_data.sort_values('销售额', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 三级分类销售额
            fig = go.Figure(data=[
                go.Bar(
                    y=level3_data.head(10)['三级分类'],
                    x=level3_data.head(10)['销售额'],
                    orientation='h',
                    marker_color='lightcoral'
                )
            ])
            fig.update_layout(
                title=f"TOP10 三级分类销售额",
                xaxis_title="销售额（元）",
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 价格分布
            fig = go.Figure(data=[
                go.Histogram(
                    x=cat_data['商品实售价'],
                    nbinsx=20,
                    marker_color='lightgreen'
                )
            ])
            fig.update_layout(
                title=f"{selected_cat} 价格分布",
                xaxis_title="商品售价（元）",
                yaxis_title="商品数量",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # TOP商品
        st.markdown(f"#### 🏆 {selected_cat} - TOP20热销商品")
        
        top_products = cat_data.groupby('商品名称').agg({
            '商品实售价': 'sum',
            '订单ID': 'nunique'
        }).round(2)
        top_products.columns = ['销售额', '订单数']
        top_products = top_products.reset_index().sort_values('销售额', ascending=False).head(20)
        
        st.dataframe(top_products, use_container_width=True, height=400)


def render_contribution_matrix(results: Dict):
    """Tab3: 品类贡献度矩阵"""
    st.markdown("#### 💎 品类贡献度矩阵（战略定位）")
    
    st.info("""
    **四象限战略矩阵**：
    - 🌟 **明星品类**：高销售额 + 高毛利率 → 核心竞争力，重点维护
    - 💎 **高价值品类**：低销售额 + 高毛利率 → 潜力品类，重点培育
    - 🔥 **引流品类**：高销售额 + 低毛利率 → 导流作用，保持竞争力
    - ⚠️ **优化品类**：低销售额 + 低毛利率 → 优化对象，考虑调整
    """)
    
    if 'contribution_matrix' not in results:
        st.warning("暂无贡献度矩阵数据")
        return
    
    matrix = results['contribution_matrix']
    
    # 散点图
    fig = go.Figure()
    
    colors = {
        '🌟 明星品类': '#2ecc71',
        '💎 高价值品类': '#9b59b6',
        '🔥 引流品类': '#e74c3c',
        '⚠️ 优化品类': '#95a5a6'
    }
    
    for cat_type in matrix['品类定位'].unique():
        data = matrix[matrix['品类定位'] == cat_type]
        fig.add_trace(
            go.Scatter(
                x=data['销售额'],
                y=data['平均毛利率'],
                mode='markers+text',
                name=cat_type,
                text=data['一级分类'],
                textposition='top center',
                marker=dict(
                    size=data['订单数'] / 10,
                    color=colors.get(cat_type, '#3498db'),
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{text}</b><br>销售额: ¥%{x:.2f}<br>毛利率: %{y:.1f}%<extra></extra>'
            )
        )
    
    # 添加中位数参考线
    sales_median = matrix['销售额'].median()
    profit_median = matrix['平均毛利率'].median()
    
    fig.add_vline(x=sales_median, line_dash="dash", line_color="gray", annotation_text="销售额中位数")
    fig.add_hline(y=profit_median, line_dash="dash", line_color="gray", annotation_text="毛利率中位数")
    
    fig.update_layout(
        title="品类贡献度矩阵（气泡大小=订单数）",
        xaxis_title="销售额（元）",
        yaxis_title="平均毛利率（%）",
        height=600,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 分类统计
    st.markdown("#### 📊 品类定位分布")
    
    type_stats = matrix.groupby('品类定位').agg({
        '一级分类': 'count',
        '销售额': 'sum',
        '平均毛利率': 'mean'
    }).round(2)
    type_stats.columns = ['品类数', '总销售额', '平均毛利率']
    type_stats = type_stats.reset_index()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(type_stats, use_container_width=True)
    
    with col2:
        # 各定位品类明细
        for cat_type in matrix['品类定位'].unique():
            cats = matrix[matrix['品类定位'] == cat_type]['一级分类'].tolist()
            st.markdown(f"**{cat_type}**: {', '.join(cats)}")


def render_cross_category(results: Dict):
    """Tab4: 跨品类组合分析"""
    st.markdown("#### 🔗 跨品类购买组合分析（与订单组合联动）")
    
    st.info("""
    **💡 业务价值**: 分析用户跨品类购买偏好，指导：
    - 🛒 商品陈列布局（关联品类就近摆放）
    - 📦 套餐组合设计（跨品类组合促销）
    - 🎯 交叉推荐策略（买了A品类推荐B品类）
    """)
    
    if 'cross_category' not in results:
        st.warning("暂无跨品类组合数据")
        return
    
    cross_cat = results['cross_category']
    
    # 组合热力图
    st.markdown("#### 🔥 品类组合热度TOP20")
    
    fig = go.Figure(data=[
        go.Bar(
            y=cross_cat['品类A'] + ' + ' + cross_cat['品类B'],
            x=cross_cat['共同购买次数'],
            orientation='h',
            text=cross_cat['共同购买次数'],
            textposition='auto',
            marker=dict(
                color=cross_cat['共同购买次数'],
                colorscale='Viridis',
                showscale=True
            )
        )
    ])
    
    fig.update_layout(
        title="跨品类组合购买频次",
        xaxis_title="共同购买次数",
        yaxis_title="",
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 详细数据表
    st.markdown("#### 📋 跨品类组合明细")
    
    display_data = cross_cat.copy()
    display_data['组合'] = display_data['品类A'] + ' + ' + display_data['品类B']
    display_data = display_data[['组合', '共同购买次数']]
    
    st.dataframe(display_data, use_container_width=True, height=400)
    
    # 策略建议
    st.markdown("#### 💡 策略建议")
    
    if len(cross_cat) > 0:
        top_combo = cross_cat.iloc[0]
        st.success(f"""
        **🌟 最强组合**: {top_combo['品类A']} + {top_combo['品类B']}
        - 共同购买: {top_combo['共同购买次数']}次
        
        **建议**:
        1. 🛒 将这两个品类的商品就近陈列
        2. 📦 设计跨品类套餐促销（如"零食+饮料组合装"）
        3. 🎯 推荐系统：购买了{top_combo['品类A']}的用户，推荐{top_combo['品类B']}
        """)


def render_full_data(results: Dict):
    """Tab5: 完整数据"""
    st.markdown("#### 📋 完整分析数据")
    
    if 'level1' in results:
        st.markdown("##### 一级分类统计")
        st.dataframe(
            results['level1'].style.format({
                'SKU数': '{:,.0f}',
                '订单数': '{:,.0f}',
                '销售额': '¥{:,.2f}',
                '平均售价': '¥{:.2f}',
                '总毛利': '¥{:,.2f}',
                '平均毛利率': '{:.1f}%',
                '销售占比%': '{:.2f}%'
            }),
            use_container_width=True
        )
    
    if 'level3' in results:
        st.markdown("##### 三级分类统计")
        st.dataframe(
            results['level3'].style.format({
                'SKU数': '{:,.0f}',
                '订单数': '{:,.0f}',
                '销售额': '¥{:,.2f}',
                '平均售价': '¥{:.2f}',
                '总毛利': '¥{:,.2f}',
                '平均毛利率': '{:.1f}%'
            }),
            use_container_width=True,
            height=400
        )


# ============================================================================
# 主函数（集成到主看板使用）
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="商品分类结构分析", page_icon="🏪", layout="wide")
    
    st.title("🏪 商品分类结构竞争力分析")
    
    st.markdown("""
    本模块独立运行用于测试，实际使用时会集成到主看板中。
    请上传数据文件进行分析。
    """)
    
    uploaded_file = st.file_uploader("上传订单数据（Excel格式）", type=['xlsx', 'xls'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        render_category_analysis(df)
