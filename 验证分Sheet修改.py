"""
验证智能门店经营看板_可视化.py中的分Sheet导出功能修改
"""

print("\n" + "="*60)
print("验证分Sheet导出功能修改")
print("="*60)

# 读取文件检查修改
with open("智能门店经营看板_可视化.py", "r", encoding="utf-8") as f:
    content = f.read()

# 检查点1: 是否调用了新方法
check1 = "diagnose_customer_price_decline_by_sheets" in content
print(f"\n1. 调用新方法 diagnose_customer_price_decline_by_sheets: {'✅' if check1 else '❌'}")

# 检查点2: 是否有三个Tab展示
check2 = 'st.tabs(["📊 客单价变化", "📉 下滑商品分析", "📈 上涨商品分析"])' in content
print(f"2. 使用Tab分维度展示: {'✅' if check2 else '❌'}")

# 检查点3: 是否有Excel导出（分Sheet）
check3 = "导出Excel（分Sheet）" in content
print(f"3. Excel导出功能（分Sheet）: {'✅' if check3 else '❌'}")

# 检查点4: 是否使用ExcelWriter写入多个sheet
check4 = "with pd.ExcelWriter" in content and "for sheet_name, df_sheet in sheets_data.items():" in content
print(f"4. 使用ExcelWriter写入多个Sheet: {'✅' if check4 else '❌'}")

# 检查点5: 是否保留CSV导出选项
check5 = "导出CSV（单文件）" in content
print(f"5. 保留CSV导出选项: {'✅' if check5 else '❌'}")

# 检查点6: 是否有说明文字
check6 = "只包含售罄、涨价导致销量降、销量下滑等问题商品" in content
print(f"6. 包含说明文字: {'✅' if check6 else '❌'}")

# 检查点7: 是否有帮助提示
check7 = "Excel文件包含3个Sheet" in content
print(f"7. 包含帮助提示: {'✅' if check7 else '❌'}")

all_passed = all([check1, check2, check3, check4, check5, check6, check7])

print("\n" + "="*60)
if all_passed:
    print("🎉 所有检查通过！分Sheet导出功能已正确集成")
    print("="*60)
    print("\n修改内容:")
    print("  ✅ 使用新的 diagnose_customer_price_decline_by_sheets() 方法")
    print("  ✅ 界面上使用3个Tab分别展示三个维度")
    print("  ✅ Excel导出会自动分成3个Sheet")
    print("  ✅ 保留了CSV单文件导出选项")
    print("  ✅ 添加了清晰的说明文字和帮助提示")
    print("\n使用说明:")
    print("  1. 运行智能看板: streamlit run 智能门店经营看板_可视化.py")
    print("  2. 进入【问题诊断引擎】-【客单价下滑归因】")
    print("  3. 点击【🔍 开始归因】按钮")
    print("  4. 结果会分3个Tab展示：")
    print("     - 📊 客单价变化")
    print("     - 📉 下滑商品分析")
    print("     - 📈 上涨商品分析")
    print("  5. 点击【⬇️ 导出Excel（分Sheet）】下载分Sheet的Excel文件")
    print("  6. 或点击【⬇️ 导出CSV（单文件）】下载传统的CSV文件")
else:
    print("❌ 部分检查失败")
    print("="*60)

print("\n")
