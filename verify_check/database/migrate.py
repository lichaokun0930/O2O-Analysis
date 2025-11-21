"""
数据迁移脚本
将Excel数据导入PostgreSQL数据库
"""
import pandas as pd
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db_context, init_database, check_connection
from database.models import Order, Product, SceneTag, DataUploadHistory
from 真实数据处理器 import RealDataProcessor
from 商品场景智能打标引擎 import ProductSceneTagger


def calculate_file_hash(file_path: str) -> str:
    """计算文件MD5哈希"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def migrate_excel_to_database(excel_path: str, force_reimport: bool = False):
    """
    将Excel数据导入数据库
    
    Args:
        excel_path: Excel文件路径
        force_reimport: 是否强制重新导入（即使已导入过）
    """
    print("\n" + "="*80)
    print("[Data Migration] Excel -> PostgreSQL")
    print("="*80 + "\n")
    
    # 1. 检查数据库连接
    if not check_connection():
        print("❌ 数据库连接失败，请检查配置！")
        return False
    
    # 2. 初始化数据库表
    init_database()
    
    # 3. 检查文件是否已导入
    file_hash = calculate_file_hash(excel_path)
    file_size = Path(excel_path).stat().st_size
    file_name = Path(excel_path).name
    
    with get_db_context() as db:
        existing = db.query(DataUploadHistory).filter(
            DataUploadHistory.file_hash == file_hash
        ).first()
        
        if existing and not force_reimport:
            print(f"[INFO] File already imported on {existing.uploaded_at}")
            print(f"       Use --force to reimport")
            return True
    
    # 4. 加载Excel数据
    print(f"[Loading data] {file_name}")
    processor = RealDataProcessor(data_dir=str(PROJECT_ROOT / "实际数据"))
    
    try:
        # RealDataProcessor返回字典，取第一个DataFrame
        data_dict = processor.load_all_data()
        df = list(data_dict.values())[0] if data_dict else pd.DataFrame()
        print(f"[OK] Data loaded: {len(df)} rows")
    except Exception as e:
        print(f"[ERROR] Data load failed: {e}")
        return False
    
    # 5. 智能场景打标
    print("\n[Tagging scenes...]")
    tagger = ProductSceneTagger()
    try:
        df = tagger.tag_product_scenes(df)
        print("[OK] Scene tagging completed")
    except Exception as e:
        print(f"[WARNING] Scene tagging failed: {e}, continuing...")
    
    # 6. 开始导入数据
    print("\n[Importing data to database...]")
    
    rows_imported = 0
    rows_failed = 0
    error_messages = []
    
    with get_db_context() as db:
        try:
            # 6.1 导入商品主数据
            print("\n  [1/3] 导入商品表...")
            products_dict = {}
            
            for _, row in tqdm(df.groupby('商品名称').first().iterrows(), desc="  商品"):
                try:
                    barcode = str(row.get('条码', ''))
                    
                    # 检查商品是否存在
                    product = db.query(Product).filter(
                        Product.barcode == barcode
                    ).first()
                    
                    if not product:
                        product = Product(
                            product_name=row['商品名称'],
                            barcode=barcode,
                            store_code=str(row.get('店内码', '')),
                            category_level1=row.get('一级分类名', ''),
                            category_level3=row.get('三级分类名', ''),
                            current_price=float(row.get('商品实售价', 0)),
                            current_cost=float(row.get('商品采购成本', 0)),
                            stock=int(row.get('剩余库存', 0)),
                        )
                        db.add(product)
                        db.flush()  # 获取ID
                    
                    products_dict[row['商品名称']] = product.id
                    
                except Exception as e:
                    error_messages.append(f"商品导入错误: {row.get('商品名称', 'Unknown')} - {e}")
                    rows_failed += 1
            
            db.commit()
            print(f"  ✅ 商品表导入完成: {len(products_dict)} 个商品")
            
            # 6.2 导入订单数据
            print("\n  [2/3] 导入订单表...")
            
            for idx, row in tqdm(df.iterrows(), total=len(df), desc="  订单"):
                try:
                    order = Order(
                        order_id=str(row['订单ID']),
                        date=pd.to_datetime(row['日期']) if pd.notna(row.get('日期')) else datetime.now(),
                        store_name=row.get('门店名称', ''),
                        
                        # 关联商品
                        product_id=products_dict.get(row['商品名称']),
                        product_name=row['商品名称'],
                        barcode=str(row.get('条码', '')),
                        
                        # 分类
                        category_level1=row.get('一级分类名', ''),
                        category_level3=row.get('三级分类名', ''),
                        
                        # 价格
                        price=float(row.get('商品实售价', 0)),
                        original_price=float(row.get('商品原价', 0)),
                        cost=float(row.get('商品采购成本', 0)),
                        actual_price=float(row.get('实收价格', 0)),
                        
                        # 销量
                        quantity=int(row.get('月售', 1)),
                        amount=float(row.get('预计订单收入', row.get('订单零售额', 0))),  # ✅ 修复:存储"预计订单收入"而不是"销售额"
                        profit=float(row.get('利润额', row.get('实际利润', 0))),  # ✅ 修复:优先使用"利润额"字段
                        profit_margin=float(row.get('利润率', 0)),
                        
                        # 费用
                        delivery_fee=float(row.get('物流配送费', 0)),
                        commission=float(row.get('平台佣金', 0)),
                        platform_service_fee=float(row.get('平台服务费', 0)),  # 修复:正确映射平台服务费字段
                        
                        # 场景
                        scene=row.get('场景', ''),
                        time_period=row.get('时段', ''),
                        
                        # 其他
                        address=row.get('收货地址', ''),
                        channel=row.get('渠道', ''),
                    )
                    
                    db.add(order)
                    rows_imported += 1
                    
                    # 每1000条提交一次
                    if rows_imported % 1000 == 0:
                        db.commit()
                        
                except Exception as e:
                    error_messages.append(f"订单导入错误 (行{idx}): {e}")
                    rows_failed += 1
            
            db.commit()
            print(f"  ✅ 订单表导入完成: {rows_imported} 条订单")
            
            # 6.3 导入场景打标结果
            print("\n  [3/3] 导入场景打标结果...")
            
            scene_count = 0
            for product_name, product_id in tqdm(products_dict.items(), desc="  场景"):
                try:
                    product_rows = df[df['商品名称'] == product_name].iloc[0]
                    
                    scene_tag = SceneTag(
                        product_id=product_id,
                        base_scene=product_rows.get('场景', ''),
                        seasonal_scene=product_rows.get('季节场景', ''),
                        holiday_scene=product_rows.get('节假日场景', ''),
                        purchase_driver=product_rows.get('购买驱动', ''),
                        confidence=0.85,  # 默认置信度
                        algorithm_version='v1.0',
                    )
                    
                    db.add(scene_tag)
                    scene_count += 1
                    
                except Exception as e:
                    error_messages.append(f"场景打标导入错误: {product_name} - {e}")
            
            db.commit()
            print(f"  ✅ 场景打标结果导入完成: {scene_count} 个商品")
            
            # 7. 记录上传历史
            upload_history = DataUploadHistory(
                file_name=file_name,
                file_size=file_size,
                file_hash=file_hash,
                rows_imported=rows_imported,
                rows_failed=rows_failed,
                success=rows_failed == 0,
                error_log="\n".join(error_messages[:100]) if error_messages else None,
            )
            db.add(upload_history)
            db.commit()
            
            # 8. 显示结果
            print("\n" + "="*80)
            print("✅ 数据迁移完成！")
            print("="*80)
            print(f"\n📊 导入统计:")
            print(f"  - 商品数量: {len(products_dict)} 个")
            print(f"  - 订单数量: {rows_imported} 条")
            print(f"  - 场景标签: {scene_count} 个")
            print(f"  - 失败记录: {rows_failed} 条")
            
            if error_messages:
                print(f"\n⚠️ 部分记录导入失败（显示前5条）:")
                for msg in error_messages[:5]:
                    print(f"  - {msg}")
            
            print("\n🎉 数据库准备就绪，可以启动应用了！\n")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"\n❌ 数据导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='数据迁移工具')
    parser.add_argument(
        '--file',
        default='实际数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx',
        help='Excel文件路径'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新导入'
    )
    
    args = parser.parse_args()
    
    # 构建完整路径
    excel_path = PROJECT_ROOT / args.file
    
    if not excel_path.exists():
        print(f"❌ 文件不存在: {excel_path}")
        sys.exit(1)
    
    # 执行迁移
    success = migrate_excel_to_database(str(excel_path), args.force)
    sys.exit(0 if success else 1)
