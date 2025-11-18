# -*- coding: utf-8 -*-
"""替换main函数的脚本"""

# 读取文件
with open('智能门店经营看板_可视化.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 新的main函数
new_main = '''def main():
    """主函数 - 简化的标签页界面"""
    
    # 页面标题
    st.markdown('<h1 class="main-header">🏪 智能门店经营看板</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 初始化系统组件
    dashboard = load_dashboard_system()
    data_processor = load_data_processor()
    
    # 创建4个功能标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 订单数据分析",
        "💰 比价分析", 
        "🎯 AI场景营销",
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
        st.header("🎯 AI场景营销分析")
        
        # 检查是否已上传数据
        if "uploaded_order_data" not in st.session_state:
            st.warning("⚠️ 请先在『订单数据分析』标签页上传数据")
            st.info("💡 AI场景营销需要基于订单数据进行智能分析")
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
            if st.button("🚀 开始AI智能分析", type="primary", use_container_width=True):
                current_data = st.session_state["uploaded_order_data"]
                
                with st.spinner("正在进行AI智能分析..."):
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
    
    # === Tab 4: 高级功能 ===
    with tab4:
        st.header("⚙️ 高级功能")
        
        # AI学习系统
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
        
        st.markdown("---")
        
        # 系统信息
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
        
        st.markdown("---")
        
        # 演示模式
        st.subheader("🎮 演示模式")
        st.info("演示模式使用内置示例数据，可用于界面演示和功能测试")
        
        if st.button("🎪 启动示例数据演示", type="secondary"):
            sample_data = load_sample_data()
            st.session_state["uploaded_order_data"] = sample_data
            st.success("✅ 已加载示例数据，请前往其他标签页体验功能")
            st.rerun()

'''

# 替换main函数
main_start = content.find('def main():')
next_func = content.find('def display_analysis_results(', main_start)

if main_start > 0 and next_func > main_start:
    new_content = content[:main_start] + new_main + content[next_func:]
    
    # 写入文件
    with open('智能门店经营看板_可视化.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('✅ main函数已成功替换')
    print(f'📊 原main函数大小: {next_func - main_start} 字符')
    print(f'📊 新main函数大小: {len(new_main)} 字符')
else:
    print('❌ 未找到函数位置')
