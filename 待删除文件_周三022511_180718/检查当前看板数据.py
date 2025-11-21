import pandas as pd

# 检查当前看板加载的数据文件
file = '2025-10-19 00_00_00至2025-11-17 23_59_59订单明细数据导出汇总.xlsx'

try:
    df = pd.read_excel(file)
    print(f"文件: {file}")
    print(f"总行数: {len(df)}行")
    
    # 检查渠道分布
    if '渠道' in df.columns:
        print(f"\n渠道分布:")
        print(df['渠道'].value_counts())
    
    # 检查美团共橙
    if '渠道' in df.columns:
        mt = df[df['渠道'].str.contains('美团', na=False)]
        print(f"\n美团相关数据: {len(mt)}行")
        if len(mt) > 0:
            print(f"美团渠道详细:")
            print(mt['渠道'].value_counts())
            
            # 检查是否有耗材
            if '一级分类名' in mt.columns:
                haocai = mt[mt['一级分类名'] == '耗材']
                print(f"\n美团数据中的耗材: {len(haocai)}行")
                if len(haocai) > 0:
                    print(f"耗材利润: {haocai['利润额'].sum():.2f}")
                
                # 计算美团共橙利润
                mt_gongcheng = mt[mt['渠道'] == '美团共橙']
                if len(mt_gongcheng) > 0:
                    print(f"\n美团共橙数据: {len(mt_gongcheng)}行")
                    print(f"利润额总和: {mt_gongcheng['利润额'].sum():.2f}")
                else:
                    mt_shanguang = mt[mt['渠道'] == '美团闪购']
                    if len(mt_shanguang) > 0:
                        print(f"\n美团闪购数据: {len(mt_shanguang)}行, {mt_shanguang['订单ID'].nunique()}个订单")
                        print(f"利润额总和: {mt_shanguang['利润额'].sum():.2f}")
                        
except FileNotFoundError:
    print(f"文件不存在: {file}")
    print("\n当前目录下的Excel文件:")
    import os
    for f in os.listdir('.'):
        if f.endswith('.xlsx'):
            print(f"  - {f}")
