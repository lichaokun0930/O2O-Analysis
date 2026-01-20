# Implementation Plan: 分距离订单诊断 (Distance-based Order Diagnosis)

## Overview

本实现计划将"分距离订单诊断"功能分解为可执行的编码任务，按照后端API → 前端类型 → 前端API → 图表组件 → 联动集成的顺序实现。

## Tasks

- [x] 1. 实现后端距离分析API
  - [x] 1.1 在 `orders.py` 中添加 `get_distance_analysis` 端点
    - 定义7个距离区间常量 DISTANCE_BANDS
    - 实现距离区间分组逻辑
    - 计算每个区间的 order_count, revenue, profit, profit_rate, delivery_cost, delivery_cost_rate, avg_order_value
    - 计算 summary 统计（total_orders, avg_distance, optimal_distance）
    - 支持 store_name, channel, target_date, start_date, end_date 筛选参数
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 1.2 编写后端API属性测试
    - **Property 1: Distance Band Grouping Completeness**
    - **Property 2: API Filtering Correctness**
    - **Property 3: Metrics Calculation Consistency**
    - **Property 5: Optimal Distance Identification**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**

- [x] 2. Checkpoint - 验证后端API
  - 启动后端服务，使用 curl 或 Postman 测试 `/api/v1/orders/distance-analysis` 端点
  - 确保返回正确的数据结构和计算结果
  - 如有问题请告知

- [x] 3. 添加前端类型定义
  - [x] 3.1 在 `types/index.ts` 中添加 `DistanceBandMetric` 接口
    - 包含字段：band_label, min_distance, max_distance, order_count, revenue, profit, profit_rate, delivery_cost, delivery_cost_rate, avg_order_value
    - _Requirements: 2.1_

  - [x] 3.2 在 `types/index.ts` 中添加 `DistanceAnalysisData` 接口
    - 包含 distance_bands 数组和 summary 对象
    - _Requirements: 2.2, 2.3_

- [x] 4. 添加前端API函数
  - [x] 4.1 在 `api/orders.ts` 中添加 `getDistanceAnalysis` 函数
    - 接受可选参数：store_name, channel, target_date, start_date, end_date
    - 返回 Promise<{ success: boolean; data: DistanceAnalysisData }>
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 5. 创建 DistanceAnalysisChart 组件
  - [x] 5.1 创建 `components/charts/DistanceAnalysisChart.tsx` 基础结构
    - 定义 Props 接口：storeName, channel, theme, selectedDate, highlightDistance
    - 实现数据获取逻辑（useEffect + API 调用）
    - 实现 loading 和 empty 状态
    - _Requirements: 4.6, 4.7_

  - [x] 5.2 实现 ECharts 图表配置
    - 配置 xAxis（7个距离区间标签）
    - 配置双 yAxis（左侧订单数，右侧利润金额）
    - 实现柱状图 series（订单数，紫色渐变）
    - 实现折线图 series（利润，绿色/红色）
    - 配置 tooltip 显示所有指标
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 5.3 实现最优距离区间高亮
    - 使用 markArea 或特殊样式标记 optimal_distance 区间
    - _Requirements: 4.5_

  - [x] 5.4 实现 highlightDistance 联动高亮
    - 根据 highlightDistance prop 计算对应的距离区间
    - 高亮对应的柱子（增加透明度和发光效果）
    - 实现平滑过渡动画
    - _Requirements: 6.2, 6.3, 6.4_

  - [x] 5.5 实现主题支持
    - 根据 theme prop 切换深色/浅色样式
    - _Requirements: 4.9_

  - [x] 5.6 编写前端组件属性测试
    - **Property 4: Highlight Distance Mapping**
    - **Validates: Requirements 6.2**

- [x] 6. Checkpoint - 验证图表组件
  - 在 App.tsx 中临时添加 DistanceAnalysisChart 组件
  - 验证图表渲染、数据加载、主题切换
  - 如有问题请告知

- [x] 7. 修改 DeliveryHeatmap 添加联动回调
  - [x] 7.1 添加 `onDistanceHighlight` 可选 prop
    - 更新 Props 接口
    - _Requirements: 5.1_

  - [x] 7.2 在雷达扫描动画中调用回调
    - 在 animate 函数中计算当前扫描位置对应的距离值（0-8km）
    - 调用 onDistanceHighlight 回调
    - _Requirements: 5.2, 5.3_

  - [x] 7.3 实现组件卸载时停止回调
    - 在 useEffect cleanup 中取消动画帧
    - _Requirements: 5.4_

- [x] 8. 集成到 App.tsx
  - [x] 8.1 添加联动状态管理
    - 添加 highlightDistance state
    - 创建 handleDistanceHighlight 回调函数
    - _Requirements: 7.4_

  - [x] 8.2 更新布局
    - 将 CostEfficiencyChart 和 DistanceAnalysisChart 放在同一行
    - 配置响应式布局（桌面端左右各50%，移动端垂直堆叠）
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 8.3 连接联动
    - 将 handleDistanceHighlight 传递给 DeliveryHeatmap
    - 将 highlightDistance 传递给 DistanceAnalysisChart
    - _Requirements: 7.4_

- [x] 9. 导出组件
  - [x] 9.1 在 `components/charts/index.ts` 中导出 DistanceAnalysisChart
    - _Requirements: 2.3_

- [x] 10. Final Checkpoint - 完整功能验证
  - 验证完整的联动流程：雷达扫描 → 距离图表高亮
  - 验证日期联动：销售趋势图选中日期 → 距离图表数据更新
  - 验证筛选功能：门店/渠道筛选 → 数据正确过滤
  - 验证响应式布局
  - 如有问题请告知

## Notes

- All tasks are required, including property-based tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- The implementation follows the existing code style of CostEfficiencyChart
