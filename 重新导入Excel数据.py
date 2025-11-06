"""
重新导入Excel数据到数据库 - 修复字段映射问题
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.migrate_orders import upsert_orders
from 真实数据处理器 import RealDataProcessor
import pandas as pd

def main():
    print("=" * 80)
    print("🔄 重新导入Excel数据 - 修复字段映射")
    print("=" * 80)
    
    # 1. 读取Excel
    excel_file = "门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
    print(f"\n📖 读取Excel: {excel_file}")
    
    df = pd.read_excel(excel_file)
    print(f"✅ 读取成功: {len(df):,} 行, {len(df.columns)} 列")
    
    # 2. 标准化数据
    print(f"\n🔧 标准化数据...")
    processor = RealDataProcessor()
    df = processor.standardize_sales_data(df)
    print(f"✅ 标准化完成: {len(df):,} 行")
    
    # 3. 数据验证
    print(f"\n📊 数据验证...")
    print(f"  日期范围: {df['日期'].min()} 到 {df['日期'].max()}")
    print(f"  订单数: {df['订单ID'].nunique():,}")
    print(f"  商品数: {df['商品名称'].nunique():,}")
    
    # 验证关键字段
    key_fields = ['利润额', '满减金额', '配送费减免金额', '用户支付配送费']
    print(f"\n  关键字段检查:")
    for field in key_fields:
        if field in df.columns:
            total = df[field].sum()
            non_zero = (df[field] > 0).sum()
            print(f"    ✅ {field}: 总计={total:,.2f}, 非零行={non_zero:,}/{len(df):,}")
        else:
            print(f"    ❌ {field}: 缺失")
    
    # 4. 确认导入
    print(f"\n" + "=" * 80)
    print(f"准备导入 {len(df):,} 条订单数据到数据库")
    print(f"此操作将更新数据库中的所有订单记录")
    print("=" * 80)
    
    confirm = input("\n是否继续? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 取消导入")
        return
    
    # 5. 导入数据
    print(f"\n🚀 开始导入...")
    stats = upsert_orders(df, batch_size=1000)
    
    # 6. 显示结果
    print(f"\n" + "=" * 80)
    print(f"✅ 导入完成!")
    print(f"=" * 80)
    print(f"  总记录数: {stats['total']:,}")
    print(f"  插入: {stats['inserted']:,}")
    print(f"  更新: {stats['updated']:,}")
    print(f"  错误: {stats['errors']:,}")
    
    if stats['errors'] > 0 and stats['error_details']:
        print(f"\n⚠️ 错误详情 (前10条):")
        for err in stats['error_details'][:10]:
            print(f"  行 {err['row']}: {err['error']}")
    
    print(f"\n" + "=" * 80)
    
    # 7. 验证导入结果
    print(f"\n🔍 验证导入结果...")
    from database.connection import get_db
    from database.models import Order
    
    db = next(get_db())
    
    # 统计
    total_orders = db.query(Order).count()
    profit_not_null = db.query(Order).filter(Order.profit != None).filter(Order.profit != 0).count()
    marketing_not_zero = db.query(Order).filter(Order.full_reduction > 0).count()
    
    print(f"  数据库总订单数: {total_orders:,}")
    print(f"  有利润数据的订单: {profit_not_null:,} ({profit_not_null/total_orders*100:.1f}%)")
    print(f"  有满减活动的订单: {marketing_not_zero:,} ({marketing_not_zero/total_orders*100:.1f}%)")
    
    # 样本数据
    sample = db.query(Order).filter(Order.profit > 0).first()
    if sample:
        print(f"\n  样本订单:")
        print(f"    商品: {sample.product_name}")
        print(f"    价格: {sample.price}")
        print(f"    成本: {sample.cost}")
        print(f"    利润: {sample.profit}")
        print(f"    满减: {sample.full_reduction}")
        print(f"    配送费减免: {sample.delivery_discount}")
    
    print(f"\n✅ 所有数据已成功导入!")

if __name__ == "__main__":
    main()
