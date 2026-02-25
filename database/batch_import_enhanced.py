# -*- coding: utf-8 -*-
"""
增强版批量数据导入工具 v2.0

功能特性：
- 支持增量导入（只导入新数据）
- 支持全量替换（删除旧数据后导入）
- 自动识别门店名称
- 详细的导入报告
- 错误处理和回滚
- 导入历史记录

使用方式：
    python -m database.batch_import_enhanced --path ./实际数据 --mode incremental
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import glob
import hashlib
import argparse
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal, init_database
from database.models import Order, DataUploadHistory
from sqlalchemy import func, text

# 尝试导入数据处理器
try:
    from 真实数据处理器 import RealDataProcessor
    DATA_PROCESSOR_AVAILABLE = True
except ImportError:
    DATA_PROCESSOR_AVAILABLE = False
    print("⚠️ 真实数据处理器未找到，将使用基础字段映射")


class BatchDataImporterEnhanced:
    """增强版批量数据导入器"""
    
    def __init__(self, data_dir: str, mode: str = "incremental"):
        """
        初始化导入器
        
        Args:
            data_dir: 数据文件目录
            mode: 导入模式 - incremental(增量) / replace(替换)
        """
        self.data_dir = data_dir
        self.mode = mode
        self.processor = RealDataProcessor() if DATA_PROCESSOR_AVAILABLE else None
        
        # 统计信息
        self.stats = {
            'files_total': 0,
            'files_success': 0,
            'files_failed': 0,
            'files_skipped': 0,
            'orders_inserted': 0,
            'orders_updated': 0,
            'orders_skipped': 0,
            'errors': []
        }
        
        # 确保数据库已初始化
        init_database()
        
        # ✅ 验证预聚合表结构（防止同步失败）
        self._validate_schema()
    
    def _validate_schema(self):
        """验证预聚合表结构，自动修复缺失字段"""
        try:
            from backend.app.services.schema_validator import SchemaValidator
            success, messages = SchemaValidator.validate_and_fix_all()
            for msg in messages:
                print(f"   {msg}")
            if not success:
                print("⚠️ 预聚合表结构存在问题，同步可能失败")
        except ImportError:
            # 验证器不存在时跳过
            pass
        except Exception as e:
            print(f"⚠️ 表结构验证失败: {e}")
    
    def find_excel_files(self) -> List[str]:
        """查找所有 Excel 文件"""
        patterns = ['*.xlsx', '*.xls']
        files = []
        
        for pattern in patterns:
            files.extend(glob.glob(f"{self.data_dir}/**/{pattern}", recursive=True))
        
        # 过滤临时文件（以 ~$ 开头）
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        
        return sorted(files)
    
    def calculate_file_hash(self, filepath: str) -> str:
        """计算文件 MD5 哈希"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_file_imported(self, filepath: str, file_hash: str) -> bool:
        """检查文件是否已导入过"""
        session = SessionLocal()
        try:
            existing = session.query(DataUploadHistory).filter(
                DataUploadHistory.file_hash == file_hash
            ).first()
            
            if existing:
                # 检查数据库中是否真的有数据
                order_count = session.query(func.count(Order.id)).scalar() or 0
                
                if order_count == 0:
                    # 数据库为空但有导入历史，说明数据被删除了，自动清理历史记录
                    print(f"   ⚠️ 检测到数据库为空但存在导入历史，自动清理...")
                    session.query(DataUploadHistory).delete()
                    session.commit()
                    print(f"   ✅ 已自动清理导入历史记录")
                    return False
                
                return True
            return False
        finally:
            session.close()
    
    def extract_store_name(self, df: pd.DataFrame, filename: str) -> str:
        """从数据或文件名中提取门店名称"""
        # 优先从数据中获取
        if '门店名称' in df.columns:
            store_names = df['门店名称'].dropna().unique()
            if len(store_names) > 0:
                return str(store_names[0])
        
        # 从文件名提取（如果包含门店名称）
        # 例如：惠宜选-泰州泰兴店_2025-01.xlsx
        basename = os.path.basename(filename)
        if '_' in basename:
            potential_store = basename.split('_')[0]
            if len(potential_store) > 2:
                return potential_store
        
        return "未知门店"
    
    def standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化 DataFrame 字段"""
        if self.processor:
            return self.processor.standardize_sales_data(df)
        
        # 基础字段映射
        column_mapping = {
            '订单号': '订单ID',
            '订单编号': '订单ID',
            '下单日期': '下单时间',
            '订单时间': '下单时间',
            '采集时间': '下单时间',
            '品名': '商品名称',
            '商品': '商品名称',
            '实付金额': '实收价格',
            '实付': '实收价格',
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        return df
    
    def import_orders(self, df: pd.DataFrame, store_names: List[str]) -> Tuple[int, int, int]:
        """
        导入订单数据（支持多门店聚合表）
        
        Args:
            df: 订单数据 DataFrame
            store_names: 门店名称列表
        
        Returns:
            (inserted, updated, skipped)
        
        注意：
        - 同一订单中同一商品可能出现多次（顾客购买多份），这些都是有效数据
        - 不再使用 订单ID+商品名称 去重，改为全量导入
        - 增量模式下，只检查文件是否已导入过，不检查单条记录
        """
        session = SessionLocal()
        inserted = 0
        updated = 0
        skipped = 0
        
        try:
            # 替换模式：先删除所有涉及门店的旧数据
            if self.mode == "replace":
                total_deleted = 0
                for store_name in store_names:
                    deleted = session.query(Order).filter(Order.store_name == store_name).delete()
                    if deleted > 0:
                        print(f"   🗑️ 删除 {store_name}: {deleted:,} 条")
                        total_deleted += deleted
                session.commit()
                if total_deleted > 0:
                    print(f"   🗑️ 删除旧数据总计: {total_deleted:,} 条")
            
            # 获取日期列
            date_col = None
            for col in ['日期', '下单时间', '采集时间', 'date']:
                if col in df.columns:
                    date_col = col
                    break
            
            if not date_col:
                raise ValueError("未找到日期列")
            
            # 批量处理
            batch_size = 5000
            total_rows = len(df)
            
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                batch_df = df.iloc[batch_start:batch_end]
                
                orders_to_insert = []
                
                for _, row in batch_df.iterrows():
                    order_id = str(row.get('订单ID', ''))
                    if not order_id or order_id == 'nan':
                        skipped += 1
                        continue
                    
                    # 注意：不再进行单条记录去重
                    # 原因：同一订单中同一商品可能出现多次（如顾客买了2份同样的商品）
                    # 这些都是有效的销售数据，不应该被跳过
                    # 增量模式的去重通过文件哈希检查实现（check_file_imported）
                    
                    # 解析日期
                    order_date = None
                    if pd.notna(row.get(date_col)):
                        try:
                            order_date = pd.to_datetime(row[date_col])
                            if pd.isna(order_date):
                                order_date = None
                        except:
                            order_date = None
                    
                    if order_date is None:
                        skipped += 1
                        continue
                    
                    # 辅助函数
                    def safe_float(val, default=0):
                        if pd.isna(val): return default
                        try: return float(val)
                        except: return default
                    
                    def safe_int(val, default=0):
                        if pd.isna(val): return default
                        try: return int(val)
                        except: return default
                    
                    def safe_str(val, default=''):
                        if pd.isna(val): return default
                        return str(val)
                    
                    # 创建订单对象（从每行数据获取门店名称，支持多门店聚合表）
                    row_store_name = safe_str(row.get('门店名称', ''))
                    if not row_store_name:
                        row_store_name = store_names[0] if store_names else '未知门店'
                    
                    order = Order(
                        order_id=order_id,
                        order_number=safe_str(row.get('订单编号', '')),
                        store_name=row_store_name,
                        product_name=safe_str(row.get('商品名称', '')),
                        date=order_date,
                        channel=safe_str(row.get('渠道', '')),
                        address=safe_str(row.get('收货地址', '')),
                        
                        # 分类
                        category_level1=safe_str(row.get('一级分类名', row.get('一级分类', ''))),
                        category_level3=safe_str(row.get('三级分类名', row.get('三级分类', ''))),
                        
                        # 价格和成本
                        price=safe_float(row.get('商品实售价', 0)),
                        original_price=safe_float(row.get('商品原价', 0)),
                        cost=safe_float(row.get('商品采购成本', row.get('成本', 0))),
                        actual_price=safe_float(row.get('实收价格', 0)),
                        
                        # 销量和金额
                        quantity=safe_int(row.get('销量', row.get('月售', 1)), 1),
                        stock=safe_int(row.get('库存', 0)),
                        remaining_stock=safe_float(row.get('剩余库存', row.get('库存', 0))),
                        amount=safe_float(row.get('预计订单收入', row.get('订单零售额', row.get('销售额', 0)))),
                        profit=safe_float(row.get('利润额', row.get('实际利润', row.get('利润', 0)))),
                        
                        # 费用
                        delivery_fee=safe_float(row.get('物流配送费', 0)),
                        commission=safe_float(row.get('平台佣金', 0)),
                        platform_service_fee=safe_float(row.get('平台服务费', row.get('平台佣金', 0))),
                        
                        # 营销活动费用
                        user_paid_delivery_fee=safe_float(row.get('用户支付配送费', 0)),
                        delivery_discount=safe_float(row.get('配送费减免金额', 0)),
                        full_reduction=safe_float(row.get('满减金额', 0)),
                        product_discount=safe_float(row.get('商品减免金额', 0)),
                        merchant_voucher=safe_float(row.get('商家代金券', 0)),
                        merchant_share=safe_float(row.get('商家承担部分券', 0)),
                        packaging_fee=safe_float(row.get('打包袋金额', 0)),
                        gift_amount=safe_float(row.get('满赠金额', 0)),
                        other_merchant_discount=safe_float(row.get('商家其他优惠', 0)),
                        new_customer_discount=safe_float(row.get('新客减免金额', 0)),
                        
                        # 利润补偿项
                        corporate_rebate=safe_float(row.get('企客后返', 0)),
                        
                        # 配送信息
                        delivery_distance=safe_float(row.get('配送距离', 0)),
                        delivery_platform=safe_str(row.get('配送平台', '')),
                        
                        # 门店信息
                        store_id=safe_str(row.get('门店ID', '')),
                        city=safe_str(row.get('城市名称', row.get('城市', ''))),
                        
                        # 条码
                        barcode=safe_str(row.get('条码', '')),
                        store_code=safe_str(row.get('店内码', '')),
                    )
                    orders_to_insert.append(order)
                    inserted += 1
                
                # 批量插入
                if orders_to_insert:
                    session.bulk_save_objects(orders_to_insert)
                    session.commit()
                
                # 显示进度
                progress = min(batch_end, total_rows)
                print(f"   📊 进度: {progress:,}/{total_rows:,} ({progress*100//total_rows}%)", end='\r')
            
            print()  # 换行
            return inserted, updated, skipped
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def log_upload_history(self, filename: str, file_hash: str, file_size: int,
                          rows_imported: int, success: bool, error_msg: str = None):
        """记录上传历史"""
        session = SessionLocal()
        try:
            history = DataUploadHistory(
                file_name=os.path.basename(filename),
                file_size=file_size,
                file_hash=file_hash,
                rows_imported=rows_imported,
                rows_failed=0 if success else rows_imported,
                success=success,
                error_log=error_msg,
                uploaded_at=datetime.now()
            )
            session.add(history)
            session.commit()
        except Exception as e:
            print(f"   ⚠️ 记录上传历史失败: {e}")
            session.rollback()
        finally:
            session.close()
    
    def import_file(self, filepath: str) -> bool:
        """导入单个文件"""
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        
        print(f"\n{'='*60}")
        print(f"📄 {filename}")
        print(f"{'='*60}")
        
        try:
            # 1. 计算文件哈希
            file_hash = self.calculate_file_hash(filepath)
            
            # 2. 检查是否已导入（增量模式）
            if self.mode == "incremental" and self.check_file_imported(filepath, file_hash):
                print(f"   ⏭️ 文件已导入过，跳过")
                self.stats['files_skipped'] += 1
                return True
            
            # 3. 加载 Excel
            print(f"   📖 加载文件...")
            df = pd.read_excel(filepath)
            original_rows = len(df)
            print(f"   📊 原始数据: {original_rows:,} 行")
            
            # 4. 标准化字段
            print(f"   🔧 标准化字段...")
            df = self.standardize_dataframe(df)
            
            # 5. 业务过滤（排除耗材等）
            if '一级分类名' in df.columns:
                df = df[df['一级分类名'] != '耗材'].copy()
            filtered_rows = len(df)
            if filtered_rows < original_rows:
                print(f"   🔍 过滤后: {filtered_rows:,} 行")
            
            # 6. 提取门店名称列表（支持多门店聚合表）
            if '门店名称' in df.columns:
                store_names = df['门店名称'].dropna().unique().tolist()
            else:
                store_names = [self.extract_store_name(df, filepath)]
            
            if len(store_names) == 1:
                print(f"   🏪 门店: {store_names[0]}")
            else:
                print(f"   🏪 门店: {len(store_names)} 个 (聚合表)")
                for s in store_names[:5]:  # 最多显示5个
                    print(f"      • {s}")
                if len(store_names) > 5:
                    print(f"      ... 还有 {len(store_names) - 5} 个")
            
            # 7. 导入数据
            print(f"   💾 导入数据库...")
            inserted, updated, skipped = self.import_orders(df, store_names)
            
            # 8. 记录历史
            self.log_upload_history(filepath, file_hash, file_size, inserted, True)
            
            # 9. 更新统计
            self.stats['files_success'] += 1
            self.stats['orders_inserted'] += inserted
            self.stats['orders_updated'] += updated
            self.stats['orders_skipped'] += skipped
            
            # 10. 记录需要更新预聚合表的门店
            if not hasattr(self, 'stores_to_sync'):
                self.stores_to_sync = set()
            self.stores_to_sync.update(store_names)
            
            print(f"   ✅ 完成: 新增 {inserted:,}, 跳过 {skipped:,}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ 失败: {error_msg[:100]}")
            self.stats['files_failed'] += 1
            self.stats['errors'].append({'file': filename, 'error': error_msg})
            self.log_upload_history(filepath, '', file_size, 0, False, error_msg)
            return False
    
    def run(self):
        """执行批量导入"""
        print("\n" + "="*60)
        print("📦 批量数据导入工具 v2.0")
        print("="*60)
        
        # 查找文件
        files = self.find_excel_files()
        self.stats['files_total'] = len(files)
        
        if not files:
            print(f"\n❌ 未找到 Excel 文件: {self.data_dir}")
            return
        
        print(f"\n📂 数据目录: {self.data_dir}")
        print(f"📊 发现 {len(files)} 个文件")
        print(f"📋 导入模式: {self.mode}")
        
        # 逐个导入
        for filepath in files:
            self.import_file(filepath)
        
        # ✅ 自动更新预聚合表
        if hasattr(self, 'stores_to_sync') and self.stores_to_sync:
            print("\n" + "="*60)
            print("🔄 自动更新预聚合表")
            print("="*60)
            try:
                from backend.app.services.aggregation_sync_service import AggregationSyncService
                AggregationSyncService.sync_store_data(list(self.stores_to_sync), async_mode=False)
            except ImportError:
                # 如果无法导入，尝试直接执行SQL
                print("⚠️ 无法导入同步服务，尝试直接更新...")
                self._sync_aggregation_tables(list(self.stores_to_sync))
        
        # ✅ 导入完成后执行一致性检查（确保所有门店数据都已同步）
        self._run_consistency_check()
        
        # 打印统计
        self.print_summary()
    
    def _run_consistency_check(self):
        """导入完成后执行一致性检查，确保所有门店数据都已同步"""
        print("\n" + "="*60)
        print("🔍 执行预聚合表一致性检查")
        print("="*60)
        
        try:
            from backend.app.services.aggregation_consistency_service import aggregation_consistency_service
            result = aggregation_consistency_service.check_and_repair()
            
            check = result.get("check_result", {})
            repair = result.get("repair_result")
            
            if check.get("consistent"):
                print(f"✅ 预聚合表一致: {len(check.get('order_stores', []))} 个门店")
            elif repair:
                synced = repair.get("synced_stores", [])
                failed = repair.get("failed_stores", [])
                if synced:
                    print(f"✅ 已修复: 同步 {len(synced)} 个门店")
                if failed:
                    print(f"⚠️ 同步失败: {len(failed)} 个门店")
                    for f in failed[:3]:
                        print(f"   - {f['store']}: {f['error'][:50]}")
            else:
                print("⚠️ 存在不一致但无需修复")
                
        except ImportError as e:
            print(f"⚠️ 无法导入一致性检查服务: {e}")
        except Exception as e:
            print(f"❌ 一致性检查失败: {e}")
    
    def _sync_aggregation_tables(self, store_names: list):
        """备用方法：直接执行SQL更新预聚合表"""
        if not store_names:
            return
        
        session = SessionLocal()
        store_list = "', '".join(store_names)
        
        try:
            # 1. 删除旧数据
            tables = ['store_daily_summary', 'store_hourly_summary', 'category_daily_summary', 
                     'delivery_summary', 'product_daily_summary']
            for table in tables:
                try:
                    result = session.execute(
                        text(f"DELETE FROM {table} WHERE store_name IN ('{store_list}')")
                    )
                    if result.rowcount > 0:
                        print(f"   🗑️ {table}: 删除 {result.rowcount} 条")
                except:
                    pass
            session.commit()
            
            # 2. 调用全量重建脚本（简化处理）
            import subprocess
            result = subprocess.run(
                ['python', '全看板性能优化实施.py'],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print("   ✅ 预聚合表更新完成")
            else:
                print(f"   ⚠️ 预聚合表更新可能失败: {result.stderr[:200]}")
        except Exception as e:
            print(f"   ❌ 预聚合表更新失败: {e}")
        finally:
            session.close()
    
    def print_summary(self):
        """打印导入统计"""
        print("\n" + "="*60)
        print("📊 导入统计")
        print("="*60)
        print(f"文件总数: {self.stats['files_total']}")
        print(f"  ✅ 成功: {self.stats['files_success']}")
        print(f"  ⏭️ 跳过: {self.stats['files_skipped']}")
        print(f"  ❌ 失败: {self.stats['files_failed']}")
        print(f"\n订单统计:")
        print(f"  📥 新增: {self.stats['orders_inserted']:,}")
        print(f"  🔄 更新: {self.stats['orders_updated']:,}")
        print(f"  ⏭️ 跳过: {self.stats['orders_skipped']:,}")
        
        if self.stats['errors']:
            print(f"\n❌ 错误详情:")
            for err in self.stats['errors'][:5]:  # 最多显示5个
                print(f"  - {err['file']}: {err['error'][:50]}")
        
        # 显示数据库总量
        session = SessionLocal()
        try:
            total_orders = session.query(func.count(Order.id)).scalar()
            total_stores = session.query(func.count(func.distinct(Order.store_name))).scalar()
            print(f"\n📈 数据库总量:")
            print(f"  订单: {total_orders:,}")
            print(f"  门店: {total_stores}")
        finally:
            session.close()


def main():
    parser = argparse.ArgumentParser(description='批量导入数据到数据库')
    parser.add_argument('--path', '-p', default='./实际数据', help='数据文件目录')
    parser.add_argument('--mode', '-m', choices=['incremental', 'replace'], 
                       default='incremental', help='导入模式')
    
    args = parser.parse_args()
    
    importer = BatchDataImporterEnhanced(
        data_dir=args.path,
        mode=args.mode
    )
    importer.run()


if __name__ == "__main__":
    main()
