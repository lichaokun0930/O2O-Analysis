# B电脑克隆后必须文件清单

## 核心程序文件 (✅ 已包含在Git中)
1. **智能门店看板_Dash版.py** - 主程序
2. **真实数据处理器.py** - 数据处理器
3. **订单数据处理器.py** - 订单处理
4. **redis_cache_manager.py** - Redis缓存管理
5. **ai_analyzer.py** - AI分析器
6. **ai_business_context.py** - 业务上下文
7. **商品场景智能打标引擎.py** - 场景打标
8. **scene_inference.py** - 场景推断
9. **loading_components.py** - 加载组件
10. **component_styles.py** - 组件样式
11. **echarts_factory.py** - ECharts工厂
12. **echarts_responsive_utils.py** - ECharts响应式
13. **tab5_extended_renders.py** - Tab5渲染

## 配置文件 (✅ 已包含)
1. **requirements.txt** - Python依赖
2. **.env.example** - 环境变量模板
3. **.gitignore** - Git忽略规则

## 启动脚本 (✅ 已包含)
1. **启动看板.ps1** - PowerShell启动
2. **启动看板.bat** - 批处理启动
3. **启动数据库.ps1** - 数据库启动

## 数据库文件 (✅ 已包含)
1. **数据库导出/o2o_dashboard_full_*.sql** - 数据库导出文件
2. **migrations/pg_ddl_*.sql** - 数据库迁移脚本

## 文档文件 (✅ 已包含)
1. **快速启动指南.md**
2. **快速开始指南.md**
3. **依赖和环境说明.md**
4. **数据字段映射规范.md**
5. **【权威】业务逻辑与数据字典完整手册.md**

## ⚠️ 不会推送到Git的文件 (需要手动准备)
以下文件被.gitignore排除,需要在B电脑上单独准备:

### 数据文件 (不推送)
- ❌ **实际数据/*.xlsx** - Excel数据文件
- ❌ **门店数据/*.csv** - CSV数据文件
- 👉 **解决方案**: 通过其他方式传输(网盘/U盘/内网)

### 环境配置 (不推送)
- ❌ **.env** - 包含敏感信息(API密钥等)
- 👉 **解决方案**: 复制.env.example为.env并填入配置

### 数据库数据 (不推送)
- ❌ **智能模型仓库/*.joblib** - 训练好的模型
- ❌ **学习数据仓库/*** - 学习数据
- 👉 **解决方案**: 
  1. 从数据库导出文件恢复 (推荐)
  2. 或重新训练模型

### Python环境 (不推送)
- ❌ **venv/** - 虚拟环境
- ❌ **__pycache__/** - 编译缓存
- 👉 **解决方案**: 使用requirements.txt重新安装依赖

## B电脑克隆后的步骤

### 1. 克隆仓库
```bash
git clone https://github.com/lichaokun0930/O2O-Analysis.git
cd "O2O-Analysis/O2O数据分析/测算模型"
```

### 2. 安装Python依赖
```powershell
# 创建虚拟环境 (推荐)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 3. 准备环境配置
```powershell
# 复制环境变量模板
Copy-Item .env.example .env

# 编辑.env文件,填入必要配置:
# - ZHIPU_API_KEY (智谱AI密钥)
# - PostgreSQL连接信息
# - Redis连接信息 (如果使用)
```

### 4. 准备数据文件
**方式A: 使用Excel数据** (如果没有数据库)
```powershell
# 创建数据目录
New-Item -ItemType Directory -Path "实际数据" -Force

# 将Excel文件放入 实际数据/ 目录
# 看板会自动读取Excel文件
```

**方式B: 恢复数据库** (推荐)
```powershell
# 1. 安装PostgreSQL
# 2. 创建数据库
createdb o2o_dashboard

# 3. 导入数据
psql -U postgres -d o2o_dashboard -f "数据库导出/o2o_dashboard_full_*.sql"
```

### 5. 启动看板
```powershell
# 方式1: PowerShell脚本 (推荐)
.\启动看板.ps1

# 方式2: 直接运行Python
python "智能门店看板_Dash版.py"

# 方式3: 批处理文件
.\启动看板.bat
```

### 6. 访问看板
- 本机访问: http://localhost:8050
- 局域网访问: http://<B电脑IP>:8050

## 核心文件验证清单

在B电脑上克隆后,检查以下文件是否存在:

### 必须存在 (推送到Git)
- [ ] 智能门店看板_Dash版.py
- [ ] 真实数据处理器.py
- [ ] requirements.txt
- [ ] 启动看板.ps1
- [ ] 快速启动指南.md
- [ ] .gitignore

### 需要手动准备 (未推送)
- [ ] .env (复制.env.example)
- [ ] 实际数据/*.xlsx (数据文件)
- [ ] PostgreSQL数据库 (如果使用)

## 常见问题

### Q1: 克隆后运行报错 "ModuleNotFoundError"
**A**: 需要安装依赖
```powershell
pip install -r requirements.txt
```

### Q2: 运行报错 "找不到数据文件"
**A**: 需要准备数据文件
- 将Excel文件放入 `实际数据/` 目录
- 或配置数据库连接

### Q3: 看板启动但没有数据
**A**: 检查数据源
- 确认Excel文件存在且格式正确
- 或检查数据库连接是否正常

### Q4: AI分析功能不可用
**A**: 需要配置API密钥
- 编辑.env文件
- 设置 `ZHIPU_API_KEY=your_api_key`

## 文件大小说明

Git仓库包含:
- 核心代码文件: ~500KB
- 文档文件: ~200KB
- 脚本文件: ~100KB
- **总计**: ~800KB (不含数据文件)

需要单独传输的文件:
- Excel数据文件: ~10-50MB (视数据量)
- 数据库导出文件: ~20-100MB (如果使用)
- **总计**: ~30-150MB

## 推送前检查

以下关键文件已包含在本次推送:
✅ 主程序 (智能门店看板_Dash版.py)
✅ 数据处理器 (真实数据处理器.py, 订单数据处理器.py)
✅ 智能模块 (AI分析器, 场景打标引擎)
✅ UI组件 (ECharts工厂, 样式库, 加载组件)
✅ 配置文件 (requirements.txt, .env.example)
✅ 启动脚本 (PowerShell + Batch)
✅ 文档 (使用指南, 业务逻辑手册)
✅ .gitignore (排除数据和敏感文件)

## 推送后验证

推送成功后,在Github上检查:
1. 文件数量是否正确
2. 核心文件是否存在
3. .gitignore是否生效 (数据文件未推送)
4. README或文档是否完整
