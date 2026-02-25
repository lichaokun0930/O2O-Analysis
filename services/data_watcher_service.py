# -*- coding: utf-8 -*-
"""
热文件夹监控服务 v1.0

功能：
- 监控 data/inbox 目录
- 新文件自动触发导入
- 导入成功 → 移动到 data/processed
- 导入失败 → 移动到 data/failed
- 支持后台运行

使用方式：
    python -m services.data_watcher_service
    python -m services.data_watcher_service --daemon  # 后台运行
"""

import sys
import os
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 尝试导入 watchdog（文件监控库）
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ watchdog 未安装，使用轮询模式")
    print("   安装命令: pip install watchdog")

from database.batch_import_enhanced import BatchDataImporterEnhanced

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DataFolderWatcher:
    """数据文件夹监控器"""
    
    def __init__(self, 
                 inbox_dir: str = "./data/inbox",
                 processed_dir: str = "./data/processed",
                 failed_dir: str = "./data/failed"):
        """
        初始化监控器
        
        Args:
            inbox_dir: 待导入文件目录
            processed_dir: 导入成功后移动到的目录
            failed_dir: 导入失败后移动到的目录
        """
        self.inbox_dir = Path(inbox_dir)
        self.processed_dir = Path(processed_dir)
        self.failed_dir = Path(failed_dir)
        
        # 确保目录存在
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # 正在处理的文件（避免重复处理）
        self.processing_files = set()
        
        logger.info(f"📂 监控目录: {self.inbox_dir.absolute()}")
        logger.info(f"✅ 成功目录: {self.processed_dir.absolute()}")
        logger.info(f"❌ 失败目录: {self.failed_dir.absolute()}")
    
    def is_excel_file(self, filepath: str) -> bool:
        """检查是否为 Excel 文件"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in ['.xlsx', '.xls'] and not os.path.basename(filepath).startswith('~$')
    
    def wait_for_file_ready(self, filepath: str, timeout: int = 60) -> bool:
        """
        等待文件写入完成
        
        大文件复制可能需要时间，等待文件大小稳定
        """
        last_size = -1
        stable_count = 0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(filepath)
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:  # 连续3次大小相同，认为写入完成
                        return True
                else:
                    stable_count = 0
                    last_size = current_size
                time.sleep(1)
            except OSError:
                time.sleep(1)
        
        return False
    
    def process_file(self, filepath: str) -> bool:
        """
        处理单个文件
        
        Returns:
            是否处理成功
        """
        filename = os.path.basename(filepath)
        
        # 检查是否正在处理
        if filepath in self.processing_files:
            return False
        
        self.processing_files.add(filepath)
        
        try:
            logger.info(f"📄 发现新文件: {filename}")
            
            # 等待文件写入完成
            logger.info(f"   ⏳ 等待文件写入完成...")
            if not self.wait_for_file_ready(filepath):
                logger.warning(f"   ⚠️ 文件写入超时: {filename}")
                return False
            
            # 创建临时目录用于单文件导入
            temp_dir = self.inbox_dir / "_processing"
            temp_dir.mkdir(exist_ok=True)
            
            # 移动到临时目录
            temp_filepath = temp_dir / filename
            shutil.move(filepath, temp_filepath)
            
            # 执行导入
            logger.info(f"   🚀 开始导入...")
            importer = BatchDataImporterEnhanced(
                data_dir=str(temp_dir),
                mode="incremental"
            )
            
            # 静默运行（不打印详细信息）
            original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            try:
                importer.run()
            finally:
                sys.stdout.close()
                sys.stdout = original_stdout
            
            # 检查结果
            if importer.stats['files_success'] > 0:
                # 成功：移动到 processed
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_filename = f"{timestamp}_{filename}"
                dest_path = self.processed_dir / dest_filename
                shutil.move(temp_filepath, dest_path)
                
                logger.info(f"   ✅ 导入成功: 新增 {importer.stats['orders_inserted']:,} 条")
                logger.info(f"   📁 已移动到: {dest_path.name}")
                return True
            else:
                # 失败：移动到 failed
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_filename = f"{timestamp}_{filename}"
                dest_path = self.failed_dir / dest_filename
                shutil.move(temp_filepath, dest_path)
                
                error_msg = importer.stats['errors'][0]['error'] if importer.stats['errors'] else "未知错误"
                logger.error(f"   ❌ 导入失败: {error_msg[:50]}")
                logger.info(f"   📁 已移动到: {dest_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ 处理异常: {e}")
            # 尝试移动到失败目录
            try:
                if os.path.exists(filepath):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_path = self.failed_dir / f"{timestamp}_{filename}"
                    shutil.move(filepath, dest_path)
            except:
                pass
            return False
        finally:
            self.processing_files.discard(filepath)
            # 清理临时目录
            temp_dir = self.inbox_dir / "_processing"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def scan_inbox(self):
        """扫描 inbox 目录中的现有文件"""
        for filepath in self.inbox_dir.glob("*"):
            if filepath.is_file() and self.is_excel_file(str(filepath)):
                self.process_file(str(filepath))
    
    def run_polling(self, interval: int = 10):
        """
        轮询模式运行
        
        Args:
            interval: 扫描间隔（秒）
        """
        logger.info(f"🔄 启动轮询模式 (间隔: {interval}秒)")
        logger.info(f"💡 将 Excel 文件放入 {self.inbox_dir.absolute()} 即可自动导入")
        logger.info("按 Ctrl+C 停止监控\n")
        
        # 先处理现有文件
        self.scan_inbox()
        
        try:
            while True:
                time.sleep(interval)
                self.scan_inbox()
        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")
    
    def run_watchdog(self):
        """使用 watchdog 实时监控"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog 不可用，切换到轮询模式")
            self.run_polling()
            return
        
        class ExcelFileHandler(FileSystemEventHandler):
            def __init__(self, watcher):
                self.watcher = watcher
            
            def on_created(self, event):
                if not event.is_directory and self.watcher.is_excel_file(event.src_path):
                    # 延迟处理，等待文件写入完成
                    time.sleep(2)
                    self.watcher.process_file(event.src_path)
        
        event_handler = ExcelFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.inbox_dir), recursive=False)
        observer.start()
        
        logger.info("👀 启动实时监控模式 (watchdog)")
        logger.info(f"💡 将 Excel 文件放入 {self.inbox_dir.absolute()} 即可自动导入")
        logger.info("按 Ctrl+C 停止监控\n")
        
        # 先处理现有文件
        self.scan_inbox()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("\n👋 监控已停止")
        
        observer.join()


def main():
    parser = argparse.ArgumentParser(description='热文件夹监控服务')
    parser.add_argument('--inbox', default='./data/inbox', help='待导入文件目录')
    parser.add_argument('--processed', default='./data/processed', help='成功文件目录')
    parser.add_argument('--failed', default='./data/failed', help='失败文件目录')
    parser.add_argument('--polling', action='store_true', help='使用轮询模式')
    parser.add_argument('--interval', type=int, default=10, help='轮询间隔(秒)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("📂 热文件夹监控服务 v1.0")
    print("="*60 + "\n")
    
    watcher = DataFolderWatcher(
        inbox_dir=args.inbox,
        processed_dir=args.processed,
        failed_dir=args.failed
    )
    
    if args.polling or not WATCHDOG_AVAILABLE:
        watcher.run_polling(interval=args.interval)
    else:
        watcher.run_watchdog()


if __name__ == "__main__":
    main()
