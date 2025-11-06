"""
诊断数据字段问题
检查Excel数据和数据库数据的字段差异
"""
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.data_source_manager import DataSourceManager
from 真实数据处理器 import RealDataProcessor

print("=" * 80)
print("📊 数据字段诊断工具")
print("=" * 80)

# 加载Excel数据
print("\n1️⃣ 加载Excel数据...")
processor = RealDataProcessor()
excel_data = processor.load_business_data()

if excel_data is not None and not excel_data.empty:
    print(f"✅ Excel数据加载成功: {len(excel_data)} 行")
    print(f"📋 Excel字段 ({len(excel_data.columns)}个):")
    for i, col in enumerate(sorted(excel_data.columns), 1):
        sample = excel_data[col].iloc[0] if len(excel_data) > 0 else None
        dtype = excel_data[col].dtype
        print(f"   {i:2d}. {col:30s} | 类型: {dtype:10s} | 示例: {sample}")
else:
    print("❌ Excel数据加载失败")

# 加载数据库数据
print("\n2️⃣ 加载数据库数据...")
try:
    manager = DataSourceManager()
    db_data = manager.load_from_database()
    
    if db_data is not None and not db_data.empty:
        print(f"✅ 数据库数据加载成功: {len(db_data)} 行")
        print(f"📋 数据库字段 ({len(db_data.columns)}个):")
        for i, col in enumerate(sorted(db_data.columns), 1):
            sample = db_data[col].iloc[0] if len(db_data) > 0 else None
            dtype = db_data[col].dtype
            print(f"   {i:2d}. {col:30s} | 类型: {dtype:10s} | 示例: {sample}")
    else:
        print("⚠️ 数据库为空")
except Exception as e:
    print(f"❌ 数据库加载失败: {e}")
    db_data = None

# 比较字段差异
if excel_data is not None and db_data is not None:
    print("\n3️⃣ 字段差异分析...")
    
    excel_cols = set(excel_data.columns)
    db_cols = set(db_data.columns)
    
    # Excel有但数据库没有
    missing_in_db = excel_cols - db_cols
    if missing_in_db:
        print(f"\n❌ Excel有但数据库缺少的字段 ({len(missing_in_db)}个):")
        for col in sorted(missing_in_db):
            print(f"   - {col}")
    
    # 数据库有但Excel没有
    extra_in_db = db_cols - excel_cols
    if extra_in_db:
        print(f"\n➕ 数据库有但Excel没有的字段 ({len(extra_in_db)}个):")
        for col in sorted(extra_in_db):
            print(f"   + {col}")
    
    # 共同字段
    common = excel_cols & db_cols
    print(f"\n✅ 共同字段 ({len(common)}个):")
    for col in sorted(common):
        print(f"   ✓ {col}")

# 检查必需字段
print("\n4️⃣ 检查必需字段...")
required_fields = [
    '订单ID', '商品名称', '商品实售价', '商品采购成本',
    '利润额', '月售', '用户支付配送费', '配送费减免金额',
    '物流配送费', '满减金额', '商品减免金额', '商家代金券',
    '商家承担部分券', '平台佣金', '打包袋金额'
]

for data_name, data in [("Excel", excel_data), ("数据库", db_data)]:
    if data is None:
        continue
    
    print(f"\n{data_name}数据:")
    missing = []
    for field in required_fields:
        if field in data.columns:
            print(f"   ✅ {field}")
        else:
            print(f"   ❌ {field} - 缺失")
            missing.append(field)
    
    if missing:
        print(f"\n⚠️ {data_name}缺少 {len(missing)} 个必需字段")
    else:
        print(f"\n✅ {data_name}包含所有必需字段")

print("\n" + "=" * 80)
print("诊断完成！")
print("=" * 80)
