"""检查Excel源文件中祥和路店的成本"""
import pandas as pd
from pathlib import Path

# 找到数据文件
data_dir = Path("实际数据")
excel_files = sorted([f for f in data_dir.glob("*.xlsx") if not f.name.startswith("~$")])

if excel_files:
    file_path = excel_files[0]
    print(f"📂 读取文件: {file_path.name}\n")
    
    # 读取Excel
    df = pd.read_excel(file_path, sheet_name=0)
    print(f"📊 总数据: {len(df)} 行\n")
    
    # 筛选祥和路店
    if '门店名称' in df.columns:
        xianghelu = df[df['门店名称'].str.contains('祥和路', na=False)]
        print(f"🏪 祥和路店数据: {len(xianghelu)} 行")
        print(f"   门店名称: {xianghelu['门店名称'].unique()[0] if len(xianghelu) > 0 else '未找到'}\n")
        
        # 检查成本字段
        if '成本' in xianghelu.columns:
            cost_col = '成本'
        elif '商品采购成本' in xianghelu.columns:
            cost_col = '商品采购成本'
        else:
            print("❌ 未找到成本字段")
            print(f"可用字段: {list(df.columns)}")
            exit()
        
        print(f"💰 成本分析(字段名: '{cost_col}'):")
        print(f"   成本总和: ¥{xianghelu[cost_col].sum():,.2f}")
        print(f"   成本非空: {xianghelu[cost_col].notna().sum()} / {len(xianghelu)}")
        print(f"   成本NaN: {xianghelu[cost_col].isna().sum()}")
        print(f"   成本为0: {(xianghelu[cost_col] == 0).sum()}")
        print(f"   成本>0: {(xianghelu[cost_col] > 0).sum()}")
        print(f"\n   成本样本(前10个):")
        print(f"   {xianghelu[cost_col].head(10).tolist()}")
        
        # 检查是否有耗材
        if '一级分类名' in xianghelu.columns:
            haocai = xianghelu[xianghelu['一级分类名'] == '耗材']
            non_haocai = xianghelu[xianghelu['一级分类名'] != '耗材']
            print(f"\n📦 分类统计:")
            print(f"   耗材行数: {len(haocai)}")
            print(f"   耗材成本: ¥{haocai[cost_col].sum():,.2f}")
            print(f"   非耗材行数: {len(non_haocai)}")
            print(f"   非耗材成本: ¥{non_haocai[cost_col].sum():,.2f}")
    else:
        print("❌ 未找到'门店名称'字段")
        print(f"可用字段: {list(df.columns)}")
else:
    print("❌ 未找到Excel文件")
