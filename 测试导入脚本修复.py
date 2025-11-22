"""
测试导入脚本修复
验证日期列识别和处理逻辑
"""

import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from 真实数据处理器 import RealDataProcessor

def test_date_column_detection():
    """测试日期列识别"""
    
    print("="*60)
    print("测试1: 日期列识别")
    print("="*60)
    
    # 模拟不同的数据格式
    test_cases = [
        {
            'name': '标准格式 - 日期列',
            'data': pd.DataFrame({
                '日期': ['2025-01-01', '2025-01-02'],
                '订单ID': ['001', '002'],
                '商品名称': ['商品A', '商品B']
            })
        },
        {
            'name': '下单时间格式',
            'data': pd.DataFrame({
                '下单时间': ['2025-01-01 10:00:00', '2025-01-02 11:00:00'],
                '订单ID': ['001', '002'],
                '商品名称': ['商品A', '商品B']
            })
        },
        {
            'name': '采集时间格式',
            'data': pd.DataFrame({
                '采集时间': ['2025-01-01', '2025-01-02'],
                '订单ID': ['001', '002'],
                '商品名称': ['商品A', '商品B']
            })
        },
        {
            'name': '英文date格式',
            'data': pd.DataFrame({
                'date': ['2025-01-01', '2025-01-02'],
                '订单ID': ['001', '002'],
                '商品名称': ['商品A', '商品B']
            })
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {case['name']}")
        df = case['data']
        print(f"原始列名: {list(df.columns)}")
        
        # 日期列识别逻辑
        date_col = None
        possible_date_cols = ['日期', '下单时间', '采集时间', 'collect_time', 'timestamp', '时间', '创建时间', 'date', 'order_date', 'created_at']
        
        for possible_col in possible_date_cols:
            if possible_col in df.columns:
                date_col = possible_col
                break
        
        if date_col:
            print(f"✅ 找到日期列: {date_col}")
            print(f"   数据示例: {df[date_col].iloc[0]}")
        else:
            print(f"❌ 未找到日期列!")


def test_standardization():
    """测试标准化流程"""
    
    print("\n" + "="*60)
    print("测试2: 标准化流程")
    print("="*60)
    
    processor = RealDataProcessor()
    
    # 模拟原始数据
    raw_data = pd.DataFrame({
        '下单时间': ['2025-01-01 10:00:00', '2025-01-02 11:00:00'],
        '订单编号': ['001', '002'],
        '商品': ['商品A', '商品B'],
        '门店': ['门店1', '门店2'],
        '售价': [100, 200],
        '数量': [1, 2]
    })
    
    print(f"\n原始数据列名: {list(raw_data.columns)}")
    
    # 标准化
    try:
        standardized = processor.standardize_sales_data(raw_data)
        print(f"\n标准化后列名: {list(standardized.columns)}")
        
        if '日期' in standardized.columns:
            print(f"✅ 日期列已标准化")
            print(f"   数据类型: {standardized['日期'].dtype}")
            print(f"   数据示例: {standardized['日期'].iloc[0]}")
        else:
            print(f"❌ 标准化后未找到日期列")
            
    except Exception as e:
        print(f"❌ 标准化失败: {e}")


def test_date_conversion():
    """测试日期转换"""
    
    print("\n" + "="*60)
    print("测试3: 日期转换")
    print("="*60)
    
    test_dates = [
        '2025-01-01',
        '2025-01-01 10:00:00',
        '2025/01/01',
        '01/01/2025',
        '2025年1月1日',
        'invalid_date',
        None,
        pd.NaT
    ]
    
    for date_value in test_dates:
        try:
            converted = pd.to_datetime(date_value)
            if pd.isna(converted):
                print(f"❌ {date_value} -> NaT")
            else:
                print(f"✅ {date_value} -> {converted}")
        except Exception as e:
            print(f"❌ {date_value} -> 转换失败: {str(e)[:50]}")


def main():
    """主测试流程"""
    
    print("\n导入脚本修复测试\n")
    
    test_date_column_detection()
    test_standardization()
    test_date_conversion()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    print("\n修复总结:")
    print("1. 日期列识别逻辑增强,支持多种列名")
    print("2. 优先使用标准化后的'日期'列")
    print("3. 日期转换失败时跳过记录,而不是使用当前时间")
    print("4. 增加详细的错误日志")


if __name__ == "__main__":
    main()
