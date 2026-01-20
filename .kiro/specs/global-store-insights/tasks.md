# Tasks - 全局门店洞察分析引擎

## Task 1: 后端洞察分析引擎核心实现

### Description
在 `store_comparison.py` 中实现全局洞察分析引擎的核心逻辑，包括统计分析、门店分群、异常检测、归因分析等功能。

### Requirements Addressed
- Requirement 1: 整体概况分析
- Requirement 2: 门店分群分析
- Requirement 3: 异常门店检测
- Requirement 4: 头尾对比分析
- Requirement 5: 利润率归因分析
- Requirement 9: 后端API支持

### Acceptance Criteria
- [x] 实现 `InsightsEngine` 类，包含所有分析方法
- [x] 实现 `calculate_statistics()` 计算描述性统计
- [x] 实现 `cluster_stores()` 门店分群
- [x] 实现 `detect_anomalies()` 异常检测
- [x] 实现 `compare_head_tail()` 头尾对比
- [x] 实现 `analyze_attribution()` 归因分析
- [x] 实现 `generate_report_text()` 文字报告生成

### Files to Modify
- `backend/app/api/v1/store_comparison.py`

### Estimated Effort: Large
### Status: ✅ COMPLETED

---

## Task 2: 后端趋势分析和策略建议实现

### Description
实现趋势分析模块和策略建议生成模块，基于环比数据分析门店增长/下滑趋势，并生成可执行的策略建议。

### Requirements Addressed
- Requirement 6: 趋势变化分析
- Requirement 7: 策略建议生成

### Acceptance Criteria
- [x] 实现 `analyze_trends()` 趋势分析方法
- [x] 实现 `generate_recommendations()` 策略建议生成
- [x] 策略建议按优先级分类（紧急/重要/一般）
- [x] 每条建议包含具体行动项

### Files to Modify
- `backend/app/api/v1/store_comparison.py`

### Estimated Effort: Medium
### Status: ✅ COMPLETED

---

## Task 3: 后端 API 端点实现

### Description
创建 `/api/v1/store-comparison/global-insights` API 端点，整合所有分析模块，返回完整的洞察报告。

### Requirements Addressed
- Requirement 9: 后端API支持

### Acceptance Criteria
- [x] 创建 `get_global_insights()` API 端点
- [x] 支持日期范围参数筛选
- [x] 支持渠道参数筛选
- [x] 返回结构化 JSON 数据
- [ ] 响应时间 < 5 秒 (待测试)
- [x] 实现缓存机制 (复用现有缓存)

### Files to Modify
- `backend/app/api/v1/store_comparison.py`

### Estimated Effort: Medium
### Status: ✅ COMPLETED

---

## Task 4: 前端类型定义

### Description
在 `types/index.ts` 中添加全局洞察相关的 TypeScript 类型定义。

### Requirements Addressed
- Requirement 8: 洞察报告展示

### Acceptance Criteria
- [x] 定义 `GlobalInsightsData` 接口
- [x] 定义 `OverviewInsight` 接口
- [x] 定义 `ClusteringInsight` 接口
- [x] 定义 `AnomalyInsight` 接口
- [x] 定义 `HeadTailInsight` 接口
- [x] 定义 `AttributionInsight` 接口
- [x] 定义 `TrendInsight` 接口
- [x] 定义 `RecommendationInsight` 接口

### Files to Modify
- `frontend-react/src/types/index.ts`

### Estimated Effort: Small
### Status: ✅ COMPLETED

---

## Task 5: 前端 API 调用方法

### Description
在 `storeComparison.ts` 中添加获取全局洞察数据的 API 调用方法。

### Requirements Addressed
- Requirement 8: 洞察报告展示

### Acceptance Criteria
- [x] 实现 `getGlobalInsights()` API 方法
- [x] 支持日期范围参数
- [x] 支持渠道参数
- [x] 正确处理错误响应

### Files to Modify
- `frontend-react/src/api/storeComparison.ts`

### Estimated Effort: Small
### Status: ✅ COMPLETED

---

## Task 6: GlobalInsightsPanel 主组件实现

### Description
创建 `GlobalInsightsPanel.tsx` 组件，作为全局洞察报告的主容器，管理各分析模块的展示和折叠状态。

### Requirements Addressed
- Requirement 8: 洞察报告展示

### Acceptance Criteria
- [x] 创建 `GlobalInsightsPanel.tsx` 组件
- [x] 实现数据加载和状态管理
- [x] 实现加载状态和错误处理
- [x] 实现各模块的折叠/展开功能
- [x] 显示报告生成时间

### Files to Create
- `frontend-react/src/components/GlobalInsightsPanel.tsx`

### Estimated Effort: Medium
### Status: ✅ COMPLETED

---

## Task 7: 洞察报告各分析模块组件

### Description
实现各个分析模块的展示组件，包括整体概况、门店分群、异常检测、头尾对比、归因分析、趋势分析、策略建议。

### Requirements Addressed
- Requirement 8: 洞察报告展示

### Acceptance Criteria
- [x] 实现 OverviewSection 组件 (内嵌在主组件)
- [x] 实现 ClusteringSection 组件 (内嵌在主组件)
- [x] 实现 AnomalySection 组件 (内嵌在主组件)
- [x] 实现 ComparisonSection 组件 (内嵌在主组件)
- [x] 实现 AttributionSection 组件 (内嵌在主组件)
- [x] 实现 TrendSection 组件 (内嵌在主组件)
- [x] 实现 RecommendSection 组件 (内嵌在主组件)
- [x] 关键数据使用醒目样式标注
- [x] 文字报告格式清晰易读

### Files to Create
- `frontend-react/src/components/GlobalInsightsPanel.tsx` (已包含所有子组件)

### Estimated Effort: Large
### Status: ✅ COMPLETED

---

## Task 8: 集成到 StoreComparisonView

### Description
将 `GlobalInsightsPanel` 组件集成到 `StoreComparisonView.tsx` 中，添加"全局洞察"按钮和面板展示。

### Requirements Addressed
- Requirement 8: 洞察报告展示

### Acceptance Criteria
- [x] 添加"全局洞察"按钮
- [x] 点击按钮展示/隐藏洞察面板
- [x] 洞察面板与现有筛选条件联动
- [x] 数据变化时自动刷新洞察报告

### Files to Modify
- `frontend-react/src/views/StoreComparisonView.tsx`

### Estimated Effort: Small
### Status: ✅ COMPLETED

---

## Task 9: 测试和优化

### Description
对全局洞察分析引擎进行测试和性能优化。

### Requirements Addressed
- All requirements

### Acceptance Criteria
- [ ] 后端 API 单元测试
- [ ] 前端组件渲染测试
- [ ] 性能测试（响应时间 < 5 秒）
- [ ] 边界情况处理（空数据、单门店等）

### Files to Create
- `backend/tests/test_global_insights.py`

### Estimated Effort: Medium
### Status: 🔄 PENDING (可选)

---

## Task 10: 门店健康度评分实现

### Description
实现门店健康度评分功能，基于多维度指标计算综合健康度分数（0-100分）。

### Requirements Addressed
- Requirement 9: 门店健康度评分

### Acceptance Criteria
- [x] 实现 `calculate_health_scores()` 方法
- [x] 综合利润率(40%)、订单量(20%)、营销成本率(20%)、配送成本率(20%)计算
- [x] 展示健康度分布（优秀/良好/一般/较差）
- [x] 列出健康度最高和最低的门店
- [x] 生成健康度分析文字总结

### Files Modified
- `backend/app/api/v1/store_comparison.py`
- `frontend-react/src/types/index.ts`
- `frontend-react/src/components/GlobalInsightsPanel.tsx`

### Estimated Effort: Medium
### Status: ✅ COMPLETED

---

## Task 11: 成本结构分析实现

### Description
实现成本结构分析功能，分析各成本项（营销/配送）的占比和分布。

### Requirements Addressed
- Requirement 11: 成本结构分析

### Acceptance Criteria
- [x] 实现 `analyze_cost_structure()` 方法
- [x] 计算营销成本、配送成本的总额和占比
- [x] 展示各成本项的均值、中位数、标准差
- [x] 识别成本占比异常的门店
- [x] 对比高绩效和低绩效门店的成本结构差异
- [x] 生成成本优化建议文字

### Files Modified
- `backend/app/api/v1/store_comparison.py`
- `frontend-react/src/types/index.ts`
- `frontend-react/src/components/GlobalInsightsPanel.tsx`

### Estimated Effort: Medium
### Status: ✅ COMPLETED

---

## Implementation Summary

✅ **已完成 10/11 个任务**

### 实现的功能：

1. **后端 InsightsEngine 类** - 完整的洞察分析引擎
   - 描述性统计分析（均值、中位数、标准差、分位数）
   - 门店分群（高/中/低绩效，基于利润率P25/P75）
   - 异常检测（Z-score、IQR、阈值方法）
   - 头尾对比分析
   - 相关性归因分析
   - 趋势变化分析
   - **门店健康度评分（0-100分）** ✨ 新增
   - **成本结构分析** ✨ 新增
   - 策略建议生成

2. **后端 API** - `/api/v1/store-comparison/global-insights`
   - 支持日期范围筛选
   - 支持渠道筛选
   - 返回结构化 JSON 数据（含健康度和成本结构）

3. **前端类型定义** - 完整的 TypeScript 接口
   - HealthScoresInsight
   - CostStructureInsight

4. **前端组件** - GlobalInsightsPanel
   - 可折叠的分析模块（9个模块）
   - 关键数据高亮显示
   - 加载/错误状态处理
   - 刷新功能

5. **集成** - 在 StoreComparisonView 中添加"全局洞察"按钮

---

## Implementation Order

1. **Task 4** (前端类型定义) - 基础依赖
2. **Task 1** (后端核心实现) - 核心功能
3. **Task 2** (趋势和建议) - 扩展功能
4. **Task 3** (API 端点) - 接口暴露
5. **Task 5** (前端 API) - 前后端连接
6. **Task 6** (主组件) - 前端框架
7. **Task 7** (子组件) - 前端细节
8. **Task 8** (集成) - 最终整合
9. **Task 9** (测试) - 质量保证

## Dependencies

```
Task 4 ──┐
         ├──> Task 5 ──> Task 6 ──> Task 7 ──> Task 8
Task 1 ──┤                                        │
         │                                        ▼
Task 2 ──┴──> Task 3 ─────────────────────────> Task 9
```
