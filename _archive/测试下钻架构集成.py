"""
测试下钻架构集成 - 验证状态管理和组件导入
"""
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("=" * 60)
print("🧪 下钻架构集成测试")
print("=" * 60)

# 测试1: 导入下钻管理模块
print("\n1️⃣ 测试导入下钻管理模块...")
try:
    from components.drill_down_manager import (
        DrillDownState, get_state_manager,
        create_breadcrumb_component, create_back_button, create_state_stores,
        analyze_channel_health, get_drill_down_button_text, get_drill_down_button_color
    )
    print("   ✅ 下钻管理模块导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 创建状态管理器实例
print("\n2️⃣ 测试创建状态管理器...")
try:
    state = DrillDownState()
    print(f"   ✅ 状态管理器创建成功")
    print(f"   - 初始层级: {state.current_layer}")
    print(f"   - 当前渠道: {state.current_channel}")
except Exception as e:
    print(f"   ❌ 创建失败: {e}")
    sys.exit(1)

# 测试3: 测试下钻操作
print("\n3️⃣ 测试下钻操作...")
try:
    # 总览 → 渠道
    state.drill_down_to_channel('美团外卖')
    assert state.current_layer == 'channel'
    assert state.current_channel == '美团外卖'
    print("   ✅ 总览→渠道下钻成功")
    
    # 渠道 → 商品清单
    state.drill_down_to_product_list('low-margin')
    assert state.current_layer == 'product_list'
    assert state.filter_type == 'low-margin'
    print("   ✅ 渠道→商品清单下钻成功")
    
    # 商品清单 → 单品洞察
    state.drill_down_to_product_insight('可口可乐')
    assert state.current_layer == 'product_insight'
    assert state.current_product == '可口可乐'
    print("   ✅ 商品→单品洞察下钻成功")
    
except Exception as e:
    print(f"   ❌ 下钻操作失败: {e}")
    sys.exit(1)

# 测试4: 测试返回操作
print("\n4️⃣ 测试返回操作...")
try:
    state.go_back()
    assert state.current_layer == 'product_list'
    print("   ✅ 返回上一层成功")
    
    state.go_back()
    assert state.current_layer == 'channel'
    print("   ✅ 再次返回成功")
    
except Exception as e:
    print(f"   ❌ 返回操作失败: {e}")
    sys.exit(1)

# 测试5: 测试面包屑生成
print("\n5️⃣ 测试面包屑导航...")
try:
    breadcrumb_path = state.get_breadcrumb_path()
    path_labels = [item['label'] for item in breadcrumb_path]
    print(f"   当前路径: {' > '.join(path_labels)}")
    assert len(breadcrumb_path) == 2  # 总览 > 美团外卖
    print("   ✅ 面包屑生成成功")
except Exception as e:
    print(f"   ❌ 面包屑生成失败: {e}")
    sys.exit(1)

# 测试6: 测试健康度分析
print("\n6️⃣ 测试健康度分析...")
try:
    test_cases = [
        (18.5, 'excellent', '⭐优秀'),
        (12.3, 'good', '✅良好'),
        (8.2, 'warning', '⚠️警戒')
    ]
    
    for rate, expected_level, expected_badge in test_cases:
        level, badge, color = analyze_channel_health(rate)
        assert level == expected_level, f"利润率{rate}%的健康度应为{expected_level}"
        assert badge == expected_badge, f"徽章应为{expected_badge}"
        print(f"   ✅ 利润率{rate}% → {badge} (等级:{level})")
        
except Exception as e:
    print(f"   ❌ 健康度分析失败: {e}")
    sys.exit(1)

# 测试7: 测试按钮文本生成
print("\n7️⃣ 测试按钮文本生成...")
try:
    assert get_drill_down_button_text('excellent') == '深入分析 →'
    assert get_drill_down_button_text('warning') == '诊断问题 🔍'
    assert get_drill_down_button_color('warning') == 'warning'
    print("   ✅ 按钮文本/颜色生成正确")
except Exception as e:
    print(f"   ❌ 按钮生成失败: {e}")
    sys.exit(1)

# 测试8: 测试Store组件创建
print("\n8️⃣ 测试Store组件创建...")
try:
    stores = create_state_stores()
    assert len(stores) == 6  # 应该有6个Store组件
    store_ids = [store.id for store in stores]
    expected_ids = [
        'drill-down-current-layer',
        'drill-down-current-channel',
        'drill-down-current-product',
        'drill-down-filter-type',
        'drill-down-navigation-history',
        'drill-down-full-state'
    ]
    for exp_id in expected_ids:
        assert exp_id in store_ids, f"缺少Store组件: {exp_id}"
    print("   ✅ Store组件创建成功")
    print(f"   - 组件数量: {len(stores)}")
    print(f"   - 组件ID: {', '.join(store_ids)}")
except Exception as e:
    print(f"   ❌ Store组件创建失败: {e}")
    sys.exit(1)

# 测试9: 测试面包屑UI组件
print("\n9️⃣ 测试面包屑UI组件...")
try:
    state_test = DrillDownState()
    state_test.drill_down_to_channel('饿了么')
    state_test.drill_down_to_product_list('discount')
    
    breadcrumb_path = state_test.get_breadcrumb_path()
    breadcrumb_ui = create_breadcrumb_component(breadcrumb_path)
    
    assert breadcrumb_ui is not None
    print("   ✅ 面包屑UI组件创建成功")
    print(f"   - 路径深度: {len(breadcrumb_path)}")
except Exception as e:
    print(f"   ❌ 面包屑UI组件创建失败: {e}")
    sys.exit(1)

# 测试10: 测试返回按钮UI组件
print("\n🔟 测试返回按钮UI组件...")
try:
    back_btn_enabled = create_back_button(disabled=False)
    back_btn_disabled = create_back_button(disabled=True)
    
    assert back_btn_enabled is not None
    assert back_btn_disabled is not None
    print("   ✅ 返回按钮UI组件创建成功")
except Exception as e:
    print(f"   ❌ 返回按钮UI组件创建失败: {e}")
    sys.exit(1)

# 最终总结
print("\n" + "=" * 60)
print("🎉 所有测试通过!")
print("=" * 60)
print("\n✅ 下钻架构已成功集成到主看板")
print("✅ 状态管理功能正常")
print("✅ UI组件工厂函数可用")
print("✅ 健康度分析逻辑正确")
print("\n📝 下一步:")
print("   1. 启动看板测试导入是否成功")
print("   2. 实现第一个下钻回调函数")
print("   3. 重构渠道卡片添加下钻按钮")
print("\n" + "=" * 60)
