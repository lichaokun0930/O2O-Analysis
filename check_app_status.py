"""检查应用状态"""
import os

# 检查日志文件
log_file = "callback_debug.txt"
if os.path.exists(log_file):
    print(f"📋 找到调试日志文件: {log_file}")
    print("\n" + "="*80)
    print("最近的日志内容:")
    print("="*80)
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        # 显示最后50行
        for line in lines[-50:]:
            print(line.rstrip())
else:
    print(f"⚠️ 未找到调试日志文件: {log_file}")
    print("可能的原因：")
    print("1. 应用还未启动")
    print("2. 还没有点击'开始诊断'按钮")
    print("3. 回调函数没有被触发")
