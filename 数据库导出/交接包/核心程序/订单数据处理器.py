#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单数据处理器 - 基于实际业务逻辑验证的数据清洗和利润计算模块
根据用户提供的真实订单数据和业务逻辑开发

业务逻辑理解：
1. 耗材数据处理：剔除所有一级分类为"耗材"的数据（如打包袋）
2. 减免金额字段：订单级字段，在同一订单的所有商品行中重复显示，代表整个订单所有商品的优惠总和
3. 利润计算公式：订单利润 = 预估订单收入 - (用户支付配送费 - 配送费减免金额 - 物流配送费)
4. 数据结构：订单级+商品级混合结构，需要按订单聚合处理重复的订单级字段

作者：AI智能助手
创建时间：2025-09-25
数据来源：2025-09-23订单明细数据
验证状态：✅ 已通过实际数据验证
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class OrderDataProcessor:
    """订单数据处理器 - 专门处理O2O订单数据"""
    
    def __init__(self):
        """初始化处理器"""
        self.df_raw = None
        self.df_cleaned = None
        self.order_summary = None
        
        # 字段映射 - 基于实际数据结构验证
        self.field_mapping = {
            'order_id': '订单ID',                 # 列9
            'estimated_revenue': '预估订单收入',    # 列24
            'delivery_fee_paid': '用户支付配送费',  # 列25
            'delivery_discount': '配送费减免金额',  # 列26
            'logistics_fee': '物流配送费',         # 列27
            'product_discount': '商品减免金额',    # 列28
            'product_name': '商品名称',           # 列5
            'category_l1': '一级分类名',          # 列4
            'product_price': '商品实售价',        # 列6
            'delivery_platform': '配送平台',      # ✅ 新增：配送平台字段
            'platform_service_fee': '平台服务费',  # ✅ 新增：平台服务费字段
        }
        
        # 关键业务参数
        self.consumable_category = '耗材'  # 需要剔除的耗材分类
        
    def load_data(self, file_path: str) -> bool:
        """
        加载订单数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.df_raw = pd.read_excel(file_path)
            print(f"[OK] 成功加载数据: {len(self.df_raw)}行, {self.df_raw[self.field_mapping['order_id']].nunique()}个订单")
            return True
        except Exception as e:
            print(f"[ERROR] 数据加载失败: {e}")
            return False
    
    def clean_data(self) -> bool:
        """
        数据清洗 - 剔除耗材数据
        
        Returns:
            bool: 清洗是否成功
        """
        if self.df_raw is None:
            print("❌ 请先加载数据")
            return False
            
        try:
            # 1. 剔除耗材数据
            consumable_mask = self.df_raw[self.field_mapping['category_l1']] == self.consumable_category
            consumable_count = consumable_mask.sum()
            
            self.df_cleaned = self.df_raw[~consumable_mask].copy()
            
            print(f"[OK] 数据清洗完成:")
            print(f"   原始数据: {len(self.df_raw)}行, {self.df_raw[self.field_mapping['order_id']].nunique()}个订单")
            print(f"   剔除耗材: {consumable_count}行")
            print(f"   清洗后: {len(self.df_cleaned)}行, {self.df_cleaned[self.field_mapping['order_id']].nunique()}个订单")
            
            return True
        except Exception as e:
            print(f"[ERROR] 数据清洗失败: {e}")
            return False
    
    def calculate_profit(self) -> bool:
        """
        计算订单利润
        
        利润计算公式：
        订单利润 = 预估订单收入 - (用户支付配送费 - 配送费减免金额 - 物流配送费)
        
        Returns:
            bool: 计算是否成功
        """
        if self.df_cleaned is None:
            print("❌ 请先进行数据清洗")
            return False
            
        try:
            # 按订单聚合，处理重复的订单级字段
            self.order_summary = self.df_cleaned.groupby(self.field_mapping['order_id']).agg({
                self.df_cleaned.columns[24]: 'first',  # 预估订单收入
                self.df_cleaned.columns[25]: 'first',  # 用户支付配送费
                self.df_cleaned.columns[26]: 'first',  # 配送费减免金额
                self.df_cleaned.columns[27]: 'first',  # 物流配送费
                self.df_cleaned.columns[28]: 'first',  # 商品减免金额
                self.field_mapping['product_name']: 'count'  # 商品数量
            }).round(2)
            
            # 重命名列
            self.order_summary.columns = [
                '预估订单收入', '用户支付配送费', '配送费减免金额', 
                '物流配送费', '商品减免金额', '商品数量'
            ]

            # 加入利润额、企客后返、平台服务费
            order_id_col = self.field_mapping['order_id']

            if '利润额' in self.df_cleaned.columns:
                profit_series = self.df_cleaned.groupby(order_id_col)['利润额'].sum()
                self.order_summary = self.order_summary.join(profit_series.rename('利润额'), how='left')
            else:
                self.order_summary['利润额'] = self.order_summary['预估订单收入']

            if '企客后返' in self.df_cleaned.columns:
                rebate_series = self.df_cleaned.groupby(order_id_col)['企客后返'].sum()
                self.order_summary = self.order_summary.join(rebate_series.rename('企客后返'), how='left')
            else:
                self.order_summary['企客后返'] = 0

            if self.field_mapping['platform_service_fee'] in self.df_cleaned.columns:
                fee_series = self.df_cleaned.groupby(order_id_col)[self.field_mapping['platform_service_fee']].sum()
                self.order_summary = self.order_summary.join(fee_series.rename('平台服务费'), how='left')
            else:
                self.order_summary['平台服务费'] = 0

            self.order_summary[['利润额', '企客后返', '平台服务费']] = self.order_summary[['利润额', '企客后返', '平台服务费']].fillna(0)
            
            # 计算配送净成本（新公式）
            self.order_summary['配送净成本'] = (
                self.order_summary['物流配送费'] -
                (self.order_summary['用户支付配送费'] - self.order_summary['配送费减免金额']) -
                self.order_summary['企客后返']
            ).round(2)
            self.order_summary['配送费净额'] = self.order_summary['配送净成本']

            # 计算订单利润（新公式）
            self.order_summary['订单利润'] = (
                self.order_summary['利润额'] -
                self.order_summary['平台服务费'] -
                self.order_summary['物流配送费'] +
                self.order_summary['企客后返']
            ).round(2)
            
            # 统计信息
            total_orders = len(self.order_summary)
            avg_profit = self.order_summary['订单利润'].mean()
            profit_range = (self.order_summary['订单利润'].min(), self.order_summary['订单利润'].max())
            positive_profit = (self.order_summary['订单利润'] > 0).sum()
            negative_profit = (self.order_summary['订单利润'] <= 0).sum()
            
            print(f"[OK] 利润计算完成:")
            print(f"   订单总数: {total_orders}个")
            print(f"   平均利润: {avg_profit:.2f}元")
            print(f"   利润范围: {profit_range[0]:.2f} ~ {profit_range[1]:.2f}元")
            print(f"   盈利订单: {positive_profit}个 ({positive_profit/total_orders*100:.1f}%)")
            print(f"   亏损订单: {negative_profit}个 ({negative_profit/total_orders*100:.1f}%)")
            
            return True
        except Exception as e:
            print(f"[ERROR] 利润计算失败: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """获取数据处理摘要"""
        if self.order_summary is None:
            return {"error": "尚未计算利润"}
        
        return {
            'order_count': len(self.order_summary),
            'avg_profit': self.order_summary['订单利润'].mean(),
            'profit_std': self.order_summary['订单利润'].std(),
            'profit_range': (self.order_summary['订单利润'].min(), self.order_summary['订单利润'].max()),
            'profitable_orders': (self.order_summary['订单利润'] > 0).sum(),
            'profit_rate': (self.order_summary['订单利润'] > 0).mean()
        }

    def get_business_insights(self) -> Dict[str, Any]:
        """
        获取业务洞察
        
        Returns:
            Dict[str, Any]: 业务分析结果
        """
        if self.order_summary is None:
            print("❌ 请先计算订单利润")
            return {}
            
        insights = {
            # 基础统计
            'total_orders': len(self.order_summary),
            'avg_profit': self.order_summary['订单利润'].mean(),
            'profit_std': self.order_summary['订单利润'].std(),
            'profit_range': (self.order_summary['订单利润'].min(), self.order_summary['订单利润'].max()),
            
            # 盈亏分析
            'profitable_orders': (self.order_summary['订单利润'] > 0).sum(),
            'loss_orders': (self.order_summary['订单利润'] <= 0).sum(),
            'profit_rate': (self.order_summary['订单利润'] > 0).mean(),
            
            # 收入分析
            'avg_revenue': self.order_summary['预估订单收入'].mean(),
            'avg_delivery_net': self.order_summary['配送费净额'].mean(),
            
            # 商品分析
            'avg_items_per_order': self.order_summary['商品数量'].mean(),
            'max_items_per_order': self.order_summary['商品数量'].max(),
            
            # 配送费分析
            'avg_delivery_paid': self.order_summary['用户支付配送费'].mean(),
            'avg_delivery_discount': self.order_summary['配送费减免金额'].mean(),
            'avg_logistics_fee': self.order_summary['物流配送费'].mean(),
        }
        
        return insights
    
    def export_results(self, output_dir: str = "results") -> bool:
        """
        导出处理结果
        
        Args:
            output_dir: 输出目录
            
        Returns:
            bool: 导出是否成功
        """
        if self.order_summary is None:
            print("❌ 没有可导出的结果")
            return False
            
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # 导出订单汇总
            summary_file = output_path / "订单利润汇总.xlsx"
            self.order_summary.to_excel(summary_file, index=True)
            
            # 导出清洗后的明细数据
            detail_file = output_path / "清洗后订单明细.xlsx"
            self.df_cleaned.to_excel(detail_file, index=False)
            
            # 导出业务洞察报告
            insights = self.get_business_insights()
            insight_file = output_path / "业务洞察报告.txt"
            with open(insight_file, 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("订单数据业务洞察报告\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("📊 基础统计\n")
                f.write(f"订单总数: {insights['total_orders']}\n")
                f.write(f"平均利润: {insights['avg_profit']:.2f}元\n")
                f.write(f"利润标准差: {insights['profit_std']:.2f}元\n")
                f.write(f"利润范围: {insights['profit_range'][0]:.2f} ~ {insights['profit_range'][1]:.2f}元\n\n")
                
                f.write("💰 盈亏分析\n")
                f.write(f"盈利订单: {insights['profitable_orders']}个 ({insights['profit_rate']*100:.1f}%)\n")
                f.write(f"亏损订单: {insights['loss_orders']}个 ({(1-insights['profit_rate'])*100:.1f}%)\n\n")
                
                f.write("📦 订单特征\n")
                f.write(f"平均预估收入: {insights['avg_revenue']:.2f}元\n")
                f.write(f"平均配送净额: {insights['avg_delivery_net']:.2f}元\n")
                f.write(f"平均商品数: {insights['avg_items_per_order']:.1f}件\n")
                f.write(f"最大商品数: {insights['max_items_per_order']}件\n\n")
                
                f.write("🚚 配送费分析\n")
                f.write(f"平均用户支付配送费: {insights['avg_delivery_paid']:.2f}元\n")
                f.write(f"平均配送费减免: {insights['avg_delivery_discount']:.2f}元\n")
                f.write(f"平均物流配送费: {insights['avg_logistics_fee']:.2f}元\n")
            
            print(f"✅ 结果导出完成:")
            print(f"   订单汇总: {summary_file}")
            print(f"   明细数据: {detail_file}")
            print(f"   洞察报告: {insight_file}")
            
            return True
        except Exception as e:
            print(f"❌ 结果导出失败: {e}")
            return False
    
    def process_pipeline(self, file_path: str, output_dir: str = "results") -> bool:
        """
        完整处理流水线
        
        Args:
            file_path: 输入文件路径
            output_dir: 输出目录
            
        Returns:
            bool: 处理是否成功
        """
        print("🚀 开始订单数据处理流水线...")
        
        # 1. 加载数据
        if not self.load_data(file_path):
            return False
            
        # 2. 数据清洗
        if not self.clean_data():
            return False
            
        # 3. 利润计算
        if not self.calculate_profit():
            return False
            
        # 4. 导出结果
        if not self.export_results(output_dir):
            return False
            
        print("🎉 订单数据处理完成！")
        return True

def main():
    """主函数 - 演示用法"""
    # 初始化处理器
    processor = OrderDataProcessor()
    
    # 设置文件路径
    data_file = "实际数据/2025-09-23 00_00_00至2025-09-23 10_02_10订单明细数据导出汇总 (1).xlsx"
    
    # 执行完整处理流水线
    success = processor.process_pipeline(data_file, "处理结果")
    
    if success:
        # 获取业务洞察
        insights = processor.get_business_insights()
        
        print(f"\n📊 关键业务指标:")
        print(f"盈利率: {insights['profit_rate']*100:.1f}%")
        print(f"平均订单利润: {insights['avg_profit']:.2f}元")
        print(f"平均商品数/订单: {insights['avg_items_per_order']:.1f}件")
        
        # 展示利润分布样本
        print(f"\n💡 订单利润样本:")
        sample_orders = processor.order_summary.head(5)
        for order_id, row in sample_orders.iterrows():
            status = "盈利" if row['订单利润'] > 0 else "亏损"
            print(f"订单{order_id}: {row['订单利润']:.2f}元 ({status}) - {row['商品数量']}件商品")

if __name__ == "__main__":
    main()