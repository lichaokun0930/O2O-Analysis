# -*- coding: utf-8 -*-
"""
快速修复可视化界面的Streamlit兼容性问题
"""

import re

def fix_streamlit_compatibility():
    """修复Streamlit兼容性问题"""
    file_path = "智能门店经营看板_可视化.py"
    
    print("🔧 修复Streamlit兼容性问题...")
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换use_container_width参数
    replacements = [
        # plotly_chart的替换
        (r'st\.plotly_chart\(([^,]+),\s*use_container_width=True\)', 
         r'st.plotly_chart(\1, width="stretch", key=f"chart_{hash(\1)}")'),
        
        # dataframe的替换
        (r'st\.dataframe\(([^,]+),\s*use_container_width=True\)', 
         r'st.dataframe(\1, width="stretch")'),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
    
    # 手动替换一些具体的情况
    content = content.replace(
        'st.plotly_chart(fig, use_container_width=True)',
        'st.plotly_chart(fig, width="stretch", key=f"chart_{id(fig)}")'
    )
    
    content = content.replace(
        'st.dataframe(pricing_df, use_container_width=True)',
        'st.dataframe(pricing_df, width="stretch")'
    )
    
    content = content.replace(
        'st.dataframe(rec_df, use_container_width=True)',
        'st.dataframe(rec_df, width="stretch")'
    )
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 兼容性问题修复完成")
    print("💡 建议重启Streamlit应用")

if __name__ == "__main__":
    fix_streamlit_compatibility()