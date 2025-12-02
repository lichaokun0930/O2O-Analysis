# -*- coding: utf-8 -*-
"""
通义千问 AI 服务模块
用于营销分析智能解读 - 按象限维度深度分析

模型: qwen3-max
API: 阿里云百炼 (OpenAI兼容接口)
"""

from openai import OpenAI
from typing import Dict, List, Optional, Any
import json
import time

# API配置
QWEN_API_KEY = "sk-1a559ff60a514d27a17be7f1bd20bfdd"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen3-max"

# 初始化客户端
_client = None

def get_client() -> OpenAI:
    """获取OpenAI客户端（懒加载）"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
        )
    return _client


# ==================== 八象限业务知识库 ====================
QUADRANT_KNOWLEDGE = {
    'Q1': {
        'name': '💰金牛过度',
        'definition': '高营销+高毛利+高动销：商品本身很优秀，但营销投入过高，在"花钱买增长"',
        'risk': '营销费用侵蚀利润，ROI可能不划算',
        'strategy': '逐步降低营销投入，测试自然销量，找到最优营销比例',
        'kpi_focus': ['营销ROI', '营销占比', '自然流量占比']
    },
    'Q2': {
        'name': '⚠️高成本蓄客',
        'definition': '高营销+高毛利+低动销：花了很多营销费但卖得不好，可能是新品蓄客期或策略失误',
        'risk': '持续烧钱但效果不佳，需要判断是蓄客期还是策略问题',
        'strategy': '分析是否新品（可容忍）还是老品（需调整），优化营销渠道或考虑退出',
        'kpi_focus': ['上架天数', '曝光点击率', '转化率']
    },
    'Q3': {
        'name': '🔴引流亏损',
        'definition': '高营销+低毛利+高动销：典型的引流款，卖得好但不赚钱，靠营销拉动',
        'risk': '单品亏损，如果没有带动其他商品销售就是纯亏',
        'strategy': '评估引流效果，看关联购买率；适度提价或降低营销投入',
        'kpi_focus': ['关联购买率', '客单价贡献', '引流ROI']
    },
    'Q4': {
        'name': '❌双输商品',
        'definition': '高营销+低毛利+低动销：花钱推广但既不赚钱也卖不动，最危险的象限',
        'risk': '纯粹浪费资源，需要立即止损',
        'strategy': '立即停止营销投入，评估是否下架或清仓处理',
        'kpi_focus': ['止损金额', '库存周转天数']
    },
    'Q5': {
        'name': '⭐黄金商品',
        'definition': '低营销+高毛利+高动销：最理想状态，不用花钱推广就能赚钱且卖得好',
        'risk': '需要保护，避免竞争对手抢占',
        'strategy': '保持现有策略，可适度增加营销扩大优势，作为利润支柱重点维护',
        'kpi_focus': ['市场份额', '复购率', '价格弹性']
    },
    'Q6': {
        'name': '💎潜力商品',
        'definition': '低营销+高毛利+低动销：利润率好但知名度低，潜在的黄金商品',
        'risk': '可能被埋没，错过增长机会',
        'strategy': '增加营销曝光，测试市场反应，有望培养成黄金商品',
        'kpi_focus': ['曝光量', '点击率', '加购率']
    },
    'Q7': {
        'name': '🎯引流爆款',
        'definition': '低营销+低毛利+高动销：不需要推广就卖得好，天然流量款',
        'risk': '毛利低，需要搭配高毛利商品才能盈利',
        'strategy': '维持现状，重点做关联销售，带动高毛利商品',
        'kpi_focus': ['关联购买率', '购物篮商品数', '连带率']
    },
    'Q8': {
        'name': '🗑️淘汰区',
        'definition': '低营销+低毛利+低动销：既不赚钱也卖不动，占用货架资源',
        'risk': '库存积压，资金占用',
        'strategy': '清仓促销或直接下架，释放资源给更优质商品',
        'kpi_focus': ['库存金额', '库龄', '货架占用']
    }
}


class QwenAIService:
    """通义千问AI服务类 - 用于Dash回调的同步调用"""
    
    def __init__(self):
        self.client = get_client()
        self._cache = {}  # 简单缓存
    
    def get_overall_insight_sync(self, analysis_summary: Dict[str, Any]) -> str:
        """
        同步生成整体分析洞察
        
        Args:
            analysis_summary: 分析汇总数据
        
        Returns:
            AI生成的洞察报告
        """
        try:
            # 构建提示词
            prompt = f"""你是一个零售数据分析专家。请根据以下商品分析数据，生成一份简洁的洞察报告（200字以内）。

## 数据概览
- 商品总数: {analysis_summary.get('total_products', 0)}个
- 筛选条件: 渠道={analysis_summary.get('channel', '全部')}, 品类={analysis_summary.get('category', '全部')}
- 平均综合得分: {analysis_summary.get('avg_score', 'N/A')}
- 优秀商品(≥80分): {analysis_summary.get('excellent_count', 0)}个
- 需优化商品(<40分): {analysis_summary.get('poor_count', 0)}个

## 利润情况
- 总利润: ¥{analysis_summary.get('total_profit', 0):,.2f}
- 盈利商品: {analysis_summary.get('profit_positive', 0)}个
- 亏损商品: {analysis_summary.get('profit_negative', 0)}个

## 科学方法象限分布
{json.dumps(analysis_summary.get('scientific_quadrant_dist', {}), ensure_ascii=False, indent=2)}
- 低置信度商品: {analysis_summary.get('low_confidence_count', 0)}个

请从以下角度给出洞察：
1. 整体商品结构健康度评估
2. 最需要优先关注的问题
3. 2-3条具体可执行的改进建议

输出要求：使用简洁的中文，可以使用少量emoji增强可读性。"""

            completion = self.client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {"role": "system", "content": "你是零售数据分析专家，擅长从数据中发现商业洞察。回答要简洁、有洞察力、可执行。使用中文回答。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            
            return completion.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"[AI] 整体洞察生成失败: {e}")
            return f"AI分析暂时不可用: {str(e)}"
    
    def generate_batch_advice_sync(self, products: List[Dict[str, Any]], max_products: int = 8) -> List[str]:
        """
        同步批量生成商品优化建议
        
        Args:
            products: 商品列表
            max_products: 最大处理商品数
        
        Returns:
            建议列表（与商品列表顺序对应）
        """
        try:
            products = products[:max_products]
            
            if not products:
                return []
            
            # 构建商品列表文本
            product_lines = []
            for i, p in enumerate(products):
                name = p.get('商品名称', '未知')
                quadrant = p.get('象限名称', '')
                score = p.get('综合得分', 'N/A')
                margin = p.get('毛利率', p.get('利润额', 0))
                sales = p.get('月售', 0)
                
                if isinstance(margin, float) and margin < 1:
                    margin_str = f"毛利率{margin:.0%}"
                else:
                    margin_str = f"利润¥{margin:.2f}" if isinstance(margin, (int, float)) else f"利润{margin}"
                
                product_lines.append(
                    f"{i+1}. {name} | 得分:{score} | {quadrant} | {margin_str} | 月售{sales:.0f}"
                )
            
            product_text = "\n".join(product_lines)
            
            prompt = f"""你是零售商品运营专家。请为以下{len(products)}个低分/问题商品分别给出简短优化建议。

每个建议要具体可执行，20字以内。

商品列表：
{product_text}

请按以下格式输出，每行一个建议，与商品序号对应：
1. 建议内容
2. 建议内容
...

只输出建议，不要其他内容。"""

            completion = self.client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {"role": "system", "content": "你是零售运营专家，擅长商品优化。回答简洁、具体、可执行。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.6,
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # 解析建议列表
            lines = response_text.split('\n')
            advice_list = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # 去除序号
                    if '. ' in line:
                        line = line.split('. ', 1)[1]
                    elif '、' in line:
                        line = line.split('、', 1)[1]
                    advice_list.append(line.strip())
            
            # 确保返回数量与输入一致
            while len(advice_list) < len(products):
                advice_list.append("请分析具体情况制定优化方案")
            
            return advice_list[:len(products)]
        
        except Exception as e:
            print(f"[AI] 批量建议生成失败: {e}")
            return ["AI建议生成失败，请稍后重试"] * len(products)

    def analyze_quadrant_deep(self, quadrant_code: str, products: List[Dict[str, Any]], 
                               store_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        深度分析单个象限的商品情况
        
        Args:
            quadrant_code: 象限编号 (Q1-Q8)
            products: 该象限的商品列表
            store_context: 门店上下文信息
        
        Returns:
            {
                'quadrant_summary': 象限整体分析,
                'key_findings': 关键发现列表,
                'action_items': 具体行动建议,
                'priority_products': 优先处理商品
            }
        """
        if not products:
            return {
                'quadrant_summary': '该象限暂无商品',
                'key_findings': [],
                'action_items': [],
                'priority_products': []
            }
        
        try:
            # 获取象限知识
            quadrant_info = QUADRANT_KNOWLEDGE.get(quadrant_code, {})
            quadrant_name = quadrant_info.get('name', '未知象限')
            definition = quadrant_info.get('definition', '')
            risk = quadrant_info.get('risk', '')
            strategy = quadrant_info.get('strategy', '')
            
            # 计算象限统计
            total_products = len(products)
            total_profit = sum(p.get('利润额', 0) for p in products)
            total_sales = sum(p.get('月售', 0) for p in products)
            avg_margin = sum(p.get('毛利率', 0) for p in products) / total_products if total_products > 0 else 0
            avg_score = sum(p.get('综合得分', 0) for p in products) / total_products if total_products > 0 else 0
            
            # 构建TOP商品明细（最多5个）
            # 按利润额绝对值排序（展示影响最大的）
            sorted_products = sorted(products, key=lambda x: abs(x.get('利润额', 0)), reverse=True)[:5]
            
            product_details = []
            for p in sorted_products:
                detail = (
                    f"• {p.get('商品名称', '未知')}: "
                    f"利润¥{p.get('利润额', 0):.2f}, "
                    f"毛利率{p.get('毛利率', 0):.1%}, "
                    f"月售{p.get('月售', 0):.0f}件, "
                    f"营销占比{p.get('营销占比', 0):.1%}, "
                    f"得分{p.get('综合得分', 0):.1f}"
                )
                product_details.append(detail)
            
            product_text = "\n".join(product_details)
            
            # 构建提示词
            prompt = f"""你是O2O即时零售（美团闪购/饿了么/京东到家）的商品运营专家。

## 当前分析象限: {quadrant_name}
**定义**: {definition}
**风险**: {risk}
**标准策略**: {strategy}

## 该象限数据概览
- 商品数量: {total_products}个
- 总利润贡献: ¥{total_profit:,.2f}
- 总销量: {total_sales:,.0f}件
- 平均毛利率: {avg_margin:.1%}
- 平均综合得分: {avg_score:.1f}分

## TOP商品明细（按利润影响排序）
{product_text}

## 请输出以下内容（JSON格式）:
```json
{{
    "situation_analysis": "当前象限情况分析（50字内，说明这批商品的整体状态和问题严重程度）",
    "key_findings": [
        "发现1：具体数据支撑的洞察",
        "发现2：具体数据支撑的洞察"
    ],
    "action_items": [
        {{
            "action": "具体操作（如：对XX商品降低营销投入30%）",
            "expected_result": "预期效果（如：预计月省¥XXX）",
            "priority": "紧急/重要/一般"
        }}
    ],
    "priority_products": ["最需要优先处理的商品名称1", "商品名称2"]
}}
```

要求：
1. 基于实际数据给出分析，不要泛泛而谈
2. 行动建议要具体到商品名称和数值
3. 考虑O2O即时零售特点（配送成本、平台抽佣、时效性等）"""

            completion = self.client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {"role": "system", "content": "你是O2O即时零售商品运营专家，擅长基于数据给出可执行的优化建议。只输出JSON格式，不要其他内容。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.6,
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # 解析JSON
            # 处理可能的markdown代码块
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            result = json.loads(response_text)
            
            return {
                'quadrant_code': quadrant_code,
                'quadrant_name': quadrant_name,
                'product_count': total_products,
                'total_profit': total_profit,
                'quadrant_summary': result.get('situation_analysis', ''),
                'key_findings': result.get('key_findings', []),
                'action_items': result.get('action_items', []),
                'priority_products': result.get('priority_products', [])
            }
            
        except json.JSONDecodeError as e:
            print(f"[AI] JSON解析失败: {e}")
            return {
                'quadrant_code': quadrant_code,
                'quadrant_name': QUADRANT_KNOWLEDGE.get(quadrant_code, {}).get('name', '未知'),
                'product_count': len(products),
                'quadrant_summary': f'该象限有{len(products)}个商品，建议参考标准策略进行优化',
                'key_findings': [QUADRANT_KNOWLEDGE.get(quadrant_code, {}).get('strategy', '')],
                'action_items': [],
                'priority_products': []
            }
        except Exception as e:
            print(f"[AI] 象限分析失败: {e}")
            return {
                'quadrant_code': quadrant_code,
                'error': str(e)
            }

    def analyze_all_quadrants_sync(self, scoring_data: List[Dict[str, Any]], 
                                    priority_quadrants: List[str] = None) -> Dict[str, Any]:
        """
        分析所有象限（或指定优先象限）
        
        Args:
            scoring_data: 评分模型输出的完整商品数据
            priority_quadrants: 优先分析的象限列表，默认分析问题象限 [Q4, Q3, Q2, Q8]
        
        Returns:
            {
                'overall_health': 整体健康度评分,
                'quadrant_analyses': {Q1: {...}, Q2: {...}, ...},
                'top_actions': 最重要的3条行动建议
            }
        """
        if priority_quadrants is None:
            # 默认优先分析问题象限（按严重程度排序）
            priority_quadrants = ['Q4', 'Q3', 'Q2', 'Q8', 'Q1']
        
        # 按象限分组
        quadrant_groups = {}
        for product in scoring_data:
            q_code = product.get('象限编号', 'Q0')
            if q_code not in quadrant_groups:
                quadrant_groups[q_code] = []
            quadrant_groups[q_code].append(product)
        
        # 计算整体健康度
        total_products = len(scoring_data)
        golden_count = len(quadrant_groups.get('Q5', []))  # 黄金商品
        problem_count = len(quadrant_groups.get('Q4', [])) + len(quadrant_groups.get('Q8', []))  # 双输+淘汰
        
        health_score = 100
        if total_products > 0:
            # 黄金商品占比加分，问题商品占比扣分
            health_score = min(100, max(0, 
                60 + (golden_count / total_products * 50) - (problem_count / total_products * 40)
            ))
        
        # 分析优先象限
        quadrant_analyses = {}
        for q_code in priority_quadrants:
            if q_code in quadrant_groups and len(quadrant_groups[q_code]) > 0:
                analysis = self.analyze_quadrant_deep(q_code, quadrant_groups[q_code])
                quadrant_analyses[q_code] = analysis
        
        # 也分析黄金商品（Q5）和引流爆款（Q7）作为正面案例
        for q_code in ['Q5', 'Q7', 'Q6']:
            if q_code in quadrant_groups and len(quadrant_groups[q_code]) > 0 and q_code not in quadrant_analyses:
                analysis = self.analyze_quadrant_deep(q_code, quadrant_groups[q_code])
                quadrant_analyses[q_code] = analysis
        
        # 汇总最重要的行动建议
        all_actions = []
        for q_code, analysis in quadrant_analyses.items():
            for action in analysis.get('action_items', []):
                action['from_quadrant'] = q_code
                all_actions.append(action)
        
        # 按优先级排序
        priority_order = {'紧急': 0, '重要': 1, '一般': 2}
        all_actions.sort(key=lambda x: priority_order.get(x.get('priority', '一般'), 2))
        
        return {
            'overall_health': round(health_score, 1),
            'total_products': total_products,
            'quadrant_distribution': {k: len(v) for k, v in quadrant_groups.items()},
            'quadrant_analyses': quadrant_analyses,
            'top_actions': all_actions[:5]
        }


def analyze_product_quadrant(product_data: Dict[str, Any]) -> str:
    """
    分析单个商品的象限归属，生成优化建议
    
    Args:
        product_data: 商品数据字典，包含：
            - 商品名称
            - 象限名称
            - 毛利率
            - 售罄率 (可选)
            - 营销占比
            - 月售
            - 优化建议 (原有建议)
    
    Returns:
        AI生成的优化建议（50字以内）
    """
    try:
        client = get_client()
        
        # 构建提示词
        prompt = f"""你是一个零售商品运营专家。请根据以下商品数据，给出简短的优化建议（30字以内）。

商品名称: {product_data.get('商品名称', '未知')}
当前象限: {product_data.get('象限名称', '未知')}
毛利率: {product_data.get('毛利率', 0):.1%}
月销量: {product_data.get('月售', 0):.0f}件
营销占比: {product_data.get('营销占比', 0):.1%}

请直接给出优化建议，不要解释原因，不要使用markdown格式。"""

        completion = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": "你是一个零售商品运营专家，擅长商品定价和营销策略优化。回答要简洁直接。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"[AI] 商品分析失败: {e}")
        return product_data.get('优化建议', '暂无建议')


def generate_marketing_insight(analysis_summary: Dict[str, Any]) -> str:
    """
    生成营销分析整体洞察报告
    
    Args:
        analysis_summary: 分析汇总数据，包含：
            - total_products: 商品总数
            - quadrant_distribution: 各象限商品数量
            - problem_products: 问题商品列表（TOP5）
            - golden_products: 黄金商品列表（TOP5）
            - avg_margin: 平均毛利率
            - avg_turnover: 平均动销率
    
    Returns:
        AI生成的洞察报告
    """
    try:
        client = get_client()
        
        # 构建提示词
        prompt = f"""你是一个零售数据分析专家。请根据以下商品分析数据，生成一份简洁的洞察报告（150字以内）。

## 数据概览
- 商品总数: {analysis_summary.get('total_products', 0)}个
- 平均毛利率: {analysis_summary.get('avg_margin', 0):.1%}
- 黄金商品(⭐): {analysis_summary.get('golden_count', 0)}个
- 问题商品(需优化): {analysis_summary.get('problem_count', 0)}个
- 淘汰区商品: {analysis_summary.get('eliminate_count', 0)}个

## 各象限分布
{json.dumps(analysis_summary.get('quadrant_distribution', {}), ensure_ascii=False, indent=2)}

## TOP问题商品
{', '.join(analysis_summary.get('problem_products', ['无'])[:5])}

## TOP黄金商品
{', '.join(analysis_summary.get('golden_products', ['无'])[:5])}

请从以下角度给出洞察：
1. 整体商品结构是否健康
2. 最需要关注的问题
3. 1-2条具体的改进建议

输出格式：直接输出文字，不要使用markdown格式，不要分点列出。"""

        completion = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": "你是一个零售数据分析专家，擅长从数据中发现商业洞察。回答要简洁、有洞察力、可执行。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        
        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"[AI] 洞察生成失败: {e}")
        return "AI分析暂时不可用，请检查网络连接。"


def generate_batch_advice(products: List[Dict[str, Any]], max_products: int = 10) -> Dict[str, str]:
    """
    批量生成商品优化建议（一次API调用）
    
    Args:
        products: 商品列表
        max_products: 最大处理商品数
    
    Returns:
        {商品名称: 优化建议} 字典
    """
    try:
        client = get_client()
        
        # 只处理前N个商品
        products = products[:max_products]
        
        # 构建商品列表文本
        product_text = "\n".join([
            f"{i+1}. {p.get('商品名称', '未知')} | {p.get('象限名称', '未知')} | 毛利率{p.get('毛利率', 0):.0%} | 月售{p.get('月售', 0):.0f}"
            for i, p in enumerate(products)
        ])
        
        prompt = f"""你是零售商品运营专家。请为以下{len(products)}个商品分别给出简短优化建议（每个15字以内）。

商品列表：
{product_text}

请按以下JSON格式输出，只输出JSON，不要其他内容：
{{"商品名称1": "建议1", "商品名称2": "建议2", ...}}"""

        completion = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": "你是零售运营专家，回答要简洁。只输出JSON格式。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.5,
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # 尝试解析JSON
        # 处理可能的markdown代码块
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        return json.loads(response_text)
    
    except json.JSONDecodeError as e:
        print(f"[AI] JSON解析失败: {e}")
        return {}
    except Exception as e:
        print(f"[AI] 批量建议生成失败: {e}")
        return {}


def test_connection() -> bool:
    """测试API连接"""
    try:
        client = get_client()
        completion = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "user", "content": "你好"},
            ],
            max_tokens=10,
        )
        return True
    except Exception as e:
        print(f"[AI] 连接测试失败: {e}")
        return False


# 便捷函数
def get_ai_insight_for_tab7(scientific_result: List[Dict], scoring_result: List[Dict]) -> Dict[str, Any]:
    """
    为营销分析Tab生成AI洞察
    
    Args:
        scientific_result: 科学方法分析结果
        scoring_result: 评分模型分析结果
    
    Returns:
        {
            'insight': AI洞察报告,
            'problem_advice': {商品名: 建议},
            'success': True/False
        }
    """
    try:
        import pandas as pd
        
        # 使用科学方法的结果（更精确）
        df = pd.DataFrame(scientific_result)
        
        if df.empty:
            return {'insight': '暂无数据', 'problem_advice': {}, 'success': False}
        
        # 统计各象限
        quadrant_dist = df['象限名称'].value_counts().to_dict() if '象限名称' in df.columns else {}
        
        # 识别黄金商品和问题商品
        golden = df[df['象限名称'].str.contains('黄金', na=False)]['商品名称'].tolist() if '象限名称' in df.columns else []
        problems = df[df['优先级'].isin(['P0', 'P1', 'P2'])]['商品名称'].tolist() if '优先级' in df.columns else []
        eliminate = df[df['象限名称'].str.contains('淘汰', na=False)]['商品名称'].tolist() if '象限名称' in df.columns else []
        
        # 构建汇总数据
        summary = {
            'total_products': len(df),
            'avg_margin': df['毛利率'].mean() if '毛利率' in df.columns else 0,
            'golden_count': len(golden),
            'problem_count': len(problems),
            'eliminate_count': len(eliminate),
            'quadrant_distribution': quadrant_dist,
            'problem_products': problems[:5],
            'golden_products': golden[:5],
        }
        
        # 生成整体洞察
        insight = generate_marketing_insight(summary)
        
        # 为问题商品生成建议
        problem_df = df[df['优先级'].isin(['P0', 'P1'])].head(10).to_dict('records') if '优先级' in df.columns else []
        problem_advice = generate_batch_advice(problem_df) if problem_df else {}
        
        return {
            'insight': insight,
            'problem_advice': problem_advice,
            'summary': summary,
            'success': True
        }
    
    except Exception as e:
        print(f"[AI] Tab7洞察生成失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'insight': f'AI分析失败: {str(e)}',
            'problem_advice': {},
            'success': False
        }


if __name__ == "__main__":
    # 测试连接
    print("测试通义千问API连接...")
    if test_connection():
        print("✅ 连接成功!")
        
        # 测试商品分析
        test_product = {
            '商品名称': '可口可乐500ml',
            '象限名称': '⭐黄金商品',
            '毛利率': 0.35,
            '月售': 1200,
            '营销占比': 0.08,
        }
        print(f"\n测试商品分析: {test_product['商品名称']}")
        advice = analyze_product_quadrant(test_product)
        print(f"AI建议: {advice}")
    else:
        print("❌ 连接失败!")
