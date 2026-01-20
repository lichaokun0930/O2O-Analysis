# Implementation Plan: 营销成本趋势图表

## Overview

新增营销成本趋势图表，通过百分比堆叠面积图展示各营销类型占比随时间的变化趋势，与现有的营销成本结构桑基图形成互补。

## Tasks

- [x] 1. 后端API实现
  - [x] 1.1 新增营销成本趋势API端点
    - 在 `backend/app/api/v1/orders.py` 中添加 `/marketing-trend` 端点
    - 实现按日期分组聚合8个营销字段的逻辑
    - 返回dates、series、totals三个数组
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 编写API属性测试
    - **Property 2: 订单级字段聚合正确性**
    - **Property 3: 日期过滤正确性**
    - **Validates: Requirements 1.2, 1.4**

- [x] 2. 前端类型定义和API客户端
  - [x] 2.1 添加类型定义
    - 在 `frontend-react/src/types/index.ts` 中添加 `MarketingTrendData` 类型
    - _Requirements: 1.3_

  - [x] 2.2 添加API调用方法
    - 在 `frontend-react/src/api/orders.ts` 中添加 `getMarketingTrend` 方法
    - _Requirements: 4.1, 4.2_

- [x] 3. 前端组件实现
  - [x] 3.1 创建营销成本趋势图表组件
    - 创建 `frontend-react/src/components/charts/MarketingTrendChart.tsx`
    - 实现百分比堆叠面积图渲染
    - 复用桑基图的颜色配置
    - 实现视图切换功能（绝对值/百分比）
    - 过滤全零营销类型
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 5.2, 5.3, 5.4_

  - [x] 3.2 编写前端属性测试
    - **Property 4: 零值类型过滤**
    - **Property 5: 百分比计算正确性**
    - **Property 6: 绝对值视图数据一致性**
    - **Validates: Requirements 2.6, 3.2, 3.3**

- [x] 4. 数据联动集成
  - [x] 4.1 更新App.tsx集成趋势图表
    - 添加趋势数据状态和获取逻辑
    - 实现全局日期筛选和门店切换联动
    - 将趋势图表放置在桑基图旁边或下方
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1_

- [x] 5. Checkpoint - 功能验证
  - 确保所有测试通过
  - 验证趋势图表正确显示各营销类型占比变化
  - 验证视图切换功能正常
  - 验证日期筛选和门店切换联动正常
  - 如有问题请询问用户

## Notes

- 所有任务均为必需，包括测试任务
- 复用现有的 `useChart` hook 和颜色配置
- 与桑基图使用相同的8个营销字段定义
- 默认显示百分比视图，支持切换到绝对值视图

