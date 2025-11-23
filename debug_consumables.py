import pandas as pd
import pathlib
import os

APP_DIR = pathlib.Path(r"D:\Python\订单数据看板\O2O-Analysis")
DATA_DIR = APP_DIR / "实际数据"

def check_data():
    print(f"Checking data in {DATA_DIR}")
    if not DATA_DIR.exists():
        print("Data dir not found")
        return

    excel_files = sorted([f for f in DATA_DIR.glob("*.xlsx") if not f.name.startswith("~$")])
    if not excel_files:
        print("No excel files found")
        return

    data_file = excel_files[0]
    print(f"Loading {data_file}")
    
    try:
        df = pd.read_excel(data_file)
        print(f"Columns: {list(df.columns)}")
        
        # Check for category column
        cat_col = None
        candidates = ['一级分类名', '美团一级分类', 'category_l1', 'primary_category', '一级分类']
        for c in candidates:
            if c in df.columns:
                cat_col = c
                break
        
        if cat_col:
            print(f"Found category column: {cat_col}")
            unique_cats = df[cat_col].unique()
            print(f"Unique categories: {unique_cats}")
            
            if '耗材' in unique_cats:
                consumables = df[df[cat_col] == '耗材']
                print(f"Found {len(consumables)} rows for '耗材'")
                cost_col = None
                cost_candidates = ['商品采购成本', '成本', '原价', 'original_price', 'cost']
                for c in cost_candidates:
                    if c in df.columns:
                        cost_col = c
                        break
                
                if cost_col:
                    total_cost = consumables[cost_col].sum()
                    print(f"Total consumable cost: {total_cost}")
                else:
                    print("Cost column not found")
            else:
                print("'耗材' not found in categories")
        else:
            print("Category column not found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()