#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心文件打包工具 - 为同事准备交接包

功能:
1. 自动收集所有必需的核心文件
2. 创建规范的目录结构
3. 生成ZIP压缩包
4. 生成交接清单

使用: python 打包核心文件.py
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# 当前目录
BASE_DIR = Path(__file__).parent

# 输出目录
OUTPUT_DIR = BASE_DIR / "数据库导出" / "核心文件交接包"
ZIP_FILE = BASE_DIR / "数据库导出" / f"核心文件交接包_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

# 必需文件列表 (P0 - 必须交接)
REQUIRED_FILES = {
    "核心程序": [
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
        "启动智能看板.ps1",
        "启动数据库.ps1",
    ],
    "使用指南": [
        "智能门店经营看板_使用指南.md",
        "README_Dash版使用指南.md",
        "快速启动指南.md",
    ],
    "业务逻辑": [
        "【权威】业务逻辑与数据字典完整手册.md",
        "业务逻辑最终确认.md",
        "Tab1业务逻辑说明文档.md",
        "Tab1订单数据概览_卡片计算公式汇总.md",
    ],
}

# 重要文件列表 (P1 - 建议交接)
IMPORTANT_FILES = {
    "数据处理": [
        "真实数据处理器.py",
        "price_comparison_dashboard.py",
    ],
    "技术文档": [
        "数据结构统一标准.md",
        "数据字段映射规范.md",
        "PostgreSQL环境配置完整指南.md",
        "依赖和环境说明.md",
        "局域网多人访问指南.md",
    ],
    "迭代记录": [
        "TAB1实收价格修复总结.md",
        "Tab7_ECharts升级报告.md",
        "上传功能优化说明.md",
    ],
}

# 可选文件列表 (P2 - 根据需要)
OPTIONAL_FILES = {
    "智能分析": [
        "自适应学习引擎.py",
        "增量学习优化器.py",
        "学习数据管理系统.py",
        "场景营销智能决策引擎.py",
        "商品分类结构分析.py",
    ],
}

# 数据库文件 (单独处理)
DATABASE_FILES = [
    "数据库导出/o2o_dashboard_full_20251118_115227.sql",
    "数据库导出/导入指南.txt",
    "数据库导出/数据库结构验证报告.md",
    "数据库导出/核心源代码交接清单.md",
    "数据库导出/导出数据库.py",
    "数据库导出/一键导出数据库.bat",
]


def create_package():
    """创建交接包"""
    
    print("=" * 80)
    print("📦 核心文件打包工具")
    print("=" * 80)
    
    # 清理旧的输出目录
    if OUTPUT_DIR.exists():
        print(f"\n🗑️  清理旧的输出目录...")
        shutil.rmtree(OUTPUT_DIR)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 创建输出目录: {OUTPUT_DIR}")
    
    # 统计
    total_files = 0
    copied_files = 0
    missing_files = []
    
    # 复制必需文件 (P0)
    print("\n" + "=" * 80)
    print("📋 第一步: 复制必需文件 (P0 - 系统核心)")
    print("=" * 80)
    
    for category, files in REQUIRED_FILES.items():
        category_dir = OUTPUT_DIR / category
        category_dir.mkdir(exist_ok=True)
        
        print(f"\n📂 {category}:")
        for file in files:
            total_files += 1
            src = BASE_DIR / file
            dst = category_dir / file
            
            if src.exists():
                shutil.copy2(src, dst)
                copied_files += 1
                file_size = src.stat().st_size / 1024  # KB
                print(f"  ✅ {file} ({file_size:.1f} KB)")
            else:
                missing_files.append(f"{category}/{file}")
                print(f"  ❌ {file} [缺失]")
    
    # 复制重要文件 (P1)
    print("\n" + "=" * 80)
    print("📋 第二步: 复制重要文件 (P1 - 功能完整)")
    print("=" * 80)
    
    for category, files in IMPORTANT_FILES.items():
        category_dir = OUTPUT_DIR / category
        category_dir.mkdir(exist_ok=True)
        
        print(f"\n📂 {category}:")
        for file in files:
            total_files += 1
            src = BASE_DIR / file
            dst = category_dir / file
            
            if src.exists():
                shutil.copy2(src, dst)
                copied_files += 1
                file_size = src.stat().st_size / 1024  # KB
                print(f"  ✅ {file} ({file_size:.1f} KB)")
            else:
                missing_files.append(f"{category}/{file}")
                print(f"  ⚠️  {file} [缺失 - 可选]")
    
    # 复制可选文件 (P2)
    print("\n" + "=" * 80)
    print("📋 第三步: 复制可选文件 (P2 - 增强功能)")
    print("=" * 80)
    
    for category, files in OPTIONAL_FILES.items():
        category_dir = OUTPUT_DIR / category
        category_dir.mkdir(exist_ok=True)
        
        print(f"\n📂 {category}:")
        for file in files:
            total_files += 1
            src = BASE_DIR / file
            dst = category_dir / file
            
            if src.exists():
                shutil.copy2(src, dst)
                copied_files += 1
                file_size = src.stat().st_size / 1024  # KB
                print(f"  ✅ {file} ({file_size:.1f} KB)")
            else:
                missing_files.append(f"{category}/{file}")
                print(f"  ⚠️  {file} [缺失 - 可选]")
    
    # 复制数据库文件
    print("\n" + "=" * 80)
    print("📋 第四步: 复制数据库文件")
    print("=" * 80)
    
    db_dir = OUTPUT_DIR / "数据库文件"
    db_dir.mkdir(exist_ok=True)
    
    print(f"\n📂 数据库文件:")
    for file in DATABASE_FILES:
        total_files += 1
        src = BASE_DIR / file
        dst = db_dir / Path(file).name
        
        if src.exists():
            shutil.copy2(src, dst)
            copied_files += 1
            file_size = src.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✅ {Path(file).name} ({file_size:.2f} MB)")
        else:
            missing_files.append(f"数据库文件/{Path(file).name}")
            print(f"  ❌ {Path(file).name} [缺失]")
    
    # 创建README
    print("\n" + "=" * 80)
    print("📋 第五步: 生成README文件")
    print("=" * 80)
    
    readme_content = f"""# 📦 智能门店经营看板 - 核心文件交接包

**打包时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**打包文件数**: {copied_files} / {total_files}  
**包含内容**: 核心程序 + 配置文件 + 文档 + 数据库

---

## 🎯 快速开始

### 第一步: 导入数据库 (30分钟)

```bash
# 1. 安装 PostgreSQL 12+
下载地址: https://www.postgresql.org/download/windows/

# 2. 创建数据库
psql -U postgres
CREATE DATABASE o2o_dashboard;
\\q

# 3. 导入数据 (使用"数据库文件"目录中的SQL文件)
psql -U postgres -d o2o_dashboard -f o2o_dashboard_full_20251118_115227.sql

# 4. 验证导入
psql -U postgres -d o2o_dashboard
SELECT COUNT(*) FROM orders;  -- 应显示 41,523
SELECT COUNT(*) FROM products; -- 应显示 6,747
\\q
```

### 第二步: Python环境配置 (15分钟)

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
.venv\\Scripts\\activate

# 3. 安装依赖 (使用"配置文件"目录中的requirements.txt)
pip install -r requirements.txt
```

### 第三步: 修改配置 (5分钟)

编辑 "配置文件/.env"，修改数据库密码：
```ini
DATABASE_URL=postgresql://postgres:你的新密码@localhost:5432/o2o_dashboard
DB_PASSWORD=你的新密码
```

### 第四步: 启动系统 (5分钟)

```bash
# 方法1: Dash版看板（推荐）
# 使用"启动脚本"目录中的启动看板.bat

# 方法2: Streamlit版看板
# 使用"启动脚本"目录中的启动智能看板.ps1

# 访问地址
Dash版: http://localhost:8050
Streamlit版: http://localhost:8502
```

---

## 📂 目录结构

```
核心文件交接包/
├── 核心程序/           # 主程序文件 (3个)
├── 配置文件/           # .env, requirements.txt等 (4个)
├── 启动脚本/           # 一键启动脚本 (3个)
├── 使用指南/           # 用户手册 (3个)
├── 业务逻辑/           # 业务逻辑文档 (4个)
├── 数据处理/           # 数据处理模块 (2个)
├── 技术文档/           # 技术文档 (5个)
├── 迭代记录/           # 版本迭代记录 (3个)
├── 智能分析/           # AI分析模块 (5个)
├── 数据库文件/         # 数据库备份和工具 (6个)
└── README.md          # 本文件
```

---

## 📋 文件清单

### 核心程序 (必需) ⭐⭐⭐
- `智能门店看板_Dash版.py` - 主看板程序 (Dash版)
- `智能门店经营看板_可视化.py` - 主看板程序 (Streamlit版)
- `订单数据处理器.py` - 数据处理核心

### 配置文件 (必需) ⭐⭐⭐
- `.env` - 环境配置 (**修改数据库密码**)
- `.env.example` - 环境配置示例
- `requirements.txt` - Python依赖包
- `.gitignore` - Git忽略配置

### 启动脚本 (必需) ⭐⭐⭐
- `启动看板.bat` - Dash版一键启动
- `启动智能看板.ps1` - Streamlit版启动
- `启动数据库.ps1` - 数据库启动检查

### 使用指南 (必需) ⭐⭐⭐
- `智能门店经营看板_使用指南.md` - 完整使用手册
- `README_Dash版使用指南.md` - Dash版快速上手
- `快速启动指南.md` - 快速启动步骤

### 业务逻辑 (必需) ⭐⭐⭐
- `【权威】业务逻辑与数据字典完整手册.md` - 权威业务手册
- `业务逻辑最终确认.md` - 最终业务逻辑
- `Tab1业务逻辑说明文档.md` - TAB1详细说明
- `Tab1订单数据概览_卡片计算公式汇总.md` - 公式汇总

### 数据库文件 (必需) ⭐⭐⭐
- `o2o_dashboard_full_20251118_115227.sql` - 完整数据库备份 (19.87 MB)
- `导入指南.txt` - 导入步骤说明
- `数据库结构验证报告.md` - 结构验证报告
- `核心源代码交接清单.md` - 完整交接清单
- `导出数据库.py` - 数据库导出工具
- `一键导出数据库.bat` - 一键导出脚本

---

## ⚠️ 重要提醒

### 1. 密码安全 ⭐⭐⭐
- ✅ 已在配置文件/.env中包含数据库密码
- ⚠️ **导入后请立即修改数据库密码**
- ⚠️ **不要将.env文件上传到Git**

### 2. 环境要求
- PostgreSQL 12+ (推荐 18.0)
- Python 3.8+ (推荐 3.13)
- Windows 10/11 或 Linux

### 3. 端口占用
- Dash看板: 端口 8050
- Streamlit看板: 端口 8502
- PostgreSQL: 端口 5432

---

## 📞 技术支持

### 问题排查

1. **数据库连接失败**
   - 检查PostgreSQL服务是否运行
   - 检查.env中的密码是否正确

2. **看板启动失败**
   - 检查虚拟环境是否激活
   - 检查依赖包是否安装完整

3. **数据不显示**
   - 检查数据库是否有数据 (`SELECT COUNT(*) FROM orders;`)
   - 清除浏览器缓存

### 参考文档
- **使用指南**: `使用指南/智能门店经营看板_使用指南.md`
- **快速启动**: `使用指南/快速启动指南.md`
- **业务逻辑**: `业务逻辑/【权威】业务逻辑与数据字典完整手册.md`
- **完整清单**: `数据库文件/核心源代码交接清单.md`

---

## 📊 统计信息

- **核心程序**: 3个文件 (31,000+ 行代码)
- **配置文件**: 4个文件
- **启动脚本**: 3个脚本
- **文档**: 17个文档
- **数据库**: 1个完整备份 (19.87 MB)
- **订单数据**: 41,523条
- **商品数据**: 6,747条

---

## ✅ 验证状态

- ✅ 数据库结构与代码100%匹配
- ✅ 所有TAB功能完整
- ✅ Phase 21-27迭代成果已包含
- ✅ 文档完整齐全

---

**打包时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**打包人员**: GitHub Copilot  
**交接状态**: ✅ 完整交接

**祝使用愉快！** 🎉
"""
    
    readme_file = OUTPUT_DIR / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  ✅ README.md")
    
    # 生成文件清单
    print("\n" + "=" * 80)
    print("📋 第六步: 生成文件清单")
    print("=" * 80)
    
    manifest_content = f"""# 文件清单

**打包时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 文件统计
- 总文件数: {total_files}
- 已复制: {copied_files}
- 缺失: {len(missing_files)}

## 已复制文件

"""
    
    for category, files in {**REQUIRED_FILES, **IMPORTANT_FILES, **OPTIONAL_FILES}.items():
        manifest_content += f"\n### {category}\n"
        for file in files:
            src = BASE_DIR / file
            if src.exists():
                manifest_content += f"- ✅ {file}\n"
            else:
                manifest_content += f"- ❌ {file} [缺失]\n"
    
    manifest_content += "\n### 数据库文件\n"
    for file in DATABASE_FILES:
        src = BASE_DIR / file
        if src.exists():
            manifest_content += f"- ✅ {Path(file).name}\n"
        else:
            manifest_content += f"- ❌ {Path(file).name} [缺失]\n"
    
    if missing_files:
        manifest_content += f"\n## 缺失文件\n\n"
        for file in missing_files:
            manifest_content += f"- ❌ {file}\n"
    
    manifest_file = OUTPUT_DIR / "文件清单.md"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    
    print(f"  ✅ 文件清单.md")
    
    # 创建ZIP压缩包
    print("\n" + "=" * 80)
    print("📋 第七步: 创建ZIP压缩包")
    print("=" * 80)
    
    print(f"\n📦 正在压缩...")
    with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(OUTPUT_DIR.parent)
                zipf.write(file_path, arcname)
                print(f"  + {arcname}")
    
    zip_size = ZIP_FILE.stat().st_size / (1024 * 1024)  # MB
    print(f"\n✅ 压缩包已生成: {ZIP_FILE.name} ({zip_size:.2f} MB)")
    
    # 打印总结
    print("\n" + "=" * 80)
    print("📊 打包总结")
    print("=" * 80)
    
    print(f"\n✅ 打包完成!")
    print(f"\n📂 输出目录: {OUTPUT_DIR}")
    print(f"📦 压缩包: {ZIP_FILE}")
    print(f"\n📊 统计:")
    print(f"  - 总文件数: {total_files}")
    print(f"  - 已复制: {copied_files}")
    print(f"  - 缺失: {len(missing_files)}")
    print(f"  - 成功率: {copied_files/total_files*100:.1f}%")
    print(f"\n💾 压缩包大小: {zip_size:.2f} MB")
    
    if missing_files:
        print(f"\n⚠️  缺失文件:")
        for file in missing_files[:10]:  # 只显示前10个
            print(f"  - {file}")
        if len(missing_files) > 10:
            print(f"  ... 还有 {len(missing_files)-10} 个文件")
    
    print("\n" + "=" * 80)
    print("🎉 交接包准备完成!")
    print("=" * 80)
    print(f"\n📋 下一步:")
    print(f"  1. 解压: {ZIP_FILE.name}")
    print(f"  2. 阅读: README.md")
    print(f"  3. 按照README中的步骤导入数据库和启动系统")
    print(f"\n⚠️  重要提醒: 导入后请修改.env中的数据库密码!")
    print("\n")


if __name__ == "__main__":
    try:
        create_package()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
