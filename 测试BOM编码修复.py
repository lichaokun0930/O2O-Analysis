"""
测试CSV导出BOM编码修复
验证Excel能否正确识别UTF-8 BOM编码的CSV文件
"""

import pandas as pd
from io import BytesIO

print("=" * 80)
print("📋 测试CSV导出BOM编码修复")
print("=" * 80)

# 1. 创建测试