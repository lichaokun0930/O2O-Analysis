# 清理旧的上传逻辑代码

# 读取文件内容
with open('智能门店经营看板_可视化.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到需要删除的旧代码范围
# 从第1042行到第1081行是旧的两门店上传逻辑
start_line = 1041  # 0-indexed, 对应第1042行
end_line = 1080    # 0-indexed, 对应第1081行

# 删除旧的上传逻辑，替换为新的比价结果文件上传界面
new_code = '''        st.write("**📊 比价结果文件分析**")
        st.info("🎯 上传通过比价脚本生成的完整比价结果Excel文件")
        
        comparison_file = st.file_uploader(
            "📤 选择比价结果Excel文件",
            type=['xlsx', 'xls'],
            help="上传通过 product_comparison_tool_local.py 生成的比价结果文件",
            key="comparison_file_uploader"
        )
        
        # 显示文件要求
        with st.expander("📋 比价结果文件说明"):
            st.markdown("""
            **支持的文件类型:**
            - ✅ 通过 `product_comparison_tool_local.py` 生成的比价结果文件
            - ✅ 文件名格式: `matched_products_comparison_final_YYYYMMDD_HHMMSS.xlsx`
            
            **文件应包含的Sheet:**
            - **1-条码精确匹配**: 条码相同的商品匹配结果
            - **2-名称模糊匹配(无条码)**: 基于商品名称的匹配结果  
            - **3-{店铺A}-独有商品**: 店铺A独有的商品
            - **4-{店铺B}-独有商品**: 店铺B独有的商品
            - **5-库存>0&A折扣≥B折扣**: 价格优势商品
            - **6-8**: 清洗数据对比Sheet(可选)
            
            **使用流程:**
            1. 🔧 先用比价脚本处理两个店铺的原始数据
            2. 📤 上传生成的比价结果Excel文件
            3. 📊 系统自动解析并展示可视化分析结果
            
            **注意事项:**
            - 确保文件是最新的比价结果
            - 检查各个Sheet是否包含有效数据
            - 支持中文商品名称和店铺名称
            """)

'''

# 重构代码数组
new_lines = lines[:start_line] + [new_code] + lines[end_line:]

# 写回文件
with open('智能门店经营看板_可视化.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'已删除第{start_line+1}到{end_line}行的旧上传逻辑代码')
print('已添加新的比价结果文件上传界面')
print('代码清理完成！')