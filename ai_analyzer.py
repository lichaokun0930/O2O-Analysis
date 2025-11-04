#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析助手模块 - 专注于数据洞察和策略建议
不包含对话功能,只提供一次性深度分析
支持多种国内外大模型: 通义千问/智谱GLM/Gemini

✨ 集成业务逻辑: 所有AI分析都基于O2O闪购业务背景
"""

import os
from typing import Dict, List, Any, Optional
import pandas as pd
import requests
import json

# ✨ 导入业务上下文模块
try:
    from ai_business_context import (
        get_base_prompt,
        get_analysis_prompt,
        get_profit_decline_prompt,
        get_product_structure_prompt,
        get_marketing_roi_prompt,
        get_period_scenario_prompt,
        get_health_warnings,
        BUSINESS_CONTEXT
    )
    BUSINESS_CONTEXT_AVAILABLE = True
    print("✅ 业务上下文模块已加载 - AI分析将基于O2O闪购业务逻辑")
except ImportError:
    BUSINESS_CONTEXT_AVAILABLE = False
    print("⚠️ 业务上下文模块未找到,AI分析将使用通用模式")

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()  # 从.env文件加载配置
except ImportError:
    pass

# 检测可用的AI库
QWEN_AVAILABLE = False
GLM_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    import dashscope
    QWEN_AVAILABLE = True
    print("✅ 通义千问SDK可用")
except ImportError:
    pass

try:
    from zai import ZhipuAiClient
    GLM_AVAILABLE = True
    print("✅ 智谱GLM SDK可用 (zai)")
except ImportError:
    try:
        from zhipuai import ZhipuAI
        GLM_AVAILABLE = True
        print("✅ 智谱GLM SDK可用 (zhipuai)")
    except ImportError:
        pass

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✅ Gemini SDK可用")
except ImportError:
    pass

if not any([QWEN_AVAILABLE, GLM_AVAILABLE, GEMINI_AVAILABLE]):
    print("⚠️ 未安装任何AI SDK,AI分析功能不可用")
    print("   推荐安装: pip install zai (智谱GLM)")


class AIAnalyzer:
    """AI分析助手 - 支持多种国内外大模型"""
    
    def __init__(self, api_key: Optional[str] = None, model_type: str = 'auto'):
        """初始化AI分析器
        
        Args:
            api_key: API密钥,如果不提供则从环境变量读取
            model_type: 模型类型 'qwen'(通义千问)/'glm'(智谱)/'gemini'/auto(自动检测)
        """
        self.ready = False
        self.model_type = None
        
        # 自动检测可用模型
        if model_type == 'auto':
            if QWEN_AVAILABLE:
                model_type = 'qwen'
            elif GLM_AVAILABLE:
                model_type = 'glm'
            elif GEMINI_AVAILABLE:
                model_type = 'gemini'
            else:
                print("❌ 没有可用的AI模型")
                return
        
        # 获取API密钥
        if api_key:
            self.api_key = api_key
        else:
            # 根据模型类型读取不同的环境变量
            env_keys = {
                'qwen': 'DASHSCOPE_API_KEY',
                'glm': 'ZHIPU_API_KEY',
                'gemini': 'GEMINI_API_KEY'
            }
            self.api_key = os.getenv(env_keys.get(model_type, 'DASHSCOPE_API_KEY'))
        
        if not self.api_key:
            print(f"⚠️ 未设置API密钥")
            return
        
        try:
            if model_type == 'qwen' and QWEN_AVAILABLE:
                self._init_qwen()
            elif model_type == 'glm' and GLM_AVAILABLE:
                self._init_glm()
            elif model_type == 'gemini' and GEMINI_AVAILABLE:
                self._init_gemini()
            else:
                print(f"❌ 模型类型 {model_type} 不可用")
                return
            
            self.model_type = model_type
            self.ready = True
            model_names = {
                'qwen': '通义千问',
                'glm': '智谱GLM',
                'gemini': 'Gemini'
            }
            print(f"✅ AI分析器初始化成功 (使用{model_names.get(model_type)})")
            
        except Exception as e:
            print(f"❌ AI分析器初始化失败: {e}")
    
    def _init_qwen(self):
        """初始化通义千问"""
        dashscope.api_key = self.api_key
        self.model_name = 'qwen-max'  # 或 qwen-plus, qwen-turbo
    
    def _init_glm(self):
        """初始化智谱GLM - 使用GLM-4.6"""
        try:
            # 优先使用官方SDK (兼容OpenAI协议)
            from zhipuai import ZhipuAI
            # 使用标准API端点 (官方文档: https://open.bigmodel.cn/api/paas/v4/)
            self.client = ZhipuAI(
                api_key=self.api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            )
            # GLM-4.6 是官方支持的模型名称
            self.model_name = 'glm-4.6'
            self.use_zai = False
            print(f"   ✅ 已配置GLM-4.6 (标准API端点)")
        except ImportError:
            # 备用: zai SDK
            try:
                from zai import ZhipuAiClient
                self.client = ZhipuAiClient(api_key=self.api_key)
                self.model_name = 'glm-4'
                self.use_zai = True
                print(f"   ⚠️ 使用 zai SDK")
            except ImportError:
                raise ImportError("请安装 zhipuai SDK: pip install zhipuai")
    
    def _init_gemini(self):
        """初始化Gemini"""
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def is_ready(self) -> bool:
        """检查AI分析器是否就绪"""
        return self.ready
    
    def _generate_content(self, prompt: str) -> str:
        """统一的内容生成接口,支持多种模型
        
        Args:
            prompt: 提示词
        
        Returns:
            生成的文本
        """
        try:
            if self.model_type == 'qwen':
                # 通义千问API调用
                from dashscope import Generation
                response = Generation.call(
                    model=self.model_name,
                    prompt=prompt,
                    result_format='message',
                    max_tokens=4096,
                    temperature=0.7
                )
                if response.status_code == 200:
                    return response.output.text
                else:
                    return f"❌ 调用失败: {response.message}"
            
            elif self.model_type == 'glm':
                # 智谱GLM API调用
                if hasattr(self, 'use_zai') and self.use_zai:
                    # 使用 zai SDK
                    print(f"   [DEBUG] 使用 zai SDK, 模型: {self.model_name}")
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=4096
                    )
                    print(f"   [DEBUG] Response type: {type(response)}")
                    print(f"   [DEBUG] Response: {response}")
                    result = response.choices[0].message.content
                    print(f"   [DEBUG] Content length: {len(result) if result else 0}")
                    return result
                else:
                    # 使用官方 zhipuai SDK
                    print(f"   [DEBUG] 使用 zhipuai SDK, 模型: {self.model_name}")
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=4096
                    )
                    print(f"   [DEBUG] Response type: {type(response)}")
                    result = response.choices[0].message.content
                    print(f"   [DEBUG] Content length: {len(result) if result else 0}")
                    return result
            
            elif self.model_type == 'gemini':
                # Gemini API调用
                response = self.model.generate_content(prompt)
                return response.text
            
            else:
                return "❌ 未知的模型类型"
        
        except Exception as e:
            return f"❌ AI调用失败: {str(e)}"
    
    def analyze_sales_decline(self, product_data: Dict) -> str:
        """分析销量下滑问题
        
        Args:
            product_data: 商品数据字典,包含:
                - product_name: 商品名称
                - current_sales: 当前销量
                - previous_sales: 之前销量
                - decline_rate: 下滑比例
                - price: 售价
                - cost: 成本
                - margin: 利润率
                - inventory: 库存
                - category: 分类
        
        Returns:
            结构化的分析报告
        """
        if not self.ready:
            return "❌ AI分析器未就绪,请检查API配置"
        
        # ✨ 使用业务上下文增强的提示词
        if BUSINESS_CONTEXT_AVAILABLE:
            base_context = get_base_prompt()
            
            # 构建数据摘要
            data_summary = {
                "商品名称": product_data.get('product_name', 'N/A'),
                "商品分类": product_data.get('category', 'N/A'),
                "售价": f"¥{product_data.get('price', 0)}",
                "成本": f"¥{product_data.get('cost', 0)}",
                "利润率": f"{product_data.get('margin', 0)}%",
                "当前销量": f"{product_data.get('current_sales', 0)}件/天",
                "之前销量": f"{product_data.get('previous_sales', 0)}件/天",
                "下滑幅度": f"{product_data.get('decline_rate', 0)}%",
                "库存": f"{product_data.get('inventory', 0)}件"
            }
            
            specific_question = """
请基于O2O闪购业务特点,深度分析销量下滑原因,并提供可执行的解决方案。

重点关注:
1. 该商品属于流量品/利润品/形象品中的哪一类?
2. 利润率是否健康(参考: 流量品<15%, 利润品>30%, 形象品15-30%)?
3. 下滑是否影响门店整体利润?影响程度如何?
4. 解决方案必须考虑成本敏感性和ROI
5. 所有建议必须量化、可执行

输出格式:
## 📊 商品角色定位
[判断商品角色,分析当前状态是否健康]

## 🔍 下滑归因分析
[列出3-5个主要原因,按影响程度排序]

## 💡 解决方案(按ROI排序)
### 方案1: [名称] (ROI: X.X, 优先级: PX)
- 执行内容: [...]
- 预期效果: [量化收益]
- 成本投入: [...]
- 执行周期: X天

### 方案2: ...

## 📈 效果预估
- 预计销量恢复: X% → Y%
- 预计利润影响: +¥X/天
- 整体ROI: X.X

## ⚠️ 风险提示
[潜在风险和注意事项]
"""
            
            prompt = get_analysis_prompt("商品销量下滑诊断", data_summary, specific_question)
        else:
            # 保留原有提示词作为后备方案
            prompt = f"""
你是一位资深零售运营顾问。请基于以下数据进行深度分析:

📊 商品信息:
- 商品名称: {product_data.get('product_name', 'N/A')}
- 商品分类: {product_data.get('category', 'N/A')}
- 售价: ¥{product_data.get('price', 0)}
- 成本: ¥{product_data.get('cost', 0)}
- 利润率: {product_data.get('margin', 0)}%

📉 销量变化:
- 当前销量: {product_data.get('current_sales', 0)}件/天
- 之前销量: {product_data.get('previous_sales', 0)}件/天
- 下滑幅度: {product_data.get('decline_rate', 0)}%

📦 库存状态:
- 当前库存: {product_data.get('inventory', 0)}件

请提供结构化分析报告,包含:

## 📊 数据洞察
[3-5条关键发现]

## 🔍 根因分析
[按影响程度排序,给出百分比占比]

## 💡 执行策略
### 1. 价格优化方案
- 建议售价: ¥X
- 调整幅度: X%
- 预期影响: 销量变化X%, 利润变化¥X

### 2. 促销方案
- 促销价: ¥X (折扣X%)
- 建议时长: X天
- 预期效果: 销量恢复至X%

### 3. 库存优化
- 建议补货量: X件
- 理由: [具体原因]

## 📈 效果预测
- 销量变化: +X%
- 利润变化: +¥X/天
- 投资回报: X倍

## ⚠️ 注意事项
[风险控制和执行建议]

要求:
1. 数字精确到个位
2. 所有建议可直接执行
3. 给出计算逻辑
4. 考虑实际可操作性
"""
        
        try:
            return self._generate_content(prompt)
        except Exception as e:
            return f"❌ AI分析失败: {str(e)}"
    
    def analyze_profit_optimization(self, product_data: Dict, target_margin: float) -> str:
        """分析利润率优化策略
        
        Args:
            product_data: 商品数据
            target_margin: 目标利润率
        
        Returns:
            优化策略报告
        """
        if not self.ready:
            return "❌ AI分析器未就绪"
        
        current_price = product_data.get('price', 0)
        cost = product_data.get('cost', 0)
        current_margin = product_data.get('margin', 0)
        
        # 计算目标售价
        target_price = cost / (1 - target_margin / 100) if target_margin < 100 else cost * 2
        price_change = target_price - current_price
        price_change_rate = (price_change / current_price) * 100 if current_price > 0 else 0
        
        # ✨ 使用业务上下文增强的提示词
        if BUSINESS_CONTEXT_AVAILABLE:
            # 构建数据摘要
            data_summary = {
                "商品名称": product_data.get('product_name', 'N/A'),
                "当前售价": f"¥{current_price}",
                "商品成本": f"¥{cost}",
                "当前利润率": f"{current_margin}%",
                "目标利润率": f"{target_margin}%",
                "建议售价": f"¥{target_price:.2f}",
                "调价幅度": f"{price_change_rate:.1f}%",
                "日均销量": f"{product_data.get('sales', 0)}件"
            }
            
            # 判断商品角色
            product_role = "未知"
            if current_margin < 15:
                product_role = "流量品(毛利<15%)"
            elif current_margin >= 30:
                product_role = "利润品(毛利>30%)"
            else:
                product_role = "形象品(毛利15-30%)"
            
            specific_question = f"""
请基于O2O闪购业务的商品角色定位,分析利润率优化策略。

商品角色识别: {product_role}

分析要求:
1. 根据商品角色判断是否需要提升利润率
   - 流量品: 关注引流效果,可接受低毛利(<15%)
   - 利润品: 核心盈利商品,目标毛利>30%
   - 形象品: 平衡品质和价格,目标毛利15-30%
2. 评估{target_margin}%利润率是否符合该商品角色定位
3. 提供多种优化路径(调价/降本/组合销售)
4. 所有方案必须量化ROI和风险
5. 考虑O2O特点: 价格敏感,竞争激烈,需快速响应

输出格式:
## 🎯 商品角色诊断
- 当前角色: {product_role}
- 利润率健康度: [评分0-100]
- 目标利润率{target_margin}%是否合理: [是/否,原因]

## 💡 优化方案(按ROI排序)

### 方案1: 价格调整 (ROI: X.X, 优先级: PX)
- 新售价: ¥{target_price:.2f}
- 调价幅度: {price_change_rate:.1f}%
- 价格弹性预估: 销量影响-X%
- 利润变化: +¥X/天
- 可行性: [高/中/低] - [原因]
- 风险: [竞争对手反应,用户流失]

### 方案2: 成本优化 (ROI: X.X, 优先级: PX)
- 目标成本: ¥X (降低X%)
- 实现路径: [供应商谈判/采购优化/规格调整]
- 难度评估: [高/中/低]
- 预期周期: X天

### 方案3: 组合销售 (ROI: X.X, 优先级: PX)
- 搭配商品: [建议XX商品组合]
- 套餐价格: ¥X
- 客单价提升: +X%
- 利润提升: +¥X/单

## 📊 方案对比表
| 方案 | 利润率 | 销量影响 | 日利润 | ROI | 推荐度 |
|------|--------|---------|--------|-----|--------|
| 调价 | {target_margin}% | -X% | +¥X | X.X | ⭐⭐⭐ |
| 降本 | {target_margin}% | 0% | +¥X | X.X | ⭐⭐⭐⭐ |
| 组合 | {target_margin}% | +X% | +¥X | X.X | ⭐⭐⭐⭐⭐ |

## 🚀 执行建议
[分短期/中期/长期,给出具体步骤]

## ⚠️ 风险提示
[市场风险,操作风险,竞争风险]
"""
            
            prompt = get_analysis_prompt("商品利润率优化", data_summary, specific_question)
        else:
            # 保留原有提示词作为后备方案
            prompt = f"""
你是一位资深定价策略顾问。请基于以下数据制定利润率优化方案:

📊 当前状态:
- 商品: {product_data.get('product_name', 'N/A')}
- 售价: ¥{current_price}
- 成本: ¥{cost}
- 利润率: {current_margin}%
- 销量: {product_data.get('sales', 0)}件/天

🎯 优化目标:
- 目标利润率: {target_margin}%
- 需要售价: ¥{target_price:.2f}
- 涨价幅度: ¥{price_change:.2f} ({price_change_rate:.1f}%)

请提供:

## 💰 价格调整方案

### 方案A: 直接涨价
- 新售价: ¥{target_price:.2f}
- 预期销量影响: [基于价格弹性估算]
- 预期利润变化: ¥X/天
- 可行性分析: [考虑市场接受度]

### 方案B: 成本优化
- 需要成本降至: ¥X
- 实现方式: [具体建议]
- 难度评估: [高/中/低]

### 方案C: 组合方案
- 价格微调: ¥X
- 成本优化: ¥X
- 搭配销售: [增加客单价]

## 📊 方案对比
| 方案 | 利润率 | 销量影响 | 总利润 | 推荐度 |
|------|--------|---------|--------|--------|
| A    | {target_margin}% | -X% | +¥X | ⭐⭐⭐ |
| B    | {target_margin}% | 0% | +¥X | ⭐⭐⭐⭐ |
| C    | {target_margin}% | +X% | +¥X | ⭐⭐⭐⭐⭐ |

## 🚀 执行建议
1. [短期行动]
2. [中期行动]
3. [长期行动]

## ⚠️ 风险提示
[需要注意的问题]
"""
        
        try:
            return self._generate_content(prompt)
        except Exception as e:
            return f"❌ AI分析失败: {str(e)}"
    
    def analyze_inventory_optimization(self, product_data: Dict) -> str:
        """分析库存优化策略"""
        if not self.ready:
            return "❌ AI分析器未就绪"
        
        prompt = f"""
你是一位库存管理专家。请分析以下商品的库存优化策略:

📦 库存数据:
- 商品: {product_data.get('product_name', 'N/A')}
- 当前库存: {product_data.get('inventory', 0)}件
- 日均销量: {product_data.get('daily_sales', 0)}件
- 可售天数: {product_data.get('days_of_stock', 0)}天
- 补货周期: {product_data.get('lead_time', 7)}天

💰 财务数据:
- 售价: ¥{product_data.get('price', 0)}
- 成本: ¥{product_data.get('cost', 0)}
- 利润率: {product_data.get('margin', 0)}%

请提供:

## 📊 库存诊断
- 库存健康度: [优秀/良好/预警/危险]
- 主要问题: [列出1-3个]

## 💡 优化策略
### 1. 补货建议
- 建议补货量: X件
- 补货时机: [立即/X天后]
- 理由: [具体分析]

### 2. 安全库存
- 建议安全库存: X件
- 计算依据: [公式+逻辑]

### 3. 库存周转
- 当前周转率: X次/月
- 目标周转率: X次/月
- 改进措施: [具体建议]

## 📈 效果预测
- 缺货风险: 降低X%
- 资金占用: 优化¥X
- 库存周转: 提升X%

## 🚀 执行计划
[按优先级排序的行动清单]
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ AI分析失败: {str(e)}"


def get_ai_analyzer(api_key: Optional[str] = None, model_type: str = 'auto') -> Optional[AIAnalyzer]:
    """获取AI分析器实例
    
    Args:
        api_key: API密钥
        model_type: 模型类型 'qwen'(通义千问)/'glm'(智谱)/'gemini'/'auto'(自动检测)
    
    Returns:
        AIAnalyzer实例,如果初始化失败返回None
    """
    try:
        analyzer = AIAnalyzer(api_key, model_type)
        if analyzer.is_ready():
            return analyzer
        return None
    except Exception as e:
        print(f"❌ 创建AI分析器失败: {e}")
        return None


    def analyze_tab2_comprehensive(self, data_context: Dict) -> Dict[str, str]:
        """Tab 2综合分析工作流 - 依次分析所有板块
        
        Args:
            data_context: 包含所有板块数据的字典
                - quadrant_data: 四象限数据
                - trend_data: 趋势数据
                - ranking_data: 商品排行数据
                - category_data: 分类数据
                - migration_data: 迁移桑基图数据
                - inventory_warnings: 库存预警数据
                - business_rules: 业务规则说明
        
        Returns:
            包含各板块分析结果的字典
        """
        if not self.ready:
            return {'error': "❌ AI分析器未就绪,请检查API配置"}
        
        results = {}
        
        # 1. 四象限分析
        if 'quadrant_data' in data_context:
            results['quadrant'] = self._analyze_quadrant(data_context['quadrant_data'], data_context.get('business_rules', {}))
        
        # 2. 趋势分析
        if 'trend_data' in data_context:
            results['trend'] = self._analyze_trend(data_context['trend_data'])
        
        # 3. 商品排行分析
        if 'ranking_data' in data_context:
            results['ranking'] = self._analyze_ranking(data_context['ranking_data'])
        
        # 4. 分类分析
        if 'category_data' in data_context:
            results['category'] = self._analyze_category(data_context['category_data'])
        
        # 5. 结构分析(桑基图)
        if 'migration_data' in data_context:
            results['structure'] = self._analyze_migration(data_context['migration_data'])
        
        # 6. 库存预警分析
        if 'inventory_warnings' in data_context:
            results['inventory'] = self._analyze_inventory(data_context['inventory_warnings'])
        
        # 7. 生成综合报告
        results['summary'] = self._generate_comprehensive_report(results, data_context)
        
        return results
    
    def _analyze_quadrant(self, quadrant_data: Dict, business_rules: Dict) -> str:
        """分析四象限数据"""
        prompt = f"""
基于商品四象限分析,提供深度洞察:

**数据概览**:
- 商品总数: {quadrant_data.get('total_products', 0)}个
- 四象限分布: {quadrant_data.get('quadrant_stats', {})}
- 平均利润率: {quadrant_data.get('avg_profit_rate', 0):.1f}%

**业务规则**:
{business_rules.get('quadrant_rules', '')}

**高利润TOP3**: {quadrant_data.get('top_products', [])}
**问题商品TOP3**: {quadrant_data.get('problem_products', [])}

请分析:
1. 四象限分布是否健康?
2. 高利润低动销商品如何激活?
3. 低利润高动销商品定价策略?
4. 具体商品优化建议(必须引用真实商品名)

限500字以内。
"""
        return self._generate_content(prompt)
    
    def _analyze_trend(self, trend_data: Dict) -> str:
        """分析趋势数据"""
        prompt = f"""
基于时序趋势数据,分析商品变化:

**趋势统计**:
- 分析周期: {trend_data.get('period', '')}
- 预警商品数: {trend_data.get('warning_count', 0)}个
- 主要预警类型: {trend_data.get('warning_types', [])}

**关键趋势**: {trend_data.get('key_trends', [])}

请分析:
1. 主要趋势及原因
2. 预警商品应对策略
3. 趋势拐点识别

限400字以内。
"""
        return self._generate_content(prompt)
    
    def _analyze_ranking(self, ranking_data: Dict) -> str:
        """分析商品排行"""
        prompt = f"""
基于商品排行榜,识别明星/淘汰商品:

**TOP商品**: {ranking_data.get('top_products', [])}
**BOTTOM商品**: {ranking_data.get('bottom_products', [])}

请分析:
1. 明星商品成功因素
2. 淘汰商品改进方向
3. 排行榜动态变化

限300字以内。
"""
        return self._generate_content(prompt)
    
    def _analyze_category(self, category_data: Dict) -> str:
        """分析品类结构"""
        prompt = f"""
基于分类数据,优化品类结构:

**分类销售TOP5**: {category_data.get('top_categories', [])}
**分类利润分析**: {category_data.get('category_profit', [])}

请分析:
1. 品类结构是否合理?
2. 哪些品类需要加强/削弱?
3. 跨品类组合建议

限300字以内。
"""
        return self._generate_content(prompt)
    
    def _analyze_migration(self, migration_data: Dict) -> str:
        """分析象限迁移"""
        prompt = f"""
基于商品象限迁移数据,分析生命周期:

**主要迁移路径**: {migration_data.get('migration_paths', [])}
**迁移商品数**: {migration_data.get('migration_count', 0)}个

请分析:
1. 哪些迁移是积极的?
2. 哪些迁移需要干预?
3. 商品生命周期管理建议

限300字以内。
"""
        return self._generate_content(prompt)
    
    def _analyze_inventory(self, inventory_warnings: List) -> str:
        """分析库存预警"""
        prompt = f"""
基于库存预警数据,制定补货/清仓策略:

**预警商品数**: {len(inventory_warnings)}个
**预警详情**: {inventory_warnings[:10]}  # 只取前10个

请给出:
1. 补货优先级排序
2. 清仓商品处理方案
3. 库存周转优化建议

限300字以内。
"""
        return self._generate_content(prompt)
    
    def _generate_comprehensive_report(self, analysis_results: Dict, data_context: Dict) -> str:
        """生成综合报告"""
        prompt = f"""
基于以下各板块分析结果,生成综合执行计划:

**四象限分析**: {analysis_results.get('quadrant', 'N/A')[:200]}...
**趋势分析**: {analysis_results.get('trend', 'N/A')[:150]}...
**排行分析**: {analysis_results.get('ranking', 'N/A')[:150]}...
**分类分析**: {analysis_results.get('category', 'N/A')[:150]}...

请整合所有分析,给出:

## 📊 核心发现 (3-5条)
## 💡 优先级策略 (本周/本月/本季度)
## 📈 预期效果 (数据化目标)
## ⚠️ 风险提示

限800字以内。
"""
        return self._generate_content(prompt)


if __name__ == '__main__':
    # 测试代码
    print("测试AI分析器...")
    
    # 模拟数据
    test_data = {
        'product_name': '28寸行李箱',
        'category': '旅行用品',
        'price': 349,
        'cost': 192,
        'margin': 45,
        'current_sales': 15,
        'previous_sales': 22,
        'decline_rate': 31.8,
        'inventory': 50
    }
    
    analyzer = get_ai_analyzer()
    
    if analyzer:
        print("\n" + "="*60)
        print("测试销量下滑分析...")
        print("="*60)
        result = analyzer.analyze_sales_decline(test_data)
        print(result)
    else:
        print("❌ AI分析器初始化失败")
