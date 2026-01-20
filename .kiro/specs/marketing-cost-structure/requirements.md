# Requirements Document

## Introduction

将现有的"成本结构"桑基图改造为"营销成本结构"桑基图，展示各渠道在8个营销字段上的费用分布。通过桑基图直观呈现营销资金从渠道流向各营销类型的全景视图。

## Glossary

- **Marketing_Sankey_Chart**: 营销成本结构桑基图组件，展示渠道与营销类型之间的资金流向
- **Channel**: 销售渠道，如美团、饿了么、京东到家等
- **Marketing_Cost_Type**: 营销成本类型，包含8个字段
- **Marketing_API**: 后端营销成本结构数据接口
- **Order_Level_Field**: 订单级字段，同一订单多行值相同，聚合时用`.first()`

## Requirements

### Requirement 1: 营销成本数据聚合

**User Story:** As a 门店运营人员, I want 按渠道聚合8个营销字段的数据, so that 我能了解每个渠道的营销投入分布。

#### Acceptance Criteria

1. THE Marketing_API SHALL 返回按渠道分组的8个营销字段数据
2. WHEN 聚合营销字段时, THE Marketing_API SHALL 对订单级字段使用`.first()`避免重复计算
3. THE Marketing_API SHALL 返回以下8个营销字段的金额：
   - 配送费减免金额 (delivery_discount)
   - 满减金额 (full_reduction)
   - 商品减免金额 (product_discount)
   - 商家代金券 (merchant_voucher)
   - 商家承担部分券 (merchant_share)
   - 满赠金额 (gift_amount)
   - 商家其他优惠 (other_discount)
   - 新客减免金额 (new_customer_discount)
4. WHEN 某营销字段值为0时, THE Marketing_API SHALL 仍返回该字段（值为0）
5. THE Marketing_API SHALL 支持按门店名称和日期范围过滤数据

### Requirement 2: 桑基图渲染

**User Story:** As a 门店运营人员, I want 通过桑基图查看营销成本流向, so that 我能直观理解各渠道的营销策略差异。

#### Acceptance Criteria

1. THE Marketing_Sankey_Chart SHALL 在左侧显示渠道节点
2. THE Marketing_Sankey_Chart SHALL 在右侧显示8个营销类型节点
3. WHEN 渲染连线时, THE Marketing_Sankey_Chart SHALL 根据金额大小调整连线宽度
4. THE Marketing_Sankey_Chart SHALL 为每种营销类型分配不同的颜色
5. WHEN 鼠标悬停在连线上时, THE Marketing_Sankey_Chart SHALL 显示tooltip包含：渠道名称、营销类型、金额
6. WHEN 某渠道某营销类型金额为0时, THE Marketing_Sankey_Chart SHALL 不显示该连线
7. THE Marketing_Sankey_Chart SHALL 支持深色和浅色主题切换

### Requirement 3: 营销效率指标展示

**User Story:** As a 门店运营人员, I want 查看营销效率汇总指标, so that 我能快速评估整体营销投入产出。

#### Acceptance Criteria

1. THE Marketing_API SHALL 返回以下汇总指标：
   - 总营销成本 (total_marketing_cost)
   - 单均营销费用 (avg_marketing_per_order)
   - 营销成本率 (marketing_cost_ratio)
   - 订单数 (order_count)
2. WHEN 计算总营销成本时, THE Marketing_API SHALL 使用公式：`总营销成本 = 配送费减免金额 + 满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠 + 新客减免金额`
3. WHEN 计算单均营销费用时, THE Marketing_API SHALL 使用公式：`单均营销费用 = 总营销成本 / 订单数`
4. WHEN 计算营销成本率时, THE Marketing_API SHALL 使用公式：`营销成本率 = 总营销成本 / 销售额 × 100%`

### Requirement 4: 数据过滤与联动

**User Story:** As a 门店运营人员, I want 营销成本图表响应全局日期筛选, so that 我能分析不同时间段的营销表现。

#### Acceptance Criteria

1. WHEN 全局日期范围变化时, THE Marketing_Sankey_Chart SHALL 重新请求并渲染对应时间段的数据
2. WHEN 门店选择变化时, THE Marketing_Sankey_Chart SHALL 重新请求并渲染对应门店的数据
3. IF 请求数据失败, THEN THE Marketing_Sankey_Chart SHALL 显示错误提示并保持上次有效数据
4. WHILE 数据加载中, THE Marketing_Sankey_Chart SHALL 显示加载状态

### Requirement 5: 替换现有成本结构图表

**User Story:** As a 开发者, I want 用营销成本结构图替换现有成本结构图, so that 看板展示更聚焦的营销分析。

#### Acceptance Criteria

1. THE System SHALL 将现有`ProfitChart.tsx`组件重构为营销成本结构桑基图
2. THE System SHALL 保持组件在App.tsx中的位置和布局不变
3. THE System SHALL 更新组件标题为"营销成本结构"
4. THE System SHALL 更新副标题为"MARKETING COST FLOW: CHANNEL → TYPE"
