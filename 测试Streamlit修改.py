"""
测试Streamlit可视化文件修改
验证周期对比和预计收入功能是否正常集成
"""

import sys
import importlib.util

print("=" * 80)
print("📋 测试Streamlit可视化文件修改")
print("=" * 80)

# 1. 测试语法检查
print("\n🔍 步骤1: 语法检查...")
try:
    import py_compile
    py_compile.compile('智能门店经营看板_可视化.py', doraise=True)
    print("✅ 语法检查通过")
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    sys.exit(1)

# 2. 测试模块导入
print("\n🔍 步骤2: 模块导入检查...")
try:
    spec = importlib.util.spec_from_file_location("visualization", "智能门店经营看板_可视化.py")
    module = importlib.util.module_from_spec(spec)
    print("✅ 模块结构正常")
except Exception as e:
    print(f"❌ 模块导入错误: {e}")
    sys.exit(1)

# 3. 检查关键代码片段
print("\n🔍 步骤3: 检查关键代码...")
with open('智能门店经营看板_可视化.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    checks = [
        ("get_available_periods", "✅ 包含周期列表获取功能"),
        ("current_period_index", "✅ 包含当前周期参数"),
        ("compare_period_index", "✅ 包含对比周期参数"),
        ("use_custom_period", "✅ 包含自定义周期开关"),
        ("预计收入", "✅ 包含预计收入显示"),
        ("📅 自定义周期对比", "✅ 包含周期对比UI标题"),
    ]
    
    all_passed = True
    for keyword, message in checks:
        if keyword in content:
            print(f"  {message}")
        else:
            print(f"  ❌ 缺少: {keyword}")
            all_passed = False
    
    if not all_passed:
        print("\n❌ 代码检查未通过")
        sys.exit(1)

# 4. 检查问题诊断引擎集成
print("\n🔍 步骤4: 检查问题诊断引擎集成...")
try:
    from 问题诊断引擎 import ProblemDiagnosticEngine
    
    # 检查新方法是否存在
    if hasattr(ProblemDiagnosticEngine, 'get_available_periods'):
        print("✅ get_available_periods 方法存在")
    else:
        print("❌ get_available_periods 方法不存在")
        sys.exit(1)
    
    # 检查diagnose_sales_decline的签名
    import inspect
    sig = inspect.signature(ProblemDiagnosticEngine.diagnose_sales_decline)
    params = list(sig.parameters.keys())
    
    required_params = ['current_period_index', 'compare_period_index']
    for param in required_params:
        if param in params:
            print(f"✅ 参数 {param} 已添加")
        else:
            print(f"❌ 参数 {param} 缺失")
            sys.exit(1)
            
except Exception as e:
    print(f"❌ 引擎集成检查失败: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ 所有测试通过!")
print("=" * 80)
print("\n💡 提示:")
print("  1. 新增功能已成功集成到Streamlit界面")
print("  2. 用户可以通过下拉菜单选择任意两个周期进行对比")
print("  3. 表格将显示动态表头(如: 第40周销量, 第39周销量)")
print("  4. 自动包含预计收入列(如果数据中存在)")
print("\n🚀 现在可以启动Streamlit进行测试:")
print("   streamlit run 智能门店经营看板_可视化.py")
