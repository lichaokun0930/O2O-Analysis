import pandas as pd

df = pd.read_excel("实际数据/祥和路.xlsx")
result = df['成本'].sum()

# 输出到文件
with open('成本验证结果.txt', 'w', encoding='utf-8') as f:
    f.write(f"源数据成本总和: {result:.2f}\n")
    f.write(f"总行数: {len(df)}\n")
    f.write(f"成本字段非空行数: {df['成本'].notna().sum()}\n")
    f.write(f"成本字段为0的行数: {(df['成本'] == 0).sum()}\n")

print(f"源数据成本总和: {result:.2f}")
print("结果已保存到: 成本验证结果.txt")
