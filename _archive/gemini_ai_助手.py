#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini AI 智能分析助手
集成 Google Gemini API,为看板提供全方位智能分析能力
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai 未安装，请运行: pip install google-generativeai")


class GeminiAIAssistant:
    """Gemini AI 智能分析助手"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化AI助手
        
        Args:
            api_key: Gemini API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        self.model = None
        self.chat_history = []
        self.context_data = {}  # 存储当前数据上下文
        
        if GEMINI_AVAILABLE and self.api_key:
            self._initialize_model()
        else:
            print("⚠️ AI助手未初始化: 缺少API密钥或依赖库")
    
    def _initialize_model(self):
        """初始化Gemini模型"""
        try:
            genai.configure(api_key=self.api_key)
            
            # 从环境变量读取模型名称,默认使用 gemini-1.5-flash
            model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
            temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
            max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))
            
            # 使用 Gemini 1.5 Flash (快速响应) 或 Pro (更准确)
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    'temperature': temperature,  # 控制创造性
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': max_tokens,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            # 设置系统提示词
            self.system_prompt = """你是一位专业的O2O门店数据分析专家。你的职责是:
1. 分析商品销售数据,识别趋势和异常
2. 解读四象限分析(明星/金牛/引流/淘汰商品)
3. 提供库存优化建议
4. 分析客单价变化原因
5. 给出商品定价和促销建议

请用专业但易懂的语言回答,提供具体可执行的建议。
当分析数据时,请关注:
- 数据趋势和变化
- 异常值和潜在问题
- 业务影响和优化机会
- 具体的行动建议

回答时请简洁明了,突出重点,使用emoji增强可读性。"""
            
            print("✅ Gemini AI助手初始化成功")
            
        except Exception as e:
            print(f"❌ AI助手初始化失败: {str(e)}")
            self.model = None
    
    def is_ready(self) -> bool:
        """检查AI助手是否就绪"""
        return self.model is not None
    
    def _safe_generate(self, prompt: str) -> str:
        """
        安全地调用Gemini API并处理各种错误情况
        
        Args:
            prompt: 提示词
            
        Returns:
            AI回复文本或错误信息
        """
        try:
            response = self.model.generate_content(prompt)
            
            # 检查响应是否有效
            if not response.candidates or len(response.candidates) == 0:
                return "⚠️ API返回空响应,可能被安全过滤。请尝试换个问法。"
            
            candidate = response.candidates[0]
            
            # 检查finish_reason
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                # 根据Google AI文档: STOP=1, MAX_TOKENS=2, SAFETY=3, RECITATION=4
                if finish_reason == 3:  # SAFETY
                    return "⚠️ 内容被安全过滤拦截。建议:\n1. 换个更中性的问法\n2. 避免敏感词汇\n3. 使用更专业的术语"
                elif finish_reason == 2:  # MAX_TOKENS
                    # 尝试提取已生成的内容
                    if candidate.content and candidate.content.parts:
                        partial = ''.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                        return f"{partial}\n\n⚠️ (回复被截断,已达到最大长度)"
                    return "⚠️ 回复超出长度限制,请简化问题或分多次提问"
            
            # 提取文本内容
            if hasattr(response, 'text') and response.text:
                return response.text
            elif candidate.content and candidate.content.parts:
                return ''.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
            else:
                return f"⚠️ 无法解析AI回复 (finish_reason={getattr(candidate, 'finish_reason', 'unknown')})"
                
        except AttributeError as e:
            return f"⚠️ API响应格式异常: {str(e)}\n建议: 换个问法或检查API配置"
        except Exception as e:
            return f"❌ API调用失败: {str(e)}"
    
    def update_context(self, context_type: str, data: Any):
        """
        更新数据上下文
        
        Args:
            context_type: 上下文类型 (quadrant_data, sales_trend, inventory等)
            data: 数据内容
        """
        self.context_data[context_type] = data
    
    def analyze_quadrant_data(self, quadrant_summary: Dict) -> str:
        """
        分析四象限数据
        
        Args:
            quadrant_summary: 四象限汇总数据
            
        Returns:
            分析结果文本
        """
        if not self.is_ready():
            return "⚠️ AI助手未就绪,请配置API密钥"
        
        prompt = f"""请分析以下商品四象限数据:

{json.dumps(quadrant_summary, ensure_ascii=False, indent=2)}

请提供:
1. 整体商品结构评估
2. 各象限商品占比分析
3. 存在的问题和风险
4. 具体优化建议

限制在300字以内。"""
        
        return self._safe_generate(prompt)
    
    def analyze_sales_trend(self, trend_data: pd.DataFrame, product_name: str = None) -> str:
        """
        分析销量趋势
        
        Args:
            trend_data: 趋势数据DataFrame
            product_name: 商品名称(可选)
            
        Returns:
            分析结果文本
        """
        if not self.is_ready():
            return "⚠️ AI助手未就绪,请配置API密钥"
        
        # 简化数据用于分析
        data_summary = trend_data.head(20).to_dict('records') if hasattr(trend_data, 'to_dict') else str(trend_data)[:500]
        
        product_info = f"商品: {product_name}\n" if product_name else ""
        
        prompt = f"""{product_info}请分析以下销售趋势数据:

{json.dumps(data_summary, ensure_ascii=False, indent=2)}

请提供:
1. 趋势变化分析(上升/下降/稳定)
2. 异常时间点识别
3. 可能原因分析
4. 应对建议

限制在250字以内。"""
        
        return self._safe_generate(prompt)
    
    def analyze_inventory_alert(self, alert_products: List[Dict]) -> str:
        """
        分析库存预警
        
        Args:
            alert_products: 预警商品列表
            
        Returns:
            分析结果文本
        """
        if not self.is_ready():
            return "⚠️ AI助手未就绪,请配置API密钥"
        
        prompt = f"""以下商品出现库存预警:

{json.dumps(alert_products[:10], ensure_ascii=False, indent=2)}

请分析:
1. 预警商品特征
2. 潜在影响
3. 优先处理顺序
4. 补货建议

限制在200字以内。"""
        
        return self._safe_generate(prompt)
    
    def analyze_avg_price_change(self, price_data: Dict) -> str:
        """
        分析客单价变化
        
        Args:
            price_data: 客单价数据
            
        Returns:
            分析结果文本
        """
        if not self.is_ready():
            return "⚠️ AI助手未就绪,请配置API密钥"
        
        prompt = f"""请分析以下客单价变化数据:

{json.dumps(price_data, ensure_ascii=False, indent=2)}

请提供:
1. 客单价变化趋势
2. 主要影响因素
3. 不同场景表现
4. 提升建议

限制在250字以内。"""
        
        return self._safe_generate(prompt)
    
    def chat(self, user_message: str, include_context: bool = True) -> str:
        """
        智能对话
        
        Args:
            user_message: 用户消息
            include_context: 是否包含数据上下文
            
        Returns:
            AI回复
        """
        if not self.is_ready():
            return "⚠️ AI助手未就绪,请配置API密钥"
        
        # 构建完整提示词
        full_prompt = self.system_prompt + "\n\n"
        
        if include_context and self.context_data:
            full_prompt += "当前数据上下文:\n"
            for ctx_type, ctx_data in self.context_data.items():
                # 简化数据避免过长
                ctx_str = str(ctx_data)[:500] if not isinstance(ctx_data, dict) else json.dumps(ctx_data, ensure_ascii=False)[:500]
                full_prompt += f"\n{ctx_type}: {ctx_str}\n"
        
        # 添加简洁回复指令
        full_prompt += f"\n\n用户问题: {user_message}\n\n请简洁回答(200字以内),突出重点:"
        
        # 使用安全生成
        reply_text = self._safe_generate(full_prompt)
        
        # 如果不是错误消息,记录对话历史
        if not reply_text.startswith('❌') and not reply_text.startswith('⚠️'):
            self.chat_history.append({
                'timestamp': datetime.now().isoformat(),
                'user': user_message,
                'assistant': reply_text
            })
        
        return reply_text
    
    def generate_report(self, report_type: str = 'comprehensive') -> str:
        """
        生成分析报告
        
        Args:
            report_type: 报告类型 (comprehensive/weekly/daily)
            
        Returns:
            报告内容
        """
        if not self.is_ready():
            return "⚠️ AI助手未就绪,请配置API密钥"
        
        context_summary = "\n".join([
            f"{k}: {str(v)[:300]}..." 
            for k, v in self.context_data.items()
        ])
        
        prompt = f"""基于以下数据,生成一份{report_type}分析报告:

{context_summary}

报告应包含:
1. 📊 整体概况
2. ⭐ 亮点发现
3. ⚠️ 风险预警
4. 💡 优化建议
5. 📈 趋势预测

请用markdown格式,限制在500字以内。"""
        
        return self._safe_generate(prompt)
    
    def get_quick_insights(self, data_type: str) -> List[str]:
        """
        获取快速洞察(预设问题模板)
        
        Args:
            data_type: 数据类型
            
        Returns:
            问题列表
        """
        templates = {
            'quadrant': [
                "为什么明星商品数量在下降?",
                "哪些金牛商品有潜力转为明星?",
                "淘汰商品应该如何处理?",
                "当前商品结构健康吗?",
            ],
            'sales': [
                "销量下降的主要原因是什么?",
                "哪个时段销售最好?",
                "如何提升销量?",
                "有哪些销售异常?",
            ],
            'inventory': [
                "哪些商品需要紧急补货?",
                "库存周转率如何?",
                "如何优化库存?",
                "有滞销风险吗?",
            ],
            'price': [
                "客单价为什么下降?",
                "如何提升客单价?",
                "定价策略合理吗?",
                "促销效果如何?",
            ]
        }
        
        return templates.get(data_type, [
            "请分析当前数据",
            "有什么优化建议?",
            "发现哪些问题?",
        ])
    
    def clear_history(self):
        """清空对话历史"""
        self.chat_history = []
    
    def export_chat_history(self) -> str:
        """导出对话历史为JSON"""
        return json.dumps(self.chat_history, ensure_ascii=False, indent=2)


# 创建全局AI助手实例
_ai_assistant = None

def get_ai_assistant(api_key: Optional[str] = None) -> GeminiAIAssistant:
    """获取AI助手单例"""
    global _ai_assistant
    if _ai_assistant is None or api_key:
        _ai_assistant = GeminiAIAssistant(api_key)
    return _ai_assistant


if __name__ == '__main__':
    # 测试代码
    print("🧪 测试 Gemini AI 助手...")
    
    # 从环境变量读取API密钥进行测试
    assistant = get_ai_assistant()
    
    if assistant.is_ready():
        print("✅ AI助手就绪")
        
        # 测试对话
        response = assistant.chat("你好,请介绍一下你的功能")
        print(f"\n🤖 AI回复:\n{response}")
    else:
        print("⚠️ 请设置环境变量 GEMINI_API_KEY 或在代码中提供API密钥")
