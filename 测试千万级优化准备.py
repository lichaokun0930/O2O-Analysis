# -*- coding: utf-8 -*-
"""
测试千万级数据优化准备工作

验证：
1. 依赖安装是否成功
2. 目录结构是否正确
3. 服务是否可用
4. 数据量监控是否正常
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

def test_dependencies():
    """测试依赖安装"""
    print("\n" + "="*60)
    print("📦 测试依赖安装")
    print("="*60)
    
    dependencies = {
        "duckdb": "DuckDB查询引擎",
        "pyarrow": "Parquet文件支持",
        "apscheduler": "定时任务调度",
    }
    
    all_ok = True
    for module, desc in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {module}: {desc}")
        except ImportError as e:
            print(f"  ❌ {module}: {desc} - 未安装")
            all_ok = False
    
    return all_ok


def test_directory_structure():
    """测试目录结构"""
    print("\n" + "="*60)
    print("📁 测试目录结构")
    print("="*60)
    
    data_dir = PROJECT_ROOT / "data"
    required_dirs = [
        data_dir / "raw",
        data_dir / "aggregated",
        data_dir / "metadata",
    ]
    
    all_ok = True
    for d in required_dirs:
        if d.exists():
            print(f"  ✅ {d.relative_to(PROJECT_ROOT)}")
        else:
            print(f"  ❌ {d.relative_to(PROJECT_ROOT)} - 不存在")
            all_ok = False
    
    return all_ok


def test_services():
    """测试服务初始化"""
    print("\n" + "="*60)
    print("🔧 测试服务初始化")
    print("="*60)
    
    all_ok = True
    
    # 测试DuckDB服务
    try:
        from backend.app.services import duckdb_service
        status = duckdb_service.get_status()
        print(f"  ✅ DuckDB服务: 已初始化 (启用状态: {status['enabled']})")
    except Exception as e:
        print(f"  ❌ DuckDB服务: {e}")
        all_ok = False
    
    # 测试Parquet同步服务
    try:
        from backend.app.services import parquet_sync_service
        status = parquet_sync_service.get_status()
        print(f"  ✅ Parquet同步服务: 已初始化")
        print(f"     - 数据目录: {status['data_dir']}")
        print(f"     - 原始文件数: {status['raw_files_count']}")
        print(f"     - 聚合文件数: {status['aggregated_files_count']}")
    except Exception as e:
        print(f"  ❌ Parquet同步服务: {e}")
        all_ok = False
    
    # 测试数据监控服务
    try:
        from backend.app.services import data_monitor_service
        stats = data_monitor_service.get_data_stats()
        print(f"  ✅ 数据监控服务: 已初始化")
        print(f"     - 总记录数: {stats['total_records']:,}")
        print(f"     - 唯一订单数: {stats['unique_orders']:,}")
        print(f"     - 门店数: {stats['store_count']}")
        print(f"     - 日均增长: {stats['daily_growth']:,.0f}")
        
        rec = stats['recommendation']
        print(f"\n  📊 当前状态: {rec['message']}")
        
        if rec['actions']:
            print(f"  📋 建议操作:")
            for action in rec['actions']:
                print(f"     - {action}")
    except Exception as e:
        print(f"  ❌ 数据监控服务: {e}")
        all_ok = False
    
    return all_ok


def test_duckdb_basic():
    """测试DuckDB基本功能"""
    print("\n" + "="*60)
    print("🦆 测试DuckDB基本功能")
    print("="*60)
    
    try:
        import duckdb
        
        # 创建内存数据库
        conn = duckdb.connect(':memory:')
        
        # 测试基本查询
        result = conn.execute("SELECT 1 + 1 as result").fetchone()
        print(f"  ✅ 基本查询: 1 + 1 = {result[0]}")
        
        # 测试Parquet读取能力
        conn.execute("SELECT * FROM read_parquet('nonexistent.parquet') LIMIT 0")
        print(f"  ✅ Parquet读取: 语法支持正常")
        
        conn.close()
        return True
    except duckdb.IOException:
        # 文件不存在是预期的，只要语法正确就行
        print(f"  ✅ Parquet读取: 语法支持正常")
        return True
    except Exception as e:
        print(f"  ❌ DuckDB测试失败: {e}")
        return False


def test_pyarrow_basic():
    """测试PyArrow基本功能"""
    print("\n" + "="*60)
    print("🏹 测试PyArrow基本功能")
    print("="*60)
    
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        import pandas as pd
        import tempfile
        import os
        
        # 创建测试数据
        df = pd.DataFrame({
            '订单ID': ['001', '002', '003'],
            '金额': [100.0, 200.0, 300.0],
            '日期': pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03'])
        })
        
        # 写入Parquet
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = f.name
        
        df.to_parquet(temp_path, engine='pyarrow', compression='snappy')
        print(f"  ✅ Parquet写入: 成功")
        
        # 读取Parquet
        df_read = pd.read_parquet(temp_path)
        print(f"  ✅ Parquet读取: 成功 ({len(df_read)} 行)")
        
        # 清理
        os.unlink(temp_path)
        
        return True
    except Exception as e:
        print(f"  ❌ PyArrow测试失败: {e}")
        return False


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           🚀 千万级数据优化 - 准备工作测试
╠══════════════════════════════════════════════════════════════════╣
║  测试项目:
║  1. 依赖安装 (duckdb, pyarrow, apscheduler)
║  2. 目录结构 (data/raw, data/aggregated, data/metadata)
║  3. 服务初始化 (DuckDB, Parquet同步, 数据监控)
║  4. DuckDB基本功能
║  5. PyArrow基本功能
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    results.append(("依赖安装", test_dependencies()))
    results.append(("目录结构", test_directory_structure()))
    results.append(("DuckDB基本功能", test_duckdb_basic()))
    results.append(("PyArrow基本功能", test_pyarrow_basic()))
    results.append(("服务初始化", test_services()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📋 测试结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！千万级优化准备工作已完成。")
        print("\n📌 下一步操作:")
        print("  1. 当数据量超过100万时，运行Parquet归档脚本")
        print("  2. 当数据量超过300万时，启用DuckDB查询引擎")
        print("  3. 访问 /api/v1/data-monitor/stats 查看数据量监控")
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息。")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
