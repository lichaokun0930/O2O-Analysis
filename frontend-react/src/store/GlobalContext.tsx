/**
 * 全局状态管理 - 门店筛选、日期范围、系统状态、订单概览
 */
import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { dataApi, type Store, type DataStats } from '../api/data';
import { ordersApi, type OrderOverview, type OrderComparison } from '../api/orders';

// 日期范围类型 - 增加 'all' 表示全部数据
export type DateRangeType = 'today' | 'yesterday' | '7days' | '30days' | 'thisWeek' | 'thisMonth' | 'custom' | 'all';

export interface DateRange {
  type: DateRangeType;
  start: string;
  end: string;
}

// 门店数据日期范围
export interface StoreDateRange {
  min_date: string | null;
  max_date: string | null;
  total_days: number;
}

// 系统状态
export interface SystemStatus {
  database: 'connected' | 'disconnected' | 'checking';
  redis: 'connected' | 'disconnected' | 'checking';
  lastCheck: Date | null;
}

// Context 类型
interface GlobalContextType {
  // 门店相关
  stores: Store[];
  selectedStore: string;
  setSelectedStore: (store: string) => void;
  storesLoading: boolean;
  
  // 渠道相关（全局联动）
  selectedChannel: string;
  setSelectedChannel: (channel: string) => void;
  channelList: string[];  // 🆕 当前门店的渠道列表
  channelListLoading: boolean;
  
  // 日期相关
  dateRange: DateRange;
  setDateRange: (range: DateRange) => void;
  setQuickDateRange: (type: DateRangeType) => void;
  
  // 门店数据日期范围（用于日历限制）
  storeDateRange: StoreDateRange | null;
  storeDateRangeLoading: boolean;
  
  // 数据统计
  stats: DataStats | null;
  statsLoading: boolean;
  
  // 订单概览（六大核心卡片）
  orderOverview: OrderOverview | null;
  orderComparison: OrderComparison | null;
  orderOverviewLoading: boolean;
  
  // 系统状态
  systemStatus: SystemStatus;
  
  // 刷新方法
  refreshStores: () => Promise<void>;
  refreshStats: () => Promise<void>;
  refreshOrderOverview: () => Promise<void>;
  refreshStoreDateRange: () => Promise<void>;
  refreshChannelList: () => Promise<void>;  // 🆕
  refreshAll: () => Promise<void>;
}

const GlobalContext = createContext<GlobalContextType | null>(null);

// 计算日期范围 - 基于参考日期（默认今天，或门店数据最大日期）
const calculateDateRange = (type: DateRangeType, referenceDate?: Date): { start: string; end: string } => {
  const baseDate = referenceDate || new Date();
  const formatDate = (d: Date) => d.toISOString().split('T')[0];
  
  switch (type) {
    case 'today':
      return { start: formatDate(baseDate), end: formatDate(baseDate) };
    case 'yesterday': {
      const yesterday = new Date(baseDate);
      yesterday.setDate(baseDate.getDate() - 1);
      return { start: formatDate(yesterday), end: formatDate(yesterday) };
    }
    case '7days': {
      const start = new Date(baseDate);
      start.setDate(baseDate.getDate() - 6);
      return { start: formatDate(start), end: formatDate(baseDate) };
    }
    case '30days': {
      const start = new Date(baseDate);
      start.setDate(baseDate.getDate() - 29);
      return { start: formatDate(start), end: formatDate(baseDate) };
    }
    case 'thisWeek': {
      const start = new Date(baseDate);
      start.setDate(baseDate.getDate() - baseDate.getDay());
      return { start: formatDate(start), end: formatDate(baseDate) };
    }
    case 'thisMonth': {
      const start = new Date(baseDate.getFullYear(), baseDate.getMonth(), 1);
      return { start: formatDate(start), end: formatDate(baseDate) };
    }
    case 'all':
      return { start: '', end: '' };
    default:
      return { start: formatDate(baseDate), end: formatDate(baseDate) };
  }
};


export const GlobalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // 门店状态
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStoreState] = useState<string>('');
  const [storesLoading, setStoresLoading] = useState(false);
  
  // 渠道状态（全局联动：销售趋势 → 分时段诊断 → 分距离诊断）
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [channelList, setChannelList] = useState<string[]>([]);
  const [channelListLoading, setChannelListLoading] = useState(false);
  
  // 日期状态 - 默认全部数据
  const [dateRange, setDateRange] = useState<DateRange>({
    type: 'all',
    start: '',
    end: ''
  });
  
  // 门店数据日期范围
  const [storeDateRange, setStoreDateRange] = useState<StoreDateRange | null>(null);
  const [storeDateRangeLoading, setStoreDateRangeLoading] = useState(false);
  
  // 数据统计
  const [stats, setStats] = useState<DataStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  
  // 订单概览数据
  const [orderOverview, setOrderOverview] = useState<OrderOverview | null>(null);
  const [orderComparison, setOrderComparison] = useState<OrderComparison | null>(null);
  const [orderOverviewLoading, setOrderOverviewLoading] = useState(false);
  
  // 系统状态
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    database: 'checking',
    redis: 'checking',
    lastCheck: null
  });

  // 快捷设置日期范围 - 基于门店数据的最大日期
  const setQuickDateRange = useCallback((type: DateRangeType) => {
    if (type === 'all') {
      setDateRange({ type: 'all', start: '', end: '' });
    } else {
      // 使用门店数据的最大日期作为参考日期，如果没有则使用今天
      const referenceDate = storeDateRange?.max_date 
        ? new Date(storeDateRange.max_date) 
        : new Date();
      const { start, end } = calculateDateRange(type, referenceDate);
      setDateRange({ type, start, end });
      console.log(`📅 日期范围计算: ${type}, 参考日期: ${referenceDate.toISOString().split('T')[0]}, 结果: ${start} ~ ${end}`);
    }
  }, [storeDateRange]);

  // 刷新门店数据日期范围
  const refreshStoreDateRange = useCallback(async () => {
    // 未选择门店时不加载
    if (!selectedStore) {
      setStoreDateRange(null);
      return;
    }
    
    setStoreDateRangeLoading(true);
    try {
      const params: { store_name?: string } = { store_name: selectedStore };
      const res = await ordersApi.getDateRange(params);
      if (res.success) {
        setStoreDateRange(res.data);
        console.log('📅 门店数据日期范围:', res.data);
      }
    } catch (error) {
      console.error('获取门店日期范围失败:', error);
      setStoreDateRange(null);
    } finally {
      setStoreDateRangeLoading(false);
    }
  }, [selectedStore]);

  // 🆕 刷新渠道列表（当门店变化时）
  const refreshChannelList = useCallback(async () => {
    if (!selectedStore) {
      setChannelList([]);
      return;
    }
    
    setChannelListLoading(true);
    try {
      const res = await ordersApi.getChannels({ store_name: selectedStore });
      if (res.success && res.data) {
        setChannelList(res.data);
        // 如果当前选中的渠道不在新列表中，重置为全部
        if (selectedChannel !== 'all' && !res.data.includes(selectedChannel)) {
          setSelectedChannel('all');
        }
        console.log('📡 渠道列表已更新:', res.data.length, '个渠道');
      }
    } catch (error) {
      console.error('获取渠道列表失败:', error);
      setChannelList([]);
    } finally {
      setChannelListLoading(false);
    }
  }, [selectedStore, selectedChannel]);

  // 设置门店
  const setSelectedStore = useCallback((store: string) => {
    setSelectedStoreState(store);
  }, []);

  // 刷新门店列表
  const refreshStores = useCallback(async () => {
    setStoresLoading(true);
    try {
      const res = await dataApi.getStores();
      if (res.success) {
        setStores(res.data);
      }
    } catch (error) {
      console.error('获取门店列表失败:', error);
      setStores([]);
    } finally {
      setStoresLoading(false);
    }
  }, []);

  // 刷新统计数据
  const refreshStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const data = await dataApi.getStats();
      setStats(data);
      setSystemStatus({
        database: data.database_status === '已连接' ? 'connected' : 'disconnected',
        redis: data.redis_status === '已连接' ? 'connected' : 'disconnected',
        lastCheck: new Date()
      });
    } catch (error) {
      console.error('获取统计数据失败:', error);
      setSystemStatus({
        database: 'disconnected',
        redis: 'disconnected',
        lastCheck: new Date()
      });
    } finally {
      setStatsLoading(false);
    }
  }, []);

  // 带重试机制的刷新统计数据
  const refreshStatsWithRetry = useCallback(async (maxRetries: number = 3, delay: number = 2000) => {
    let lastError: any = null;
    for (let i = 0; i < maxRetries; i++) {
      try {
        await refreshStats();
        return;
      } catch (error) {
        lastError = error;
        console.log(`重试 ${i + 1}/${maxRetries} 失败，${delay}ms 后再次尝试...`);
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    console.error('所有重试均失败:', lastError);
  }, [refreshStats]);


  // 刷新订单概览数据
  const refreshOrderOverview = useCallback(async () => {
    // 未选择门店时不加载数据
    if (!selectedStore) {
      setOrderOverview(null);
      setOrderComparison(null);
      setOrderOverviewLoading(false);
      console.log('📊 未选择门店，不加载数据');
      return;
    }
    
    setOrderOverviewLoading(true);
    try {
      // 构建查询参数 - 必须有门店
      const params: { store_name: string; start_date?: string; end_date?: string } = {
        store_name: selectedStore
      };
      
      // 根据日期类型决定是否传日期参数
      // "全部数据"时不传日期，让后端使用数据的完整范围
      // 其他情况传具体日期
      if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
        params.start_date = dateRange.start;
        params.end_date = dateRange.end;
      }

      console.log('📊 请求订单概览, 参数:', params, '日期类型:', dateRange.type);

      // 并行获取概览和环比数据
      const [overviewRes, comparisonRes] = await Promise.all([
        ordersApi.getOverview(params),
        ordersApi.getComparison(params)
      ]);
      
      if (overviewRes.success) {
        setOrderOverview(overviewRes.data);
      } else {
        console.error('❌ 订单概览获取失败:', overviewRes);
        setOrderOverview(null);
      }

      // 环比数据处理
      // 如果上一周期没有数据（previous全为0），则不显示环比
      if (comparisonRes.success && comparisonRes.data) {
        const prevMetrics = comparisonRes.data.previous;
        const hasValidPrevious = prevMetrics && (
          prevMetrics.order_count > 0 || 
          prevMetrics.total_sales > 0 || 
          prevMetrics.total_profit !== 0
        );
        
        if (hasValidPrevious) {
          setOrderComparison(comparisonRes.data);
          console.log('📊 环比数据有效:', comparisonRes.data.period);
        } else {
          // 上一周期无数据，清空环比
          setOrderComparison(null);
          console.log('📊 上一周期无数据，不显示环比');
        }
      } else {
        setOrderComparison(null);
      }
    } catch (error) {
      console.error('❌ 获取订单概览失败:', error);
      setOrderOverview(null);
      setOrderComparison(null);
    } finally {
      setOrderOverviewLoading(false);
    }
  }, [selectedStore, dateRange.type, dateRange.start, dateRange.end]);  // 🔧 使用具体属性作为依赖

  // 刷新所有数据
  const refreshAll = useCallback(async () => {
    await Promise.all([refreshStores(), refreshStats(), refreshStoreDateRange(), refreshChannelList()]);
    await refreshOrderOverview();
  }, [refreshStores, refreshStats, refreshStoreDateRange, refreshChannelList, refreshOrderOverview]);

  // 初始化加载（只执行一次）- 使用带重试机制的版本
  useEffect(() => {
    refreshStores();
    refreshStatsWithRetry(5, 2000);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 定期检查系统状态（每30秒检查一次）
  useEffect(() => {
    const interval = setInterval(() => {
      refreshStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 门店变化时刷新日期范围
  useEffect(() => {
    refreshStoreDateRange();
    refreshChannelList();  // 🆕 同时刷新渠道列表
  }, [selectedStore]); // eslint-disable-line react-hooks/exhaustive-deps

  // 门店或日期范围变化时刷新订单数据
  useEffect(() => {
    refreshOrderOverview();
  }, [selectedStore, dateRange.type, dateRange.start, dateRange.end]); // eslint-disable-line react-hooks/exhaustive-deps

  const value: GlobalContextType = {
    stores,
    selectedStore,
    setSelectedStore,
    storesLoading,
    selectedChannel,
    setSelectedChannel,
    channelList,
    channelListLoading,
    dateRange,
    setDateRange,
    setQuickDateRange,
    storeDateRange,
    storeDateRangeLoading,
    stats,
    statsLoading,
    orderOverview,
    orderComparison,
    orderOverviewLoading,
    systemStatus,
    refreshStores,
    refreshStats,
    refreshOrderOverview,
    refreshStoreDateRange,
    refreshChannelList,
    refreshAll
  };

  return (
    <GlobalContext.Provider value={value}>
      {children}
    </GlobalContext.Provider>
  );
};

// Hook
export const useGlobalContext = () => {
  const context = useContext(GlobalContext);
  if (!context) {
    throw new Error('useGlobalContext must be used within GlobalProvider');
  }
  return context;
};

export default GlobalContext;
