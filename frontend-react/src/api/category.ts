/**
 * 品类健康度分析 API
 * 对应后端 /api/v1/category 路由
 */
import request from './index';

// ==================== 类型定义 ====================

/** 品类健康度数据项 */
export interface CategoryHealthItem {
  name: string;                  // 品类名称
  level: number;                 // 分类级别 (1=一级, 3=三级)
  parent: string | null;         // 父级分类
  current_revenue: number;       // 本期销售额
  previous_revenue: number;      // 上期销售额
  growth_rate: number;           // 环比增长率 (%)
  current_quantity: number;      // 本期销量
  previous_quantity: number;     // 上期销量
  quantity_growth_rate: number;  // 销量环比增长率 (%)
  volatility: number;            // 波动系数 (CV)
  volatility_level: string;      // 波动等级 (低/中/高)
  avg_discount: number;          // 本期平均折扣 (如 8.5 表示 8.5折)
  prev_discount: number;         // 上期平均折扣
  discount_change: number;       // 折扣变化 (本期 - 上期)
  profit_margin: number;         // 利润率 (%)
  daily_revenue: number[];       // 每日销售额（用于 sparkline）
}

/** 品类健康度响应 */
export interface CategoryHealthResponse {
  success: boolean;
  data: CategoryHealthItem[];
  period: {
    start: string;
    end: string;
    days: number;
  };
  summary: {
    total_categories: number;
    total_revenue: number;
  };
}

// ==================== API 方法 ====================

export const categoryApi = {
  /**
   * 获取品类健康度分析数据
   * @param params.store_name 门店名称
   * @param params.channel 渠道名称
   * @param params.period 周期天数 (7/14/30)，与 start_date/end_date 二选一
   * @param params.start_date 开始日期 (YYYY-MM-DD)
   * @param params.end_date 结束日期 (YYYY-MM-DD)
   * @param params.level 分类级别 (1=一级, 3=三级)
   * @param params.parent_category 父级分类（下钻时使用）
   */
  getHealth(params?: {
    store_name?: string;
    channel?: string;
    period?: number;
    start_date?: string;
    end_date?: string;
    level?: number;
    parent_category?: string;
  }): Promise<CategoryHealthResponse> {
    return request.get('/category/health', { params });
  },
};
