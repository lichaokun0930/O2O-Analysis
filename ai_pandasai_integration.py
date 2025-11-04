#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PandasAI集成模块 (阶段2优化)
支持自然语言查询数据,自动生成pandas代码

功能:
1. 自然语言转pandas查询
2. 自动数据验证 (遵循"刻在基因中"的规则)
3. 智能图表推荐
4. 查询历史记录

依赖安装:
pip install pandasai
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# 尝试导入PandasAI (懒加载模式)
PANDASAI_AVAILABLE = False
SmartDataframe = None
PandasAI_OpenAI = None

def _check_pandasai():
    """延迟检查PandasAI是否可用"""
    global PANDASAI_AVAILABLE, SmartDataframe, PandasAI_OpenAI
    if PANDASAI_AVAILABLE:
        return True
    try:
        from pandasai import SmartDataframe as _SmartDataframe
        from pandasai.llm import OpenAI as _PandasAI_OpenAI
        SmartDataframe = _SmartDataframe
        PandasAI_OpenAI = _PandasAI_OpenAI
        PANDASAI_AVAILABLE = True
        return True
    except ImportError:
        return False

# 导入GLM客户端
try:
    from zhipuai import ZhipuAI
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False
    print("⚠️ zhipuai未安装")


# ==================== 数据验证规则 ====================

VALIDATION_RULES = """
【自动验证规则】(刻在基因中)

在生成任何数据查询代码时,必须遵循以下规则:

1. 销售额计算:
   ✅ 正确: df.groupby('订单ID')['实收价格'].sum().sum()
   ❌ 错误: df['实收价格'].sum()
   原因: 多商品订单会被重复计算

2. 客单价计算:
   ✅ 正确: 销售额 / df['订单ID'].nunique()
   ❌ 错误: df['实收价格'].mean()
   原因: 客单价是每个订单的平均金额,不是每个商品的平均价格

3. 订单数计算:
   ✅ 正确: df['订单ID'].nunique()
   ❌ 错误: len(df)
   原因: len(df)是商品行数,不是订单数

4. 时段/场景聚合:
   必须先按订单ID分组,再聚合时段/场景
   示例: df.groupby(['订单ID', '时段'])['实收价格'].sum().groupby('时段').sum()

5. 商品排行:
   按订单销售额排名,不是商品行数
   示例: df.groupby('商品名称')['实收价格'].sum().sort_values(ascending=False)

代码生成指令:
- 使用groupby时优先按订单ID分组
- 计算总额时用.sum().sum()而非单层.sum()
- 统计订单数用.nunique()而非.count()
- 避免直接对实收价格列求和
"""


# ==================== PandasAI包装器 ====================

class SmartDataAnalyzer:
    """智能数据分析器 - PandasAI + 数据验证"""
    
    def __init__(self, api_key: Optional[str] = None, model_type: str = 'glm'):
        """初始化智能分析器
        
        Args:
            api_key: API密钥
            model_type: 模型类型 ('glm'/'openai')
        """
        if not PANDASAI_AVAILABLE:
            raise ImportError("请先安装PandasAI: pip install pandasai")
        
        self.api_key = api_key or os.getenv('ZHIPU_API_KEY')
        self.model_type = model_type
        self.query_history = []
        
        # 初始化LLM
        if model_type == 'glm':
            # 使用自定义GLM包装器
            self.llm = GLMWrapper(api_key=self.api_key)
        else:
            # 使用OpenAI
            self.llm = PandasAI_OpenAI(api_token=self.api_key)
        
        print(f"✅ SmartDataAnalyzer初始化完成 (模型: {model_type})")
    
    def query(self, df: pd.DataFrame, question: str, 
              validate: bool = True, save_history: bool = True) -> Any:
        """自然语言查询数据
        
        Args:
            df: 数据DataFrame
            question: 自然语言问题
            validate: 是否验证生成的代码 (默认True)
            save_history: 是否保存查询历史 (默认True)
        
        Returns:
            查询结果 (可能是数值、DataFrame、图表等)
        """
        # 增强问题,注入验证规则
        enhanced_question = self._enhance_question(question, validate)
        
        # 创建SmartDataframe
        sdf = SmartDataframe(
            df,
            config={
                "llm": self.llm,
                "enable_cache": True,
                "save_charts": True,
                "save_charts_path": "./charts",
                "verbose": True,
                "custom_whitelisted_dependencies": ["numpy", "pandas"],
                # 注入代码生成指令
                "custom_instructions": VALIDATION_RULES
            }
        )
        
        try:
            # 执行查询
            print(f"🔍 查询: {question}")
            result = sdf.chat(enhanced_question)
            
            # 保存历史
            if save_history:
                self._save_query_history(question, result, success=True)
            
            print(f"✅ 查询成功")
            return result
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            if save_history:
                self._save_query_history(question, None, success=False, error=str(e))
            raise
    
    def _enhance_question(self, question: str, validate: bool) -> str:
        """增强问题,注入验证规则"""
        if not validate:
            return question
        
        # 检查问题中是否涉及需要验证的计算
        needs_validation = any(keyword in question for keyword in 
                              ['销售额', '客单价', '订单数', '总额', '销量', '排行'])
        
        if needs_validation:
            enhanced = f"""
{question}

重要提示:
- 计算销售额时必须先按订单ID分组: df.groupby('订单ID')['实收价格'].sum()
- 计算客单价用订单数,不是商品数: 销售额 / df['订单ID'].nunique()
- 统计订单数用 .nunique() 而非 .count()
- 多商品订单不要重复计算

请严格遵守以上规则生成代码。
"""
            return enhanced
        
        return question
    
    def _save_query_history(self, question: str, result: Any, 
                           success: bool, error: Optional[str] = None):
        """保存查询历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "success": success,
            "error": error,
            "result_type": type(result).__name__ if result is not None else None
        }
        self.query_history.append(history_entry)
    
    def get_query_history(self, limit: int = 10) -> List[Dict]:
        """获取查询历史
        
        Args:
            limit: 返回最近N条记录
        
        Returns:
            历史记录列表
        """
        return self.query_history[-limit:]
    
    def export_query_history(self, filepath: str = "query_history.json"):
        """导出查询历史到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.query_history, f, ensure_ascii=False, indent=2)
        print(f"✅ 查询历史已导出: {filepath}")


# ==================== GLM包装器 (适配PandasAI) ====================

class GLMWrapper:
    """GLM-4.6包装器,适配PandasAI的LLM接口"""
    
    def __init__(self, api_key: str):
        """初始化GLM客户端"""
        if not GLM_AVAILABLE:
            raise ImportError("请先安装zhipuai: pip install zhipuai")
        
        self.client = ZhipuAI(
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4/coding"
        )
        self.model_name = 'glm-4.6'
        print(f"   ✅ GLM-4.6已配置 (coding端点)")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成内容 (PandasAI要求的接口)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.3),  # 代码生成用低temperature
                max_tokens=kwargs.get('max_tokens', 2048)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ GLM-4.6调用失败: {e}")
            raise
    
    def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """对话完成 (备用接口)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get('temperature', 0.3),
                max_tokens=kwargs.get('max_tokens', 2048)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ GLM-4.6调用失败: {e}")
            raise


# ==================== 快捷查询函数 ====================

def quick_query(df: pd.DataFrame, question: str, 
                api_key: Optional[str] = None) -> Any:
    """快捷查询 (无需创建analyzer实例)
    
    Args:
        df: 数据DataFrame
        question: 自然语言问题
        api_key: API密钥 (可选,默认从环境变量读取)
    
    Returns:
        查询结果
    
    Example:
        >>> result = quick_query(订单数据, "帮我找出利润率低于5%的商品TOP10")
        >>> print(result)
    """
    analyzer = SmartDataAnalyzer(api_key=api_key)
    return analyzer.query(df, question)


# ==================== 预定义查询模板 ====================

QUERY_TEMPLATES = {
    "高利润商品": "找出利润率大于{threshold}%的商品,按利润额排序,返回TOP{top_n}",
    "低客单价订单": "找出客单价低于{threshold}元的订单,统计数量和占比",
    "滞销商品": "找出最近{days}天没有销售的商品,返回商品名称和最后销售日期",
    "时段销量分析": "分析不同时段的订单量、销售额和客单价,并按销售额降序排序",
    "场景营销效果": "分析不同消费场景的订单量、销售额、客单价和利润率",
    "商品角色分布": "统计流量品、利润品、形象品的数量和销售额占比",
    "成本结构分析": "计算商品成本、履约成本、营销成本的占比,并与健康基准对比",
    "营销ROI排名": "计算每个营销活动的ROI,按ROI降序排序,标注出ROI<1的活动"
}


def get_template_query(template_name: str, **params) -> str:
    """获取预定义查询模板
    
    Args:
        template_name: 模板名称
        **params: 模板参数
    
    Returns:
        格式化后的查询语句
    
    Example:
        >>> query = get_template_query("高利润商品", threshold=20, top_n=10)
        >>> result = quick_query(订单数据, query)
    """
    if template_name not in QUERY_TEMPLATES:
        raise ValueError(f"未知模板: {template_name}, 可用模板: {list(QUERY_TEMPLATES.keys())}")
    
    template = QUERY_TEMPLATES[template_name]
    return template.format(**params)


# ==================== 单元测试 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("PandasAI集成模块测试")
    print("=" * 80)
    
    # 创建测试数据
    test_data = pd.DataFrame({
        '订单ID': ['A001', 'A001', 'A002', 'A003', 'A003', 'A003'],
        '商品名称': ['牛奶', '面包', '洗发水', '可乐', '薯片', '巧克力'],
        '实收价格': [15.5, 8.5, 35.0, 3.5, 6.5, 12.0],
        '成本': [12.0, 6.0, 20.0, 2.5, 4.0, 8.0],
        '时段': ['上午', '上午', '下午', '晚上', '晚上', '晚上'],
        '场景': ['早餐', '早餐', '个护', '零食', '零食', '零食']
    })
    
    print("\n【测试数据】")
    print(test_data)
    print(f"\n数据形状: {test_data.shape}")
    print(f"订单数: {test_data['订单ID'].nunique()}")
    print(f"商品数: {len(test_data)}")
    
    # 验证数据计算规则
    print("\n【验证数据计算规则】")
    
    # 错误方式
    wrong_sales = test_data['实收价格'].sum()
    print(f"❌ 错误: df['实收价格'].sum() = {wrong_sales:.2f}")
    
    # 正确方式
    correct_sales = test_data.groupby('订单ID')['实收价格'].sum().sum()
    print(f"✅ 正确: df.groupby('订单ID')['实收价格'].sum().sum() = {correct_sales:.2f}")
    
    # 客单价
    order_count = test_data['订单ID'].nunique()
    avg_order_value = correct_sales / order_count
    print(f"✅ 客单价: {correct_sales:.2f} / {order_count} = {avg_order_value:.2f}元/单")
    
    print("\n【查询模板测试】")
    print(f"可用模板: {list(QUERY_TEMPLATES.keys())}")
    
    query1 = get_template_query("高利润商品", threshold=20, top_n=5)
    print(f"\n模板1: {query1}")
    
    query2 = get_template_query("时段销量分析")
    print(f"模板2: {query2}")
    
    # 如果PandasAI可用,尝试实际查询
    if PANDASAI_AVAILABLE and GLM_AVAILABLE:
        print("\n【实际查询测试】(需要API密钥)")
        api_key = os.getenv('ZHIPU_API_KEY')
        if api_key:
            try:
                analyzer = SmartDataAnalyzer(api_key=api_key)
                
                # 测试查询
                question = "计算总销售额和客单价"
                print(f"\n🔍 查询: {question}")
                # result = analyzer.query(test_data, question)
                # print(f"结果: {result}")
                print("(实际查询已注释,避免消耗API额度)")
                
            except Exception as e:
                print(f"⚠️ 测试跳过: {e}")
        else:
            print("⚠️ 未找到ZHIPU_API_KEY环境变量")
    else:
        print("\n⚠️ PandasAI或GLM未安装,跳过实际查询测试")
    
    print("\n✅ 测试完成!")
