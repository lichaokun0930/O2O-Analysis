import re

file = '智能门店看板_Dash版.py'
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有 calc_mode='all_with_fallback' 为 calc_mode='all_no_fallback'
new_content = content.replace("calc_mode='all_with_fallback'", "calc_mode='all_no_fallback'")

with open(file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ 替换完成!")
print(f"已将所有 calc_mode='all_with_fallback' 改为 calc_mode='all_no_fallback'")
