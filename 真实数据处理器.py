#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据接入和预处理模块
根据用户提供的实际数据优化算法参数和业务逻辑
"""

import pandas as pd
import numpy as np
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class RealDataProcessor:
    """真实数据处理器"""
    
    def __init__(self, data_dir: str = "实际数据"):
        self.data_dir = data_dir
        self.processed_data = {}
        self.data_quality_report = {}
        self.business_insights = {}
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        print(f"📂 数据处理器初始化完成，数据目录: {data_dir}")
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """加载所有可用数据"""
        
        print("🔍 搜索可用数据文件...")
        
        data_files = {
            'sales_data': self._find_file(['销售', 'sales', '商品', 'product']),
            'competitor_data': self._find_file(['竞对', 'competitor', '竞品']),
            'cost_data': self._find_file(['成本', 'cost', '费用']),
            'store_data': self._find_file(['门店', 'store', '店铺']),
            'order_data': self._find_file(['订单', 'order', '交易']),
            'historical_data': self._find_file(['历史', 'history', '趋势'])
        }
        
        loaded_data = {}
        
        for data_type, file_path in data_files.items():
            if file_path:
                try:
                    df = self._load_file(file_path)
                    loaded_data[data_type] = df
                    print(f"✅ 已加载 {data_type}: {len(df)} 条记录")
                    
                    # 生成数据质量报告
                    self.data_quality_report[data_type] = self._assess_data_quality(df)
                    
                except Exception as e:
                    print(f"❌ 加载 {data_type} 失败: {str(e)}")
            else:
                print(f"⚠️  未找到 {data_type} 数据文件")
        
        self.processed_data = loaded_data
        return loaded_data
    
    def _find_file(self, keywords: List[str]) -> Optional[str]:
        """根据关键词查找文件"""
        
        for file in os.listdir(self.data_dir):
            if file.endswith(('.xlsx', '.xls', '.csv')):
                for keyword in keywords:
                    if keyword in file:
                        return os.path.join(self.data_dir, file)
        return None
    
    def _load_file(self, file_path: str) -> pd.DataFrame:
        """加载单个数据文件"""
        
        if file_path.endswith('.csv'):
            # 尝试不同编码
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except:
                    continue
            raise ValueError(f"无法读取CSV文件: {file_path}")
        
        elif file_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """评估数据质量"""
        
        quality_report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': df.duplicated().sum(),
            'data_types': df.dtypes.to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'quality_score': 0.0
        }
        
        # 计算质量分数
        missing_rate = quality_report['missing_values'] / (len(df) * len(df.columns))
        duplicate_rate = quality_report['duplicate_rows'] / len(df)
        
        quality_score = max(0, 1.0 - missing_rate * 2 - duplicate_rate)
        quality_report['quality_score'] = round(quality_score, 3)
        
        return quality_report
    
    def standardize_sales_data(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """标准化销售数据（保持中文字段名，匹配问题诊断引擎）"""
        
        print("🔧 标准化销售数据...")
        
        # 字段映射 (映射为中文字段名，匹配诊断引擎需求)
        field_mapping = {
            # 商品信息
            '商品名称': ['商品名称', 'product_name', 'name', '名称', '商品'],
            '条码': ['条码', 'barcode', 'sku', 'SKU', '商品编码'],
            '一级分类名': ['美团一级分类', '一级分类名', 'category_l1', 'primary_category', '一级分类'],
            '三级分类名': ['美团三级分类', '三级分类名', 'category_l3', 'tertiary_category', '三级分类'],
            
            # 价格成本信息（匹配诊断引擎字段）
            '商品实售价': ['售价', '商品实售价', 'price', 'selling_price', '现价', '实售价'],
            '商品采购成本': ['商品采购成本', '成本', '原价', 'original_price', 'cost', 'list_price', '标价', '进货价', '商品原价'],
            '实收价格': ['实收价格', 'actual_price', 'received_price', '实付价格', '客户实付'],  # ✅ 新增：W列实收价格
            
            # 订单配送信息
            '订单ID': ['订单ID', 'order_id', 'orderId', '订单号'],
            '物流配送费': ['物流配送费', '配送费', 'delivery_fee', 'shipping_fee'],
            '平台佣金': ['平台佣金', '佣金', 'commission', 'platform_fee'],
            
            # 销量库存
            '月售': ['月售', 'monthly_sales', 'sales_volume', '月销量', '销量'],
            '库存': ['库存', 'stock', 'inventory', '存量', '剩余库存'],
            
            # 时段场景信息
            '时段': ['时段', 'time_period', '时间段'],
            '场景': ['场景', 'scene', 'scenario'],
            '商品角色': ['商品角色', 'product_role', '角色'],
            
            # 时间信息 ⭐ 重要: 增加"下单时间"映射
            '日期': ['日期', 'date', '下单时间', '采集时间', 'collect_time', 'timestamp', '时间', '创建时间'],
            '周': ['周', 'week', '星期'],
            '门店名称': ['门店名称', 'store_name', 'shop_name', '店名']
        }
        
        # 执行字段映射
        standardized_df = sales_df.copy()
        mapped_fields = {}
        
        for standard_field, possible_names in field_mapping.items():
            for possible_name in possible_names:
                if possible_name in standardized_df.columns:
                    if standard_field != possible_name:
                        standardized_df = standardized_df.rename(columns={possible_name: standard_field})
                    mapped_fields[standard_field] = possible_name
                    break
        
        # 数据类型转换和清洗（使用中文字段名）
        if '商品实售价' in standardized_df.columns:
            standardized_df['商品实售价'] = pd.to_numeric(standardized_df['商品实售价'], errors='coerce')
        
        if '商品采购成本' in standardized_df.columns:
            standardized_df['商品采购成本'] = pd.to_numeric(standardized_df['商品采购成本'], errors='coerce')
        
        if '月售' in standardized_df.columns:
            standardized_df['月售'] = pd.to_numeric(standardized_df['月售'], errors='coerce')
        
        if '库存' in standardized_df.columns:
            standardized_df['库存'] = pd.to_numeric(standardized_df['库存'], errors='coerce')
        
        if '物流配送费' in standardized_df.columns:
            standardized_df['物流配送费'] = pd.to_numeric(standardized_df['物流配送费'], errors='coerce')
        
        if '平台佣金' in standardized_df.columns:
            standardized_df['平台佣金'] = pd.to_numeric(standardized_df['平台佣金'], errors='coerce')
        
        # 日期类型转换
        if '日期' in standardized_df.columns:
            standardized_df['日期'] = pd.to_datetime(standardized_df['日期'], errors='coerce')
        
        # 计算衍生字段（匹配诊断引擎计算逻辑）
        if '商品实售价' in standardized_df.columns and '商品采购成本' in standardized_df.columns:
            # 单品毛利
            standardized_df['单品毛利'] = standardized_df['商品实售价'] - standardized_df['商品采购成本']
            # 单品毛利率（百分比）
            standardized_df['单品毛利率'] = (
                (standardized_df['单品毛利'] / standardized_df['商品实售价'].where(standardized_df['商品实售价'] > 0)) * 100
            ).fillna(0)
        
        if '月售' in standardized_df.columns and '库存' in standardized_df.columns:
            standardized_df['库存周转率'] = (
                standardized_df['月售'] / 
                standardized_df['库存'].where(standardized_df['库存'] > 0)
            )
        
        print(f"✅ 销售数据标准化完成: {len(standardized_df)} 条记录")
        print(f"📊 映射字段: {mapped_fields}")
        
        return standardized_df
    
    def analyze_business_patterns(self) -> Dict[str, Any]:
        """分析业务模式和特征"""
        
        if 'sales_data' not in self.processed_data:
            return {"error": "缺少销售数据"}
        
        sales_df = self.processed_data['sales_data']
        standardized_sales = self.standardize_sales_data(sales_df)
        
        analysis = {
            'data_overview': self._analyze_data_overview(standardized_sales),
            'price_analysis': self._analyze_price_patterns(standardized_sales),
            'sales_analysis': self._analyze_sales_patterns(standardized_sales),
            'category_analysis': self._analyze_category_patterns(standardized_sales),
            'optimization_suggestions': []
        }
        
        # 生成优化建议
        analysis['optimization_suggestions'] = self._generate_optimization_suggestions(analysis)
        
        self.business_insights = analysis
        return analysis
    
    def _analyze_data_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """数据总览分析"""
        
        return {
            'total_products': len(df),
            'unique_products': df['product_name'].nunique() if 'product_name' in df.columns else 0,
            'price_range': {
                'min': df['price'].min() if 'price' in df.columns else 0,
                'max': df['price'].max() if 'price' in df.columns else 0,
                'mean': df['price'].mean() if 'price' in df.columns else 0
            },
            'sales_range': {
                'min': df['monthly_sales'].min() if 'monthly_sales' in df.columns else 0,
                'max': df['monthly_sales'].max() if 'monthly_sales' in df.columns else 0,
                'mean': df['monthly_sales'].mean() if 'monthly_sales' in df.columns else 0
            },
            'categories': df['category_l1'].value_counts().to_dict() if 'category_l1' in df.columns else {}
        }
    
    def _analyze_price_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """价格模式分析"""
        
        if 'price' not in df.columns:
            return {"error": "缺少价格字段"}
        
        price_analysis = {
            'price_distribution': {
                'low_price': len(df[df['price'] <= df['price'].quantile(0.25)]),
                'medium_price': len(df[(df['price'] > df['price'].quantile(0.25)) & 
                                     (df['price'] <= df['price'].quantile(0.75))]),
                'high_price': len(df[df['price'] > df['price'].quantile(0.75)])
            }
        }
        
        # 价格与销量关系
        if 'monthly_sales' in df.columns:
            price_sales_corr = df[['price', 'monthly_sales']].corr().iloc[0, 1]
            price_analysis['price_sales_correlation'] = price_sales_corr
        
        # 毛利率分析
        if 'margin_rate' in df.columns:
            price_analysis['margin_distribution'] = {
                'high_margin': len(df[df['margin_rate'] > 0.3]),
                'medium_margin': len(df[(df['margin_rate'] > 0.1) & (df['margin_rate'] <= 0.3)]),
                'low_margin': len(df[df['margin_rate'] <= 0.1])
            }
        
        return price_analysis
    
    def _analyze_sales_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """销售模式分析"""
        
        if 'monthly_sales' not in df.columns:
            return {"error": "缺少销量字段"}
        
        # 销售分层分析
        high_sales_threshold = df['monthly_sales'].quantile(0.8)
        medium_sales_threshold = df['monthly_sales'].quantile(0.5)
        
        sales_analysis = {
            'sales_distribution': {
                'high_volume': len(df[df['monthly_sales'] >= high_sales_threshold]),
                'medium_volume': len(df[(df['monthly_sales'] >= medium_sales_threshold) & 
                                       (df['monthly_sales'] < high_sales_threshold)]),
                'low_volume': len(df[df['monthly_sales'] < medium_sales_threshold])
            },
            'top_products': df.nlargest(10, 'monthly_sales')[['product_name', 'monthly_sales']].to_dict('records')
        }
        
        # ABC分析 (帕累托分析)
        df_sorted = df.sort_values('monthly_sales', ascending=False)
        df_sorted['sales_cumsum'] = df_sorted['monthly_sales'].cumsum()
        total_sales = df_sorted['monthly_sales'].sum()
        
        df_sorted['sales_cumsum_pct'] = df_sorted['sales_cumsum'] / total_sales
        
        a_products = len(df_sorted[df_sorted['sales_cumsum_pct'] <= 0.8])
        b_products = len(df_sorted[(df_sorted['sales_cumsum_pct'] > 0.8) & 
                                  (df_sorted['sales_cumsum_pct'] <= 0.95)])
        c_products = len(df_sorted) - a_products - b_products
        
        sales_analysis['abc_analysis'] = {
            'A_products': a_products,
            'B_products': b_products, 
            'C_products': c_products
        }
        
        return sales_analysis
    
    def _analyze_category_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """品类模式分析"""
        
        if 'category_l1' not in df.columns:
            return {"error": "缺少分类字段"}
        
        category_stats = df.groupby('category_l1').agg({
            'product_name': 'count',
            'price': 'mean',
            'monthly_sales': 'sum' if 'monthly_sales' in df.columns else 'count'
        }).round(2)
        
        category_analysis = {
            'category_performance': category_stats.to_dict('index'),
            'dominant_categories': category_stats.sort_values('monthly_sales', ascending=False).head(5).index.tolist()
        }
        
        return category_analysis
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """基于分析结果生成优化建议"""
        
        suggestions = []
        
        # 基于价格分析的建议
        if 'price_analysis' in analysis:
            price_data = analysis['price_analysis']
            
            if 'price_sales_correlation' in price_data:
                correlation = price_data['price_sales_correlation']
                if correlation < -0.5:
                    suggestions.append("价格敏感度较高，建议实施竞争定价策略")
                elif correlation > 0.2:
                    suggestions.append("价格与销量正相关，可能存在品牌溢价空间")
        
        # 基于销售分析的建议
        if 'sales_analysis' in analysis:
            sales_data = analysis['sales_analysis']
            
            if 'abc_analysis' in sales_data:
                abc = sales_data['abc_analysis']
                a_ratio = abc['A_products'] / (abc['A_products'] + abc['B_products'] + abc['C_products'])
                
                if a_ratio < 0.2:
                    suggestions.append("A类商品占比较低，建议加强核心商品推广")
                
                if abc['C_products'] > abc['A_products'] * 2:
                    suggestions.append("C类商品过多，建议优化商品结构")
        
        # 基于品类分析的建议
        if 'category_analysis' in analysis:
            category_data = analysis['category_analysis']
            
            if 'dominant_categories' in category_data:
                dominant_cats = category_data['dominant_categories']
                if len(dominant_cats) <= 2:
                    suggestions.append("品类集中度较高，建议扩展多元化商品")
        
        return suggestions
    
    def generate_optimized_parameters(self) -> Dict[str, Any]:
        """基于真实数据生成优化参数"""
        
        if not self.business_insights:
            self.analyze_business_patterns()
        
        optimized_params = {
            'traffic_product_params': self._optimize_traffic_product_params(),
            'discount_product_params': self._optimize_discount_product_params(),
            'risk_assessment_params': self._optimize_risk_params(),
            'prediction_params': self._optimize_prediction_params()
        }
        
        return optimized_params
    
    def _optimize_traffic_product_params(self) -> Dict[str, float]:
        """优化流量品识别参数"""
        
        sales_data = self.processed_data.get('sales_data')
        if sales_data is None:
            return {"sales_weight": 0.4, "price_weight": 0.3, "brand_weight": 0.2, "correlation_weight": 0.1}
        
        standardized_sales = self.standardize_sales_data(sales_data)
        
        # 基于实际数据调整权重
        params = {"sales_weight": 0.4, "price_weight": 0.3, "brand_weight": 0.2, "correlation_weight": 0.1}
        
        if 'monthly_sales' in standardized_sales.columns:
            sales_std = standardized_sales['monthly_sales'].std()
            sales_mean = standardized_sales['monthly_sales'].mean()
            
            # 如果销量差异很大，增加销量权重
            if sales_std / sales_mean > 2.0:
                params["sales_weight"] = 0.5
                params["price_weight"] = 0.25
        
        return params
    
    def _optimize_discount_product_params(self) -> Dict[str, float]:
        """优化折扣品识别参数"""
        
        return {
            "inventory_weight": 0.4,
            "margin_weight": 0.3, 
            "seasonality_weight": 0.2,
            "category_weight": 0.1,
            "min_margin_threshold": 0.15,
            "inventory_turnover_threshold": 0.5
        }
    
    def _optimize_risk_params(self) -> Dict[str, float]:
        """优化风险评估参数"""
        
        return {
            "market_risk_weight": 0.4,
            "operational_risk_weight": 0.3,
            "financial_risk_weight": 0.3,
            "high_risk_threshold": 0.7,
            "medium_risk_threshold": 0.4
        }
    
    def _optimize_prediction_params(self) -> Dict[str, Any]:
        """优化预测模型参数"""
        
        return {
            "trend_window": 7,  # 趋势计算窗口期
            "seasonal_factor": 0.1,  # 季节性因子
            "noise_factor": 0.02,  # 随机噪声因子
            "confidence_interval": 0.95  # 置信区间
        }
    
    def export_optimization_config(self, output_path: str = "优化参数配置.json"):
        """导出优化配置"""
        
        config = {
            "generation_time": datetime.now().isoformat(),
            "data_sources": list(self.processed_data.keys()),
            "data_quality": self.data_quality_report,
            "business_insights": self.business_insights,
            "optimized_parameters": self.generate_optimized_parameters()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 优化配置已导出到: {output_path}")
        
        return config
    
    def generate_data_report(self) -> str:
        """生成数据质量和分析报告"""
        
        report = []
        report.append("# 📊 数据质量和业务分析报告\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 数据质量概览
        report.append("## 📋 数据质量概览\n")
        for data_type, quality in self.data_quality_report.items():
            report.append(f"### {data_type}")
            report.append(f"- 数据量: {quality['total_rows']} 行 × {quality['total_columns']} 列")
            report.append(f"- 缺失值: {quality['missing_values']} 个")
            report.append(f"- 重复行: {quality['duplicate_rows']} 行")
            report.append(f"- 质量评分: {quality['quality_score']:.3f}/1.000")
            report.append(f"- 内存占用: {quality['memory_usage_mb']:.2f} MB\n")
        
        # 业务分析洞察
        if self.business_insights:
            report.append("## 🎯 业务分析洞察\n")
            
            insights = self.business_insights
            
            if 'data_overview' in insights:
                overview = insights['data_overview']
                report.append("### 数据概览")
                report.append(f"- 商品总数: {overview['total_products']}")
                report.append(f"- 独特商品: {overview['unique_products']}")
                report.append(f"- 价格区间: ¥{overview['price_range']['min']:.2f} - ¥{overview['price_range']['max']:.2f}")
                report.append(f"- 平均价格: ¥{overview['price_range']['mean']:.2f}\n")
            
            if 'optimization_suggestions' in insights:
                report.append("### 🚀 优化建议")
                for i, suggestion in enumerate(insights['optimization_suggestions'], 1):
                    report.append(f"{i}. {suggestion}")
                report.append("")
        
        return "\n".join(report)


# 使用示例
if __name__ == "__main__":
    print("🎯 真实数据处理器测试运行")
    
    processor = RealDataProcessor("实际数据")
    
    # 如果有数据文件，将自动加载和分析
    loaded_data = processor.load_all_data()
    
    if loaded_data:
        print("\n📊 执行业务模式分析...")
        business_analysis = processor.analyze_business_patterns()
        
        print("\n🔧 生成优化参数...")
        optimized_params = processor.generate_optimized_parameters()
        
        print("\n📝 导出配置文件...")
        config = processor.export_optimization_config()
        
        print("\n📋 生成数据报告...")
        report = processor.generate_data_report()
        
        with open("数据分析报告.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        print("✅ 数据处理和分析完成！")
    else:
        print("ℹ️  未找到数据文件，请将数据文件放入 '实际数据' 目录")
        print("支持格式: .xlsx, .xls, .csv")
        print("建议文件名包含: 销售、竞对、成本、门店、订单、历史 等关键词")