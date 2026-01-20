import React, { useMemo } from 'react';
import * as echarts from 'echarts';
import { ChannelMetrics, MarketingDailyBreakdown } from '@/types';
import { useChart } from '@/hooks/useChart';

interface Props {
  data: ChannelMetrics[];
  selectedId?: string | null;
  theme: 'dark' | 'light';
}

const MarketingCostChart: React.FC<Props> = ({ data, theme }) => {
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';
  const splitLineColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

  const { categories, series } = useMemo(() => {
    const aggregatedData: Record<string, MarketingDailyBreakdown> = {};
    const sourceChannels = data;

    if (sourceChannels.length > 0 && sourceChannels[0].marketingTrend) {
      sourceChannels[0].marketingTrend.forEach(d => {
        aggregatedData[d.date] = { date: d.date, itemDiscount: 0, thresholdDiscount: 0, vouchers: 0, other: 0 };
      });
    }

    sourceChannels.forEach(c => {
      c.marketingTrend?.forEach(d => {
        if (aggregatedData[d.date]) {
          aggregatedData[d.date].itemDiscount += d.itemDiscount;
          aggregatedData[d.date].thresholdDiscount += d.thresholdDiscount;
          aggregatedData[d.date].vouchers += d.vouchers;
          aggregatedData[d.date].other += d.other;
        }
      });
    });

    const dates = Object.keys(aggregatedData);
    
    return {
      categories: dates,
      series: [
        { name: '单品直降', data: dates.map(d => aggregatedData[d].itemDiscount), color: '#f43f5e' },
        { name: '满减活动', data: dates.map(d => aggregatedData[d].thresholdDiscount), color: '#f59e0b' },
        { name: '红包/券', data: dates.map(d => aggregatedData[d].vouchers), color: '#3b82f6' },
        { name: '推广/广告', data: dates.map(d => aggregatedData[d].other), color: '#8b5cf6' }
      ]
    };
  }, [data]);

  const option: echarts.EChartsOption = {
    grid: { top: 30, right: 10, bottom: 0, left: 10, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0,0,0,0.1)',
      padding: 12,
      textStyle: { fontFamily: 'JetBrains Mono', color: isDark ? '#fff' : '#0f172a' },
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['单品直降', '满减活动', '红包/券', '推广/广告'],
      textStyle: { color: axisColor, fontSize: 10 },
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: axisColor, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } },
      axisLabel: { color: axisColor, fontSize: 10, formatter: (val: number) => `¥${val/1000}k` }
    },
    series: series.map(s => ({
      name: s.name,
      type: 'bar',
      stack: 'total',
      data: s.data,
      itemStyle: { color: s.color },
      barWidth: '40%'
    }))
  };

  const chartRef = useChart(option, [data, theme], theme);

  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col relative overflow-hidden">
      <div className="mb-4 relative z-10">
        <h3 className="text-lg font-bold flex items-center gap-2" style={{color: titleColor}}>
          <span className="w-1 h-4 bg-gradient-to-b from-rose-400 to-rose-600 rounded-sm"></span>
          营销成本趋势
        </h3>
        <p className="text-xs mt-1 font-mono uppercase tracking-wider opacity-70" style={{color: subTitleColor}}>
          7-DAY COST BREAKDOWN
        </p>
      </div>
      
      <div className="flex-1 w-full min-h-[250px]">
        <div ref={chartRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default MarketingCostChart;
