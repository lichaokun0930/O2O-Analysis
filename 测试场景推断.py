"""
场景智能推断功能测试脚本
测试系统是否能正确推断各种消费场景
"""

import pandas as pd
from datetime import datetime

print("🔍🔍🔍 场景智能推断功能测试 🔍🔍🔍\n")
print("=" * 60)

# 模拟测试数据
test_data = [
    # 早餐场景
    {'下单时间': '2025-01-15 07:30:00', '商品名称': '豆浆', '一级分类名': '饮料', '三级分类名': '豆制品饮料', '时段': '清晨(6-9点)'},
    {'下单时间': '2025-01-15 08:00:00', '商品名称': '油条', '一级分类名': '速食', '三级分类名': '早点', '时段': '清晨(6-9点)'},
    {'下单时间': '2025-01-15 08:30:00', '商品名称': '包子', '一级分类名': '速食', '三级分类名': '早点', '时段': '清晨(6-9点)'},
    
    # 午餐场景
    {'下单时间': '2025-01-15 12:30:00', '商品名称': '盖浇饭', '一级分类名': '快餐', '三级分类名': '米饭类', '时段': '正午(12-14点)'},
    {'下单时间': '2025-01-15 13:00:00', '商品名称': '炒饭', '一级分类名': '快餐', '三级分类名': '米饭类', '时段': '正午(12-14点)'},
    
    # 下午茶场景
    {'下单时间': '2025-01-15 15:00:00', '商品名称': '奶茶', '一级分类名': '饮料', '三级分类名': '茶饮', '时段': '下午(14-18点)'},
    {'下单时间': '2025-01-15 15:30:00', '商品名称': '蛋糕', '一级分类名': '烘焙', '三级分类名': '甜点', '时段': '下午(14-18点)'},
    {'下单时间': '2025-01-15 16:00:00', '商品名称': '咖啡', '一级分类名': '饮料', '三级分类名': '咖啡', '时段': '下午(14-18点)'},
    
    # 晚餐场景
    {'下单时间': '2025-01-15 19:00:00', '商品名称': '火锅', '一级分类名': '餐饮', '三级分类名': '火锅', '时段': '傍晚(18-21点)'},
    {'下单时间': '2025-01-15 19:30:00', '商品名称': '烧烤', '一级分类名': '餐饮', '三级分类名': '烧烤', '时段': '傍晚(18-21点)'},
    
    # 夜宵场景
    {'下单时间': '2025-01-15 23:30:00', '商品名称': '小龙虾', '一级分类名': '海鲜', '三级分类名': '小龙虾', '时段': '晚间(21-24点)'},
    {'下单时间': '2025-01-16 01:00:00', '商品名称': '泡面', '一级分类名': '速食', '三级分类名': '方便面', '时段': '深夜(0-3点)'},
    
    # 零食场景
    {'下单时间': '2025-01-15 10:00:00', '商品名称': '薯片', '一级分类名': '休闲食品', '三级分类名': '膨化食品', '时段': '上午(9-12点)'},
    {'下单时间': '2025-01-15 14:00:00', '商品名称': '巧克力', '一级分类名': '休闲食品', '三级分类名': '糖果', '时段': '下午(14-18点)'},
    
    # 日用品场景
    {'下单时间': '2025-01-15 10:30:00', '商品名称': '纸巾', '一级分类名': '个护清洁', '三级分类名': '纸品', '时段': '上午(9-12点)'},
    {'下单时间': '2025-01-15 11:00:00', '商品名称': '洗洁精', '一级分类名': '个护清洁', '三级分类名': '清洁用品', '时段': '上午(9-12点)'},
    
    # 应急购买场景
    {'下单时间': '2025-01-15 22:00:00', '商品名称': '创可贴', '一级分类名': '医药', '三级分类名': '急救用品', '时段': '晚间(21-24点)'},
    {'下单时间': '2025-01-15 23:00:00', '商品名称': '口罩', '一级分类名': '个护清洁', '三级分类名': '防护用品', '时段': '晚间(21-24点)'},
]

df = pd.DataFrame(test_data)

# 场景推断函数（与主程序相同）
def infer_scene(row):
    """
    基于时段、商品名称、商品分类智能推断消费场景
    """
    time_slot = row.get('时段', '')
    product_name = str(row.get('商品名称', '')).lower()
    category_1 = str(row.get('一级分类名', '')).lower()
    category_3 = str(row.get('三级分类名', '')).lower()
    
    # === 1. 基于商品名称关键词（最精准）===
    
    # 早餐关键词
    breakfast_keywords = ['豆浆', '油条', '包子', '粥', '鸡蛋', '煎饼', '馒头', '早餐', '稀饭']
    if any(kw in product_name for kw in breakfast_keywords):
        return '早餐'
    
    # 午餐关键词
    lunch_keywords = ['盖浇饭', '快餐', '便当', '炒饭', '面条', '米线', '盒饭', '套餐', '工作餐']
    if any(kw in product_name for kw in lunch_keywords) and ('12' in time_slot or '正午' in time_slot or '下午' in time_slot):
        return '午餐'
    
    # 晚餐关键词
    dinner_keywords = ['晚餐', '炒菜', '火锅', '烧烤', '聚餐']
    if any(kw in product_name for kw in dinner_keywords):
        return '晚餐'
    
    # 夜宵关键词
    midnight_keywords = ['夜宵', '小龙虾', '泡面', '方便面', '啤酒', '炸鸡']
    if any(kw in product_name for kw in midnight_keywords) and ('深夜' in time_slot or '晚间' in time_slot or '凌晨' in time_slot):
        return '夜宵'
    
    # 下午茶关键词
    tea_keywords = ['奶茶', '咖啡', '蛋糕', '甜点', '面包', '饼干', '冰淇淋', '果汁']
    if any(kw in product_name for kw in tea_keywords) and '下午' in time_slot:
        return '下午茶'
    
    # 零食/休闲关键词
    snack_keywords = ['薯片', '糖果', '巧克力', '坚果', '瓜子', '零食']
    if any(kw in product_name for kw in snack_keywords):
        return '休闲零食'
    
    # 日用品关键词
    daily_keywords = ['纸巾', '洗洁精', '垃圾袋', '牙膏', '洗发水', '沐浴露', '洗衣液']
    if any(kw in product_name for kw in daily_keywords):
        return '日用补充'
    
    # 应急/突发关键词
    emergency_keywords = ['电池', '创可贴', '药', '消毒', '口罩', '卫生巾']
    if any(kw in product_name for kw in emergency_keywords):
        return '应急购买'
    
    # === 2. 基于商品分类（中等精准）===
    
    # 烟酒分类
    if '烟酒' in category_1 or '烟' in category_3 or '酒' in category_3:
        if '深夜' in time_slot or '晚间' in time_slot:
            return '夜间社交'
        return '社交娱乐'
    
    # 饮料分类
    if '饮料' in category_1 or '饮品' in category_3:
        if '下午' in time_slot:
            return '下午茶'
        elif '深夜' in time_slot or '晚间' in time_slot:
            return '夜间饮品'
        return '日常饮品'
    
    # 乳品分类
    if '乳品' in category_1 or '奶' in category_3:
        if '清晨' in time_slot:
            return '早餐'
        return '营养补充'
    
    # 粮油调味分类
    if '粮油' in category_1 or '调味' in category_1:
        return '家庭烹饪'
    
    # 休闲食品分类
    if '休闲' in category_1 or '零食' in category_3:
        return '休闲零食'
    
    # 个护清洁分类
    if '个护' in category_1 or '清洁' in category_1 or '日化' in category_1:
        return '日用补充'
    
    # === 3. 基于时段（兜底方案）===
    
    time_to_scene = {
        '清晨(6-9点)': '早餐',
        '上午(9-12点)': '日常购物',
        '正午(12-14点)': '午餐',
        '下午(14-18点)': '下午茶',
        '傍晚(18-21点)': '晚餐',
        '晚间(21-24点)': '居家消费',
        '深夜(0-3点)': '夜宵',
        '凌晨(3-6点)': '应急购买'
    }
    
    return time_to_scene.get(time_slot, '日常购物')

# 应用场景推断
df['推断场景'] = df.apply(infer_scene, axis=1)

print("测试数据推断结果：\n")
print(df[['下单时间', '商品名称', '时段', '推断场景']].to_string(index=False))

print("\n" + "=" * 60)
print("\n场景分布统计：\n")
scene_counts = df['推断场景'].value_counts()
for scene, count in scene_counts.items():
    print(f"  {scene}: {count} 个订单")

print("\n" + "=" * 60)
print("\n✅ 测试完成！")
print("\n场景推断逻辑：")
print("  1. 🎯 优先级1：商品名称关键词（最精准）")
print("  2. 🏷️ 优先级2：商品分类（中等精准）")
print("  3. ⏰ 优先级3：时段兜底（保证覆盖）")
print("\n覆盖场景：")
all_scenes = set(df['推断场景'].unique())
print(f"  共识别 {len(all_scenes)} 种场景：{', '.join(sorted(all_scenes))}")
