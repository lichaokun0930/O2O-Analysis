/**
 * 营销成本趋势图表组件
 * 
 * 功能：
 * - 百分比堆叠面积图展示各营销类型占比随时间的变化趋势
 * - 支持绝对值/百分比视图切换
 * - 复用桑基图的颜色配置
 * - 过滤全零营销类型
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 5.2, 5.3, 5.4
 */
import React, { useMemo, useState } from 'react';
import * as echarts from 'echarts';
import { MarketingTrendData, MarketingTrendSeries } from '@/types';
import { useChart } from '@/hooks/useChart';
import { useGlobalContext } from '@/store/GlobalContext';
import ChannelDropdown from '@/components/ui/ChannelDropdown';

interface Props {
  data: MarketingTrendData | null;
  theme: 'dark' | 'light';
  loading?: boolean;
  error?: string | null;
  selectedChannel: string;      // 当前选中渠道
  onChannelChange: (channel: string) => void;  // 渠道切换回调
}

// 视图模式类型
export type ViewMode = 'percentage' | 'absolute';

// 营销类型字段映射（7个营销字段，不含配送费减免金额）
// 配送费减免金额属于配送成本，不属于营销成本
export const MARKETING_FIELD_MAPPING: [keyof MarketingTrendSeries, string][] = [
  ['full_reduction', '满减金额'],
  ['product_discount', '商品减免'],
  ['merchant_voucher', '商家代金券'],
  ['merchant_share', '商家承担券'],
  ['gift_amount', '满赠金额'],
  ['other_discount', '商家其他优惠'],
  ['new_customer_discount', '新客减免'],
];

// 营销类型颜色配置（7个营销字段）
export const MARKETING_TYPE_COLORS: Record<string, string> = {
  '满减金额': '#f59e0b',
  '商品减免': '#eab308',
  '商家代金券': '#22c55e',
  '商家承担券': '#14b8a6',
  '满赠金额': '#3b82f6',
  '商家其他优惠': '#8b5cf6',
  '新客减免': '#ec4899',
};

/**
 * 过滤全零营销类型
 * Property 4: 零值类型过滤
 * Validates: Requirements 2.6
 */
export function filterZeroTypes(
  series: MarketingTrendSeries
): [keyof MarketingTrendSeries, string][] {
  return MARKETING_FIELD_MAPPING.filter(([field]) => {
    const values = series[field];
    return values && values.some(v => v > 0);
  });
}

/**
 * 计算百分比数据
 * Property 5: 百分比计算正确性
 * Validates: Requirements 3.3
 */
export function calculatePercentages(
  values: number[],
  totals: number[]
): number[] {
  return values.map((v, i) => {
    const total = totals[i];
    if (total === 0) return 0;
    return (v / total) * 100;
  });
}

/**
 * 转换为ECharts堆叠面积图配置
 */
export function transformToStackedAreaData(
  data: MarketingTrendData,
  viewMode: ViewMode,
  isDark: boolean
): echarts.EChartsOption {
  const { dates, series, totals } = data;
  
  // 过滤全零营销类型
  const activeTypes = filterZeroTypes(series);
  
  // 构建ECharts series
  const echartsSeries: echarts.SeriesOption[] = activeTypes.map(([field, displayName]) => {
    const values = series[field] || [];
    
    // 根据视图模式计算显示值
    const displayValues = viewMode === 'percentage'
      ? calculatePercentages(values, totals)
      : values;
    
    return {
      name: displayName,
      type: 'line',
      stack: 'total',
      areaStyle: { opacity: 0.6 },
      emphasis: { focus: 'series' },
      data: displayValues,
      itemStyle: { color: MARKETING_TYPE_COLORS[displayName] },
      lineStyle: { width: 1 },
      symbol: 'none',
      smooth: 0.3,
    };
  });
  
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const splitLineColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
  
  return {
    grid: { top: 40, right: 20, bottom: 60, left: 50, containLabel: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0,0,0,0.1)',
      padding: 12,
      textStyle: { fontFamily: 'JetBrains Mono', color: isDark ? '#fff' : '#0f172a', fontSize: 11 },
      axisPointer: { type: 'cross', label: { backgroundColor: '#6366f1' } },
      formatter: (params: any) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const date = params[0].axisValue;
        let result = `<div style="font-weight:bold;margin-bottom:8px">${date}</div>`;
        
        // 计算当日总额
        const dayIndex = dates.indexOf(date);
        const dayTotal = dayIndex >= 0 ? totals[dayIndex] : 0;
        
        params.forEach((item: any) => {
          const value = item.value || 0;
          const percentage = dayTotal > 0 ? ((value / (viewMode === 'percentage' ? 100 : dayTotal)) * 100) : 0;
          
          if (viewMode === 'percentage') {
            result += `<div style="display:flex;justify-content:space-between;gap:16px">
              <span>${item.marker}${item.seriesName}</span>
              <span style="font-weight:bold">${value.toFixed(1)}%</span>
            </div>`;
          } else {
            result += `<div style="display:flex;justify-content:space-between;gap:16px">
              <span>${item.marker}${item.seriesName}</span>
              <span style="font-weight:bold">¥${value.toLocaleString()} (${percentage.toFixed(1)}%)</span>
            </div>`;
          }
        });
        
        if (viewMode === 'absolute') {
          result += `<div style="margin-top:8px;padding-top:8px;border-top:1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}">
            <span style="font-weight:bold">总计: ¥${dayTotal.toLocaleString()}</span>
          </div>`;
        }
        
        return result;
      }
    },
    legend: {
      data: activeTypes.map(([, name]) => name),
      bottom: 0,
      textStyle: { color: axisColor, fontSize: 10 },
      itemGap: 12,
      icon: 'roundRect',
      itemWidth: 12,
      itemHeight: 8
    },
    xAxis: {
      type: 'category',
      data: dates.map(d => d.slice(5)), // 只显示月-日
      boundaryGap: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: axisColor, fontSize: 10, fontFamily: 'JetBrains Mono' }
    },
    yAxis: {
      type: 'value',
      max: viewMode === 'percentage' ? 100 : undefined,
      splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } },
      axisLabel: {
        color: axisColor,
        fontSize: 10,
        formatter: viewMode === 'percentage' ? '{value}%' : (val: number) => `¥${val >= 1000 ? (val/1000).toFixed(0) + 'k' : val}`
      }
    },
    series: echartsSeries,
  };
}

const MarketingTrendChart: React.FC<Props> = ({ 
  data, 
  theme, 
  loading, 
  error,
  selectedChannel,
  onChannelChange
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('percentage');
  const { channelList } = useGlobalContext();  // 直接从全局获取渠道列表
  
  // 调试日志
  console.log('📈 MarketingTrendChart channelList:', channelList);
  
  const isDark = theme === 'dark';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';

  // 生成ECharts配置
  const option = useMemo<echarts.EChartsOption>(() => {
    console.log('📈 MarketingTrendChart option 计算, data:', data);
    if (!data || !data.dates || data.dates.length === 0) {
      console.log('📈 MarketingTrendChart - 无数据，返回空 series');
      return {
        series: []
      };
    }
    const result = transformToStackedAreaData(data, viewMode, isDark);
    console.log('📈 MarketingTrendChart option 结果:', {
      seriesCount: (result.series as any[])?.length,
      xAxisData: (result.xAxis as any)?.data?.length,
      firstSeriesName: (result.series as any[])?.[0]?.name,
      firstSeriesDataSample: (result.series as any[])?.[0]?.data?.slice(0, 3)
    });
    return result;
  }, [data, viewMode, isDark]);

  // 🔧 使用空数组作为额外依赖，因为 option 已经包含了所有依赖
  // 这样可以避免重复触发 useEffect
  const chartRef = useChart(option, [], theme);

  // 🔧 始终渲染图表容器，避免 loading 状态切换时丢失 chartRef
  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-b from-pink-500/5 to-transparent pointer-events-none"></div>

      <div className="mb-2 flex justify-between items-start relative z-10">
        <div>
          <h3 className="text-lg font-bold flex items-center gap-2" style={{color: titleColor}}>
            <span className="w-1 h-5 bg-gradient-to-b from-pink-400 to-pink-600 rounded-full shadow-[0_0_10px_#ec4899]"></span>
            营销成本趋势
          </h3>
          <p className="text-xs mt-1 font-mono uppercase tracking-widest opacity-70" style={{color: subTitleColor}}>
            MARKETING COST TREND: TYPE RATIO OVER TIME
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* 渠道选择器 - 复用共享组件 */}
          <ChannelDropdown
            selectedChannel={selectedChannel}
            channelList={channelList}
            onSelect={onChannelChange}
            isDark={isDark}
            accentColor="pink"
          />
          
          {/* 视图切换按钮 */}
          <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
            <button
              onClick={() => setViewMode('percentage')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all duration-200 ${
                viewMode === 'percentage'
                  ? 'bg-pink-500/20 text-pink-300 shadow-[0_0_10px_rgba(236,72,153,0.3)]'
                  : isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              百分比
            </button>
            <button
              onClick={() => setViewMode('absolute')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all duration-200 ${
                viewMode === 'absolute'
                  ? 'bg-pink-500/20 text-pink-300 shadow-[0_0_10px_rgba(236,72,153,0.3)]'
                  : isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              绝对值
            </button>
          </div>
        </div>
      </div>
      
      <div className="flex-1 w-full min-h-[280px] relative">
        {/* 图表容器 - 始终渲染 */}
        <div ref={chartRef} className="w-full h-full" style={{ minHeight: '280px' }} />
        
        {/* 加载状态覆盖层 */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm rounded-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500"></div>
          </div>
        )}
        
        {/* 错误状态覆盖层 */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm rounded-lg">
            <p className="text-rose-400 text-sm">{error}</p>
          </div>
        )}
        
        {/* 无数据状态 */}
        {!loading && !error && (!data || !data.dates || data.dates.length === 0) && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-slate-500 text-sm">暂无数据，请选择门店</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketingTrendChart;
