"""
涨价降价计算示例演示

展示不同场景下的涨价降价判定逻辑
"""

def analyze_price_change(product_name, before_price, current_price, before_qty, current_qty):
    """
    分析商品价格和销量变化
    
    参数:
    - product_name: 商品名称
    - before_price: 之前单价
    - current_price: 当前单价
    - before_qty: 之前销量
    - current_qty: 当前销量
    """
    # 计算变化
    price_change = current_price - before_price
    price_change_rate = ((current_price - before_price) / before_price * 100) if before_price > 0 else 0
    qty_change = current_qty - before_qty
    
    # 判定原因(与代码逻辑一致)
    if current_qty == 0 and before_qty > 0:
        reason = "🔴售罄"
    elif current_qty == 0:
        reason = "⚪新品"
    elif price_change_rate > 5:  # 涨价阈值: 5%
        if qty_change < 0:
            reason = "💰涨价导致销量降"
        else:
            reason = "💰涨价(销量增)"
    elif price_change_rate < -5:  # 降价阈值: -5%
        if qty_change < 0:
            reason = "💸降价仍降量"
        else:
            reason = "💸降价促销成功"
    elif qty_change < -before_qty * 0.3:  # 销量下降>30%
        reason = "📉销量大幅下滑"
    elif qty_change < 0:
        reason = "📉销量小幅下滑"
    else:
        reason = "✅正常"
    
    # 输出结果
    print(f"\n{'='*80}")
    print(f"商品: {product_name}")
    print(f"{'='*80}")
    print(f"  之前单价: ¥{before_price:.2f}")
    print(f"  当前单价: ¥{current_price:.2f}")
    print(f"  单价变化: ¥{price_change:+.2f}")
    print(f"  单价变化率: {price_change_rate:+.1f}%")
    print(f"  ")
    print(f"  之前销量: {before_qty}件")
    print(f"  当前销量: {current_qty}件")
    print(f"  销量变化: {qty_change:+d}件")
    if before_qty > 0:
        qty_change_rate = (qty_change / before_qty * 100)
        print(f"  销量变化率: {qty_change_rate:+.1f}%")
    print(f"  ")
    print(f"  【判定结果】: {reason}")
    print(f"  ")
    
    # 判定逻辑说明
    print(f"  【判定逻辑】:")
    if current_qty == 0 and before_qty > 0:
        print(f"    ✓ 当前销量=0 且 之前销量>0 → 售罄")
    elif current_qty == 0:
        print(f"    ✓ 当前销量=0 且 之前销量=0 → 新品")
    elif price_change_rate > 5:
        print(f"    ✓ 单价变化率{price_change_rate:+.1f}% > 5% → 涨价")
        if qty_change < 0:
            print(f"    ✓ 销量变化{qty_change}件 < 0 → 销量下降")
        else:
            print(f"    ✓ 销量变化{qty_change}件 > 0 → 销量上升")
    elif price_change_rate < -5:
        print(f"    ✓ 单价变化率{price_change_rate:+.1f}% < -5% → 降价")
        if qty_change < 0:
            print(f"    ✓ 销量变化{qty_change}件 < 0 → 销量仍下降")
        else:
            print(f"    ✓ 销量变化{qty_change}件 > 0 → 销量上升(促销成功)")
    elif qty_change < -before_qty * 0.3:
        print(f"    ✓ 价格稳定(-5%~5%范围内)")
        print(f"    ✓ 销量变化{qty_change}件 < -{before_qty}*0.3 → 销量下降>30%")
    elif qty_change < 0:
        print(f"    ✓ 价格稳定(-5%~5%范围内)")
        print(f"    ✓ 销量变化{qty_change}件 < 0 且 降幅<30% → 销量小幅下滑")
    else:
        print(f"    ✓ 价格稳定,销量正常")
    
    print(f"{'='*80}\n")
    
    return reason


if __name__ == "__main__":
    print("\n" + "="*80)
    print("涨价降价计算逻辑演示")
    print("阈值设置: 涨降价阈值=±5%, 销量大幅下滑阈值=30%")
    print("="*80)
    
    # 示例1: 涨价导致销量降
    analyze_price_change(
        product_name="可口可乐",
        before_price=3.5,
        current_price=4.0,
        before_qty=100,
        current_qty=80
    )
    
    # 示例2: 降价仍降量
    analyze_price_change(
        product_name="洗发水",
        before_price=15.0,
        current_price=12.0,
        before_qty=50,
        current_qty=40
    )
    
    # 示例3: 降价促销成功
    analyze_price_change(
        product_name="薯片",
        before_price=5.0,
        current_price=4.0,
        before_qty=80,
        current_qty=120
    )
    
    # 示例4: 销量大幅下滑(价格稳定)
    analyze_price_change(
        product_name="红牛",
        before_price=6.5,
        current_price=6.5,
        before_qty=100,
        current_qty=60
    )
    
    # 示例5: 价格微调(不算涨价)
    analyze_price_change(
        product_name="矿泉水",
        before_price=2.0,
        current_price=2.08,
        before_qty=200,
        current_qty=190
    )
    
    # 示例6: 售罄
    analyze_price_change(
        product_name="巧克力",
        before_price=8.0,
        current_price=8.0,
        before_qty=60,
        current_qty=0
    )
    
    # 示例7: 涨价但销量增加
    analyze_price_change(
        product_name="网红零食",
        before_price=10.0,
        current_price=12.0,
        before_qty=50,
        current_qty=80
    )
    
    print("\n" + "="*80)
    print("总结")
    print("="*80)
    print("涨价判定: 单价变化率 > 5%")
    print("降价判定: 单价变化率 < -5%")
    print("价格稳定: -5% ≤ 单价变化率 ≤ 5%")
    print("销量大幅下滑: 销量下降 > 30%")
    print("="*80)
    print()
    
    # 阈值敏感性分析
    print("="*80)
    print("阈值敏感性分析 - 同一商品在不同阈值下的判定")
    print("="*80)
    print()
    print("商品: 测试商品 | 之前¥10.0 → 当前¥10.4 (变化率+4%)")
    print()
    print("阈值±3%: 判定为【涨价】(4% > 3%)")
    print("阈值±5%: 判定为【价格稳定】(4% < 5%) ⭐当前使用")
    print("阈值±10%: 判定为【价格稳定】(4% < 10%)")
    print()
    print("建议: 根据业务特点选择合适的阈值")
    print("  - 高频快消品: ±3% (价格敏感)")
    print("  - 标准零售: ±5% (默认值)")
    print("  - 高价商品: ±10% (价格稳定)")
    print("="*80)
