# -*- coding: utf-8 -*-
"""
测试热销缺货和价格异常修复
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入诊断分析模块
from components.today_must_do.diagnosis_analysis import analyze_urgent_issues

def create_test_data():
    """创建测试数据"""
    # 生成昨日和前几天的数据
    today = pd.Timestamp.now().normalize()
    yesterday = today - timedelta(days=1)
    
    # 创建测试订单数据
    data = []
    
    # 1. 热销缺货测试数据：商品A在前7天有销量，昨日库存为0
    for i in range(7):
        date = yesterday - timedelta(days=i)
        data.append({
            '订单ID': f'ORDER_{i}_A',
            '商品名称': '商品A_热销缺货',
            '日期': date,
            '月售': 10,
            '销量': 10,
            '剩余库存': 0 if i == 0 else 50,  # 昨日库存为0
            '实收价格': 100,
            '商品采购成本': 500,  # 单品成本 = 500/10 = 50
            '利润额': 300,
            '一级分类名': '食品',
            '平台': '美团',
            '门店名称': '测试门店'
        })
    
    # 2. 价格异常测试数据：商品B售价低于成本
    data.append({
        '订单ID': 'ORDER_PRICE_B',
        '商品名称': '商品B_价格异常',
        '日期': yesterday,
        '月售': 5,
        '销量': 5,
        '剩余库存': 100,
        '实收价格': 8,  # 售价8元
        '商品采购成本': 50,  # 单品成本 = 50/5 = 10元，售价<成本
        '利润额': -10,
        '一级分类名': '食品',
        '平台': '美团',
        '门店名称': '测试门店'
    })
    
    # 3. 正常商品
    data.append({
        '订单ID': 'ORDER_NORMAL_C',
        '商品名称': '商品C_正常',
        '日期': yesterday,
        '月售': 10,
        '销量': 10,
        '剩余库存': 100,
        '实收价格': 100,
        '商品采购成本': 500,  # 单品成本 = 50
        '利润额': 300,
        '一级分类名': '食品',
        '平台': '美团',
        '门店名称': '测试门店'
    })
    
    df = pd.DataFrame(data)
    return df

def test_diagnosis():
    """测试诊断分析"""
    print("="*80)
    print("🧪 测试热销缺货和价格异常修复")
    print("="*80)
    
    # 创建测试数据
    df = create_test_data()
    print(f"\n📊 测试数据: {len(df)} 条记录")
    print(f"   - 商品数: {df['商品名称'].nunique()}")
    print(f"   - 日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
    
    # 执行诊断分析
    print("\n🔍 执行诊断分析...")
    try:
        result = analyze_urgent_issues(df)
        
        print("\n" + "="*80)
        print("📋 诊断结果:")
        print("="*80)
        
        # 热销缺货
        stockout = result['stockout']
        print(f"\n🔴 热销缺货:")
        print(f"   - 缺货商品数: {stockout['count']}")
        print(f"   - 预估损失: ¥{stockout['loss']:.2f}")
        print(f"   - 渠道分布: {stockout['channels']}")
        print(f"   - 持续缺货(≥3天): {stockout.get('persistent_count', 0)}")
        print(f"   - 新增缺货: {stockout.get('new_count', 0)}")
        if stockout.get('error'):
            print(f"   ⚠️ 错误: {stockout['error']}")
        
        # 价格异常
        price_abnormal = result['price_abnormal']
        print(f"\n🟠 价格异常:")
        print(f"   - 异常商品数: {price_abnormal['count']}")
        print(f"   - 预估损失: ¥{price_abnormal['loss']:.2f}")
        print(f"   - 严重异常: {price_abnormal['severe_count']}")
        print(f"   - 轻度异常: {price_abnormal['mild_count']}")
        print(f"   - TOP商品: {price_abnormal['products']}")
        if price_abnormal.get('error'):
            print(f"   ⚠️ 错误: {price_abnormal['error']}")
        
        # 验证结果
        print("\n" + "="*80)
        print("✅ 验证结果:")
        print("="*80)
        
        success = True
        
        # 验证热销缺货
        if stockout['count'] > 0:
            print("✅ 热销缺货检测正常 (检测到缺货商品)")
        else:
            print("❌ 热销缺货检测失败 (应该检测到商品A)")
            success = False
        
        # 验证价格异常
        if price_abnormal['count'] > 0:
            print("✅ 价格异常检测正常 (检测到异常商品)")
        else:
            print("❌ 价格异常检测失败 (应该检测到商品B)")
            success = False
        
        if success:
            print("\n🎉 所有测试通过！修复成功！")
        else:
            print("\n⚠️ 部分测试失败，需要进一步检查")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_diagnosis()
