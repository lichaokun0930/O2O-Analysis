/**
 * 门店排行榜图表
 * 
 * 功能：
 * - 柱状图展示门店排名
 * - 支持切换指标（销售额/利润/订单量）
 * - 颜色根据利润率分级
 */
import React, { useMemo } from 'react';
import * as echarts from 'echarts';
import type { StoreComparisonData } from '../../types';
import { useChart } from '../../hooks/useChart';

interface StoreRankingChartProps {
  stores: StoreComparisonData[];
  metric: 'revenue' | 'profit' | 'profit_margin' | 'order_count';
  theme?: 'dark' | 'light';
  loading?: boolean;
}

const StoreRankingChart: React.FC<StoreRankingChartProps> = ({
  stores,
  metric,
  theme = 'dark',
  loading = false
}) => {
  // 准备数据
  const chartData = useMemo(() => {
    if (stores.length === 0) return { names: [], values: [], colors: [] };
    
    // 取前10名
    const topStores = stores.slice(0, 10);
    
    const names = topStores.map(s => s.store_name);
    const values = topStores.map(s => {
      switch (metric) {
        case 'revenue': return s.total_revenue;
        case 'profit': return s.total_profit;
        case 'profit_margin': return s.profit_margin;
        case 'order_count': return s.order_count;
        default: return s.total_revenue;
      }
    });
    
    // 根据利润率设置颜色
    const colors = topStores.map(s => {
      if (s.profit_margin >= 30) return '#10b981'; // 绿色
      if (s.profit_margin >= 20) return '#06b6d4'; // 青色
      if (s.profit_margin >= 10) return '#f59e0b'; // 橙色
      return '#ef4444'; // 红色
    });
    
    return { names, values, colors };
  }, [stores, metric]);
  
  const metricLabels = {
    revenue: '销售额',
    profit: '利润',
    profit_margin: '利润率',
    order_count: '订单量'
  };
  
  const metricUnits = {
    revenue: '元',
    profit: '元',
    profit_margin: '%',
    order_count: '单'
  };
  
  const option: echarts.EChartsOption = useMemo(() => ({
    title: {
      text: `门店${metricLabels[metric]}排行榜 Top 10`,
      left: 'center',
      top: 10,
      textStyle: {
        color: theme === 'dark' ? '#fff' : '#1e293b',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'rgba(255, 255, 255, 0.2)',
      textStyle: {
        color: '#fff'
      },
      formatter: (params: any) => {
        const data = params[0];
        const store = stores.find(s => s.store_name === data.name);
        if (!store) return '';
        
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${store.store_name}</div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>销售额:</span>
              <span style="font-weight: bold;">¥${store.total_revenue.toLocaleString()}</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>利润:</span>
              <span style="font-weight: bold;">¥${store.total_profit.toLocaleString()}</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>利润率:</span>
              <span style="font-weight: bold;">${store.profit_margin.toFixed(1)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 16px;">
              <span>订单量:</span>
              <span style="font-weight: bold;">${store.order_count.toLocaleString()}单</span>
            </div>
          </div>
        `;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 60,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.names,
      axisLabel: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b',
        rotate: 45,
        fontSize: 11
      },
      axisLine: {
        lineStyle: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: metricUnits[metric],
      nameTextStyle: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b'
      },
      axisLabel: {
        color: theme === 'dark' ? '#94a3b8' : '#64748b',
        formatter: (value: number) => {
          if (metric === 'profit_margin') return value.toFixed(0);
          if (value >= 10000) return (value / 10000).toFixed(1) + 'w';
          return value.toLocaleString();
        }
      },
      splitLine: {
        lineStyle: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: chartData.values.map((value, index) => ({
          value,
          itemStyle: {
            color: chartData.colors[index]
          }
        })),
        barWidth: '60%',
        label: {
          show: true,
          position: 'top',
          color: theme === 'dark' ? '#fff' : '#1e293b',
          fontSize: 10,
          formatter: (params: any) => {
            const value = params.value;
            if (metric === 'profit_margin') return value.toFixed(1) + '%';
            if (value >= 10000) return (value / 10000).toFixed(1) + 'w';
            return value.toLocaleString();
          }
        }
      }
    ]
  }), [chartData, metric, theme, stores, metricLabels, metricUnits]);
  
  // ✅ 修复：始终渲染 chartRef div，让 useChart 正确初始化
  const chartRef = useChart(option, [chartData, metric, theme, stores], theme);
  
  // 判断是否有有效数据
  const hasData = !loading && stores.length > 0 && chartData.names.length > 0;
  
  return (
    <div className="glass-panel rounded-2xl p-6 h-full">
      {/* 图表容器 - 始终渲染，通过 visibility 控制显示 */}
      <div 
        ref={chartRef} 
        className="w-full h-full" 
        style={{ 
          minHeight: '350px',
          visibility: hasData ? 'visible' : 'hidden',
          position: hasData ? 'relative' : 'absolute'
        }} 
      />
      
      {/* 加载/空数据提示 - 覆盖在图表上方 */}
      {!hasData && (
        <div className="w-full h-full flex flex-col items-center justify-center" style={{ minHeight: '350px' }}>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <div className="w-5 h-5 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin" />
              加载中...
            </div>
          ) : (
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-3 bg-slate-800 rounded-lg flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
              <p className="text-slate-400 text-sm mb-1">暂无排行榜数据</p>
              <p className="text-slate-500 text-xs">请调整筛选条件后重试</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StoreRankingChart;
