import React, { useMemo, useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Radar } from 'lucide-react';
import { ordersApi, DeliveryRadarPoint } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';

interface Props {
  data?: any[];
  selectedId?: string | null;
  theme: 'dark' | 'light';
  selectedDistanceBand?: { minDistance: number; maxDistance: number } | null;
  storeName?: string;
  selectedDate?: string | null;  // 联动：从销售趋势图选中的日期
  selectedDateRange?: { start: string; end: string } | null;  // 🆕 日期范围选择
}

const DeliveryHeatmap: React.FC<Props> = ({ theme, selectedDistanceBand, storeName: propsStoreName, selectedDate, selectedDateRange }) => {
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#94a3b8' : '#64748b'; 
  const titleColor = isDark ? '#fff' : '#0f172a';
  const subTitleColor = isDark ? '#94a3b8' : '#64748b';
  const splitLineColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';

  const { selectedStore: contextStore, dateRange } = useGlobalContext();
  const selectedStore = propsStoreName || contextStore;

  const [radarData, setRadarData] = useState<DeliveryRadarPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [analysisDate, setAnalysisDate] = useState<string | null>(null);  // 🆕 分析日期
  // 🎨 渠道筛选状态
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);

  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    console.log('📡 DeliveryHeatmap - selectedStore:', selectedStore, 'selectedDate:', selectedDate, 'selectedDateRange:', selectedDateRange);
    
    if (!selectedStore) {
      setRadarData([]);
      setAnalysisDate(null);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const params: any = { store_name: selectedStore };
        
        // 🆕 优先使用下钻日期/日期范围
        if (selectedDate) {
          params.target_date = selectedDate;
        } else if (selectedDateRange) {
          // 🆕 销售趋势图下钻的日期范围
          params.start_date = selectedDateRange.start;
          params.end_date = selectedDateRange.end;
        } else if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
          // 全局日期范围（顶部日期选择器）
          params.start_date = dateRange.start;
          params.end_date = dateRange.end;
        }
        // 不传日期参数时，后端默认使用最新一天
        
        if (selectedDistanceBand) {
          params.min_distance = selectedDistanceBand.minDistance;
          params.max_distance = selectedDistanceBand.maxDistance;
        }

        console.log('📡 配送溢价雷达请求参数:', params);
        const res = await ordersApi.getDeliveryRadar(params);
        
        if (res.success) {
          console.log('📡 配送溢价雷达数据:', res.data?.length, '条, 日期:', res.date);
          setRadarData(res.data || []);
          setAnalysisDate(res.date || null);
        }
      } catch (error) {
        console.error('获取配送溢价雷达数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedStore, selectedDate, selectedDateRange, dateRange.type, dateRange.start, dateRange.end, selectedDistanceBand]);

  const { basePoints, channelStats } = useMemo(() => {
    if (!radarData.length) {
      console.log('📡 DeliveryHeatmap basePoints - 无数据');
      return {
        basePoints: [],
        channelStats: [] as { name: string; count: number; color: string }[]
      };
    }

    // 过滤掉无效数据
    const validData = radarData.filter(p => 
      typeof p.distance === 'number' && !isNaN(p.distance) &&
      typeof p.hour === 'number' && !isNaN(p.hour) &&
      typeof p.delivery_cost === 'number' && !isNaN(p.delivery_cost) &&
      typeof p.order_value === 'number' && !isNaN(p.order_value) &&
      typeof p.profit === 'number' && !isNaN(p.profit)
    );

    // 只显示溢价订单
    const premiumData = validData.filter(p => p.is_premium);

    // 🎨 统计各渠道溢价订单数（用于显示，不受筛选影响）
    const channelCountMap: Record<string, number> = {};
    premiumData.forEach(p => {
      const ch = p.channel || '其他';
      let matchedKey = '其他';
      if (ch.includes('美团')) matchedKey = '美团';
      else if (ch.includes('饿了么')) matchedKey = '饿了么';
      else if (ch.includes('抖音')) matchedKey = '抖音';
      else if (ch.includes('京东')) matchedKey = '京东';
      channelCountMap[matchedKey] = (channelCountMap[matchedKey] || 0) + 1;
    });

    const channelColorMap: Record<string, string> = {
      '美团': '#FFB800',
      '饿了么': '#0096FF',
      '抖音': '#1a1a1a',
      '京东': '#E4393C',
      '其他': '#8B5CF6',
    };

    const stats = Object.entries(channelCountMap)
      .map(([name, count]) => ({ name, count, color: channelColorMap[name] || '#8B5CF6' }))
      .sort((a, b) => b.count - a.count);

    // 🔧 根据选中的渠道筛选数据
    let filteredData = premiumData;
    if (selectedChannel) {
      filteredData = premiumData.filter(p => {
        const ch = p.channel || '其他';
        if (selectedChannel === '美团') return ch.includes('美团');
        if (selectedChannel === '饿了么') return ch.includes('饿了么');
        if (selectedChannel === '抖音') return ch.includes('抖音');
        if (selectedChannel === '京东') return ch.includes('京东');
        if (selectedChannel === '其他') return !ch.includes('美团') && !ch.includes('饿了么') && !ch.includes('抖音') && !ch.includes('京东');
        return true;
      });
    }

    const points = filteredData.map(p => ({
      value: [p.distance, p.hour, p.delivery_cost, p.order_value, p.profit, p.channel || ''] as [number, number, number, number, number, string],
      originalAngle: p.hour,
      isPremium: p.is_premium
    }));

    console.log('📡 DeliveryHeatmap - 溢价订单:', premiumData.length, '筛选后:', points.length);

    return {
      basePoints: points,
      channelStats: stats
    };
  }, [radarData, selectedChannel]);

  const maxDistance = useMemo(() => {
    if (!basePoints.length) return 8.5;
    const maxDist = Math.max(...basePoints.map(p => p.value[0]));
    // 确保最大距离至少为 2km，避免 interval=2 时显示问题
    return Math.max(2, Math.ceil(maxDist) + 0.5);
  }, [basePoints]);

  // 🎨 渠道颜色映射
  const channelColors: Record<string, string> = {
    '美团': '#FFB800',      // 美团黄
    '饿了么': '#0096FF',    // 饿了么蓝
    '抖音': '#000000',      // 抖音黑
    '京东': '#E4393C',      // 京东红
    '其他': '#8B5CF6',      // 紫色
  };

  const getChannelColor = (channel: string): string => {
    if (!channel) return '#f43f5e';
    for (const [key, color] of Object.entries(channelColors)) {
      if (channel.includes(key)) return color;
    }
    return '#f43f5e'; // 默认红色
  };

  const option: echarts.EChartsOption = useMemo(() => {
    if (!basePoints.length) {
      console.log('📡 DeliveryHeatmap option - 无数据，返回空 series');
      return { series: [] };
    }
    
    console.log('📡 DeliveryHeatmap option - 生成配置:', {
      pointsCount: basePoints.length,
      maxDistance,
      firstPoint: basePoints[0]?.value
    });
    
    return {
      polar: { radius: ['5%', '82%'], center: ['50%', '50%'] },
      angleAxis: {
        type: 'value',
        min: 0,
        max: 24,
        interval: 3,
        startAngle: 90,
        clockwise: true,
        axisLine: { lineStyle: { color: splitLineColor } },
        axisLabel: { formatter: '{value}h', color: axisColor, fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 'bold' },
        splitLine: { show: true, lineStyle: { color: splitLineColor, width: 1 } }
      },
      radiusAxis: {
        min: 0,
        max: maxDistance,
        // 动态计算刻度间隔，确保至少有 2-4 个刻度
        interval: maxDistance <= 2 ? 0.5 : maxDistance <= 4 ? 1 : 2,
        axisLine: { show: false },
        axisLabel: { formatter: '{value}km', color: axisColor, fontSize: 9, verticalAlign: 'bottom' },
        splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } }
      },
      tooltip: {
        backgroundColor: isDark ? 'rgba(2, 6, 23, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        borderColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0,0,0,0.1)',
        padding: 12,
        textStyle: { fontFamily: 'JetBrains Mono', color: isDark ? '#fff' : '#0f172a' },
        formatter: (params: any) => {
          const data = params.data?.value;
          if (!data) return '';
          const [dist, hour, cost, aov, profit, channel] = data;
          return `
            <div style="font-weight:600;margin-bottom:6px;color:#f43f5e">⚠️ 配送溢价订单</div>
            <div>渠道: ${channel || '未知'}</div>
            <div>距离: ${dist.toFixed(1)}km</div>
            <div>时段: ${hour}:00</div>
            <div>配送成本: <span style="color:#f43f5e;font-weight:bold">¥${cost.toFixed(1)}</span></div>
            <div>客单价: ¥${aov.toFixed(0)}</div>
            <div>利润: <span style="color:${profit >= 0 ? '#22c55e' : '#f43f5e'}">¥${profit.toFixed(1)}</span></div>
            <div style="margin-top:4px;font-size:10px;color:#94a3b8">配送净成本 > ¥6</div>
          `;
        }
      },
      series: [{
        name: '溢价订单',
        type: 'scatter',
        coordinateSystem: 'polar',
        encode: { radius: 0, angle: 1 },
        data: basePoints.map(p => {
          const channel = p.value[5] as string;
          const color = getChannelColor(channel);
          return {
            value: p.value,
            itemStyle: {
              color: color,
              opacity: 0.85,
              shadowBlur: 12,
              shadowColor: `${color}80`  // 50% 透明度的阴影
            }
          };
        }),
        symbolSize: (val: number[]) => Math.max(8, Math.min(val[2] * 1.5, 30)),
        itemStyle: { 
          borderColor: isDark ? 'rgba(255,255,255,0.9)' : '#fff', 
          borderWidth: 1.5 
        },
        emphasis: {
          itemStyle: { opacity: 1, shadowBlur: 20, borderColor: '#fff', borderWidth: 2 },
          scale: 1.3
        }
      }]
    };
  }, [basePoints, isDark, axisColor, splitLineColor, maxDistance]);

  // 🔧 直接管理 ECharts 实例
  // 初始化图表（当容器可用且有门店选择时）
  useEffect(() => {
    if (!chartContainerRef.current || !selectedStore) {
      console.log('📡 DeliveryHeatmap 初始化 - 跳过: container=', !!chartContainerRef.current, 'store=', selectedStore);
      return;
    }
    
    // 获取或创建实例
    let instance = echarts.getInstanceByDom(chartContainerRef.current);
    if (!instance) {
      instance = echarts.init(chartContainerRef.current, isDark ? 'dark' : undefined);
      console.log('📡 DeliveryHeatmap - 创建新的 ECharts 实例');
    }
    
    // 保存实例引用
    chartInstanceRef.current = instance;
    
    // 处理 resize
    const handleResize = () => {
      instance?.resize();
    };
    window.addEventListener('resize', handleResize);
    
    // 初始 resize
    setTimeout(() => {
      instance?.resize();
    }, 50);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [isDark, selectedStore]);
  
  // 更新图表数据（当 option 变化时）
  useEffect(() => {
    const instance = chartInstanceRef.current;
    if (!instance) {
      console.log('📡 DeliveryHeatmap 更新 - 实例不存在');
      return;
    }
    
    if (!basePoints.length) {
      // 清空图表但保留坐标系
      console.log('📡 DeliveryHeatmap 更新 - 无数据，清空 series');
      instance.setOption({
        polar: { radius: ['12%', '75%'], center: ['50%', '50%'] },
        angleAxis: {
          type: 'value',
          min: 0,
          max: 24,
          interval: 3,
          startAngle: 90,
          clockwise: true,
          axisLine: { lineStyle: { color: splitLineColor } },
          axisLabel: { formatter: '{value}h', color: axisColor, fontSize: 10 },
          splitLine: { show: true, lineStyle: { color: splitLineColor, width: 1 } }
        },
        radiusAxis: {
          min: 0,
          max: 8.5,
          interval: 2,
          axisLine: { show: false },
          axisLabel: { formatter: '{value}km', color: axisColor, fontSize: 9 },
          splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } }
        },
        series: []
      }, { notMerge: true });
      return;
    }
    
    // 设置配置 - 使用 notMerge: true 完全替换
    instance.setOption(option, { notMerge: true });
    console.log('📡 DeliveryHeatmap - setOption 完成, 数据点:', basePoints.length);
    
    // 强制 resize 确保正确渲染
    setTimeout(() => {
      instance?.resize();
    }, 100);
  }, [option, basePoints, axisColor, splitLineColor]);
  
  // 清理实例
  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose();
        chartInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="glass-panel rounded-2xl p-4 h-full flex flex-col relative overflow-hidden group">
      {/* 标题行：紧凑布局，标题和渠道分布在同一行 */}
      <div className="shrink-0 relative z-20 flex justify-between items-center mb-1">
        <div className="flex items-center gap-2">
          <Radar size={16} className="text-cyan-400 animate-pulse" />
          <h3 className="text-base font-bold" style={{color: titleColor}}>
            {analysisDate ? (
              // 检查是否是日期范围格式
              analysisDate.includes('~') 
                ? `${analysisDate.split('~').map(s => s.trim().slice(5)).join(' ~ ')} 配送溢价雷达`
                : `${analysisDate.slice(5)} 配送溢价雷达`
            ) : '配送溢价雷达'}
          </h3>
          {selectedDistanceBand && (
            <span className="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400">
              {selectedDistanceBand.minDistance}-{selectedDistanceBand.maxDistance}km
            </span>
          )}
          {(selectedDate || selectedDateRange) && (
            <span className="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 ml-1">
              已联动
            </span>
          )}
        </div>
        
        {/* 渠道分布放右上角 - 可点击筛选 */}
        <div className="flex items-center gap-2">
          {channelStats.slice(0, 4).map(ch => (
            <button 
              key={ch.name} 
              onClick={() => setSelectedChannel(selectedChannel === ch.name ? null : ch.name)}
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded transition-all cursor-pointer ${
                selectedChannel === ch.name 
                  ? 'bg-white/20 ring-1 ring-white/30' 
                  : selectedChannel ? 'opacity-40' : 'hover:bg-white/10'
              }`}
            >
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ch.color }} />
              <span className="text-[10px]" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>{ch.name}</span>
              <span className="text-[10px] font-mono font-bold" style={{ color: ch.color }}>{ch.count}</span>
            </button>
          ))}
          {selectedChannel && (
            <button 
              onClick={() => setSelectedChannel(null)}
              className="text-[10px] text-cyan-400 hover:text-cyan-300 ml-1"
            >
              ✕
            </button>
          )}
        </div>
      </div>
      
      {/* 图表区域：占满剩余空间 */}
      <div className="flex-1 w-full relative z-10 flex items-center justify-center">
        {!selectedStore ? (
          <div className="text-center">
            <div className="text-sm mb-2" style={{ color: subTitleColor }}>请先选择门店</div>
            <div className="text-xs opacity-60" style={{ color: subTitleColor }}>选择门店后将显示配送溢价分析</div>
          </div>
        ) : (
          <>
            {/* 图表容器始终渲染 */}
            <div 
              ref={chartContainerRef} 
              className="w-full h-full relative z-10" 
              style={{ visibility: loading || !basePoints.length ? 'hidden' : 'visible' }}
            />
            
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center z-20">
                <div className="animate-pulse text-sm" style={{ color: subTitleColor }}>加载中...</div>
              </div>
            )}
            
            {!loading && !basePoints.length && (
              <div className="absolute inset-0 flex items-center justify-center z-20">
                <div className="text-sm text-center" style={{ color: subTitleColor }}>
                  {selectedChannel 
                    ? `${selectedChannel} 渠道无溢价订单` 
                    : selectedDistanceBand 
                      ? `${selectedDistanceBand.minDistance}-${selectedDistanceBand.maxDistance}km 范围内无溢价订单` 
                      : '暂无溢价订单数据'}
                </div>
              </div>
            )}
            
            {/* 扫描动画 */}
            {basePoints.length > 0 && !loading && (
              <div className="absolute flex items-center justify-center pointer-events-none z-20 aspect-square h-[85%]">
                <div 
                  className="w-full h-full rounded-full animate-spin opacity-50" 
                  style={{
                    animationDuration: '6s',
                    animationTimingFunction: 'linear',
                    background: 'conic-gradient(from 0deg, transparent 0deg, transparent 300deg, rgba(34, 211, 238, 0.3) 360deg)'
                  }}
                />
                <div className="absolute w-1.5 h-1.5 bg-cyan-400 rounded-full shadow-[0_0_15px_#22d3ee] animate-ping" />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DeliveryHeatmap;
