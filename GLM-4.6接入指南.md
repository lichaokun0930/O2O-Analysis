# GLM-4.6大模型接入指南

> 本文档详细说明如何在其他看板中集成智谱GLM-4.6大模型

## 📦 一、环境准备

### 1.1 安装依赖

```bash
# 安装智谱GLM官方SDK (支持GLM-4.6)
pip install zhipuai

# 可选: 安装dotenv用于环境变量管理
pip install python-dotenv
```

### 1.2 获取API密钥

1. 访问智谱AI开放平台: https://open.bigmodel.cn/usercenter/apikeys
2. 注册/登录账号
3. 创建API密钥
4. 复制密钥备用

### 1.3 配置环境变量

**方式1: 创建`.env`文件** (推荐)
```ini
# .env
ZHIPU_API_KEY=your_api_key_here
AI_MODEL_TYPE=glm
```

**方式2: 系统环境变量**
```bash
# Windows PowerShell
$env:ZHIPU_API_KEY="your_api_key_here"

# Linux/Mac
export ZHIPU_API_KEY="your_api_key_here"
```

---

## 🔧 二、核心模块说明

### 2.1 ai_analyzer.py 模块结构

```
ai_analyzer.py
├── AIAnalyzer 类           # AI分析器主类
│   ├── __init__()          # 初始化,支持多模型
│   ├── _init_glm()         # GLM-4.6初始化
│   ├── _generate_content() # 统一内容生成接口
│   └── analyze_*()         # 各种分析方法
└── get_ai_analyzer()       # 工厂函数
```

### 2.2 GLM-4.6初始化代码

```python
def _init_glm(self):
    """初始化智谱GLM-4.6"""
    from zhipuai import ZhipuAI
    
    # 创建客户端 (使用编程工具专用端点)
    self.client = ZhipuAI(
        api_key=self.api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/coding"  # GLM-4.6编程工具专用端点
    )
    
    # 设置模型版本
    self.model_name = 'glm-4.6'  # 最新版本
    self.use_zai = False
    
    print(f"✅ 已配置GLM-4.6")
```

### 2.3 API调用代码

```python
def _generate_content(self, prompt: str) -> str:
    """调用GLM-4.6生成内容"""
    response = self.client.chat.completions.create(
        model=self.model_name,              # 'glm-4.6'
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,                    # 创造性参数 (0-1)
        max_tokens=4096                     # 最大输出长度
    )
    
    return response.choices[0].message.content
```

---

## 🚀 三、快速集成步骤

### 3.1 复制核心文件

将以下文件复制到您的项目目录:
```
your_project/
├── ai_analyzer.py              # ✅ 必需: AI分析器模块
├── ai_business_context.py      # 可选: 业务上下文提示词
└── .env                        # ✅ 必需: API密钥配置
```

### 3.2 基础使用示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例: 在您的看板中集成GLM-4.6
"""

from ai_analyzer import get_ai_analyzer
import os

# Step 1: 初始化AI分析器
def init_ai_model():
    """初始化GLM-4.6"""
    # 从环境变量读取API密钥
    api_key = os.getenv('ZHIPU_API_KEY')
    
    if not api_key:
        print("⚠️ 请设置ZHIPU_API_KEY环境变量")
        return None
    
    # 创建分析器实例
    analyzer = get_ai_analyzer(api_key=api_key, model_type='glm')
    
    if analyzer and analyzer.is_ready():
        print("✅ GLM-4.6 已就绪")
        return analyzer
    else:
        print("❌ GLM-4.6 初始化失败")
        return None

# Step 2: 使用分析器
analyzer = init_ai_model()

if analyzer:
    # 示例1: 基础文本生成
    prompt = "分析销量下滑的可能原因"
    result = analyzer._generate_content(prompt)
    print(result)
    
    # 示例2: 结构化数据分析
    product_data = {
        'name': '商品A',
        'sales_decline': -30.5,
        'avg_price': 89.9,
        'stock': 150
    }
    analysis = analyzer.analyze_sales_decline(product_data)
    print(analysis)
```

### 3.3 在Streamlit中集成

```python
import streamlit as st
from ai_analyzer import get_ai_analyzer
import os

# 缓存AI分析器实例
@st.cache_resource
def load_ai_analyzer():
    """加载并缓存AI分析器"""
    api_key = os.getenv('ZHIPU_API_KEY')
    if api_key:
        return get_ai_analyzer(api_key=api_key, model_type='glm')
    return None

# 主界面
st.title("🤖 AI智能分析")

# 初始化
analyzer = load_ai_analyzer()

if analyzer and analyzer.is_ready():
    st.success("✅ GLM-4.6 已连接")
    
    # 输入框
    user_input = st.text_area("输入您的问题:", height=100)
    
    if st.button("🔍 开始分析"):
        if user_input:
            with st.spinner("正在分析..."):
                result = analyzer._generate_content(user_input)
                st.markdown("### 分析结果")
                st.write(result)
        else:
            st.warning("请输入问题")
else:
    st.error("❌ AI分析器未就绪,请检查API密钥配置")
    st.info("💡 设置环境变量: ZHIPU_API_KEY=your_key")
```

### 3.4 在Dash中集成

```python
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from ai_analyzer import get_ai_analyzer
import os

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 全局AI分析器
AI_ANALYZER = None

def init_ai_analyzer():
    """初始化AI分析器"""
    global AI_ANALYZER
    if AI_ANALYZER is None:
        api_key = os.getenv('ZHIPU_API_KEY')
        AI_ANALYZER = get_ai_analyzer(api_key=api_key, model_type='glm')
    return AI_ANALYZER

# 布局
app.layout = dbc.Container([
    html.H1("🤖 AI智能分析", className="text-center my-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Textarea(
                id='user-input',
                placeholder='输入您的问题...',
                style={'height': '200px'}
            ),
            dbc.Button(
                "🔍 开始分析",
                id='analyze-btn',
                color='primary',
                className='mt-3'
            )
        ], width=12)
    ]),
    
    html.Div(id='analysis-result', className='mt-4')
])

# 回调函数
@app.callback(
    Output('analysis-result', 'children'),
    Input('analyze-btn', 'n_clicks'),
    State('user-input', 'value'),
    prevent_initial_call=True
)
def run_analysis(n_clicks, user_input):
    if not user_input:
        return dbc.Alert("请输入问题", color="warning")
    
    # 初始化分析器
    analyzer = init_ai_analyzer()
    if not analyzer or not analyzer.is_ready():
        return dbc.Alert([
            html.Strong("❌ AI分析器未就绪"),
            html.Br(),
            html.Small("请设置 ZHIPU_API_KEY 环境变量")
        ], color="danger")
    
    try:
        # 调用AI分析
        result = analyzer._generate_content(user_input)
        
        return dbc.Card([
            dbc.CardHeader("🤖 AI分析结果"),
            dbc.CardBody([
                html.P(result, style={'white-space': 'pre-wrap'})
            ])
        ], className="shadow-sm")
        
    except Exception as e:
        return dbc.Alert(f"❌ 分析失败: {str(e)}", color="danger")

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
```

---

## 🎯 四、高级功能

### 4.1 多模型切换

```python
import os

# 设置模型类型
os.environ['AI_MODEL_TYPE'] = 'glm'    # 智谱GLM-4.6
# os.environ['AI_MODEL_TYPE'] = 'qwen'  # 通义千问
# os.environ['AI_MODEL_TYPE'] = 'gemini' # Gemini

# 自动选择模型
model_type = os.getenv('AI_MODEL_TYPE', 'glm')
analyzer = get_ai_analyzer(model_type=model_type)
```

### 4.2 自定义业务提示词

```python
# 在调用前添加业务上下文
business_context = """
您是一位资深的O2O零售业务专家,精通门店运营和数据分析。
请基于以下业务背景进行分析:
- 业务类型: O2O闪购
- 主要渠道: 美团外卖、饿了么
- 配送模式: 骑手配送 + 用户自提
"""

user_question = "如何提升客单价?"

# 组合完整提示词
full_prompt = f"{business_context}\n\n问题: {user_question}"

# 调用分析
result = analyzer._generate_content(full_prompt)
```

### 4.3 流式输出 (高级)

```python
def stream_analysis(analyzer, prompt: str):
    """流式输出分析结果"""
    response = analyzer.client.chat.completions.create(
        model='glm-4.6',
        messages=[{"role": "user", "content": prompt}],
        stream=True  # 启用流式输出
    )
    
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# 使用示例
for text in stream_analysis(analyzer, "分析销量趋势"):
    print(text, end='', flush=True)
```

### 4.4 错误处理与重试

```python
import time

def safe_generate(analyzer, prompt: str, max_retries: int = 3) -> str:
    """带重试机制的内容生成"""
    for attempt in range(max_retries):
        try:
            result = analyzer._generate_content(prompt)
            return result
        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                return f"❌ 分析失败,已重试{max_retries}次"

# 使用
result = safe_generate(analyzer, "分析数据")
```

---

## 📊 五、实战案例

### 5.1 销量下滑分析

```python
def analyze_product_decline(analyzer, product_name: str, data: dict):
    """分析商品销量下滑原因"""
    prompt = f"""
    商品名称: {product_name}
    销量变化: {data['sales_change']}%
    价格: ¥{data['price']}
    库存: {data['stock']}
    竞品情况: {data.get('competitor_info', '未知')}
    
    请分析可能的原因并提供改进建议。
    """
    
    return analyzer._generate_content(prompt)

# 使用示例
product_data = {
    'sales_change': -25.3,
    'price': 89.9,
    'stock': 120,
    'competitor_info': '竞品降价10%'
}

result = analyze_product_decline(analyzer, "商品A", product_data)
print(result)
```

### 5.2 客单价优化建议

```python
def get_pricing_suggestions(analyzer, current_metrics: dict):
    """获取客单价优化建议"""
    prompt = f"""
    当前运营数据:
    - 平均客单价: ¥{current_metrics['avg_order_value']}
    - 订单数: {current_metrics['order_count']}
    - 商品平均价格: ¥{current_metrics['avg_product_price']}
    - 客户复购率: {current_metrics['repeat_rate']}%
    
    请提供3-5条具体的客单价提升策略。
    """
    
    return analyzer._generate_content(prompt)
```

### 5.3 场景营销策略

```python
def generate_marketing_strategy(analyzer, scene: str, target_group: str):
    """生成场景化营销策略"""
    prompt = f"""
    场景: {scene}
    目标客群: {target_group}
    
    请制定具体的营销策略,包括:
    1. 商品组合建议
    2. 促销活动方案
    3. 推广渠道选择
    4. 预期效果评估
    """
    
    return analyzer._generate_content(prompt)

# 使用示例
strategy = generate_marketing_strategy(
    analyzer,
    scene="早餐场景",
    target_group="上班族"
)
```

---

## ⚙️ 六、配置参数说明

### 6.1 模型参数

| 参数 | 说明 | 默认值 | 取值范围 |
|------|------|--------|----------|
| `model` | 模型版本 | `glm-4.6` | `glm-4`, `glm-4.6` |
| `temperature` | 创造性参数 | `0.7` | 0.0 - 1.0 |
| `max_tokens` | 最大输出长度 | `4096` | 1 - 8192 |
| `top_p` | 核采样参数 | `0.7` | 0.0 - 1.0 |

### 6.2 temperature参数建议

- **0.0 - 0.3**: 精确分析、数据计算 (确定性高)
- **0.4 - 0.7**: 业务建议、策略规划 (平衡)
- **0.8 - 1.0**: 创意文案、头脑风暴 (创造性高)

### 6.3 使用示例

```python
# 精确数据分析
response = analyzer.client.chat.completions.create(
    model='glm-4.6',
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2,  # 低温度,更精确
    max_tokens=2048
)

# 创意营销文案
response = analyzer.client.chat.completions.create(
    model='glm-4.6',
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,  # 高温度,更有创意
    max_tokens=4096
)
```

---

## 🔍 七、常见问题排查

### 7.1 API密钥无效

**问题**: `❌ 401 Unauthorized`

**解决方案**:
1. 检查API密钥是否正确
2. 确认密钥是否已激活
3. 检查账户余额是否充足

```python
# 测试API密钥
import os
from zhipuai import ZhipuAI

api_key = os.getenv('ZHIPU_API_KEY')
client = ZhipuAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model='glm-4.6',
        messages=[{"role": "user", "content": "你好"}]
    )
    print("✅ API密钥有效")
except Exception as e:
    print(f"❌ API密钥测试失败: {e}")
```

### 7.2 超时错误

**问题**: `❌ Request timeout`

**解决方案**:
```python
from zhipuai import ZhipuAI
import httpx

# 设置超时时间
client = ZhipuAI(
    api_key=api_key,
    timeout=httpx.Timeout(60.0)  # 60秒超时
)
```

### 7.3 速率限制

**问题**: `❌ 429 Too Many Requests`

**解决方案**:
```python
import time

def call_with_retry(client, prompt, max_retries=3):
    for i in range(max_retries):
        try:
            response = client.chat.completions.create(
                model='glm-4.6',
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                wait_time = 2 ** i  # 指数退避
                print(f"速率限制,等待{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                raise
```

### 7.4 模型版本不支持

**问题**: `❌ Model not found: glm-4.6`

**解决方案**:
```python
# 降级到glm-4
self.model_name = 'glm-4'

# 或检查可用模型
available_models = ['glm-4', 'glm-4.6', 'glm-3-turbo']
```

---

## 📚 八、参考资源

### 8.1 官方文档

- **智谱AI开放平台**: https://open.bigmodel.cn/
- **API文档**: https://open.bigmodel.cn/dev/api
- **SDK文档**: https://github.com/zhipuai/zhipuai-sdk-python
- **定价说明**: https://open.bigmodel.cn/pricing

### 8.2 示例代码

- **本项目完整代码**: `ai_analyzer.py`
- **Dash集成示例**: `智能门店看板_Dash版.py`
- **Streamlit示例**: `智能门店经营看板_可视化.py`

### 8.3 社区支持

- **GitHub Issues**: https://github.com/zhipuai/zhipuai-sdk-python/issues
- **技术论坛**: https://open.bigmodel.cn/forum

---

## ✅ 九、检查清单

在部署前,请确认以下事项:

- [ ] 已安装 `zhipuai` SDK
- [ ] 已获取有效的API密钥
- [ ] API密钥已配置到环境变量
- [ ] 账户余额充足
- [ ] 已测试基础调用功能
- [ ] 已实现错误处理机制
- [ ] 已设置合理的超时时间
- [ ] 已复制必要的模块文件

---

## 🎉 十、总结

通过本指南,您应该能够:

1. ✅ 在任何Python项目中集成GLM-4.6
2. ✅ 理解API调用的完整流程
3. ✅ 实现基础和高级功能
4. ✅ 排查常见问题
5. ✅ 优化性能和用户体验

**核心要点**:
- 使用官方 `zhipuai` SDK
- 指定模型版本为 `glm-4.6`
- 妥善管理API密钥
- 实现错误处理和重试机制
- 根据场景调整温度参数

**下一步**:
- 探索更多AI分析场景
- 优化提示词工程
- 集成到实际业务系统
- 监控API使用情况和成本

---

*最后更新: 2025年10月27日*
*作者: GitHub Copilot*
