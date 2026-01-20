/**
 * 全量门店对比分析视图
 * 
 * 功能：
 * - 独立日期选择器（支持自定义对比周期）
 * - 汇总指标卡片
 * - 门店对比数据表格
 * - 门店排行榜图表
 * - 门店效率散点图
 * - 环比/同比数据展示
 * - 门店筛选（剔除不关注的门店）
 * - 数据导出
 * - 异常门店标识
 * 
 * 优化点：
 * - 修复缓存key依赖问题
 * - 添加加载状态反馈
 * - 渠道筛选后更新门店列表
 * - 支持数据导出
 * - 散点图点击交互
 */
import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { 
  Store, DollarSign, ShoppingBag, Percent, Package, Filter, X, 
  Download, AlertTriangle, Award, Brain
} from 'lucide-react';
import { storeComparisonApi, type StoreComparisonParams } from '../api/storeComparison';
import type { StoreComparisonData, StoreWeekOverWeekData } from '../types';
import { useGlobalContext } from '../store/GlobalContext';
import StatCard from '../components/StatCard';
import StoreComparisonTable from '../components/StoreComparisonTable';
import StoreRankingChart from '../components/charts/StoreRankingChart';
import StoreEfficiencyScatter from '../components/charts/StoreEfficiencyScatter';
import ComparisonDatePicker from '../components/ComparisonDatePicker';
import ChannelDropdown from '../components/ui/ChannelDropdown';
import GlobalInsightsPanel from '../components/GlobalInsightsPanel';

interface StoreComparisonViewProps {
  theme?: 'dark' | 'light';
}

const StoreComparisonView: React.FC<StoreComparisonViewProps> = ({ theme = 'dark' }) => {
  const { storeDateRange, selectedStore } = useGlobalContext();
  
  const [stores, setStores] = useState<StoreComparisonData[]>([]);
  const [weekOverWeekData, setWeekOverWeekData] = useState<StoreWeekOverWeekData[]>([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'revenue' | 'profit' | 'profit_margin' | 'order_count'>('revenue');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // 独立日期选择器状态
  const [currentPeriodStart, setCurrentPeriodStart] = useState<string>('');
  const [currentPeriodEnd, setCurrentPeriodEnd] = useState<string>('');
  
  // 渠道筛选状态
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [availableChannels, setAvailableChannels] = useState<string[]>([]);
  const [channelsLoading, setChannelsLoading] = useState(false);
  
  // 门店筛选状态
  const [excludedStores, setExcludedStores] = useState<string[]>(() => {
    const saved = sessionStorage.getItem('excludedStores');
    return saved ? JSON.parse(saved) : [];
  });
  const [showStoreFilter, setShowStoreFilter] = useState(false);
  const [filteredStoreNames, setFilteredStoreNames] = useState<string[]>([]);
  
  // 导出状态
  const [exporting, setExporting] = useState(false);
  
  // 选中的门店（用于散点图点击交互）
  const [selectedStoreName, setSelectedStoreName] = useState<string | null>(null);
  
  // 全局洞察面板状态
  const [showInsights, setShowInsights] = useState(false);
  
  // 用于防止重复请求的ref
  const lastRequestRef = useRef<string>('');
  
  // 标记是否已初始化
  const isInitializedRef = useRef(false);
  
  // 初始化日期范围
  useEffect(() => {
    if (storeDateRange?.max_date && !isInitializedRef.current) {
      const endDate = new Date(storeDateRange.max_date);
      const startDate = new Date(endDate);
      startDate.setDate(startDate.getDate() - 6);
      
      const newEnd = endDate.toISOString().split('T')[0];
      const newStart = startDate.toISOString().split('T')[0];
      
      setCurrentPeriodEnd(newEnd);
      setCurrentPeriodStart(newStart);
      isInitializedRef.current = true;
      
      // 初始化完成后立即触发数据加载
      console.log('📅 [门店对比] 日期初始化:', newStart, '-', newEnd);
    }
  }, [storeDateRange?.max_date]);
  
  // 计算上期日期范围
  const previousPeriod = useMemo(() => {
    if (!currentPeriodStart || !currentPeriodEnd) {
      return { start: '', end: '' };
    }
    
    const start = new Date(currentPeriodStart);
    const end = new Date(currentPeriodEnd);
    const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    
    const prevEnd = new Date(start);
    prevEnd.setDate(prevEnd.getDate() - 1);
    
    const prevStart = new Date(prevEnd);
    prevStart.setDate(prevStart.getDate() - days + 1);
    
    return {
      start: prevStart.toISOString().split('T')[0],
      end: prevEnd.toISOString().split('T')[0]
    };
  }, [currentPeriodStart, currentPeriodEnd]);
  
  // 加载可用渠道列表（日期变化时触发）
  useEffect(() => {
    if (!currentPeriodStart || !currentPeriodEnd) return;
    
    const loadChannels = async () => {
      setChannelsLoading(true);
      try {
        const res = await storeComparisonApi.getAvailableChannels({
          start_date: currentPeriodStart,
          end_date: currentPeriodEnd
        });
        if (res.success && res.data) {
          setAvailableChannels(res.data);
        }
      } catch (error) {
        console.error('获取可用渠道列表失败:', error);
      } finally {
        setChannelsLoading(false);
      }
    };
    loadChannels();
  }, [currentPeriodStart, currentPeriodEnd]);
  
  // 渠道变化时更新门店列表
  useEffect(() => {
    if (!currentPeriodStart || !currentPeriodEnd) return;
    
    const loadStoresByChannel = async () => {
      try {
        const res = await storeComparisonApi.getStoresByChannel({
          start_date: currentPeriodStart,
          end_date: currentPeriodEnd,
          channel: selectedChannel === 'all' ? undefined : selectedChannel
        });
        if (res.success && res.data) {
          setFilteredStoreNames(res.data);
          // 清除不在新列表中的已剔除门店
          setExcludedStores(prev => prev.filter(s => res.data.includes(s)));
        }
      } catch (error) {
        console.error('获取门店列表失败:', error);
      }
    };
    loadStoresByChannel();
  }, [currentPeriodStart, currentPeriodEnd, selectedChannel]);
  
  // 保存剔除门店到 sessionStorage
  useEffect(() => {
    sessionStorage.setItem('excludedStores', JSON.stringify(excludedStores));
  }, [excludedStores]);
  
  // 过滤掉被剔除的门店
  const filteredStores = useMemo(() => {
    return stores.filter(store => !excludedStores.includes(store.store_name));
  }, [stores, excludedStores]);
  
  // 汇总数据（基于过滤后的门店）
  const summary = useMemo(() => {
    if (filteredStores.length === 0) {
      return {
        total_stores: 0,
        total_orders: 0,
        total_revenue: 0,
        total_profit: 0,
        avg_profit_margin: 0,
        anomaly_count: 0
      };
    }
    
    const total_orders = filteredStores.reduce((sum, s) => sum + s.order_count, 0);
    const total_revenue = filteredStores.reduce((sum, s) => sum + s.total_revenue, 0);
    const total_profit = filteredStores.reduce((sum, s) => sum + s.total_profit, 0);
    // 使用加权平均利润率
    const avg_profit_margin = total_revenue > 0 ? (total_profit / total_revenue * 100) : 0;
    // 统计异常门店数
    const anomaly_count = filteredStores.filter(s => s.anomalies && s.anomalies.length > 0).length;
    
    return {
      total_stores: filteredStores.length,
      total_orders,
      total_revenue,
      total_profit,
      avg_profit_margin,
      anomaly_count
    };
  }, [filteredStores]);
  
  // 加载数据 - 简化依赖，确保首次加载
  const fetchData = useCallback(async () => {
    // 必须有日期才能加载
    if (!currentPeriodStart || !currentPeriodEnd) {
      console.log('⏳ [门店对比] 等待日期初始化...');
      return;
    }
    
    // 计算上期日期（内联计算，避免依赖问题）
    const start = new Date(currentPeriodStart);
    const end = new Date(currentPeriodEnd);
    const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    
    const prevEnd = new Date(start);
    prevEnd.setDate(prevEnd.getDate() - 1);
    
    const prevStart = new Date(prevEnd);
    prevStart.setDate(prevStart.getDate() - days + 1);
    
    const prevStartStr = prevStart.toISOString().split('T')[0];
    const prevEndStr = prevEnd.toISOString().split('T')[0];
    
    // 生成请求标识
    const requestKey = `${currentPeriodStart}-${currentPeriodEnd}-${sortBy}-${sortOrder}-${selectedChannel}`;
    
    // 防止重复请求
    if (lastRequestRef.current === requestKey) {
      console.log('📦 [门店对比] 跳过重复请求');
      return;
    }
    
    lastRequestRef.current = requestKey;
    setLoading(true);
    
    console.log('🔄 [门店对比] 开始加载数据...');
    
    try {
      const params: StoreComparisonParams = {
        sort_by: sortBy,
        sort_order: sortOrder,
        start_date: currentPeriodStart,
        end_date: currentPeriodEnd,
        channel: selectedChannel === 'all' ? undefined : selectedChannel
      };
      
      console.log('🔍 [门店对比] 请求参数:', params);
      
      // 并行获取对比数据和环比数据
      const [comparisonRes, weekOverWeekRes] = await Promise.all([
        storeComparisonApi.getComparison(params),
        storeComparisonApi.getWeekOverWeek(
          currentPeriodEnd, 
          prevStartStr, 
          prevEndStr,
          selectedChannel === 'all' ? undefined : selectedChannel
        )
      ]);
      
      if (comparisonRes.success && comparisonRes.data) {
        console.log('✅ [门店对比] 门店数据:', comparisonRes.data.stores.length, '个门店');
        setStores(comparisonRes.data.stores);
      } else {
        console.warn('⚠️ [门店对比] 无门店数据');
        setStores([]);
      }
      
      if (weekOverWeekRes.success && weekOverWeekRes.data) {
        setWeekOverWeekData(weekOverWeekRes.data.stores);
      }
    } catch (error) {
      console.error('❌ [门店对比] 获取数据失败:', error);
      setStores([]);
    } finally {
      setLoading(false);
    }
  }, [currentPeriodStart, currentPeriodEnd, sortBy, sortOrder, selectedChannel]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // 合并环比数据
  const storesWithComparison = useMemo(() => {
    return filteredStores.map(store => {
      const weekOverWeek = weekOverWeekData.find(w => w.store_name === store.store_name);
      return {
        ...store,
        weekOverWeek: weekOverWeek?.changes
      };
    });
  }, [filteredStores, weekOverWeekData]);
  
  // 门店列表（用于筛选器）
  const allStoreNames = useMemo(() => {
    return filteredStoreNames.length > 0 ? filteredStoreNames : stores.map(s => s.store_name).sort();
  }, [filteredStoreNames, stores]);
  
  // 切换门店选择
  const toggleStoreSelection = (storeName: string) => {
    setExcludedStores(prev => {
      if (prev.includes(storeName)) {
        return prev.filter(s => s !== storeName);
      } else {
        return [...prev, storeName];
      }
    });
  };
  
  // 全选/全不选
  const toggleAllStores = () => {
    if (excludedStores.length === 0) {
      setExcludedStores(allStoreNames);
    } else {
      setExcludedStores([]);
    }
  };
  
  // 应用日期筛选
  const handleApplyDateFilter = (start: string, end: string) => {
    setCurrentPeriodStart(start);
    setCurrentPeriodEnd(end);
    lastRequestRef.current = ''; // 清除请求标识，强制重新加载
  };
  
  // 重置日期筛选
  const handleResetDateFilter = () => {
    if (storeDateRange?.max_date) {
      const endDate = new Date(storeDateRange.max_date);
      const startDate = new Date(endDate);
      startDate.setDate(startDate.getDate() - 6);
      
      setCurrentPeriodEnd(endDate.toISOString().split('T')[0]);
      setCurrentPeriodStart(startDate.toISOString().split('T')[0]);
      lastRequestRef.current = '';
    }
  };
  
  // 导出数据
  const handleExport = async (format: 'json' | 'csv') => {
    setExporting(true);
    try {
      const res = await storeComparisonApi.exportData({
        start_date: currentPeriodStart,
        end_date: currentPeriodEnd,
        channel: selectedChannel === 'all' ? undefined : selectedChannel,
        format
      });
      
      if (res.success && res.data) {
        const { content, filename } = res.data;
        
        if (format === 'csv') {
          // 下载CSV
          const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          link.click();
          URL.revokeObjectURL(url);
        } else {
          // 下载JSON
          const blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          link.click();
          URL.revokeObjectURL(url);
        }
      }
    } catch (error) {
      console.error('导出失败:', error);
    } finally {
      setExporting(false);
    }
  };
  
  // 散点图点击处理
  const handleScatterClick = (storeName: string) => {
    setSelectedStoreName(prev => prev === storeName ? null : storeName);
  };
  
  return (
    <div className="flex flex-col gap-6 w-full">
      {/* 标题和操作区 */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Store size={24} className="text-indigo-400" />
            全量门店对比分析
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            对比所有门店的关键指标，发现优劣势门店
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* 全局洞察按钮 */}
          <button
            onClick={() => setShowInsights(!showInsights)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              showInsights 
                ? 'bg-purple-600 text-white' 
                : 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-400'
            }`}
          >
            <Brain size={14} />
            {showInsights ? '收起洞察' : '🔍 全局洞察'}
          </button>
          
          {/* 导出按钮 */}
          <div className="flex gap-2">
            <button
              onClick={() => handleExport('csv')}
              disabled={exporting || loading || stores.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 
                         text-emerald-400 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              <Download size={14} />
              导出CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              disabled={exporting || loading || stores.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 
                         text-blue-400 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              <Download size={14} />
              导出JSON
            </button>
          </div>
          
          {/* 提示 */}
          {selectedStore && (
            <div className="text-xs text-amber-400 bg-amber-500/10 px-3 py-2 rounded-lg border border-amber-500/20">
              💡 全量门店对比显示所有门店数据，不受顶部门店筛选影响
            </div>
          )}
        </div>
      </div>
      
      {/* 筛选控制区 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 日期选择器 */}
        <ComparisonDatePicker
          currentStart={currentPeriodStart}
          currentEnd={currentPeriodEnd}
          previousStart={previousPeriod.start}
          previousEnd={previousPeriod.end}
          minDate={storeDateRange?.min_date || undefined}
          maxDate={storeDateRange?.max_date || undefined}
          onApply={handleApplyDateFilter}
          onReset={handleResetDateFilter}
        />
        
        {/* 渠道筛选器 */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter size={18} className="text-blue-400" />
            <h3 className="text-sm font-semibold text-white">渠道筛选</h3>
            {channelsLoading && (
              <span className="text-xs text-slate-500 animate-pulse">加载中...</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <ChannelDropdown
              selectedChannel={selectedChannel}
              channelList={availableChannels}
              onSelect={(ch) => {
                setSelectedChannel(ch);
                lastRequestRef.current = ''; // 强制重新加载
              }}
              isDark={theme === 'dark'}
              accentColor="cyan"
            />
            <span className="text-xs text-slate-400 flex-1">
              {selectedChannel === 'all' 
                ? `显示所有渠道 (${availableChannels.length}个)` 
                : `仅显示${selectedChannel}渠道`}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            💡 只显示当前日期范围内有数据的渠道
          </p>
        </div>
        
        {/* 门店筛选器 */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-indigo-400" />
              <h3 className="text-sm font-semibold text-white">
                显示门店 ({filteredStores.length}/{allStoreNames.length})
              </h3>
            </div>
            <button
              onClick={() => setShowStoreFilter(!showStoreFilter)}
              className="text-xs text-indigo-400 hover:text-indigo-300"
            >
              {showStoreFilter ? '收起' : '展开'}
            </button>
          </div>
          
          {showStoreFilter && (
            <div className="space-y-2">
              <div className="flex gap-2 mb-2">
                <button
                  onClick={toggleAllStores}
                  className="text-xs px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors"
                >
                  {excludedStores.length === 0 ? '全部剔除' : '全部恢复'}
                </button>
                {excludedStores.length > 0 && (
                  <span className="text-xs text-amber-400 flex items-center">
                    已剔除 {excludedStores.length} 个门店
                  </span>
                )}
              </div>
              
              <div className="max-h-40 overflow-y-auto space-y-1 bg-slate-900/50 rounded p-2">
                {allStoreNames.map(storeName => (
                  <label
                    key={storeName}
                    className="flex items-center gap-2 px-2 py-1 hover:bg-slate-800 rounded cursor-pointer text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={!excludedStores.includes(storeName)}
                      onChange={() => toggleStoreSelection(storeName)}
                      className="w-4 h-4 text-indigo-600 bg-slate-700 border-slate-600 rounded focus:ring-indigo-500"
                    />
                    <span className={excludedStores.includes(storeName) ? 'text-slate-500 line-through' : 'text-white'}>
                      {storeName}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}
          
          {!showStoreFilter && excludedStores.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {excludedStores.slice(0, 3).map(storeName => (
                <span key={storeName} className="text-xs px-2 py-1 bg-slate-700 text-slate-300 rounded flex items-center gap-1">
                  {storeName}
                  <X size={12} className="cursor-pointer hover:text-white" onClick={() => toggleStoreSelection(storeName)} />
                </span>
              ))}
              {excludedStores.length > 3 && (
                <span className="text-xs px-2 py-1 text-slate-400">
                  +{excludedStores.length - 3} 更多
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 加载状态提示 */}
      {loading && (
        <div className="fixed top-4 right-4 z-50 bg-indigo-600/90 text-white px-4 py-2 rounded-lg 
                        flex items-center gap-2 shadow-lg animate-pulse">
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          正在加载数据...
        </div>
      )}
      
      {/* 初始化加载状态 */}
      {!currentPeriodStart && !currentPeriodEnd && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mb-4" />
          <h3 className="text-lg font-medium text-slate-400 mb-2">正在初始化...</h3>
          <p className="text-sm text-slate-500">正在获取日期范围</p>
        </div>
      )}
      
      {/* 全局洞察面板 */}
      {showInsights && currentPeriodStart && currentPeriodEnd && (
        <GlobalInsightsPanel
          startDate={currentPeriodStart}
          endDate={currentPeriodEnd}
          channel={selectedChannel}
          theme={theme}
        />
      )}
      
      {/* 汇总指标卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard
          title="显示门店数"
          value={summary.total_stores.toString()}
          subtext={excludedStores.length > 0 ? `已剔除 ${excludedStores.length} 个` : '全部门店'}
          icon={<Store size={18} />}
          iconColor="indigo"
          theme={theme}
          loading={loading}
          compact
        />
        <StatCard
          title="总订单量"
          value={summary.total_orders.toLocaleString()}
          subtext="订单"
          icon={<ShoppingBag size={18} />}
          iconColor="cyan"
          theme={theme}
          loading={loading}
          compact
        />
        <StatCard
          title="总销售额"
          value={`¥${summary.total_revenue.toLocaleString()}`}
          subtext="销售额"
          icon={<DollarSign size={18} />}
          iconColor="emerald"
          theme={theme}
          loading={loading}
          compact
        />
        <StatCard
          title="总利润"
          value={`¥${summary.total_profit.toLocaleString()}`}
          subtext="利润"
          icon={<Package size={18} />}
          iconColor="amber"
          theme={theme}
          loading={loading}
          compact
        />
        <StatCard
          title="加权利润率"
          value={`${summary.avg_profit_margin.toFixed(1)}%`}
          subtext="总利润/总销售额"
          icon={<Percent size={18} />}
          iconColor="violet"
          theme={theme}
          loading={loading}
          compact
        />
        <StatCard
          title="异常门店"
          value={summary.anomaly_count.toString()}
          subtext={summary.anomaly_count > 0 ? '需关注' : '运营正常'}
          icon={<AlertTriangle size={18} />}
          iconColor={summary.anomaly_count > 0 ? 'rose' : 'emerald'}
          theme={theme}
          loading={loading}
          compact
        />
      </div>
      
      {/* 图表区域 */}
      <div className="space-y-6">
        {/* 门店排行榜 */}
        <div className="h-[450px]">
          <StoreRankingChart
            stores={filteredStores}
            metric={sortBy}
            theme={theme}
            loading={loading}
          />
        </div>
        
        {/* 门店效率散点图 */}
        <div className="h-[450px]">
          <StoreEfficiencyScatter
            stores={filteredStores}
            theme={theme}
            loading={loading}
            selectedStore={selectedStoreName}
            onStoreClick={handleScatterClick}
          />
        </div>
      </div>
      
      {/* 选中门店详情 */}
      {selectedStoreName && (
        <div className="bg-indigo-900/30 border border-indigo-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Award size={20} className="text-indigo-400" />
              {selectedStoreName} 详情
            </h3>
            <button
              onClick={() => setSelectedStoreName(null)}
              className="text-slate-400 hover:text-white"
            >
              <X size={18} />
            </button>
          </div>
          {(() => {
            const store = filteredStores.find(s => s.store_name === selectedStoreName);
            if (!store) return null;
            
            return (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">订单量</span>
                  <p className="text-white font-medium">{store.order_count.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-slate-400">销售额</span>
                  <p className="text-white font-medium">¥{store.total_revenue.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-slate-400">利润</span>
                  <p className="text-white font-medium">¥{store.total_profit.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-slate-400">利润率</span>
                  <p className={`font-medium ${
                    store.profit_margin >= 30 ? 'text-emerald-400' :
                    store.profit_margin >= 20 ? 'text-cyan-400' :
                    store.profit_margin >= 10 ? 'text-amber-400' : 'text-red-400'
                  }`}>{store.profit_margin.toFixed(1)}%</p>
                </div>
                <div>
                  <span className="text-slate-400">客单价</span>
                  <p className="text-white font-medium">¥{store.aov.toFixed(1)}</p>
                </div>
                <div>
                  <span className="text-slate-400">单均配送费</span>
                  <p className="text-white font-medium">¥{store.avg_delivery_fee.toFixed(1)}</p>
                </div>
                <div>
                  <span className="text-slate-400">单均营销费</span>
                  <p className="text-white font-medium">¥{store.avg_marketing_cost.toFixed(1)}</p>
                </div>
                
                {/* 异常提示 */}
                {store.anomalies && store.anomalies.length > 0 && (
                  <div className="col-span-full mt-2 space-y-1">
                    {store.anomalies.map((anomaly, idx) => (
                      <div 
                        key={idx}
                        className={`text-xs px-3 py-1.5 rounded flex items-center gap-2 ${
                          anomaly.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                          anomaly.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}
                      >
                        <AlertTriangle size={12} />
                        {anomaly.message}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}
      
      {/* 数据表格 */}
      <div>
        <StoreComparisonTable
          stores={storesWithComparison}
          theme={theme}
          loading={loading}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSort={(field, order) => {
            setSortBy(field);
            setSortOrder(order);
            lastRequestRef.current = ''; // 强制重新加载
          }}
          onStoreClick={setSelectedStoreName}
        />
      </div>
      
      {/* 空状态 */}
      {!loading && stores.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Store size={48} className="text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400 mb-2">暂无门店数据</h3>
          <p className="text-sm text-slate-500 max-w-md">
            当前筛选条件下没有找到门店数据。请尝试调整日期范围或渠道筛选条件。
          </p>
          <button
            onClick={handleResetDateFilter}
            className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition-colors"
          >
            重置筛选条件
          </button>
        </div>
      )}
    </div>
  );
};

export default StoreComparisonView;
