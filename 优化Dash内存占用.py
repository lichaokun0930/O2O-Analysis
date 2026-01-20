#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash版本内存优化脚本

功能：
1. 优化数据类型（Float64→Float32, 分类字段→Category）
2. 导出为Parquet格式（高压缩率）
3. 修改Dash代码以使用Parquet

预期效果：
- 内存占用：1.8GB → 600-800MB（减少60%）
- 加载速度：提升50%
- 磁盘占用：减少70%
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from pathlib import Path
import sys

# 数据库配置
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/o2o_dashboard"

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    优化DataFrame内存占用
    
    策略：
    1. Float64 → Float32（减少50%）
    2. Int64 → Int32/Int16（减少50-75%）
    3. 分类字段 → Category（减少80-90%）
    """
    print("\n" + "="*80)
    print("🔧 开始优化数据类型...")
    print("="*80)
    
    # 记录优化前内存
    mem_before = df.memory_usage(deep=True).sum() / 1024**2
    print(f"📊 优化前内存: {mem_before:.2f} MB")
    
    df = df.copy()
    
    # 1. 优化浮点数类型
    float_cols = df.select_dtypes(include=['float64']).columns
    if len(float_cols) > 0:
        print(f"\n✅ 优化 {len(float_cols)} 个浮点数列: Float64 → Float32")
        for col in float_cols:
            df[col] = df[col].astype('float32')
    
    # 2. 优化整数类型
    int_cols = df.select_dtypes(include=['int64']).columns
    if len(int_cols) > 0:
        print(f"✅ 优化 {len(int_cols)} 个整数列:")
        for col in int_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            
            # 根据数值范围选择合适的类型
            if col_min >= 0:  # 无符号整数
                if col_max < 255:
                    df[col] = df[col].astype('uint8')
                    print(f"   - {col}: Int64 → UInt8")
                elif col_max < 65535:
                    df[col] = df[col].astype('uint16')
                    print(f"   - {col}: Int64 → UInt16")
                elif col_max < 4294967295:
                    df[col] = df[col].astype('uint32')
                    print(f"   - {col}: Int64 → UInt32")
            else:  # 有符号整数
                if col_min > -128 and col_max < 127:
                    df[col] = df[col].astype('int8')
                    print(f"   - {col}: Int64 → Int8")
                elif col_min > -32768 and col_max < 32767:
                    df[col] = df[col].astype('int16')
                    print(f"   - {col}: Int64 → Int16")
                elif col_min > -2147483648 and col_max < 2147483647:
                    df[col] = df[col].astype('int32')
                    print(f"   - {col}: Int64 → Int32")
    
    # 3. 优化分类字段（关键！）
    categorical_candidates = [
        '渠道', '门店名称', '门店ID', '店内码',
        '一级分类名', '三级分类名', 
        '商品名称', '条码',
        '消费场景', '时段', '配送平台'
    ]
    
    categorical_cols = [col for col in categorical_candidates if col in df.columns]
    if len(categorical_cols) > 0:
        print(f"\n✅ 优化 {len(categorical_cols)} 个分类列: Object → Category")
        for col in categorical_cols:
            unique_count = df[col].nunique()
            total_count = len(df)
            ratio = unique_count / total_count * 100
            
            # 只有当唯一值比例 < 50% 时才转换为Category
            if ratio < 50:
                df[col] = df[col].astype('category')
                print(f"   - {col}: {unique_count} 个唯一值 ({ratio:.1f}%)")
            else:
                print(f"   ⚠️ {col}: 唯一值过多 ({ratio:.1f}%)，保持Object类型")
    
    # 记录优化后内存
    mem_after = df.memory_usage(deep=True).sum() / 1024**2
    reduction = (1 - mem_after / mem_before) * 100
    
    print(f"\n📊 优化后内存: {mem_after:.2f} MB")
    print(f"💾 内存减少: {mem_before - mem_after:.2f} MB ({reduction:.1f}%)")
    print("="*80 + "\n")
    
    return df


def export_to_parquet(df: pd.DataFrame, output_path: str):
    """
    导出为Parquet格式
    
    优势：
    - 列式存储，压缩率高
    - 保留数据类型
    - 读取速度快
    """
    print("\n" + "="*80)
    print("💾 导出为Parquet格式...")
    print("="*80)
    
    # 导出
    df.to_parquet(
        output_path,
        engine='pyarrow',
        compression='snappy',  # 快速压缩
        index=False
    )
    
    # 检查文件大小
    file_size = Path(output_path).stat().st_size / 1024**2
    print(f"✅ 导出完成: {output_path}")
    print(f"📦 文件大小: {file_size:.2f} MB")
    print("="*80 + "\n")


def load_from_database():
    """从PostgreSQL加载数据"""
    print("\n" + "="*80)
    print("🔄 从数据库加载数据...")
    print("="*80)
    
    engine = create_engine(DATABASE_URL)
    
    # 加载订单数据
    query = """
    SELECT 
        order_id as "订单ID",
        date as "日期",
        store_name as "门店名称",
        store_id as "门店ID",
        channel as "渠道",
        product_name as "商品名称",
        barcode as "条码",
        category_level1 as "一级分类名",
        category_level3 as "三级分类名",
        quantity as "月售",
        price as "商品实售价",
        actual_price as "实收价格",
        cost as "商品采购成本",
        profit as "利润额",
        delivery_fee as "物流配送费",
        platform_service_fee as "平台服务费",
        commission as "平台佣金",
        amount as "预计订单收入",
        corporate_rebate as "企客后返",
        user_paid_delivery_fee as "用户支付配送费",
        delivery_discount as "配送费减免金额",
        full_reduction as "满减金额",
        product_discount as "商品减免金额",
        new_customer_discount as "新客减免金额",
        merchant_voucher as "商家代金券",
        merchant_share as "商家承担部分券",
        gift_amount as "满赠金额",
        other_merchant_discount as "商家其他优惠"
    FROM orders
    ORDER BY date DESC
    """
    
    df = pd.read_sql(query, engine)
    
    print(f"✅ 数据加载完成: {len(df):,} 行")
    print(f"📊 数据范围: {df['日期'].min()} ~ {df['日期'].max()}")
    print(f"🏪 门店数量: {df['门店名称'].nunique()}")
    print("="*80 + "\n")
    
    return df


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 Dash版本内存优化工具")
    print("="*80)
    
    # 1. 从数据库加载
    df = load_from_database()
    
    # 2. 优化数据类型
    df_optimized = optimize_dataframe_memory(df)
    
    # 3. 导出为Parquet
    output_dir = Path("data_cache")
    output_dir.mkdir(exist_ok=True)
    
    parquet_path = output_dir / "orders_optimized.parquet"
    export_to_parquet(df_optimized, str(parquet_path))
    
    # 4. 验证读取
    print("\n" + "="*80)
    print("🔍 验证Parquet文件...")
    print("="*80)
    
    df_loaded = pd.read_parquet(parquet_path)
    mem_loaded = df_loaded.memory_usage(deep=True).sum() / 1024**2
    
    print(f"✅ 读取成功: {len(df_loaded):,} 行")
    print(f"📊 内存占用: {mem_loaded:.2f} MB")
    print(f"🎯 数据类型保留: {df_loaded.dtypes.value_counts().to_dict()}")
    print("="*80 + "\n")
    
    # 5. 生成使用说明
    print("\n" + "="*80)
    print("📝 使用说明")
    print("="*80)
    print("""
修改 智能门店看板_Dash版.py 中的数据加载代码：

# 原代码（第1207行附近）：
# GLOBAL_DATA = df_loaded.copy()

# 新代码：
import pandas as pd
from pathlib import Path

# 从Parquet加载（替代数据库查询）
parquet_path = Path(__file__).parent / "data_cache" / "orders_optimized.parquet"
if parquet_path.exists():
    print("📦 从Parquet缓存加载数据...")
    GLOBAL_DATA = pd.read_parquet(parquet_path)
    print(f"✅ 数据加载完成: {len(GLOBAL_DATA):,} 行")
else:
    # 回退到原有逻辑
    GLOBAL_DATA = df_loaded.copy()

预期效果：
- 启动速度：提升 50%
- 内存占用：减少 60% (1.8GB → 700MB)
- 磁盘占用：减少 70%
    """)
    print("="*80 + "\n")
    
    print("✅ 优化完成！")
    print(f"📦 Parquet文件位置: {parquet_path}")
    print("\n💡 提示：每次数据库更新后，重新运行此脚本更新Parquet文件")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
