"""
纯代码文件打包工具
只包含Python代码、配置文件、启动脚本和数据库文件
不包含任何说明文档和Markdown文件
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import zipfile

# 工作目录
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "数据库导出" / "纯代码交接包"

# 定义需要打包的文件（只包含代码和必需配置）
REQUIRED_FILES = {
    "核心程序": [
        # 主程序
        "智能门店看板_Dash版.py",
        "智能门店经营看板_可视化.py",
        "订单数据处理器.py",
        
        # 必需的依赖模块
        "scene_inference.py",
        "cache_utils.py",
        "echarts_responsive_utils.py",
        "ai_analyzer.py",
        "ai_business_context.py",
        "echarts_factory.py",
        "component_styles.py",
        "tab5_extended_renders.py",
        "商品场景智能打标引擎.py",
    ],
    
    "配置文件": [
        ".env",
        ".env.example",
        "requirements.txt",
        ".gitignore",
    ],
    
    "启动脚本": [
        "启动看板.bat",
        "启动数据库.ps1",
    ],
    
    "数据处理": [
        "真实数据处理器.py",
        "price_comparison_dashboard.py",
    ],
    
    "智能分析": [
        "自适应学习引擎.py",
        "增量学习优化器.py",
        "学习数据管理系统.py",
        "场景营销智能决策引擎.py",
        "商品分类结构分析.py",
    ],
}

def clean_output_dir():
    """清理输出目录"""
    if OUTPUT_DIR.exists():
        print(f"🗑️  清理旧的输出目录...")
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 创建输出目录: {OUTPUT_DIR}")

def copy_files():
    """复制所有必需的文件"""
    print("\n" + "="*60)
    print("📋 复制代码文件")
    print("="*60)
    
    copied_count = 0
    missing_files = []
    
    for category, files in REQUIRED_FILES.items():
        category_dir = OUTPUT_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📂 {category}:")
        for filename in files:
            src_path = BASE_DIR / filename
            dst_path = category_dir / filename
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                size_kb = src_path.stat().st_size / 1024
                print(f"  ✅ {filename} ({size_kb:.1f} KB)")
                copied_count += 1
            else:
                print(f"  ❌ {filename} [缺失]")
                missing_files.append(f"{category}/{filename}")
    
    return copied_count, missing_files

def copy_database_files():
    """复制数据库文件"""
    print("\n" + "="*60)
    print("📋 复制数据库文件")
    print("="*60)
    
    db_export_dir = BASE_DIR / "数据库导出"
    db_dest_dir = OUTPUT_DIR / "数据库文件"
    db_dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 只复制必需的数据库文件
    db_files = [
        "导入指南.txt",
        "导出数据库.py",
        "一键导出数据库.bat",
    ]
    
    # 找到最新的SQL文件
    sql_files = list(db_export_dir.glob("o2o_dashboard_full_*.sql"))
    if sql_files:
        latest_sql = max(sql_files, key=lambda p: p.stat().st_mtime)
        db_files.append(latest_sql.name)
    
    copied = 0
    print(f"\n📂 数据库文件:")
    for filename in db_files:
        src_path = db_export_dir / filename
        if src_path.exists():
            dst_path = db_dest_dir / filename
            shutil.copy2(src_path, dst_path)
            size_mb = src_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {filename} ({size_mb:.2f} MB)")
            copied += 1
    
    return copied

def create_minimal_readme():
    """创建极简README"""
    readme_content = """# 智能门店看板系统 - 纯代码包

## 快速启动

### 1. 导入数据库
```bash
# 参考 数据库文件/导入指南.txt
```

### 2. 配置环境
```bash
# 复制 .env.example 为 .env
# 修改数据库密码
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动系统
```bash
# Windows: 双击 启动看板.bat
# 或手动: python 智能门店看板_Dash版.py
```

访问: http://localhost:8050
"""
    
    readme_path = OUTPUT_DIR / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("\n✅ README.txt")

def create_file_list():
    """生成文件清单"""
    print("\n" + "="*60)
    print("📋 生成文件清单")
    print("="*60)
    
    file_list_content = ["# 纯代码交接包文件清单\n"]
    file_list_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    total_size = 0
    file_count = 0
    
    for category in sorted(OUTPUT_DIR.iterdir()):
        if category.is_dir():
            file_list_content.append(f"\n## {category.name}\n")
            
            for file_path in sorted(category.iterdir()):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size
                    file_count += 1
                    
                    if size > 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    else:
                        size_str = f"{size / 1024:.1f} KB"
                    
                    file_list_content.append(f"- {file_path.name} ({size_str})\n")
    
    file_list_content.append(f"\n---\n")
    file_list_content.append(f"**总计**: {file_count} 个文件, ")
    file_list_content.append(f"总大小: {total_size / (1024 * 1024):.2f} MB\n")
    
    list_path = OUTPUT_DIR / "文件清单.txt"
    with open(list_path, 'w', encoding='utf-8') as f:
        f.write(''.join(file_list_content))
    
    print("✅ 文件清单.txt")

def create_zip():
    """创建ZIP压缩包"""
    print("\n" + "="*60)
    print("📋 创建ZIP压缩包")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"纯代码交接包_{timestamp}.zip"
    zip_path = OUTPUT_DIR.parent / zip_name
    
    print(f"\n📦 正在压缩...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(OUTPUT_DIR.parent)
                zipf.write(file_path, arcname)
                print(f"  + {arcname}")
    
    zip_size = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ 压缩包已生成: {zip_name} ({zip_size:.2f} MB)")
    
    return zip_path, zip_size

def main():
    """主函数"""
    print("="*60)
    print("                📦 纯代码文件打包工具")
    print("="*60)
    
    # 清理输出目录
    clean_output_dir()
    
    # 复制文件
    copied_count, missing_files = copy_files()
    
    # 复制数据库文件
    db_count = copy_database_files()
    
    # 创建README
    create_minimal_readme()
    
    # 创建文件清单
    create_file_list()
    
    # 创建ZIP
    zip_path, zip_size = create_zip()
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 打包总结")
    print("="*60)
    
    print(f"\n✅ 打包完成!")
    print(f"\n📂 输出目录: {OUTPUT_DIR}")
    print(f"📦 压缩包: {zip_path}")
    print(f"\n📊 统计:")
    print(f"  - 代码文件: {copied_count}")
    print(f"  - 数据库文件: {db_count}")
    print(f"  - 总文件数: {copied_count + db_count + 2}")  # +2 为 README 和文件清单
    
    if missing_files:
        print(f"  - 缺失: {len(missing_files)}")
        print(f"  - 成功率: {copied_count/(copied_count+len(missing_files))*100:.1f}%")
    else:
        print(f"  - 成功率: 100%")
    
    print(f"\n💾 压缩包大小: {zip_size:.2f} MB")
    
    if missing_files:
        print(f"\n⚠️  缺失文件:")
        for f in missing_files:
            print(f"  - {f}")
    
    print("\n" + "="*60)
    print("🎉 纯代码交接包准备完成!")
    print("="*60)
    print(f"\n📋 下一步:")
    print(f"  1. 解压: {zip_path.name}")
    print(f"  2. 阅读: README.txt")
    print(f"  3. 按照说明导入数据库和启动系统")

if __name__ == "__main__":
    main()
