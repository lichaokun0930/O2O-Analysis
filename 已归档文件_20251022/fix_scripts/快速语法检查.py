"""
快速语法检查
验证修改后的代码没有语法错误
"""

import py_compile
import sys
from pathlib import Path

def check_syntax():
    """检查 Python 文件语法"""
    
    file_path = Path(__file__).parent / "智能门店看板_Dash版.py"
    
    print("=" * 70)
    print("🔍 Python 语法检查")
    print("=" * 70)
    print(f"文件: {file_path.name}")
    print()
    
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("✅ 语法检查通过！")
        print()
        print("=" * 70)
        print("✅ BUILD: PASS")
        print("=" * 70)
        return True
        
    except py_compile.PyCompileError as e:
        print(f"❌ 语法错误:")
        print(f"   文件: {e.file}")
        print(f"   行号: {e.msg}")
        print()
        print("=" * 70)
        print("❌ BUILD: FAIL")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = check_syntax()
    sys.exit(0 if success else 1)
