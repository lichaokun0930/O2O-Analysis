/**
 * 订单数据 API
 * 对应后端 /api/v1/orders 路由
 */
import request from './index';
import type { DistanceAnalysisData, MarketingStructureData, MarketingTrendData } from '../types';

// ==================== 类型定义 ====================

/** 成本结构数据（资金流向全景桑基图专用） */
export interface CostStructureChannel {
  id: string;
  name: string;
  revenue: number;
  profit: number;
  order_count: number;
  costs: {
    cogs: number;      // 商品成本
    delivery: number;  // 配送净成本
    marketing: number; // 商家活动成本
    commission: number; // 平台服务费
  };
  rates: {
    profit_rate: number;
    cogs_rate: number;
    delivery_rate: number;
    marketing_rate: number;
    commission_rate: number;
  };
}

export interface CostStructureData {
  channels: CostStructureChannel[];
  total: {
    revenue: number;
    profit: number;
    cogs: number;
    delivery: number;
    marketing: number;
    commission: number;
  };
}

/** 订单概览数据（六大核心卡片 + GMV营销成本率） */
export interface OrderOverview {
  total_orders: number;        // 订单总数
  total_actual_sales: number;  // 商品实收额
  total_profit: number;        // 总利润
  avg_order_value: number;     // 平均客单价
  profit_rate: number;         // 总利润率
  active_products: number;     // 动销商品数
  // ✅ 新增：GMV和营销成本率
  gmv?: number;                // 营业额（GMV）
  marketing_cost?: number;     // 营销成本
  marketing_cost_rate?: number; // 营销成本率
}

/** 环比数据 */
export interface OrderComparison {
  current: {
    order_count: number;
    total_sales: number;
    total_profit: number;
    avg_order_value: number;
    profit_rate: number;
    active_products: number;
  };
  previous: {
    order_count: number;
    total_sales: number;
    total_profit: number;
    avg_order_value: number;
    profit_rate: number;
    active_products: number;
  };
  changes: {
    order_count: number;
    total_sales: number;
    total_profit: number;
    avg_order_value: number;
    profit_rate: number;  // 利润率用差值
    active_products: number;
  };
  period: {
    current_start: string;
    current_end: string;
    previous_start: string;
    previous_end: string;
    period_days: number;
  };
}

/** 渠道统计数据 */
export interface ChannelStats {
  channel: string;
  order_count: number;
  amount: number;
  profit: number;
  order_ratio: number;
  amount_ratio: number;
  avg_value: number;
  profit_rate: number;
}

/** 趋势数据 */
export interface OrderTrend {
  dates: string[];
  order_counts: number[];
  amounts: number[];
  profits: number[];
  avg_values: number[];
  profit_rates: number[];  // 🆕 利润率数组（与Dash版本一致）
}

/** 查询参数 */
export interface OrderQueryParams {
  store_name?: string;
  start_date?: string;
  end_date?: string;
}

// ==================== API 方法 ====================

export const ordersApi = {
  /**
   * 获取订单概览（六大核心卡片）
   * 对应 Dash 版本 Tab1 订单数据概览
   */
  getOverview(params?: OrderQueryParams): Promise<{ success: boolean; data: OrderOverview }> {
    return request.get('/orders/overview', { params });
  },

  /**
   * 获取订单环比数据
   */
  getComparison(params?: OrderQueryParams): Promise<{ success: boolean; data: OrderComparison }> {
    return request.get('/orders/comparison', { params });
  },

  /**
   * 获取渠道统计数据
   */
  getChannelStats(params?: OrderQueryParams): Promise<{ success: boolean; data: ChannelStats[] }> {
    return request.get('/orders/channels', { params });
  },

  /**
   * 获取成本结构分析数据（资金流向全景桑基图专用）
   * 与Dash版本Tab1成本结构分析完全一致
   */
  getCostStructure(params?: OrderQueryParams): Promise<{ success: boolean; data: CostStructureData }> {
    return request.get('/orders/cost-structure', { params });
  },

  /**
   * 获取订单趋势数据（与Dash版本销售趋势分析一致）
   * 支持渠道筛选、日期范围和利润率返回
   */
  getTrend(params?: {
    days?: number;
    store_name?: string;
    channel?: string;  // 渠道筛选，'all'或空表示全部渠道
    start_date?: string;  // 🆕 日期范围开始 (YYYY-MM-DD)
    end_date?: string;    // 🆕 日期范围结束 (YYYY-MM-DD)
    granularity?: 'day' | 'week' | 'month';
  }): Promise<{ success: boolean; data: OrderTrend }> {
    return request.get('/orders/trend', { params });
  },

  /**
   * 获取门店列表
   */
  getStores(): Promise<{ success: boolean; data: string[] }> {
    return request.get('/orders/stores');
  },

  /**
   * 获取渠道列表（支持门店筛选）
   */
  getChannels(params?: { store_name?: string }): Promise<{ success: boolean; data: string[] }> {
    return request.get('/orders/channel-list', { params });
  },

  /**
   * 获取客单价区间分布
   */
  getPriceDistribution(params?: OrderQueryParams): Promise<{
    success: boolean;
    data: {
      price_ranges: Array<{
        label: string;
        count: number;
        ratio: number;
        color: string;
      }>;
      business_zones: {
        flow_zone: { label: string; count: number; ratio: number };
        main_zone: { label: string; count: number; ratio: number };
        profit_zone: { label: string; count: number; ratio: number };
        high_zone: { label: string; count: number; ratio: number };
      };
      avg_basket_depth: number;
      total_orders: number;
      avg_order_value: number;
    };
  }> {
    return request.get('/orders/price-distribution', { params });
  },

  /**
   * 获取利润区间分布
   */
  getProfitDistribution(params?: OrderQueryParams): Promise<{
    success: boolean;
    data: {
      labels: string[];
      counts: number[];
      colors: string[];
      total_orders: number;
    };
  }> {
    return request.get('/orders/profit-distribution', { params });
  },

  /**
   * 获取渠道环比对比数据
   */
  getChannelComparison(params?: OrderQueryParams): Promise<{
    success: boolean;
    data: Array<{
      channel: string;
      current: {
        order_count: number;
        amount: number;
        profit: number;
        avg_value: number;
        profit_rate: number;
        product_cost: number;
        product_cost_rate: number;
        delivery_cost: number;
        delivery_cost_rate: number;
        platform_fee: number;
        platform_fee_rate: number;
      };
      previous: {
        order_count: number;
        amount: number;
        profit: number;
        avg_value: number;
        profit_rate: number;
      } | null;
      changes: {
        order_count: number | null;
        amount: number | null;
        profit: number | null;
        avg_value: number | null;
        profit_rate: number | null;
      };
      rating: string;
    }>;
  }> {
    return request.get('/orders/channel-comparison', { params });
  },

  /**
   * 获取异常诊断数据
   */
  getAnomalyDetection(params?: OrderQueryParams): Promise<{
    success: boolean;
    data: {
      low_profit: Array<{
        order_id: string;
        amount: number;
        profit: number;
        profit_rate: number;
        channel: string;
      }>;
      high_delivery: Array<{
        order_id: string;
        amount: number;
        delivery_cost: number;
        delivery_ratio: number;
        channel: string;
      }>;
      negative_profit: Array<{
        order_id: string;
        amount: number;
        profit: number;
        loss: number;
        channel: string;
      }>;
      summary: {
        total_orders: number;
        low_profit_count: number;
        low_profit_ratio: number;
        high_delivery_count: number;
        high_delivery_ratio: number;
        negative_profit_count: number;
        negative_profit_ratio: number;
        total_loss: number;
      };
    };
  }> {
    return request.get('/orders/anomaly-detection', { params });
  },

  /**
   * 获取门店数据日期范围
   * 用于日历选择器限制可选日期
   */
  getDateRange(params?: { store_name?: string }): Promise<{
    success: boolean;
    data: {
      min_date: string | null;
      max_date: string | null;
      total_days: number;
    };
  }> {
    return request.get('/orders/date-range', { params });
  },

  /**
   * 获取分时段品类走势数据（销售趋势图表联动）
   * - 指定单日期：返回24小时分时段品类销售数据
   * - 指定日期范围：返回范围内每日品类销售数据
   * - 不指定日期：返回近7天每日品类销售数据
   */
  getCategoryHourlyTrend(params?: {
    store_name?: string;
    date?: string;  // YYYY-MM-DD 或 MM-DD 格式（单日期）
    start_date?: string;  // 🆕 日期范围开始
    end_date?: string;    // 🆕 日期范围结束
    channel?: string;
  }): Promise<{
    success: boolean;
    data: CategoryHourlyTrend;
  }> {
    return request.get('/orders/category-hourly-trend', { params });
  },

  /**
   * 获取商品销量排行数据（销售趋势图表联动）
   * 支持多维度排序：quantity/revenue/profit/loss
   * 支持单日期或日期范围
   */
  getTopProductsByDate(params?: {
    store_name?: string;
    date?: string;
    start_date?: string;  // 🆕 日期范围开始
    end_date?: string;    // 🆕 日期范围结束
    channel?: string;
    sort_by?: 'quantity' | 'revenue' | 'profit' | 'loss';
    limit?: number;
  }): Promise<{
    success: boolean;
    data: TopProductsData;
  }> {
    return request.get('/orders/top-products-by-date', { params });
  },

  /**
   * 获取分时利润数据（分时段诊断图表专用）
   * 
   * 核心功能：
   * - 按小时聚合订单数和净利润
   * - 智能识别高峰时段（订单量 > 均值+0.5σ）
   * - 计算单均利润
   */
  getHourlyProfit(params?: {
    store_name?: string;
    target_date?: string;  // YYYY-MM-DD
    channel?: string;
  }): Promise<{
    success: boolean;
    data: HourlyProfitData;
  }> {
    return request.get('/orders/hourly-profit', { params });
  },

  /**
   * 获取分距离订单诊断数据
   * 
   * 核心功能：
   * - 按7个距离区间聚合订单指标
   * - 计算每个区间的订单数、销售额、利润、利润率、配送成本等
   * - 识别最优配送距离区间（利润率最高）
   * 
   * Requirements: 3.1, 3.2, 3.3
   */
  getDistanceAnalysis(params?: {
    store_name?: string;
    channel?: string;
    target_date?: string;   // YYYY-MM-DD 或 MM-DD 格式
    start_date?: string;    // YYYY-MM-DD
    end_date?: string;      // YYYY-MM-DD
  }): Promise<{
    success: boolean;
    data: DistanceAnalysisData;
  }> {
    return request.get('/orders/distance-analysis', { params });
  },

  /**
   * 获取配送溢价雷达数据
   * 
   * 核心功能：
   * - 返回每个订单的配送距离、时段、配送成本、利润等
   * - 用于雷达图展示配送溢价订单的时空分布
   * - 支持距离区间筛选（与分距离诊断图表联动）
   */
  getDeliveryRadar(params?: {
    store_name?: string;
    channel?: string;
    target_date?: string;   // 🆕 目标日期
    start_date?: string;
    end_date?: string;
    min_distance?: number;  // 最小距离(km)
    max_distance?: number;  // 最大距离(km)
  }): Promise<{
    success: boolean;
    date?: string;          // 🆕 分析日期
    data: DeliveryRadarPoint[];
    summary: DeliveryRadarSummary;
  }> {
    return request.get('/orders/delivery-radar', { params });
  },

  /**
   * 获取营销成本结构数据（营销成本结构桑基图专用）
   * 
   * 核心功能：
   * - 按渠道聚合8个营销字段的费用分布
   * - 返回汇总指标（总营销成本、单均营销费用、营销成本率）
   * - 支持门店和日期范围过滤
   * 
   * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2
   */
  getMarketingStructure(params?: {
    store_name?: string;
    start_date?: string;    // YYYY-MM-DD
    end_date?: string;      // YYYY-MM-DD
  }): Promise<{
    success: boolean;
    data: MarketingStructureData;
  }> {
    return request.get('/orders/marketing-structure', { params });
  },

  /**
   * 获取营销成本趋势数据（营销成本趋势图表专用）
   * 
   * 核心功能：
   * - 按日期分组聚合8个营销字段的费用数据
   * - 返回时间序列数据用于堆叠面积图展示
   * - 支持门店、渠道和日期范围过滤
   * 
   * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2
   */
  getMarketingTrend(params?: {
    store_name?: string;
    channel?: string;       // 🆕 渠道筛选
    start_date?: string;    // YYYY-MM-DD
    end_date?: string;      // YYYY-MM-DD
  }): Promise<{
    success: boolean;
    data: MarketingTrendData;
  }> {
    return request.get('/orders/marketing-trend', { params });
  },
};

/** 分时段品类走势数据 */
export interface CategoryHourlyTrend {
  labels: string[];      // 时间标签（小时或日期）
  categories: string[];  // 品类列表
  series: Array<{
    name: string;
    data: number[];
    color: string;
  }>;
  mode: 'hourly' | 'daily';  // 模式：分时段或按日
  date?: string;             // 指定的日期
}

/** 商品销量排行数据 */
export interface TopProductsData {
  products: Array<{
    name: string;
    quantity: number;
    revenue: number;
    profit: number;
    category: string;
    growth: number;
  }>;
  sort_by: string;
  date?: string;
  total_count: number;
}

/** 高峰时段信息 */
export interface PeakPeriod {
  start: string;      // "11:00"
  end: string;        // "14:00"
  name: string;       // "午高峰"
  start_hour: number;
  end_hour: number;
}

/** 分时利润数据（分时段诊断图表专用） */
export interface HourlyProfitData {
  date: string | null;
  hours: string[];           // ["00:00", "01:00", ..., "23:00"]
  orders: number[];          // 每小时订单数
  profits: number[];         // 每小时净利润
  revenues: number[];        // 每小时销售额
  avg_profits: number[];     // 每小时单均利润
  peak_periods: PeakPeriod[]; // 智能识别的高峰时段
}

/** 配送溢价雷达数据点 */
export interface DeliveryRadarPoint {
  distance: number;      // 配送距离(km)
  hour: number;          // 下单时段(0-23)
  delivery_cost: number; // 配送净成本
  order_value: number;   // 客单价
  profit: number;        // 订单利润
  is_premium: boolean;   // 是否溢价(配送成本>6元)
  channel: string;       // 渠道
}

/** 配送溢价雷达汇总数据 */
export interface DeliveryRadarSummary {
  total: number;              // 总订单数
  premium_count: number;      // 溢价订单数
  premium_rate: number;       // 溢价率(%)
  healthy_avg_profit: number; // 健康订单平均利润
  premium_avg_profit: number; // 溢价订单平均利润
}

export default ordersApi;
