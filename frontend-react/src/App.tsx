import React, { useEffect, useState, useRef, useMemo, Suspense, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import StatCard from './components/StatCard';
// 首屏必需组件（直接导入）
import DailyTrendChart from './components/charts/DailyTrendChart';
import AIInsightsPanel from './components/AIInsightsPanel';
import AICommandBar from './components/AICommandBar';

// 🆕 懒加载非首屏组件（优化首屏加载速度）
const CostStructureChart = React.lazy(() => import('./components/charts/ProfitChart'));
const HourlyAnalysisChart = React.lazy(() => import('./components/charts/CostEfficiencyChart'));
const CategoryAnalysisChart = React.lazy(() => import('./components/charts/CategoryAnalysisChart'));
const MarketingCostChart = React.lazy(() => import('./components/charts/MarketingCostChart'));
const DeliveryHeatmap = React.lazy(() => import('./components/charts/DeliveryHeatmap'));
const MarketingTrendChart = React.lazy(() => import('./components/charts/MarketingTrendChart'));
const ProfitSimulator = React.lazy(() => import('./components/ProfitSimulator'));
const DataTable = React.lazy(() => import('./components/DataTable'));
const CategoryTrendChart = React.lazy(() => import('./components/charts/CategoryTrendChart'));
const TopProductsChart = React.lazy(() => import('./components/charts/TopProductsChart'));
const CategoryHealthTable = React.lazy(() => import('./components/charts/CategoryHealthTable'));
const DistanceAnalysisChart = React.lazy(() => import('./components/charts/DistanceAnalysisChart'));
const AllStoresOverviewChart = React.lazy(() => import('./components/charts/AllStoresOverviewChart'));

// 懒加载页面组件
const DataManagement = React.lazy(() => import('./views/DataManagement'));
const StoreComparisonView = React.lazy(() => import('./views/StoreComparisonView'));

import { DashboardData, FocusArea } from './types';
import { ShoppingBag, DollarSign, Wallet, Minimize2, Zap, TrendingUp, Package, Percent, ArrowDown } from 'lucide-react';
import { usePerformanceMonitor } from './hooks/usePerformanceMonitor';
import { getDashboardData } from './services/mockData';
import { useGlobalContext } from './store/GlobalContext';
import { ordersApi } from './api/orders';
import type { ChannelMarketingData, MarketingTrendData } from './types';

// 🆕 图表加载占位组件
const ChartLoading = ({ height = 400 }: { height?: number }) => (
  <div
    className="glass-panel rounded-2xl flex items-center justify-center animate-pulse"
    style={{ height }}
  >
    <div className="text-slate-500 text-sm">图表加载中...</div>
  </div>
);

const MinimizeAction = ({ onExit }: { onExit: () => void }) => (
  <div className="absolute top-4 right-4 z-[70] animate-fade-in-up">
    <button
      onClick={(e) => { e.stopPropagation(); onExit(); }}
      className="group flex items-center gap-2 pl-2 pr-2 py-1.5 bg-slate-800/80 backdrop-blur-md text-white border border-white/20 rounded-lg hover:bg-slate-700 transition-all duration-200 shadow-lg"
    >
      <span className="text-[10px] font-mono font-bold tracking-wider text-slate-300 group-hover:text-white">MINIMIZE</span>
      <Minimize2 size={14} className="text-indigo-400 group-hover:text-indigo-300" />
    </button>
  </div>
);



const DashboardSkeleton = React.lazy(() => import('./components/ui/Skeleton').then(m => ({ default: m.DashboardSkeleton })));

// 内联简化版骨架屏（用于首次加载）
const InlineSkeleton = () => (
  <div className="min-h-screen bg-slate-950 p-8 grid grid-cols-12 gap-6 animate-pulse">
    <div className="col-span-12 h-20 bg-white/5 rounded-xl"></div>
    {[...Array(6)].map((_, i) => (
      <div key={i} className="col-span-6 lg:col-span-2 h-32 bg-white/5 rounded-2xl"></div>
    ))}
    <div className="col-span-12 xl:col-span-8 h-[550px] bg-white/5 rounded-2xl"></div>
    <div className="col-span-12 xl:col-span-4 h-[550px] bg-white/5 rounded-2xl"></div>
  </div>
);


function Dashboard({ theme }: { theme: 'dark' | 'light' }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [focusArea, setFocusArea] = useState<FocusArea>(null);
  const [aiProcessing, setAiProcessing] = useState(false);

  // 🆕 营销成本结构真实数据（营销成本结构桑基图专用）
  const [marketingStructureChannels, setMarketingStructureChannels] = useState<ChannelMarketingData[]>([]);
  const [marketingStructureLoading, setMarketingStructureLoading] = useState(false);

  // 🆕 营销成本趋势数据（营销成本趋势图表专用）
  // Requirements: 4.1, 4.2, 4.3, 4.4, 5.1
  const [marketingTrendData, setMarketingTrendData] = useState<MarketingTrendData | null>(null);
  const [marketingTrendLoading, setMarketingTrendLoading] = useState(false);
  const [marketingTrendError, setMarketingTrendError] = useState<string | null>(null);

  // 🆕 图表联动状态：支持单日期或日期范围选择
  // selectedDrillDate: 单日期选择（向后兼容）
  // selectedDateRange: 日期范围选择（点击两个柱子形成范围）
  const [selectedDrillDate, setSelectedDrillDate] = useState<string | null>(null);
  const [selectedDrillIndex, setSelectedDrillIndex] = useState<number | undefined>(undefined);
  const [selectedDateRange, setSelectedDateRange] = useState<{ start: string; end: string; startIndex: number; endIndex: number } | null>(null);
  const [totalDateCount, setTotalDateCount] = useState<number>(30);  // 默认30天

  // 🆕 分距离诊断图表 → 配送溢价雷达 联动状态
  // 用户点击柱状图的距离区间，雷达图过滤显示该区间的数据
  const [selectedDistanceBand, setSelectedDistanceBand] = useState<{ minDistance: number; maxDistance: number } | null>(null);

  // 🆕 营销趋势图表独立的渠道选择状态
  const [marketingTrendChannel, setMarketingTrendChannel] = useState<string>('all');

  // 从全局状态获取真实订单数据
  const {
    orderOverview,
    orderComparison,
    orderOverviewLoading,
    dateRange,
    selectedStore,
    selectedChannel   // 全局渠道状态
  } = useGlobalContext();

  const isLowPerf = usePerformanceMonitor();

  const trendRef = useRef<HTMLDivElement>(null);
  const efficiencyRef = useRef<HTMLDivElement>(null);
  const costRef = useRef<HTMLDivElement>(null);
  const profitRef = useRef<HTMLDivElement>(null);
  const drillDownRef = useRef<HTMLDivElement>(null); // 🆕 下钻区域ref

  // 🆕 获取营销成本结构真实数据
  // Requirements: 4.1, 4.2, 4.3, 4.4, 5.2
  const fetchMarketingStructure = useCallback(async () => {
    setMarketingStructureLoading(true);
    try {
      // 🔧 store_name 可选（空=全部门店）
      const params: { store_name?: string; start_date?: string; end_date?: string } = {
        store_name: selectedStore || undefined
      };

      // Requirements 4.1, 4.2: 响应全局日期筛选
      if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
        params.start_date = dateRange.start;
        params.end_date = dateRange.end;
      }

      const res = await ordersApi.getMarketingStructure(params);

      if (res.success && res.data.channels.length > 0) {
        // 直接使用API返回的ChannelMarketingData格式
        setMarketingStructureChannels(res.data.channels);
      } else {
        setMarketingStructureChannels([]);
      }
    } catch (error) {
      // Requirements 4.3: 请求失败时保持上次有效数据（这里清空，让组件显示空状态）
      console.error('获取营销成本结构数据失败:', error);
      setMarketingStructureChannels([]);
    } finally {
      setMarketingStructureLoading(false);
    }
  }, [selectedStore, dateRange.type, dateRange.start, dateRange.end]);  // 🔧 使用具体属性作为依赖

  // 门店或日期变化时获取营销成本结构数据
  // Requirements 4.1, 4.2: 日期范围变化和门店选择变化时重新请求
  useEffect(() => {
    fetchMarketingStructure();
  }, [fetchMarketingStructure]);

  // 🆕 获取营销成本趋势真实数据
  // Requirements: 4.1, 4.2, 4.3, 4.4, 5.1
  const fetchMarketingTrend = useCallback(async () => {
    console.log('📈 fetchMarketingTrend 调用, selectedStore:', selectedStore || '全部门店');

    setMarketingTrendLoading(true);
    setMarketingTrendError(null);
    try {
      // 🔧 store_name 可选（空=全部门店）
      const params: { store_name?: string; channel?: string; start_date?: string; end_date?: string } = {
        store_name: selectedStore || undefined
      };

      // 🆕 添加渠道筛选（使用营销趋势图表独立的渠道状态）
      if (marketingTrendChannel && marketingTrendChannel !== 'all') {
        params.channel = marketingTrendChannel;
      }

      // Requirements 4.1, 4.2: 响应全局日期筛选
      if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
        params.start_date = dateRange.start;
        params.end_date = dateRange.end;
      }

      console.log('📈 营销趋势请求参数:', params);
      const res = await ordersApi.getMarketingTrend(params);
      console.log('📈 营销趋势API响应:', res);

      if (res.success && res.data.dates.length > 0) {
        console.log('📈 营销趋势数据加载成功, 日期数:', res.data.dates.length);
        setMarketingTrendData(res.data);
        setMarketingTrendError(null);
      } else {
        console.log('📈 营销趋势数据为空');
        // Requirements 4.3: 请求失败时保持上次有效数据
        // 这里如果没有数据，设置为null让组件显示空状态
        setMarketingTrendData(null);
      }
    } catch (error) {
      // Requirements 4.3: 请求失败时显示错误提示
      console.error('📈 获取营销成本趋势数据失败:', error);
      setMarketingTrendError('数据加载失败，请稍后重试');
      // 保持上次有效数据（不清空marketingTrendData）
    } finally {
      setMarketingTrendLoading(false);
    }
  }, [selectedStore, marketingTrendChannel, dateRange.type, dateRange.start, dateRange.end]);  // 🔧 使用 marketingTrendChannel

  // 门店或日期变化时获取营销成本趋势数据
  // Requirements 4.1, 4.2: 日期范围变化和门店选择变化时重新请求
  useEffect(() => {
    fetchMarketingTrend();
  }, [fetchMarketingTrend]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const generatedData = getDashboardData();
      setData(generatedData);
    }, 100);
    return () => clearTimeout(timer);
  }, [dateRange]);

  // Handle Focus Mode
  useEffect(() => {
    if (focusArea) document.body.classList.add('has-focus');
    else document.body.classList.remove('has-focus');
  }, [focusArea]);

  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setFocusArea(null);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  // 🆕 处理日期选择：支持单日期和日期范围选择
  // - 第一次点击：选中单个日期
  // - 第二次点击不同日期：形成日期范围
  // - 点击已选中的日期：取消选择
  const handleDrillDateSelect = useCallback((date: string | null, index?: number, total?: number) => {
    if (total !== undefined) {
      setTotalDateCount(total);
    }

    // 取消选择
    if (date === null) {
      setSelectedDrillDate(null);
      setSelectedDrillIndex(undefined);
      setSelectedDateRange(null);
      return;
    }

    // 如果已有日期范围，点击任意位置重置为单日期选择
    if (selectedDateRange) {
      setSelectedDateRange(null);
      setSelectedDrillDate(date);
      setSelectedDrillIndex(index);
      return;
    }

    // 如果已选中单个日期
    if (selectedDrillDate && index !== undefined) {
      // 点击同一个日期：取消选择
      if (selectedDrillDate === date) {
        setSelectedDrillDate(null);
        setSelectedDrillIndex(undefined);
        return;
      }

      // 点击不同日期：形成日期范围
      const startDate = selectedDrillDate < date ? selectedDrillDate : date;
      const endDate = selectedDrillDate < date ? date : selectedDrillDate;
      const startIdx = selectedDrillDate < date ? selectedDrillIndex! : index;
      const endIdx = selectedDrillDate < date ? index : selectedDrillIndex!;

      setSelectedDateRange({ start: startDate, end: endDate, startIndex: startIdx, endIndex: endIdx });
      setSelectedDrillDate(null);  // 清除单日期选择
      setSelectedDrillIndex(undefined);
      return;
    }

    // 首次选择：设置单个日期
    setSelectedDrillDate(date);
    setSelectedDrillIndex(index);
  }, [selectedDrillDate, selectedDrillIndex, selectedDateRange]);

  // 🆕 处理分距离诊断图表点击联动
  // 用户点击柱状图的距离区间，雷达图过滤显示该区间的数据
  const handleDistanceBandSelect = useCallback((bandIndex: number, bandLabel: string, minDistance: number, maxDistance: number) => {
    console.log('📊 距离区间选中:', bandIndex, bandLabel, minDistance, '-', maxDistance, 'km');
    // bandIndex === -1 表示取消选中
    if (bandIndex === -1) {
      setSelectedDistanceBand(null);
    } else {
      setSelectedDistanceBand({ minDistance, maxDistance });
    }
  }, []);

  const handleAICommand = async (cmd: string) => {
    setAiProcessing(true);
    // Simulate processing
    await new Promise(r => setTimeout(r, 1500));
    setAiProcessing(false);

    // AI 命令处理（可扩展）
    console.log('AI Command:', cmd);
  };

  const handleFocusLocate = (area: FocusArea) => {
    if (focusArea === area) {
      setFocusArea(null);
      return;
    }
    setFocusArea(area);
    const refMap: Record<string, React.RefObject<HTMLDivElement>> = {
      'trend': trendRef,
      'efficiency': efficiencyRef,
      'cost': costRef,
      'profit': profitRef
    };
    const target = refMap[area as string];
    if (target?.current) {
      setTimeout(() => target.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
    }
  };

  const getFocusClass = (targetArea: FocusArea) => focusArea === targetArea ? 'is-focused relative' : '';

  // --- FILTER LOGIC ---
  // 使用mock数据作为基础数据
  const filteredData = useMemo(() => {
    if (!data) return null;
    return data;
  }, [data]);

  if (!filteredData) return (
    <Suspense fallback={<InlineSkeleton />}>
      <DashboardSkeleton />
    </Suspense>
  );


  return (
    <div className={`flex flex-col gap-6 relative z-10 w-full transition-all duration-500`}>

      {/* --- Header Row --- */}
      <div className={`flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 animate-fade-in-up transition-opacity duration-500 ${focusArea ? 'opacity-20 blur-sm pointer-events-none' : 'opacity-100'}`}>
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 tracking-tight">
            运营诊断中心
          </h2>
          <p className="text-slate-400 text-xs mt-1 font-mono opacity-60 flex items-center gap-2">
            SYSTEM: ONLINE
            {isLowPerf && <span className="text-neon-yellow flex items-center gap-1"><Zap size={10} /> LITE</span>}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-4 w-full xl:w-auto">
          <div className="w-full sm:w-auto flex-1">
            <AICommandBar onCommand={handleAICommand} isProcessing={aiProcessing} />
          </div>
        </div>
      </div>

      {/* --- MAIN BENTO GRID --- */}
      <div className="grid grid-cols-12 gap-6 w-full pb-12">

        {/* Row 1: 4个核心指标卡片 - 上排 */}
        {/* 环比显示逻辑：有环比数据时显示，无数据时显示"无数据" */}
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-1`}>
          <StatCard
            title="订单总数"
            value={orderOverview ? orderOverview.total_orders.toLocaleString() : '-'}
            change={orderComparison?.changes?.order_count}
            subtext="环比"
            icon={<ShoppingBag size={18} />}
            iconColor="indigo"
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-2`}>
          <StatCard
            title="商品实收额"
            value={orderOverview ? `¥${orderOverview.total_actual_sales.toLocaleString()}` : '-'}
            change={orderComparison?.changes?.total_sales}
            subtext="环比"
            icon={<DollarSign size={18} />}
            iconColor="cyan"
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-3`}>
          <StatCard
            title="营业额(GMV)"
            value={orderOverview?.gmv ? `¥${orderOverview.gmv.toLocaleString()}` : '-'}
            subtext="商品原价×销量+打包费+配送费"
            icon={<DollarSign size={18} />}
            iconColor="orange"
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-4`}>
          <StatCard
            title="总利润"
            value={orderOverview ? `¥${orderOverview.total_profit.toLocaleString()}` : '-'}
            change={orderComparison?.changes?.total_profit}
            subtext="环比"
            icon={<Wallet size={18} />}
            iconColor="emerald"
            trendColor={(orderComparison?.changes?.total_profit ?? 0) < 0 ? "red" : "green"}
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>

        {/* Row 2: 4个核心指标卡片 - 下排 */}
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-5`}>
          <StatCard
            title="平均客单价"
            value={orderOverview ? `¥${orderOverview.avg_order_value.toFixed(1)}` : '-'}
            change={orderComparison?.changes?.avg_order_value}
            subtext="环比"
            icon={<TrendingUp size={18} />}
            iconColor="amber"
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-6`}>
          <StatCard
            title="总利润率"
            value={orderOverview ? `${orderOverview.profit_rate.toFixed(1)}%` : '-'}
            change={orderComparison?.changes?.profit_rate}
            subtext="环比(百分点)"
            icon={<Percent size={18} />}
            iconColor="violet"
            trendColor={(orderComparison?.changes?.profit_rate ?? 0) < 0 ? "red" : "green"}
            theme={theme}
            loading={orderOverviewLoading}
            compact
            isPercentChange
          />
        </div>
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-7`}>
          <StatCard
            title="营销成本率"
            value={orderOverview?.marketing_cost_rate !== undefined ? `${orderOverview.marketing_cost_rate.toFixed(2)}%` : '-'}
            subtext={orderOverview?.marketing_cost ? `营销成本: ¥${orderOverview.marketing_cost.toLocaleString()}` : '营销成本/GMV'}
            icon={<Percent size={18} />}
            iconColor="pink"
            trendColor={(orderOverview?.marketing_cost_rate ?? 0) > 15 ? "red" : "green"}
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>
        <div className={`col-span-6 lg:col-span-3 animate-fade-in-up stagger-8`}>
          <StatCard
            title="动销商品数"
            value={orderOverview ? orderOverview.active_products.toLocaleString() : '-'}
            change={orderComparison?.changes?.active_products}
            subtext="环比"
            icon={<Package size={18} />}
            iconColor="rose"
            theme={theme}
            loading={orderOverviewLoading}
            compact
          />
        </div>

        {/* Row 2.5: 全门店经营总览（独立于门店选择器） */}
        <div className="col-span-12 animate-fade-in-up stagger-8">
          <Suspense fallback={<ChartLoading height={300} />}>
            <AllStoresOverviewChart theme={theme} />
          </Suspense>
        </div>

        {/* Row 3: Trend Chart + AI Panel - Uses Filtered Data */}
        <div ref={trendRef} className={`col-span-12 xl:col-span-8 h-[550px] animate-fade-in-up stagger-9 ${getFocusClass('trend')}`}>
          {focusArea === 'trend' && <MinimizeAction onExit={() => setFocusArea(null)} />}
          <DailyTrendChart
            data={filteredData.channels}
            theme={theme}
            onDateSelect={handleDrillDateSelect}
            selectedDate={selectedDrillDate}
            selectedDateRange={selectedDateRange ? { start: selectedDateRange.start, end: selectedDateRange.end } : undefined}
          />
        </div>

        <div className="col-span-12 xl:col-span-4 h-[550px] animate-fade-in-up stagger-10 z-30">
          <AIInsightsPanel data={filteredData} onLocate={handleFocusLocate} activeFocus={focusArea} />
        </div>

        {/* 🆕 图表联动区域：分时段品类走势 + 商品销量 */}
        {/* 视觉连接线（选中日期或日期范围时显示） */}
        {(selectedDrillDate || selectedDateRange) && (
          <div className="col-span-12 xl:col-span-8 relative h-10 -mt-4 -mb-2 z-0 animate-fade-in-up">
            {/* 单日期选择：显示单个连接线 */}
            {selectedDrillDate && !selectedDateRange && (
              <div
                className="absolute flex flex-col items-center text-indigo-400 transition-all duration-300"
                style={{
                  left: selectedDrillIndex !== undefined
                    ? `calc(50px + ${((selectedDrillIndex + 0.5) / totalDateCount) * 85}%)`
                    : '50%',
                  transform: 'translateX(-50%)'
                }}
              >
                <div className="h-6 w-0.5 bg-gradient-to-b from-indigo-500/0 via-indigo-500 to-indigo-500"></div>
                <div className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-[10px] font-mono flex items-center gap-2 whitespace-nowrap">
                  <ArrowDown size={10} /> 点击另一日期形成范围 | {selectedDrillDate?.slice(5)}
                </div>
              </div>
            )}
            {/* 日期范围选择：显示范围连接线 */}
            {selectedDateRange && (
              <div
                className="absolute flex flex-col items-center text-emerald-400 transition-all duration-300"
                style={{
                  left: `calc(50px + ${((selectedDateRange.startIndex + selectedDateRange.endIndex + 1) / 2 / totalDateCount) * 85}%)`,
                  transform: 'translateX(-50%)'
                }}
              >
                <div className="h-6 w-0.5 bg-gradient-to-b from-emerald-500/0 via-emerald-500 to-emerald-500"></div>
                <div className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-[10px] font-mono flex items-center gap-2 whitespace-nowrap">
                  <ArrowDown size={10} /> 日期范围: {selectedDateRange.start.slice(5)} ~ {selectedDateRange.end.slice(5)}
                </div>
              </div>
            )}
          </div>
        )}
        {/* 占位：当显示连接线时，右侧AI面板区域留空 */}
        {(selectedDrillDate || selectedDateRange) && <div className="hidden xl:block xl:col-span-4"></div>}

        <div ref={drillDownRef} className={`col-span-12 grid grid-cols-12 gap-6 transition-all duration-500 ${(selectedDrillDate || selectedDateRange) ? 'bg-indigo-900/5 p-4 rounded-3xl border border-indigo-500/10' : ''}`}>
          <div className="col-span-12 lg:col-span-6 h-[400px] animate-fade-in-up stagger-2">
            <Suspense fallback={<ChartLoading height={400} />}>
              <CategoryTrendChart
                selectedDate={selectedDrillDate}
                selectedDateRange={selectedDateRange ? { start: selectedDateRange.start, end: selectedDateRange.end } : undefined}
                theme={theme}
              />
            </Suspense>
          </div>
          <div className="col-span-12 lg:col-span-6 h-[400px] animate-fade-in-up stagger-2">
            <Suspense fallback={<ChartLoading height={400} />}>
              <TopProductsChart
                selectedDate={selectedDrillDate}
                selectedDateRange={selectedDateRange ? { start: selectedDateRange.start, end: selectedDateRange.end } : undefined}
                theme={theme}
              />
            </Suspense>
          </div>
        </div>

        {/* Row 3: Hourly Analysis + Distance Analysis (Checkpoint 6 验证) */}
        <div ref={efficiencyRef} className={`col-span-12 xl:col-span-6 h-[450px] animate-enter stagger-7 ${getFocusClass('efficiency')}`}>
          {focusArea === 'efficiency' && <MinimizeAction onExit={() => setFocusArea(null)} />}
          <Suspense fallback={<ChartLoading height={450} />}>
            <HourlyAnalysisChart
              storeName={selectedStore || undefined}
              channel={selectedChannel === 'all' ? undefined : selectedChannel}
              theme={theme}
              selectedDate={selectedDrillDate}
              selectedDateRange={selectedDateRange ? { start: selectedDateRange.start, end: selectedDateRange.end } : undefined}
            />
          </Suspense>
        </div>

        {/* 🆕 分距离订单诊断图表 - Checkpoint 6 验证 */}
        <div className="col-span-12 xl:col-span-6 h-[450px] animate-enter stagger-8">
          <Suspense fallback={<ChartLoading height={450} />}>
            <DistanceAnalysisChart
              storeName={selectedStore || undefined}
              channel={selectedChannel === 'all' ? undefined : selectedChannel}
              theme={theme}
              selectedDate={selectedDrillDate}
              selectedDateRange={selectedDateRange ? { start: selectedDateRange.start, end: selectedDateRange.end } : undefined}
              onDistanceBandSelect={handleDistanceBandSelect}
            />
          </Suspense>
        </div>

        {/* Row 4: 营销成本结构桑基图 + 营销成本趋势图表 */}
        <div ref={costRef} className={`col-span-12 lg:col-span-6 h-[450px] animate-enter stagger-8 ${getFocusClass('cost')}`}>
          {focusArea === 'cost' && <MinimizeAction onExit={() => setFocusArea(null)} />}
          <Suspense fallback={<ChartLoading height={450} />}>
            {marketingStructureLoading ? (
              <div className="glass-panel rounded-2xl p-6 h-full flex items-center justify-center">
                <div className="text-slate-400 text-sm">加载营销成本数据中...</div>
              </div>
            ) : (
              <CostStructureChart data={marketingStructureChannels} theme={theme} />
            )}
          </Suspense>
        </div>
        <div className="col-span-12 lg:col-span-6 h-[450px] animate-enter stagger-9">
          <Suspense fallback={<ChartLoading height={450} />}>
            <MarketingTrendChart
              data={marketingTrendData}
              theme={theme}
              loading={marketingTrendLoading}
              error={marketingTrendError}
              selectedChannel={marketingTrendChannel}
              onChannelChange={setMarketingTrendChannel}
            />
          </Suspense>
        </div>

        {/* Row 5: 配送溢价雷达（全宽） */}
        <div className="col-span-12 h-[450px] animate-enter stagger-10">
          <Suspense fallback={<ChartLoading height={450} />}>
            <DeliveryHeatmap
              theme={theme}
              selectedDistanceBand={selectedDistanceBand}
              storeName={selectedStore || undefined}
              selectedDate={selectedDrillDate}
              selectedDateRange={selectedDateRange ? { start: selectedDateRange.start, end: selectedDateRange.end } : undefined}
            />
          </Suspense>
        </div>

        {/* Row 6: 品类效益矩阵工作台（独享一排，包含趋势图） */}
        <div ref={profitRef} className={`col-span-12 h-[800px] animate-enter stagger-1 ${getFocusClass('profit')}`}>
          {focusArea === 'profit' && <MinimizeAction onExit={() => setFocusArea(null)} />}
          <Suspense fallback={<ChartLoading height={800} />}>
            <CategoryAnalysisChart
              data={data!.channels}
              theme={theme}
            />
          </Suspense>
        </div>

        {/* Row 6: 品类健康度分析表格 */}
        <div className="col-span-12 h-[500px] animate-enter stagger-2">
          <Suspense fallback={<ChartLoading height={500} />}>
            <CategoryHealthTable theme={theme} />
          </Suspense>
        </div>

        {/* Row 7: 营销成本 + 利润模拟器 */}
        <div className="col-span-12 lg:col-span-6 h-[450px] animate-enter stagger-3">
          <Suspense fallback={<ChartLoading height={450} />}>
            <MarketingCostChart data={filteredData.channels} theme={theme} />
          </Suspense>
        </div>
        <div className="col-span-12 lg:col-span-6 h-[450px] animate-enter stagger-4">
          <Suspense fallback={<ChartLoading height={450} />}>
            <ProfitSimulator data={filteredData} />
          </Suspense>
        </div>

        {/* Row 8: Data Table - Uses Filtered Data */}
        <div className={`col-span-12 animate-enter stagger-5 ${focusArea ? 'opacity-20 blur-sm pointer-events-none' : 'opacity-100'}`}>
          <Suspense fallback={<ChartLoading height={400} />}>
            <DataTable data={filteredData.channels} />
          </Suspense>
        </div>

      </div>

      {focusArea && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 glass-panel text-white px-4 py-2 rounded-full shadow-2xl z-[100] animate-bounce">
          <p className="text-xs font-mono font-bold tracking-widest flex items-center gap-2">
            <Minimize2 size={12} /> PRESS ESC TO EXIT
          </p>
        </div>
      )}
    </div>
  );
}

// 主应用组件 - 包含路由
function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // Handle Theme Change
  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
  }, [theme]);

  return (
    <Layout theme={theme} onToggleTheme={() => setTheme(prev => prev === 'dark' ? 'light' : 'dark')}>
      <Routes>
        <Route path="/" element={<Dashboard theme={theme} />} />
        <Route path="/data" element={
          <Suspense fallback={<div className="flex items-center justify-center h-[60vh]">
            <div className="text-slate-400">加载中...</div>
          </div>}>
            <DataManagement />
          </Suspense>
        } />
        <Route path="/stores" element={
          <Suspense fallback={<div className="flex items-center justify-center h-[60vh]">
            <div className="text-slate-400">加载中...</div>
          </div>}>
            <StoreComparisonView theme={theme} />
          </Suspense>
        } />
        <Route path="/channels" element={<ComingSoon title="渠道分析" />} />
        <Route path="/trends" element={<ComingSoon title="趋势洞察" />} />
        <Route path="/settings" element={<ComingSoon title="系统设置" />} />
      </Routes>
    </Layout>
  );
}

// 占位页面
const ComingSoon = ({ title }: { title: string }) => (
  <div className="flex flex-col items-center justify-center h-[60vh] text-center">
    <div className="text-6xl mb-4">🚧</div>
    <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
    <p className="text-slate-400">功能开发中，敬请期待...</p>
  </div>
);

export default App;
