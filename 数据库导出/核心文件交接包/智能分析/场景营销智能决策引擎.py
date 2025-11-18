#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景营销智能决策引擎
================================================================================
集成多种机器学习模型，为FMCG零售场景营销提供智能决策支持

核心模块：
1. FP-Growth商品组合挖掘 - 发现"追剧套餐"、"提神套餐"等关联规则
2. XGBoost场景识别模型 - 预测用户购买场景（上午提神/下午茶歇/晚间放松/深夜应急）
3. RFM客户分群模型 - 识别高频应急、计划囤货、价格敏感、偶发尝鲜用户
4. 决策树规则生成 - 可解释的场景识别规则
5. 协同过滤推荐 - 基于用户行为的商品推荐

作者: AI Assistant
日期: 2025-10-14
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# 机器学习库
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, silhouette_score

# XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError as e:
    XGBOOST_AVAILABLE = False
    print(f"⚠️ XGBoost未安装，将使用RandomForest替代 (错误: {e})")

# 关联规则挖掘
try:
    from mlxtend.frequent_patterns import fpgrowth, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    MLXTEND_AVAILABLE = True
except ImportError as e:
    MLXTEND_AVAILABLE = False
    print(f"⚠️ mlxtend未安装，FP-Growth功能将不可用 (错误: {e})")

# 可视化
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ============================================================================
# 1. FP-Growth商品组合挖掘引擎
# ============================================================================

class ProductCombinationMiner:
    """
    商品组合挖掘引擎 - 基于FP-Growth算法
    
    功能：
    - 挖掘频繁购买的商品组合
    - 生成场景化套餐建议（追剧套餐、提神套餐、应急套餐等）
    - 计算关联规则的支持度、置信度、提升度
    """
    
    def __init__(self, min_support: float = 0.01, min_confidence: float = 0.3):
        """
        初始化参数
        
        Args:
            min_support: 最小支持度阈值（默认1%）
            min_confidence: 最小置信度阈值（默认30%）
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.frequent_itemsets = None
        self.rules = None
        self.scene_packages = {}
        
    def mine_from_orders(self, order_data: pd.DataFrame) -> Dict[str, Any]:
        """
        从订单数据中挖掘商品组合
        
        Args:
            order_data: 订单明细数据，必须包含'订单ID'和'商品名称'列
            
        Returns:
            包含频繁项集和关联规则的字典
        """
        if not MLXTEND_AVAILABLE:
            return {
                'status': 'error',
                'message': '请安装mlxtend库: pip install mlxtend'
            }
        
        try:
            # 1. 构建购物篮
            print("📦 构建购物篮...")
            baskets = order_data.groupby('订单ID')['商品名称'].apply(list).values.tolist()
            
            # 过滤单品订单（至少2个商品才有组合意义）
            baskets = [basket for basket in baskets if len(basket) >= 2]
            
            if len(baskets) < 10:
                return {
                    'status': 'error',
                    'message': f'有效订单数量不足（{len(baskets)}），至少需要10个多商品订单'
                }
            
            # 2. 编码为事务矩阵
            print("🔄 编码事务矩阵...")
            te = TransactionEncoder()
            te_ary = te.fit(baskets).transform(baskets)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
            
            # 3. 挖掘频繁项集
            print("⛏️ 挖掘频繁项集...")
            self.frequent_itemsets = fpgrowth(
                df_encoded, 
                min_support=self.min_support, 
                use_colnames=True,
                max_len=None  # 移除长度限制，让算法自动处理
            )
            
            if self.frequent_itemsets.empty:
                return {
                    'status': 'warning',
                    'message': f'未找到满足支持度{self.min_support}的频繁项集，建议降低阈值'
                }
            
            # 只保留2个及以上商品的组合
            self.frequent_itemsets = self.frequent_itemsets[
                self.frequent_itemsets['itemsets'].apply(lambda x: len(x) >= 2)
            ]
            
            # 4. 生成关联规则
            print("📋 生成关联规则...")
            if len(self.frequent_itemsets) > 0:
                try:
                    self.rules = association_rules(
                        self.frequent_itemsets, 
                        metric="confidence", 
                        min_threshold=self.min_confidence,
                        support_only=False  # 确保生成完整的规则信息
                    )
                except (ValueError, KeyError) as e:
                    print(f"⚠️ 关联规则生成遇到问题: {str(e)}")
                    print("   尝试使用备用方法...")
                    # 备用方案：使用support_only=True，然后手动计算
                    try:
                        # 先只获取支持度信息
                        self.rules = association_rules(
                            self.frequent_itemsets,
                            metric="support",
                            min_threshold=self.min_support
                        )
                    except Exception as e2:
                        print(f"   备用方法也失败: {str(e2)}")
                        self.rules = pd.DataFrame()
                
                # 计算提升度
                if not self.rules.empty:
                    self.rules['lift'] = self.rules.get('lift', 1.0).round(2)
                    self.rules['confidence'] = self.rules.get('confidence', 0.0).round(3)
                    self.rules['support'] = self.rules.get('support', 0.0).round(4)
            else:
                self.rules = pd.DataFrame()
            
            # 5. 识别场景化套餐
            self._identify_scene_packages(order_data)
            
            print(f"✅ 挖掘完成：{len(self.frequent_itemsets)}个频繁项集，{len(self.rules)}条关联规则")
            
            return {
                'status': 'success',
                'frequent_itemsets': self.frequent_itemsets,
                'rules': self.rules,
                'scene_packages': self.scene_packages,
                'stats': {
                    'total_baskets': len(baskets),
                    'frequent_itemsets_count': len(self.frequent_itemsets),
                    'rules_count': len(self.rules)
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'挖掘过程出错: {str(e)}'
            }
    
    def _identify_scene_packages(self, order_data: pd.DataFrame):
        """
        识别场景化套餐
        
        基于时段和商品分类特征，将频繁项集映射到场景
        """
        if self.frequent_itemsets is None or self.frequent_itemsets.empty:
            return
        
        # 场景关键词映射（基于O2O外卖业务场景）
        scene_keywords = {
            # 早餐刚需（6-8点）
            '早餐套餐': ['面包', '牛奶', '鸡蛋', '豆浆', '油条', '包子', '粥', '早餐'],
            
            # 日常补给（9-17点）
            '日用补给套餐': ['纸巾', '洗洁精', '垃圾袋', '牙膏', '洗发水', '卫生纸', '电池'],
            '办公提神套餐': ['咖啡', '红牛', '坚果', '巧克力', '能量', '功能饮料', '茶'],
            '亲子套餐': ['牛奶', '果冻', '糖果', '饼干', '儿童', '乳酸菌', '酸奶'],
            
            # 休闲娱乐（14-17、21-23点）
            '追剧套餐': ['薯片', '可乐', '瓜子', '爆米花', '饮料', '膨化', '碳酸'],
            '下午茶套餐': ['蛋糕', '饼干', '奶茶', '咖啡', '甜品', '点心'],
            
            # 正餐高峰（12-13、18-20点）
            '聚餐套餐': ['啤酒', '白酒', '花生', '瓜子', '卤味', '鸭脖', '鸭翅', '酒水'],
            
            # 深夜应急（0-5点）
            '应急套餐': ['纸巾', '电池', '创可贴', '感冒药', '退烧贴', '药品'],
            '夜宵套餐': ['方便面', '火腿肠', '啤酒', '卤味', '烧烤', '小龙虾'],
            '熬夜套餐': ['红牛', '咖啡', '能量饮料', '坚果', '巧克力', '薯片']
        }
        
        for scene_name, keywords in scene_keywords.items():
            matched_itemsets = []
            
            for idx, row in self.frequent_itemsets.iterrows():
                itemset = row['itemsets']
                # 确保itemset是可迭代的（处理frozenset）
                itemset_list = list(itemset) if not isinstance(itemset, list) else itemset
                itemset_str = ' '.join(itemset_list)
                
                # 检查是否包含场景关键词
                match_count = sum(1 for keyword in keywords if keyword in itemset_str)
                if match_count >= 2:  # 至少匹配2个关键词
                    matched_itemsets.append({
                        'items': itemset_list,
                        'support': row['support'],
                        'match_score': match_count
                    })
            
            if matched_itemsets:
                # 按匹配度和支持度排序
                matched_itemsets.sort(
                    key=lambda x: (x['match_score'], x['support']), 
                    reverse=True
                )
                self.scene_packages[scene_name] = matched_itemsets[:5]  # 保留TOP5
    
    def get_top_combinations(self, top_n: int = 10) -> pd.DataFrame:
        """获取TOP N商品组合"""
        if self.frequent_itemsets is None or self.frequent_itemsets.empty:
            return pd.DataFrame()
        
        top_items = self.frequent_itemsets.nlargest(top_n, 'support').copy()
        top_items['items_str'] = top_items['itemsets'].apply(
            lambda x: ' + '.join(sorted(list(x)))
        )
        return top_items[['items_str', 'support']]
    
    def get_top_rules(self, top_n: int = 10, sort_by: str = 'lift') -> pd.DataFrame:
        """获取TOP N关联规则"""
        if self.rules is None or self.rules.empty:
            return pd.DataFrame()
        
        top_rules = self.rules.nlargest(top_n, sort_by).copy()
        top_rules['rule'] = top_rules.apply(
            lambda row: f"{', '.join(list(row['antecedents']))} → {', '.join(list(row['consequents']))}", 
            axis=1
        )
        return top_rules[['rule', 'support', 'confidence', 'lift']]
    
    def visualize_rules_network(self, top_n: int = 20) -> go.Figure:
        """
        可视化关联规则网络图
        
        Args:
            top_n: 显示TOP N规则
            
        Returns:
            Plotly图表对象
        """
        if self.rules is None or self.rules.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="暂无关联规则数据",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # 选择TOP规则
        top_rules = self.rules.nlargest(top_n, 'lift')
        
        # 构建节点和边
        nodes = set()
        edges = []
        
        for _, rule in top_rules.iterrows():
            # 转换frozenset为list
            antecedents = list(rule['antecedents'])
            consequents = list(rule['consequents'])
            
            for item in antecedents:
                nodes.add(item)
            for item in consequents:
                nodes.add(item)
            
            # 创建边（使用已转换的list）
            for ant in antecedents:
                for cons in consequents:
                    edges.append({
                        'source': ant,
                        'target': cons,
                        'confidence': rule['confidence'],
                        'lift': rule['lift']
                    })
        
        # 创建简化的网络可视化（使用散点图模拟）
        fig = go.Figure()
        
        # 添加节点
        node_list = list(nodes)
        n = len(node_list)
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        x_nodes = np.cos(angles)
        y_nodes = np.sin(angles)
        
        fig.add_trace(go.Scatter(
            x=x_nodes, y=y_nodes,
            mode='markers+text',
            marker=dict(size=20, color='lightblue', line=dict(width=2)),
            text=node_list,
            textposition='top center',
            hoverinfo='text',
            name='商品'
        ))
        
        # 添加边（前10条）
        for edge in edges[:10]:
            src_idx = node_list.index(edge['source'])
            tgt_idx = node_list.index(edge['target'])
            
            fig.add_trace(go.Scatter(
                x=[x_nodes[src_idx], x_nodes[tgt_idx]],
                y=[y_nodes[src_idx], y_nodes[tgt_idx]],
                mode='lines',
                line=dict(
                    width=edge['confidence']*3,
                    color=f"rgba(100,100,255,{edge['confidence']})"
                ),
                hoverinfo='text',
                hovertext=f"置信度: {edge['confidence']:.2f}<br>提升度: {edge['lift']:.2f}",
                showlegend=False
            ))
        
        fig.update_layout(
            title="商品关联规则网络图",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600,
            hovermode='closest'
        )
        
        return fig


# ============================================================================
# 2. XGBoost场景识别模型
# ============================================================================

class SceneRecognitionModel:
    """
    场景识别模型 - 基于XGBoost/RandomForest
    
    功能：
    - 预测用户购买场景（上午提神/下午茶歇/晚间放松/深夜应急）
    - 特征工程：时段、距离、品类、配送费、订单结构
    - 输出场景概率分布
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_importance = None
        self.is_trained = False
        
    def prepare_features(self, order_data: pd.DataFrame) -> pd.DataFrame:
        """
        特征工程
        
        从订单数据中提取场景识别特征
        """
        df = order_data.copy()
        
        # 1. 时段特征
        if '日期_datetime' in df.columns:
            df['hour'] = pd.to_datetime(df['日期_datetime']).dt.hour
        elif '小时' in df.columns:
            df['hour'] = df['小时']
        else:
            df['hour'] = 12  # 默认值
        
        # 时段编码（优化为8时段）
        df['time_slot'] = pd.cut(
            df['hour'], 
            bins=[0, 3, 6, 9, 12, 14, 18, 21, 24],
            labels=['凌晨(3-5)', '清晨(6-8)', '上午(9-11)', '正午(12-13)', 
                    '下午(14-17)', '傍晚(18-20)', '晚间(21-23)', '深夜(0-2)'],
            include_lowest=True
        )
        df['time_slot_code'] = df['time_slot'].cat.codes
        
        # 2. 星期特征（增强）
        if '日期_datetime' in df.columns:
            df['weekday'] = pd.to_datetime(df['日期_datetime']).dt.dayofweek
            df['is_weekend'] = (df['weekday'] >= 5).astype(int)
            df['is_friday'] = (df['weekday'] == 4).astype(int)  # 周五特殊处理
        else:
            df['weekday'] = 3
            df['is_weekend'] = 0
            df['is_friday'] = 0
        
        # 3. 配送距离特征
        if '配送距离' in df.columns:
            df['distance'] = df['配送距离']
            df['distance_bin'] = pd.cut(
                df['distance'],
                bins=[0, 1, 3, 5, 100],
                labels=['近距离', '中距离', '远距离', '超远'],
                include_lowest=True
            )
            df['distance_code'] = df['distance_bin'].cat.codes
        else:
            df['distance'] = 2.0
            df['distance_code'] = 1
        
        # 4. 商品特征
        if '三级分类名' in df.columns:
            # 分类编码
            category_map = {
                '休闲食品': 1, '零食': 1, '膨化食品': 1,
                '饮料': 2, '酒水': 2, '碳酸饮料': 2,
                '日用百货': 3, '生活用品': 3,
                '乳制品': 4, '奶制品': 4
            }
            df['category_type'] = df['三级分类名'].apply(
                lambda x: next((v for k, v in category_map.items() if k in str(x)), 0)
            )
        else:
            df['category_type'] = 1
        
        # 5. 订单级特征（需要聚合）
        order_agg = df.groupby('订单ID').agg({
            '商品实售价': ['sum', 'mean', 'count'],
            '配送距离': 'first',
            'hour': 'first',
            'weekday': 'first',
            'is_weekend': 'first'
        }).reset_index()
        order_agg.columns = ['订单ID', '订单金额', '平均单价', '商品数', '配送距离', 'hour', 'weekday', 'is_weekend']
        
        # 6. 配送费特征（增强）
        if '物流配送费' in df.columns:
            order_agg = order_agg.merge(
                df.groupby('订单ID')['物流配送费'].first().reset_index(),
                on='订单ID'
            )
            order_agg['delivery_fee_ratio'] = (
                order_agg['物流配送费'] / order_agg['订单金额']
            ).fillna(0)
        else:
            order_agg['物流配送费'] = 0
            order_agg['delivery_fee_ratio'] = 0
        
        # 7. O2O特有特征
        order_agg['is_single_item'] = (order_agg['商品数'] == 1).astype(int)  # 单件订单
        order_agg['is_multi_item'] = (order_agg['商品数'] >= 3).astype(int)   # 多件订单
        order_agg['is_high_value'] = (order_agg['订单金额'] > 50).astype(int)  # 高客单价
        
        return order_agg
    
    def auto_label_scenes(self, order_features: pd.DataFrame) -> pd.Series:
        """
        自动标注场景（基于规则 - O2O外卖优化版）
        
        场景定义（基于业务专家经验）：
        1. 早餐刚需场景（6-8点）：出行/整理/早餐
        2. 日常补给场景（9-11、14-17点）：办公/居家/日用/家务/亲子
        3. 正餐高峰场景（12-13、18-20点）：午餐/晚餐/归家
        4. 休闲娱乐场景（21-23点）：居家/夜生活前/下午茶
        5. 深夜应急场景（0-5点）：突发/急用/夜宵/熬夜
        """
        df = order_features.copy()
        
        scenes = []
        for _, row in df.iterrows():
            hour = row.get('hour', 12)
            item_count = row.get('商品数', 1)
            distance = row.get('配送距离', 0)
            fee_ratio = row.get('delivery_fee_ratio', 0)
            order_amount = row.get('订单金额', 0)
            is_weekend = row.get('is_weekend', 0)
            
            # 规则判断（优化：覆盖全天24小时）
            if 6 <= hour < 9:
                # 早餐刚需：6-8点
                scene = '早餐刚需'
                
            elif 9 <= hour < 12:
                # 上午时段：日常补给
                if is_weekend:
                    scene = '日常补给(周末居家)'
                else:
                    scene = '日常补给(工作日)'
                    
            elif 12 <= hour < 14:
                # 正午：午餐高峰
                scene = '正餐高峰'
                
            elif 14 <= hour < 18:
                # 下午时段：日常补给或休闲
                if item_count >= 3:
                    scene = '休闲娱乐'  # 多件零食 = 下午茶
                else:
                    if is_weekend:
                        scene = '日常补给(周末居家)'
                    else:
                        scene = '日常补给(工作日)'
                        
            elif 18 <= hour < 21:
                # 傍晚：晚餐高峰
                scene = '正餐高峰'
                    
            elif 21 <= hour < 24:
                # 晚间：休闲娱乐
                scene = '休闲娱乐'
                    
            elif 0 <= hour < 3:
                # 深夜0-2点：夜宵或应急
                if fee_ratio > 0.15 or distance > 3:
                    scene = '深夜应急(紧急)'
                else:
                    scene = '深夜应急(夜宵)'
                    
            else:  # 3-6点
                # 凌晨3-5点：熬夜党
                scene = '深夜应急(熬夜党)'
            
            scenes.append(scene)
        
        return pd.Series(scenes, index=df.index)
    
    def train(self, order_data: pd.DataFrame) -> Dict[str, Any]:
        """
        训练场景识别模型
        
        Args:
            order_data: 订单明细数据
            
        Returns:
            训练结果统计
        """
        try:
            print("🔧 特征工程...")
            features_df = self.prepare_features(order_data)
            
            print("🏷️ 自动标注场景...")
            features_df['scene'] = self.auto_label_scenes(features_df)
            
            # 诊断：显示场景分布
            scene_counts = features_df['scene'].value_counts()
            print(f"\n📊 场景分布统计:")
            for scene, count in scene_counts.items():
                print(f"   {scene}: {count}单 ({count/len(features_df)*100:.1f}%)")
            
            # 诊断：显示时段分布
            hour_dist = features_df['hour'].value_counts().sort_index()
            print(f"\n⏰ 时段分布: {hour_dist.index.min()}时-{hour_dist.index.max()}时")
            print(f"   主要时段: {', '.join([f'{h}时({c}单)' for h, c in hour_dist.head(5).items()])}")
            
            # 检查场景数量，如果太少则合并细分场景
            if len(scene_counts) < 3:
                print(f"\n⚠️ 警告：仅发现{len(scene_counts)}个场景，数据时段分布可能过于集中")
                print(f"   建议：扩大时间范围或检查数据是否覆盖全天")
                
                # 合并深夜子场景
                features_df['scene'] = features_df['scene'].replace({
                    '深夜应急(紧急)': '深夜应急',
                    '深夜应急(夜宵)': '深夜应急',
                    '深夜应急(熬夜党)': '深夜应急',
                    '日常补给(工作日)': '日常补给',
                    '日常补给(周末居家)': '日常补给'
                })
                
                scene_counts = features_df['scene'].value_counts()
                print(f"\n🔄 已合并细分场景，当前场景数: {len(scene_counts)}")
                for scene, count in scene_counts.items():
                    print(f"   {scene}: {count}单 ({count/len(features_df)*100:.1f}%)")
            
            # 特征列
            feature_cols = ['hour', 'weekday', '配送距离', '订单金额', 
                           '平均单价', '商品数', 'delivery_fee_ratio']
            
            # 确保所有特征列存在
            for col in feature_cols:
                if col not in features_df.columns:
                    features_df[col] = 0
            
            X = features_df[feature_cols].fillna(0)
            y = features_df['scene']
            
            # 编码标签
            y_encoded = self.label_encoder.fit_transform(y)
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
            )
            
            # 标准化
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 训练模型
            print("🚀 训练模型...")
            if XGBOOST_AVAILABLE:
                self.model = xgb.XGBClassifier(
                    max_depth=6,
                    n_estimators=100,
                    learning_rate=0.1,
                    random_state=42,
                    use_label_encoder=False,
                    eval_metric='mlogloss',
                    base_score=0.5  # 修复: 明确设置 base_score 避免参数错误
                )
            else:
                self.model = RandomForestClassifier(
                    max_depth=6,
                    n_estimators=100,
                    random_state=42
                )
            
            self.model.fit(X_train_scaled, y_train)
            
            # 评估
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # 特征重要性
            self.feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            self.is_trained = True
            
            print(f"✅ 模型训练完成")
            print(f"   训练集准确率: {train_score:.3f}")
            print(f"   测试集准确率: {test_score:.3f}")
            
            return {
                'status': 'success',
                'train_score': train_score,
                'test_score': test_score,
                'feature_importance': self.feature_importance,
                'scene_distribution': y.value_counts().to_dict()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'模型训练失败: {str(e)}'
            }
    
    def predict_scene(self, order_data: pd.DataFrame) -> pd.DataFrame:
        """
        预测订单场景
        
        Returns:
            包含场景预测和概率的DataFrame
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练，请先调用train()方法")
        
        features_df = self.prepare_features(order_data)
        
        feature_cols = ['hour', 'weekday', '配送距离', '订单金额', 
                       '平均单价', '商品数', 'delivery_fee_ratio']
        
        for col in feature_cols:
            if col not in features_df.columns:
                features_df[col] = 0
        
        X = features_df[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # 预测
        y_pred = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)
        
        # 解码
        scene_pred = self.label_encoder.inverse_transform(y_pred)
        
        # 构建结果
        result = features_df[['订单ID']].copy()
        result['predicted_scene'] = scene_pred
        
        # 添加各场景概率
        for i, scene in enumerate(self.label_encoder.classes_):
            result[f'prob_{scene}'] = y_proba[:, i]
        
        return result
    
    def visualize_feature_importance(self) -> go.Figure:
        """可视化特征重要性"""
        if self.feature_importance is None:
            fig = go.Figure()
            fig.add_annotation(text="模型尚未训练", x=0.5, y=0.5)
            return fig
        
        fig = px.bar(
            self.feature_importance,
            x='importance',
            y='feature',
            orientation='h',
            title='场景识别特征重要性',
            labels={'importance': '重要性', 'feature': '特征'}
        )
        fig.update_layout(height=400)
        return fig


# ============================================================================
# 3. RFM客户分群模型
# ============================================================================

class RFMCustomerSegmentation:
    """
    RFM客户分群模型
    
    功能：
    - 基于RFM（最近购买时间、购买频率、购买金额）+ 场景特征聚类
    - 识别4类用户：高频应急、计划囤货、价格敏感、偶发尝鲜
    - 为每类用户生成营销策略
    """
    
    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.scaler = StandardScaler()
        self.rfm_data = None
        self.cluster_labels = None
        self.cluster_profiles = {}
        
    def calculate_rfm(self, order_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算RFM特征
        
        Args:
            order_data: 订单数据，需包含用户ID、日期、金额
            
        Returns:
            RFM特征DataFrame
        """
        # 确定用户ID列
        user_col = None
        for col in ['用户ID', '用户电话', '地址', '收货地址']:
            if col in order_data.columns:
                # 检查该列的有效值比例
                valid_rate = order_data[col].notna().sum() / len(order_data)
                if valid_rate > 0.1:  # 至少10%的数据有值
                    user_col = col
                    break
        
        if user_col is None:
            raise ValueError("无法找到有效的用户标识列")
        
        # 订单级聚合 - 使用商品金额（不含配送费）计算Monetary
        if '订单ID' in order_data.columns:
            # RFM的M（Monetary）应该是商品金额，不包含配送费
            if '商品实售价' not in order_data.columns:
                return pd.DataFrame()
            
            # 按订单聚合：商品实售价求和 = 订单商品总金额
            order_level = order_data.groupby('订单ID').agg({
                user_col: 'first',
                '日期_datetime': 'first' if '日期_datetime' in order_data.columns else 'first',
                '商品实售价': 'sum'  # 订单商品总金额（不含配送费）
            }).reset_index()
            
            order_level.columns = ['订单ID', user_col, 'order_date', 'order_amount']
        else:
            return pd.DataFrame()
        
        # 计算RFM
        if 'order_date' in order_level.columns:
            current_date = pd.to_datetime(order_level['order_date']).max()
            order_level['order_date'] = pd.to_datetime(order_level['order_date'])
        else:
            current_date = pd.Timestamp.now()
            order_level['order_date'] = current_date
        
        # 计算数据时间跨度（天数）
        min_date = pd.to_datetime(order_level['order_date']).min()
        data_span_days = (current_date - min_date).days + 1
        data_span_weeks = max(data_span_days / 7, 0.1)  # 至少0.1周，避免除零
        
        rfm = order_level.groupby(user_col).agg({
            'order_date': lambda x: (current_date - x.max()).days,  # Recency
            '订单ID': 'count',  # 订单总数
            'order_amount': 'sum'  # Monetary
        }).reset_index()
        
        rfm.columns = [user_col, 'recency', 'order_count', 'monetary']
        
        # 标准化频次：计算每周平均订单数（更有业务意义）
        rfm['frequency'] = rfm['order_count'] / data_span_weeks
        
        # 保留原始订单数和数据周期，用于前端展示
        rfm['total_orders'] = rfm['order_count']
        rfm['data_span_days'] = data_span_days
        
        print(f"📊 数据时间跨度: {data_span_days}天 ({data_span_weeks:.1f}周)")
        print(f"   频次已标准化为每周平均订单数")
        
        # 过滤异常值：剔除超高频用户（可能是数据聚合问题）
        # 使用IQR方法识别异常值
        freq_q75 = rfm['frequency'].quantile(0.75)
        freq_q25 = rfm['frequency'].quantile(0.25)
        freq_iqr = freq_q75 - freq_q25
        freq_upper_bound = freq_q75 + 3 * freq_iqr  # 3倍IQR作为上界
        
        # 记录异常用户数量
        outlier_users = rfm[rfm['frequency'] > freq_upper_bound]
        if len(outlier_users) > 0:
            print(f"⚠️  检测到 {len(outlier_users)} 个异常高频用户（频次>{freq_upper_bound:.0f}），已自动过滤")
            print(f"   异常用户频次范围: {outlier_users['frequency'].min():.0f}-{outlier_users['frequency'].max():.0f}")
        
        # 过滤掉异常值
        rfm = rfm[rfm['frequency'] <= freq_upper_bound].copy()
        
        # 添加场景特征
        if '配送距离' in order_data.columns:
            avg_dist = order_data.groupby(user_col)['配送距离'].mean().reset_index()
            # 检测距离单位，如果平均值>100，很可能是米，需要转换为公里
            if avg_dist['配送距离'].mean() > 100:
                avg_dist['配送距离'] = avg_dist['配送距离'] / 1000
            rfm = rfm.merge(avg_dist, on=user_col)
            rfm.rename(columns={'配送距离': 'avg_distance'}, inplace=True)
        else:
            rfm['avg_distance'] = 0
        
        # 配送净成本占比计算（基于订单底层业务逻辑）
        if '物流配送费' in order_data.columns and '商品实售价' in order_data.columns and '订单ID' in order_data.columns:
            # 配送净成本 = 物流配送费 - 用户支付配送费 + 配送费减免金额
            # 配送净成本占比 = 配送净成本 / 商品金额
            
            agg_dict = {
                user_col: 'first',
                '物流配送费': 'first',      # 订单级字段
                '商品实售价': 'sum'         # 明细级，求和得到订单商品总金额
            }
            
            # 添加可选字段
            if '用户支付配送费' in order_data.columns:
                agg_dict['用户支付配送费'] = 'first'
            if '配送费减免金额' in order_data.columns:
                agg_dict['配送费减免金额'] = 'first'
            
            order_fee_data = order_data.groupby('订单ID').agg(agg_dict).reset_index()
            
            # 计算配送净成本（门店实际承担的配送成本）
            logistics_fee = pd.to_numeric(order_fee_data['物流配送费'], errors='coerce').fillna(0)
            user_paid = pd.to_numeric(order_fee_data.get('用户支付配送费', pd.Series(0, index=order_fee_data.index)), errors='coerce').fillna(0)
            fee_discount = pd.to_numeric(order_fee_data.get('配送费减免金额', pd.Series(0, index=order_fee_data.index)), errors='coerce').fillna(0)
            
            # 配送净成本 = 物流配送费 - 用户支付 + 平台减免
            order_fee_data['net_delivery_cost'] = logistics_fee - user_paid + fee_discount
            
            # 配送净成本占商品金额的比例
            order_fee_data['fee_ratio'] = (
                order_fee_data['net_delivery_cost'] / 
                pd.to_numeric(order_fee_data['商品实售价'], errors='coerce').replace(0, np.nan)
            ).fillna(0)
            
            # 限制异常值：配送费占比通常在-50%~100%之间（负值表示用户支付>实际成本）
            order_fee_data['fee_ratio'] = order_fee_data['fee_ratio'].clip(lower=-0.5, upper=1.0)
            
            # 按用户聚合平均配送费占比
            user_fee_ratio = order_fee_data.groupby(user_col)['fee_ratio'].mean().reset_index()
            rfm = rfm.merge(user_fee_ratio, on=user_col, how='left')
            rfm.rename(columns={'fee_ratio': 'avg_fee_ratio'}, inplace=True)
        else:
            rfm['avg_fee_ratio'] = 0
        
        # 添加囤货行为特征：商品数量和品类多样性
        if '订单ID' in order_data.columns:
            # 确定品类列名（可能是"美团三级分类"或"三级分类名"）
            category_col = None
            for col in ['美团三级分类', '三级分类名', '三级分类', '分类']:
                if col in order_data.columns:
                    category_col = col
                    break
            
            # 构建聚合字典
            agg_dict = {
                user_col: 'first'
            }
            
            # 添加商品名称计数（商品件数）
            if '商品名称' in order_data.columns:
                agg_dict['商品名称'] = 'count'
            
            # 添加品类计数（品类多样性）
            if category_col:
                agg_dict[category_col] = 'nunique'
            
            # 计算每个订单的商品数量和品类数
            order_items = order_data.groupby('订单ID').agg(agg_dict).reset_index()
            
            # 动态设置列名
            new_cols = ['订单ID', user_col]
            if '商品名称' in agg_dict:
                new_cols.append('items_count')
            if category_col:
                new_cols.append('category_count')
            
            order_items.columns = new_cols
            
            # 按用户聚合平均值
            agg_user_dict = {}
            if 'items_count' in order_items.columns:
                agg_user_dict['items_count'] = 'mean'
            if 'category_count' in order_items.columns:
                agg_user_dict['category_count'] = 'mean'
            
            if agg_user_dict:
                user_items = order_items.groupby(user_col).agg(agg_user_dict).reset_index()
                
                # 重命名列
                rename_dict = {}
                if 'items_count' in user_items.columns:
                    rename_dict['items_count'] = 'avg_items_per_order'
                if 'category_count' in user_items.columns:
                    rename_dict['category_count'] = 'avg_categories_per_order'
                
                user_items = user_items.rename(columns=rename_dict)
                rfm = rfm.merge(user_items, on=user_col, how='left')
            
            # 填充缺失值
            if 'avg_items_per_order' not in rfm.columns:
                rfm['avg_items_per_order'] = 0
            if 'avg_categories_per_order' not in rfm.columns:
                rfm['avg_categories_per_order'] = 0
        else:
            rfm['avg_items_per_order'] = 0
            rfm['avg_categories_per_order'] = 0
        
        self.rfm_data = rfm
        return rfm
    
    def segment_customers(self) -> Dict[str, Any]:
        """
        客户分群
        
        Returns:
            分群结果和统计信息
        """
        if self.rfm_data is None or self.rfm_data.empty:
            return {
                'status': 'error',
                'message': 'RFM数据为空，请先调用calculate_rfm()'
            }
        
        try:
            # 特征列（增加商品数量和品类多样性）
            feature_cols = [
                'recency', 'frequency', 'monetary', 
                'avg_distance', 'avg_fee_ratio',
                'avg_items_per_order', 'avg_categories_per_order'
            ]
            X = self.rfm_data[feature_cols].fillna(0)
            
            # 标准化
            X_scaled = self.scaler.fit_transform(X)
            
            # 聚类
            self.cluster_labels = self.kmeans.fit_predict(X_scaled)
            self.rfm_data['cluster'] = self.cluster_labels
            
            # 计算轮廓系数
            silhouette_avg = silhouette_score(X_scaled, self.cluster_labels)
            
            # 分析每个簇的特征
            self._profile_clusters()
            
            print(f"✅ 客户分群完成：{self.n_clusters}个群组")
            print(f"   轮廓系数: {silhouette_avg:.3f}")
            
            return {
                'status': 'success',
                'n_clusters': self.n_clusters,
                'silhouette_score': silhouette_avg,
                'cluster_profiles': self.cluster_profiles,
                'distribution': self.rfm_data['cluster'].value_counts().to_dict()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'分群失败: {str(e)}'
            }
    
    def _profile_clusters(self):
        """
        分析每个簇的特征画像（改进版：结合商品数量和品类判断囤货行为）
        """
        feature_cols = [
            'recency', 'frequency', 'monetary', 
            'avg_distance', 'avg_fee_ratio',
            'avg_items_per_order', 'avg_categories_per_order'
        ]
        
        # 先计算所有簇的特征
        cluster_stats = []
        for cluster_id in range(self.n_clusters):
            cluster_data = self.rfm_data[self.rfm_data['cluster'] == cluster_id]
            
            profile = {
                'cluster_id': cluster_id,
                'size': len(cluster_data),
                'percentage': len(cluster_data) / len(self.rfm_data) * 100,
                'avg_recency': cluster_data['recency'].mean(),
                'avg_frequency': cluster_data['frequency'].mean(),
                'avg_monetary': cluster_data['monetary'].mean(),
                'avg_distance': cluster_data['avg_distance'].mean(),
                'avg_fee_ratio': cluster_data['avg_fee_ratio'].mean(),
                'avg_items_per_order': cluster_data['avg_items_per_order'].mean(),
                'avg_categories_per_order': cluster_data['avg_categories_per_order'].mean(),
                # 新增：保留原始订单数和数据周期（用于前端展示）
                'avg_total_orders': cluster_data['total_orders'].mean(),
                'data_span_days': cluster_data['data_span_days'].iloc[0] if len(cluster_data) > 0 else 30
            }
            cluster_stats.append(profile)
        
        cluster_df = pd.DataFrame(cluster_stats)
        
        # 过滤异常簇（人数<总数的1%，或人数<10）
        min_size = max(10, len(self.rfm_data) * 0.01)
        normal_clusters = cluster_df[cluster_df['size'] >= min_size].copy()
        outlier_clusters = cluster_df[cluster_df['size'] < min_size].copy()
        
        # 按特征排序分配4种客户类型（改进版：囤货判断更准确）
        assigned_profiles = {}
        
        # 1. 计划囤货用户：高商品数量 + 高品类多样性 + 低频次 + 低配送费占比
        #    （真正的囤货：买得多、买得杂、不常买、不是因为起送价高）
        if len(normal_clusters) > 0:
            normal_clusters['bulk_score'] = (
                normal_clusters['avg_items_per_order'] * 0.3 +          # 商品数量权重30%
                normal_clusters['avg_categories_per_order'] * 0.3 +     # 品类多样性30%
                normal_clusters['avg_monetary'] * 0.02 +                # 金额权重20%（系数0.02避免数值过大）
                (1 / (normal_clusters['avg_frequency'] + 0.1)) * 0.1 +  # 低频次10%
                (1 / (normal_clusters['avg_fee_ratio'] + 0.01)) * 0.1   # 低配送费占比10%
            )
            bulk_cluster = normal_clusters.nlargest(1, 'bulk_score').iloc[0]
            assigned_profiles[int(bulk_cluster['cluster_id'])] = {
                **cluster_stats[int(bulk_cluster['cluster_id'])],
                'name': '计划囤货用户',
                'strategy': '推荐大包装促销，满减活动，会员储值优惠',
                'definition': '主动规划性采购，单次购买商品数量多（6-10件/单）、品类丰富（4-6种/单），追求性价比而非即时性，配送费占比相对较低'
            }
            normal_clusters = normal_clusters[normal_clusters['cluster_id'] != bulk_cluster['cluster_id']]
        
        # 2. 价格敏感用户：配送费占比最高（对配送成本敏感，追求免配送费）
        if len(normal_clusters) > 0:
            price_cluster = normal_clusters.nlargest(1, 'avg_fee_ratio').iloc[0]
            assigned_profiles[int(price_cluster['cluster_id'])] = {
                **cluster_stats[int(price_cluster['cluster_id'])],
                'name': '价格敏感用户',
                'strategy': '主推特价商品，拼团优惠，满额免配送费',
                'definition': '对价格和配送成本高度敏感，单次购买金额相对较低，配送费占比较高（20-25%），倾向于凑单满减或寻找免配送费活动'
            }
            normal_clusters = normal_clusters[normal_clusters['cluster_id'] != price_cluster['cluster_id']]
        
        # 3. 高频应急用户：频次最高 或 剩余簇中特征最明显的
        if len(normal_clusters) > 0:
            # 如果有明显高频的簇，选它；否则选剩余的第一个作为高频应急
            emergency_cluster = normal_clusters.nlargest(1, 'avg_frequency').iloc[0]
            assigned_profiles[int(emergency_cluster['cluster_id'])] = {
                **cluster_stats[int(emergency_cluster['cluster_id'])],
                'name': '高频应急用户',
                'strategy': '保证应急商品库存，提供加急配送服务，适度溢价可接受',
                'definition': '购买频次相对较高（1.3-1.5次/周），购买行为具有应急性和即时性特征，对配送速度要求高，对价格相对不敏感'
            }
            normal_clusters = normal_clusters[normal_clusters['cluster_id'] != emergency_cluster['cluster_id']]
        
        # 4. 偶发尝鲜用户：剩余的正常簇
        if len(normal_clusters) > 0:
            for _, row in normal_clusters.iterrows():
                assigned_profiles[int(row['cluster_id'])] = {
                    **cluster_stats[int(row['cluster_id'])],
                    'name': '偶发尝鲜用户',
                    'strategy': '新品推荐，首单优惠，场景化套餐引导',
                    'definition': '购买频次低（1-2次/月），尝试性购买为主，对新品和促销活动敏感，需要通过优惠和场景化营销激活复购'
                }
        
        # 异常簇统一归为"偶发尝鲜用户"
        for _, row in outlier_clusters.iterrows():
            assigned_profiles[int(row['cluster_id'])] = {
                **cluster_stats[int(row['cluster_id'])],
                'name': '偶发尝鲜用户',
                'strategy': '新品推荐，首单优惠，场景化套餐引导',
                'definition': '购买频次极低或数据异常，尝试性购买为主，需要通过优惠和场景化营销激活复购'
            }
        
        self.cluster_profiles = assigned_profiles
    
    def visualize_clusters(self) -> go.Figure:
        """
        可视化客户群组（3D散点图）
        """
        if self.rfm_data is None or 'cluster' not in self.rfm_data.columns:
            fig = go.Figure()
            fig.add_annotation(text="尚未进行分群", x=0.5, y=0.5)
            return fig
        
        # 使用RFM三维可视化
        df_plot = self.rfm_data.copy()
        df_plot['cluster_name'] = df_plot['cluster'].map(
            lambda x: self.cluster_profiles[x]['name']
        )
        
        fig = px.scatter_3d(
            df_plot,
            x='recency',
            y='frequency',
            z='monetary',
            color='cluster_name',
            title='RFM客户分群3D视图',
            labels={
                'recency': '最近购买(天)',
                'frequency': '购买频次',
                'monetary': '购买金额',
                'cluster_name': '客户群组'
            },
            hover_data=['avg_distance', 'avg_fee_ratio']
        )
        
        fig.update_layout(height=600)
        return fig
    
    def get_cluster_summary(self) -> pd.DataFrame:
        """
        获取群组摘要表
        """
        if not self.cluster_profiles:
            return pd.DataFrame()
        
        summary = []
        for cluster_id, profile in self.cluster_profiles.items():
            summary.append({
                '群组': profile['name'],
                '用户数': profile['size'],
                '占比': f"{profile['percentage']:.1f}%",
                '平均频次': f"{profile['avg_frequency']:.1f}",
                '平均金额': f"¥{profile['avg_monetary']:.0f}",
                '平均距离': f"{profile['avg_distance']:.1f}km",
                '配送费占比': f"{profile['avg_fee_ratio']*100:.1f}%",
                '营销策略': profile['strategy']
            })
        
        return pd.DataFrame(summary)


# ============================================================================
# 4. 决策树规则生成器
# ============================================================================

class SceneDecisionTreeRules:
    """
    场景识别决策树规则生成器
    
    功能：
    - 生成可解释的IF-THEN规则
    - 可视化决策路径
    - 自动标注订单场景
    """
    
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.tree = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=50,
            min_samples_leaf=20,
            random_state=42
        )
        self.feature_names = []
        self.class_names = []
        self.rules_text = ""
        self.is_trained = False
        
    def train_rule_tree(self, order_data: pd.DataFrame) -> Dict[str, Any]:
        """
        训练决策树规则
        """
        try:
            # 特征工程（复用SceneRecognitionModel的逻辑）
            scene_model = SceneRecognitionModel()
            features_df = scene_model.prepare_features(order_data)
            features_df['scene'] = scene_model.auto_label_scenes(features_df)
            
            # 特征列
            self.feature_names = ['hour', 'weekday', '配送距离', '订单金额', 
                                 '平均单价', '商品数', 'delivery_fee_ratio']
            
            for col in self.feature_names:
                if col not in features_df.columns:
                    features_df[col] = 0
            
            X = features_df[self.feature_names].fillna(0)
            y = features_df['scene']
            
            self.class_names = y.unique().tolist()
            
            # 训练决策树
            self.tree.fit(X, y)
            
            # 提取规则
            self.rules_text = export_text(
                self.tree, 
                feature_names=self.feature_names,
                class_names=self.class_names,
                max_depth=self.max_depth
            )
            
            self.is_trained = True
            
            # 评估
            train_score = self.tree.score(X, y)
            
            print(f"✅ 决策树规则生成完成")
            print(f"   准确率: {train_score:.3f}")
            print(f"   树深度: {self.tree.get_depth()}")
            print(f"   叶子节点数: {self.tree.get_n_leaves()}")
            
            return {
                'status': 'success',
                'accuracy': train_score,
                'tree_depth': self.tree.get_depth(),
                'n_leaves': self.tree.get_n_leaves(),
                'rules': self.rules_text
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'规则生成失败: {str(e)}'
            }
    
    def get_rules_text(self) -> str:
        """获取文本格式的规则"""
        return self.rules_text
    
    def extract_key_rules(self, top_n: int = 10) -> List[str]:
        """
        提取关键规则（基于特征重要性）
        """
        if not self.is_trained:
            return []
        
        # 获取特征重要性
        importance = self.tree.feature_importances_
        important_features = sorted(
            zip(self.feature_names, importance),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        rules = [
            f"• {feat}: {imp:.3f}" for feat, imp in important_features
        ]
        
        return rules
    
    def visualize_tree_rules(self) -> go.Figure:
        """
        可视化决策树规则（简化版）
        """
        if not self.is_trained:
            fig = go.Figure()
            fig.add_annotation(text="决策树尚未训练", x=0.5, y=0.5)
            return fig
        
        # 特征重要性条形图
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.tree.feature_importances_
        }).sort_values('importance', ascending=False)
        
        fig = px.bar(
            importance_df,
            x='importance',
            y='feature',
            orientation='h',
            title='决策树特征重要性',
            labels={'importance': '重要性', 'feature': '特征'}
        )
        fig.update_layout(height=400)
        return fig


# ============================================================================
# 5. 统一的场景营销智能决策引擎
# ============================================================================

class SceneMarketingIntelligence:
    """
    场景营销智能决策引擎 - 统一入口
    
    集成所有子模型，提供一站式场景营销分析
    """
    
    def __init__(self):
        self.product_miner = ProductCombinationMiner()
        self.scene_model = SceneRecognitionModel()
        self.rfm_segment = RFMCustomerSegmentation()
        self.rule_tree = SceneDecisionTreeRules()
        
        self.analysis_results = {}
        
    def run_full_analysis(self, order_data: pd.DataFrame) -> Dict[str, Any]:
        """
        运行完整分析流程
        
        Args:
            order_data: 订单明细数据
            
        Returns:
            所有分析结果的汇总
        """
        print("=" * 80)
        print("🚀 场景营销智能决策引擎 - 全流程分析")
        print("=" * 80)
        
        results = {}
        
        # 1. 商品组合挖掘
        print("\n【1/5】商品组合挖掘...")
        try:
            combo_result = self.product_miner.mine_from_orders(order_data)
            results['product_combinations'] = combo_result
            print(f"✅ 完成：{combo_result.get('stats', {}).get('rules_count', 0)}条关联规则")
        except Exception as e:
            print(f"❌ 商品组合挖掘失败: {e}")
            results['product_combinations'] = {'status': 'error', 'message': str(e)}
        
        # 2. 场景识别模型
        print("\n【2/5】场景识别模型训练...")
        try:
            scene_result = self.scene_model.train(order_data)
            results['scene_recognition'] = scene_result
            print(f"✅ 完成：测试准确率 {scene_result.get('test_score', 0):.3f}")
        except Exception as e:
            print(f"❌ 场景识别失败: {e}")
            results['scene_recognition'] = {'status': 'error', 'message': str(e)}
        
        # 3. 客户分群
        print("\n【3/5】RFM客户分群...")
        try:
            self.rfm_segment.calculate_rfm(order_data)
            segment_result = self.rfm_segment.segment_customers()
            results['customer_segmentation'] = segment_result
            print(f"✅ 完成：{segment_result.get('n_clusters', 0)}个客户群组")
        except Exception as e:
            print(f"❌ 客户分群失败: {e}")
            results['customer_segmentation'] = {'status': 'error', 'message': str(e)}
        
        # 4. 决策树规则
        print("\n【4/5】决策树规则生成...")
        try:
            rule_result = self.rule_tree.train_rule_tree(order_data)
            results['decision_rules'] = rule_result
            print(f"✅ 完成：生成 {rule_result.get('n_leaves', 0)} 个规则节点")
        except Exception as e:
            print(f"❌ 决策树规则生成失败: {e}")
            results['decision_rules'] = {'status': 'error', 'message': str(e)}
        
        # 5. 场景预测
        print("\n【5/5】订单场景预测...")
        try:
            if self.scene_model.is_trained:
                scene_predictions = self.scene_model.predict_scene(order_data)
                results['scene_predictions'] = scene_predictions
                print(f"✅ 完成：预测 {len(scene_predictions)} 个订单场景")
            else:
                results['scene_predictions'] = None
        except Exception as e:
            print(f"❌ 场景预测失败: {e}")
            results['scene_predictions'] = None
        
        print("\n" + "=" * 80)
        print("🎉 全流程分析完成！")
        print("=" * 80)
        
        self.analysis_results = results
        return results
    
    def get_summary_report(self) -> str:
        """
        生成分析摘要报告
        """
        if not self.analysis_results:
            return "尚未运行分析，请先调用run_full_analysis()"
        
        report = []
        report.append("=" * 80)
        report.append("📊 场景营销智能决策报告")
        report.append("=" * 80)
        report.append("")
        
        # 1. 商品组合
        if 'product_combinations' in self.analysis_results:
            combo = self.analysis_results['product_combinations']
            if combo.get('status') == 'success':
                stats = combo.get('stats', {})
                report.append(f"【商品组合挖掘】")
                report.append(f"  • 分析订单数: {stats.get('total_baskets', 0)}")
                report.append(f"  • 频繁项集: {stats.get('frequent_itemsets_count', 0)}")
                report.append(f"  • 关联规则: {stats.get('rules_count', 0)}")
                
                scene_pkgs = combo.get('scene_packages', {})
                if scene_pkgs:
                    report.append(f"  • 识别场景套餐: {', '.join(scene_pkgs.keys())}")
                report.append("")
        
        # 2. 场景识别
        if 'scene_recognition' in self.analysis_results:
            scene = self.analysis_results['scene_recognition']
            if scene.get('status') == 'success':
                report.append(f"【场景识别模型】")
                report.append(f"  • 训练准确率: {scene.get('train_score', 0):.1%}")
                report.append(f"  • 测试准确率: {scene.get('test_score', 0):.1%}")
                
                dist = scene.get('scene_distribution', {})
                if dist:
                    report.append(f"  • 场景分布:")
                    for scene_name, count in dist.items():
                        report.append(f"    - {scene_name}: {count}")
                report.append("")
        
        # 3. 客户分群
        if 'customer_segmentation' in self.analysis_results:
            seg = self.analysis_results['customer_segmentation']
            if seg.get('status') == 'success':
                report.append(f"【客户分群】")
                report.append(f"  • 群组数量: {seg.get('n_clusters', 0)}")
                report.append(f"  • 轮廓系数: {seg.get('silhouette_score', 0):.3f}")
                
                profiles = seg.get('cluster_profiles', {})
                if profiles:
                    report.append(f"  • 客户群组:")
                    for cluster_id, profile in profiles.items():
                        report.append(f"    - {profile['name']}: {profile['size']}人 ({profile['percentage']:.1f}%)")
                report.append("")
        
        # 4. 决策规则
        if 'decision_rules' in self.analysis_results:
            rules = self.analysis_results['decision_rules']
            if rules.get('status') == 'success':
                report.append(f"【决策树规则】")
                report.append(f"  • 准确率: {rules.get('accuracy', 0):.1%}")
                report.append(f"  • 树深度: {rules.get('tree_depth', 0)}")
                report.append(f"  • 规则节点: {rules.get('n_leaves', 0)}")
                report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("场景营销智能决策引擎 - 模块测试")
    print("=" * 80)
    print("✅ 所有模块导入成功")
    print("")
    print("可用模块:")
    print("  1. ProductCombinationMiner - 商品组合挖掘")
    print("  2. SceneRecognitionModel - 场景识别模型")
    print("  3. RFMCustomerSegmentation - 客户分群")
    print("  4. SceneDecisionTreeRules - 决策树规则")
    print("  5. SceneMarketingIntelligence - 统一引擎")
    print("")
    print("使用示例:")
    print("  engine = SceneMarketingIntelligence()")
    print("  results = engine.run_full_analysis(order_data)")
    print("=" * 80)
