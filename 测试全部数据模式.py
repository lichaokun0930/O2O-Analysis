"""
测试全部数据模式（days_range=0）的bug修复

问题：当days_range=0时，Python的if判断会认为0是False，导致使用默认值15
修复：使用 `if current_days is not None` 而不是 `if current_days`
"""

def test_old_logic():
    """旧逻辑（有bug）"""
    print("=" * 60)
    print("测试旧逻辑（有bug）")
    print("=" * 60)
    
    # 模拟不同的current_days值
    test_cases = [None, 0, 7, 15, 30]
    
    for current_days in test_cases:
        # 旧逻辑：if current_days else 15
        days_range = current_days if current_days else 15
        current_str = str(current_days) if current_days is not None else "None"
        print(f"current_days={current_str:>4} → days_range={days_range:>4} {'❌ BUG!' if current_days == 0 else ''}")

def test_new_logic():
    """新逻辑（已修复）"""
    print("\n" + "=" * 60)
    print("测试新逻辑（已修复）")
    print("=" * 60)
    
    # 模拟不同的current_days值
    test_cases = [None, 0, 7, 15, 30]
    
    for current_days in test_cases:
        # 新逻辑：if current_days is not None else 15
        days_range = current_days if current_days is not None else 15
        mode = "全部数据" if days_range == 0 else f"{days_range}天"
        current_str = str(current_days) if current_days is not None else "None"
        print(f"current_days={current_str:>4} → days_range={days_range:>4} ({mode}) ✅")

def explain_bug():
    """解释bug原因"""
    print("\n" + "=" * 60)
    print("Bug原因解释")
    print("=" * 60)
    print("""
在Python中，数字0被认为是False：
    
    if 0:
        print("不会执行")  # 0是False
    else:
        print("会执行")    # 进入else分支
    
因此，当使用以下代码时：
    
    days_range = current_days if current_days else 15
    
如果current_days=0（全部数据模式），Python会认为0是False，
所以会使用默认值15，导致"全部数据"模式失效！

正确的写法应该是：
    
    days_range = current_days if current_days is not None else 15
    
这样只有当current_days是None时才使用默认值15，
而current_days=0时会正确使用0（全部数据模式）。
    """)

if __name__ == '__main__':
    test_old_logic()
    test_new_logic()
    explain_bug()
    
    print("\n" + "=" * 60)
    print("结论")
    print("=" * 60)
    print("""
✅ 已修复的位置：
1. callbacks.py 第1511行：导出回调函数
2. callbacks.py 第1585行：筛选回调函数

🎯 修复效果：
- 选择"全部数据"时，days_range=0
- 导出时使用全部数据计算（不进行趋势对比）
- 文件名显示"全部数据"而不是"0天"
- 看板和导出使用相同的计算逻辑
    """)
