# 通义千问大模型配置使用说明

## 📋 文件说明

- **qwen_config.py**: 纯净的千问模型配置文件，不包含任何业务逻辑
- **qwen_使用说明.md**: 本文档，使用指南

## 🔧 配置说明

### 1. API密钥配置

在 `qwen_config.py` 中修改以下配置：

```python
# 方式1: 直接配置（简单但不够安全）
QWEN_API_KEY = "sk-1a559ff60a514d27a17be7f1bd20bfdd"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen3-max"

# 方式2: 从环境变量读取（推荐）
QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'your_default_key')
```

### 2. 模型选择

通义千问提供多个模型版本：

| 模型名称 | 说明 | 适用场景 |
|---------|------|---------|
| `qwen3-max` | 最新最强版本 | 复杂推理、长文本理解、代码生成 |
| `qwen-max` | 强性能版本 | 复杂推理、长文本理解 |
| `qwen-plus` | 平衡性能 | 日常对话、文本生成 |
| `qwen-turbo` | 快速响应 | 简单任务、高并发 |

### 3. 获取API密钥

1. 访问阿里云百炼平台: https://dashscope.console.aliyun.com/
2. 注册/登录账号
3. 进入"API-KEY管理"页面
4. 创建新的API密钥
5. 复制密钥到配置文件

## 🚀 快速开始

### 测试连接

```bash
# 运行测试脚本
python qwen_config.py
```

### 基础使用示例

#### 1. 简单对话

```python
from qwen_config import simple_chat

# 单轮对话
response = simple_chat("你好，介绍一下自己")
print(response)

# 带系统提示词
response = simple_chat(
    user_message="分析这段代码的时间复杂度",
    system_prompt="你是一个Python编程专家"
)
print(response)
```

#### 2. 多轮对话

```python
from qwen_config import chat

messages = [
    {"role": "system", "content": "你是一个友好的AI助手"},
    {"role": "user", "content": "我想学习Python"},
    {"role": "assistant", "content": "很好！Python是一门很适合初学者的语言"},
    {"role": "user", "content": "从哪里开始学习？"}
]

response = chat(messages)
print(response)
```

#### 3. 流式输出

```python
from qwen_config import stream_chat

messages = [{"role": "user", "content": "写一首关于春天的诗"}]

for chunk in stream_chat(messages):
    print(chunk, end='', flush=True)
```

#### 4. JSON格式输出

```python
from qwen_config import json_chat

result = json_chat(
    user_message="分析'今天天气真好'的情感，返回JSON格式",
    system_prompt="你是情感分析专家，只输出JSON格式: {\"sentiment\": \"正面/负面/中性\", \"score\": 0-1}"
)

print(result)
# 输出: {'sentiment': '正面', 'score': 0.95}
```

## 📚 API参考

### chat()

完整的对话函数，支持所有参数。

```python
def chat(
    messages: List[Dict[str, str]],  # 消息列表
    model: str = None,                # 模型名称
    temperature: float = 0.7,         # 温度参数 (0-2)
    max_tokens: int = 1000,           # 最大token数
    stream: bool = False,             # 是否流式输出
    **kwargs                          # 其他参数
) -> str:
```

**参数说明:**
- `messages`: 消息列表，每条消息包含 `role` 和 `content`
  - `role`: "system" | "user" | "assistant"
  - `content`: 消息内容
- `temperature`: 控制随机性，0=确定性，2=最随机
- `max_tokens`: 限制生成长度
- `stream`: True时返回流式对象

### simple_chat()

简化的单轮对话函数。

```python
def simple_chat(
    user_message: str,           # 用户消息
    system_prompt: str = None,   # 系统提示词
    temperature: float = 0.7,    # 温度参数
    max_tokens: int = 1000       # 最大token数
) -> str:
```

### stream_chat()

流式输出函数，逐字返回内容。

```python
def stream_chat(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> Generator[str]:
```

### json_chat()

返回JSON格式的对话函数。

```python
def json_chat(
    user_message: str,
    system_prompt: str = None,
    temperature: float = 0.5,    # 建议较低温度
    max_tokens: int = 2000
) -> Dict[str, Any]:
```

### 工具函数

```python
# 测试连接
test_connection() -> bool

# 获取配置信息
get_model_info() -> Dict[str, Any]

# 获取客户端实例
get_client() -> OpenAI
```

## 💡 使用技巧

### 1. 温度参数选择

```python
# 创意写作、头脑风暴 (高随机性)
response = simple_chat("写一个科幻故事", temperature=1.2)

# 日常对话 (平衡)
response = simple_chat("介绍一下Python", temperature=0.7)

# 数据分析、代码生成 (低随机性)
response = simple_chat("写一个排序算法", temperature=0.3)

# JSON输出、结构化数据 (最低随机性)
result = json_chat("分析情感", temperature=0.1)
```

### 2. 系统提示词设计

```python
# 角色定位
system_prompt = "你是一个资深Python工程师，擅长代码优化和性能调优"

# 输出格式要求
system_prompt = "你是数据分析师。回答要简洁，使用要点列表，不超过100字"

# 专业领域
system_prompt = "你是医疗健康专家，回答要准确、专业，引用权威来源"
```

### 3. 错误处理

```python
from qwen_config import chat

try:
    response = chat(messages)
    print(response)
except Exception as e:
    print(f"调用失败: {e}")
    # 处理错误，如重试、降级等
```

### 4. 成本控制

```python
# 限制token数量
response = simple_chat("介绍Python", max_tokens=100)

# 使用更便宜的模型
from qwen_config import chat, QWEN_MODEL
response = chat(messages, model="qwen-turbo")  # 替代默认的qwen3-max
```

## 🔒 安全建议

### 1. 使用环境变量

创建 `.env` 文件：

```bash
DASHSCOPE_API_KEY=sk-your-api-key-here
```

修改 `qwen_config.py`：

```python
from dotenv import load_dotenv
load_dotenv()

QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY')
```

### 2. 不要提交密钥到Git

在 `.gitignore` 中添加：

```
.env
qwen_config.py  # 如果包含硬编码密钥
```

### 3. 生产环境配置

```python
# 使用配置管理系统
import boto3  # AWS Secrets Manager
import azure.keyvault  # Azure Key Vault

# 或使用配置中心
QWEN_API_KEY = config_center.get('qwen_api_key')
```

## 📊 性能优化

### 1. 客户端复用

```python
# ✅ 好的做法 - 复用客户端
from qwen_config import get_client

client = get_client()  # 单例模式，自动复用

# ❌ 不好的做法 - 每次创建新客户端
# client = OpenAI(api_key=..., base_url=...)
```

### 2. 批量处理

```python
# 批量生成多个回复
messages_list = [
    [{"role": "user", "content": "问题1"}],
    [{"role": "user", "content": "问题2"}],
    [{"role": "user", "content": "问题3"}],
]

responses = [chat(msgs) for msgs in messages_list]
```

### 3. 异步调用

```python
import asyncio
from openai import AsyncOpenAI

async_client = AsyncOpenAI(
    api_key=QWEN_API_KEY,
    base_url=QWEN_BASE_URL
)

async def async_chat(messages):
    completion = await async_client.chat.completions.create(
        model=QWEN_MODEL,
        messages=messages
    )
    return completion.choices[0].message.content

# 并发调用
responses = await asyncio.gather(
    async_chat(messages1),
    async_chat(messages2),
    async_chat(messages3)
)
```

## 🐛 常见问题

### Q1: 连接超时

```python
# 增加超时时间
from openai import OpenAI

client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url=QWEN_BASE_URL,
    timeout=60.0  # 60秒超时
)
```

### Q2: JSON解析失败

```python
# 在提示词中明确要求JSON格式
system_prompt = """
你是AI助手。请严格按照以下JSON格式输出，不要包含任何其他内容：
{
    "key1": "value1",
    "key2": "value2"
}
"""
```

### Q3: 响应内容被截断

```python
# 增加max_tokens
response = simple_chat("写一篇长文章", max_tokens=4000)
```

### Q4: API密钥无效

```python
# 检查密钥是否正确
from qwen_config import test_connection

if not test_connection():
    print("请检查API密钥配置")
```

## 📖 更多资源

- 官方文档: https://help.aliyun.com/zh/dashscope/
- API参考: https://help.aliyun.com/zh/dashscope/developer-reference/api-details
- 模型介绍: https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction
- 价格说明: https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-metering-and-billing

## 📝 更新日志

- 2024-12-23: 创建纯净版配置文件
  - 移除所有业务逻辑
  - 提供基础调用函数
  - 添加完整使用示例
