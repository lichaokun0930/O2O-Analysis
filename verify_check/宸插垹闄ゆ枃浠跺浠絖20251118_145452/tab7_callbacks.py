#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tab 7: 营销分析看板 - 回调函数模块
双维度智能诊断:科学方法(品类动态阈值) + 评分模型(综合评估)
"""

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from 科学八象限分析器 import ScientificQuadrantAnalyzer
from 评分模型分析器 import ScoringModelAnalyzer


def register_tab7_callbacks(app):
    """注册Tab 7的所有回调函数"""
    
    # ==================== 回调1: 筛选条件更新 ====================
    @app.callback(
        [Output('tab7-scientific-data', 'data'),
         Output('tab7-scoring-data', 'data')],
        [Input('tab7-channel-filter', 'value'),
         Input('tab7-category-filter', 'value')],
        State('tab7-raw-data', 'data'),
        prevent_initial_call=True
    )
    def update_analysis_by_filter(channel, category, raw_data):
        """根据渠道和品类筛选更新分析数据"""
        if not raw_data:
            raise PreventUpdate
        
        try:
            df = pd.DataFrame(raw_data)
            
            # 应用渠道筛选
            if channel != 'ALL' and '渠道' in df.columns:
                df = df[df['渠道'] == channel].copy()
            
            # 应用品类筛选
            if category != 'ALL' and '一级分类名' in df.columns:
                df = df[df['一级分类名'] == category].copy()
            
            if len(df) == 0:
                return [], []
            
            # 重新分析
            scientific_analyzer = ScientificQuadrantAnalyzer(df, use_category_threshold=True)
            scientific_result = scientific_analyzer.analyze_with_confidence()
            
            scoring_analyzer = ScoringModelAnalyzer(df)
            scoring_result = scoring_analyzer.analyze_with_scoring({
                '营销效率': 0.25,
                '盈利能力': 0.45,
                '动销健康': 0.3
            })
            
            return scientific_result.to_dict('records'), scoring_result.to_dict('records')
            
        except Exception as e:
            print(f"❌ 筛选更新失败: {e}")
            raise PreventUpdate
    
    
    # ==================== 回调2: 科学方法关键指标 ====================
    @app.callback(
        [Output('scientific-golden-count', 'children'),
         Output('scientific-eliminate-count', 'children'),
         Output('scientific-low-confidence-count', 'children')],
        Input('tab7-scientific-data', 'data')
    )
    def update_scientific_metrics(scientific_data):
        """更新科学方法关键指标"""
        if not scientific_data:
            return "0", "0", "0"
        
        try:
            df = pd.DataFrame(scientific_data)
            
            if '象限名称' not in df.columns or '置信度标签' not in df.columns:
                return "0", "0", "0"
            
            golden_count = len(df[df['象限名称'].str.contains('黄金', na=False)])
            eliminate_count = len(df[df['象限名称'].str.contains('淘汰', na=False)])
            low_conf_count = len(df[df['置信度标签'] == '低置信'])
        except Exception as e:
            print(f"❌ 科学方法指标更新失败: {e}")
            return "0", "0", "0"
        
        return (
            f"{golden_count} ({golden_count/len(df)*100:.1f}%)",
            f"{eliminate_count} ({eliminate_count/len(df)*100:.1f}%)",
            f"{low_conf_count} ({low_conf_count/len(df)*100:.1f}%)"
        )
    
    
    # ==================== 回调3: 评分模型关键指标 ====================
    @app.callback(
        [Output('scoring-avg-score', 'children'),
         Output('scoring-excellent-count', 'children'),
         Output('scoring-poor-count', 'children')],
        Input('tab7-scoring-data', 'data')
    )
    def update_scoring_metrics(scoring_data):
        """更新评分模型关键指标"""
        if not scoring_data:
            return "0.0", "0", "0"
        
        try:
            df = pd.DataFrame(scoring_data)
            
            if '综合得分' not in df.columns or '评分等级' not in df.columns:
                return "0.0", "0", "0"
            
            avg_score = df['综合得分'].mean()
            excellent_count = len(df[df['评分等级'] == '⭐优秀'])
            poor_count = len(df[df['评分等级'] == '⚠️需优化'])
        except Exception as e:
            print(f"❌ 评分模型指标更新失败: {e}")
            return "0.0", "0", "0"
        
        return (
            f"{avg_score:.1f}分",
            f"{excellent_count} ({excellent_count/len(df)*100:.1f}%)",
            f"{poor_count} ({poor_count/len(df)*100:.1f}%)"
        )
    
    
    # ==================== 回调4: 科学方法象限分布饼图 ====================
    @app.callback(
        Output('scientific-quadrant-pie', 'children'),
        Input('tab7-scientific-data', 'data')
    )
    def update_scientific_pie(scientific_data):
        """科学方法象限分布饼图"""
        if not scientific_data:
            return dbc.Alert("暂无数据", color="warning")
        
        df = pd.DataFrame(scientific_data)
        quadrant_counts = df['象限名称'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=quadrant_counts.index,
            values=quadrant_counts.values,
            hole=0.3,
            textinfo='label+percent',
            marker=dict(colors=['#28a745', '#ffc107', '#17a2b8', '#6c757d', 
                               '#dc3545', '#fd7e14', '#e83e8c', '#6610f2'])
        )])
        fig.update_layout(
            title='八象限分布',
            height=300,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    
    # ==================== 回调5: 科学方法置信度分布图 ====================
    @app.callback(
        Output('scientific-confidence-bar', 'children'),
        Input('tab7-scientific-data', 'data')
    )
    def update_scientific_confidence(scientific_data):
        """科学方法置信度分布图"""
        if not scientific_data:
            return dbc.Alert("暂无数据", color="warning")
        
        df = pd.DataFrame(scientific_data)
        conf_counts = df['置信度标签'].value_counts()
        
        colors = {'高置信': '#28a745', '中置信': '#ffc107', '低置信': '#dc3545'}
        
        fig = go.Figure(data=[go.Bar(
            x=conf_counts.index,
            y=conf_counts.values,
            marker_color=[colors.get(x, '#6c757d') for x in conf_counts.index],
            text=conf_counts.values,
            textposition='auto'
        )])
        fig.update_layout(
            title='置信度分布',
            height=250,
            xaxis_title='置信度',
            yaxis_title='商品数',
            margin=dict(l=20, r=20, t=40, b=40)
        )
        
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    
    # ==================== 回调6: 评分模型分布柱状图 ====================
    @app.callback(
        Output('scoring-distribution-bar', 'children'),
        Input('tab7-scoring-data', 'data')
    )
    def update_scoring_distribution(scoring_data):
        """评分模型评分分布柱状图"""
        if not scoring_data:
            return dbc.Alert("暂无数据", color="warning")
        
        df = pd.DataFrame(scoring_data)
        grade_counts = df['评分等级'].value_counts()
        
        colors = {'⭐优秀': '#28a745', '✅表现良好': '#17a2b8', 
                 '📊待改进': '#ffc107', '⚠️需优化': '#dc3545'}
        
        fig = go.Figure(data=[go.Bar(
            x=grade_counts.index,
            y=grade_counts.values,
            marker_color=[colors.get(x, '#6c757d') for x in grade_counts.index],
            text=grade_counts.values,
            textposition='auto'
        )])
        fig.update_layout(
            title='评分等级分布',
            height=250,
            xaxis_title='评分等级',
            yaxis_title='商品数',
            margin=dict(l=20, r=20, t=40, b=40)
        )
        
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    
    # ==================== 回调7: 评分模型TOP/底部商品 ====================
    @app.callback(
        Output('scoring-top-bottom-products', 'children'),
        Input('tab7-scoring-data', 'data')
    )
    def update_top_bottom_products(scoring_data):
        """评分模型TOP10和底部10商品列表"""
        if not scoring_data:
            return dbc.Alert("暂无数据", color="warning")
        
        df = pd.DataFrame(scoring_data)
        df_sorted = df.sort_values('综合得分', ascending=False)
        
        top10 = df_sorted.head(10)
        bottom10 = df_sorted.tail(10)
        
        return html.Div([
            html.H6("⭐ TOP10高分商品", className="text-success mb-2"),
            html.Ul([
                html.Li(f"{row['商品名称'][:20]}... ({row['综合得分']:.1f}分)", 
                       className="small")
                for _, row in top10.iterrows()
            ], className="mb-3"),
            
            html.H6("⚠️ 底部10低分商品", className="text-danger mb-2"),
            html.Ul([
                html.Li(f"{row['商品名称'][:20]}... ({row['综合得分']:.1f}分)", 
                       className="small")
                for _, row in bottom10.iterrows()
            ])
        ])
    
    
    # ==================== 回调8: 品类阈值信息(筛选时) ====================
    @app.callback(
        Output('scientific-category-threshold-info', 'children'),
        [Input('tab7-category-filter', 'value'),
         Input('tab7-scientific-data', 'data')]
    )
    def update_category_threshold_info(category, scientific_data):
        """显示当前品类的动态阈值信息"""
        if category == 'ALL' or not scientific_data:
            return None
        
        df = pd.DataFrame(scientific_data)
        
        # 获取该品类的阈值(从科学方法分析结果推断)
        if len(df) > 0 and '一级分类名' in df.columns:
            category_data = df[df['一级分类名'] == category]
            if len(category_data) > 0 and '营销占比' in category_data.columns and '毛利率' in category_data.columns:
                # 计算该品类的中位数阈值
                marketing_median = category_data['营销占比'].median()
                margin_median = category_data['毛利率'].median()
                
                return dbc.Alert([
                    html.Strong(f"📊 {category}品类动态阈值:"),
                    html.Br(),
                    f"营销占比中位数: {marketing_median*100:.1f}%",
                    html.Br(),
                    f"毛利率中位数: {margin_median*100:.1f}%"
                ], color="info", className="mt-2 small")
        
        return None
    
    
    # ==================== 回调9: 品类平均分信息(筛选时) ====================
    @app.callback(
        Output('scoring-category-avg-info', 'children'),
        [Input('tab7-category-filter', 'value'),
         Input('tab7-scoring-data', 'data')]
    )
    def update_category_avg_info(category, scoring_data):
        """显示当前品类的平均分信息"""
        if category == 'ALL' or not scoring_data:
            return None
        
        df = pd.DataFrame(scoring_data)
        
        if len(df) > 0 and '一级分类名' in df.columns:
            category_data = df[df['一级分类名'] == category]
            required_cols = ['综合得分', '营销效率分', '盈利能力分', '动销健康分']
            if len(category_data) > 0 and all(col in category_data.columns for col in required_cols):
                avg_score = category_data['综合得分'].mean()
                marketing_avg = category_data['营销效率分'].mean()
                profit_avg = category_data['盈利能力分'].mean()
                turnover_avg = category_data['动销健康分'].mean()
                
                return dbc.Alert([
                    html.Strong(f"📊 {category}品类平均得分:"),
                    html.Br(),
                    f"综合得分: {avg_score:.1f}分",
                    html.Br(),
                    f"营销效率: {marketing_avg:.1f}分 | 盈利能力: {profit_avg:.1f}分 | 动销健康: {turnover_avg:.1f}分"
                ], color="info", className="mt-2 small")
        
        return None
    
    
    # ==================== 回调10: TOP20问题商品一致性表格 ====================
    @app.callback(
        [Output('consistency-info', 'children'),
         Output('top20-problem-products-table', 'children')],
        [Input('tab7-scientific-data', 'data'),
         Input('tab7-scoring-data', 'data')]
    )
    def update_top20_problems(scientific_data, scoring_data):
        """显示两种方法都标记为问题的TOP20商品"""
        if not scientific_data or not scoring_data:
            return "数据加载中...", dbc.Alert("暂无数据", color="warning")
        
        try:
            sci_df = pd.DataFrame(scientific_data)
            score_df = pd.DataFrame(scoring_data)
            
            # 检查必需字段
            if '象限编号' not in sci_df.columns or '综合得分' not in score_df.columns:
                return "字段缺失", dbc.Alert("数据字段不完整,无法分析", color="danger")
            
            # 定义问题商品
            # 科学方法: 淘汰区、双输商品
            sci_problems = sci_df[sci_df['象限编号'].isin(['Q8', 'Q4'])]
            
            # 评分模型: 需优化(得分<40)
            score_problems = score_df[score_df['综合得分'] < 40]
        except Exception as e:
            print(f"❌ TOP20问题商品分析失败: {e}")
            return f"分析失败: {str(e)}", dbc.Alert(f"分析失败: {str(e)}", color="danger")
        
        # 找到两种方法都标记为问题的商品
        common_problems = pd.merge(
            sci_problems[['商品名称', '象限名称', '置信度标签']],
            score_problems[['商品名称', '综合得分', '评分等级']],
            on='商品名称'
        )
        
        # 一致性统计
        total_products = len(sci_df)
        sci_problem_count = len(sci_problems)
        score_problem_count = len(score_problems)
        common_count = len(common_problems)
        
        consistency_rate = (common_count / min(sci_problem_count, score_problem_count) * 100) if min(sci_problem_count, score_problem_count) > 0 else 0
        
        consistency_text = (
            f"科学方法标记问题商品: {sci_problem_count}个 | "
            f"评分模型标记问题商品: {score_problem_count}个 | "
            f"两种方法都标记: {common_count}个 ({consistency_rate:.1f}%一致)"
        )
        
        # 生成表格
        if len(common_problems) == 0:
            table = dbc.Alert("未发现两种方法都标记为问题的商品", color="success")
        else:
            # 按综合得分排序,取TOP20
            top20 = common_problems.sort_values('综合得分').head(20)
            
            # 格式化数值
            top20_display = top20.copy()
            top20_display['综合得分'] = top20_display['综合得分'].apply(lambda x: f"{x:.1f}")
            
            table = dbc.Table.from_dataframe(
                top20_display,
                striped=True,
                bordered=True,
                hover=True,
                size='sm',
                className='table-responsive'
            )
        
        return consistency_text, table
    
    
    # ==================== 回调11: 差异对比弹窗 ====================
    @app.callback(
        [Output('difference-comparison-modal', 'is_open'),
         Output('difference-comparison-content', 'children')],
        [Input('btn-show-difference', 'n_clicks'),
         Input('close-difference-modal', 'n_clicks')],
        [State('tab7-scientific-data', 'data'),
         State('tab7-scoring-data', 'data')],
        prevent_initial_call=True
    )
    def toggle_difference_modal(open_clicks, close_clicks, scientific_data, scoring_data):
        """切换差异对比弹窗"""
        from dash import callback_context
        
        if not callback_context.triggered:
            raise PreventUpdate
        
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'close-difference-modal':
            return False, None
        
        if button_id == 'btn-show-difference':
            if not scientific_data or not scoring_data:
                return True, dbc.Alert("数据加载中...", color="warning")
            
            try:
                sci_df = pd.DataFrame(scientific_data)
                score_df = pd.DataFrame(scoring_data)
                
                # 检查必需字段
                if '象限名称' not in sci_df.columns or '商品名称' not in sci_df.columns:
                    return True, dbc.Alert("科学方法数据字段不完整", color="danger")
                if '象限名称' not in score_df.columns or '商品名称' not in score_df.columns:
                    return True, dbc.Alert("评分模型数据字段不完整", color="danger")
                
                # 合并数据对比
                comparison = pd.merge(
                    sci_df[['商品名称', '象限名称', '置信度标签']],
                    score_df[['商品名称', '象限名称', '综合得分', '评分等级']],
                    on='商品名称',
                    suffixes=('_科学', '_评分')
                )
            except Exception as e:
                print(f"❌ 差异对比失败: {e}")
                return True, dbc.Alert(f"差异对比失败: {str(e)}", color="danger")
            
            # 分类一致性统计
            same_count = (comparison['象限名称_科学'] == comparison['象限名称_评分']).sum()
            diff_count = len(comparison) - same_count
            
            # 典型差异案例
            different_cases = comparison[comparison['象限名称_科学'] != comparison['象限名称_评分']].head(10)
            
            content = html.Div([
                html.H5("📊 分类一致性统计"),
                html.P(f"总商品数: {len(comparison)}"),
                html.P(f"分类一致: {same_count} ({same_count/len(comparison)*100:.1f}%)"),
                html.P(f"分类不同: {diff_count} ({diff_count/len(comparison)*100:.1f}%)"),
                
                html.Hr(),
                
                html.H5("🔍 典型差异案例 (前10个)"),
                dbc.Table.from_dataframe(
                    different_cases[['商品名称', '象限名称_科学', '置信度标签', '象限名称_评分', '综合得分', '评分等级']],
                    striped=True,
                    bordered=True,
                    hover=True,
                    size='sm'
                ) if len(different_cases) > 0 else dbc.Alert("所有商品分类完全一致!", color="success")
            ])
            
            return True, content
        
        raise PreventUpdate
    
    
    # ==================== 回调12: 导出科学分析报告 ====================
    @app.callback(
        Output('download-scientific-data', 'data'),
        Input('export-scientific-btn', 'n_clicks'),
        State('tab7-scientific-data', 'data'),
        prevent_initial_call=True
    )
    def export_scientific_report(n_clicks, scientific_data):
        """导出科学分析报告Excel"""
        if not scientific_data:
            raise PreventUpdate
        
        from datetime import datetime
        
        df = pd.DataFrame(scientific_data)
        
        # 创建Excel
        filename = f"科学分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return dcc.send_data_frame(df.to_excel, filename, index=False, sheet_name='科学方法分析')
    
    
    # ==================== 回调13: 导出评分排名报告 ====================
    @app.callback(
        Output('download-scoring-data', 'data'),
        Input('export-scoring-btn', 'n_clicks'),
        State('tab7-scoring-data', 'data'),
        prevent_initial_call=True
    )
    def export_scoring_report(n_clicks, scoring_data):
        """导出评分排名报告Excel"""
        if not scoring_data:
            raise PreventUpdate
        
        from datetime import datetime
        
        df = pd.DataFrame(scoring_data)
        df_sorted = df.sort_values('综合得分', ascending=False)
        
        filename = f"评分排名报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 创建多Sheet Excel
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_sorted.to_excel(writer, sheet_name='全部商品', index=False)
            df_sorted.head(50).to_excel(writer, sheet_name='TOP50高分商品', index=False)
            df_sorted.tail(50).to_excel(writer, sheet_name='底部50低分商品', index=False)
            
            # 评分明细(三个维度拆分)
            detail_df = df_sorted[['商品名称', '综合得分', '营销效率分', '盈利能力分', '动销健康分', '评分等级']]
            detail_df.to_excel(writer, sheet_name='三维得分明细', index=False)
        
        output.seek(0)
        
        return dcc.send_bytes(output.getvalue(), filename)
