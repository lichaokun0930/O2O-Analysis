import os
import datetime
import sys

LOG_FILE = "DEVELOPMENT_LOG.md"

TEMPLATE = """
## [{timestamp}] {title}

- **类型**: {type_icon} {type_name}
- **涉及文件**: `{files}`
- **问题/背景**: 
  > {description}
- **根本原因**: 
  {root_cause}
- **解决方案**: 
  {solution}
- **💡 避坑/经验**: 
  **{lesson}**

---
"""

TYPE_MAP = {
    "1": ("🐛", "Bug修复"),
    "2": ("✨", "新功能"),
    "3": ("♻️", "代码重构"),
    "4": ("📚", "文档/配置"),
    "5": ("🚀", "性能优化")
}

def init_log_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("# 🛠️ O2O看板开发日志 & 避坑指南\n\n")
            f.write("> 本文档记录开发过程中的关键变更、Bug修复及技术沉淀，用于后续查阅和避免重复踩坑。\n\n")
            f.write("---\n")
        print(f"✅ 已初始化日志文件: {LOG_FILE}")

def get_multiline_input(prompt):
    print(f"{prompt} (输入 'END' 结束，或直接回车单行输入):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        lines.append(line)
        if len(lines) == 1 and line.strip() != "":
            # 如果是单行输入且不是空行，允许直接结束（简单的用户体验优化）
            # 但为了支持多行，这里我们还是标准一点，或者检测空行
            pass 
    return "\n  ".join(lines) if lines else "无"

def add_entry():
    print("\n📝 **添加新的开发日志**")
    print("--------------------------------")
    
    # 1. 标题
    title = input("1. 输入标题 (例如: 修复下钻页面无数据): ").strip()
    if not title:
        print("❌ 标题不能为空")
        return

    # 2. 类型
    print("\n2. 选择变更类型:")
    for k, v in TYPE_MAP.items():
        print(f"   {k}. {v[0]} {v[1]}")
    type_choice = input("   请选择 (默认1): ").strip() or "1"
    type_icon, type_name = TYPE_MAP.get(type_choice, TYPE_MAP["1"])

    # 3. 涉及文件
    files = input("\n3. 涉及哪些文件 (逗号分隔): ").strip()

    # 4. 问题描述
    print("\n4. 问题描述/背景 (简述遇到的现象):")
    description = input("   > ").strip()

    # 5. 根本原因
    print("\n5. 根本原因 (技术层面的分析):")
    root_cause = input("   > ").strip()

    # 6. 解决方案
    print("\n6. 解决方案 (你做了什么修改):")
    solution = input("   > ").strip()

    # 7. 避坑指南
    print("\n7. 💡 避坑/经验 (给未来的自己一句话建议):")
    lesson = input("   > ").strip()

    # 生成内容
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = TEMPLATE.format(
        timestamp=timestamp,
        title=title,
        type_icon=type_icon,
        type_name=type_name,
        files=files,
        description=description,
        root_cause=root_cause,
        solution=solution,
        lesson=lesson
    )

    # 写入文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    
    print(f"\n✅ 日志已成功追加到 {LOG_FILE}")

def main():
    init_log_file()
    
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        add_entry()
    else:
        print("\n欢迎使用开发日志工具!")
        print("1. 添加新日志")
        print("2. 退出")
        choice = input("请选择: ")
        if choice == "1":
            add_entry()

if __name__ == "__main__":
    main()
