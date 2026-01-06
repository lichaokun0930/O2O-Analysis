# -*- coding: utf-8 -*-
"""
后台任务模块 - V8.1 企业级性能优化

功能:
- 定时预计算诊断数据
- 定时预计算商品评分数据
- 将结果缓存到Redis

设计理念:
- 用户访问时直接读缓存(<1秒)
- 后台每5分钟更新一次
- 避免阻塞用户请求

作者: AI Assistant
版本: V8.1
日期: 2025-12-11
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

# 全局调度器实例
_scheduler = None


def update_diagnosis_cache():
    """
    更新诊断数据缓存 - V8.4分层缓存+智能预热
    
    执行流程:
    1. 从数据库加载数据
    2. 分析热点门店（基于访问日志）
    3. 优先预热热点门店（并行）
    4. 后台渐进式预热其他门店
    
    策略:
    - 使用分层缓存架构
    - 热点门店优先（80/20原则）
    - 并行预热（多线程）
    - 压缩存储（节省内存）
    """
    try:
        print(f"\n{'='*80}")
        print(f"[后台任务] V8.4分层缓存智能预热 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        import time
        import pandas as pd
        from concurrent.futures import ThreadPoolExecutor, as_completed
        start_time = time.time()
        
        # 导入分层缓存管理器
        from hierarchical_cache_manager import get_hierarchical_cache
        hierarchical_cache = get_hierarchical_cache()
        
        if not hierarchical_cache.enabled:
            print("[后台任务] ⚠️ 分层缓存未启用")
            return
        
        # 获取全局数据
        try:
            from 智能门店看板_Dash版 import GLOBAL_DATA
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                print("[后台任务] ⚠️ GLOBAL_DATA为空，跳过更新")
                return
            
            df = GLOBAL_DATA.copy()
            print(f"[后台任务] 数据行数: {len(df):,}")
            
        except Exception as e:
            print(f"[后台任务] ❌ 获取GLOBAL_DATA失败: {e}")
            return
        
        # 导入诊断计算函数
        from components.today_must_do.diagnosis_analysis import get_diagnosis_summary
        
        # 获取日期范围
        date_col = '日期' if '日期' in df.columns else '下单时间'
        dates = pd.to_datetime(df[date_col])
        date_range = (dates.min().strftime('%Y-%m-%d'), dates.max().strftime('%Y-%m-%d'))
        
        cached_count = 0
        
        # ===== 阶段1: 预热全局数据 =====
        print(f"\n[阶段1] 预热全局数据...")
        try:
            diagnosis = get_diagnosis_summary(df)
            hierarchical_cache.cache_diagnosis(
                store_ids=[],  # 空列表表示全局
                date_range=date_range,
                diagnosis=diagnosis,
                ttl=3600
            )
            cached_count += 1
            print(f"[阶段1] ✅ 全局数据已缓存")
        except Exception as e:
            print(f"[阶段1] ⚠️ 全局数据缓存失败: {e}")
        
        # ===== 阶段2: 分析热点门店 =====
        if '门店名称' not in df.columns:
            print("[后台任务] ⚠️ 无门店字段，跳过门店预热")
            return
        
        all_stores = df['门店名称'].unique().tolist()
        total_stores = len(all_stores)
        print(f"\n[阶段2] 分析热点门店（总数: {total_stores}）...")
        
        # 基于访问日志分析热点
        hot_stores = hierarchical_cache.analyze_hot_stores(top_n=max(1, total_stores // 5))
        
        # 确保热点门店在all_stores中
        hot_stores = [s for s in hot_stores if s in all_stores]
        
        # 如果没有访问日志，默认预热前20%
        if not hot_stores:
            hot_count = max(1, total_stores // 5)
            hot_stores = all_stores[:hot_count]
            print(f"[阶段2] 无访问日志，默认预热前{hot_count}个门店")
        else:
            print(f"[阶段2] 识别热点门店: {len(hot_stores)}个")
        
        # 冷门店 = 全部 - 热点
        cold_stores = [s for s in all_stores if s not in hot_stores]
        
        # ===== 阶段3: 并行预热热点门店 =====
        print(f"\n[阶段3] 并行预热热点门店（{len(hot_stores)}个）...")
        
        def warmup_single_store(store_name):
            """预热单个门店"""
            try:
                store_df = df[df['门店名称'] == store_name]
                diagnosis = get_diagnosis_summary(store_df)
                hierarchical_cache.cache_diagnosis(
                    store_ids=[store_name],
                    date_range=date_range,
                    diagnosis=diagnosis,
                    ttl=3600
                )
                return (store_name, True, None)
            except Exception as e:
                return (store_name, False, str(e))
        
        # 并行预热（最多5个线程）
        hot_success = 0
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(warmup_single_store, store): store for store in hot_stores}
            
            for idx, future in enumerate(as_completed(futures), 1):
                store_name, success, error = future.result()
                if success:
                    hot_success += 1
                    cached_count += 1
                    print(f"[阶段3] ✅ [{idx}/{len(hot_stores)}] {store_name}")
                else:
                    print(f"[阶段3] ⚠️ [{idx}/{len(hot_stores)}] {store_name} 失败: {error}")
        
        print(f"[阶段3] 热点门店预热完成: {hot_success}/{len(hot_stores)}")
        
        # ===== 阶段4: 渐进式预热冷门店（限制数量，避免超时）=====
        if cold_stores:
            # 只预热部分冷门店（最多20个），避免任务超时
            cold_to_warmup = cold_stores[:20]
            print(f"\n[阶段4] 渐进式预热冷门店（{len(cold_to_warmup)}/{len(cold_stores)}）...")
            
            cold_success = 0
            for idx, store_name in enumerate(cold_to_warmup, 1):
                try:
                    store_df = df[df['门店名称'] == store_name]
                    diagnosis = get_diagnosis_summary(store_df)
                    hierarchical_cache.cache_diagnosis(
                        store_ids=[store_name],
                        date_range=date_range,
                        diagnosis=diagnosis,
                        ttl=3600
                    )
                    cold_success += 1
                    cached_count += 1
                    print(f"[阶段4] ✅ [{idx}/{len(cold_to_warmup)}] {store_name}")
                except Exception as e:
                    print(f"[阶段4] ⚠️ [{idx}/{len(cold_to_warmup)}] {store_name} 失败: {e}")
            
            print(f"[阶段4] 冷门店预热完成: {cold_success}/{len(cold_to_warmup)}")
            
            if len(cold_stores) > 20:
                print(f"[阶段4] 剩余{len(cold_stores) - 20}个门店将按需缓存（首次访问时）")
        
        # ===== 总结 =====
        elapsed = time.time() - start_time
        stats = hierarchical_cache.get_stats()
        
        print(f"\n{'='*80}")
        print(f"[后台任务] ✅ V8.4智能预热完成")
        print(f"[后台任务] 总耗时: {elapsed:.2f}秒")
        print(f"[后台任务] 已缓存: {cached_count} 个数据集")
        print(f"[后台任务] 内存使用: {stats.get('used_memory_mb', 0):.1f}MB / {stats.get('max_memory_mb', 0):.1f}MB")
        print(f"[后台任务] 缓存命中率: {stats.get('hit_rate', 0):.1f}%")
        print(f"[后台任务] 下次更新: {datetime.now().strftime('%H:%M:%S')} + 5分钟")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"[后台任务] ❌ 更新诊断数据失败: {e}")
        import traceback
        traceback.print_exc()


def update_product_scores_cache():
    """
    更新商品评分数据缓存
    
    执行流程:
    1. 从数据库加载数据
    2. 计算商品评分
    3. 存入Redis缓存
    """
    try:
        print(f"\n{'='*80}")
        print(f"[后台任务] 开始更新商品评分缓存 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        import time
        start_time = time.time()
        
        # 导入必要的模块
        from redis_cache_manager import REDIS_CACHE_MANAGER
        
        # 获取全局数据
        try:
            from 智能门店看板_Dash版 import GLOBAL_DATA
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                print("[后台任务] ⚠️ GLOBAL_DATA为空，跳过更新")
                return
            
            df = GLOBAL_DATA.copy()
            print(f"[后台任务] 数据行数: {len(df)}")
            
        except Exception as e:
            print(f"[后台任务] ❌ 获取GLOBAL_DATA失败: {e}")
            return
        
        # 计算商品评分（这里简化处理，实际可以调用具体的评分函数）
        # 由于商品评分计算较复杂，暂时跳过
        print(f"[后台任务] ℹ️ 商品评分缓存更新已跳过（待实现）")
        
        elapsed = time.time() - start_time
        print(f"[后台任务] 耗时: {elapsed:.2f}秒")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"[后台任务] ❌ 更新商品评分失败: {e}")
        import traceback
        traceback.print_exc()


def start_background_tasks():
    """
    启动后台任务调度器
    
    任务列表:
    1. 每5分钟更新诊断数据缓存
    2. 每10分钟更新商品评分缓存
    
    Returns:
        BackgroundScheduler: 调度器实例
    """
    global _scheduler
    
    if _scheduler is not None:
        print("[后台任务] ⚠️ 调度器已经在运行")
        return _scheduler
    
    print(f"\n{'='*80}")
    print("[后台任务] 🚀 启动后台任务调度器...")
    print(f"{'='*80}")
    
    _scheduler = BackgroundScheduler()
    
    # 任务1: 更新诊断数据缓存（每5分钟）
    _scheduler.add_job(
        update_diagnosis_cache,
        'interval',
        minutes=5,
        id='update_diagnosis',
        name='更新诊断数据缓存',
        max_instances=1,  # 同时只运行一个实例
        coalesce=True,    # 如果错过了执行时间，只执行一次
        replace_existing=True
    )
    print("[后台任务] ✅ 已添加任务: 更新诊断数据缓存 (每5分钟)")
    
    # 任务2: 更新商品评分缓存（每10分钟）
    _scheduler.add_job(
        update_product_scores_cache,
        'interval',
        minutes=10,
        id='update_product_scores',
        name='更新商品评分缓存',
        max_instances=1,
        coalesce=True,
        replace_existing=True
    )
    print("[后台任务] ✅ 已添加任务: 更新商品评分缓存 (每10分钟)")
    
    # 启动调度器
    _scheduler.start()
    print("[后台任务] ✅ 调度器已启动")
    
    # 立即执行一次（预热缓存）
    print("[后台任务] 🔥 立即执行一次预热缓存...")
    try:
        update_diagnosis_cache()
    except Exception as e:
        print(f"[后台任务] ⚠️ 预热失败: {e}")
    
    print(f"{'='*80}\n")
    
    return _scheduler


def stop_background_tasks():
    """
    停止后台任务调度器
    """
    global _scheduler
    
    if _scheduler is None:
        print("[后台任务] ⚠️ 调度器未运行")
        return
    
    print("[后台任务] 🛑 停止后台任务调度器...")
    _scheduler.shutdown(wait=False)
    _scheduler = None
    print("[后台任务] ✅ 调度器已停止")


def get_scheduler_status():
    """
    获取调度器状态
    
    Returns:
        dict: 调度器状态信息
    """
    global _scheduler
    
    if _scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None
        })
    
    return {
        'running': _scheduler.running,
        'jobs': jobs
    }


# 导出
__all__ = [
    'start_background_tasks',
    'stop_background_tasks',
    'get_scheduler_status',
    'update_diagnosis_cache',
    'update_product_scores_cache'
]
