#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能门店数据导入系统
- 自动识别新增数据文件
- 避免重复导入
- 自动数据完整性校验
"""

import pandas as pd
import os
import sys
import hashlib
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.connection import SessionLocal
from database.models import Order

# 导入历史记录文件
IMPORT_HISTORY_FILE = "学习数据仓库/import_history.json"

class SmartImporter:
    """智能数据导入器"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.import_history = self.load_import_history()
        self.validation_report = {
            'success': True,
            'warnings': [],
            'errors': [],
            'stats': {}
        }
    
    def load_import_history(self):
        """加载导入历史记录"""
        if os.path.exists(IMPORT_HISTORY_FILE):
            with open(IMPORT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_import_history(self):
        """保存导入历史记录"""
        os.makedirs(os.path.dirname(IMPORT_HISTORY_FILE), exist_ok=True)
        with open(IMPORT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.import_history, f, ensure_ascii=False, indent=2)
    
    def get_file_hash(self, filepath):
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_file_signature(self, filepath):
        """获取文件签名(hash + 修改时间)"""
        file_hash = self.get_file_hash(filepath)
        mod_time = os.path.getmtime(filepath)
        return {
            'hash': file_hash,
            'mod_time': mod_time,
            'size': os.path.getsize(filepath)
        }
    
    def scan_new_files(self):
        """扫描新增的Excel文件"""
        print("="*70)
        print(" 🔍 扫描新增数据文件")
        print("="*70)
        
        # 扫描所有Excel文件
        excel_files = []
        for pattern in ["实际数据/*.xlsx", "门店数据/*.xlsx", "门店数据/**/*.xlsx"]:
            excel_files.extend(Path(".").glob(pattern))
        
        # 过滤临时文件
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]
        
        print(f"\n找到 {len(excel_files)} 个Excel文件")
        
        # 识别新文件
        new_files = []
        updated_files = []
        skipped_files = []
        
        for file_path in excel_files:
            file_str = str(file_path)
            signature = self.get_file_signature(file_str)
            
            if file_str not in self.import_history:
                # 全新文件
                new_files.append((file_str, signature))
                print(f"  🆕 新文件: {file_path.name}")
            else:
                old_sig = self.import_history[file_str]
                if signature['hash'] != old_sig.get('hash'):
                    # 文件已更新
                    updated_files.append((file_str, signature))
                    print(f"  🔄 已更新: {file_path.name}")
                else:
                    # 已导入,跳过
                    skipped_files.append(file_str)
                    print(f"  ⏭️  已导入: {file_path.name}")
        
        print(f"\n📊 统计:")
        print(f"  新文件: {len(new_files)}")
        print(f"  更新文件: {len(updated_files)}")
        print(f"  跳过文件: {len(skipped_files)}")
        
        return new_files + updated_files
    
    def validate_excel_structure(self, df, file_name):
        """验证Excel数据结构"""
        print(f"\n  📋 验证数据结构: {file_name}")
        
        # 必需字段
        required_fields = [
            '订单ID', '门店名称', '商品名称', '商品实售价', 
            '销量', '一级分类名', '下单时间'
        ]
        
        # 重要字段(非必需但强烈建议)
        important_fields = [
            '成本', '利润额', '物流配送费', '平台佣金',
            '剩余库存', '条码', '店内码'
        ]
        
        validation_ok = True
        
        # 检查必需字段
        for field in required_fields:
            if field not in df.columns:
                self.validation_report['errors'].append(
                    f"❌ {file_name}: 缺少必需字段 '{field}'"
                )
                validation_ok = False
        
        # 检查重要字段
        for field in important_fields:
            if field not in df.columns:
                self.validation_report['warnings'].append(
                    f"⚠️  {file_name}: 缺少重要字段 '{field}'"
                )
        
        # 检查数据质量
        if '成本' in df.columns:
            non_zero_cost = len(df[df['成本'] > 0])
            cost_ratio = non_zero_cost / len(df) * 100 if len(df) > 0 else 0
            
            if cost_ratio < 50:
                self.validation_report['warnings'].append(
                    f"⚠️  {file_name}: 成本数据较少({cost_ratio:.1f}%有成本)"
                )
            
            print(f"    ✅ 成本字段: {non_zero_cost}/{len(df)} ({cost_ratio:.1f}%)")
        else:
            print(f"    ❌ 成本字段: 不存在")
        
        if '订单ID' in df.columns:
            unique_orders = df['订单ID'].nunique()
            print(f"    ✅ 订单数量: {unique_orders:,}")
        
        return validation_ok
    
    def import_file(self, file_path, signature):
        """导入单个文件"""
        print(f"\n{'='*70}")
        print(f" 📥 导入文件: {os.path.basename(file_path)}")
        print(f"{'='*70}")
        
        try:
            # 1. 读取Excel
            print(f"\n1️⃣ 读取Excel...")
            df = pd.read_excel(file_path)
            print(f"   总行数: {len(df):,}")
            
            # 2. 验证数据结构
            if not self.validate_excel_structure(df, os.path.basename(file_path)):
                return False
            
            # 3. 过滤耗材
            if '一级分类名' in df.columns:
                original_len = len(df)
                df = df[~df['一级分类名'].isin(['耗材'])]
                filtered_count = original_len - len(df)
                if filtered_count > 0:
                    print(f"\n2️⃣ 过滤数据: 移除 {filtered_count:,} 条耗材记录")
            
            # 4. 检查是否已存在该门店数据
            if '门店名称' in df.columns:
                store_name = df['门店名称'].iloc[0]
                existing = self.session.query(Order).filter(
                    Order.store_name == store_name
                ).first()
                
                if existing:
                    print(f"\n⚠️  检测到门店 '{store_name}' 已存在数据")
                    confirm = input("   是否覆盖? (yes/no): ").strip().lower()
                    if confirm != 'yes':
                        print("   ⏭️  跳过此文件")
                        return False
                    
                    # 删除旧数据
                    print(f"   🗑️  删除旧数据...")
                    self.session.query(Order).filter(
                        Order.store_name == store_name
                    ).delete()
                    self.session.commit()
            
            # 5. 导入数据
            print(f"\n3️⃣ 导入数据...")
            success_count = 0
            error_count = 0
            field_errors = {}  # 记录字段错误
            
            for idx, row in df.iterrows():
                try:
                    order_data = self.map_row_to_order(row)
                    order = Order(**order_data)
                    self.session.add(order)
                    success_count += 1
                    
                    # 每1000条提交一次
                    if success_count % 1000 == 0:
                        self.session.commit()
                        print(f"   进度: {success_count:,}/{len(df):,} ({success_count/len(df)*100:.1f}%)", end='\r')
                
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    field_errors[error_msg] = field_errors.get(error_msg, 0) + 1
                    
                    if error_count <= 3:
                        print(f"\n   ⚠️  第{idx+1}行失败: {e}")
            
            # 最终提交
            self.session.commit()
            
            print(f"\n\n4️⃣ 导入结果:")
            print(f"   ✅ 成功: {success_count:,}/{len(df):,} ({success_count/len(df)*100:.1f}%)")
            if error_count > 0:
                print(f"   ❌ 失败: {error_count:,}")
                print(f"\n   失败原因统计:")
                for error, count in field_errors.items():
                    print(f"     • {error}: {count}次")
            
            # 6. 数据完整性校验
            self.validate_imported_data(file_path, df, success_count)
            
            # 7. 更新导入历史
            self.import_history[file_path] = {
                **signature,
                'import_time': datetime.now().isoformat(),
                'rows_imported': success_count,
                'rows_failed': error_count
            }
            
            return True
            
        except Exception as e:
            self.session.rollback()
            self.validation_report['errors'].append(
                f"❌ 文件导入失败 {os.path.basename(file_path)}: {e}"
            )
            print(f"\n❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def map_row_to_order(self, row):
        """映射Excel行到Order对象"""
        return {
            'order_id': str(row.get('订单ID', '')),
            'date': pd.to_datetime(row.get('下单时间')) if pd.notna(row.get('下单时间')) else None,
            'store_name': str(row.get('门店名称', '')),
            'store_id': str(row.get('门店ID', '')),
            'product_name': str(row.get('商品名称', '')),
            'price': float(row.get('商品实售价', 0)),
            'original_price': float(row.get('商品原价', 0)),
            'quantity': int(row.get('销量', 0)),
            'cost': float(row.get('成本', 0)) if pd.notna(row.get('成本')) else 0.0,
            'profit': float(row.get('利润额', 0)) if pd.notna(row.get('利润额')) else 0.0,
            'category_level1': str(row.get('一级分类名', '')),
            'category_level3': str(row.get('三级分类名', '')),
            'barcode': str(row.get('条码', '')),
            'stock': int(row.get('剩余库存', 0)) if pd.notna(row.get('剩余库存')) else 0,
            'delivery_fee': float(row.get('物流配送费', 0)) if pd.notna(row.get('物流配送费')) else 0.0,
            'commission': float(row.get('平台佣金', 0)) if pd.notna(row.get('平台佣金')) else 0.0,
            'user_paid_delivery_fee': float(row.get('用户支付配送费', 0)) if pd.notna(row.get('用户支付配送费')) else 0.0,
            'delivery_discount': float(row.get('配送费减免金额', 0)) if pd.notna(row.get('配送费减免金额')) else 0.0,
            'full_reduction': float(row.get('满减金额', 0)) if pd.notna(row.get('满减金额')) else 0.0,
            'product_discount': float(row.get('商品减免金额', 0)) if pd.notna(row.get('商品减免金额')) else 0.0,
            'merchant_voucher': float(row.get('商家代金券', 0)) if pd.notna(row.get('商家代金券')) else 0.0,
            'merchant_share': float(row.get('商家承担部分券', 0)) if pd.notna(row.get('商家承担部分券')) else 0.0,
            'packaging_fee': float(row.get('打包袋金额', 0)) if pd.notna(row.get('打包袋金额')) else 0.0,
            'delivery_distance': float(row.get('配送距离', 0)) if pd.notna(row.get('配送距离')) else 0.0,
            'city': str(row.get('城市名称', '')),
            'address': str(row.get('收货地址', '')),
            'channel': str(row.get('渠道', '')),
            'actual_price': float(row.get('实收价格', 0)) if pd.notna(row.get('实收价格')) else 0.0,
            'amount': float(row.get('订单零售额', 0)) if pd.notna(row.get('订单零售额')) else 0.0,
        }
    
    def validate_imported_data(self, file_path, df_source, imported_count):
        """验证导入数据的完整性"""
        print(f"\n5️⃣ 数据完整性校验...")
        
        file_name = os.path.basename(file_path)
        
        # 1. 检查导入数量
        expected_count = len(df_source)
        if imported_count < expected_count:
            loss_ratio = (expected_count - imported_count) / expected_count * 100
            self.validation_report['warnings'].append(
                f"⚠️  {file_name}: 数据丢失 {expected_count - imported_count} 条 ({loss_ratio:.1f}%)"
            )
            print(f"   ⚠️  导入率: {imported_count}/{expected_count} ({imported_count/expected_count*100:.1f}%)")
        else:
            print(f"   ✅ 导入率: 100%")
        
        # 2. 获取数据库中的数据
        if '门店名称' in df_source.columns:
            store_name = df_source['门店名称'].iloc[0]
            db_orders = self.session.query(Order).filter(
                Order.store_name == store_name
            ).all()
            
            print(f"   数据库记录数: {len(db_orders):,}")
            
            # 3. 验证关键字段
            validation_fields = {
                '成本': ('cost', 'sum'),
                '利润额': ('profit', 'sum'),
                '商品实售价': ('price', 'sum'),
                '物流配送费': ('delivery_fee', 'sum'),
                '平台佣金': ('commission', 'sum'),
            }
            
            all_fields_ok = True
            
            for excel_field, (db_field, agg_method) in validation_fields.items():
                if excel_field in df_source.columns:
                    # Excel值
                    if agg_method == 'sum':
                        excel_value = df_source[excel_field].sum()
                    else:
                        excel_value = df_source[excel_field].mean()
                    
                    # 数据库值
                    db_values = [getattr(o, db_field, 0) or 0 for o in db_orders]
                    if agg_method == 'sum':
                        db_value = sum(db_values)
                    else:
                        db_value = sum(db_values) / len(db_values) if db_values else 0
                    
                    # 比较(允许0.01%误差)
                    if excel_value > 0:
                        diff_ratio = abs(db_value - excel_value) / excel_value * 100
                        if diff_ratio > 0.01:
                            all_fields_ok = False
                            self.validation_report['errors'].append(
                                f"❌ {file_name}: {excel_field}字段不匹配 "
                                f"(Excel:¥{excel_value:,.2f} vs DB:¥{db_value:,.2f}, 差异{diff_ratio:.2f}%)"
                            )
                            print(f"   ❌ {excel_field}: Excel=¥{excel_value:,.2f}, DB=¥{db_value:,.2f} (差异{diff_ratio:.2f}%)")
                        else:
                            print(f"   ✅ {excel_field}: ¥{db_value:,.2f}")
                    elif db_value == 0:
                        print(f"   ✅ {excel_field}: ¥0.00")
                    else:
                        all_fields_ok = False
                        self.validation_report['warnings'].append(
                            f"⚠️  {file_name}: {excel_field}字段异常 (Excel无数据但DB有¥{db_value:,.2f})"
                        )
                        print(f"   ⚠️  {excel_field}: Excel无数据, DB=¥{db_value:,.2f}")
            
            # 4. 特别检查成本字段(这是之前的问题)
            if '成本' in df_source.columns:
                source_cost_sum = df_source['成本'].sum()
                db_cost_sum = sum(o.cost or 0 for o in db_orders)
                
                if source_cost_sum > 0 and db_cost_sum == 0:
                    all_fields_ok = False
                    self.validation_report['errors'].append(
                        f"❌ {file_name}: 成本字段导入失败! Excel有¥{source_cost_sum:,.2f}但数据库为¥0"
                    )
                    print(f"\n   🚨 严重警告: 成本字段导入失败!")
                    print(f"      Excel成本总额: ¥{source_cost_sum:,.2f}")
                    print(f"      数据库成本总额: ¥{db_cost_sum:,.2f}")
            
            if all_fields_ok:
                print(f"\n   ✅ 所有字段校验通过!")
            else:
                self.validation_report['success'] = False
                print(f"\n   ❌ 部分字段校验失败,请检查上述错误!")
    
    def print_final_report(self):
        """打印最终报告"""
        print(f"\n{'='*70}")
        print(f" 📊 导入完成 - 最终报告")
        print(f"{'='*70}")
        
        if self.validation_report['success'] and not self.validation_report['errors']:
            print(f"\n✅ 所有数据导入成功,未发现错误!\n")
        else:
            if self.validation_report['errors']:
                print(f"\n❌ 发现 {len(self.validation_report['errors'])} 个错误:")
                for error in self.validation_report['errors']:
                    print(f"   {error}")
            
            if self.validation_report['warnings']:
                print(f"\n⚠️  发现 {len(self.validation_report['warnings'])} 个警告:")
                for warning in self.validation_report['warnings']:
                    print(f"   {warning}")
        
        print(f"\n{'='*70}\n")
    
    def run(self):
        """执行智能导入"""
        try:
            # 1. 扫描新文件
            new_files = self.scan_new_files()
            
            if not new_files:
                print(f"\n✅ 没有新数据需要导入!")
                return
            
            # 2. 确认导入
            print(f"\n准备导入 {len(new_files)} 个文件")
            confirm = input("是否继续? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("操作已取消")
                return
            
            # 3. 逐个导入
            success_files = []
            failed_files = []
            
            for file_path, signature in new_files:
                if self.import_file(file_path, signature):
                    success_files.append(file_path)
                else:
                    failed_files.append(file_path)
            
            # 4. 保存导入历史
            self.save_import_history()
            
            # 5. 打印最终报告
            self.print_final_report()
            
            print(f"导入统计:")
            print(f"  成功: {len(success_files)}")
            print(f"  失败: {len(failed_files)}")
            
        finally:
            self.session.close()

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           🚀 智能门店数据导入系统 v2.0                           ║
║                                                                  ║
║  功能:                                                           ║
║    ✅ 自动识别新增数据文件                                       ║
║    ✅ 避免重复导入老数据                                         ║
║    ✅ 自动数据完整性校验                                         ║
║    ✅ 导入问题实时报警                                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    importer = SmartImporter()
    importer.run()

if __name__ == "__main__":
    main()
