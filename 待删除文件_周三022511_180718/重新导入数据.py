#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新导入数据到数据库(保留耗材)
"""

import sys
import os

print("="*80)
print("🔄 重新导入数据流程")
print("="*80)

# Step 1: 清空现有数据
print("\n【Step 1: 清空现有订单数据】")
print("⚠️  这将删除数据库中的所有订单数据...")
confirm = input("确认继续? (输入 yes 继续): ")

if confirm.lower() != 'yes':
    print("❌ 操作已取消")
    sys.exit(0)

print("🗑️  正在清空数据...")

# 直接使用SQL清空
from database.connection import SessionLocal
from database.models import Order, Product

db = SessionLocal()
try:
    order_count = db.query(Order).count()
    product_count = db.query(Product).count()
    print(f"   当前订单数: {order_count:,}")
    print(f"   当前商品数: {product_count:,}")
    
    db.query(Order).delete()
    db.query(Product).delete()
    db.commit()
    print("✅ 清空完成")
except Exception as e:
    db.rollback()
    print(f"❌ 清空失败: {e}")
    sys.exit(1)
finally:
    db.close()

# Step 2: 重新导入
print("\n【Step 2: 重新导入数据(保留耗材)】")
print("📂 将从以下文件导入:")
print("   实际数据/2025-10-19 00_00_00至2025-11-17 23_59_59订单明细数据导出汇总.xlsx")
print("\n🔧 导入配置:")
print("   ✅ 保留耗材数据(购物袋等)")
print("   ✅ 使用订单数据处理器标准化")
print("   ✅ 批量导入(batch_size=1000)")

confirm2 = input("\n确认开始导入? (输入 yes 继续): ")
if confirm2.lower() != 'yes':
    print("❌ 操作已取消")
    sys.exit(0)

print("\n" + "="*80)
print("开始导入...")
print("="*80)

# 执行导入
os.system('python database/migrate_orders.py')

print("\n" + "="*80)
print("✅ 导入完成!")
print("="*80)
print("\n📊 下一步:")
print("   1. 运行验证脚本: python 完整自检.py")
print("   2. 重启看板: python 智能门店看板_Dash版.py")
print("   3. 检查美团共橙利润是否为 652.06元")
