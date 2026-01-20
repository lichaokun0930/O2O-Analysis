/**
 * 库存风险趋势图
 * 
 * 🆕 重构版本 - 解决数据窗口问题
 * 
 * 展示售罄率趋势和滞销率趋势的时间序列变化
 * - 左图：售罄率趋势（红色面积图）
 * - 右图：滞销率趋势（分级堆叠面积图）
 * 
 * 自适应逻辑：
 * - 根据数据量自动决定可展示的滞销等级（轻度7天/中度15天/重度30天）
 * - 趋势起始日 = 数据起始日 + 最高可用等级的回溯天数
 * - 避免数据不足导致的虚假递增趋势
 */

import React, { useEffect, useState, useMemo } from 'react';
import { useChart } from '@/hooks/useChart';
import { useGlobalContext } from '@/store/GlobalContext';
import { inventoryRiskApi } from '@/api/inventoryRisk';
import { AlertTriangle, TrendingDown, Package, RefreshCw, AlertCircle, Info } from 'lucide-react';

// 🆕 新的API返回数据结构
interface TrendDataItem {
  date: string;
  soldOutCount: number;
  soldOutRate: number;
  slowMovingCount: number;
  slowMovingRate: number;
  slowMovingByLevel: Record<string, number>;
  slowMovingRateByLevel: Record<string, number>;
  totalSku: number;
  totalSkuWithStock: number;
}

interface TrendApiResponse {
  success: boolean;
  data: TrendDataItem[];
  availableLevels: string[];
  trendStartDate: string;
  dateRange: { start: string; end: string };
  totalDataDays: number;
  changeSummary?: {
    soldOutRateChange: number;
    slowMovingRateChange: number;
    periodDays: number;
  };
  levelDefinitions: Record<string, string>;
  message?: string;
}

interface Props {
  theme?: 'dark' | 'light';
  height?: number;
}

// 等级颜色配置
const LEVEL_COLORS: Record<string, string> = {
  watch: '#a3e635',   // 青绿色（需关注）
  light: '#fbbf24',   // 黄色
  medium: '#f97316',  // 橙色
  heavy: '#dc2626',   // 红色
};

const LEVEL_LABELS: Record<string, string> = {
  watch: '关注(3天)',
  light: '轻度(7天)',
  medium: '中度(15天)',
  heavy: '重度(30天)',
};

const InventoryRiskTrendChart: React.FC<Props> = ({ theme = 'dark', height = 420 }) => {
  const { selectedStore } = useGlobalContext();
  
  const [trendData, setTrendData] = useState<TrendDataItem[]>([]);
  const [availableLevels, setAvailableLevels] = useState<string[]>([]);
  const [changeSummary, setChangeSummary] = useState<TrendApiResponse['changeSummary'] | null>(null);
  const [totalDataDays, setTotalDataDays] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 获取趋势数据
  useEffect(() => {
    const fetchTrend = async () => {
      if (!selectedStore) {
        setTrendData([]);
        setAvailableLevels([]);
        setChangeSummary(null);
        setError(null);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        console.log('[InventoryRiskTrendChart] 开始获取趋势数据, store:', selectedStore);
        const res = await inventoryRiskApi.getRiskTrend(selectedStore, undefined, 30) as TrendApiResponse;
        console.log('[InventoryRiskTrendChart] API响应:', res);
        
        if (res.success && res.data && res.data.length > 0) {
          setTrendData(res.data);
          setAvailableLevels(res.availableLevels || []);
          setChangeSummary(res.changeSummary || null);
          setTotalDataDays(res.totalDataDays || 0);
          console.log('[InventoryRiskTrendChart] 设置趋势数据:', res.data.length, '条, 可用等级:', res.availableLevels);
        } else {
          setTrendData([]);
          setAvailableLevels(res.availableLevels || []);
          setTotalDataDays(res.totalDataDays || 0);
          const msg = res.message || '暂无趋势数据';
          setError(msg);
          console.log('[InventoryRiskTrendChart] 无数据:', msg);
        }
      } catch (err: any) {
        console.error('[InventoryRiskTrendChart] 获取库存风险趋势失败:', err);
        const errorMsg = err?.response?.data?.detail || err?.message || '获取数据失败，请检查后端服务';
        setError(errorMsg);
        setTrendData([]);
        setAvailableLevels([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTrend();
  }, [selectedStore]);  // 🔧 移除 dateRange 依赖，避免无限循环
  
  // 计算统计摘要
  const summary = useMemo(() => {
    if (trendData.length === 0) return null;
    
    const latest = trendData[trendData.length - 1];
    const first = trendData[0];
    
    return {
      // 售罄
      latestSoldOutRate: latest.soldOutRate,
      latestSoldOutCount: latest.soldOutCount,
      soldOutRateChange: changeSummary?.soldOutRateChange ?? (latest.soldOutRate - first.soldOutRate),
      // 滞销
      latestSlowMovingRate: latest.slowMovingRate,
      latestSlowMovingCount: latest.slowMovingCount,
      slowMovingRateChange: changeSummary?.slowMovingRateChange ?? (latest.slowMovingRate - first.slowMovingRate),
      // 分级
      slowMovingByLevel: latest.slowMovingByLevel,
      slowMovingRateByLevel: latest.slowMovingRateByLevel,
      // 基数
      totalSku: latest.totalSku,
      totalSkuWithStock: latest.totalSkuWithStock
    };
  }, [trendData, changeSummary]);
  
  // 售罄率趋势图配置
  const soldOutOption = useMemo(() => {
    if (trendData.length === 0) return null;
    
    const dates = trendData.map(d => d.date.slice(5));
    const soldOutRates = trendData.map(d => d.soldOutRate);
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis' as const,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: 'rgba(244, 63, 94, 0.3)',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        formatter: (params: any) => {
          const p = params[0];
          const idx = p.dataIndex;
          const item = trendData[idx];
          return `<div class="font-mono text-xs">
            <div class="text-slate-400">${p.axisValue}</div>
            <div class="text-rose-400 font-bold mt-1">售罄率: ${p.value}%</div>
            <div class="text-slate-500 text-[10px] mt-0.5">售罄品: ${item.soldOutCount} / ${item.totalSku} SKU</div>
          </div>`;
        }
      },
      grid: { top: 15, left: 50, right: 15, bottom: 45 },
      xAxis: {
        type: 'category' as const,
        data: dates,
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } },
        axisTick: { show: false },
        axisLabel: { 
          color: '#64748b', 
          fontSize: 10, 
          interval: Math.floor(dates.length / 6),
          rotate: 0,
          margin: 10
        }
      },
      yAxis: {
        type: 'value' as const,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } },
        axisLabel: { 
          color: '#64748b', 
          fontSize: 10,
          formatter: (v: number) => `${v}%`
        }
      },
      series: [{
        type: 'line' as const,
        data: soldOutRates,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3,
        lineStyle: { color: '#f43f5e', width: 2 },
        itemStyle: { color: '#f43f5e' },
        areaStyle: {
          color: {
            type: 'linear' as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(244, 63, 94, 0.4)' },
              { offset: 1, color: 'rgba(244, 63, 94, 0)' }
            ]
          }
        }
      }]
    };
  }, [trendData]);
  
  // 🆕 滞销率趋势图配置（自适应等级）
  const slowMovingOption = useMemo(() => {
    if (trendData.length === 0 || availableLevels.length === 0) return null;
    
    const dates = trendData.map(d => d.date.slice(5));
    
    // 根据可用等级动态生成 series
    const series = availableLevels.map((level) => {
      const data = trendData.map(d => d.slowMovingRateByLevel[level] || 0);
      
      return {
        name: LEVEL_LABELS[level] || level,
        type: 'line' as const,
        stack: 'total',
        data,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 0 },
        areaStyle: {
          color: LEVEL_COLORS[level] || '#94a3b8',
          opacity: 0.8
        },
        emphasis: { focus: 'series' as const }
      };
    }).reverse(); // 反转顺序，让重度在底部
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis' as const,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: 'rgba(249, 115, 22, 0.3)',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        formatter: (params: any) => {
          const date = params[0]?.axisValue || '';
          const idx = params[0]?.dataIndex;
          const item = trendData[idx];
          
          let totalRate = 0;
          let html = `<div class="font-mono text-xs"><div class="text-slate-400 mb-1">${date}</div>`;
          
          // 按等级显示
          availableLevels.forEach(level => {
            const rate = item.slowMovingRateByLevel[level] || 0;
            const count = item.slowMovingByLevel[level] || 0;
            totalRate += rate;
            html += `<div class="flex items-center gap-2 py-0.5">
              <span style="background:${LEVEL_COLORS[level]};width:6px;height:6px;border-radius:1px;"></span>
              <span class="text-slate-400">${LEVEL_LABELS[level]}:</span>
              <span style="color:${LEVEL_COLORS[level]}" class="font-bold">${rate}%</span>
              <span class="text-slate-500">(${count}个)</span>
            </div>`;
          });
          
          html += `<div class="border-t border-white/10 mt-1 pt-1">
            <span class="text-orange-400 font-bold">总滞销率: ${item.slowMovingRate}%</span>
            <span class="text-slate-500 ml-2">(${item.slowMovingCount}/${item.totalSkuWithStock} SKU)</span>
          </div></div>`;
          return html;
        }
      },
      legend: {
        show: true,
        top: 0,
        right: 0,
        textStyle: { color: '#94a3b8', fontSize: 10 },
        itemWidth: 10,
        itemHeight: 6,
        itemGap: 8
      },
      grid: { top: 30, left: 50, right: 15, bottom: 45 },
      xAxis: {
        type: 'category' as const,
        data: dates,
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } },
        axisTick: { show: false },
        axisLabel: { 
          color: '#64748b', 
          fontSize: 10, 
          interval: Math.floor(dates.length / 6),
          rotate: 0,
          margin: 10
        }
      },
      yAxis: {
        type: 'value' as const,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } },
        axisLabel: { 
          color: '#64748b', 
          fontSize: 10,
          formatter: (v: number) => `${v}%`
        }
      },
      series
    };
  }, [trendData, availableLevels]);
  
  // 初始化图表
  const soldOutRef = useChart(soldOutOption || {}, [trendData], theme);
  const slowMovingRef = useChart(slowMovingOption || {}, [trendData, availableLevels], theme);
  
  // 图表区域高度
  const chartHeight = height - 160;
  
  // 无门店选择
  if (!selectedStore) {
    return (
      <div className="glass-panel h-full flex flex-col items-center justify-center text-slate-500">
        <Package size={32} className="mb-2 opacity-50" />
        <p className="text-sm">请先选择门店</p>
      </div>
    );
  }
  
  return (
    <div className="glass-panel h-full flex flex-col">
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-rose-500/20 to-orange-500/20 border border-rose-500/30">
            <TrendingDown size={16} className="text-rose-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">库存风险趋势</h3>
            <p className="text-[10px] text-slate-500 font-mono">
              INVENTORY RISK TREND · {trendData.length > 0 ? `${trendData.length}天趋势` : '加载中...'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 🆕 数据说明提示 */}
          {totalDataDays > 0 && availableLevels.length < 3 && (
            <div className="flex items-center gap-1 px-2 py-1 rounded bg-amber-500/10 border border-amber-500/20">
              <Info size={10} className="text-amber-400" />
              <span className="text-[10px] text-amber-400">
                数据{totalDataDays}天，仅展示{availableLevels.length}个等级
              </span>
            </div>
          )}
          {loading && <RefreshCw size={14} className="text-indigo-400 animate-spin" />}
        </div>
      </div>
      
      {/* 双图表区域 */}
      <div className="flex-1 grid grid-cols-2 gap-4 p-4">
        {/* 售罄率趋势 */}
        <div className="flex flex-col bg-slate-800/30 rounded-xl border border-white/5 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
            <div className="flex items-center gap-2">
              <AlertTriangle size={12} className="text-rose-400" />
              <span className="text-xs font-medium text-white">售罄率趋势</span>
            </div>
            {summary && (
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-rose-400">{summary.latestSoldOutRate}%</span>
                {summary.soldOutRateChange !== 0 && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${summary.soldOutRateChange > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                    {summary.soldOutRateChange > 0 ? '↑' : '↓'}{Math.abs(summary.soldOutRateChange).toFixed(1)}%
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="flex-1 relative">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10">
                <RefreshCw size={20} className="text-indigo-400 animate-spin" />
              </div>
            )}
            {!loading && error && trendData.length === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 p-4">
                <AlertCircle size={20} className="mb-1 opacity-50" />
                <p className="text-[10px] text-center">{error}</p>
              </div>
            )}
            {!loading && !error && trendData.length === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 p-4">
                <Package size={20} className="mb-1 opacity-50" />
                <p className="text-[10px]">暂无数据</p>
              </div>
            )}
            <div ref={soldOutRef} style={{ width: '100%', height: chartHeight }} />
          </div>
        </div>
        
        {/* 滞销率趋势 */}
        <div className="flex flex-col bg-slate-800/30 rounded-xl border border-white/5 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Package size={12} className="text-orange-400" />
              <span className="text-xs font-medium text-white">滞销率趋势</span>
            </div>
            {summary && (
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-orange-400">{summary.latestSlowMovingRate}%</span>
                {summary.slowMovingRateChange !== 0 && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${summary.slowMovingRateChange > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                    {summary.slowMovingRateChange > 0 ? '↑' : '↓'}{Math.abs(summary.slowMovingRateChange).toFixed(1)}%
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="flex-1 relative">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10">
                <RefreshCw size={20} className="text-indigo-400 animate-spin" />
              </div>
            )}
            {!loading && error && trendData.length === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 p-4">
                <AlertCircle size={20} className="mb-1 opacity-50" />
                <p className="text-[10px] text-center">{error}</p>
              </div>
            )}
            {!loading && !error && trendData.length === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 p-4">
                <Package size={20} className="mb-1 opacity-50" />
                <p className="text-[10px]">暂无数据</p>
              </div>
            )}
            <div ref={slowMovingRef} style={{ width: '100%', height: chartHeight }} />
          </div>
        </div>
      </div>
      
      {/* 底部说明区域 - 🆕 分两行显示售罄和滞销的定义 */}
      {summary && (
        <div className="px-4 py-2 border-t border-white/5 space-y-1.5">
          {/* 第一行：售罄定义 */}
          <div className="flex items-center justify-between text-[10px]">
            <div className="flex items-center gap-3">
              <span className="text-slate-500">售罄定义:</span>
              <span className="text-rose-400/80">库存=0 且 近7天有销量</span>
            </div>
            <div className="text-slate-500">
              当前: {summary.latestSoldOutCount} / {summary.totalSku} SKU 售罄 ({summary.latestSoldOutRate}%)
            </div>
          </div>
          
          {/* 第二行：滞销分级 */}
          {availableLevels.length > 0 && (
            <div className="flex items-center justify-between text-[10px]">
              <div className="flex items-center gap-3">
                <span className="text-slate-500">滞销分级:</span>
                {availableLevels.map(level => (
                  <div key={level} className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: LEVEL_COLORS[level] }}></span>
                    <span className="text-slate-400">{LEVEL_LABELS[level]}</span>
                  </div>
                ))}
              </div>
              <div className="text-slate-500">
                当前: {summary.latestSlowMovingCount} / {summary.totalSkuWithStock} SKU 滞销 ({summary.latestSlowMovingRate}%)
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InventoryRiskTrendChart;
