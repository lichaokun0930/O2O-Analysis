import React, { useEffect, useState, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { ordersApi, HourlyProfitData } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';

interface Props {
  storeName?: string;
  channel?: string;
  theme: 'dark' | 'light';
  selectedDate?: string | null;  // 🆕 联动：从销售趋势图选中的日期
  selectedDateRange?: { start: string; end: string } | null;  // 🆕 日期范围选择
}

const CostEfficiencyChart: React.FC<Props> = ({ storeName, channel, theme, selectedDate, selectedDateRange }) => {
  const [data, setData] = useState<HourlyProfitData | null>(null);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  
  // 🆕 获取全局日期范围
  const { dateRange } = useGlobalContext();
  
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';
  const splitLineColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

  // 🆕 直接使用 selectedDate，后端已支持 MM-DD 格式
  const targetDate = selectedDate || undefined;

  // 加载数据
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // 🆕 构建请求参数：优先使用下钻日期/日期范围
        const params: {
          store_name?: string;
          channel?: string;
          target_date?: string;
          start_date?: string;
          end_date?: string;
        } = {
          store_name: storeName,
          channel: channel,
        };
        
        if (targetDate) {
          // 销售趋势图下钻的单日期
          params.target_date = targetDate;
        } else if (selectedDateRange) {
          // 🆕 销售趋势图下钻的日期范围
          params.start_date = selectedDateRange.start;
          params.end_date = selectedDateRange.end;
        } else if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
          // 全局日期范围（顶部日期选择器）
          params.start_date = dateRange.start;
          params.end_date = dateRange.end;
        }
        
        // 🔍 调试日志
        console.log('📊 分时段诊断请求参数:', params, '| dateRange:', dateRange);
        
        const res = await ordersApi.getHourlyProfit(params);
        if (res.success && res.data) {
          setData(res.data);
          console.log('📊 分时段诊断返回数据:', res.data.date);
        }
      } catch (err) {
        console.error('获取分时利润数据失败:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [storeName, channel, targetDate, selectedDateRange, dateRange.type, dateRange.start, dateRange.end]);

  // 初始化和更新图表
  useEffect(() => {
    if (!chartRef.current || !data) return;

    // 初始化图表
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
    }

    const { hours, orders, profits, avg_profits, peak_periods } = data;

    // 生成高峰时段的背景区域数据
    const peakMarkAreaData = peak_periods && peak_periods.length > 0 
      ? peak_periods.map(peak => [
          { 
            xAxis: hours[peak.start_hour] || `${peak.start_hour}:00`,
            itemStyle: { color: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)' }
          },
          { xAxis: hours[Math.min(peak.end_hour + 1, 23)] || `${peak.end_hour + 1}:00` }
        ])
      : [];

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      grid: { top: 35, right: 45, bottom: 25, left: 40, containLabel: true },
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0,0,0,0.1)',
        padding: 16,
        textStyle: { fontFamily: 'JetBrains Mono', color: isDark ? '#fff' : '#0f172a', fontSize: 12 },
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const hour = params[0]?.axisValue || '';
          let html = `<div style="font-weight:600;margin-bottom:8px;font-size:13px">${hour}</div>`;
          
          params.forEach((p: any) => {
            const value = p.value;
            const color = p.seriesName === '净利润' 
              ? (value >= 0 ? '#22c55e' : '#f43f5e')
              : p.color;
            
            html += `<div style="display:flex;justify-content:space-between;align-items:center;margin:4px 0">
              <span style="display:flex;align-items:center;gap:6px">
                <span style="width:8px;height:8px;border-radius:50%;background:${color}"></span>
                ${p.seriesName}
              </span>
              <span style="font-weight:600;margin-left:20px">${
                p.seriesName === '净利润' ? `¥${value.toFixed(2)}` : value
              }</span>
            </div>`;
          });
          
          // 添加单均利润
          const hourIndex = hours.indexOf(hour);
          if (hourIndex >= 0 && orders[hourIndex] > 0) {
            const avgProfit = avg_profits[hourIndex];
            const avgColor = avgProfit >= 0 ? '#22c55e' : '#f43f5e';
            html += `<div style="border-top:1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'};margin-top:8px;padding-top:8px">
              <span style="color:${isDark ? '#94a3b8' : '#64748b'}">单均利润:</span>
              <span style="font-weight:600;color:${avgColor};margin-left:8px">¥${avgProfit.toFixed(2)}</span>
            </div>`;
          }
          
          return html;
        }
      },
      legend: {
        data: ['订单数', '净利润'],
        top: 2,
        right: 5,
        textStyle: { color: axisColor, fontSize: 10 },
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 12,
        itemStyle: {
          // 订单数用紫色，净利润用绿色
        }
      },
      xAxis: {
        type: 'category',
        data: hours,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { 
          color: axisColor, 
          fontSize: 10, 
          interval: 2,
          formatter: (v: string) => v.replace(':00', '')
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '',  // 移除Y轴名称，避免与图例重复
          position: 'left',
          splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } },
          axisLabel: { color: axisColor, fontSize: 10 },
          nameTextStyle: { color: axisColor, fontSize: 10 }
        },
        {
          type: 'value',
          name: '',  // 移除Y轴名称，避免与图例重复
          position: 'right',
          splitLine: { show: false },
          axisLabel: { 
            color: axisColor, 
            fontSize: 10, 
            formatter: (v: number) => `¥${v}`
          },
          nameTextStyle: { color: axisColor, fontSize: 10 }
        }
      ],
      series: [
        // 订单柱（低饱和度蓝紫色背景）
        {
          name: '订单数',
          type: 'bar',
          data: orders,
          barWidth: 12,
          itemStyle: {
            borderRadius: [3, 3, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: isDark ? 'rgba(139, 92, 246, 0.8)' : 'rgba(139, 92, 246, 0.7)' },
              { offset: 1, color: isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(139, 92, 246, 0.1)' }
            ])
          },
          // 高峰时段背景标记
          markArea: peakMarkAreaData.length > 0 ? {
            silent: true,
            data: peakMarkAreaData as any
          } : undefined
        },
        // 净利润线（带面积填充，盈利绿/亏损红）
        {
          name: '净利润',
          type: 'line',
          yAxisIndex: 1,
          data: profits,
          smooth: 0.3,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: {
            color: '#22c55e'  // 固定绿色，用于图例显示
          },
          lineStyle: { 
            width: 2.5,
            color: '#22c55e',
            shadowColor: 'rgba(34, 197, 94, 0.3)',
            shadowBlur: 8
          },
          // 面积填充
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(34, 197, 94, 0.25)' },
              { offset: 0.5, color: 'rgba(34, 197, 94, 0.05)' },
              { offset: 1, color: 'rgba(244, 63, 94, 0.15)' }
            ])
          },
          // 零线标记
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: {
              color: isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)',
              type: 'dashed',
              width: 1
            },
            data: [{ yAxis: 0 }],
            label: { show: false }
          }
        }
      ]
    };

    chartInstance.current.setOption(option, true);

    // 处理 resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, isDark, axisColor, splitLineColor]);

  // 主题变化时重新初始化
  useEffect(() => {
    if (chartInstance.current) {
      chartInstance.current.dispose();
      chartInstance.current = null;
    }
  }, [theme]);

  // 清理
  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  // 🆕 计算当前显示的日期描述（支持日期范围）
  const dateLabel = useMemo(() => {
    if (data?.date) {
      // 检查是否是日期范围格式（包含 ~）
      if (data.date.includes('~')) {
        // 日期范围：提取 MM-DD ~ MM-DD 格式
        const parts = data.date.split('~').map(s => s.trim());
        if (parts.length === 2 && parts[0] && parts[1]) {
          return `${parts[0].slice(5)} ~ ${parts[1].slice(5)}`;
        }
        return data.date;
      }
      return data.date.slice(5); // 单日期：MM-DD 格式
    }
    return null;
  }, [data?.date]);

  // 检查是否有有效数据
  const hasData = data && data.orders && data.orders.some(v => v > 0);
  
  // 🆕 判断是否是日期范围联动
  const isRangeLinked = selectedDateRange !== null && selectedDateRange !== undefined;

  return (
    <div className="glass-panel rounded-2xl p-4 h-full flex flex-col relative">
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-emerald-500/5 to-transparent pointer-events-none rounded-b-2xl"></div>

      <div className="mb-2 relative z-10">
        <h3 className="text-base font-bold flex items-center gap-2" style={{color: titleColor}}>
          <span className="w-1 h-4 bg-gradient-to-b from-emerald-400 to-emerald-600 rounded-full"></span>
          {dateLabel ? `${dateLabel} 分时段诊断` : '分时段诊断'}
          {(selectedDate || isRangeLinked) && (
            <span className="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 ml-1">
              已联动
            </span>
          )}
        </h3>
        <p className="text-[10px] mt-0.5 font-mono uppercase tracking-wider opacity-70" style={{color: subTitleColor}}>
          HOURLY PROFIT ANALYSIS
        </p>
      </div>
      
      <div className="flex-1 w-full min-h-0">
        {loading ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="animate-pulse text-sm" style={{color: subTitleColor}}>加载中...</div>
          </div>
        ) : !hasData ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-sm" style={{color: subTitleColor}}>暂无数据</div>
          </div>
        ) : (
          <div ref={chartRef} className="w-full h-full" />
        )}
      </div>
    </div>
  );
};

export default CostEfficiencyChart;
