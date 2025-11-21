"""检查祥和路店数据的字段情况"""
import pandas as pd
import pickle
import gzip
from pathlib import Path

# 查找学习数据仓库中的缓存文件
cache_dir = Path("学习数据仓库/processed_data")

print("=" * 80)
print("查找缓存文件...")
print("=" * 80)

# 列出所有pkl.gz文件
cache_files = sorted(cache_dir.glob("*.pkl.gz"), key=lambda x: x.stat().st_mtime, reverse=True)
print(f"\n找到 {len(cache_files)} 个缓存文件\n")

# 显示前10个文件
print("最新的10个文件:")
for i, f in enumerate(cache_files[:10], 1):
    size_kb = f.stat().st_size / 1024
    mtime = pd.Timestamp.fromtimestamp(f.stat().st_mtime)
    print(f"{i:2d}. {f.name:60s} ({size_kb:7.1f} KB, {mtime})")

if len(cache_files) > 0:
    # 找祥和路店的文件,并且大于10KB
    latest_file = None
    for f in cache_files:
        if '祥和路' in f.name and f.stat().st_size > 10 * 1024:  # 大于10KB
            latest_file = f
            break
    
    if not latest_file:
        print("\n❌ 未找到祥和路店的有效数据文件,使用任意一个大文件")
        for f in cache_files:
            if f.stat().st_size > 10 * 1024:
                latest_file = f
                break
    
    if not latest_file:
        print("\n❌ 所有文件都太小")
        exit()
    
    print(f"\n使用文件: {latest_file.name}")
    print(f"文件大小: {latest_file.stat().st_size / 1024:.1f} KB")
    print(f"修改时间: {pd.Timestamp.fromtimestamp(latest_file.stat().st_mtime)}\n")
    
    # 加载数据
    print("=" * 80)
    print("加载数据...")
    print("=" * 80)
    
    try:
        with gzip.open(latest_file, 'rb') as f:
            payload = pickle.load(f)
        
        # 检查payload的类型
        if isinstance(payload, pd.DataFrame):
            df = payload
            metadata = {}
            print("\n✅ 数据加载成功 (直接DataFrame格式)")
        elif isinstance(payload, dict) and 'data' in payload:
            df = payload['data']
            metadata = payload.get('metadata', {})
            print("\n✅ 数据加载成功 (dict格式)")
        else:
            df = payload
            metadata = {}
            print(f"\n⚠️ 数据格式: {type(payload)}")
            
        if not isinstance(df, pd.DataFrame):
            print(f"❌ payload不是DataFrame: {type(df)}")
            print(f"payload内容: {payload if not isinstance(payload, pd.DataFrame) else '...'}")
            exit()
        
        print(f"\n✅ 数据加载成功")
        print(f"文件名: {metadata.get('original_file', '未知')}")
        print(f"上传时间: {metadata.get('upload_time', '未知')}")
        print(f"数据形状: {df.shape}")
        
        # 检查所有列名
        print("\n" + "=" * 80)
        print("所有字段列表:")
        print("=" * 80)
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")
        
        # 检查关键字段
        print("\n" + "=" * 80)
        print("关键字段检查:")
        print("=" * 80)
        
        critical_fields = {
            '商品名称': '商品名称',
            '一级分类名': '一级分类',
            '库存': '库存数量',
            '日期': '订单日期',
            '月售': '销量'
        }
        
        for standard_field, possible_names in critical_fields.items():
            found = False
            for col in df.columns:
                if standard_field in col or any(name in col for name in possible_names.split('|')):
                    print(f"✅ {standard_field:12s} → 实际字段: {col}")
                    print(f"   数据类型: {df[col].dtype}")
                    print(f"   非空数量: {df[col].notna().sum()}/{len(df)}")
                    if '库存' in col:
                        print(f"   库存统计: min={df[col].min():.1f}, max={df[col].max():.1f}, mean={df[col].mean():.2f}")
                        print(f"   库存>0: {(df[col] > 0).sum()} 条")
                        print(f"   库存=0: {(df[col] == 0).sum()} 条")
                    elif '月售' in standard_field or '销量' in col:
                        print(f"   销量统计: min={df[col].min():.1f}, max={df[col].max():.1f}, sum={df[col].sum():.0f}")
                        print(f"   销量>0: {(df[col] > 0).sum()}/{len(df)}")
                    found = True
                    break
            if not found:
                print(f"❌ {standard_field} → 未找到")
        
        # 检查有库存字段的情况
        print("\n" + "=" * 80)
        print("库存相关字段详细分析:")
        print("=" * 80)
        
        stock_cols = [col for col in df.columns if '库存' in col]
        if stock_cols:
            for col in stock_cols:
                print(f"\n字段: {col}")
                print(f"  数据类型: {df[col].dtype}")
                print(f"  非空: {df[col].notna().sum()}/{len(df)}")
                print(f"  唯一值数量: {df[col].nunique()}")
                print(f"  值分布:\n{df[col].value_counts().head(10)}")
        else:
            print("❌ 没有找到任何包含'库存'的字段")
        
        # 如果有一级分类，检查各分类的数据情况
        if '一级分类名' in df.columns:
            print("\n" + "=" * 80)
            print("各分类数据量:")
            print("=" * 80)
            print(df['一级分类名'].value_counts())
            
            # 如果有库存字段，检查各分类的库存情况
            if stock_cols:
                print("\n" + "=" * 80)
                print("各分类库存情况 (使用第一个库存字段):")
                print("=" * 80)
                stock_field = stock_cols[0]
                cat_stock = df.groupby('一级分类名')[stock_field].agg(['sum', 'mean', 'count'])
                print(cat_stock)
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ 未找到任何缓存文件")
