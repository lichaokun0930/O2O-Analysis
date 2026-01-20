# Requirements Document

## Introduction

本功能为O2O订单数据看板新增"分距离订单诊断"图表组件，用于分析不同配送距离区间的订单表现。该组件将与现有的"配送溢价雷达"(DeliveryHeatmap)形成联动，当雷达扫描到特定距离区间时，高亮显示对应的柱状图。

## Glossary

- **Distance_Analysis_Chart**: 分距离订单诊断图表组件，展示不同配送距离区间的订单数、利润等指标
- **Distance_Band**: 配送距离区间，共7个区间：0-1km, 1-2km, 2-3km, 3-4km, 4-5km, 5-6km, 6km+
- **Delivery_Heatmap**: 配送溢价雷达组件，现有组件，需要添加联动回调
- **Radar_Scan**: 雷达扫描动画，6秒一圈，扫描到的区域会高亮显示
- **Optimal_Distance**: 最优配送距离，利润率最高的距离区间
- **Backend_API**: 后端API接口，提供距离分析数据

## Requirements

### Requirement 1: 后端API - 距离分析数据接口

**User Story:** As a frontend developer, I want to fetch distance-based order analysis data from the backend, so that I can render the distance analysis chart.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/orders/distance-analysis`, THE Backend_API SHALL return distance band metrics grouped by 7 distance ranges
2. WHEN the request includes `store_name` parameter, THE Backend_API SHALL filter data by the specified store
3. WHEN the request includes `channel` parameter, THE Backend_API SHALL filter data by the specified channel
4. WHEN the request includes `target_date` parameter, THE Backend_API SHALL filter data by the specified date
5. WHEN the request includes `start_date` and `end_date` parameters, THE Backend_API SHALL filter data by the date range
6. THE Backend_API SHALL return for each Distance_Band: order_count, revenue, profit, profit_rate, delivery_cost, delivery_cost_rate, avg_order_value
7. THE Backend_API SHALL return summary statistics including total_orders, avg_distance, and optimal_distance
8. IF no orders exist for a Distance_Band, THE Backend_API SHALL return zero values for that band

### Requirement 2: 前端类型定义

**User Story:** As a frontend developer, I want TypeScript type definitions for distance analysis data, so that I can ensure type safety in the codebase.

#### Acceptance Criteria

1. THE System SHALL define `DistanceBandMetric` interface with fields: band_label, min_distance, max_distance, order_count, revenue, profit, profit_rate, delivery_cost, delivery_cost_rate, avg_order_value
2. THE System SHALL define `DistanceAnalysisData` interface containing distance_bands array and summary object
3. THE System SHALL export these types from the types module

### Requirement 3: 前端API函数

**User Story:** As a frontend developer, I want an API function to fetch distance analysis data, so that I can call it from React components.

#### Acceptance Criteria

1. THE System SHALL provide `getDistanceAnalysis()` function in the orders API module
2. WHEN called with optional parameters (store_name, channel, target_date, start_date, end_date), THE function SHALL pass them to the backend
3. THE function SHALL return a Promise with typed response data

### Requirement 4: 分距离订单诊断图表组件

**User Story:** As a business analyst, I want to see order performance across different delivery distance ranges, so that I can identify optimal delivery zones and cost issues.

#### Acceptance Criteria

1. THE Distance_Analysis_Chart SHALL display a bar chart showing order count for each of the 7 distance bands
2. THE Distance_Analysis_Chart SHALL display a line chart overlay showing profit for each distance band
3. THE Distance_Analysis_Chart SHALL use the same visual style as CostEfficiencyChart (分时段诊断)
4. WHEN hovering over a bar, THE Distance_Analysis_Chart SHALL show a tooltip with all metrics for that distance band
5. THE Distance_Analysis_Chart SHALL highlight the Optimal_Distance band with a distinct visual indicator
6. THE Distance_Analysis_Chart SHALL display a loading state while fetching data
7. THE Distance_Analysis_Chart SHALL display "暂无数据" when no data is available
8. WHEN `selectedDate` prop is provided, THE Distance_Analysis_Chart SHALL filter data by that date
9. THE Distance_Analysis_Chart SHALL support both dark and light themes

### Requirement 5: 配送溢价雷达联动回调

**User Story:** As a user, I want the distance analysis chart to highlight the corresponding distance band when the radar scans that area, so that I can see the correlation between the two visualizations.

#### Acceptance Criteria

1. THE Delivery_Heatmap SHALL accept an optional `onDistanceHighlight` callback prop
2. WHEN the radar scan animation passes through a distance range, THE Delivery_Heatmap SHALL call `onDistanceHighlight` with the current distance value (0-8km)
3. THE callback SHALL be called at 60fps during the animation to provide smooth updates
4. WHEN the component unmounts, THE Delivery_Heatmap SHALL stop calling the callback

### Requirement 6: 图表联动高亮效果

**User Story:** As a user, I want to see the distance analysis chart highlight the bar corresponding to the radar's current scan position, so that I can visually correlate the two charts.

#### Acceptance Criteria

1. THE Distance_Analysis_Chart SHALL accept an optional `highlightDistance` prop (number in km)
2. WHEN `highlightDistance` falls within a Distance_Band range, THE Distance_Analysis_Chart SHALL highlight that bar with increased opacity and glow effect
3. WHEN `highlightDistance` is null or undefined, THE Distance_Analysis_Chart SHALL show all bars with normal styling
4. THE highlight transition SHALL be smooth (CSS transition or ECharts animation)

### Requirement 7: 布局集成

**User Story:** As a user, I want to see the distance analysis chart positioned next to the hourly analysis chart, so that I can compare time-based and distance-based diagnostics.

#### Acceptance Criteria

1. THE Distance_Analysis_Chart SHALL be placed in the same row as CostEfficiencyChart (分时段诊断)
2. THE layout SHALL be: CostEfficiencyChart (left 50%) + Distance_Analysis_Chart (right 50%)
3. WHEN on mobile screens (< 1024px), THE charts SHALL stack vertically
4. THE App component SHALL manage the linkage state between Delivery_Heatmap and Distance_Analysis_Chart
