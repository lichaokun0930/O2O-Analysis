"""
测试客单价分析的分sheet输出功能
"""

import pandas as pd
from 问题诊断引擎 import ProblemDiagnosticEngine


def 创建测试数据():
    """创建测试数据 - 确保有明显的客单价变化"""
    data = []
    
    # === 第一天数据（对比期）- 客单价较高 ===
    # 创建20个订单，客单价约150元
    for i in range(20):
        order_id = f'ORDER_001_{i}'
        # 每个订单买2-3个商品
        for j in range(2):
            if j == 0:
                # 高价商品
                data.append({
                    '日期': pd.Timestamp('2025-01-01'),
                    '订单ID': order_id,
                    '商品名称': '商品A_高价',
                    '商品实售价': 100,
                    '一级分类名': '类别1',
                    '三级分类名': '子类1',
                    '剩余库存': 100
                })
            else:
                # 中价商品
                data.append({
                    '日期': pd.Timestamp('2025-01-01'),
                    '订单ID': order_id,
                    '商品名称': '商品B_中价',
                    '商品实售价': 50,
                    '一级分类名': '类别1',
                    '三级分类名': '子类1',
                    '剩余库存': 100
                })
    
    # === 第二天数据（当前期）- 客单价下滑 ===
    # 创建20个订单，客单价约80元（下滑约47%）
    for i in range(20):
        order_id = f'ORDER_002_{i}'
        # 场景1: 10个订单 - 商品A售罄，改买便宜商品
        if i < 10:
            data.append({
                '日期': pd.Timestamp('2025-01-02'),
                '订单ID': order_id,
                '商品名称': '商品C_低价替代',
                '商品实售价': 30,
                '一级分类名': '类别2',
                '三级分类名': '子类2',
                '剩余库存': 100
            })
            data.append({
                '日期': pd.Timestamp('2025-01-02'),
                '订单ID': order_id,
                '商品名称': '商品B_中价',
                '商品实售价': 50,
                '一级分类名': '类别1',
                '三级分类名': '子类1',
                '剩余库存': 90
            })
        # 场景2: 5个订单 - 商品D涨价但销量增（上涨商品）
        elif i < 15:
            data.append({
                '日期': pd.Timestamp('2025-01-02'),
                '订单ID': order_id,
                '商品名称': '商品D_涨价销量增',
                '商品实售价': 60,  # 从50涨到60
                '一级分类名': '类别3',
                '三级分类名': '子类3',
                '剩余库存': 80
            })
            data.append({
                '日期': pd.Timestamp('2025-01-02'),
                '订单ID': order_id,
                '商品名称': '商品B_中价',
                '商品实售价': 50,
                '一级分类名': '类别1',
                '三级分类名': '子类1',
                '剩余库存': 85
            })
        # 场景3: 5个订单 - 商品E涨价导致销量降（下滑商品）
        else:
            data.append({
                '日期': pd.Timestamp('2025-01-02'),
                '订单ID': order_id,
                '商品名称': '商品E_涨价销量降',
                '商品实售价': 120,  # 从100涨到120
                '一级分类名': '类别4',
                '三级分类名': '子类4',
                '剩余库存': 95
            })
    
    # 添加对比数据：第一天也要有这些商品
    # 商品D在第一天（价格50，销量少）
    for i in range(3):
        data.append({
            '日期': pd.Timestamp('2025-01-01'),
            '订单ID': f'ORDER_001_D_{i}',
            '商品名称': '商品D_涨价销量增',
            '商品实售价': 50,
            '一级分类名': '类别3',
            '三级分类名': '子类3',
            '剩余库存': 100
        })
    
    # 商品E在第一天（价格100，销量多）
    for i in range(10):
        data.append({
            '日期': pd.Timestamp('2025-01-01'),
            '订单ID': f'ORDER_001_E_{i}',
            '商品名称': '商品E_涨价销量降',
            '商品实售价': 100,
            '一级分类名': '类别4',
            '三级分类名': '子类4',
            '剩余库存': 100
        })
    
    # 商品A在第一天销售（后来售罄）
    for i in range(15):
        data.append({
            '日期': pd.Timestamp('2025-01-01'),
            '订单ID': f'ORDER_001_A_{i}',
            '商品名称': '商品A_高价',
            '商品实售价': 100,
            '一级分类名': '类别1',
            '三级分类名': '子类1',
            '剩余库存': 100
        })
    
    # 第二天商品A售罄
    data.append({
        '日期': pd.Timestamp('2025-01-02'),
        '订单ID': 'ORDER_002_A_last',
        '商品名称': '商品A_高价',
        '商品实售价': 100,
        '一级分类名': '类别1',
        '三级分类名': '子类1',
        '剩余库存': 0  # 售罄
    })
    
    return pd.DataFrame(data)


def main():
    print("\n" + "="*60)
    print("测试客单价分析 - 分Sheet输出")
    print("="*60)
    
    # 创建测试数据
    df = 创建测试数据()
    print(f"\n✓ 创建测试数据: {len(df)} 条记录")
    
    # 初始化引擎
    engine = ProblemDiagnosticEngine(df)
    print(f"✓ 初始化问题诊断引擎")
    
    # 先测试原始方法
    print(f"\n测试原始方法 diagnose_customer_price_decline()...")
    original_result = engine.diagnose_customer_price_decline(
        time_period='day',
        threshold=-5.0
    )
    print(f"  原始方法返回: {len(original_result)} 行")
    if len(original_result) > 0:
        print(f"  列数: {len(original_result.columns)}")
        print(f"  前5列: {list(original_result.columns[:5])}")
    
    # 调用分sheet方法
    print(f"\n调用 diagnose_customer_price_decline_by_sheets()...")
    sheets_data = engine.diagnose_customer_price_decline_by_sheets(
        time_period='day',
        threshold=-5.0
    )
    
    print(f"\n✓ 返回 {len(sheets_data)} 个Sheet")
    
    # 检查每个sheet
    for sheet_name, df_sheet in sheets_data.items():
        print(f"\n{'='*60}")
        print(f"Sheet: {sheet_name}")
        print(f"{'='*60}")
        
        if len(df_sheet) == 0:
            print("  ⚠️ 空数据")
            continue
        
        print(f"  行数: {len(df_sheet)}")
        print(f"  列数: {len(df_sheet.columns)}")
        print(f"\n  列名:")
        for i, col in enumerate(df_sheet.columns, 1):
            print(f"    {i}. {col}")
        
        # 显示数据示例
        if len(df_sheet) > 0:
            print(f"\n  数据示例（第1行）:")
            row = df_sheet.iloc[0]
            for col in df_sheet.columns[:10]:  # 只显示前10列
                value = row[col]
                if pd.notna(value) and value != '':
                    print(f"    {col}: {value}")
    
    # 保存到Excel
    output_file = '测试分sheet输出_结果.xlsx'
    print(f"\n{'='*60}")
    print(f"保存到Excel: {output_file}")
    print(f"{'='*60}")
    
    # 检查是否有数据
    has_data = any(len(df_sheet) > 0 for df_sheet in sheets_data.values())
    
    if has_data:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df_sheet in sheets_data.items():
                if len(df_sheet) > 0:
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  ✓ 写入sheet: {sheet_name} ({len(df_sheet)} 行)")
        
        print(f"\n✅ 测试完成！文件已保存: {output_file}")
    else:
        print(f"\n⚠️ 所有sheet都为空，未保存Excel文件")
        print(f"  可能原因：数据不满足阈值条件或数据量不足")
    
    # 验证
    print(f"\n{'='*60}")
    print(f"验证结果")
    print(f"{'='*60}")
    
    all_passed = True
    
    # 验证1: 三个sheet都存在
    expected_sheets = ['客单价变化', '下滑商品分析', '上涨商品分析']
    for sheet_name in expected_sheets:
        if sheet_name in sheets_data:
            print(f"  ✓ {sheet_name} 存在")
        else:
            print(f"  ❌ {sheet_name} 缺失")
            all_passed = False
    
    # 验证2: 客单价变化sheet包含基础字段
    if '客单价变化' in sheets_data and len(sheets_data['客单价变化']) > 0:
        expected_cols = ['对比周期', '之前客单价', '当前客单价', '客单价变化', '变化幅度%']
        price_df = sheets_data['客单价变化']
        for col in expected_cols:
            if col in price_df.columns:
                print(f"  ✓ 客单价变化包含字段: {col}")
            else:
                print(f"  ❌ 客单价变化缺少字段: {col}")
                all_passed = False
    
    # 验证3: 下滑商品sheet只包含下滑商品字段
    if '下滑商品分析' in sheets_data and len(sheets_data['下滑商品分析']) > 0:
        declining_df = sheets_data['下滑商品分析']
        has_declining = any('下滑商品' in col for col in declining_df.columns)
        has_rising = any('上涨商品' in col for col in declining_df.columns)
        
        if has_declining and not has_rising:
            print(f"  ✓ 下滑商品分析只包含下滑商品字段")
        else:
            print(f"  ❌ 下滑商品分析字段不正确")
            all_passed = False
    
    # 验证4: 上涨商品sheet只包含上涨商品字段
    if '上涨商品分析' in sheets_data and len(sheets_data['上涨商品分析']) > 0:
        rising_df = sheets_data['上涨商品分析']
        has_rising = any('上涨商品' in col for col in rising_df.columns)
        has_declining = any('下滑商品' in col for col in rising_df.columns)
        
        if has_rising and not has_declining:
            print(f"  ✓ 上涨商品分析只包含上涨商品字段")
        else:
            print(f"  ❌ 上涨商品分析字段不正确")
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 所有验证通过！")
    else:
        print(f"\n❌ 部分验证失败")
    
    return all_passed


if __name__ == '__main__':
    main()
