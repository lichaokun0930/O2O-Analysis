/**
 * 门店效率散点图
 * 
 * 功能：
 * - X轴：营销成本率
 * - Y轴：利润率
 * - 气泡大小：销售额
 * - 四象限分析
 * - 点击交互
 * 
 * 优化点：
 * - 动态坐标轴范围（根据数据分布自动缩放）
 * - 缩小气泡尺寸（8-25px）
 * - 智能标签显示（仅Top5销售额+异常门店显示标签）
 * - 选中状态高亮
 */
import React, { useMemo } from 'react';
import * as echarts from 'echarts';
import type { StoreComparisonData } from '../../types';
import { useChart } from '../../hooks/useChart';
import { Store } from 'lucide-react';

interface StoreEfficiencyScatterProps {
  stores: StoreComparisonData[];
  theme?: 'dark' | 'light';
  loading?: boolean;
  selectedStore?: string | null;
  onStoreClick?: (storeName: string) => void;
}

const StoreEfficiencyScatter: React.FC<StoreEfficiencyScatterProps> = ({
  stores,
  theme = 'dark',
  loading = false,
  selectedStore = null,
  onStoreClick
}) => {
  // 准备数据
  const { chartData, axisRange, topStores, avgMarketingRate, avgProfitMargin } = useMemo(() => {
    if (stores.length === 0) return { 
      chartData: [], 
      axisRange: { xMin: 0, xMax: 25, yMin: 0, yMax: 25 },
      topStores: new Set<string>(),
      avgMarketingRate: 0,
      avgProfitMargin: 0
    };
    
    // 计算平均值用于象限划分
    const avgMR = stores.reduce((sum, s) => sum + s.marketing_cost_rate, 0) / stores.length;
    const avgPM = stores.reduce((sum, s) => sum + s.profit_margin, 0) / stores.length;
    
    // 计算数据范围（动态坐标轴）
    const marketingRates = stores.map(s => s.marketing_cost_rate);
    const profitMargins = stores.map(s => s.profit_margin);
    const minX = Math.min(...marketingRates);
    const maxX = Math.max(...marketingRates);
    const minY = Math.min(...profitMargins);
    const maxY = Math.max(...profitMargins);
    
    // 添加10%边距
    const xPadding = (maxX - minX) * 0.1 || 2;
    const yPadding = (maxY - minY) * 0.1 || 2;
    
    const axisRange = {
      xMin: Math.max(0, Math.floor(minX - xPadding)),
      xMax: Math.ceil(maxX + xPadding),
      yMin: Math.max(0, Math.floor(minY - yPadding)),
      yMax: Math.ceil(maxY + yPadding)
    };
    
    // 找出Top5销售额门店
    const sortedByRevenue = [...stores].sort((a, b) => b.total_revenue - a.total_revenue);
    const top5Stores = new Set(sortedByRevenue.slice(0, 5).map(s => s.store_name));
    
    // 找出异常门店（有anomalies的）
    const anomalyStores = new Set(stores.filter(s => s.anomalies && s.anomalies.length > 0).map(s => s.store_name));
    
    // 合并需要显示标签的门店
    const topStores = new Set([...top5Stores, ...anomalyStores]);
    
    const data = stores.map(s => ({
      name: s.store_name,
      value: [
        s.marketing_cost_rate,  // X轴：营销成本率
        s.profit_margin,        // Y轴：利润率
        s.total_revenue         // 气泡大小：销售额
      ],
      // 是否显示标签
      showLabel: topStores.has(s.store_name) || s.store_name === selectedStore,
      // 根据象限设置颜色，选中状态高亮
      itemStyle: {
        color: s.store_name === selectedStore ? '#818cf8' :  // 选中状态
               s.profit_margin >= avgPM && s.marketing_cost_rate <= avgMR ? '#10b981' :  // 左上：优质门店
               s.profit_margin >= avgPM && s.marketing_cost_rate > avgMR ? '#06b6d4' :   // 右上：潜力门店
               s.profit_margin < avgPM && s.marketing_cost_rate <= avgMR ? '#f59e0b' :   // 左下：改进门店
               '#ef4444',  // 右下：亏损门店
        borderColor: s.store_name === selectedStore ? '#fff' : 'transparent',
        borderWidth: s.store_name === selectedStore ? 2 : 0,
        shadowBlur: s.store_name === selectedStore ? 10 : 0,
        shadowColor: s.store_name === selectedStore ? 'rgba(129, 140, 248, 0.5)' : 'transparent',
        opacity: 0.85
      }
    }));
    
    return { 
      chartData: data, 
      axisRange, 
      topStores,
      avgMarketingRate: avgMR, 
      avgProfitMargin: avgPM 
    };
  }, [stores, selectedStore]);
  
  const option: echarts.EChartsOption = useMemo(() => ({
    title: {
      text: '门店效率分析（营销成本率 vs 利润率）',
      left: 'center',
      top: 10,
      textStyle: {
        color: theme === 'dark' ? '#fff' : '#1e293b',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'rgba(255, 255, 255, 0.2)',
      textStyle: {
        color: '#fff'
      },
      formatter: (params: any) => {
        const data = params.data;
        const store = stores.find(s => s.store_name === data.name);
        if (!store) return '';
        
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${store.store_name}</div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>营销成本率:</span>
              <span style="font-weight: bold;">${store.marketing_cost_rate.toFixed(1)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>利润率:</span>
              <span style="font-weight: bold;">${store.profit_margin.toFixed(1)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>销售额:</span>
              <span style="font-weight: bold;">¥${store.total_revenue.toLocaleString()}</span>
            </div>
          </div>
        `;
      }
    },
    grid: {
      left: '3%',
      right: '7%',
      bottom: '3%',
      top: 60,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '营销成本率 (%)',
      nameLocation: 'middle',
      nameGap: 30,
      min: axisRange.xMin,
      max: axisRange.xMax,
      nameTextStyle: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b',
        fontSize: 12
      },
      axisLabel: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '利润率 (%)',
      nameLocation: 'middle',
      nameGap: 40,
      min: axisRange.yMin,
      max: axisRange.yMax,
      nameTextStyle: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b',
        fontSize: 12
      },
      axisLabel: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        }
      }
    },
    series: [
      {
        type: 'scatter',
        data: chartData,
        symbolSize: (data: any) => {
          // 缩小气泡尺寸：8-25px（原来是10-40px）
          const maxRevenue = Math.max(...stores.map(s => s.total_revenue));
          const minSize = 8;
          const maxSize = 25;
          return minSize + (data[2] / maxRevenue) * (maxSize - minSize);
        },
        label: {
          show: true,
          position: 'top',
          color: theme === 'dark' ? '#fff' : '#1e293b',
          fontSize: 9,
          distance: 5,
          formatter: (params: any) => {
            // 只显示Top5销售额门店 + 异常门店 + 选中门店的标签
            if (params.data.showLabel) {
              // 截取门店名称，避免过长
              const name = params.data.name;
              return name.length > 10 ? name.substring(0, 10) + '...' : name;
            }
            return '';
          }
        },
        emphasis: {
          focus: 'self',
          label: {
            show: true,
            fontSize: 11,
            fontWeight: 'bold',
            formatter: (params: any) => params.data.name
          },
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        }
      },
      // 添加平均线（垂直）
      {
        type: 'line',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: {
            type: 'dashed',
            color: '#6366f1',
            width: 1
          },
          label: {
            show: true,
            position: 'end',
            formatter: '平均营销成本率',
            color: '#6366f1',
            fontSize: 10
          },
          data: [
            { xAxis: avgMarketingRate }
          ]
        }
      },
      // 添加平均线（水平）
      {
        type: 'line',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: {
            type: 'dashed',
            color: '#6366f1',
            width: 1
          },
          label: {
            show: true,
            position: 'end',
            formatter: '平均利润率',
            color: '#6366f1',
            fontSize: 10
          },
          data: [
            { yAxis: avgProfitMargin }
          ]
        }
      }
    ]
  }), [chartData, theme, stores, avgMarketingRate, avgProfitMargin, axisRange]);
  
  // 点击事件处理
  const handleClick = (params: any) => {
    if (params.data?.name && onStoreClick) {
      onStoreClick(params.data.name);
    }
  };
  
  // ✅ 修复：始终渲染 chartRef div，让 useChart 正确初始化
  const chartRef = useChart(option, [chartData, theme, stores, selectedStore], theme, handleClick);
  
  // 判断是否有有效数据
  const hasData = !loading && stores.length > 0 && chartData.length > 0;
  
  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col">
      {/* 图表容器 - 始终渲染，通过 visibility 控制显示 */}
      <div 
        ref={chartRef} 
        className="w-full flex-1" 
        style={{ 
          minHeight: '300px',
          visibility: hasData ? 'visible' : 'hidden',
          position: hasData ? 'relative' : 'absolute'
        }} 
      />
      
      {/* 加载/空数据提示 - 覆盖在图表上方 */}
      {!hasData && (
        <div className="w-full flex-1 flex flex-col items-center justify-center" style={{ minHeight: '300px' }}>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <div className="w-5 h-5 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin" />
              加载中...
            </div>
          ) : (
            <div className="text-center">
              <Store size={40} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400 text-sm mb-1">暂无门店效率数据</p>
              <p className="text-slate-500 text-xs">请调整筛选条件后重试</p>
            </div>
          )}
        </div>
      )}
      
      {/* 象限说明 */}
      <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          <span className="text-slate-400">优质门店（高利润低营销）</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
          <span className="text-slate-400">潜力门店（高利润高营销）</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <span className="text-slate-400">改进门店（低利润低营销）</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-slate-400">亏损门店（低利润高营销）</span>
        </div>
      </div>
    </div>
  );
};

export default StoreEfficiencyScatter;
