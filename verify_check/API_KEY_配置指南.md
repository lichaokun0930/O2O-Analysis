# GLM-4.6 API Key 配置指南

## 📋 前提条件
✅ zhipuai SDK 已安装（版本 2.1.5）  
✅ 智能看板已启动  
⚠️ 需要配置 API Key 以激活 AI 分析功能

---

## 🔑 获取 API Key

### 1. 访问智谱AI开放平台
**网址**: https://open.bigmodel.cn/

### 2. 注册/登录账号
- 使用手机号或第三方账号登录
- 新用户可获得免费体验额度

### 3. 创建 API Key
1. 进入"控制台" → "API Keys"
2. 点击"创建新的 API Key"
3. 复制生成的 Key（格式类似：`xxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx`）

---

## ⚙️ 配置方式

### 方案A: PowerShell 环境变量（推荐）✨

**临时配置（当前会话有效）**:
```powershell
# 设置 API Key
$env:ZHIPU_API_KEY = "your_api_key_here"

# 验证配置
echo $env:ZHIPU_API_KEY

# 启动看板
.\启动看板_Python311.ps1
```

**永久配置（系统级）**:
```powershell
# 添加到用户环境变量
[System.Environment]::SetEnvironmentVariable("ZHIPU_API_KEY", "your_api_key_here", "User")

# 重启 PowerShell 后生效
```

---

### 方案B: 修改代码配置文件

**文件**: `ai_analyzer.py`

**位置**: 约第 50-60 行

**修改前**:
```python
# API Key 配置（优先从环境变量读取）
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')
```

**修改后**:
```python
# API Key 配置（直接硬编码）
ZHIPU_API_KEY = "your_api_key_here"  # ⬅️ 替换为实际 Key
```

⚠️ **注意**: 此方法会将 Key 明文保存，不建议用于生产环境或公开代码。

---

### 方案C: 使用 .env 文件（开发推荐）

**步骤**:

1. 在项目根目录创建 `.env` 文件：
```bash
ZHIPU_API_KEY=your_api_key_here
```

2. 确保 `ai_analyzer.py` 加载了 `.env`（已默认支持）：
```python
from dotenv import load_dotenv
load_dotenv()  # 自动加载 .env 文件
```

3. 启动看板即可自动读取。

---

## ✅ 验证配置

### 方法1: 查看启动日志
```
🤖 检查AI分析功能...
   ✅ 已配置GLM-4.6 (标准API端点)
✅ AI分析器初始化成功 (使用智谱GLM)
   ✅ AI分析器就绪 (智谱GLM-4.6)  ⬅️ 看到这行说明配置成功
```

### 方法2: 测试 API 调用
```powershell
& ".\.venv311\Scripts\python.exe" -c "
import os
os.environ['ZHIPU_API_KEY'] = 'your_key_here'
from ai_analyzer import get_ai_analyzer
analyzer = get_ai_analyzer('glm')
print('✅ API Key 配置成功!' if analyzer else '❌ 配置失败')
"
```

### 方法3: 使用看板功能
1. 访问 http://localhost:8050
2. 切换到 Tab 4（商品分析）
3. 点击"生成 AI 洞察"按钮
4. 如果返回分析报告，说明配置成功

---

## 🐛 常见问题

### Q1: 提示 "API Key 未配置" 或 "AI分析器未就绪"
**原因**: API Key 未正确设置或格式错误

**解决**:
1. 检查 Key 格式（应包含点号分隔的两部分）
2. 确保没有多余的空格或引号
3. 重启 PowerShell 或看板进程

---

### Q2: 提示 "API 调用失败" 或 "401 Unauthorized"
**原因**: API Key 无效或已过期

**解决**:
1. 在智谱AI平台检查 Key 状态
2. 确认账户额度是否充足
3. 重新生成新的 API Key

---

### Q3: 看板启动后仍提示 "未安装AI SDK"
**原因**: zhipuai 包未正确安装

**解决**:
```powershell
& ".\.venv311\Scripts\python.exe" -m pip install --upgrade zhipuai
```

---

### Q4: 设置环境变量后仍无效
**原因**: 环境变量未被正确加载

**解决**:
```powershell
# 完全重启 PowerShell 窗口
# 或使用临时环境变量方式：
$env:ZHIPU_API_KEY = "your_key"; & ".\.venv311\Scripts\python.exe" "智能门店看板_Dash版.py"
```

---

## 🚀 快速开始（完整流程）

```powershell
# 1. 设置 API Key（替换为实际 Key）
$env:ZHIPU_API_KEY = "xxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx"

# 2. 启动看板
.\启动看板_Python311.ps1

# 3. 打开浏览器
# 访问 http://localhost:8050

# 4. 测试 AI 功能
# 进入 Tab 4 → 点击"生成 AI 洞察"
```

---

## 📊 功能清单

配置 API Key 后可用的功能：

### ✅ 阶段1 - GLM-4.6 基础分析
- Tab 4: 商品组合优化 AI 洞察
- 基于 Few-Shot 示例库的智能分析
- CoT 思维链 6 步推理
- 数据验证规则自动注入

### ⚠️ 阶段2 - PandasAI（需额外配置）
- 🤖 AI 智能助手 Tab
- 自然语言数据查询
- 查询模板快速分析
- 查询历史管理

**注意**: PandasAI 功能依赖 GLM-4.6 API，配置 Key 后自动启用。

### ❌ 阶段3 - RAG 知识库（暂不可用）
- 原因: Torch DLL 依赖缺失
- 解决: 安装 Visual C++ Redistributable

---

## 💡 最佳实践

### 开发环境
- 使用 `.env` 文件管理 Key
- 将 `.env` 添加到 `.gitignore`
- 定期轮换 API Key

### 生产环境
- 使用系统环境变量
- 设置 Key 访问权限
- 监控 API 调用额度

### 安全建议
- ❌ 不要将 Key 提交到版本控制
- ❌ 不要在公开代码中硬编码 Key
- ✅ 使用环境变量或密钥管理服务
- ✅ 定期检查 Key 使用情况

---

## 📞 支持

### 智谱AI官方支持
- 文档: https://open.bigmodel.cn/dev/api
- 社区: https://open.bigmodel.cn/forum

### 本地支持
- 查看日志: 看板启动时的终端输出
- 调试模式: 在 `ai_analyzer.py` 中启用 debug 日志
- 问题报告: 记录完整错误信息与环境配置

---

## ✅ 配置完成检查清单

- [ ] 已获取智谱AI API Key
- [ ] 已设置环境变量或修改配置文件
- [ ] 看板启动日志显示 "✅ AI分析器就绪"
- [ ] 可在 Tab 4 成功生成 AI 洞察
- [ ] 🤖 AI 智能助手 Tab 可见且可用

完成以上检查后，所有 AI 功能（阶段1/阶段2）即可正常使用！
