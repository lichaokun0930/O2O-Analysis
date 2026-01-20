import React, { useEffect, useState, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { ordersApi } from '@/api/orders';
import type { DistanceAnalysisData } from '@/types';
import { useGlobalContext } from '@/store/GlobalContext';

/**
 * DistanceAnalysisChart Props 接口
 * Requirements: 4.6, 4.7, 4.9, 6.2
 */
interface Props {
  storeName?: string;
  channel?: string;
  theme: 'dark' | 'light';
  selectedDate?: string | null;      // 联动：从销售趋势图选中的日期
  selectedDateRange?: { start: string; end: string } | null;  // 🆕 日期范围选择
  /** 联动回调：用户点击某个距离区间时触发 */
  onDistanceBandSelect?: (bandIndex: number, bandLabel: string, minDistance: number, maxDistance: number) => void;
}

/**
 * 分距离订单诊断图表组件
 * 
 * 功能：
 * - 展示7个距离区间的订单数（柱状图）和利润（折线图）
 * - 高亮最优配送距离区间
 * - 支持与配送溢价雷达联动高亮
 * - 支持深色/浅色主题
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.9, 6.2, 6.3, 6.4
 */
const DistanceAnalysisChart: React.FC<Props> = ({
  storeName,
  channel,
  theme,
  selectedDate,
  selectedDateRange,
  onDistanceBandSelect
}) => {
  const [data, setData] = useState<DistanceAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedBandIndex, setSelectedBandIndex] = useState<number | null>(null); // 选中的距离区间索引
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // 🆕 获取全局日期范围
  const { dateRange } = useGlobalContext();

  // 主题相关颜色
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';
  const splitLineColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

  // 直接使用 selectedDate，后端已支持 MM-DD 格式
  const targetDate = selectedDate || undefined;

  // 加载数据 - Requirements: 4.6
  useEffect(() => {
    // 未选择门店时不发起请求
    if (!storeName) {
      setData(null);
      setLoading(false);
      return;
    }
    
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
        
        // 🔍 调试日志：检查传递的参数
        console.log('📊 DistanceAnalysisChart 请求参数:', params);
        
        const res = await ordersApi.getDistanceAnalysis(params);
        
        // 🔍 调试日志：检查返回的数据
        if (res.success && res.data) {
          console.log('📊 DistanceAnalysisChart 返回数据:', {
            date: res.data.date,
            total_orders: res.data.summary?.total_orders,
            bands: res.data.distance_bands?.map(b => `${b.band_label}: ${b.order_count}`)
          });
          setData(res.data);
        }
      } catch (err) {
        console.error('获取分距离订单诊断数据失败:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [storeName, channel, targetDate, selectedDateRange, dateRange.type, dateRange.start, dateRange.end]);

  // 初始化和更新图表 - Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.3, 6.4
  useEffect(() => {
    if (!chartRef.current || !data) return;

    // 初始化图表
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
    }

    const { distance_bands, summary } = data;

    // 提取数据
    const labels = distance_bands.map(b => b.band_label);
    const orderCounts = distance_bands.map(b => b.order_count);
    const profits = distance_bands.map(b => b.profit);

    // 找到最优距离区间的索引 - Requirements: 4.5
    const optimalIndex = labels.indexOf(summary.optimal_distance);

    // 生成柱状图颜色，高亮选中区间 - Requirements: 6.3, 6.4
    const barColors = distance_bands.map((_, index) => {
      const isOptimal = index === optimalIndex;
      const isSelected = index === selectedBandIndex; // 用户点击选中的区间
      
      if (isSelected) {
        // 用户选中的区间：青色高亮（与雷达图联动）
        return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(34, 211, 238, 1)' },      // cyan-400
          { offset: 1, color: 'rgba(34, 211, 238, 0.5)' }
        ]);
      } else if (isOptimal) {
        // 最优区间：金色高亮
        return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(250, 204, 21, 0.9)' },    // yellow-400
          { offset: 1, color: 'rgba(250, 204, 21, 0.3)' }
        ]);
      } else {
        // 普通柱子：紫色渐变
        return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: isDark ? 'rgba(139, 92, 246, 0.8)' : 'rgba(139, 92, 246, 0.7)' },
          { offset: 1, color: isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(139, 92, 246, 0.1)' }
        ]);
      }
    });

    // 生成最优距离区间的 markArea - Requirements: 4.5
    const optimalMarkArea = optimalIndex >= 0 ? {
      silent: true,
      data: [[
        {
          xAxis: labels[optimalIndex],
          itemStyle: {
            color: isDark ? 'rgba(250, 204, 21, 0.08)' : 'rgba(250, 204, 21, 0.1)'
          }
        },
        { xAxis: labels[optimalIndex] }
      ]] as any
    } : undefined;

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
        // Requirements: 4.4 - tooltip 显示所有指标
        formatter: (params: any) => {
          const bandLabel = params[0]?.axisValue || '';
          const bandIndex = labels.indexOf(bandLabel);
          const band = distance_bands[bandIndex];
          
          if (!band) return '';

          const isOptimal = bandLabel === summary.optimal_distance;
          
          let html = `<div style="font-weight:600;margin-bottom:8px;font-size:13px">
            ${bandLabel}
            ${isOptimal ? '<span style="color:#facc15;margin-left:6px">★ 最优区间</span>' : ''}
          </div>`;
          
          // 订单数
          html += `<div style="display:flex;justify-content:space-between;align-items:center;margin:4px 0">
            <span style="display:flex;align-items:center;gap:6px">
              <span style="width:8px;height:8px;border-radius:50%;background:#8b5cf6"></span>
              订单数
            </span>
            <span style="font-weight:600;margin-left:20px">${band.order_count}</span>
          </div>`;
          
          // 利润
          const profitColor = band.profit >= 0 ? '#22c55e' : '#f43f5e';
          html += `<div style="display:flex;justify-content:space-between;align-items:center;margin:4px 0">
            <span style="display:flex;align-items:center;gap:6px">
              <span style="width:8px;height:8px;border-radius:50%;background:${profitColor}"></span>
              利润
            </span>
            <span style="font-weight:600;margin-left:20px;color:${profitColor}">¥${band.profit.toFixed(2)}</span>
          </div>`;
          
          // 分隔线
          html += `<div style="border-top:1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'};margin:8px 0"></div>`;
          
          // 其他指标
          html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:11px">
            <div><span style="color:${isDark ? '#94a3b8' : '#64748b'}">销售额:</span> <span style="font-weight:600">¥${band.revenue.toFixed(0)}</span></div>
            <div><span style="color:${isDark ? '#94a3b8' : '#64748b'}">利润率:</span> <span style="font-weight:600;color:${band.profit_rate >= 0 ? '#22c55e' : '#f43f5e'}">${band.profit_rate.toFixed(1)}%</span></div>
            <div><span style="color:${isDark ? '#94a3b8' : '#64748b'}">配送成本:</span> <span style="font-weight:600">¥${band.delivery_cost.toFixed(0)}</span></div>
            <div><span style="color:${isDark ? '#94a3b8' : '#64748b'}">配送成本率:</span> <span style="font-weight:600">${band.delivery_cost_rate.toFixed(1)}%</span></div>
            <div><span style="color:${isDark ? '#94a3b8' : '#64748b'}">客单价:</span> <span style="font-weight:600">¥${band.avg_order_value.toFixed(0)}</span></div>
          </div>`;
          
          return html;
        }
      },
      legend: {
        data: ['订单数', '利润'],
        top: 2,
        right: 5,
        textStyle: { color: axisColor, fontSize: 10 },
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 12
      },
      // Requirements: 4.1 - xAxis 配置7个距离区间标签
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: axisColor,
          fontSize: 10,
          interval: 0,
          rotate: 0
        }
      },
      // Requirements: 4.2 - 双 yAxis（左侧订单数，右侧利润金额）
      yAxis: [
        {
          type: 'value',
          name: '',
          position: 'left',
          splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } },
          axisLabel: { color: axisColor, fontSize: 10 },
          nameTextStyle: { color: axisColor, fontSize: 10 }
        },
        {
          type: 'value',
          name: '',
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
        // Requirements: 4.1 - 柱状图 series（订单数，紫色渐变）
        {
          name: '订单数',
          type: 'bar',
          z: 10,  // 提高z层级，确保可以被点击
          data: orderCounts.map((value, index) => ({
            value,
            itemStyle: {
              color: barColors[index],
              borderRadius: [3, 3, 0, 0],
              // 选中时添加发光效果 - Requirements: 6.3
              shadowBlur: index === selectedBandIndex ? 15 : 0,
              shadowColor: index === selectedBandIndex ? 'rgba(34, 211, 238, 0.6)' : 'transparent'
            }
          })),
          barWidth: 28,  // 增加柱子宽度，便于点击
          barMaxWidth: 40,
          markArea: optimalMarkArea,
          // 平滑过渡动画 - Requirements: 6.4
          animationDuration: 300,
          animationEasing: 'cubicOut'
        },
        // Requirements: 4.3 - 折线图 series（利润，绿色/红色）
        {
          name: '利润',
          type: 'line',
          yAxisIndex: 1,
          data: profits,
          smooth: 0.3,
          symbol: 'circle',
          symbolSize: 6,
          z: 1,  // 降低z层级，让柱状图在上面
          silent: true,  // 🔧 关键修复：禁用折线图的鼠标事件，避免遮挡柱状图点击
          itemStyle: {
            color: '#22c55e'
          },
          lineStyle: {
            width: 2.5,
            color: '#22c55e',
            shadowColor: 'rgba(34, 197, 94, 0.3)',
            shadowBlur: 8
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(34, 197, 94, 0.15)' },
              { offset: 0.5, color: 'rgba(34, 197, 94, 0.03)' },
              { offset: 1, color: 'rgba(244, 63, 94, 0.08)' }
            ]),
            opacity: 0.8
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

    // 添加柱状图点击事件 - 联动到雷达图
    chartInstance.current.off('click'); // 先移除旧的监听器
    chartInstance.current.on('click', 'series.bar', (params: any) => {
      // 只响应柱状图的点击
      const bandIndex = params.dataIndex;
      const band = distance_bands[bandIndex];
      if (band) {
        console.log('📊 柱状图点击:', band.band_label, bandIndex);
        // 如果点击同一个区间，取消选中
          if (selectedBandIndex === bandIndex) {
            setSelectedBandIndex(null);
            if (onDistanceBandSelect) {
              onDistanceBandSelect(-1, '', 0, 0); // 取消选中
            }
          } else {
            setSelectedBandIndex(bandIndex);
            if (onDistanceBandSelect) {
              onDistanceBandSelect(bandIndex, band.band_label, band.min_distance, band.max_distance);
            }
          }
        }
    });

    // 处理 resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, isDark, axisColor, splitLineColor, selectedBandIndex, onDistanceBandSelect]);

  // 主题变化时重新初始化 - Requirements: 4.9
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

  // 检查是否有有效数据 - Requirements: 4.7
  const hasData = data && data.distance_bands && data.distance_bands.some(b => b.order_count > 0);

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
  
  // 🆕 判断是否是日期范围联动
  const isRangeLinked = selectedDateRange !== null && selectedDateRange !== undefined;

  return (
    <div className="glass-panel rounded-2xl p-4 h-full flex flex-col relative">
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-violet-500/5 to-transparent pointer-events-none rounded-b-2xl"></div>

      <div className="mb-2 relative z-10">
        <h3 className="text-base font-bold flex items-center gap-2" style={{ color: titleColor }}>
          <span className="w-1 h-4 bg-gradient-to-b from-violet-400 to-violet-600 rounded-full"></span>
          {dateLabel ? `${dateLabel} 分距离诊断` : '分距离诊断'}
          {(selectedDate || isRangeLinked) && (
            <span className="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-400 ml-1">
              已联动
            </span>
          )}
          {selectedBandIndex !== null && data?.distance_bands[selectedBandIndex] && (
            <span className="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 ml-1">
              已选: {data.distance_bands[selectedBandIndex].band_label}
            </span>
          )}
        </h3>
        <p className="text-[10px] mt-0.5 font-mono uppercase tracking-wider opacity-70" style={{ color: subTitleColor }}>
          DISTANCE-BASED ORDER DIAGNOSIS
          {data?.summary?.optimal_distance && (
            <span className="ml-2 normal-case text-yellow-400">
              (最优: {data.summary.optimal_distance})
            </span>
          )}
          {selectedBandIndex !== null && (
            <span className="ml-2 normal-case text-cyan-400">
              点击柱子取消选中
            </span>
          )}
        </p>
      </div>

      <div className="flex-1 w-full min-h-0">
        {/* 未选择门店提示 */}
        {!storeName ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-sm mb-2" style={{ color: subTitleColor }}>请先选择门店</div>
              <div className="text-xs opacity-60" style={{ color: subTitleColor }}>选择门店后将显示该门店的配送距离分析</div>
            </div>
          </div>
        ) : loading ? (
          /* Loading 状态 - Requirements: 4.6 */
          <div className="w-full h-full flex items-center justify-center">
            <div className="animate-pulse text-sm" style={{ color: subTitleColor }}>加载中...</div>
          </div>
        ) : !hasData ? (
          /* Empty 状态 - Requirements: 4.7 */
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-sm" style={{ color: subTitleColor }}>暂无数据</div>
          </div>
        ) : (
          <div ref={chartRef} className="w-full h-full" />
        )}
      </div>
    </div>
  );
};

export default DistanceAnalysisChart;
