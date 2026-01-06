# -*- coding: utf-8 -*-
"""
通义千问大模型配置文件
纯净版 - 不包含业务逻辑，仅提供模型配置和基础调用功能
"""

from openai import OpenAI
from typing import Dict, List, Optional, Any
import json
import os

# =============================================================================
# 模型配置
# =============================================================================

# API配置
QWEN_API_KEY = "sk-1a559ff60a514d27a17be7f1bd20bfdd"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen3-max"  # 可选: qwen3-max, qwen-max, qwen-plus, qwen-turbo

# 或者从环境变量读取（推荐）
# QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'your_default_key')

# =============================================================================
# 客户端初始化
# =============================================================================

_client = None

def get_client() -> OpenAI:
    """
    获取OpenAI客户端（懒加载，单例模式）
    
    Returns:
        OpenAI: 配置好的客户端实例
    """
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
        )
    return _client


# =============================================================================
# 基础调用函数
# =============================================================================

def chat(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    stream: bool = False,
    **kwargs
) -> str:
    """
    基础对话函数
    
    Args:
        messages: 消息列表，格式: [{"role": "user", "content": "你好"}]
        model: 模型名称，默认使用QWEN_MODEL
        temperature: 温度参数 (0-2)，越高越随机
        max_tokens: 最大生成token数
        stream: 是否流式输出
        **kwargs: 其他参数
    
    Returns:
        str: 模型回复内容
    
    Example:
        >>> response = chat([{"role": "user", "content": "你好"}])
        >>> print(response)
    """
    try:
        client = get_client()
        
        completion = client.chat.completions.create(
            model=model or QWEN_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        
        if stream:
            return completion  # 返回流式对象
        else:
            return completion.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"[Qwen] 调用失败: {e}")
        raise


def simple_chat(
    user_message: str,
    system_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """
    简化的对话函数（单轮对话）
    
    Args:
        user_message: 用户消息
        system_prompt: 系统提示词（可选）
        temperature: 温度参数
        max_tokens: 最大token数
    
    Returns:
        str: 模型回复
    
    Example:
        >>> response = simple_chat("介绍一下Python")
        >>> print(response)
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": user_message})
    
    return chat(messages, temperature=temperature, max_tokens=max_tokens)


def stream_chat(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
):
    """
    流式对话函数
    
    Args:
        messages: 消息列表
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大token数
    
    Yields:
        str: 逐字输出的内容
    
    Example:
        >>> for chunk in stream_chat([{"role": "user", "content": "讲个故事"}]):
        >>>     print(chunk, end='', flush=True)
    """
    try:
        client = get_client()
        
        stream = client.chat.completions.create(
            model=model or QWEN_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    except Exception as e:
        print(f"[Qwen] 流式调用失败: {e}")
        raise


def json_chat(
    user_message: str,
    system_prompt: str = None,
    temperature: float = 0.5,
    max_tokens: int = 2000
) -> Dict[str, Any]:
    """
    JSON格式输出的对话函数
    
    Args:
        user_message: 用户消息
        system_prompt: 系统提示词
        temperature: 温度参数（建议较低以保证JSON格式）
        max_tokens: 最大token数
    
    Returns:
        Dict: 解析后的JSON对象
    
    Example:
        >>> result = json_chat("分析这段文本的情感: 今天天气真好")
        >>> print(result)
    """
    if system_prompt is None:
        system_prompt = "你是一个AI助手。请以JSON格式输出结果，不要包含其他内容。"
    
    response = simple_chat(user_message, system_prompt, temperature, max_tokens)
    
    # 尝试解析JSON
    try:
        # 处理可能的markdown代码块
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
        
        return json.loads(response.strip())
    
    except json.JSONDecodeError as e:
        print(f"[Qwen] JSON解析失败: {e}")
        print(f"原始响应: {response}")
        raise


# =============================================================================
# 工具函数
# =============================================================================

def test_connection() -> bool:
    """
    测试API连接是否正常
    
    Returns:
        bool: 连接成功返回True，否则返回False
    """
    try:
        response = simple_chat("你好", max_tokens=10)
        print(f"[Qwen] 连接测试成功，响应: {response}")
        return True
    except Exception as e:
        print(f"[Qwen] 连接测试失败: {e}")
        return False


def get_model_info() -> Dict[str, Any]:
    """
    获取当前配置信息
    
    Returns:
        Dict: 配置信息字典
    """
    return {
        "model": QWEN_MODEL,
        "base_url": QWEN_BASE_URL,
        "api_key_prefix": QWEN_API_KEY[:10] + "..." if QWEN_API_KEY else None,
        "client_initialized": _client is not None
    }


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("通义千问大模型配置测试")
    print("=" * 60)
    
    # 1. 测试连接
    print("\n1. 测试API连接...")
    if test_connection():
        print("✅ 连接成功!")
    else:
        print("❌ 连接失败!")
        exit(1)
    
    # 2. 查看配置信息
    print("\n2. 当前配置信息:")
    info = get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # 3. 简单对话测试
    print("\n3. 简单对话测试:")
    response = simple_chat("用一句话介绍Python编程语言", max_tokens=100)
    print(f"   问: 用一句话介绍Python编程语言")
    print(f"   答: {response}")
    
    # 4. 多轮对话测试
    print("\n4. 多轮对话测试:")
    messages = [
        {"role": "system", "content": "你是一个友好的AI助手"},
        {"role": "user", "content": "你好，我想学习编程"},
        {"role": "assistant", "content": "你好！学习编程是个很好的选择。你想学习哪种编程语言呢？"},
        {"role": "user", "content": "推荐一个适合初学者的"}
    ]
    response = chat(messages, max_tokens=200)
    print(f"   答: {response}")
    
    # 5. JSON输出测试
    print("\n5. JSON输出测试:")
    try:
        result = json_chat(
            "请分析'今天天气真好'这句话的情感，输出JSON格式: {\"sentiment\": \"正面/负面/中性\", \"confidence\": 0.0-1.0}",
            max_tokens=100
        )
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   JSON测试失败: {e}")
    
    # 6. 流式输出测试
    print("\n6. 流式输出测试:")
    print("   问: 讲一个简短的笑话")
    print("   答: ", end='', flush=True)
    try:
        for chunk in stream_chat([{"role": "user", "content": "讲一个简短的笑话"}], max_tokens=200):
            print(chunk, end='', flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\n   流式测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
