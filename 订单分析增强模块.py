# -*- coding: utf-8 -*-
"""
订单数据分析增强模块
为智能门店经营看板提供完整的订单分析功能
基于 standard_business_config 的标准业务逻辑
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# ==============================================================================
# 增强的订单概览模块
# ==============================================================================

def render_enhanced_order_overview(df: pd.DataFrame, order_summary: Dict[str, Any]) -> None:
    """增强的订单概览 - 包含数据质量检查、关键指标卡片、渠道分布等"""
    
    st.subheader("📊 订单业务概览")
    
    # 1. 数据时间范围检测
    if '下单时间' in df.columns:
        min_date = df['下单时间'].min()
        max_date = df['下单时间'].max()
        days_span = (max_date - min_date).days + 1
        
        st.info(f"📅 数据时间范围: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')} ({days_span}天)")
    
    # 2. 核心指标卡片（第一行）
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "总订单数",
            f"{order_summary.get('订单总数', 0):,}",
            help="统计期间内的总订单数量"
        )
    
    with col2:
        total_sales = order_summary.get('总销售额', 0)
        st.metric(
            "商品销售额",
            f"¥{total_sales:,.0f}",
            help="所有订单的商品实售价总和（不含打包费和配送费）"
        )
    
    with col3:
        total_revenue = order_summary.get('订单总收入', 0)
        st.metric(
            "订单总收入",
            f"¥{total_revenue:,.0f}",
            help="商品实售价 + 打包费 + 用户支付配送费"
        )
    
    with col4:
        avg_price = order_summary.get('平均客单价', 0)
        median_price = order_summary.get('客单价中位数', 0)
        st.metric(
            "平均客单价",
            f"¥{avg_price:.2f}",
            delta=f"中位数¥{median_price:.2f}",
            help="平均每单商品销售额 (均值)"
        )
    
    with col5:
        total_profit = order_summary.get('总利润额', 0)
        avg_profit = order_summary.get('平均订单利润', 0)
        st.metric(
            "总利润额",
            f"¥{total_profit:,.0f}",
            delta=f"均¥{avg_profit:.2f}/单",
            delta_color="normal",
            help="订单总收入 - 所有成本 = 净利润"
        )
    
    with col6:
        profit_ratio = order_summary.get('盈利订单比例', 0)
        profit_orders = order_summary.get('盈利订单数', 0)
        st.metric(
            "盈利订单占比",
            f"{profit_ratio:.1%}",
            delta=f"{profit_orders:,}单",
            delta_color="normal",
            help="实际盈利订单占比"
        )
    
    # 3. 成本结构卡片（第二行）
    st.markdown("---")
    st.write("**💵 成本结构分析**")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        # 计算商品总成本
        total_product_cost = order_summary.get('总商品成本', df['成本'].sum() if '成本' in df.columns else 0)
        avg_product_cost = total_product_cost / order_summary.get('订单总数', 1) if order_summary.get('订单总数', 0) > 0 else 0
        st.metric(
            "总商品成本",
            f"¥{total_product_cost:,.0f}",
            delta=f"均¥{avg_product_cost:.2f}/单",
            delta_color="inverse",
            help="所有商品的采购成本总和"
        )
    
    with col2:
        delivery_cost = order_summary.get('总配送成本', 0)
        avg_delivery = order_summary.get('平均配送成本', 0)
        st.metric(
            "总配送成本",
            f"¥{delivery_cost:,.0f}",
            delta=f"均¥{avg_delivery:.2f}/单",
            delta_color="inverse",
            help="标准公式: 用户支付配送费 - 配送费减免 - 物流配送费"
        )
    
    with col3:
        # 计算活动营销成本（不含商品折扣和配送费减免）
        activity_marketing_cost = order_summary.get('总活动营销成本', 0)
        avg_activity_marketing = activity_marketing_cost / order_summary.get('订单总数', 1) if order_summary.get('订单总数', 0) > 0 else 0
        st.metric(
            "活动营销成本",
            f"¥{activity_marketing_cost:,.0f}",
            delta=f"均¥{avg_activity_marketing:.2f}/单",
            delta_color="inverse",
            help="包括满减、代金券、满赠、新客减免等（不含商品折扣，配送费减免已在配送成本中扣除）"
        )
    
    with col4:
        # 计算商品折扣成本
        product_discount_cost = order_summary.get('总商品折扣成本', df.groupby('订单ID')['商品减免金额'].first().sum() if '商品减免金额' in df.columns else 0)
        avg_product_discount = product_discount_cost / order_summary.get('订单总数', 1) if order_summary.get('订单总数', 0) > 0 else 0
        st.metric(
            "商品折扣成本",
            f"¥{product_discount_cost:,.0f}",
            delta=f"均¥{avg_product_discount:.2f}/单",
            delta_color="inverse",
            help="商品原价与实售价的差额"
        )
    
    with col5:
        # 计算平台佣金总额
        total_commission = order_summary.get('总平台佣金', df.groupby('订单ID')['平台佣金'].first().sum() if '平台佣金' in df.columns else 0)
        avg_commission = total_commission / order_summary.get('订单总数', 1) if order_summary.get('订单总数', 0) > 0 else 0
        st.metric(
            "总平台佣金",
            f"¥{total_commission:,.0f}",
            delta=f"均¥{avg_commission:.2f}/单",
            delta_color="inverse",
            help="支付给平台的佣金总额"
        )
    
    with col6:
        if total_sales > 0:
            profit_margin = (total_profit / total_sales) * 100
            st.metric(
                "整体利润率",
                f"{profit_margin:.1f}%",
                help="总利润占总销售额的百分比"
            )
    
    # 3.5 利润率分析（第三行）
    st.markdown("---")
    st.write("**📈 利润率与成本率分析**")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        # 毛利率 = (销售额 - 商品成本) / 销售额
        if total_sales > 0:
            total_product_cost = order_summary.get('总商品成本', df['成本'].sum() if '成本' in df.columns else 0)
            gross_margin = ((total_sales - total_product_cost) / total_sales) * 100
            st.metric(
                "毛利率",
                f"{gross_margin:.1f}%",
                help="毛利率 = (销售额 - 商品成本) / 销售额"
            )
    
    with col2:
        # 配送成本率
        if total_sales > 0:
            delivery_cost = order_summary.get('总配送成本', 0)
            delivery_rate = (delivery_cost / total_sales) * 100
            st.metric(
                "配送成本率",
                f"{delivery_rate:.1f}%",
                help="配送成本占销售额的百分比"
            )
    
    with col3:
        # 活动营销成本率（不含商品折扣）
        if total_sales > 0:
            activity_marketing_cost = order_summary.get('总活动营销成本', 0)
            activity_marketing_rate = (activity_marketing_cost / total_sales) * 100
            st.metric(
                "活动营销率",
                f"{activity_marketing_rate:.1f}%",
                help="活动营销成本占销售额的百分比（不含商品折扣）"
            )
    
    with col4:
        # 商品折扣率
        if total_sales > 0:
            product_discount_cost = order_summary.get('总商品折扣成本', df.groupby('订单ID')['商品减免金额'].first().sum() if '商品减免金额' in df.columns else 0)
            product_discount_rate = (product_discount_cost / total_sales) * 100
            st.metric(
                "商品折扣率",
                f"{product_discount_rate:.1f}%",
                help="商品折扣成本占销售额的百分比"
            )
    
    with col5:
        # 平台佣金率
        if total_sales > 0:
            total_commission = order_summary.get('总平台佣金', df.groupby('订单ID')['平台佣金'].first().sum() if '平台佣金' in df.columns else 0)
            commission_rate = (total_commission / total_sales) * 100
            st.metric(
                "平台佣金率",
                f"{commission_rate:.1f}%",
                help="平台佣金占销售额的百分比"
            )
    
    with col6:
        # 综合成本率（所有成本合计）
        if total_sales > 0:
            total_product_cost = order_summary.get('总商品成本', df['成本'].sum() if '成本' in df.columns else 0)
            total_commission = order_summary.get('总平台佣金', df.groupby('订单ID')['平台佣金'].first().sum() if '平台佣金' in df.columns else 0)
            delivery_cost = order_summary.get('总配送成本', 0)
            activity_marketing_cost = order_summary.get('总活动营销成本', 0)
            product_discount_cost = order_summary.get('总商品折扣成本', df.groupby('订单ID')['商品减免金额'].first().sum() if '商品减免金额' in df.columns else 0)
            total_cost = total_product_cost + delivery_cost + activity_marketing_cost + product_discount_cost + total_commission
            total_cost_rate = (total_cost / total_sales) * 100
            st.metric(
                "综合成本率",
                f"{total_cost_rate:.1f}%",
                help="所有成本合计占销售额的百分比"
            )
    
    # 4. 数据质量检查
    st.markdown("---")
    st.write("**🔍 数据质量检查**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 缺失值检查
        key_columns = ['订单ID', '商品名称', '商品实售价', '销量', '下单时间', '门店名称']
        missing_check = {}
        for col in key_columns:
            if col in df.columns:
                missing_count = df[col].isnull().sum()
                missing_rate = missing_count / len(df) * 100
                missing_check[col] = f"{missing_count:,} ({missing_rate:.1f}%)"
        
        if missing_check:
            missing_df = pd.DataFrame(list(missing_check.items()), 
                                     columns=['字段', '缺失情况'])
            st.dataframe(missing_df, use_container_width=True)
    
    with col2:
        # 异常值检测
        anomalies = []
        
        # 检查负价格
        if '商品实售价' in df.columns:
            negative_price = (df['商品实售价'] < 0).sum()
            if negative_price > 0:
                anomalies.append(f"❌ 负售价商品: {negative_price}个")
        
        # 检查零销量
        if '销量' in df.columns:
            zero_qty = (df['销量'] <= 0).sum()
            if zero_qty > 0:
                anomalies.append(f"⚠️ 零销量记录: {zero_qty}条")
        
        # 检查异常配送费
        if '物流配送费' in df.columns:
            high_delivery = (df['物流配送费'] > 20).sum()
            if high_delivery > 0:
                anomalies.append(f"⚠️ 配送费>20元: {high_delivery}单")
        
        if anomalies:
            st.warning("**数据异常提醒:**\n\n" + "\n\n".join(anomalies))
        else:
            st.success("✅ 未发现明显数据异常")
    
    # 5. 渠道与门店分布（可视化）
    st.markdown("---")
    st.write("**📈 业务分布分析**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 渠道分布
        if '渠道' in df.columns:
            channel_stats = df.groupby('渠道').agg({
                '订单ID': pd.Series.nunique,
                '商品实售价': lambda x: (x * df.loc[x.index, '销量']).sum() if '销量' in df.columns else x.sum()
            }).reset_index()
            channel_stats.columns = ['渠道', '订单数', '销售额']
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('渠道订单量占比', '渠道销售额占比'),
                specs=[[{'type':'pie'}, {'type':'pie'}]]
            )
            
            fig.add_trace(
                go.Pie(labels=channel_stats['渠道'], values=channel_stats['订单数'], name='订单量'),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Pie(labels=channel_stats['渠道'], values=channel_stats['销售额'], name='销售额'),
                row=1, col=2
            )
            
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 门店分布
        if '门店名称' in df.columns:
            store_stats = df.groupby('门店名称').agg({
                '订单ID': pd.Series.nunique,
                '商品实售价': lambda x: (x * df.loc[x.index, '销量']).sum() if '销量' in df.columns else x.sum()
            }).reset_index()
            store_stats.columns = ['门店', '订单数', '销售额']
            store_stats = store_stats.sort_values('销售额', ascending=True).tail(10)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=store_stats['门店'],
                x=store_stats['销售额'],
                orientation='h',
                text=store_stats['销售额'].apply(lambda x: f'¥{x:,.0f}'),
                textposition='auto'
            ))
            fig.update_layout(
                title="TOP 10 门店销售额",
                xaxis_title="销售额(元)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 6. 业务逻辑说明（可折叠）
    with st.expander("📖 标准业务逻辑说明"):
        st.markdown("""
        ### 🎯 本看板采用的标准业务逻辑
        
        #### 核心计算公式:
        
        1. **预估订单收入** =  
           `(订单零售额 + 打包费 - 商家活动支出 - 平台佣金 + 用户支付配送费)`
        
        2. **商家活动支出** =  
           `(配送费减免金额 + 满减金额 + 商品减免金额 + 商家代金券)`
        
        3. **配送成本** =  
           `(用户支付配送费 - 配送费减免金额 - 物流配送费)`
        
        4. **订单实际利润额** =  
           `预估订单收入 - 配送成本`
        
        #### 字段说明:
        
        - **商品实售价**: 商品在前端展示的原价（非用户实付价）
        - **用户支付金额**: 用户实际支付价格（考虑各种补贴活动）
        - **订单ID**: 唯一订单标识，同一订单多个商品会有多行记录
        - **销量**: 该商品在订单中的数量
        
        #### 注意事项:
        
        - 订单级字段（如物流配送费、平台佣金）在同一订单的多行中会重复显示
        - 利润计算仅扣减"物流配送费"和"平台佣金"，不包含商品成本
        - 负利润订单可能由于配送费过高或平台佣金过高导致
        """)


# ==============================================================================
# 增强的利润分析模块
# ==============================================================================

def render_enhanced_profit_analysis(df: pd.DataFrame, order_summary: Dict[str, Any]) -> None:
    """增强的利润分析 - 负毛利商品、成本结构、主凑单品对比等"""
    
    st.subheader("💰 利润深度分析")
    
    # 1. 利润概览指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总利润额",
            f"¥{order_summary.get('总利润额', 0):,.0f}",
            help="按标准业务逻辑计算的实际利润总额"
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
        profit_ratio = order_summary.get('盈利订单比例', 0)
        color = "normal" if profit_ratio >= 0.8 else "inverse"
        st.metric(
            "盈利订单占比",
            f"{profit_ratio:.1%}",
            delta="健康" if profit_ratio >= 0.8 else "需关注",
            delta_color=color,
            help="盈利订单占比 >= 80% 为健康状态"
        )
    
    # 2. 负毛利商品分析
    st.markdown("---")
    st.write("**🚨 负毛利商品识别 (Top 50)**")
    
    if '利润额' in df.columns and '商品名称' in df.columns:
        # 计算商品级利润
        product_profit = df.groupby('商品名称').agg({
            '利润额': 'sum',
            '销量': 'sum',
            '商品实售价': 'mean',
            '订单ID': pd.Series.nunique
        }).reset_index()
        product_profit.columns = ['商品名称', '总利润', '总销量', '平均售价', '订单数']
        
        # 筛选负利润商品
        negative_products = product_profit[product_profit['总利润'] < 0].copy()
        negative_products['单位利润'] = negative_products['总利润'] / negative_products['总销量']
        negative_products = negative_products.sort_values('总利润').head(50)
        
        if len(negative_products) > 0:
            st.warning(f"⚠️ 发现 {len(negative_products)} 个负毛利商品（显示前50）")
            
            # 格式化展示
            display_df = negative_products.copy()
            display_df['总利润'] = display_df['总利润'].apply(lambda x: f"¥{x:,.2f}")
            display_df['平均售价'] = display_df['平均售价'].apply(lambda x: f"¥{x:.2f}")
            display_df['单位利润'] = display_df['单位利润'].apply(lambda x: f"¥{x:.2f}")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=300
            )
            
            # 可视化负利润TOP 10
            if len(negative_products) >= 10:
                top10_negative = negative_products.head(10)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=top10_negative['商品名称'],
                    y=top10_negative['总利润'],
                    marker_color='indianred',
                    text=top10_negative['总利润'].apply(lambda x: f'¥{x:,.0f}'),
                    textposition='auto'
                ))
                fig.update_layout(
                    title="负利润 TOP 10 商品",
                    xaxis_title="商品名称",
                    yaxis_title="总利润(元)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ 未发现负毛利商品")
    else:
        st.info("缺少必要字段，无法进行负毛利分析")
    
    # 3. 成本结构分析
    st.markdown("---")
    st.write("**📊 成本结构占比**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 成本结构饼图
        cost_items = {
            '配送成本': order_summary.get('总配送成本', 0),
            '营销成本': order_summary.get('总营销成本', 0),
        }
        
        # 添加其他成本项（如果有）
        if 'total_commission' in order_summary:
            cost_items['平台佣金'] = order_summary.get('total_commission', 0)
        
        cost_df = pd.DataFrame(list(cost_items.items()), columns=['成本项', '金额'])
        cost_df = cost_df[cost_df['金额'] > 0]  # 只显示非零成本
        
        if len(cost_df) > 0:
            fig = px.pie(
                cost_df,
                values='金额',
                names='成本项',
                title='成本结构占比'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 成本率对比
        total_sales = order_summary.get('总销售额', 1)  # 避免除零
        cost_rates = {
            '配送成本率': (order_summary.get('总配送成本', 0) / total_sales) * 100,
            '营销成本率': (order_summary.get('总营销成本', 0) / total_sales) * 100,
            '利润率': (order_summary.get('总利润额', 0) / total_sales) * 100
        }
        
        rate_df = pd.DataFrame(list(cost_rates.items()), columns=['指标', '占比(%)'])
        
        fig = px.bar(
            rate_df,
            x='指标',
            y='占比(%)',
            title='成本率与利润率对比',
            text=rate_df['占比(%)'].apply(lambda x: f'{x:.1f}%')
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # 4. 主单品 vs 凑单品利润对比
    st.markdown("---")
    st.write("**🎯 主单品 vs 凑单品分析**")
    
    if '商品角色' in df.columns and '利润额' in df.columns:
        role_analysis = df.groupby('商品角色').agg({
            '订单ID': pd.Series.nunique,
            '商品名称': 'count',
            '利润额': 'sum',
            '销量': 'sum'
        }).reset_index()
        role_analysis.columns = ['商品角色', '订单数', '商品条目数', '总利润', '总销量']
        role_analysis['平均利润'] = role_analysis['总利润'] / role_analysis['订单数']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(
                role_analysis.style.format({
                    '总利润': '¥{:,.2f}',
                    '平均利润': '¥{:,.2f}',
                    '订单数': '{:,}',
                    '商品条目数': '{:,}',
                    '总销量': '{:,}'
                }),
                use_container_width=True
            )
        
        with col2:
            fig = px.bar(
                role_analysis,
                x='商品角色',
                y='总利润',
                title='主单品 vs 凑单品利润对比',
                text=role_analysis['总利润'].apply(lambda x: f'¥{x:,.0f}')
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("未找到商品角色字段，请确保数据预处理完成")
    
    # 5. 利润趋势图（按日期）
    st.markdown("---")
    st.write("**📈 利润趋势分析**")
    
    if '下单日期' in df.columns and '利润额' in df.columns and '订单ID' in df.columns:
        daily_profit = df.groupby('下单日期').agg({
            '利润额': 'sum',
            '订单ID': pd.Series.nunique
        }).reset_index()
        daily_profit.columns = ['日期', '总利润', '订单数']
        daily_profit['平均订单利润'] = daily_profit['总利润'] / daily_profit['订单数']
        
        # 双轴图表：总利润（柱状图） + 平均订单利润（折线图）
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=daily_profit['日期'],
                y=daily_profit['总利润'],
                name='总利润',
                marker_color='lightblue'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=daily_profit['日期'],
                y=daily_profit['平均订单利润'],
                name='平均订单利润',
                mode='lines+markers',
                line=dict(color='red', width=2)
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title='每日利润趋势',
            xaxis_title='日期',
            height=400
        )
        fig.update_yaxes(title_text="总利润(元)", secondary_y=False)
        fig.update_yaxes(title_text="平均订单利润(元)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("缺少日期或利润字段，无法生成趋势图")


# ==============================================================================
# 主函数（测试用）
# ==============================================================================

if __name__ == "__main__":
    print("订单分析增强模块已加载")
    print("请在主看板文件中导入并使用这些函数")
