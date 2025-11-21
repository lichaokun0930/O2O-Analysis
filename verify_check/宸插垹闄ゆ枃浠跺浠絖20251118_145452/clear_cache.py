"""
清理Python缓存,确保使用最新代码
"""
import os
import shutil

print("=" * 60)
print("🧹 清理Python缓存")
print("=" * 60)

# 清理__pycache__
cache_dirs = []
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_dir = os.path.join(root, '__pycache__')
        cache_dirs.append(cache_dir)

if cache_dirs:
    print(f"\n找到 {len(cache_dirs)} 个缓存目录:")
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"   ✅ 已删除: {cache_dir}")
        except Exception as e:
            print(f"   ❌ 删除失败: {cache_dir} - {e}")
else:
    print("\n✅ 没有找到缓存目录")

# 清理.pyc文件
pyc_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc'):
            pyc_file = os.path.join(root, file)
            pyc_files.append(pyc_file)

if pyc_files:
    print(f"\n找到 {len(pyc_files)} 个.pyc文件:")
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"   ✅ 已删除: {pyc_file}")
        except Exception as e:
            print(f"   ❌ 删除失败: {pyc_file} - {e}")
else:
    print("\n✅ 没有找到.pyc文件")

print("\n" + "=" * 60)
print("✅ 缓存清理完成!")
print("=" * 60)
print("\n现在可以重新启动看板:")
print("   python 智能门店看板_Dash版.py")
