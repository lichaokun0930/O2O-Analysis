import os
import datetime
import time

def scan_today_changes(directory="."):
    today = datetime.date.today()
    print(f"🔍 正在扫描 {today} 修改过的文件...\n")
    
    changed_files = []
    
    exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache'}
    exclude_extensions = {'.pyc', '.log', '.tmp'}

    for root, dirs, files in os.walk(directory):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in exclude_extensions):
                continue
                
            file_path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(file_path)
                mtime_date = datetime.date.fromtimestamp(mtime)
                
                if mtime_date == today:
                    # 获取相对路径
                    rel_path = os.path.relpath(file_path, directory)
                    # 排除日志文件本身
                    if "DEVELOPMENT_LOG.md" in rel_path:
                        continue
                    changed_files.append((rel_path, datetime.datetime.fromtimestamp(mtime)))
            except Exception:
                continue

    if not changed_files:
        print("今天没有检测到文件变动。")
        return

    print(f"✅ 发现 {len(changed_files)} 个文件变动:\n")
    
    # 按时间排序
    changed_files.sort(key=lambda x: x[1], reverse=True)
    
    for f, t in changed_files:
        time_str = t.strftime("%H:%M:%S")
        print(f"- [{time_str}] {f}")

    print("\n💡 提示: 您可以将此列表复制给 Copilot，让我帮您生成开发日志。")

if __name__ == "__main__":
    scan_today_changes()
