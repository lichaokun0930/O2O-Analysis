# 🏪 智能门店经营看板 - Dash版

## 📖 简介

这是智能门店经营看板的Dash版本，解决了Streamlit版本的页面跳转问题，提供更流畅的交互体验。

## 🚀 快速启动

### 方式1：双击启动脚本（推荐）

**Windows用户（批处理）：**
1. 双击 `启动看板.bat`
2. 等待看到 "Dash is running on http://0.0.0.0:8050/"
3. 打开浏览器访问 http://localhost:8050

**Windows用户（PowerShell）：**
1. 右键 `启动看板.ps1` → "使用PowerShell运行"
2. 如果提示"无法运行脚本"，先执行：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. 等待应用启动完成
4. 打开浏览器访问 http://localhost:8050

### 方式2：命令行启动

```bash
# 1. 切换到项目目录
cd "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"

# 2. 运行应用
python "智能门店看板_Dash版.py"

# 3. 访问 http://localhost:8050
```

### 方式3：VSCode中启动

1. 在VSCode中打开 `智能门店看板_Dash版.py`
2. 按 `F5` 或点击右上角的"运行"按钮
3. 等待终端显示 "Dash is running on http://0.0.0.0:8050/"
4. 打开浏览器访问 http://localhost:8050

## ✅ 验证启动成功

### 检查端口是否监听

```powershell
netstat -ano | findstr :8050
```

应该看到类似输出：
```
TCP    0.0.0.0:8050           0.0.0.0:0              LISTENING       12345
```

### 检查网络连接

```powershell
Test-NetConnection -ComputerName localhost -Port 8050
```

`TcpTestSucceeded` 应该显示 `True`

## 📋 功能模块

### Tab 4.1: 📉 销量下滑诊断
- ⏰ 分时段下滑分布
- 🎭 分场景下滑分布  
- 💸 收入损失TOP10
- 📊 周期销量对比
- 📉 分类收入损失排名
- 🔻 各分类下滑TOP商品
- 💰 四维散点分析
- 💵 商品价格分布
- 🌳 分类树状图
- 🔥 时段×场景热力图

### Tab 4.2: 💰 客单价归因分析
- 客单价变化汇总
- 下滑商品分析
- 上涨商品分析

## 🔧 故障排除

### 问题1：应用无法启动

**症状**：双击脚本后窗口立即关闭

**解决方案**：
1. 使用命令行启动查看错误信息
2. 检查Python是否正确安装：`python --version`
3. 检查依赖是否安装：`pip list | findstr dash`

### 问题2：端口被占用

**症状**：提示 "Address already in use"

**解决方案**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8050

# 结束进程（将PID替换为实际进程ID）
taskkill /F /PID <PID>
```

### 问题3：浏览器无法访问

**症状**：浏览器显示"无法访问此网站"

**检查清单**：
1. ✅ 确认应用已启动（终端显示 "Dash is running"）
2. ✅ 确认端口8050在监听（使用 `netstat` 命令）
3. ✅ 尝试使用不同地址：
   - http://localhost:8050
   - http://127.0.0.1:8050
4. ✅ 检查防火墙是否阻止
5. ✅ 尝试强制刷新浏览器（Ctrl+F5）

### 问题4：emoji显示乱码

**症状**：控制台显示emoji为乱码或出错

**解决方案**：
已在代码中自动处理。如仍有问题，请确保：
1. PowerShell编码设置为UTF-8
2. 使用提供的启动脚本

## 📊 数据要求

应用会自动加载以下目录的数据：
- `实际数据/`
- `门店数据/`

Excel文件应包含以下字段：
- 订单ID
- 商品名称
- 商品实售价
- 数量
- 下单时间
- 场景
- 时段
- 一级分类名
- 三级分类名

## 📝 技术栈

- **框架**: Dash (基于Flask + Plotly)
- **UI组件**: dash-bootstrap-components
- **图表**: Plotly Graph Objects & Express
- **数据处理**: pandas, numpy
- **诊断引擎**: 问题诊断引擎.py

## 🔗 相关链接

- **Streamlit版本**: `智能门店经营看板_可视化.py`
- **问题诊断引擎**: `问题诊断引擎.py`
- **数据处理器**: `真实数据处理器.py`

## 📞 支持

如遇问题，请检查：
1. 终端的错误输出
2. 浏览器控制台（F12）的错误信息
3. 确保数据文件格式正确

## 📄 许可证

内部使用项目

---

**最后更新**: 2025-10-17
**版本**: v1.0 (完整重构版)
