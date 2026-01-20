import React, { useMemo, useState, useEffect, useCallback } from 'react';
import * as echarts from 'echarts';
import { ChannelMetrics } from '@/types';
import { useChart } from '@/hooks/useChart';
import { Target } from 'lucide-react';
import { ordersApi, OrderTrend } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';
import ChannelDropdown from '@/components/ui/ChannelDropdown';

interface Props {
  data: ChannelMetrics[];
  selectedId?: string | null;
  theme: 'dark' | 'light';
  // 🆕 图表联动props
  onDateSelect?: (date: string | null, index?: number, total?: number) => void;
  selectedDate?: string | null;
  // 🆕 日期范围选择（点击两个柱子形成范围）
  selectedDateRange?: { start: string; end: string } | null;
}

const DailyTrendChart: React.FC<Props> = ({ data, theme, onDateSelect, selectedDate, selectedDateRange }) => {
  const [showAnomalies, setShowAnomalies] = useState(false);
  const [apiTrendData, setApiTrendData] = useState<OrderTrend | null>(null);
  const [loading, setLoading] = useState(false);
  
  // 🆕 使用全局渠道状态和渠道列表（避免重复请求）
  const { selectedStore, dateRange, selectedChannel, setSelectedChannel, channelList } = useGlobalContext();
  
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';
  const splitLineColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

  // 获取趋势数据（当门店、渠道或日期范围变化时）
  useEffect(() => {
    const fetchTrendData = async () => {
      if (!selectedStore) {
        setApiTrendData(null);
        return;
      }
      
      setLoading(true);
      try {
        // 🆕 构建请求参数，支持日期范围
        const params: {
          store_name: string;
          channel?: string;
          days?: number;
          start_date?: string;
          end_date?: string;
          granularity: 'day' | 'week' | 'month';
        } = {
          store_name: selectedStore,
          channel: selectedChannel === 'all' ? undefined : selectedChannel,
          granularity: 'day'
        };
        
        // 如果有自定义日期范围，使用日期范围；否则使用默认30天
        if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
          params.start_date = dateRange.start;
          params.end_date = dateRange.end;
        } else {
          params.days = 30;
        }
        
        const res = await ordersApi.getTrend(params);
        if (res.success && res.data) {
          setApiTrendData(res.data);
        }
      } catch (error) {
        console.error('获取趋势数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTrendData();
  }, [selectedStore, selectedChannel, dateRange.type, dateRange.start, dateRange.end]);

  // 计算利润率异常点（与Dash版本一致：利润率 < 均值 - 1σ）
  const calculateProfitRateAnomalies = (profitRates: number[], dates: string[], revenues: number[]) => {
    if (profitRates.length === 0) return [];
    
    // 过滤掉0值，只计算有效利润率
    const validRates = profitRates.filter(r => r > 0);
    if (validRates.length === 0) return [];
    
    // 计算均值和标准差
    const mean = validRates.reduce((a, b) => a + b, 0) / validRates.length;
    const variance = validRates.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / validRates.length;
    const std = Math.sqrt(variance);
    
    // 异常阈值：均值 - 1个标准差
    const anomalyThreshold = mean - std;
    
    // 找出异常点（标注在销售额曲线上，保持原有展示效果）
    const anomalies: { name: string; xAxis: string; yAxis: number; value: string; itemStyle: { color: string } }[] = [];
    profitRates.forEach((rate, index) => {
      // 利润率 < 阈值 且 > 0（避免0值）
      if (rate < anomalyThreshold && rate > 0) {
        anomalies.push({
          name: 'Profit Rate Low',
          xAxis: dates[index],
          yAxis: revenues[index],  // 标注在销售额曲线上
          value: `${rate.toFixed(1)}%`,
          itemStyle: { color: '#f43f5e' }
        });
      }
    });
    
    return anomalies;
  };

  // 处理数据：优先使用API数据，否则使用mock数据
  // 🆕 新增 fullDates 数组，保存完整日期用于 API 调用
  const { categories, fullDates, values, anomalies, profitRates, avgValues } = useMemo(() => {
    // 如果有API数据，使用API数据
    if (apiTrendData && apiTrendData.dates.length > 0) {
      const combinedData = apiTrendData.dates.map((date, index) => ({
        date: date.slice(5), // 只显示月-日（用于图表显示）
        fullDate: date,      // 🆕 完整日期（用于 API 调用）
        revenue: apiTrendData.amounts[index] || 0,
        profit: apiTrendData.profits[index] || 0,
        orders: apiTrendData.order_counts[index] || 0,
        profitRate: apiTrendData.profit_rates?.[index] || 0,
        avgValue: apiTrendData.avg_values?.[index] || 0  // 🆕 客单价
      }));

      const _profitRates = combinedData.map(d => d.profitRate);
      const _avgValues = combinedData.map(d => d.avgValue);
      const _dates = combinedData.map(d => d.date);
      const _fullDates = combinedData.map(d => d.fullDate);  // 🆕 完整日期数组
      const _revenues = combinedData.map(d => d.revenue);
      
      // 🆕 使用利润率统计异常检测（与Dash版本一致）
      const _anomalies = calculateProfitRateAnomalies(_profitRates, _dates, _revenues);

      return {
        categories: _dates,
        fullDates: _fullDates,  // 🆕 返回完整日期
        values: combinedData,
        anomalies: _anomalies,
        profitRates: _profitRates,
        avgValues: _avgValues
      };
    }

    // 备用：使用mock数据
    let combinedData: { date: string; fullDate: string; revenue: number; profit: number; orders: number; profitRate: number; avgValue: number }[] = [];
    
    if (data.length > 0) {
      combinedData = data[0].dailyTrend.map(d => ({
        date: d.date,
        fullDate: d.date,  // 🆕 mock数据中 date 就是完整日期
        revenue: 0,
        profit: 0,
        orders: 0,
        profitRate: 0,
        avgValue: 0
      }));

      const sourceChannels = data;

      sourceChannels.forEach(channel => {
        channel.dailyTrend.forEach((d, index) => {
          if (combinedData[index]) {
            combinedData[index].revenue += d.revenue;
            combinedData[index].profit += d.profit;
            combinedData[index].orders += d.orders;
          }
        });
      });

      // 计算利润率和客单价
      combinedData.forEach(d => {
        d.profitRate = d.revenue > 0 ? (d.profit / d.revenue * 100) : 0;
        d.avgValue = d.orders > 0 ? (d.revenue / d.orders) : 0;
      });
    }

    const _profitRates = combinedData.map(d => d.profitRate);
    const _avgValues = combinedData.map(d => d.avgValue);
    const _dates = combinedData.map(d => d.date);
    const _fullDates = combinedData.map(d => d.fullDate);  // 🆕 完整日期数组
    const _revenues = combinedData.map(d => d.revenue);
    
    // 🆕 使用利润率统计异常检测（与Dash版本一致）
    const _anomalies = calculateProfitRateAnomalies(_profitRates, _dates, _revenues);

    return {
      categories: _dates,
      fullDates: _fullDates,  // 🆕 返回完整日期
      values: combinedData,
      anomalies: _anomalies,
      profitRates: _profitRates,
      avgValues: _avgValues
    };
  }, [data, apiTrendData]);

  // 🆕 处理图表点击事件 - 传递完整日期给下钻图表
  const handleClick = useCallback((params: any) => {
    // 允许点击任何系列（包括透明的 HitBox）来触发选择
    if (onDateSelect && params.dataIndex !== undefined) {
      const total = categories.length;  // 获取总日期数
      const clickedFullDate = fullDates[params.dataIndex];  // YYYY-MM-DD 格式（用于 API）
      
      // 🆕 使用完整日期进行比较和传递
      if (selectedDate === clickedFullDate) {
        onDateSelect(null, undefined, total);  // 取消选中
      } else {
        onDateSelect(clickedFullDate, params.dataIndex, total);  // 🆕 传递完整日期、索引和总数
      }
    }
  }, [onDateSelect, selectedDate, categories.length, fullDates]);

  // 计算最大销售额（用于 HitBox 高度）
  const maxRevenue = useMemo(() => {
    return Math.max(...values.map(v => v.revenue), 1000);
  }, [values]);

  // 🆕 智能计算各指标的Y轴范围（分层显示）
  const axisRanges = useMemo(() => {
    const revenues = values.map(v => v.revenue);
    const profits = values.map(v => v.profit);
    const orders = values.map(v => v.orders);
    const rates = profitRates;
    
    // 销售额：自动范围，占据上层
    const maxRevenue = Math.max(...revenues, 1000);
    
    // 利润轴：扩大范围让绿线在下层（约占图表20%-50%区域）
    const maxProfit = Math.max(...profits, 100);
    const profitMax = Math.ceil(maxProfit * 3 / 100) * 100;  // 扩大3倍，让线在下方
    
    // 订单数轴：独立计算
    const maxOrders = Math.max(...orders, 10);
    const ordersMax = Math.ceil(maxOrders * 1.3 / 10) * 10;
    
    // 利润率轴：扩大范围让黄线在中上层（约占图表40%-60%区域）
    const maxRate = Math.max(...rates, 10);
    const rateMax = Math.ceil(maxRate * 2.2 / 10) * 10;  // 扩大2.2倍
    
    return {
      revenueMax: maxRevenue,
      profitMax,
      ordersMax,
      rateMax: Math.max(rateMax, 100)
    };
  }, [values, profitRates]);

  // 🆕 ECharts配置：保持原有样式 + 点击联动高亮
  const option: echarts.EChartsOption = {
    grid: { top: 30, right: 50, bottom: 40, left: 50, containLabel: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0,0,0,0.1)',
      padding: 16,
      textStyle: { fontFamily: 'JetBrains Mono', color: isDark ? '#fff' : '#0f172a' },
      axisPointer: { type: 'cross', label: { backgroundColor: '#6366f1' }, lineStyle: { type: 'dashed', color: '#6366f1' } },
      formatter: (params: any) => {
        if (!Array.isArray(params)) return '';
        // 过滤掉 HitBox 系列
        const filteredParams = params.filter((p: any) => p.seriesName !== 'HitBox');
        if (filteredParams.length === 0) return '';
        let result = `<div style="font-weight:bold;margin-bottom:8px">${filteredParams[0]?.axisValue}</div>`;
        filteredParams.forEach((item: any) => {
          let value = '';
          if (item.seriesName === '利润率') {
            value = `${item.value?.toFixed(1)}%`;
          } else if (item.seriesName === '订单数') {
            value = `${item.value}`;
          } else {
            value = `¥${(item.value || 0).toLocaleString()}`;
          }
          result += `<div style="display:flex;justify-content:space-between;gap:16px">
            <span>${item.marker}${item.seriesName}</span>
            <span style="font-weight:bold">${value}</span>
          </div>`;
        });
        return result;
        }
    },
    legend: {
      data: ['销售额', '总利润', '利润率', '订单数'],
      bottom: 0,
      textStyle: { color: axisColor, fontSize: 10 },
      itemGap: 16,
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10
    },
    xAxis: {
      type: 'category',
      data: categories,
      boundaryGap: true,  // 🆕 确保柱状图对齐
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: axisColor, fontSize: 10, fontFamily: 'JetBrains Mono' }
    },
    yAxis: [
      // Y轴0: 销售额（左侧，主轴）
      {
        type: 'value',
        name: '',
        splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } },
        axisLabel: { color: axisColor, fontSize: 10, formatter: (val: number) => `¥${val/1000}k` }
      },
      // Y轴1: 利润率（右侧）- 扩大范围让黄线在中上层
      {
        type: 'value',
        name: '',
        position: 'right',
        min: 0,
        max: axisRanges.rateMax,
        splitLine: { show: false },
        axisLabel: { color: axisColor, fontSize: 10, formatter: '{value}%' }
      },
      // Y轴2: HitBox专用（隐藏）
      {
        type: 'value',
        name: '',
        position: 'left',
        show: false,
        splitLine: { show: false },
        min: 0,
        max: 100
      },
      // Y轴3: 利润专用（隐藏）- 扩大范围让绿线在下层
      {
        type: 'value',
        name: '',
        position: 'left',
        show: false,
        splitLine: { show: false },
        min: 0,
        max: axisRanges.profitMax
      },
      // Y轴4: 订单数专用（隐藏）
      {
        type: 'value',
        name: '',
        position: 'left',
        show: false,
        splitLine: { show: false },
        min: 0,
        max: axisRanges.ordersMax
      }
    ],
    series: [
      // 🆕 HitBox 系列（透明柱状图，用于捕获点击事件）
      {
        name: 'HitBox',
        type: 'bar',
        yAxisIndex: 2,  // 🆕 使用独立的隐藏Y轴
        data: values.map(() => 100),  // 固定高度，填满区域
        barWidth: '80%',  // 宽点击区域
        barGap: '-100%',  // 覆盖在其他柱子上
        z: 10,  // 🆕 放在最上层，确保能捕获点击
        itemStyle: { color: 'transparent' },
        tooltip: { show: false },
        silent: false  // 🆕 确保响应事件
      },
      // 订单数柱状图（粗柱子样式 + 点击高亮）
      {
        name: '订单数',
        type: 'bar',
        yAxisIndex: 4,  // 🆕 使用独立的订单数Y轴
        data: values.map(v => {
          // 判断是否在选中范围内
          const isInRange = selectedDateRange 
            ? v.fullDate >= selectedDateRange.start && v.fullDate <= selectedDateRange.end
            : false;
          const isSingleSelected = selectedDate && v.fullDate === selectedDate;
          const isHighlighted = isInRange || isSingleSelected;
          
          return {
            value: v.orders,
            itemStyle: (selectedDate || selectedDateRange) ? {
              // 选中状态：高亮选中日期或范围内日期
              borderRadius: [2, 2, 0, 0],
              color: isHighlighted 
                ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: isInRange ? '#34d399' : '#818cf8' },  // 范围用绿色，单选用紫色
                    { offset: 1, color: isInRange ? '#059669' : '#6366f1' }
                  ])
                : new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: isDark ? 'rgba(71, 85, 105, 0.2)' : 'rgba(71, 85, 105, 0.15)' },
                    { offset: 1, color: isDark ? 'rgba(51, 65, 85, 0.05)' : 'rgba(71, 85, 105, 0.02)' }
                  ]),
              shadowBlur: isHighlighted ? 15 : 0,
              shadowColor: isHighlighted 
                ? (isInRange ? 'rgba(52, 211, 153, 0.5)' : 'rgba(99, 102, 241, 0.5)') 
                : 'transparent'
            } : {
              // 未选中状态：保持原有样式
              borderRadius: [2, 2, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: isDark ? 'rgba(71, 85, 105, 0.55)' : 'rgba(71, 85, 105, 0.35)' },
                { offset: 1, color: isDark ? 'rgba(51, 65, 85, 0.15)' : 'rgba(71, 85, 105, 0.05)' }
              ])
            }
          };
        }),
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: isDark ? 'rgba(148, 163, 184, 0.95)' : 'rgba(100, 116, 139, 0.7)' },
              { offset: 1, color: isDark ? 'rgba(100, 116, 139, 0.4)' : 'rgba(100, 116, 139, 0.2)' }
            ]),
            shadowColor: isDark ? 'rgba(148, 163, 184, 0.4)' : 'rgba(100, 116, 139, 0.3)',
            shadowBlur: 12
          }
        },
        barWidth: '60%',  // 🆕 粗柱子，填充大部分区域
        barGap: '-100%',  // 🆕 与 HitBox 重叠
        z: 1
      },
      // 总利润（绿色线条，使用独立Y轴让线条展开）
      {
        name: '总利润',
        type: 'line',
        smooth: 0.4,
        symbol: 'none',
        showSymbol: false,
        yAxisIndex: 3,  // 🆕 使用独立的利润Y轴
        itemStyle: { color: '#22c55e' },
        lineStyle: { 
          width: 2.5, 
          color: '#22c55e',
          opacity: selectedDate ? 0.3 : 1,
          shadowColor: 'rgba(34, 197, 94, 0.7)',
          shadowBlur: 10,
          shadowOffsetY: -4
        },
        emphasis: {
          focus: 'series',
          itemStyle: { color: '#22c55e', borderColor: '#fff', borderWidth: 2 },
          lineStyle: { width: 3, shadowBlur: 14, shadowOffsetY: -5 }
        },
        data: values.map(v => v.profit),
        z: 2
      },
      // 利润率曲线（黄色虚线）- 在中上层
      {
        name: '利润率',
        type: 'line',
        smooth: 0.4,
        symbol: 'none',
        showSymbol: false,
        yAxisIndex: 1,
        itemStyle: { color: '#fbbf24' },  // 黄色
        lineStyle: { 
          width: 2, 
          color: '#fbbf24',
          type: [5, 5],
          opacity: selectedDate ? 0.3 : 1
        },
        emphasis: {
          focus: 'series',
          itemStyle: { color: '#fbbf24', borderColor: '#fff', borderWidth: 2 },
          lineStyle: { width: 2.5, type: 'solid' }
        },
        data: profitRates,
        z: 3
      },
      // 销售额曲线（主角：白色线条，强光晕效果）- 在最上层
      {
        name: '销售额',
        type: 'line',
        smooth: 0.4,
        symbol: 'none',
        showSymbol: false,
        yAxisIndex: 0,
        itemStyle: { color: isDark ? '#f8fafc' : '#334155' },
        lineStyle: {
          width: 3,
          color: isDark ? '#f8fafc' : '#334155',
          opacity: selectedDate ? 0.3 : 1,
          shadowColor: isDark ? 'rgba(255, 255, 255, 0.8)' : 'rgba(51, 65, 85, 0.5)',
          shadowBlur: 20,
          shadowOffsetY: 0
        },
        areaStyle: {
          opacity: selectedDate ? 0.05 : 0.2,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(74, 144, 226, 0.3)' },
            { offset: 1, color: 'rgba(74, 144, 226, 0.05)' }
          ])
        },
        emphasis: {
          focus: 'series',
          itemStyle: { 
            color: '#fff', 
            borderColor: '#818cf8', 
            borderWidth: 2,
            shadowColor: 'rgba(129, 140, 248, 0.5)',
            shadowBlur: 10
          },
          lineStyle: { width: 4 }
        },
        data: values.map(v => v.revenue),
        // 异常标注
        markPoint: showAnomalies && anomalies.length > 0 ? {
          data: anomalies
            .filter(a => a.xAxis !== undefined && a.yAxis !== undefined && !isNaN(a.yAxis))
            .map(a => ({
              name: a.name,
              coord: [a.xAxis, a.yAxis],
              itemStyle: a.itemStyle
            })),
          symbol: 'pin',
          symbolSize: 40,
          label: { show: true, fontSize: 8, formatter: '!' },
          animation: true,
          animationDuration: 800,
          animationEasing: 'elasticOut'
        } : undefined,
        z: 3
      }
    ]
  };

  const chartRef = useChart(option, [data, showAnomalies, theme, apiTrendData, selectedChannel, selectedDate, selectedDateRange, axisRanges], theme, handleClick);

  return (
    <div className={`glass-panel rounded-2xl p-6 h-full flex flex-col relative overflow-hidden group transition-all duration-300 ${selectedDate ? 'border-indigo-500/50 shadow-[0_0_30px_rgba(99,102,241,0.15)]' : ''}`}>
      <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-b from-indigo-500/5 to-transparent pointer-events-none"></div>

      <div className="mb-2 flex justify-between items-start relative z-10">
        <div>
          <h3 className="text-lg font-bold flex items-center gap-2" style={{color: titleColor}}>
            <span className="w-1 h-5 bg-gradient-to-b from-indigo-400 to-indigo-600 rounded-full shadow-[0_0_10px_#818cf8]"></span>
            销售趋势分析
            {selectedDate && <span className="text-xs bg-indigo-500 text-white px-2 py-0.5 rounded-md font-mono ml-2">{selectedDate.slice(5)}</span>}
          </h3>
          <p className="text-xs mt-1 font-mono uppercase tracking-widest opacity-70 flex items-center gap-1" style={{color: subTitleColor}}>
            {selectedChannel === 'all' ? '全部渠道' : selectedChannel} · 含利润率
            {onDateSelect && <span className="ml-2 text-indigo-400">| 点击柱子下钻</span>}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 渠道筛选下拉框 */}
          <ChannelDropdown 
            selectedChannel={selectedChannel}
            channelList={channelList}
            onSelect={setSelectedChannel}
            isDark={isDark}
          />
          
          {/* 异常监测按钮 */}
          <button 
            onClick={() => setShowAnomalies(!showAnomalies)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-300 ${
              showAnomalies 
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.2)]' 
              : isDark ? 'bg-slate-800/50 border-white/5 text-slate-400 hover:text-white' : 'bg-white/50 border-black/5 text-slate-600 hover:text-slate-900'
            }`}
          >
            {showAnomalies ? <Target size={14} className="animate-pulse" /> : <Target size={14} />}
            {showAnomalies ? '异常 ON' : '异常 OFF'}
          </button>
        </div>
      </div>
      
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/10 z-20 rounded-2xl">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        </div>
      )}
      
      <div className="flex-1 w-full min-h-[350px] relative cursor-pointer">
        <div ref={chartRef} className="absolute inset-0 w-full h-full" />
      </div>
    </div>
  );
};

export default DailyTrendChart;
