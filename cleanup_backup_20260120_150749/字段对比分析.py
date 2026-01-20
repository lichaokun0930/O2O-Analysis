# -*- coding: utf-8 -*-
"""
完整字段对比分析：原始Excel vs Dash版本 vs React版本
"""

# 原始Excel字段（用户提供的完整列表）
EXCEL_FIELDS = [
    "下单时间", "门店名称", "收货地址", "一级分类名", "商品名称", "商品实售价", 
    "商品原价", "销量", "订单ID", "剩余库存", "三级分类名", "利润额", "订单零售额", 
    "条码", "成本", "店内码", "物流配送费", "配送距离", "渠道", "平台佣金", 
    "实收价格", "用户支付金额", "预计订单收入", "用户支付配送费", "配送费减免金额", 
    "满减金额", "商品减免金额", "商家代金券", "商家承担部分券", "打包袋金额", 
    "门店ID", "平台服务费", "用户ID", "满赠金额", "商家其他优惠", "新客减免金额", 
    "分摊比例", "门店性质", "企客后返", "配送平台", "退款数量", "城市名称", "订单编号"
]

# Dash版本字段映射（从智能门店看板_Dash版.py提取）
DASH_FIELD_MAPPING = {
    'order_id': '订单ID',
    'date': '下单时间/日期',
    'store_name': '门店名称',
    'product_name': '商品名称',
    'barcode': '条码',
    'store_code': '店内码',
    'price': '商品实售价',
    'original_price': '商品原价',
    'quantity': '销量/月售',
    'cost': '成本/商品采购成本',
    'profit': '利润额/实际利润',
    'category_level1': '一级分类名',
    'category_level3': '三级分类名',
    'remaining_stock': '剩余库存/库存',
    'delivery_fee': '物流配送费',
    'commission': '平台佣金',
    'platform_service_fee': '平台服务费',
    'user_paid_delivery_fee': '用户支付配送费',
    'delivery_discount': '配送费减免金额',
    'full_reduction': '满减金额',
    'product_discount': '商品减免金额',
    'merchant_voucher': '商家代金券',
    'merchant_share': '商家承担部分券',
    'packaging_fee': '打包袋金额',
    'gift_amount': '满赠金额',
    'other_merchant_discount': '商家其他优惠',
    'new_customer_discount': '新客减免金额',
    'corporate_rebate': '企客后返',
    'delivery_platform': '配送平台',
    'delivery_distance': '配送距离/distance',
    'store_id': '门店ID',
    'store_franchise_type': '门店加盟类型',
    'city': '城市',
    'address': '收货地址',
    'channel': '渠道',
    'actual_price': '实收价格',
    'amount': '预计订单收入/订单零售额',
}

# React版本字段映射（从data_management.py提取 - 修复后）
REACT_FIELD_MAPPING = {
    'order_id': '订单ID',
    'order_number': '订单编号',
    'date': '下单时间/日期',
    'store_name': '门店名称',
    'product_name': '商品名称',
    'channel': '渠道',
    'address': '收货地址',
    'category_level1': '一级分类名/一级分类',
    'category_level3': '三级分类名/三级分类',
    'price': '商品实售价',
    'original_price': '商品原价',
    'cost': '商品采购成本/成本',
    'actual_price': '实收价格',
    'quantity': '销量/月售',
    'stock': '库存',
    'remaining_stock': '剩余库存/库存',
    'amount': '预计订单收入/订单零售额/销售额',
    'profit': '利润额/实际利润/利润',
    'delivery_fee': '物流配送费',
    'commission': '平台佣金',
    'platform_service_fee': '平台服务费/平台佣金',
    'user_paid_delivery_fee': '用户支付配送费',
    'delivery_discount': '配送费减免金额',
    'full_reduction': '满减金额',
    'product_discount': '商品减免金额',
    'merchant_voucher': '商家代金券',
    'merchant_share': '商家承担部分券',
    'packaging_fee': '打包袋金额',
    'gift_amount': '满赠金额',
    'other_merchant_discount': '商家其他优惠',
    'new_customer_discount': '新客减免金额',
    'corporate_rebate': '企客后返',
    'delivery_distance': '配送距离',
    'delivery_platform': '配送平台',
    'store_id': '门店ID',
    'store_franchise_type': '门店加盟类型',
    'city': '城市名称/城市',
    'barcode': '条码',
    'store_code': '店内码',
}

def analyze_fields():
    print("=" * 80)
    print("完整字段对比分析：原始Excel vs Dash版本 vs React版本")
    print("=" * 80)
    
    # 1. Excel字段在Dash和React中的映射情况
    print("\n" + "=" * 80)
    print("1. 原始Excel字段映射对比")
    print("=" * 80)
    print(f"{'Excel字段':<20} {'Dash版本':<15} {'React版本':<15} {'状态':<10}")
    print("-" * 80)
    
    dash_excel_fields = set()
    react_excel_fields = set()
    
    for db_field, excel_field in DASH_FIELD_MAPPING.items():
        for ef in excel_field.split('/'):
            dash_excel_fields.add(ef.strip())
    
    for db_field, excel_field in REACT_FIELD_MAPPING.items():
        for ef in excel_field.split('/'):
            react_excel_fields.add(ef.strip())
    
    missing_in_both = []
    missing_in_react = []
    missing_in_dash = []
    
    for excel_field in EXCEL_FIELDS:
        in_dash = excel_field in dash_excel_fields
        in_react = excel_field in react_excel_fields
        
        dash_status = "✅" if in_dash else "❌"
        react_status = "✅" if in_react else "❌"
        
        if not in_dash and not in_react:
            status = "⚠️ 两者都缺"
            missing_in_both.append(excel_field)
        elif not in_react:
            status = "⚠️ React缺"
            missing_in_react.append(excel_field)
        elif not in_dash:
            status = "⚠️ Dash缺"
            missing_in_dash.append(excel_field)
        else:
            status = "✅ 一致"
        
        print(f"{excel_field:<20} {dash_status:<15} {react_status:<15} {status:<10}")
    
    # 2. 汇总
    print("\n" + "=" * 80)
    print("2. 汇总")
    print("=" * 80)
    
    print(f"\n原始Excel字段总数: {len(EXCEL_FIELDS)}")
    print(f"Dash版本映射字段数: {len(dash_excel_fields)}")
    print(f"React版本映射字段数: {len(react_excel_fields)}")
    
    if missing_in_both:
        print(f"\n⚠️ 两个版本都未映射的字段 ({len(missing_in_both)}个):")
        for f in missing_in_both:
            print(f"   - {f}")
    
    if missing_in_react:
        print(f"\n⚠️ React版本缺失的字段 ({len(missing_in_react)}个):")
        for f in missing_in_react:
            print(f"   - {f}")
    
    if missing_in_dash:
        print(f"\n⚠️ Dash版本缺失的字段 ({len(missing_in_dash)}个):")
        for f in missing_in_dash:
            print(f"   - {f}")
    
    # 3. 数据库字段对比
    print("\n" + "=" * 80)
    print("3. 数据库字段映射对比")
    print("=" * 80)
    
    all_db_fields = set(DASH_FIELD_MAPPING.keys()) | set(REACT_FIELD_MAPPING.keys())
    
    print(f"\n{'数据库字段':<25} {'Dash映射':<30} {'React映射':<30}")
    print("-" * 85)
    
    for db_field in sorted(all_db_fields):
        dash_map = DASH_FIELD_MAPPING.get(db_field, "❌ 未映射")
        react_map = REACT_FIELD_MAPPING.get(db_field, "❌ 未映射")
        print(f"{db_field:<25} {dash_map:<30} {react_map:<30}")
    
    # 4. React独有但Dash没有的字段
    react_only = set(REACT_FIELD_MAPPING.keys()) - set(DASH_FIELD_MAPPING.keys())
    dash_only = set(DASH_FIELD_MAPPING.keys()) - set(REACT_FIELD_MAPPING.keys())
    
    if react_only:
        print(f"\n✅ React版本独有的字段映射:")
        for f in react_only:
            print(f"   - {f}: {REACT_FIELD_MAPPING[f]}")
    
    if dash_only:
        print(f"\n⚠️ Dash版本有但React版本缺失的字段映射:")
        for f in dash_only:
            print(f"   - {f}: {DASH_FIELD_MAPPING[f]}")

if __name__ == "__main__":
    analyze_fields()
