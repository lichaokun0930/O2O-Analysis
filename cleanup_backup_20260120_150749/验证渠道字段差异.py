# -*- coding: utf-8 -*-
"""
验证渠道字段差异

对比：
- Dash 版本：使用 '渠道' 字段（如 美团共橙、饿了么）
- React 版本：使用 order_number 前缀（SG、ELE、JD）

以惠宜选-泰州泰兴店为例
"""

import pandas as pd
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order

def main():
    store_name = "惠宜选-泰州泰兴店"
    
    session = SessionLocal()
    try:
        # 查询该门店的所有订单
        orders = session.query(Order).filter(Order.store_name == store_name).all()
        
        # 统计渠道字段和订单编号前缀的对应关系
        channel_prefix_map = {}
        
        for order in orders:
            channel = order.channel
            order_number = order.order_number or ''
            
            # 获取前缀
            if order_number.startswith('SG'):
                prefix = 'SG'
            elif order_number.startswith('ELE'):
                prefix = 'ELE'
            elif order_number.startswith('JD'):
                prefix = 'JD'
            else:
                prefix = 'OTHER'
            
            key = (prefix, channel)
            if key not in channel_prefix_map:
                channel_prefix_map[key] = 0
            channel_prefix_map[key] += 1
        
        print("="*80)
        print(f"渠道字段与订单编号前缀对应关系 - {store_name}")
        print("="*80)
        
        # 按前缀分组显示
        prefixes = ['SG', 'ELE', 'JD', 'OTHER']
        for prefix in prefixes:
            print(f"\n📊 {prefix} 前缀:")
            print("-"*60)
            
            prefix_data = [(k, v) for k, v in channel_prefix_map.items() if k[0] == prefix]
            prefix_data.sort(key=lambda x: -x[1])
            
            total = sum(v for _, v in prefix_data)
            for (p, channel), count in prefix_data:
                print(f"  {channel}: {count} 条记录 ({count/total*100:.1f}%)")
            
            print(f"  总计: {total} 条记录")
        
        print("\n" + "="*80)
        print("📋 结论:")
        print("  - Dash 版本按 '渠道' 字段分组（如 美团共橙、饿了么）")
        print("  - React 版本按 order_number 前缀分组（SG、ELE、JD）")
        print("  - 如果一个前缀对应多个渠道，数据会有差异")
        print("="*80)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
