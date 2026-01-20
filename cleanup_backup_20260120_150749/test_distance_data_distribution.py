# -*- coding: utf-8 -*-
"""
验证配送距离数据分布
检查数据库中的原始距离数据是否正确
"""
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func, distinct
import pandas as pd

def analyze_distance_distribution():
    """分析配送距离数据分布"""
    session = SessionLocal()
    try:
        print("=" * 80)
        print("📊 配送距离数据分布分析")
        print("=" * 80)
        
        # 1. 获取所有订单的配送距离（去重订单ID）
        print("\n1️⃣ 查询数据库中的配送距离数据...")
        
        # 按订单ID去重，获取每个订单的配送距离
        query = session.query(
            Order.order_id,
            Order.delivery_distance,
            Order.store_name
        ).distinct(Order.order_id)
        
        results = query.all()
        print(f"   总订单数（去重后）: {len(results)}")
        
        # 转换为DataFrame
        df = pd.DataFrame(results, columns=['订单ID', '配送距离', '门店名称'])
        
        # 2. 检查配送距离的基本统计
        print("\n2️⃣ 配送距离基本统计（原始值）:")
        print(f"   非空值数量: {df['配送距离'].notna().sum()}")
        print(f"   空值数量: {df['配送距离'].isna().sum()}")
        
        valid_distances = df[df['配送距离'].notna()]['配送距离']
        if len(valid_distances) > 0:
            print(f"   最小值: {valid_distances.min()}")
            print(f"   最大值: {valid_distances.max()}")
            print(f"   平均值: {valid_distances.mean():.2f}")
            print(f"   中位数: {valid_distances.median():.2f}")
        
        # 3. 判断单位（米 vs 公里）
        print("\n3️⃣ 单位判断:")
        if len(valid_distances) > 0:
            avg = valid_distances.mean()
            if avg > 100:
                print(f"   ⚠️ 平均值={avg:.2f}，判断为【米】，需要除以1000转换为公里")
                df['配送距离_km'] = df['配送距离'] / 1000
            else:
                print(f"   ✅ 平均值={avg:.2f}，判断为【公里】")
                df['配送距离_km'] = df['配送距离']
        
        # 4. 按距离区间统计（转换后）
        print("\n4️⃣ 按距离区间统计（转换为公里后）:")
        
        def get_band(distance):
            if pd.isna(distance):
                return "无距离数据"
            if distance < 0:
                return "异常负值"
            elif distance < 1:
                return "0-1km"
            elif distance < 2:
                return "1-2km"
            elif distance < 3:
                return "2-3km"
            elif distance < 4:
                return "3-4km"
            elif distance < 5:
                return "4-5km"
            elif distance < 6:
                return "5-6km"
            else:
                return "6km+"
        
        df['距离区间'] = df['配送距离_km'].apply(get_band)
        
        band_counts = df['距离区间'].value_counts()
        print("\n   距离区间分布:")
        for band, count in band_counts.items():
            pct = count / len(df) * 100
            print(f"   {band}: {count} 订单 ({pct:.1f}%)")
        
        # 5. 检查异常数据
        print("\n5️⃣ 异常数据检查:")
        
        # 检查距离为0的订单
        zero_distance = df[df['配送距离'] == 0]
        print(f"   配送距离=0的订单: {len(zero_distance)}")
        
        # 检查距离>10km的订单（可能是异常）
        if '配送距离_km' in df.columns:
            far_orders = df[df['配送距离_km'] > 10]
            print(f"   配送距离>10km的订单: {len(far_orders)}")
            if len(far_orders) > 0 and len(far_orders) <= 10:
                print("   示例:")
                for _, row in far_orders.head(5).iterrows():
                    print(f"     订单{row['订单ID']}: {row['配送距离_km']:.2f}km")
        
        # 6. 按门店统计
        print("\n6️⃣ 按门店统计配送距离:")
        store_stats = df.groupby('门店名称').agg({
            '订单ID': 'count',
            '配送距离_km': ['mean', 'min', 'max']
        }).round(2)
        store_stats.columns = ['订单数', '平均距离', '最小距离', '最大距离']
        print(store_stats.to_string())
        
        print("\n" + "=" * 80)
        print("✅ 分析完成")
        print("=" * 80)
        
        return df
        
    finally:
        session.close()


if __name__ == "__main__":
    analyze_distance_distribution()
