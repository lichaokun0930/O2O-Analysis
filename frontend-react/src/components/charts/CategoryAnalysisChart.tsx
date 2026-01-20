/**
 * 品类效益矩阵工作台
 * 
 * 重构版本：
 * - 左侧：品类树状图（宏观视图）
 * - 右侧：库存风险趋势图（售罄趋势 + 滞销趋势）
 * - 底部：内联展开的商品详情列表
 * - 支持点击趋势图下钻查看具体商品
 */

import React, { useMemo, useCallback, useState, useEffect } from 'react';
import * as echarts from 'echarts';
import { ChannelMetrics, SkuRiskMetric, CategoryMetric } from '@/types';
import { useChart } from '@/hooks/useChart';
import { ArrowLeft, Layers, ZoomIn, BarChart3, RefreshCw, AlertTriangle, Package, ChevronUp, ExternalLink, DollarSign, Clock, Repeat } from 'lucide-react';
import RiskDetailDrawer from '../RiskDetailDrawer';
import { useGlobalContext } from '@/store/GlobalContext';
import { inventoryRiskApi, InventoryRiskTrendItem, SoldOutAnalysis } from '@/api/inventoryRisk';
import { categoryMatrixApi } from '@/api/categoryMatrix';

interface Props {
  data: ChannelMetrics[];
  selectedId?: string | null;
  theme?: 'dark' | 'light';
}

// 内联展开的商品详情类型
interface InlineDetail {
  isOpen: boolean;
  date: string;
  type: 'OUT_OF_STOCK' | 'SLOW_MOVING' | null;
  data: SkuRiskMetric[];
  loading: boolean;
  total: number;
}

const CategoryAnalysisChart: React.FC<Props> = ({ theme = 'dark' }) => {
  const isDark = theme === 'dark';
  const { selectedStore } = useGlobalContext();

  // 品类数据状态
  const [categoryData, setCategoryData] = useState<CategoryMetric[]>([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);

  // 🆕 内部管理的品类选择状态（不再联动外部）
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // 🆕 当前选中的三级分类（用于趋势图联动）
  const [selectedSubCategory, setSelectedSubCategory] = useState<string | null>(null);

  // 趋势数据状态
  const [trendData, setTrendData] = useState<InventoryRiskTrendItem[]>([]);
  const [trendLoading, setTrendLoading] = useState(false);

  // 🆕 售罄分析数据状态
  const [soldOutAnalysis, setSoldOutAnalysis] = useState<SoldOutAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // 内联详情状态
  const [inlineDetail, setInlineDetail] = useState<InlineDetail>({
    isOpen: false, date: '', type: null, data: [], loading: false, total: 0
  });

  // 抽屉状态（查看全部时使用）
  const [drawerState, setDrawerState] = useState<{
    isOpen: boolean;
    itemName: string;
    type: 'OUT_OF_STOCK' | 'SLOW_MOVING' | null;
    data: SkuRiskMetric[];
    loading: boolean;
  }>({ isOpen: false, itemName: '', type: null, data: [], loading: false });

  // 获取品类数据
  useEffect(() => {
    const fetchCategoryData = async () => {
      setDataLoading(true);
      setDataError(null);
      
      try {
        const res = await categoryMatrixApi.getPerformanceWithRisk({
          store_name: selectedStore || undefined,
          parent_category: selectedCategory || undefined
        });
        
        if (res.success && res.data && res.data.length > 0) {
          setCategoryData(res.data);
        } else {
          setCategoryData([]);
          if (res.error) setDataError(res.error);
        }
      } catch (error: any) {
        setCategoryData([]);
        setDataError(error?.message || '获取数据失败');
      } finally {
        setDataLoading(false);
      }
    };

    fetchCategoryData();
  }, [selectedStore, selectedCategory]);

  // 🆕 计算当前用于趋势图筛选的分类（优先三级分类，否则一级分类）
  const currentFilterCategory = selectedSubCategory || selectedCategory;

  // 获取趋势数据 - 🆕 与品类联动（支持一级和三级分类）
  useEffect(() => {
    const fetchTrend = async () => {
      if (!selectedStore) {
        setTrendData([]);
        return;
      }
      
      console.log('[TrendFetch] currentFilterCategory:', currentFilterCategory);
      
      setTrendLoading(true);
      try {
        // 🆕 使用 currentFilterCategory 实现联动
        const res = await inventoryRiskApi.getRiskTrend(selectedStore, currentFilterCategory || undefined, 30);
        console.log('[TrendFetch] API响应:', res);
        if (res.success && res.data) {
          setTrendData(res.data);
        } else {
          setTrendData([]);
        }
      } catch (err) {
        console.error('[TrendFetch] 错误:', err);
        setTrendData([]);
      } finally {
        setTrendLoading(false);
      }
    };
    
    fetchTrend();
  }, [selectedStore, currentFilterCategory]);  // 🆕 使用 currentFilterCategory

  // 🆕 获取售罄分析数据 - 与品类联动（支持一级和三级分类）
  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!selectedStore) {
        setSoldOutAnalysis(null);
        return;
      }
      
      setAnalysisLoading(true);
      try {
        // 🆕 使用 currentFilterCategory 实现联动
        const res = await inventoryRiskApi.getSoldOutAnalysis(selectedStore, currentFilterCategory || undefined, 30);
        if (res.success && res.data) {
          setSoldOutAnalysis(res.data);
        } else {
          setSoldOutAnalysis(null);
        }
      } catch (err) {
        setSoldOutAnalysis(null);
      } finally {
        setAnalysisLoading(false);
      }
    };
    
    fetchAnalysis();
  }, [selectedStore, currentFilterCategory]);  // 🆕 使用 currentFilterCategory

  // 趋势图点击处理 - 内联展开商品列表
  const handleTrendClick = useCallback(async (date: string, type: 'OUT_OF_STOCK' | 'SLOW_MOVING') => {
    // 如果点击同一个，则收起
    if (inlineDetail.isOpen && inlineDetail.date === date && inlineDetail.type === type) {
      setInlineDetail(prev => ({ ...prev, isOpen: false }));
      return;
    }
    
    // 展开并加载数据
    setInlineDetail({ isOpen: true, date, type, data: [], loading: true, total: 0 });
    
    try {
      let products: SkuRiskMetric[] = [];
      let total = 0;
      
      if (type === 'OUT_OF_STOCK') {
        const res = await inventoryRiskApi.getSoldOutProducts(selectedStore || undefined, undefined, 1, 5);
        products = res.data || [];
        total = res.total || 0;
      } else {
        const res = await inventoryRiskApi.getSlowMovingProducts(selectedStore || undefined, undefined, undefined, 1, 5);
        products = res.data || [];
        total = res.total || 0;
      }
      
      setInlineDetail(prev => ({ ...prev, data: products, loading: false, total }));
    } catch (error) {
      setInlineDetail(prev => ({ ...prev, data: [], loading: false, total: 0 }));
    }
  }, [inlineDetail, selectedStore]);

  // 查看全部 - 打开抽屉
  const handleViewAll = useCallback(() => {
    if (!inlineDetail.type) return;
    
    setDrawerState({
      isOpen: true,
      itemName: inlineDetail.date,
      type: inlineDetail.type,
      data: [],
      loading: true
    });
    
    const fetchAll = async () => {
      try {
        let products: SkuRiskMetric[] = [];
        if (inlineDetail.type === 'OUT_OF_STOCK') {
          const res = await inventoryRiskApi.getSoldOutProducts(selectedStore || undefined, undefined, 1, 100);
          products = res.data || [];
        } else {
          const res = await inventoryRiskApi.getSlowMovingProducts(selectedStore || undefined, undefined, undefined, 1, 100);
          products = res.data || [];
        }
        setDrawerState(prev => ({ ...prev, data: products, loading: false }));
      } catch (error) {
        setDrawerState(prev => ({ ...prev, data: [], loading: false }));
      }
    };
    
    fetchAll();
  }, [inlineDetail, selectedStore]);

  const closeDrawer = () => setDrawerState(prev => ({ ...prev, isOpen: false }));

  // 颜色函数
  const getProfitColor = (margin: number) => {
    if (margin >= 0.55) return '#22d3ee';
    if (margin >= 0.45) return '#34d399';
    if (margin >= 0.35) return '#818cf8';
    if (margin >= 0.25) return '#a78bfa';
    if (margin >= 0.15) return '#fbbf24';
    return '#f43f5e';
  };

  // 转换品类数据为图表格式
  const chartData = useMemo(() => {
    if (!categoryData || categoryData.length === 0) return [];
    
    return categoryData.map((item) => {
      const parts = item.name.split('|');
      const displayName = parts.length > 1 ? parts[1] : item.name;
      const marginDecimal = (item.grossMargin || 0) / 100;
      
      return {
        name: displayName,
        fullName: item.name,
        value: item.revenue || 0,
        profit: item.profit || 0,
        orderCount: item.orderCount || 0,
        margin: item.grossMargin || 0,
        marginDecimal,
        soldOut: item.soldOutCount || 0,
        slowMoving: item.slowMovingCount || 0,
        turnover: item.inventoryTurnover || 0,
        itemStyle: {
          color: getProfitColor(marginDecimal),
          borderColor: isDark ? '#0f172a' : '#fff',
          borderWidth: 2,
          gapWidth: 1,
        },
      };
    });
  }, [categoryData, isDark]);
  
  const hasValidData = useMemo(() => {
    return chartData.length > 0 && chartData.some(item => item.value > 0);
  }, [chartData]);

  // 趋势统计摘要 - 🆕 只保留数量，去掉率
  const trendSummary = useMemo(() => {
    if (trendData.length === 0) return null;
    const latest = trendData[trendData.length - 1];
    const first = trendData[0];
    return {
      latestSoldOut: latest.soldOutCount,
      latestSlowMoving: latest.slowMovingCount,
      latestSlowMovingRate: latest.slowMovingRate || 0,
      soldOutChange: latest.soldOutCount - first.soldOutCount,
      slowMovingChange: latest.slowMovingCount - first.slowMovingCount,
      slowMovingRateChange: (latest.slowMovingRate || 0) - (first.slowMovingRate || 0),
      totalSkuWithStock: latest.totalSkuWithStock || 0,
    };
  }, [trendData]);

  // 树状图点击处理 - 🆕 支持一级和三级分类联动
  const handleTreemapClick = useCallback((params: unknown) => {
    const p = params as { name?: string; data?: { fullName?: string } };
    if (!p.name) return;
    
    console.log('[TreemapClick] params:', { name: p.name, fullName: p.data?.fullName, selectedCategory });
    
    if (!selectedCategory) {
      // 当前在一级分类视图，点击进入三级分类
      setSelectedCategory(p.name);
      setSelectedSubCategory(null);  // 清除三级分类选择
    } else {
      // 当前在三级分类视图，点击选中/取消选中三级分类
      const clickedName = p.data?.fullName || p.name;
      console.log('[TreemapClick] 选中三级分类:', clickedName);
      if (selectedSubCategory === clickedName) {
        // 再次点击同一个，取消选中
        setSelectedSubCategory(null);
      } else {
        // 选中新的三级分类
        setSelectedSubCategory(clickedName);
      }
    }
  }, [selectedCategory, selectedSubCategory]);

  // 树状图配置 - 🆕 支持三级分类选中高亮
  const treemapOption: echarts.EChartsOption = useMemo(() => {
    if (!hasValidData) return { series: [] };
    
    // 为选中的项添加高亮样式
    const dataWithHighlight = chartData.map(item => ({
      ...item,
      itemStyle: {
        ...item.itemStyle,
        // 如果是选中的三级分类，添加高亮边框
        borderColor: selectedSubCategory === item.fullName ? '#a855f7' : (isDark ? '#0f172a' : '#fff'),
        borderWidth: selectedSubCategory === item.fullName ? 3 : 2,
      }
    }));
    
    return {
      // 全局动画配置
      animation: true,
      animationDuration: 500,
      animationEasing: 'cubicOut' as const,
      animationDurationUpdate: 500,
      animationEasingUpdate: 'cubicOut' as const,
      tooltip: {
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0,0,0,0.1)',
        textStyle: { fontFamily: 'JetBrains Mono', color: isDark ? '#fff' : '#0f172a' },
        padding: 12,
        formatter: (params: any) => {
          const data = params.data;
          if (!data) return '';
          return `
            <div style="font-weight: bold; margin-bottom: 8px;">${data.name}</div>
            <div>销售额: ¥${(data.value || 0).toLocaleString()}</div>
            <div>利润: ¥${(data.profit || 0).toLocaleString()}</div>
            <div>利润率: ${(data.margin || 0).toFixed(1)}%</div>
            <div>订单数: ${data.orderCount || 0}</div>
            ${data.soldOut > 0 ? `<div style="color:#f43f5e">售罄: ${data.soldOut}个</div>` : ''}
            ${data.slowMoving > 0 ? `<div style="color:#f97316">滞销: ${data.slowMoving}个</div>` : ''}
            ${selectedCategory ? '<div style="color:#a855f7;margin-top:4px;font-size:10px">点击筛选趋势图</div>' : ''}
          `;
        }
      },
      series: [{
        type: 'treemap',
        data: dataWithHighlight,
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        // 动画配置
        animation: true,
        animationDurationUpdate: 500,
        animationEasingUpdate: 'cubicOut' as const,
        label: {
          show: true,
          formatter: (params: any) => {
            const d = params.data;
            let label = `${d.name}\n¥${(d.value/1000).toFixed(0)}k`;
            if (d.soldOut > 0 || d.slowMoving > 0) {
              label += `\n⚠️`;
            }
            // 🆕 选中的项添加标记
            if (selectedSubCategory === d.fullName) {
              label += `\n✓`;
            }
            return label;
          },
          fontSize: 10,
          color: '#fff',
          textShadowBlur: 2,
          textShadowColor: 'rgba(0,0,0,0.5)',
        },
        itemStyle: {
          borderRadius: 4,
          borderColor: isDark ? '#1e293b' : '#fff',
          borderWidth: 2,
        },
      }],
    };
  }, [chartData, isDark, hasValidData, selectedSubCategory, selectedCategory]);

  const treemapRef = useChart(treemapOption, [chartData, isDark, selectedCategory, selectedSubCategory], theme, handleTreemapClick);

  // 售罄趋势图配置 - 🆕 改为显示售罄品数量（去掉率）
  const soldOutOption = useMemo(() => {
    if (trendData.length === 0) return { series: [] };
    
    const dates = trendData.map(d => d.date.slice(5));
    const soldOutCounts = trendData.map(d => d.soldOutCount);
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis' as const,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: 'rgba(244, 63, 94, 0.3)',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        formatter: (params: any) => {
          const p = params[0];
          return `<div class="font-mono text-xs">
            <div class="text-slate-400">${p.axisValue}</div>
            <div class="text-rose-400 font-bold mt-1">售罄品: ${p.value} 个</div>
            <div class="text-slate-500 text-[10px] mt-1">点击查看详情</div>
          </div>`;
        }
      },
      grid: { top: 10, left: 35, right: 10, bottom: 25 },
      xAxis: {
        type: 'category' as const,
        data: dates,
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748b', fontSize: 9, interval: Math.floor(dates.length / 5) }
      },
      yAxis: {
        type: 'value' as const,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } },
        axisLabel: { color: '#64748b', fontSize: 9 }
      },
      series: [{
        type: 'line' as const,
        data: soldOutCounts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#f43f5e', width: 2 },
        itemStyle: { color: '#f43f5e' },
        emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 2, shadowBlur: 10, shadowColor: 'rgba(244,63,94,0.5)' } },
        areaStyle: {
          color: { type: 'linear' as const, x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(244, 63, 94, 0.3)' }, { offset: 1, color: 'rgba(244, 63, 94, 0)' }]
          }
        }
      }]
    };
  }, [trendData]);

  // 售罄趋势图点击
  const handleSoldOutClick = useCallback((params: any) => {
    if (params.dataIndex !== undefined && trendData[params.dataIndex]) {
      const date = trendData[params.dataIndex].date;
      handleTrendClick(date, 'OUT_OF_STOCK');
    }
  }, [trendData, handleTrendClick]);

  const soldOutRef = useChart(soldOutOption, [trendData], theme, handleSoldOutClick);

  // 滞销趋势图配置 - 🆕 适配新的数据结构（自适应等级）
  const slowMovingOption = useMemo(() => {
    if (trendData.length === 0) return { series: [] };
    
    const dates = trendData.map(d => d.date.slice(5));
    
    // 🆕 动态获取可用等级的数据（4级：关注/轻度/中度/重度）
    const watchData = trendData.map(d => d.slowMovingByLevel?.watch || 0);
    const lightData = trendData.map(d => d.slowMovingByLevel?.light || 0);
    const mediumData = trendData.map(d => d.slowMovingByLevel?.medium || 0);
    const heavyData = trendData.map(d => d.slowMovingByLevel?.heavy || 0);
    
    // 🆕 检查哪些等级有数据
    const hasWatch = watchData.some(v => v > 0);
    const hasLight = lightData.some(v => v > 0);
    const hasMedium = mediumData.some(v => v > 0);
    const hasHeavy = heavyData.some(v => v > 0);
    
    // 🆕 动态构建 series（从重到轻，堆叠顺序）
    const series: any[] = [];
    if (hasHeavy) {
      series.push({ name: '重度(30天)', type: 'bar' as const, stack: 'total', data: heavyData, itemStyle: { color: '#dc2626' }, barWidth: '60%' });
    }
    if (hasMedium) {
      series.push({ name: '中度(15天)', type: 'bar' as const, stack: 'total', data: mediumData, itemStyle: { color: '#f97316' } });
    }
    if (hasLight) {
      series.push({ name: '轻度(7天)', type: 'bar' as const, stack: 'total', data: lightData, itemStyle: { color: '#fbbf24' } });
    }
    if (hasWatch) {
      series.push({ name: '关注(3天)', type: 'bar' as const, stack: 'total', data: watchData, itemStyle: { color: '#a3e635', borderRadius: [2, 2, 0, 0] } });
    }
    
    // 如果没有任何数据，返回空配置
    if (series.length === 0) {
      return { series: [] };
    }
    
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
          
          let total = 0;
          let html = `<div class="font-mono text-xs"><div class="text-slate-400 mb-1">${date}</div>`;
          params.forEach((p: any) => {
            total += p.value || 0;
            html += `<div style="display:flex;align-items:center;gap:4px;padding:2px 0">
              <span style="background:${p.color};width:6px;height:6px;border-radius:1px;"></span>
              <span style="color:#94a3b8">${p.seriesName}:</span>
              <span style="color:${p.color};font-weight:bold">${p.value}</span>
            </div>`;
          });
          // 🆕 显示滞销率
          const rate = item?.slowMovingRate || 0;
          html += `<div style="border-top:1px solid rgba(255,255,255,0.1);margin-top:4px;padding-top:4px;color:#f97316;font-weight:bold">合计: ${total} (${rate}%)</div>`;
          html += `<div style="color:#64748b;font-size:10px;margin-top:4px">点击查看详情</div></div>`;
          return html;
        }
      },
      legend: { show: false },
      grid: { top: 10, left: 35, right: 10, bottom: 25 },
      xAxis: {
        type: 'category' as const,
        data: dates,
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748b', fontSize: 9, interval: Math.floor(dates.length / 5) }
      },
      yAxis: {
        type: 'value' as const,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } },
        axisLabel: { color: '#64748b', fontSize: 9 }
      },
      series
    };
  }, [trendData]);

  // 滞销趋势图点击
  const handleSlowMovingClick = useCallback((params: any) => {
    if (params.dataIndex !== undefined && trendData[params.dataIndex]) {
      const date = trendData[params.dataIndex].date;
      handleTrendClick(date, 'SLOW_MOVING');
    }
  }, [trendData, handleTrendClick]);

  const slowMovingRef = useChart(slowMovingOption, [trendData], theme, handleSlowMovingClick);

  return (
    <div className={`glass-panel rounded-2xl p-4 h-full flex flex-col relative overflow-hidden transition-all duration-300 ${selectedCategory ? 'border-purple-500/50 shadow-[0_0_30px_rgba(168,85,247,0.15)]' : ''}`}>
      
      {/* 风险详情抽屉 */}
      <RiskDetailDrawer
        isOpen={drawerState.isOpen}
        onClose={closeDrawer}
        itemName={drawerState.itemName}
        riskType={drawerState.type}
        data={drawerState.data}
        loading={drawerState.loading}
      />

      {/* 头部 */}
      <div className="mb-3 shrink-0 flex justify-between items-start z-20 relative">
        <div className="flex flex-col">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers size={16} className="text-purple-400" />
            品类效益矩阵工作台
          </h3>
          <div className="flex items-center gap-2 mt-0.5 h-5">
            {dataLoading ? (
              <p className="text-[10px] text-indigo-400 font-mono flex items-center gap-1 animate-pulse">
                <RefreshCw size={10} className="animate-spin" /> 加载中...
              </p>
            ) : !selectedCategory ? (
              <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider opacity-70 flex items-center gap-1">
                <ZoomIn size={10} /> 点击树状图下钻 · 点击趋势图查看详情
              </p>
            ) : (
              <div className="flex items-center gap-2 animate-fade-in-up">
                <span className="text-[10px] text-slate-500">ROOT /</span>
                <span className="text-[10px] font-bold text-purple-300 px-1.5 py-0.5 bg-purple-500/10 rounded border border-purple-500/20">
                  {selectedCategory}
                </span>
              </div>
            )}
          </div>
        </div>

        {selectedCategory && (
          <button
            onClick={(e) => { e.stopPropagation(); setSelectedCategory(null); setSelectedSubCategory(null); }}
            className="group flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white text-[10px] font-bold transition-all border border-white/10"
          >
            <ArrowLeft size={12} className="group-hover:-translate-x-1 transition-transform" />
            返回
          </button>
        )}
      </div>

      {/* 错误提示 */}
      {dataError && (
        <div className="mb-2 px-2 py-1.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-[10px] flex items-center gap-2">
          <span>⚠️</span><span>{dataError}</span>
        </div>
      )}

      {/* 主内容区：上下布局 */}
      <div className="flex-1 min-h-0 flex flex-col gap-3 relative z-10">
        
        {/* 上排：Treemap 可视化（占60%高度） */}
        <div className="h-[60%] relative rounded-xl overflow-hidden border border-white/5 bg-slate-950/20 transition-all duration-300">
          <div className="absolute top-2 left-2 z-10 flex items-center gap-1.5 px-1.5 py-0.5 bg-black/40 backdrop-blur-md rounded text-[9px] text-slate-300 font-mono pointer-events-none">
            <BarChart3 size={9} />
            宏观视图
          </div>
          
          <div 
            ref={treemapRef} 
            className={`absolute inset-0 transition-opacity duration-300 ${hasValidData && !dataLoading ? 'opacity-100' : 'opacity-0'}`}
          />
          
          {dataLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <RefreshCw size={20} className="text-indigo-400 animate-spin" />
            </div>
          )}
          
          {!dataLoading && !hasValidData && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 text-xs gap-1 p-4">
              <Layers size={24} className="text-slate-600" />
              <span>{chartData.length === 0 ? '暂无品类数据' : '销售额为0'}</span>
            </div>
          )}
        </div>

        {/* 下排：趋势图区域（占40%高度，左右并排） */}
        <div className="h-[40%] grid grid-cols-2 gap-3">
          {/* 售罄趋势 */}
          <div className="h-full flex flex-col bg-slate-950/20 rounded-xl border border-white/5 overflow-hidden">
            <div className="flex items-center justify-between px-2.5 py-1.5 border-b border-white/5 shrink-0">
              <div className="flex items-center gap-1.5">
                <AlertTriangle size={11} className="text-rose-400" />
                <span className="text-[11px] font-medium text-white">售罄趋势</span>
                {/* 🆕 显示当前筛选品类（优先显示三级分类） */}
                {currentFilterCategory && (
                  <span className="text-[8px] px-1 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 max-w-[80px] truncate" title={currentFilterCategory}>
                    {currentFilterCategory.includes('|') ? currentFilterCategory.split('|').pop() : currentFilterCategory}
                  </span>
                )}
                {/* 售罄定义提示 */}
                <span className="text-[8px] text-slate-500 ml-1" title="库存=0 且 近7天有销量">
                  (库存=0且近7天有销)
                </span>
              </div>
              {trendSummary && (
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold text-rose-400">{trendSummary.latestSoldOut}</span>
                  <span className="text-[9px] text-slate-500">个</span>
                  {trendSummary.soldOutChange !== 0 && (
                    <span className={`text-[9px] px-1 py-0.5 rounded ${trendSummary.soldOutChange > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                      {trendSummary.soldOutChange > 0 ? '↑' : '↓'}{Math.abs(trendSummary.soldOutChange)}
                    </span>
                  )}
                </div>
              )}
            </div>
            <div className="flex-1 relative">
              {trendLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10">
                  <RefreshCw size={16} className="text-indigo-400 animate-spin" />
                </div>
              )}
              <div ref={soldOutRef} className="absolute inset-0" />
            </div>
          </div>

          {/* 滞销趋势 */}
          <div className="h-full flex flex-col bg-slate-950/20 rounded-xl border border-white/5 overflow-hidden">
            <div className="flex items-center justify-between px-2.5 py-1.5 border-b border-white/5 shrink-0">
              <div className="flex items-center gap-1.5">
                <Package size={11} className="text-orange-400" />
                <span className="text-[11px] font-medium text-white">滞销趋势</span>
                {/* 🆕 显示当前筛选品类（优先显示三级分类） */}
                {currentFilterCategory && (
                  <span className="text-[8px] px-1 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 max-w-[80px] truncate" title={currentFilterCategory}>
                    {currentFilterCategory.includes('|') ? currentFilterCategory.split('|').pop() : currentFilterCategory}
                  </span>
                )}
                {/* 图例：关注/轻/中/重 */}
                <div className="flex items-center gap-1 ml-2">
                  <span className="w-1.5 h-1.5 rounded-sm bg-lime-400"></span>
                  <span className="text-[8px] text-slate-500">关注</span>
                  <span className="w-1.5 h-1.5 rounded-sm bg-yellow-400"></span>
                  <span className="text-[8px] text-slate-500">轻</span>
                  <span className="w-1.5 h-1.5 rounded-sm bg-orange-500"></span>
                  <span className="text-[8px] text-slate-500">中</span>
                  <span className="w-1.5 h-1.5 rounded-sm bg-red-600"></span>
                  <span className="text-[8px] text-slate-500">重</span>
                </div>
              </div>
              {trendSummary && (
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold text-orange-400">{trendSummary.latestSlowMoving}</span>
                  <span className="text-[9px] text-slate-500">个</span>
                  {trendSummary.slowMovingChange !== 0 && (
                    <span className={`text-[9px] px-1 py-0.5 rounded ${trendSummary.slowMovingChange > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                      {trendSummary.slowMovingChange > 0 ? '↑' : '↓'}{Math.abs(trendSummary.slowMovingChange)}
                    </span>
                  )}
                </div>
              )}
            </div>
            <div className="flex-1 relative">
              {trendLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10">
                  <RefreshCw size={16} className="text-indigo-400 animate-spin" />
                </div>
              )}
              <div ref={slowMovingRef} className="absolute inset-0" />
            </div>
          </div>
        </div>
      </div>

      {/* 🆕 售罄分析面板 */}
      {soldOutAnalysis && (
        <div className="mt-3 grid grid-cols-4 gap-2">
          {/* 售罄损失金额 */}
          <div className="bg-slate-900/50 rounded-lg border border-white/5 p-2.5">
            <div className="flex items-center gap-1.5 mb-1.5">
              <DollarSign size={12} className="text-rose-400" />
              <span className="text-[10px] text-slate-400">预估损失</span>
            </div>
            <div className="text-lg font-bold text-rose-400">
              ¥{soldOutAnalysis.estimatedLoss.toLocaleString()}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">基于日均销售额</div>
          </div>

          {/* 平均恢复时间 */}
          <div className="bg-slate-900/50 rounded-lg border border-white/5 p-2.5">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Clock size={12} className="text-amber-400" />
              <span className="text-[10px] text-slate-400">平均恢复</span>
            </div>
            <div className="text-lg font-bold text-amber-400">
              {soldOutAnalysis.avgRecoveryDays} <span className="text-xs font-normal">天</span>
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">从售罄到补货</div>
          </div>

          {/* 品类分布 TOP3 */}
          <div className="bg-slate-900/50 rounded-lg border border-white/5 p-2.5">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Layers size={12} className="text-indigo-400" />
              <span className="text-[10px] text-slate-400">品类分布</span>
            </div>
            <div className="space-y-1">
              {soldOutAnalysis.byCategory.slice(0, 3).map((cat, idx) => (
                <div key={cat.category} className="flex items-center justify-between text-[10px]">
                  <span className="text-slate-300 truncate max-w-[80px]" title={cat.category}>
                    {idx + 1}. {cat.category}
                  </span>
                  <span className="text-rose-400 font-mono">{cat.count}个</span>
                </div>
              ))}
              {soldOutAnalysis.byCategory.length === 0 && (
                <div className="text-[10px] text-slate-500">暂无数据</div>
              )}
            </div>
          </div>

          {/* 高频售罄品 TOP3 */}
          <div className="bg-slate-900/50 rounded-lg border border-white/5 p-2.5">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Repeat size={12} className="text-purple-400" />
              <span className="text-[10px] text-slate-400">高频售罄</span>
            </div>
            <div className="space-y-1">
              {soldOutAnalysis.frequentSoldOut.slice(0, 3).map((item, idx) => (
                <div key={item.name} className="flex items-center justify-between text-[10px]">
                  <span className="text-slate-300 truncate max-w-[80px]" title={item.name}>
                    {idx + 1}. {item.name}
                  </span>
                  <span className="text-purple-400 font-mono">{item.times}次</span>
                </div>
              ))}
              {soldOutAnalysis.frequentSoldOut.length === 0 && (
                <div className="text-[10px] text-slate-500">暂无高频售罄</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 售罄分析加载状态 */}
      {analysisLoading && !soldOutAnalysis && (
        <div className="mt-3 flex items-center justify-center py-4 bg-slate-900/30 rounded-lg border border-white/5">
          <RefreshCw size={14} className="text-indigo-400 animate-spin mr-2" />
          <span className="text-[10px] text-slate-400">加载售罄分析...</span>
        </div>
      )}

      {/* 内联展开的商品详情 */}
      {inlineDetail.isOpen && (
        <div className="mt-3 animate-fade-in-up">
          <div className="bg-slate-900/50 rounded-xl border border-white/10 overflow-hidden">
            {/* 详情头部 */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-white/5 bg-slate-800/30">
              <div className="flex items-center gap-2">
                {inlineDetail.type === 'OUT_OF_STOCK' ? (
                  <AlertTriangle size={14} className="text-rose-400" />
                ) : (
                  <Package size={14} className="text-orange-400" />
                )}
                <span className="text-xs font-bold text-white">
                  {inlineDetail.type === 'OUT_OF_STOCK' ? '售罄品详情' : '滞销品详情'}
                </span>
                <span className="text-[10px] text-slate-500">
                  {inlineDetail.date} · 共 {inlineDetail.total} 个
                </span>
              </div>
              <div className="flex items-center gap-2">
                {inlineDetail.total > 5 && (
                  <button
                    onClick={handleViewAll}
                    className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500 hover:text-white transition-all"
                  >
                    查看全部 <ExternalLink size={10} />
                  </button>
                )}
                <button
                  onClick={() => setInlineDetail(prev => ({ ...prev, isOpen: false }))}
                  className="p-1 rounded hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                >
                  <ChevronUp size={14} />
                </button>
              </div>
            </div>
            
            {/* 商品列表 */}
            <div className="p-2">
              {inlineDetail.loading ? (
                <div className="flex items-center justify-center py-4">
                  <RefreshCw size={16} className="text-indigo-400 animate-spin" />
                </div>
              ) : inlineDetail.data.length === 0 ? (
                <div className="text-center py-4 text-slate-500 text-xs">暂无数据</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-2">
                  {inlineDetail.data.slice(0, 5).map((item, idx) => (
                    <div key={item.id || idx} className="flex items-center gap-2 px-2.5 py-2 bg-slate-800/50 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
                      <div className={`w-1.5 h-8 rounded-full ${inlineDetail.type === 'OUT_OF_STOCK' ? 'bg-rose-500' : 'bg-orange-500'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium text-white truncate" title={item.skuName}>{item.skuName}</div>
                        <div className="text-[10px] text-slate-500">{item.reason}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] font-mono text-slate-400">¥{(item.impactValue || 0).toFixed(0)}</div>
                        <div className="text-[9px] text-slate-600">{item.duration || item.action}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryAnalysisChart;
