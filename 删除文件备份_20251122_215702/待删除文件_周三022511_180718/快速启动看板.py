#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动看板 - 测试数据库数据加载
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置环境变量强制使用数据库
import os
os.environ['USE_DATABASE'] = '1'

# 启动看板
from 智能门店看板_Dash版 import app

if __name__ == '__main__':
    print("=" * 80)
    print("启动智能看板 - 数据库模式")
    print("=" * 80)
    print("浏览器访问: http://127.0.0.1:8050")
    print("=" * 80)
    
    app.run_server(debug=False, host='127.0.0.1', port=8050)
