import os
import shutil
from pathlib import Path

print("="*80)
print("🧹 清理看板缓存数据")
print("="*80)

cache_dirs = [
    Path("学习数据仓库/uploaded_data"),
    Path("学习数据仓库/cache"),
    Path("__pycache__")
]

for cache_dir in cache_dirs:
    if cache_dir.exists():
        try:
            file_count = len(list(cache_dir.rglob('*')))
            print(f"\n📁 清理目录: {cache_dir}")
            print(f"   文件数: {file_count}")
            
            # 删除所有文件但保留目录结构
            for item in cache_dir.rglob('*'):
                if item.is_file():
                    try:
                        item.unlink()
                        print(f"   ✅ 删除: {item.name}")
                    except Exception as e:
                        print(f"   ❌ 删除失败: {item.name} - {e}")
                        
            print(f"   ✅ {cache_dir} 清理完成")
        except Exception as e:
            print(f"   ❌ 清理失败: {e}")
    else:
        print(f"\n⏭️  跳过(不存在): {cache_dir}")

print("\n" + "="*80)
print("✅ 缓存清理完成!")
print("="*80)
print("\n📝 下一步操作:")
print("   1. 重启看板: python 智能门店看板_Dash版.py")
print("   2. 重新上传祥和路.xlsx")
print("   3. 查看利润是否更新为¥23,800左右")
