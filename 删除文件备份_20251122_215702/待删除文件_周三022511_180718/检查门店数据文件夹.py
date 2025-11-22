"""
检查门店数据文件夹中的枫瑞店数据
"""
import pandas as pd

file_path = '门店数据/枫瑞店.xlsx'

# 检查所有sheet
xl_file = pd.ExcelFile(file_path)
print("=" * 80)
print(f"📂 文件: {file_path}")
print("=" * 80)
print(f"\nSheet列表: {xl_file.sheet_names}")

# 读取每个sheet
for sheet_name in xl_file.sheet_names:
    print(f"\n{'=' * 80}")
    print(f"📊 Sheet: {sheet_name}")
    print('=' * 80)
    
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    print(f"  行数: {len(df)}")
    print(f"  列数: {len(df.columns)}")
    print(f"  列名: {df.columns.tolist()[:10]}")  # 显示前10个列名
    
    # 检查是否有渠道字段
    if '渠道' in df.columns:
        print(f"\n  渠道分布:")
        for ch, cnt in df['渠道'].value_counts().items():
            print(f"    {ch}: {cnt}行")
    
    # 检查是否有利润额字段
    if '利润额' in df.columns:
        print(f"\n  利润额统计:")
        print(f"    总和: {df['利润额'].sum():.2f}")
        print(f"    非0行数: {(df['利润额'] != 0).sum()}")
        print(f"    为0行数: {(df['利润额'] == 0).sum()}")
    
    # 检查订单数
    if '订单ID' in df.columns:
        print(f"\n  订单统计:")
        print(f"    唯一订单ID数: {df['订单ID'].nunique()}")
    
    # 检查一级分类
    if '一级分类名' in df.columns:
        print(f"\n  一级分类分布:")
        for cat, cnt in df['一级分类名'].value_counts().head(5).items():
            print(f"    {cat}: {cnt}行")
