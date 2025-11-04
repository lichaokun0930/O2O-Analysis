# 简化版main函数 - 用于替换原有的复杂界面

def main_simplified():
    """主函数 - 简化重构版"""
    
    # 页面标题
    st.markdown('<h1 class="main-header">🏪 智能门店经营看板</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 加载系统组件
    dashboard = load_dashboard_system()
    
    # 主界面：使用标签页组织不同功能模块
    main_tabs = st.tabs([
        "📊 订单数据分析", 
        "💹 比价分析", 
        "🤖 AI场景营销",
        "🔧 高级功能"
    ])
    
    # Tab 1: 订单数据分析（主要功能）
    with main_tabs[0]:
        st.subheader("📊 订单数据分析")
        render_order_data_uploader()
    
    # Tab 2: 比价分析
    with main_tabs[1]:
        st.subheader("💹 比价分析")
        render_unified_price_comparison_module()
    
    # Tab 3: AI场景营销（需要先上传数据）
    with main_tabs[2]:
        st.subheader("🤖 AI场景营销智能决策")
        
        if 'current_data' in st.session_state and st.session_state['current_data']:
            # 如果已经上传了数据，显示场景营销模块
            current_data = st.session_state['current_data']
            
            # 渲染场景营销模块
            st.info("💡 基于已上传的订单数据进行AI场景识别与营销决策")
            
            # 这里可以调用场景营销相关的渲染函数
            st.success(f"✅ 当前数据：{len(current_data.get('raw_data', []))} 条订单")
            
            # 场景营销的具体功能可以在这里展开
            st.write("**场景营销功能模块**")
            
        else:
            st.warning("⚠️ 请先在"订单数据分析"标签页上传数据")
            if st.button("👉 前往上传数据"):
                st.rerun()
    
    # Tab 4: 高级功能（AI学习系统等）
    with main_tabs[3]:
        st.subheader("🔧 高级功能与系统设置")
        
        # AI 学习系统
        with st.expander("🧠 AI学习系统", expanded=False):
            learning_status = dashboard.get_learning_status()
            if learning_status.get("enabled"):
                st.success("✅ AI学习系统已启用")
                learning_stats = learning_status.get("learning_statistics", {})
                if learning_stats:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("总学习次数", learning_stats.get('total_learning_sessions', 0))
                    with col2:
                        st.metric("在线更新", learning_stats.get('online_updates', 0))
                    with col3:
                        st.metric("批量更新", learning_stats.get('batch_updates', 0))
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("🔄 手动模型训练", help="使用历史数据手动训练模型"):
                        with st.spinner("正在训练模型..."):
                            sample_data = load_sample_data()
                            training_result = dashboard.manual_model_training([sample_data])
                            if training_result.get("success"):
                                st.success("🎉 模型训练完成")
                            else:
                                st.error(f"❌ 训练失败: {training_result.get('error', '未知错误')}")
                with col_b:
                    if st.button("📄 导出学习报告"):
                        report_path = dashboard.export_learning_insights()
                        if report_path:
                            st.success("✅ 报告已导出")
                        else:
                            st.error("❌ 导出失败")
            else:
                st.info("AI学习系统暂未启用")
        
        # 系统信息
        with st.expander("📋 系统信息", expanded=False):
            real_data, load_messages = load_real_business_data()
            
            if real_data:
                st.success(f"📊 检测到真实数据：{real_data['data_source']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("数据时段", real_data['data_period'])
                with col2:
                    st.metric("订单数", f"{real_data['total_orders']:,}")
                with col3:
                    st.metric("商品种类", f"{real_data['total_products']:,}")
            else:
                st.warning("未检测到真实数据文件")
                if load_messages:
                    for msg in load_messages:
                        st.info(msg)
        
        # 示例数据演示（仅供测试）
        with st.expander("🎭 示例数据演示模式", expanded=False):
            st.warning("⚠️ 此模式仅用于功能演示，不适用于真实业务分析")
            
            if st.button("🚀 启动示例数据分析"):
                sample_data = load_sample_data()
                with st.spinner("正在进行智能分析..."):
                    analysis_result = dashboard.comprehensive_analysis(
                        sample_data,
                        sample_data.get("competitor_data"),
                    )
                    st.session_state["analysis_result"] = analysis_result
                    st.session_state["current_data"] = sample_data
                    st.session_state["forecast_days"] = 30
                st.success("✅ 示例分析完成，查看下方结果")
        
        # 如果有分析结果，显示它
        if "analysis_result" in st.session_state:
            st.markdown("---")
            st.subheader("📈 分析结果")
            
            col_reset, col_space = st.columns([1, 4])
            with col_reset:
                if st.button("🔄 清除分析结果"):
                    if "analysis_result" in st.session_state:
                        del st.session_state["analysis_result"]
                    if "current_data" in st.session_state:
                        del st.session_state["current_data"]
                    st.rerun()
            
            analysis_scope = ["销售分析", "策略建议", "预测分析"]
            display_analysis_results(
                st.session_state["analysis_result"], 
                analysis_scope, 
                dashboard
            )
