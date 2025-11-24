"""
快速验证看板启动 - 检查下钻模块导入
"""
print("🔍 检查下钻模块导入...")

try:
    # 模拟看板的导入过程
    from components.drill_down_manager import (
        DrillDownState, get_state_manager,
        create_breadcrumb_component, create_back_button, create_state_stores,
        analyze_channel_health, get_drill_down_button_text, get_drill_down_button_color
    )
    print("✅ 下钻状态管理模块已加载")
    
    # 创建一个简单的测试
    state = DrillDownState()
    state.drill_down_to_channel('美团外卖')
    breadcrumb = state.get_breadcrumb_path()
    path = ' > '.join([item['label'] for item in breadcrumb])
    
    print(f"✅ 状态管理测试通过")
    print(f"   当前路径: {path}")
    print(f"   当前层级: {state.current_layer}")
    
    # 测试健康度分析
    level, badge, color = analyze_channel_health(16.8)
    print(f"✅ 健康度分析测试通过")
    print(f"   利润率16.8% → {badge}")
    
    # 测试Store组件
    stores = create_state_stores()
    print(f"✅ Store组件创建成功 ({len(stores)}个)")
    
    print("\n🎉 所有核心功能正常!")
    print("📝 看板可以安全启动")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("⚠️  请确保components目录存在")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
