"""
验证空态 Figure 修复质量
检查所有 Output(..., 'figure') 的回调是否使用了正确的空态返回值
"""

import re
import sys
from pathlib import Path

# 防止导入主文件时启动应用
sys.argv = ['验证脚本']

def verify_figure_returns():
    """验证所有 figure Output 的回调都使用了 create_empty_plotly_figure"""
    
    file_path = Path(__file__).parent / "智能门店看板_Dash版.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 70)
    print("🔍 验证空态 Figure 修复质量")
    print("=" * 70)
    
    # 1. 检查是否创建了 create_empty_plotly_figure 函数
    if 'def create_empty_plotly_figure' in content:
        print("✅ 1. create_empty_plotly_figure 函数已创建")
    else:
        print("❌ 1. 缺少 create_empty_plotly_figure 函数")
        return False
    
    # 2. 查找所有 Output(..., 'figure') 的回调
    figure_outputs = re.findall(r"Output\(['\"]([^'\"]+)['\"],\s*['\"]figure['\"]", content)
    print(f"\n📊 2. 找到 {len(figure_outputs)} 个 Output(..., 'figure') 回调:")
    for output_id in figure_outputs:
        print(f"   • {output_id}")
    
    # 3. 检查这些回调函数中是否还有使用 create_empty_figure
    issues = []
    
    # 查找所有回调函数定义
    callback_pattern = r'@app\.callback\((.*?)\)\s*def\s+(\w+)\((.*?)\):(.*?)(?=@app\.callback|if __name__|$)'
    callbacks = re.findall(callback_pattern, content, re.DOTALL)
    
    print(f"\n🔍 3. 检查回调函数中的空态返回值...")
    
    for callback_decorator, func_name, params, func_body in callbacks:
        # 检查这个回调是否有 Output(..., 'figure')
        if "Output" in callback_decorator and "'figure'" in callback_decorator:
            # 检查函数体中是否有 create_empty_figure (应该使用 create_empty_plotly_figure)
            if 'create_empty_figure(' in func_body and 'create_empty_plotly_figure' not in func_body:
                # 排除注释
                lines_with_issue = []
                for line in func_body.split('\n'):
                    if 'create_empty_figure(' in line and not line.strip().startswith('#'):
                        lines_with_issue.append(line.strip())
                
                if lines_with_issue:
                    issues.append({
                        'function': func_name,
                        'lines': lines_with_issue
                    })
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"\n   函数: {issue['function']}")
            for line in issue['lines']:
                print(f"      - {line}")
        return False
    else:
        print("   ✅ 所有 Output(..., 'figure') 回调都正确使用了 create_empty_plotly_figure")
    
    # 4. 统计使用情况
    plotly_count = len(re.findall(r'create_empty_plotly_figure\(', content))
    html_count = len(re.findall(r'create_empty_figure\(', content))
    
    print(f"\n📊 4. 使用统计:")
    print(f"   create_empty_plotly_figure: {plotly_count} 次")
    print(f"   create_empty_figure: {html_count} 次 (用于 children Output)")
    
    # 5. 检查 create_empty_plotly_figure 函数定义是否正确
    plotly_func_match = re.search(
        r'def create_empty_plotly_figure\((.*?)\):(.*?)(?=\ndef\s|\nclass\s|\n@|\nif __name__|$)',
        content,
        re.DOTALL
    )
    
    if plotly_func_match:
        func_body = plotly_func_match.group(2)
        checks = {
            'fig = go.Figure()': 'go.Figure()' in func_body,
            'add_annotation': 'add_annotation' in func_body,
            'update_layout': 'update_layout' in func_body,
            'return fig': 'return fig' in func_body
        }
        
        print(f"\n✅ 5. create_empty_plotly_figure 函数结构检查:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        if not all(checks.values()):
            return False
    
    print("\n" + "=" * 70)
    print("✅ 所有检查通过！空态 Figure 修复完成。")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    verify_figure_returns()
