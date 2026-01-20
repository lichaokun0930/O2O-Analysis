# Requirements Document

## Introduction

新增营销成本趋势图表，与现有的营销成本结构桑基图形成互补。桑基图展示"渠道→营销类型"的资金流向（静态结构），趋势图展示"时间→营销类型占比"的变化（动态趋势）。通过百分比堆叠面积图，直观呈现各营销类型占比随时间的变化趋势。

## Glossary

- **Marketing_Trend_Chart**: 营销成本趋势图表组件，展示各营销类型占比随时间的变化
- **Stacked_Area_Chart**: 百分比堆叠面积图，Y轴为0-100%，展示各类型占比
- **Marketing_Cost_Type**: 营销成本类型，包含8个字段（配送费减免、满减金额等）
- **Marketing_Trend_API**: 后端营销成本趋势数据接口
- **Granularity**: 时间粒度，支持按日或按周聚合

## Requirements

### Requirement 1: 营销成本趋势数据聚合

**User Story:** As a 门店运营人员, I want 按日期聚合各营销类型的成本数据, so that 我能分析营销投入的时间变化趋势。

#### Acceptance Criteria

1. THE Marketing_Trend_API SHALL 返回按日期分组的8个营销字段数据
2. WHEN 聚合营销字段时, THE Marketing_Trend_API SHALL 对订单级字段使用`.first()`避免重复计算
3. THE Marketing_Trend_API SHALL 返回以下数据结构：
   - dates: 日期数组
   - series: 各营销类型的每日金额数组
   - totals: 每日总营销成本数组
4. THE Marketing_Trend_API SHALL 支持按门店名称和日期范围过滤数据
5. WHEN 某日期某营销类型金额为0时, THE Marketing_Trend_API SHALL 返回0（不省略）

### Requirement 2: 百分比堆叠面积图渲染

**User Story:** As a 门店运营人员, I want 通过堆叠面积图查看营销成本占比趋势, so that 我能直观理解各营销类型占比的变化。

#### Acceptance Criteria

1. THE Marketing_Trend_Chart SHALL 使用百分比堆叠面积图展示数据
2. THE Marketing_Trend_Chart SHALL X轴显示日期，Y轴显示0-100%占比
3. THE Marketing_Trend_Chart SHALL 为每种营销类型分配与桑基图一致的颜色
4. WHEN 鼠标悬停时, THE Marketing_Trend_Chart SHALL 显示tooltip包含：日期、各营销类型金额和占比
5. THE Marketing_Trend_Chart SHALL 支持深色和浅色主题切换
6. WHEN 某营销类型在整个时间范围内金额都为0时, THE Marketing_Trend_Chart SHALL 不显示该类型

### Requirement 3: 视图切换功能

**User Story:** As a 门店运营人员, I want 切换绝对值和百分比视图, so that 我能从不同角度分析营销成本。

#### Acceptance Criteria

1. THE Marketing_Trend_Chart SHALL 提供视图切换按钮（绝对值/百分比）
2. WHEN 切换到绝对值视图时, THE Marketing_Trend_Chart SHALL Y轴显示金额，面积高度反映实际金额
3. WHEN 切换到百分比视图时, THE Marketing_Trend_Chart SHALL Y轴显示0-100%，面积高度反映占比
4. THE Marketing_Trend_Chart SHALL 默认显示百分比视图

### Requirement 4: 数据过滤与联动

**User Story:** As a 门店运营人员, I want 营销趋势图表响应全局日期筛选, so that 我能分析不同时间段的营销变化。

#### Acceptance Criteria

1. WHEN 全局日期范围变化时, THE Marketing_Trend_Chart SHALL 重新请求并渲染对应时间段的数据
2. WHEN 门店选择变化时, THE Marketing_Trend_Chart SHALL 重新请求并渲染对应门店的数据
3. IF 请求数据失败, THEN THE Marketing_Trend_Chart SHALL 显示错误提示并保持上次有效数据
4. WHILE 数据加载中, THE Marketing_Trend_Chart SHALL 显示加载状态

### Requirement 5: 图表布局集成

**User Story:** As a 开发者, I want 将营销趋势图表集成到看板中, so that 与桑基图形成互补展示。

#### Acceptance Criteria

1. THE System SHALL 将营销趋势图表放置在营销成本结构桑基图旁边或下方
2. THE Marketing_Trend_Chart SHALL 标题为"营销成本趋势"
3. THE Marketing_Trend_Chart SHALL 副标题为"MARKETING COST TREND: TYPE RATIO OVER TIME"
4. THE Marketing_Trend_Chart SHALL 与桑基图使用相同的营销类型颜色配置

