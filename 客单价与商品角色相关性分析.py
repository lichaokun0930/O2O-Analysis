"""
客单价与商品角色相关性分析
使用统计学方法验证商品角色对客单价的影响
"""
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# 加载数据
print("="*60)
print("客单价与商品角色相关性分析")
print("="*60)

df = pd.read_excel('门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx')
df['下单时间'] = pd.to_datetime(df['下单时间'])

print(f"\n[OK] 数据加载完成，共 {len(df)} 行")
print(f"[INFO] 日期范围: {df['下单时间'].min()} ~ {df['下单时间'].max()}")

# 添加商品角色字段（根据订单内价格最高的商品判定）
if '商品实售价' in df.columns and '订单ID' in df.columns:
    max_price_per_order = df.groupby('订单ID')['商品实售价'].transform('max')
    df['商品角色'] = np.where(df['商品实售价'] == max_price_per_order, '主力品', '凑单品')
    print(f"[OK] 已添加商品角色字段（主力品=订单内最高价商品，其余为凑单品）")
else:
    print("[ERROR] 缺少必要字段：订单ID 或 商品实售价")
    exit(1)

# 1. 计算每个订单的客单价和商品角色分布
print("\n" + "="*60)
print("1. 订单级分析：计算客单价与商品角色占比")
print("="*60)

# 按订单分组
order_analysis = []
for order_id, order_data in df.groupby('订单ID'):
    # 客单价（订单总金额）
    order_total = order_data['商品实售价'].sum()
    
    # 商品角色统计
    role_counts = order_data['商品角色'].value_counts()
    total_items = len(order_data)
    
    # 计算各角色占比
    main_ratio = role_counts.get('主力品', 0) / total_items  # 主力品占比
    addon_ratio = role_counts.get('凑单品', 0) / total_items  # 凑单品占比
    other_ratio = 1 - main_ratio - addon_ratio  # 其他占比
    
    # 计算各角色贡献金额
    main_amount = order_data[order_data['商品角色'] == '主力品']['商品实售价'].sum() if '主力品' in role_counts else 0
    addon_amount = order_data[order_data['商品角色'] == '凑单品']['商品实售价'].sum() if '凑单品' in role_counts else 0
    
    order_analysis.append({
        '订单ID': order_id,
        '客单价': order_total,
        '商品数量': total_items,
        '主力品数量': role_counts.get('主力品', 0),
        '凑单品数量': role_counts.get('凑单品', 0),
        '主力品占比': main_ratio,
        '凑单品占比': addon_ratio,
        '主力品金额': main_amount,
        '凑单品金额': addon_amount,
        '主力品金额占比': main_amount / order_total if order_total > 0 else 0,
        '凑单品金额占比': addon_amount / order_total if order_total > 0 else 0
    })

order_df = pd.DataFrame(order_analysis)
print(f"\n[OK] 分析了 {len(order_df)} 个订单")
print(f"[DATA] 平均客单价: {order_df['客单价'].mean():.2f} 元")
print(f"[DATA] 平均商品数量: {order_df['商品数量'].mean():.2f}")
print(f"[DATA] 平均主力品占比: {order_df['主力品占比'].mean()*100:.1f}%")
print(f"[DATA] 平均凑单品占比: {order_df['凑单品占比'].mean()*100:.1f}%")

# 2. 相关性分析
print("\n" + "="*60)
print("2. 相关性分析（Pearson相关系数）")
print("="*60)

# 2.1 主力品数量占比 vs 客单价
corr_main_ratio, p_main_ratio = stats.pearsonr(order_df['主力品占比'], order_df['客单价'])
print(f"\n[ANALYSIS] 主力品占比 vs 客单价:")
print(f"   相关系数: {corr_main_ratio:.4f}")
print(f"   P值: {p_main_ratio:.6f}")
print(f"   显著性: {'[YES] 显著相关 (p<0.05)' if p_main_ratio < 0.05 else '[NO] 不显著 (p>=0.05)'}")

# 2.2 凑单品数量占比 vs 客单价
corr_addon_ratio, p_addon_ratio = stats.pearsonr(order_df['凑单品占比'], order_df['客单价'])
print(f"\n[ANALYSIS] 凑单品占比 vs 客单价:")
print(f"   相关系数: {corr_addon_ratio:.4f}")
print(f"   P值: {p_addon_ratio:.6f}")
print(f"   显著性: {'[YES] 显著相关 (p<0.05)' if p_addon_ratio < 0.05 else '[NO] 不显著 (p>=0.05)'}")

# 2.3 主力品金额占比 vs 客单价
corr_main_amount, p_main_amount = stats.pearsonr(order_df['主力品金额占比'], order_df['客单价'])
print(f"\n[ANALYSIS] 主力品金额占比 vs 客单价:")
print(f"   相关系数: {corr_main_amount:.4f}")
print(f"   P值: {p_main_amount:.6f}")
print(f"   显著性: {'[YES] 显著相关 (p<0.05)' if p_main_amount < 0.05 else '[NO] 不显著 (p>=0.05)'}")

# 3. 分组对比分析（高主力品 vs 低主力品）
print("\n" + "="*60)
print("3. 分组对比分析（T检验）")
print("="*60)

# 按主力品占比分组（中位数分割）
median_main = order_df['主力品占比'].median()
high_main = order_df[order_df['主力品占比'] >= median_main]
low_main = order_df[order_df['主力品占比'] < median_main]

print(f"\n分组标准：主力品占比中位数 = {median_main*100:.1f}%")
print(f"高主力品组：{len(high_main)} 个订单（主力品占比 ≥ {median_main*100:.1f}%）")
print(f"低主力品组：{len(low_main)} 个订单（主力品占比 < {median_main*100:.1f}%）")

# T检验
t_stat, p_value = stats.ttest_ind(high_main['客单价'], low_main['客单价'])
print(f"\n[DATA] 客单价对比:")
print(f"   高主力品组平均客单价: {high_main['客单价'].mean():.2f} 元")
print(f"   低主力品组平均客单价: {low_main['客单价'].mean():.2f} 元")
print(f"   差异: {high_main['客单价'].mean() - low_main['客单价'].mean():.2f} 元")
print(f"   T统计量: {t_stat:.4f}")
print(f"   P值: {p_value:.6f}")
print(f"   结论: {'[YES] 两组客单价有显著差异 (p<0.05)' if p_value < 0.05 else '[NO] 无显著差异 (p>=0.05)'}")

# 4. 回归分析（多元线性回归）
print("\n" + "="*60)
print("4. 多元线性回归分析")
print("="*60)

# 构建特征矩阵
X = order_df[['主力品占比', '凑单品占比', '商品数量']]
y = order_df['客单价']

# 训练模型
model = LinearRegression()
model.fit(X, y)
y_pred = model.predict(X)

# 模型评估
r2 = r2_score(y, y_pred)
print(f"\n[MODEL] 回归模型性能:")
print(f"   R² (决定系数): {r2:.4f}")
print(f"   解释力: {r2*100:.2f}% 的客单价变化可由这些因素解释")

print(f"\n[COEF] 回归系数（影响程度）:")
print(f"   主力品占比系数: {model.coef_[0]:.2f}")
print(f"     -> 主力品占比每提升1%，客单价预期增加 {model.coef_[0]/100:.2f} 元")
print(f"   凑单品占比系数: {model.coef_[1]:.2f}")
print(f"     -> 凑单品占比每提升1%，客单价预期变化 {model.coef_[1]/100:.2f} 元")
print(f"   商品数量系数: {model.coef_[2]:.2f}")
print(f"     -> 每增加1个商品，客单价预期增加 {model.coef_[2]:.2f} 元")
print(f"   截距: {model.intercept_:.2f}")

# 5. 结论与建议
print("\n" + "="*60)
print("5. 统计结论与业务建议")
print("="*60)

print(f"""
【核心发现】：

1. **相关性验证**：
   - 主力品占比与客单价的相关系数为 {corr_main_ratio:.3f}
   - {'[YES] 显著正相关' if corr_main_ratio > 0 and p_main_ratio < 0.05 else '[NO] 关系不显著'}
   - 凑单品占比与客单价的相关系数为 {corr_addon_ratio:.3f}
   - {'[YES] 显著负相关' if corr_addon_ratio < 0 and p_addon_ratio < 0.05 else '[NO] 关系不显著'}

2. **分组对比**：
   - 高主力品订单平均客单价: {high_main['客单价'].mean():.2f} 元
   - 低主力品订单平均客单价: {low_main['客单价'].mean():.2f} 元
   - 差异: {high_main['客单价'].mean() - low_main['客单价'].mean():.2f} 元
   - {'[YES] 统计显著差异 (p<0.05)' if p_value < 0.05 else '[NO] 差异不显著'}

3. **回归分析**：
   - 模型解释力 (R²): {r2:.2%}
   - 主力品占比每提升10%，客单价预期增加约 {model.coef_[0]*0.1:.2f} 元

【业务建议】：

{'[建议] 单独分析商品角色：' if abs(corr_main_ratio) > 0.3 or abs(corr_addon_ratio) > 0.3 else '[警告] 商品角色影响不显著：'}
   
   1. 在客单价归因分析中，增加"按商品角色分组"的分析维度
   2. 对比不同商品角色占比下的客单价变化趋势
   3. 识别"主力品流失"导致的客单价下滑场景
   4. 监控"凑单品泛滥"对客单价的稀释效应
   
   具体实施：
   - 计算每个周期的主力品占比、凑单品占比
   - 分析客单价下滑时，商品角色结构的变化
   - 给出针对性建议（如"增加主力品促销"、"控制凑单品比例"）
""")

print("\n分析完成！")
