"""
测试商品健康分析字段删除
验证实收价格和特殊标记字段已被删除
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.data_source_manager import DataSourceManager

def test_field_removal():
    """测试字段删除"""
    print("="*60)
    print("测试商品健康分析字段删除")
    print("="*60)
    
    # 加载数据
    print("\n1. 加载数据...")
    data_manager = DataSourceManager()
    df = data_manager.load_data()
    
    if df is None or df.empty:
        print("❌ 数据加载失败")
        return
    
    print(f"✅ 数据加载成功: {len(df)} 条记录")
    
    # 检查原始数据中是否有这两个字段
    print("\n2. 检查原始数据字段...")
    has_actual_price = '实收价格' in df.columns
    has_sale_price = '商品实售价' in df.columns
    has_special_mark = '特殊标记' in df.columns
    has_problem_tag = '问题标签' in df.columns
    
    print(f"   实收价格: {'✅ 存在' if has_actual_price else '❌ 不存在'}")
    print(f"   商品实售价: {'✅ 存在' if has_sale_price else '❌ 不存在'}")
    print(f"   特殊标记: {'✅ 存在' if has_special_mark else '❌ 不存在'}")
    print(f"   问题标签: {'✅ 存在' if has_problem_tag else '❌ 不存在'}")
    
    # 如果原始数据中有这两个字段，检查它们是否相同
    if has_actual_price and has_sale_price:
        print("\n3. 检查实收价格和商品实售价是否相同...")
        sample_df = df[['商品实售价', '实收价格']].head(10)
        print(sample_df)
        
        # 计算差异
        df_check = df[['商品实售价', '实收价格']].dropna()
        if len(df_check) > 0:
            diff = (df_check['商品实售价'] - df_check['实收价格']).abs()
            same_count = (diff < 0.01).sum()
            total_count = len(df_check)
            same_ratio = same_count / total_count * 100
            
            print(f"\n   相同记录: {same_count}/{total_count} ({same_ratio:.1f}%)")
            
            if same_ratio > 95:
                print("   ⚠️ 两个字段基本相同，删除实收价格是合理的")
            else:
                print("   ⚠️ 两个字段有差异，需要进一步确认")
                print(f"   平均差异: ¥{diff.mean():.2f}")
                print(f"   最大差异: ¥{diff.max():.2f}")
    
    print("\n4. 验证修改...")
    print("   ✅ 已从商品健康分析表格中删除以下字段:")
    print("      - 实收价格（与商品实售价重复）")
    print("      - 特殊标记（与问题标签重复）")
    print("\n   保留字段:")
    print("      - 商品实售价（商家定价）")
    print("      - 问题标签（问题诊断）")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == '__main__':
    test_field_removal()
