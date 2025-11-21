#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时监控日志文件"""

import time
import sys
from pathlib import Path

log_file = Path(__file__).parent / "dash_debug.log"

print(f"📊 开始监控日志文件: {log_file}")
print("=" * 80)

# 记录已读取的位置
last_position = 0

if log_file.exists():
    # 先读取现有内容
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        print(content)
        last_position = f.tell()

print("\n🔍 等待新日志输出...\n")
print("=" * 80)

try:
    while True:
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(last_position)
                new_content = f.read()
                if new_content:
                    print(new_content, end='', flush=True)
                    last_position = f.tell()
        time.sleep(0.5)  # 每0.5秒检查一次
except KeyboardInterrupt:
    print("\n\n⏹️  监控已停止")
