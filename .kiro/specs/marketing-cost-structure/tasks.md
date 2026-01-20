# Implementation Plan: 营销成本结构桑基图

## Overview

将现有的"成本结构"桑基图改造为"营销成本结构"桑基图，展示各渠道在8个营销字段上的费用分布。

## Tasks

- [x] 1. 后端API实现
  - [x] 1.1 新增营销成本结构API端点
    - 在 `backend/app/api/v1/orders.py` 中添加 `/marketing-structure` 端点
    - 实现按渠道聚合8个营销字段的逻辑
    - 计算汇总指标（总营销成本、单均营销费用、营销成本率）
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4_

  - [x] 1.2 编写API单元测试
    - **Property 2: 订单级字段聚合正确性**
    - **Property 3: 总营销成本计算正确性**
    - **Validates: Requirements 1.2, 3.1, 3.2**

- [x] 2. 前端API客户端更新
  - [x] 2.1 添加营销成本结构API调用方法
    - 在 `frontend-react/src/api/orders.ts` 中添加 `getMarketingStructure` 方法
    - 定义 `MarketingStructureData` 和 `ChannelMarketingData` 类型
    - _Requirements: 4.1, 4.2_

  - [x] 2.2 更新类型定义
    - 在 `frontend-react/src/types/index.ts` 中添加营销成本相关类型
    - _Requirements: 1.3_

- [x] 3. 前端组件重构
  - [x] 3.1 重构ProfitChart为营销成本结构桑基图
    - 修改 `frontend-react/src/components/charts/ProfitChart.tsx`
    - 更新节点配置：左侧渠道节点，右侧8个营销类型节点
    - 配置8种营销类型颜色
    - 实现数据转换逻辑（transformToSankeyData）
    - 过滤零值连线
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.1, 5.3, 5.4_

  - [x] 3.2 编写桑基图数据转换测试
    - **Property 6: 桑基图连线过滤零值**
    - **Validates: Requirements 2.6**

- [x] 4. 数据联动集成
  - [x] 4.1 更新App.tsx中的数据获取逻辑
    - 修改 `fetchCostStructure` 函数调用新API
    - 更新数据转换逻辑 `convertToChannelMetrics`
    - 确保全局日期筛选和门店切换联动正常
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.2_

- [x] 5. Checkpoint - 功能验证
  - 确保所有测试通过
  - 验证桑基图正确显示渠道到营销类型的资金流向
  - 验证日期筛选和门店切换联动正常
  - 如有问题请询问用户

## Notes

- 所有任务均为必需，包括测试任务
- 现有的 `cost-structure` API 保留不变，新增 `marketing-structure` API
- 组件重构保持在原位置，只修改内部逻辑和展示内容
- 8个营销字段都是订单级字段，聚合时使用 `.first()` 避免重复计算
