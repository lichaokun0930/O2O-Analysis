"""
测试返回按钮需要点击2次的问题
"""
from components.drill_down_manager import DrillDownState

print("="*60)
print("模拟用户操作流程")
print("="*60)

# 1. 初始状态
print("\n1️⃣ 初始状态: overview")
state = DrillDownState()
print(f"   current_layer: {state.current_layer}")
print(f"   history: {state.navigation_history}")

# 2. 点击"美团闪购"下钻按钮
print("\n2️⃣ 点击下钻按钮: overview → channel(美团闪购)")
new_state_dict = state.drill_down_to_channel('美团闪购')
print(f"   返回的state:")
print(f"     current_layer: {new_state_dict['current_layer']}")
print(f"     current_channel: {new_state_dict['current_channel']}")
print(f"     history: {new_state_dict['navigation_history']}")

# 3. 模拟回调函数: 创建新的DrillDownState并加载状态
print("\n3️⃣ 【回调函数】update_drill_down_container 被触发")
print("   接收到Store传来的状态:")
received_layer = new_state_dict['current_layer']
received_channel = new_state_dict['current_channel']
received_history = new_state_dict['navigation_history']
print(f"     current_layer: {received_layer}")
print(f"     current_channel: {received_channel}")
print(f"     history: {received_history}")

# 4. 模拟第1次点击返回按钮
print("\n4️⃣ 【第1次点击返回】go_back_callback 被触发")
print("   接收到Store传来的状态:")
print(f"     current_layer: {received_layer}")
print(f"     current_channel: {received_channel}")
print(f"     history: {received_history}")

# 创建新的state实例并加载
state2 = DrillDownState()
state2.current_layer = received_layer
state2.current_channel = received_channel
state2.navigation_history = received_history.copy() if received_history else []

print(f"\n   state2加载后:")
print(f"     current_layer: {state2.current_layer}")
print(f"     history: {state2.navigation_history}")

# 执行返回
new_state_dict2 = state2.go_back()
print(f"\n   返回后的state:")
print(f"     current_layer: {new_state_dict2['current_layer']}")
print(f"     current_channel: {new_state_dict2['current_channel']}")
print(f"     history: {new_state_dict2['navigation_history']}")

# 5. 检查是否回到overview
if new_state_dict2['current_layer'] == 'overview':
    print("\n✅ 第1次点击成功返回到overview!")
else:
    print(f"\n❌ 第1次点击失败! 当前层级: {new_state_dict2['current_layer']}")
    print("   需要再点击一次返回...")
    
    # 模拟第2次点击
    print("\n5️⃣ 【第2次点击返回】go_back_callback 被触发")
    state3 = DrillDownState()
    state3.current_layer = new_state_dict2['current_layer']
    state3.current_channel = new_state_dict2['current_channel']
    state3.navigation_history = new_state_dict2['navigation_history'].copy()
    
    new_state_dict3 = state3.go_back()
    print(f"   返回后的state:")
    print(f"     current_layer: {new_state_dict3['current_layer']}")
    print(f"     history: {new_state_dict3['navigation_history']}")
    
    if new_state_dict3['current_layer'] == 'overview':
        print("\n✅ 第2次点击成功返回到overview!")

print("\n" + "="*60)
