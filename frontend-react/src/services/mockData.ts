import { ChannelType, DashboardData, ChannelMetrics, HourlyMetric, DistanceMetric, DailyMetric, CategoryMetric, AOVBucket, MarketingCostBreakdown, MarketingDailyBreakdown } from '@/types';

const generateHourlyData = (totalOrders: number, baseDeliveryCost: number): HourlyMetric[] => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);
  return hours.map((hour, index) => {
    let weight = 0.5;
    if (index >= 11 && index <= 13) weight = 2.5;
    if (index >= 17 && index <= 19) weight = 2.0;
    const hourOrders = Math.floor((totalOrders / 30) * weight * (0.8 + Math.random() * 0.4));
    return {
      hour,
      orders: hourOrders,
      revenue: hourOrders * 45,
      deliveryCost: hourOrders * baseDeliveryCost * (index >= 11 && index <= 13 ? 1.2 : 1)
    };
  });
};

const generateDistanceData = (totalOrders: number): DistanceMetric[] => {
  return [
    { range: '0-1km', orders: Math.floor(totalOrders * 0.4), avgDeliveryCost: 3.5 },
    { range: '1-3km', orders: Math.floor(totalOrders * 0.45), avgDeliveryCost: 5.8 },
    { range: '3km+', orders: Math.floor(totalOrders * 0.15), avgDeliveryCost: 9.2 }
  ];
};

const generateDailyTrend = (totalRevenue: number, totalOrders: number, profitMargin: number): DailyMetric[] => {
  const trends: DailyMetric[] = [];
  const today = new Date();
  const avgDailyRev = totalRevenue / 30;
  const avgDailyOrders = totalOrders / 30;

  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const isWeekend = d.getDay() === 0 || d.getDay() === 6;
    const seasonality = isWeekend ? 1.2 : 0.9;
    const noise = 0.8 + Math.random() * 0.4;
    
    const dailyRev = Math.floor(avgDailyRev * seasonality * noise);
    const dailyProfit = Math.floor(dailyRev * (profitMargin + (Math.random() - 0.5) * 0.1));

    trends.push({
      date: d.toISOString().split('T')[0].slice(5),
      revenue: dailyRev,
      profit: dailyProfit,
      orders: Math.floor(avgDailyOrders * seasonality * noise)
    });
  }
  return trends;
};

const generateCategories = (totalRevenue: number): CategoryMetric[] => {
  const categoriesStructure = [
    { name: '现磨咖啡', items: ['生椰拿铁', '冰美式', '焦糖玛奇朵', '燕麦拿铁', 'Dirty脏咖', '卡布奇诺', '澳白', '意式浓缩'], baseMargin: 0.65 },
    { name: '人气热食', items: ['老坛酸菜鱼', '小炒黄牛肉', '麻婆豆腐', '红烧肉', '宫保鸡丁', '鱼香肉丝', '番茄炒蛋', '梅菜扣肉', '大盘鸡'], baseMargin: 0.35 },
    { name: '超值套餐', items: ['单人工作餐', '双人分享桶', '全家福套餐', '商务会议餐', '情侣约会餐'], baseMargin: 0.25 },
    { name: '烘焙甜点', items: ['提拉米苏', '纽约芝士', '红丝绒', '黑森林', '榴莲千层', '蛋挞(3只)', '菠萝包'], baseMargin: 0.55 }
  ];

  let results: CategoryMetric[] = [];
  
  categoriesStructure.forEach(cat => {
    cat.items.forEach(item => {
      const itemShare = (Math.random() * 0.1) + 0.01; 
      const revenue = Math.floor(totalRevenue * 0.25 * itemShare); 
      const margin = cat.baseMargin + (Math.random() * 0.2 - 0.1);
      const profit = Math.floor(revenue * margin);
      const orderCount = Math.floor(revenue / (30 + Math.random() * 20)); // 模拟销量

      // 注意：售罄品和滞销品数据从后端API获取，这里不再模拟
      // 后端API使用与Dash版本完全一致的计算逻辑
      results.push({
        name: `${cat.name}|${item}`,
        revenue: revenue,
        cost: revenue - profit,
        profit: profit,
        grossMargin: margin,
        orderCount: orderCount,
        // 以下字段由后端API提供真实数据
        soldOutCount: 0,
        slowMovingCount: 0,
        inventoryTurnover: 0,
      });
    });
  });

  return results.sort((a, b) => b.revenue - a.revenue).slice(0, 50);
};

const generateAOVBuckets = (totalOrders: number, avgTicket: number): AOVBucket[] => {
  const ranges = ["0-20", "20-40", "40-60", "60-80", "80-100", "100+"];
  return ranges.map(range => {
    let weight = 0.1;
    if (avgTicket < 30 && range === "20-40") weight = 0.5;
    if (avgTicket >= 30 && range === "40-60") weight = 0.4;
    return { range, count: Math.floor(totalOrders * weight * (0.8 + Math.random() * 0.4)) };
  });
};

const generateMarketingDetails = (totalMarketing: number): MarketingCostBreakdown => {
  return {
    itemDiscount: totalMarketing * 0.3,
    thresholdDiscount: totalMarketing * 0.4,
    vouchers: totalMarketing * 0.2,
    other: totalMarketing * 0.1 
  };
};

const generateMarketingTrend = (totalMarketing: number): MarketingDailyBreakdown[] => {
  const dailyAvg = totalMarketing / 30;
  const trend: MarketingDailyBreakdown[] = [];
  const today = new Date();

  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const isWeekend = d.getDay() === 0 || d.getDay() === 6;
    const multiplier = isWeekend ? 1.3 : 0.9;
    
    const dayTotal = dailyAvg * multiplier * (0.9 + Math.random() * 0.2);
    
    trend.push({
      date: d.toISOString().split('T')[0].slice(5),
      itemDiscount: Math.floor(dayTotal * 0.3),
      thresholdDiscount: Math.floor(dayTotal * 0.4),
      vouchers: Math.floor(dayTotal * 0.2),
      other: Math.floor(dayTotal * 0.1)
    });
  }
  return trend;
}

const calculateDiagnosticMetrics = (
  id: string, 
  name: ChannelType, 
  gmv: number, 
  orderCount: number,
  cogsRatio: number,
  marketingRatio: number,
  commissionRatio: number,
  avgRiderCost: number
): ChannelMetrics => {
  const cogs = gmv * cogsRatio;
  const marketing = gmv * marketingRatio;
  const commission = gmv * commissionRatio;
  const delivery = orderCount * avgRiderCost;
  
  const totalCost = cogs + marketing + commission + delivery;
  const profit = gmv - totalCost;
  const profitMargin = profit / gmv;

  return {
    id,
    name,
    revenue: gmv,
    costs: { cogs, marketing, delivery, commission },
    marketingDetails: generateMarketingDetails(marketing),
    marketingTrend: generateMarketingTrend(marketing),
    totalCost,
    profit,
    marketingRate: marketing / gmv,
    profitMargin,
    orderCount,
    avgOrderValue: gmv / orderCount,
    avgDeliveryCost: delivery / orderCount,
    hourlyData: generateHourlyData(orderCount, avgRiderCost),
    distanceData: generateDistanceData(orderCount),
    dailyTrend: generateDailyTrend(gmv, orderCount, profitMargin),
    categoryPerformance: generateCategories(gmv),
    aovDistribution: generateAOVBuckets(orderCount, gmv / orderCount)
  };
};

export const getDashboardData = (): DashboardData => {
  const channels: ChannelMetrics[] = [
    calculateDiagnosticMetrics('1', ChannelType.MEITUAN, 450000, 11250, 0.35, 0.15, 0.18, 6.5),
    calculateDiagnosticMetrics('2', ChannelType.ELEME, 380000, 9500, 0.35, 0.20, 0.16, 6.2),
    calculateDiagnosticMetrics('3', ChannelType.DOUYIN, 600000, 15000, 0.35, 0.25, 0.05, 1.5),
    calculateDiagnosticMetrics('4', ChannelType.OFFLINE, 550000, 13750, 0.35, 0.02, 0.01, 0),
    calculateDiagnosticMetrics('5', ChannelType.PRIVATE_DOMAIN, 200000, 4000, 0.35, 0.05, 0.02, 5.0) 
  ];

  const totalRevenue = channels.reduce((acc, c) => acc + c.revenue, 0);
  const totalProfit = channels.reduce((acc, c) => acc + c.profit, 0);
  const totalOrders = channels.reduce((acc, c) => acc + c.orderCount, 0);

  return {
    totalRevenue,
    totalProfit,
    totalOrders,
    channels,
    lastUpdated: new Date().toLocaleString()
  };
};
