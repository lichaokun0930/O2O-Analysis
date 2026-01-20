"""
测试商品健康分析表格数据显示

验证V8.10.1修复：
1. 表格列定义正确传递
2. 表格数据正常显示
3. 样式配置正确应用
"""

import pandas as pd
from components.today_must_do.pagination_utils import create_paginated_datatable

print("=" * 80)
print("测试商品健康分析表格数据显示")
print("=" * 80)

# 创建测试数据
test_data = {
    '排名': [1, 2, 3],
    '商品名称': ['测试商品A', '测试商品B', '测试商品C'],
    '四象限分类': ['🌟 明星商品', '🔥 畅销商品', '💎 潜力商品'],
    '销量': ['100件', '80件', '60件'],
    '销售额': ['¥10,000', '¥8,000', '¥6,000'],
    '综合利润率': ['25.5%', '30.2%', '18.9%']
}

df = pd.DataFrame(test_data)

print(f"\n1️⃣ 测试数据:")
print(f"   行数: {len(df)}")
print(f"   列数: {len(df.columns)}")
print(f"   列名: {list(df.columns)}")
print(f"\n   数据预览:")
print(df.to_string(index=False))

# 创建自定义列定义
columns_def = [
    {'name': '排名', 'id': '排名'},
    {'name': '商品名称', 'id': '商品名称'},
    {'name': '六象限分类', 'id': '四象限分类'},  # 显示名称不同
    {'name': '销量', 'id': '销量'},
    {'name': '销售额', 'id': '销售额'},
    {'name': '综合利润率', 'id': '综合利润率'}
]

print(f"\n2️⃣ 自定义列定义:")
for col in columns_def:
    print(f"   显示名: '{col['name']}' -> 数据列: '{col['id']}'")

# 创建样式配置
style_data_conditional = [
    {'if': {'filter_query': '{四象限分类} contains "🌟 明星商品"', 'column_id': '四象限分类'}, 
     'color': '#52c41a', 'fontWeight': 'bold'},
    {'if': {'filter_query': '{四象限分类} contains "🔥 畅销商品"', 'column_id': '四象限分类'}, 
     'color': '#ff9800', 'fontWeight': 'bold'},
    {'if': {'filter_query': '{四象限分类} contains "💎 潜力商品"', 'column_id': '四象限分类'}, 
     'color': '#722ed1', 'fontWeight': 'bold'},
]

style_cell_conditional = [
    {'if': {'column_id': '排名'}, 'minWidth': '50px', 'width': '60px', 'textAlign': 'center'},
    {'if': {'column_id': '商品名称'}, 'minWidth': '120px', 'maxWidth': '250px'},
    {'if': {'column_id': '四象限分类'}, 'minWidth': '90px', 'maxWidth': '130px'},
]

print(f"\n3️⃣ 样式配置:")
print(f"   数据样式条件: {len(style_data_conditional)}个")
print(f"   单元格样式条件: {len(style_cell_conditional)}个")

# 测试创建分页表格
print(f"\n4️⃣ 创建分页表格...")
try:
    table = create_paginated_datatable(
        df=df,
        table_id='test-table',
        page_size=100,
        max_height='600px',
        enable_sort=True,
        enable_filter=False,
        columns=columns_def,
        style_data_conditional=style_data_conditional,
        style_cell_conditional=style_cell_conditional
    )
    print("   ✅ 表格创建成功")
    print(f"   类型: {type(table)}")
    
    # 检查表格组件
    if hasattr(table, 'children'):
        print(f"   子组件数量: {len(table.children) if isinstance(table.children, list) else 1}")
        
        # 查找DataTable组件
        from dash import dash_table
        for child in (table.children if isinstance(table.children, list) else [table.children]):
            if isinstance(child, dash_table.DataTable):
                print(f"\n   ✅ 找到DataTable组件:")
                print(f"      ID: {child.id}")
                print(f"      数据行数: {len(child.data) if child.data else 0}")
                print(f"      列数: {len(child.columns) if child.columns else 0}")
                if child.columns:
                    print(f"      列定义:")
                    for col in child.columns:
                        print(f"         {col}")
                break
    
except Exception as e:
    print(f"   ❌ 表格创建失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n5️⃣ 验证结果:")
print("   如果看到'✅ 表格创建成功'和'✅ 找到DataTable组件'，说明修复有效")
print("   如果数据行数>0且列定义正确，说明表格可以正常显示数据")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
