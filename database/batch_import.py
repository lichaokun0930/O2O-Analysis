"""
P1任务：批量历史数据导入工具
支持导入指定目录下的所有Excel文件到数据库
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import glob
import os

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.models import Order, Product, DataUploadHistory
from 真实数据处理器 import RealDataProcessor


class BatchDataImporter:
    """批量数据导入器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.processor = RealDataProcessor()
        self.stats = {
            'files_processed': 0,
            'files_success': 0,
            'files_failed': 0,
            'total_orders': 0,
            'total_products': 0,
        }
    
    def find_excel_files(self):
        """查找所有Excel文件"""
        patterns = ['*.xlsx', '*.xls', '*.xlsm']
        files = []
        
        for pattern in patterns:
            files.extend(glob.glob(f"{self.data_dir}/**/{pattern}", recursive=True))
        
        # 过滤临时文件
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        
        return sorted(files)
    
    def extract_products(self, df: pd.DataFrame):
        """从订单数据中提取商品信息"""
        products = []
        seen = set()
        
        for _, row in df.iterrows():
            product_name = str(row.get('商品名称', ''))
            if product_name and product_name not in seen:
                seen.add(product_name)
                
                product = {
                    'name': product_name,
                    'barcode': str(row.get('商品条形码', '')) if pd.notna(row.get('商品条形码')) else None,
                    'category_level1': str(row.get('一级分类名', '')) if pd.notna(row.get('一级分类名')) else None,
                    'category_level2': str(row.get('二级分类名', '')) if pd.notna(row.get('二级分类名')) else None,
                    'category_level3': str(row.get('三级分类名', '')) if pd.notna(row.get('三级分类名')) else None,
                    'price': float(row.get('商品实售价', 0)) if pd.notna(row.get('商品实售价')) else 0,
                    'cost': float(row.get('商品采购成本', 0)) if pd.notna(row.get('商品采购成本')) else None,
                }
                products.append(product)
        
        return products
    
    def import_products_batch(self, products: list):
        """批量导入商品"""
        db = next(get_db())
        imported = 0
        updated = 0
        
        try:
            for product_data in products:
                # 检查是否已存在
                existing = db.query(Product).filter(Product.name == product_data['name']).first()
                
                if existing:
                    # 更新
                    for key, value in product_data.items():
                        if key != 'name' and value is not None:
                            setattr(existing, key, value)
                    updated += 1
                else:
                    # 新增
                    db.add(Product(**product_data))
                    imported += 1
                
                # 每100条提交一次
                if (imported + updated) % 100 == 0:
                    db.commit()
            
            db.commit()
            return imported, updated
            
        finally:
            db.close()
    
    def import_orders_batch(self, df: pd.DataFrame):
        """批量导入订单"""
        db = next(get_db())
        imported = 0
        updated = 0
        errors = 0
        
        # ✅ 日期列检查 (已经过standardize_sales_data处理,应该是"日期"列)
        date_col = None
        
        # 优先使用标准化后的"日期"列
        if '日期' in df.columns:
            date_col = '日期'
            print(f"[日期列] 使用标准化列: {date_col}")
        else:
            # 如果没有,尝试其他可能的列名
            possible_date_cols = ['下单时间', '采集时间', 'collect_time', 'timestamp', '时间', '创建时间', 'date', 'order_date', 'created_at']
            for possible_col in possible_date_cols:
                if possible_col in df.columns:
                    date_col = possible_col
                    print(f"[日期列] 使用备用列: {date_col}")
                    break
        
        if not date_col:
            print(f"[错误] 未找到日期列!")
            print(f"[可用列] {list(df.columns)[:10]}")
            raise ValueError("数据缺少日期列,无法导入")
        
        try:
            for idx, row in df.iterrows():
                try:
                    order_id = str(row.get('订单ID', ''))
                    if not order_id or order_id == 'nan':
                        continue
                    
                    existing = db.query(Order).filter(Order.order_id == order_id).first()
                    
                    # ✅ 使用识别到的日期列并进行安全转换
                    order_date = None
                    if date_col and pd.notna(row.get(date_col)):
                        try:
                            order_date = pd.to_datetime(row[date_col])
                            
                            # 检查日期是否有效
                            if pd.isna(order_date):
                                print(f"[警告] 订单 {order_id} 日期为NaT: {row.get(date_col)}")
                                order_date = None
                                
                        except Exception as e:
                            print(f"[警告] 订单 {order_id} 日期转换失败: {row.get(date_col)} - {e}")
                            order_date = None
                    
                    # ✅ 如果日期无效,跳过这条记录(不使用当前时间)
                    if order_date is None or pd.isna(order_date):
                        print(f"[跳过] 订单 {order_id} 缺少有效日期")
                        errors += 1
                        continue
                    
                    # 🔧 库存字段兼容性处理(支持多种列名)
                    stock_value = None
                    remaining_stock_value = None
                    
                    # 尝试读取库存字段(优先级从高到低)
                    for col in ['库存', 'stock', '期末库存']:
                        if col in row.index and pd.notna(row.get(col)):
                            stock_value = float(row[col]) if row[col] != '' else None
                            break
                    
                    # 尝试读取剩余库存字段
                    for col in ['剩余库存', 'remaining_stock', '当前库存']:
                        if col in row.index and pd.notna(row.get(col)):
                            remaining_stock_value = float(row[col]) if row[col] != '' else None
                            break
                    
                    order_data = {
                        'order_id': order_id,
                        'date': order_date,
                        'store_name': str(row.get('门店名称', 'UNKNOWN')),
                        'product_name': str(row.get('商品名称', '')),
                        'barcode': str(row.get('商品条形码', '')) if pd.notna(row.get('商品条形码')) else None,
                        'category_level1': str(row.get('一级分类名', '')) if pd.notna(row.get('一级分类名')) else None,
                        'category_level3': str(row.get('三级分类名', '')) if pd.notna(row.get('三级分类名')) else None,
                        'price': float(row.get('商品实售价', 0)) if pd.notna(row.get('商品实售价')) else 0,
                        'cost': float(row.get('商品采购成本', 0)) if pd.notna(row.get('商品采购成本')) else None,
                        'quantity': int(row.get('销售数量', 1)) if pd.notna(row.get('销售数量')) else 1,
                        'amount': float(row.get('实收金额', 0)) if pd.notna(row.get('实收金额')) else 0,
                        'channel': str(row.get('渠道', '')) if pd.notna(row.get('渠道')) else None,
                        'stock': int(stock_value) if stock_value is not None else 0,  # 🔧 库存
                        'remaining_stock': float(remaining_stock_value) if remaining_stock_value is not None else 0,  # 🔧 剩余库存
                    }
                    
                    if existing:
                        for key, value in order_data.items():
                            if key != 'order_id':
                                setattr(existing, key, value)
                        existing.updated_at = datetime.now()
                        updated += 1
                    else:
                        db.add(Order(**order_data))
                        imported += 1
                    
                    # 每50条提交一次
                    if (imported + updated) % 50 == 0:
                        db.commit()
                        
                except Exception as e:
                    db.rollback()
                    errors += 1
                    continue
            
            db.commit()
            return imported, updated, errors
            
        finally:
            db.close()
    
    def log_upload_history(self, filename: str, records: int, success: bool, error_msg: str = None):
        """记录上传历史"""
        db = next(get_db())
        
        try:
            history = DataUploadHistory(
                filename=filename,
                upload_date=datetime.now(),
                records_count=records,
                status='success' if success else 'failed',
                error_message=error_msg
            )
            db.add(history)
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
    
    def import_file(self, file_path: str):
        """导入单个文件"""
        filename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"[FILE] {filename}")
        print(f"{'='*60}")
        
        try:
            # 1. 加载数据
            print(f"[1/4] 加载Excel...")
            df = pd.read_excel(file_path)
            original_count = len(df)
            print(f"   {original_count:,} 行")
            
            # 2. 标准化
            print(f"[2/4] 标准化字段...")
            df = self.processor.standardize_sales_data(df)
            
            # 3. 业务过滤
            print(f"[3/4] 业务过滤...")
            if '一级分类名' in df.columns:
                df = df[df['一级分类名'] != '耗材'].copy()
            if '渠道' in df.columns:
                df = df[~df['渠道'].str.contains('咖啡', na=False)].copy()
            
            filtered_count = len(df)
            print(f"   保留 {filtered_count:,} 行")
            
            # 4. 导入数据
            print(f"[4/4] 导入数据库...")
            
            # 导入商品
            products = self.extract_products(df)
            p_imported, p_updated = self.import_products_batch(products)
            print(f"   商品: 新增 {p_imported}, 更新 {p_updated}")
            
            # 导入订单
            o_imported, o_updated, o_errors = self.import_orders_batch(df)
            print(f"   订单: 新增 {o_imported}, 更新 {o_updated}, 错误 {o_errors}")
            
            # 记录历史
            self.log_upload_history(filename, filtered_count, True)
            
            self.stats['files_success'] += 1
            self.stats['total_products'] += p_imported
            self.stats['total_orders'] += o_imported
            
            print(f"✅ 文件导入成功")
            return True
            
        except Exception as e:
            print(f"❌ 文件导入失败: {str(e)[:100]}")
            self.log_upload_history(filename, 0, False, str(e))
            self.stats['files_failed'] += 1
            return False
    
    def run(self):
        """执行批量导入"""
        print("\n" + "="*60)
        print("P1任务：批量历史数据导入")
        print("="*60)
        
        # 查找文件
        files = self.find_excel_files()
        
        if not files:
            print(f"\n未找到Excel文件: {self.data_dir}")
            return
        
        print(f"\n发现 {len(files)} 个Excel文件")
        for i, f in enumerate(files, 1):
            print(f"  {i}. {os.path.basename(f)}")
        
        # 确认导入
        print(f"\n即将导入这些文件到数据库，继续吗？")
        print(f"输入 'yes' 继续，其他任意键取消: ", end='')
        
        # 自动确认（用于脚本执行）
        confirm = 'yes'
        print(confirm)
        
        if confirm.lower() != 'yes':
            print("已取消导入")
            return
        
        # 逐个导入
        for file_path in files:
            self.stats['files_processed'] += 1
            self.import_file(file_path)
        
        # 最终统计
        print(f"\n" + "="*60)
        print("批量导入完成")
        print("="*60)
        print(f"文件总数: {len(files)}")
        print(f"成功: {self.stats['files_success']}")
        print(f"失败: {self.stats['files_failed']}")
        print(f"新增商品: {self.stats['total_products']}")
        print(f"新增订单: {self.stats['total_orders']}")
        
        # 验证数据库
        db = next(get_db())
        try:
            total_products = db.query(Product).count()
            total_orders = db.query(Order).count()
            print(f"\n数据库总计:")
            print(f"  商品: {total_products:,}")
            print(f"  订单: {total_orders:,}")
        finally:
            db.close()


if __name__ == "__main__":
    # 默认数据目录
    data_dir = r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据"
    
    # 如果提供了命令行参数，使用参数指定的目录
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
    importer = BatchDataImporter(data_dir)
    importer.run()
