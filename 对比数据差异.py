#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比Streamlit和Dash版本的数据差异
找出计算逻辑的不一致之处
"""

import json
from pathlib import Path
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

APP_DIR = Path(__file__).resolve().parent

def load_results():
    """加载两个版本的结果"""
    streamlit_file = APP_DIR / "数据验证结果_Streamlit版.json"
    dash_file = APP_DIR / "数据验证结果_Dash版.json"
    
    # 加载Streamlit结果
    if streamlit_file.exists():
        with open(streamlit_file, 'r', encoding='utf-8') as f:
            streamlit_metrics = json.load(f)
        print(f"✅ 已加载Streamlit版本数据: {streamlit_file.name}")
    else:
        print(f"❌ 未找到Streamlit版本数据: {streamlit_file}")
        streamlit_metrics = None
    
    # 加载Dash结果  
    if dash_file.exists():
        with open(dash_file, 'r', encoding='utf-8') as f:
            dash_metrics = json.load(f)
        print(f"✅ 已加载Dash版本数据: {dash_file.name}")
    else:
        print(f"❌ 未找到Dash版本数据: {dash_file}")
        print(f"💡 请先运行Dash应用并上传数据，查看Tab 1的指标")
        dash_metrics = None
    
    return streamlit_metrics, dash_metrics


def compare_metrics(streamlit_metrics, dash_metrics=None):
    """
    对比两个版本的指标
    如果dash_metrics为None，则显示Streamlit的基准值供手工对比
    """
    print("\n" + "=" * 100)
    print("📊 数据一致性对比分析")
    print("=" * 100)
    
    if dash_metrics is None:
        # 只显示Streamlit的基准值
        print(f"\n{Fore.YELLOW}⚠️ Dash版本数据未提供，显示Streamlit基准值供您手工对比{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}{'指标':<30} {'Streamlit基准值':>25} {'需要Dash达到':>20}{Style.RESET_ALL}")
        print("-" * 100)
        
        for key in sorted(streamlit_metrics.keys()):
            value = streamlit_metrics[key]
            
            if isinstance(value, (int, float)):
                if isinstance(value, int):
                    s_str = f"{value:,}"
                else:
                    if '率' in key or '百分比' in key:
                        s_str = f"{value:.2f}%"
                    else:
                        s_str = f"¥{value:,.2f}" if '金额' in key or '成本' in key or '利润' in key or '销售' in key or '客单价' in key else f"{value:,.2f}"
                
                target = "完全一致 ✅"
                print(f"{key:<30} {s_str:>25} {target:>20}")
        
        print("\n" + "=" * 100)
        print(f"{Fore.GREEN}📋 验证步骤：{Style.RESET_ALL}")
        print("1. 打开Dash应用: http://localhost:8050")
        print("2. 上传相同的Excel文件")
        print("3. 查看Tab 1的指标卡片")
        print("4. 逐个对比上表中的数值")
        print("5. 找出不一致的指标")
        print("6. 回报给我，我来修复计算逻辑")
        print("=" * 100)
        
        return []
    
    # 完整对比
    all_keys = set(streamlit_metrics.keys()) | set(dash_metrics.keys())
    
    differences = []
    
    print(f"\n{Fore.CYAN}{'指标':<30} {'Streamlit':>20} {'Dash':>20} {'差异':>15} {'状态':>10}{Style.RESET_ALL}")
    print("-" * 100)
    
    for key in sorted(all_keys):
        streamlit_val = streamlit_metrics.get(key, 0)
        dash_val = dash_metrics.get(key, 0)
        
        # 计算差异
        if streamlit_val == 0 and dash_val == 0:
            diff_pct = 0
            diff_abs = 0
        elif streamlit_val == 0:
            diff_pct = 100
            diff_abs = dash_val
        else:
            diff_abs = dash_val - streamlit_val
            diff_pct = (diff_abs / streamlit_val) * 100
        
        # 判断是否一致
        if abs(diff_pct) < 0.01:  # 0.01%以内认为一致
            status = f"{Fore.GREEN}✅{Style.RESET_ALL}"
            color = Fore.WHITE
        elif abs(diff_pct) < 1:  # 1%以内认为接近
            status = f"{Fore.YELLOW}⚠️{Style.RESET_ALL}"
            color = Fore.YELLOW
            differences.append({
                'metric': key,
                'streamlit': streamlit_val,
                'dash': dash_val,
                'diff': diff_abs,
                'diff_pct': diff_pct,
                'severity': 'warning'
            })
        else:
            status = f"{Fore.RED}❌{Style.RESET_ALL}"
            color = Fore.RED
            differences.append({
                'metric': key,
                'streamlit': streamlit_val,
                'dash': dash_val,
                'diff': diff_abs,
                'diff_pct': diff_pct,
                'severity': 'error'
            })
        
        # 格式化输出
        if isinstance(streamlit_val, int):
            s_str = f"{streamlit_val:,}"
            d_str = f"{dash_val:,}"
        else:
            s_str = f"{streamlit_val:,.2f}"
            d_str = f"{dash_val:,.2f}"
        
        diff_str = f"{diff_pct:+.2f}%"
        
        print(f"{color}{key:<30} {s_str:>20} {d_str:>20} {diff_str:>15} {status}{Style.RESET_ALL}")
    
    return differences


def analyze_differences(differences):
    """分析差异原因"""
    if not differences:
        print("\n" + "=" * 100)
        print(f"{Fore.GREEN}🎉 恭喜！所有指标100%一致！{Style.RESET_ALL}")
        print("=" * 100)
        return
    
    print("\n" + "=" * 100)
    print(f"{Fore.RED}⚠️ 发现数据差异，需要修复{Style.RESET_ALL}")
    print("=" * 100)
    
    errors = [d for d in differences if d['severity'] == 'error']
    warnings = [d for d in differences if d['severity'] == 'warning']
    
    if errors:
        print(f"\n{Fore.RED}🔴 严重差异 (>1%):{Style.RESET_ALL}")
        for i, diff in enumerate(errors, 1):
            print(f"\n  {i}. {Fore.RED}{diff['metric']}{Style.RESET_ALL}")
            print(f"     Streamlit: {diff['streamlit']:,.2f}")
            print(f"     Dash:      {diff['dash']:,.2f}")
            print(f"     差异:      {diff['diff']:+,.2f} ({diff['diff_pct']:+.2f}%)")
    
    if warnings:
        print(f"\n{Fore.YELLOW}⚠️ 轻微差异 (<1%):{Style.RESET_ALL}")
        for i, diff in enumerate(warnings, 1):
            print(f"\n  {i}. {Fore.YELLOW}{diff['metric']}{Style.RESET_ALL}")
            print(f"     Streamlit: {diff['streamlit']:,.2f}")
            print(f"     Dash:      {diff['dash']:,.2f}")
            print(f"     差异:      {diff['diff']:+,.2f} ({diff['diff_pct']:+.2f}%)")


def main():
    """主函数"""
    print("\n" + "🔍" * 50)
    print("数据一致性对比分析工具")
    print("🔍" * 50 + "\n")
    
    # 加载结果
    streamlit_metrics, dash_metrics = load_results()
    
    if streamlit_metrics is None:
        print(f"\n{Fore.RED}❌ 缺少Streamlit基准数据，请先运行: python 提取Streamlit数据.py{Style.RESET_ALL}")
        return
    
    # 对比指标
    differences = compare_metrics(streamlit_metrics, dash_metrics)
    
    # 分析差异
    if dash_metrics is not None:
        analyze_differences(differences)
        
        if differences:
            print("\n" + "=" * 100)
            print(f"{Fore.CYAN}🔧 修复建议：{Style.RESET_ALL}")
            print("1. 检查Dash版本的计算公式是否与Streamlit一致")
            print("2. 检查数据过滤逻辑是否完全相同")
            print("3. 检查字段映射是否正确")
            print("4. 检查数据类型转换")
            print("=" * 100)


if __name__ == "__main__":
    try:
        from colorama import init
        main()
    except ImportError:
        print("⚠️ 未安装colorama，输出将没有颜色")
        print("安装命令: pip install colorama")
        main()
