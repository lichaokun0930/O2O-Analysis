import React, { useMemo, useState, useEffect } from 'react';
import * as echarts from 'echarts';
import { useChart } from '@/hooks/useChart';
import { Trophy, DollarSign, Wallet, AlertTriangle } from 'lucide-react';
import { ordersApi, TopProductsData } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';

interface Props {
  selectedDate: string | null;
  selectedDateRange?: { start: string; end: string } | null;  // 🆕 日期范围选择（从销售趋势图点击）
  theme: 'dark' | 'light';
}

type TabType = 'quantity' | 'revenue' | 'profit' | 'loss';

const TopProductsChart: React.FC<Props> = ({ selectedDate, selectedDateRange, theme }) => {
  const [activeTab, setActiveTab] = useState<TabType>('quantity');
  const [data, setData] = useState<TopProductsData | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { selectedStore, dateRange } = useGlobalContext();  // 🆕 获取全局日期范围
  
  const isDark = theme === 'dark';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';

  // 获取数据
  useEffect(() => {
    const fetchData = async () => {
      if (!selectedStore) {
        setData(null);
        return;
      }
      
      setLoading(true);
      try {
        // 🆕 优先级：销售趋势图点击的日期范围 > 销售趋势图点击的单日期 > 全局日期范围 > 默认全部数据
        const params: { 
          store_name: string; 
          date?: string; 
          start_date?: string; 
          end_date?: string;
          sort_by: TabType;
          limit: number;
        } = {
          store_name: selectedStore,
          sort_by: activeTab,
          limit: 15
        };
        
        if (selectedDateRange) {
          // 销售趋势图点击的日期范围
          params.start_date = selectedDateRange.start;
          params.end_date = selectedDateRange.end;
        } else if (selectedDate) {
          // 销售趋势图点击的单日期
          params.date = selectedDate;
        } else if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
          // 🆕 全局日期范围（顶部日期选择器）
          params.start_date = dateRange.start;
          params.end_date = dateRange.end;
        }
        // 否则不传日期参数，后端返回全部数据
        
        const res = await ordersApi.getTopProductsByDate(params);
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (error) {
        console.error('获取商品排行数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [selectedStore, selectedDate, selectedDateRange, dateRange.type, dateRange.start, dateRange.end, activeTab]);

  // 获取配置
  const config = useMemo(() => {
    switch (activeTab) {
      case 'quantity':
        return { colorStart: '#34d399', colorEnd: '#059669', label: '销量', unit: '', valueKey: 'quantity' };
      case 'revenue':
        return { colorStart: '#818cf8', colorEnd: '#4f46e5', label: '营收', unit: '¥', valueKey: 'revenue' };
      case 'profit':
        return { colorStart: '#fbbf24', colorEnd: '#d97706', label: '毛利', unit: '¥', valueKey: 'profit' };
      case 'loss':
        return { colorStart: '#f43f5e', colorEnd: '#be123c', label: '亏损/低利', unit: '¥', valueKey: 'profit' };
      default:
        return { colorStart: '#34d399', colorEnd: '#059669', label: '销量', unit: '', valueKey: 'quantity' };
    }
  }, [activeTab]);

  // 计算最大值（用于背景条）
  const maxValue = useMemo(() => {
    if (!data || data.products.length === 0) return 100;
    const values = data.products.map(p => Math.abs((p as any)[config.valueKey] || 0));
    return Math.max(...values);
  }, [data, config.valueKey]);

  // 构建ECharts配置
  const option: echarts.EChartsOption = useMemo(() => {
    if (!data || data.products.length === 0) {
      return {
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '暂无数据',
            fill: subTitleColor,
            fontSize: 14
          }
        }
      };
    }

    const products = data.products;
    // 格式化Y轴标签：排名 + 商品名（截断）
    const productLabels = products.map((p, i) => {
      const rank = i + 1;
      // 截断商品名称，显示更多字符
      let name = p.name;
      if (name.length > 20) {
        name = name.slice(0, 20) + '...';
      }
      return `${rank}. ${name}`;
    });
    const values = products.map(p => Math.abs((p as any)[config.valueKey] || 0));

    // 根据排名设置不同颜色
    const barColors = products.map((_, i) => {
      if (i === 0) return '#fbbf24'; // 金色
      if (i === 1) return '#94a3b8'; // 银色
      if (i === 2) return '#cd7f32'; // 铜色
      return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
        { offset: 0, color: config.colorStart },
        { offset: 1, color: config.colorEnd }
      ]);
    });

    return {
      graphic: [],
      grid: { 
        left: 0,
        right: 35, 
        top: 5, 
        bottom: 5,
        containLabel: true
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        textStyle: { color: isDark ? '#fff' : '#0f172a' },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return '';
          const index = params[0].dataIndex;
          const item = products[index];
          if (!item) return '';
          
          const growth = item.growth || 0;
          const growthColor = growth > 0 ? '#34d399' : growth < 0 ? '#f43f5e' : '#94a3b8';
          const growthIcon = growth > 0 ? '▲' : growth < 0 ? '▼' : '-';
          
          return `
            <div style="font-weight:bold;margin-bottom:4px;display:flex;justify-content:space-between;gap:16px">
              <span>${item.name}</span>
              <span style="color:${growthColor};font-family:monospace">${growthIcon} ${Math.abs(growth)}%</span>
            </div>
            <div style="font-size:12px;color:${subTitleColor};margin-bottom:8px">分类: ${item.category}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;font-size:12px">
              <span style="color:${subTitleColor}">销量:</span>
              <span style="font-family:monospace;text-align:right;font-weight:bold;color:${isDark ? '#fff' : '#0f172a'}">${item.quantity}</span>
              <span style="color:${subTitleColor}">营收:</span>
              <span style="font-family:monospace;text-align:right;font-weight:bold;color:#818cf8">¥${Math.round(item.revenue).toLocaleString()}</span>
              <span style="color:${subTitleColor}">毛利:</span>
              <span style="font-family:monospace;text-align:right;font-weight:bold;color:${item.profit >= 0 ? '#34d399' : '#f43f5e'}">¥${Math.round(item.profit).toLocaleString()}</span>
            </div>
          `;
        }
      },
      xAxis: {
        type: 'value',
        show: false,
        max: maxValue * 1.05
      },
      yAxis: {
        type: 'category',
        data: productLabels,
        inverse: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: isDark ? '#cbd5e1' : '#475569',
          fontSize: 11,
          fontWeight: 'normal' as const,
          formatter: (value: string | number, index: number) => {
            const strValue = String(value);
            // 前三名用特殊颜色通过 rich 样式实现
            if (index === 0) return `{gold|${strValue}}`;
            if (index === 1) return `{silver|${strValue}}`;
            if (index === 2) return `{bronze|${strValue}}`;
            return strValue;
          },
          rich: {
            gold: { color: '#fbbf24', fontWeight: 'bold' as const, fontSize: 11 },
            silver: { color: '#94a3b8', fontWeight: 'bold' as const, fontSize: 11 },
            bronze: { color: '#cd7f32', fontWeight: 'bold' as const, fontSize: 11 }
          }
        }
      } as echarts.YAXisComponentOption,
      series: [
        // 背景条（轨道）
        {
          type: 'bar',
          data: products.map(() => maxValue * 1.05),
          barWidth: 12,
          barGap: '-100%',
          z: 0,
          itemStyle: {
            color: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
            borderRadius: 6
          },
          tooltip: { show: false },
          animation: false
        },
        // 前景条（数值）
        {
          type: 'bar',
          data: values.map((v, i) => ({
            value: v,
            itemStyle: {
              color: barColors[i],
              borderRadius: 6
            }
          })),
          barWidth: 12,
          label: {
            show: true,
            position: 'right',
            formatter: (params: any) => {
              const val = Math.round(params.value);
              return `${config.unit}${val.toLocaleString()}`;
            },
            color: isDark ? '#e2e8f0' : '#475569',
            fontSize: 11,
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 'bold'
          }
        }
      ]
    };
  }, [data, config, maxValue, isDark, subTitleColor]);

  const chartRef = useChart(option, [data, activeTab, theme], theme);

  const tabs: { id: TabType; label: string; icon: React.ReactNode; color: string }[] = [
    { id: 'quantity', label: '销量榜', icon: <Trophy size={12} />, color: 'emerald' },
    { id: 'revenue', label: '营收榜', icon: <DollarSign size={12} />, color: 'indigo' },
    { id: 'profit', label: '毛利榜', icon: <Wallet size={12} />, color: 'amber' },
    { id: 'loss', label: '亏损榜', icon: <AlertTriangle size={12} />, color: 'rose' },
  ];

  // 🆕 计算当前显示的日期范围描述
  const dateRangeLabel = useMemo(() => {
    if (selectedDateRange) {
      // 如果起止日期相同，只显示单个日期
      if (selectedDateRange.start === selectedDateRange.end) {
        return `${selectedDateRange.start.slice(5)} 商品${config.label}`;
      }
      return `${selectedDateRange.start.slice(5)}~${selectedDateRange.end.slice(5)} 商品${config.label}`;
    }
    if (selectedDate) {
      return `${selectedDate.slice(5)} 商品${config.label}`;
    }
    if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
      // 如果起止日期相同，只显示单个日期
      if (dateRange.start === dateRange.end) {
        return `${dateRange.start.slice(5)} 商品${config.label}`;
      }
      return `${dateRange.start.slice(5)}~${dateRange.end.slice(5)} 商品${config.label}`;
    }
    return `商品${config.label} TOP 15`;
  }, [selectedDateRange, selectedDate, dateRange, config.label]);

  return (
    <div className="glass-panel rounded-2xl p-4 h-full flex flex-col relative overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/10 z-20 rounded-2xl">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
        </div>
      )}
      
      {/* 标题区域 - 紧凑布局 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {activeTab === 'quantity' && <Trophy size={16} className="text-emerald-400" />}
          {activeTab === 'revenue' && <DollarSign size={16} className="text-indigo-400" />}
          {activeTab === 'profit' && <Wallet size={16} className="text-amber-400" />}
          {activeTab === 'loss' && <AlertTriangle size={16} className="text-rose-400" />}
          <h3 className="text-base font-bold" style={{color: titleColor}}>
            {dateRangeLabel}
          </h3>
        </div>
        <span className="text-[10px] font-mono uppercase tracking-wider opacity-50" style={{color: subTitleColor}}>
          BY {config.valueKey.toUpperCase()}
        </span>
      </div>

      {/* 维度切换按钮 - 紧凑 */}
      <div className="flex p-0.5 bg-slate-900/50 rounded-lg border border-white/5 w-fit mb-3">
        {tabs.map(tab => {
          const isActive = activeTab === tab.id;
          let activeClass = '';
          if (isActive) {
            if (tab.color === 'emerald') activeClass = 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20';
            if (tab.color === 'indigo') activeClass = 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20';
            if (tab.color === 'amber') activeClass = 'bg-amber-500 text-white shadow-lg shadow-amber-500/20';
            if (tab.color === 'rose') activeClass = 'bg-rose-500 text-white shadow-lg shadow-rose-500/20';
          } else {
            activeClass = 'text-slate-400 hover:text-white hover:bg-white/5';
          }

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold transition-all duration-300 ${activeClass}`}
            >
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>
      
      {/* 图表区域 - 占满剩余空间 */}
      <div className="flex-1 w-full min-h-0">
        <div ref={chartRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default TopProductsChart;
