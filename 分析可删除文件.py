#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目文件清理分析工具
分析哪些文件可以安全删除
"""
import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 核心运行文件（绝对不能删除）
CORE_FILES = {
    '智能门店看板_Dash版.py',
    'requirements.txt',
    'README.md',
    '.gitignore',
    '.env.example',
    '启动看板.ps1',
    '启动看板.bat',
}

# 核心模块（被主程序导入）
CORE_MODULES = {
    'ai_analyzer.py',
    'ai_business_context.py',
    'ai_pandasai_integration.py',
    'ai_qwen_service.py',
    'background_tasks.py',
    'cache_utils.py',
    'component_styles.py',
    'echarts_factory.py',
    'echarts_responsive_utils.py',
    'hierarchical_cache_manager.py',
    'loading_components.py',
    'redis_cache_manager.py',
    'redis_config.py',
    'redis_health_monitor.py',
    'scene_inference.py',
    'tab5_extended_renders.py',
    '真实数据处理器.py',
    '科学八象限分析器.py',
    '评分模型分析器.py',
    '商品场景智能打标引擎.py',
}

# 核心目录（不能删除）
CORE_DIRS = {
    'components',
    'database',
    'assets',
    '.venv',
    '__pycache__',
    '.git',
}

def analyze_files():
    """分析项目文件"""
    
    results = {
        '可以删除的文档': [],
        '可以删除的测试脚本': [],
        '可以删除的旧版本文档': [],
        '可以删除的临时文件': [],
        '可以删除的备份文件': [],
        '可以删除的诊断工具': [],
        '可以删除的安装脚本': [],
        '可以删除的Git脚本': [],
        '可以归档的历史文档': [],
        '核心文件（保留）': [],
        '数据文件（保留）': [],
    }
    
    # 遍历项目文件
    for file_path in PROJECT_ROOT.rglob('*'):
        if file_path.is_dir():
            continue
            
        # 跳过特定目录
        if any(part in CORE_DIRS for part in file_path.parts):
            continue
            
        rel_path = file_path.relative_to(PROJECT_ROOT)
        filename = file_path.name
        
        # 核心文件
        if filename in CORE_FILES or filename in CORE_MODULES:
            results['核心文件（保留）'].append(str(rel_path))
            continue
        
        # 数据文件
        if file_path.suffix in ['.xlsx', '.xls', '.csv', '.db', '.sqlite']:
            results['数据文件（保留）'].append(str(rel_path))
            continue
            
        # V7.x/V8.x 版本文档（旧版本可删除）
        if re.match(r'V[78]\.\d+', filename):
            # 保留最新版本 V8.9.1
            if 'V8.9.1' in filename or 'V8.9' in filename:
                results['核心文件（保留）'].append(str(rel_path))
            elif any(x in filename for x in ['V7.', 'V8.0', 'V8.1', 'V8.2', 'V8.3', 'V8.4', 'V8.5', 'V8.6', 'V8.7', 'V8.8']):
                results['可以删除的旧版本文档'].append(str(rel_path))
            continue
        
        # 测试脚本
        if filename.startswith('测试') and file_path.suffix == '.py':
            results['可以删除的测试脚本'].append(str(rel_path))
            continue
        
        # 验证脚本
        if filename.startswith('验证') and file_path.suffix == '.py':
            results['可以删除的测试脚本'].append(str(rel_path))
            continue
        
        # 诊断工具
        if filename.startswith('诊断') or '诊断' in filename:
            results['可以删除的诊断工具'].append(str(rel_path))
            continue
        
        # 安装脚本（保留核心的）
        if filename.startswith('安装'):
            if '安装依赖.ps1' in filename or '安装生产级依赖.ps1' in filename:
                results['核心文件（保留）'].append(str(rel_path))
            else:
                results['可以删除的安装脚本'].append(str(rel_path))
            continue
        
        # Git相关脚本（保留核心的）
        if 'git' in filename.lower() or filename.startswith('推送'):
            if filename in ['git_pull.ps1', 'git_push.ps1', 'git_sync.ps1']:
                results['核心文件（保留）'].append(str(rel_path))
            else:
                results['可以删除的Git脚本'].append(str(rel_path))
            continue
        
        # A电脑/B电脑操作脚本
        if filename.startswith('A电脑') or filename.startswith('B电脑') or 'AB电脑' in filename:
            results['可以删除的文档'].append(str(rel_path))
            continue
        
        # 临时文件
        if any(x in filename for x in ['temp', 'tmp', '临时', 'debug_output', '~$']):
            results['可以删除的临时文件'].append(str(rel_path))
            continue
        
        # 备份文件
        if '备份' in filename or 'backup' in filename.lower() or filename.endswith('.backup'):
            results['可以删除的备份文件'].append(str(rel_path))
            continue
        
        # 历史分析报告
        if any(x in filename for x in ['分析报告', '评估报告', '问题分析', '实施报告', '完成报告', '修复说明']):
            results['可以归档的历史文档'].append(str(rel_path))
            continue
        
        # 使用指南（保留核心的）
        if '使用指南' in filename or '操作指南' in filename or '配置指南' in filename:
            if any(x in filename for x in ['快速启动', '新电脑', 'PostgreSQL', 'Redis', 'Git']):
                results['核心文件（保留）'].append(str(rel_path))
            else:
                results['可以归档的历史文档'].append(str(rel_path))
            continue
    
    return results

def print_results(results):
    """打印分析结果"""
    print("=" * 80)
    print("项目文件清理分析报告")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_deletable = 0
    
    for category, files in results.items():
        if not files:
            continue
            
        print(f"\n{'='*80}")
        print(f"{category} ({len(files)} 个文件)")
        print('='*80)
        
        if '可以删除' in category or '可以归档' in category:
            total_deletable += len(files)
        
        for file in sorted(files)[:20]:  # 只显示前20个
            print(f"  - {file}")
        
        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 个文件")
    
    print(f"\n{'='*80}")
    print(f"总结:")
    print(f"  可以删除/归档的文件总数: {total_deletable}")
    print(f"  核心文件数: {len(results['核心文件（保留）'])}")
    print('='*80)

def generate_cleanup_script(results):
    """生成清理脚本"""
    script_path = PROJECT_ROOT / '执行清理.ps1'
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("# 项目文件清理脚本\n")
        f.write("# 自动生成于: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
        f.write("Write-Host '项目文件清理工具' -ForegroundColor Cyan\n")
        f.write("Write-Host '=' * 80 -ForegroundColor Cyan\n\n")
        
        for category in ['可以删除的旧版本文档', '可以删除的测试脚本', '可以删除的临时文件', '可以删除的备份文件']:
            files = results.get(category, [])
            if not files:
                continue
                
            f.write(f"\n# {category}\n")
            f.write(f"Write-Host '\\n清理: {category} ({len(files)} 个)' -ForegroundColor Yellow\n")
            
            for file in files:
                f.write(f'Remove-Item "{file}" -ErrorAction SilentlyContinue\n')
        
        f.write("\nWrite-Host '\\n清理完成!' -ForegroundColor Green\n")
    
    print(f"\n✅ 已生成清理脚本: {script_path}")
    print("   运行 .\\执行清理.ps1 执行清理")

if __name__ == '__main__':
    results = analyze_files()
    print_results(results)
    generate_cleanup_script(results)
