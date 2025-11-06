"""
检查GLOBAL_DATA中的字段
"""
import sys
import os
import glob
import pickle
import gzip

cache_dir = "学习数据仓库/uploaded_data"
cache_files = glob.glob(os.path.join(cache_dir, "*.pkl.gz"))

if not cache_files:
    print("未找到缓存文件")
    sys.exit(1)

# 获取最新文件
latest = max(cache_files, key=os.path.getmtime)
print(f"最新缓存文件: {os.path.basename(latest)}")

# 加载数据
with gzip.open(latest, 'rb') as f:
    data = pickle.load(f)

# 检查数据类型
print(f"\n数据类型: {type(data)}")

if isinstance(data, dict):
    print(f"字典键数: {len(data)}")
    print(f"字典键: {list(data.keys())}")
    
    # 尝试从字典中提取DataFrame
    if 'data' in data:
        df = data['data']
    elif 'df' in data:
        df = data['df']
    else:
        print("\n无法从dict中找到DataFrame，尝试第一个值：")
        df = list(data.values())[0]
else:
    df = data

import pandas as pd
if not isinstance(df, pd.DataFrame):
    print(f"错误：数据不是DataFrame，而是 {type(df)}")
    sys.exit(1)

print(f"\n数据行数: {len(df)}")
print(f"字段总数: {len(df.columns)}\n")

print("所有字段:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

# 检查关键字段
print("\n\n关键字段检查:")
required = ['日期', '商品名称', '三级分类名', '场景', '时段', '销量', '预计订单收入', '利润额']
for field in required:
    exists = field in df.columns
    status = "✅" if exists else "❌"
    print(f"  {status} {field}")

# 检查日期范围
if '日期' in df.columns:
    print(f"\n日期范围:")
    print(f"  最小: {df['日期'].min()}")
    print(f"  最大: {df['日期'].max()}")
    print(f"  类型: {df['日期'].dtype}")
    
    # 计算天数
    import pandas as pd
    if pd.api.types.is_datetime64_any_dtype(df['日期']):
        days = (df['日期'].max() - df['日期'].min()).days
        print(f"  跨度: {days} 天 ({days/7:.1f} 周)")
