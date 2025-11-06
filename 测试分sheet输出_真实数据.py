"""
使用真实Excel数据测试分sheet输出功能
"""

import pandas as pd
from 问题诊断引擎 import ProblemDiagnosticEngine


def main():
    print("\n" + "="*60)
    print("使用真实数据测试客单价分析 - 分Sheet输出")
    print("="*60)
    
    # 读取真实数据
    excel_file = "门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
    print(f"\n读取数据: {excel_file}")
    
    try:
        df = pd.read_excel(excel_file)
        print(f"✓ 读取成功: {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return
    
    # 初始化引擎
    engine = ProblemDiagnosticEngine(df)
    print(f"✓ 初始化问题诊断引擎")
    
    # 先测试原始方法
    print(f"\n{'='*60}")
    print(f"测试原始方法 diagnose_customer_price_decline()")
    print(f"{'='*60}")
    
    original_result = engine.diagnose_customer_price_decline(
        time_period='day',
        threshold=-5.0
    )
    print(f"  返回: {len(original_result)} 行")
    if len(original_result) > 0:
        print(f"  列数: {len(original_result.columns)}")
        print(f"\n  前10列:")
        for i, col in enumerate(original_result.columns[:10], 1):
            print(f"    {i}. {col}")
    
    # 调用分sheet方法
    print(f"\n{'='*60}")
    print(f"调用 diagnose_customer_price_decline_by_sheets()")
    print(f"{'='*60}")
    
    sheets_data = engine.diagnose_customer_price_decline_by_sheets(
        time_period='day',
        threshold=-5.0
    )
    
    print(f"\n✓ 返回 {len(sheets_data)} 个Sheet")
    
    # 检查每个sheet
    for sheet_name, df_sheet in sheets_data.items():
        print(f"\n{'-'*60}")
        print(f"Sheet: {sheet_name}")
        print(f"{'-'*60}")
        
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
            print(f"\n  数据示例（前3行）:")
            for idx in range(min(3, len(df_sheet))):
                print(f"\n  第{idx+1}行:")
                row = df_sheet.iloc[idx]
                for col in df_sheet.columns[:8]:  # 只显示前8列
                    value = row[col]
                    if pd.notna(value) and value != '':
                        print(f"    {col}: {value}")
    
    # 保存到Excel
    output_file = '真实数据分sheet输出_结果.xlsx'
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
                    print(f"  ✓ 写入sheet: {sheet_name} ({len(df_sheet)} 行 × {len(df_sheet.columns)} 列)")
        
        print(f"\n✅ 测试完成！文件已保存: {output_file}")
    else:
        print(f"\n⚠️ 所有sheet都为空，未保存Excel文件")
    
    # 简单验证
    print(f"\n{'='*60}")
    print(f"验证结果")
    print(f"{'='*60}")
    
    for sheet_name in ['客单价变化', '下滑商品分析', '上涨商品分析']:
        if sheet_name in sheets_data:
            df_sheet = sheets_data[sheet_name]
            status = f"{len(df_sheet)} 行" if len(df_sheet) > 0 else "空"
            print(f"  {sheet_name}: {status}")


if __name__ == '__main__':
    main()
