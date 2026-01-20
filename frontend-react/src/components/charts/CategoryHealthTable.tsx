/**
 * 品类健康度分析表格
 * 展示品类的销售额、环比增长、波动系数、平均折扣、利润率
 */
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { 
  Layers, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronRight,
  ArrowUpDown, RefreshCw, ChevronLeft, Activity, Calendar, Check
} from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import { format, isAfter, isBefore, isValid, parse } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { categoryApi, CategoryHealthItem } from '@/api/category';
import { ordersApi } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';

interface Props {
  theme?: 'dark' | 'light';
}

interface DateRangeSelection {
  from: Date | undefined;
  to?: Date | undefined;
}

type SortKey = 'current_revenue' | 'growth_rate' | 'current_quantity' | 'quantity_growth_rate' | 'volatility' | 'avg_discount' | 'profit_margin';
type SortOrder = 'asc' | 'desc';
type PeriodMode = 'preset' | 'custom';

const CategoryHealthTable: React.FC<Props> = () => {
  const [data, setData] = useState<CategoryHealthItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [periodMode, setPeriodMode] = useState<PeriodMode>('preset');
  const [period, setPeriod] = useState<7 | 14 | 30>(7);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [channel, setChannel] = useState<string>('');
  const [channelDropdownOpen, setChannelDropdownOpen] = useState(false);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [selectedRange, setSelectedRange] = useState<DateRangeSelection | undefined>();
  const [drillCategory, setDrillCategory] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('current_revenue');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [periodInfo, setPeriodInfo] = useState<{ start: string; end: string } | null>(null);
  
  const channelButtonRef = useRef<HTMLButtonElement>(null);
  const channelDropdownRef = useRef<HTMLDivElement>(null);
  const calendarButtonRef = useRef<HTMLButtonElement>(null);
  const calendarDropdownRef = useRef<HTMLDivElement>(null);
  
  const { selectedStore, storeDateRange, channelList } = useGlobalContext();

  // 解析数据日期范围
  const minDate = storeDateRange?.min_date ? parse(storeDateRange.min_date, 'yyyy-MM-dd', new Date()) : undefined;
  const maxDate = storeDateRange?.max_date ? parse(storeDateRange.max_date, 'yyyy-MM-dd', new Date()) : undefined;

  // 🆕 当门店变化时，如果当前选中的渠道不在新列表中，重置为全部
  useEffect(() => {
    if (channel && channelList.length > 0 && !channelList.includes(channel)) {
      setChannel('');
    }
  }, [channelList, channel]);

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (channelDropdownOpen && 
          channelButtonRef.current && !channelButtonRef.current.contains(target) &&
          channelDropdownRef.current && !channelDropdownRef.current.contains(target)) {
        setChannelDropdownOpen(false);
      }
      if (calendarOpen && 
          calendarButtonRef.current && !calendarButtonRef.current.contains(target) &&
          calendarDropdownRef.current && !calendarDropdownRef.current.contains(target)) {
        setCalendarOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [channelDropdownOpen, calendarOpen]);

  // 判断日期是否禁用
  const isDateDisabled = useCallback((date: Date) => {
    if (minDate && isBefore(date, minDate)) return true;
    if (maxDate && isAfter(date, maxDate)) return true;
    return false;
  }, [minDate, maxDate]);

  // 打开日历
  const handleOpenCalendar = useCallback(() => {
    if (periodMode === 'custom' && startDate && endDate) {
      const from = parse(startDate, 'yyyy-MM-dd', new Date());
      const to = parse(endDate, 'yyyy-MM-dd', new Date());
      if (isValid(from) && isValid(to)) {
        setSelectedRange({ from, to });
      }
    } else {
      setSelectedRange(undefined);
    }
    setCalendarOpen(true);
  }, [periodMode, startDate, endDate]);

  // 确认日期选择
  const handleConfirmDate = useCallback(() => {
    if (selectedRange?.from && selectedRange?.to) {
      setStartDate(format(selectedRange.from, 'yyyy-MM-dd'));
      setEndDate(format(selectedRange.to, 'yyyy-MM-dd'));
      setPeriodMode('custom');
      setCalendarOpen(false);
    }
  }, [selectedRange]);

  // 获取数据
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Parameters<typeof categoryApi.getHealth>[0] = {
        store_name: selectedStore || undefined,
        channel: channel || undefined,
        level: drillCategory ? 3 : 1,
        parent_category: drillCategory || undefined,
      };
      
      if (periodMode === 'custom' && startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
      } else {
        params.period = period;
      }
      
      const res = await categoryApi.getHealth(params);
      if (res.success) {
        setData(res.data);
        setPeriodInfo({ start: res.period.start, end: res.period.end });
      }
    } catch (error) {
      console.error('获取品类健康度数据失败:', error);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [selectedStore, channel, periodMode, period, startDate, endDate, drillCategory]);

  // 刷新并重置排序
  const handleRefresh = useCallback(() => {
    setSortKey('current_revenue');
    setSortOrder('desc');
    setChannel('');
    setPeriodMode('preset');
    setPeriod(7);
    setStartDate('');
    setEndDate('');
    setSelectedRange(undefined);
    fetchData();
  }, [fetchData]);

  // 切换到预设周期
  const handlePresetPeriod = (p: 7 | 14 | 30) => {
    setPeriodMode('preset');
    setPeriod(p);
    setStartDate('');
    setEndDate('');
    setSelectedRange(undefined);
  };

  // 选择渠道
  const handleChannelSelect = (ch: string) => {
    setChannel(ch);
    setChannelDropdownOpen(false);
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 排序
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      const diff = (aVal as number) - (bVal as number);
      return sortOrder === 'desc' ? -diff : diff;
    });
  }, [data, sortKey, sortOrder]);

  // 切换排序
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  // 下钻到三级分类
  const handleDrill = (categoryName: string) => {
    setDrillCategory(categoryName);
  };

  // 返回上级
  const handleBack = () => {
    setDrillCategory(null);
  };

  // 渲染增长率
  const renderGrowth = (rate: number) => {
    if (rate > 0) {
      return (
        <span className="flex items-center gap-1 text-emerald-400 font-mono">
          <TrendingUp size={14} />
          +{rate.toFixed(1)}%
        </span>
      );
    } else if (rate < 0) {
      return (
        <span className="flex items-center gap-1 text-rose-400 font-mono">
          <TrendingDown size={14} />
          {rate.toFixed(1)}%
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 text-slate-400 font-mono">
        <Minus size={14} />
        0%
      </span>
    );
  };

  // 渲染波动等级
  const renderVolatility = (level: string, cv: number) => {
    const colors: Record<string, string> = {
      '低': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      '中': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      '高': 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    };
    return (
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${colors[level] || colors['中']}`}>
          {level}
        </span>
        <span className="text-slate-500 text-xs font-mono">{cv.toFixed(1)}%</span>
      </div>
    );
  };

  // 渲染折扣（含变化）
  const renderDiscount = (discount: number, change: number) => {
    const color = discount < 8 ? 'text-rose-400' : discount < 9 ? 'text-amber-400' : 'text-slate-300';
    
    // 变化箭头：正数表示折扣力度减小（价格上涨），负数表示折扣力度增大（价格下降）
    let changeEl = null;
    if (Math.abs(change) >= 0.1) {
      if (change > 0) {
        // 折扣数值变大 = 折扣力度减小 = 涨价
        changeEl = <span className="text-emerald-400 text-xs ml-1">↑{change.toFixed(1)}</span>;
      } else {
        // 折扣数值变小 = 折扣力度增大 = 降价
        changeEl = <span className="text-rose-400 text-xs ml-1">↓{Math.abs(change).toFixed(1)}</span>;
      }
    }
    
    return (
      <span className={`font-mono ${color}`}>
        {discount.toFixed(1)}折{changeEl}
      </span>
    );
  };

  // 渲染利润率
  const renderProfitMargin = (margin: number) => {
    const color = margin >= 40 ? 'text-emerald-400' : margin >= 25 ? 'text-cyan-400' : margin >= 10 ? 'text-amber-400' : 'text-rose-400';
    return <span className={`font-mono font-medium ${color}`}>{margin.toFixed(1)}%</span>;
  };

  // 渲染迷你趋势图 (Sparkline)
  const renderSparkline = (values: number[]) => {
    if (!values || values.length < 2) return null;
    
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    const height = 24;
    const width = 60;
    const points = values.map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');
    
    // 判断趋势
    const trend = values[values.length - 1] >= values[0] ? 'up' : 'down';
    const strokeColor = trend === 'up' ? '#34d399' : '#f87171';
    
    return (
      <svg width={width} height={height} className="opacity-70">
        <polyline
          points={points}
          fill="none"
          stroke={strokeColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  // 排序图标
  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) {
      return <ArrowUpDown size={12} className="text-slate-600" />;
    }
    return sortOrder === 'desc' 
      ? <ChevronDown size={12} className="text-indigo-400" />
      : <ChevronRight size={12} className="text-indigo-400 rotate-[-90deg]" />;
  };

  return (
    <div className="glass-panel rounded-2xl overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-white/5 bg-white/[0.02]">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Activity size={18} className="text-violet-400" />
              品类健康度分析
              {drillCategory && (
                <span className="text-sm font-normal text-slate-400 ml-2">
                  / {drillCategory}
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500 mt-1 font-mono uppercase tracking-wider">
              CATEGORY HEALTH METRICS · {periodInfo ? `${periodInfo.start} ~ ${periodInfo.end}` : ''}
            </p>
          </div>
          
          <div className="flex items-center gap-3 flex-wrap">
            {/* 返回按钮 */}
            {drillCategory && (
              <button
                onClick={handleBack}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 rounded-lg text-xs font-medium transition-all"
              >
                <ChevronLeft size={14} />
                返回上级
              </button>
            )}
            
            {/* 渠道下拉选择 */}
            <div className="relative">
              <button
                ref={channelButtonRef}
                onClick={() => setChannelDropdownOpen(!channelDropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-white transition-all"
              >
                <span className="text-cyan-400">渠道:</span>
                <span className="max-w-[80px] truncate">{channel || '全部'}</span>
                <ChevronDown size={12} className={`text-slate-400 transition-transform ${channelDropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              
              {channelDropdownOpen && (
                <div 
                  ref={channelDropdownRef}
                  className="absolute top-full left-0 mt-2 w-36 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden animate-fade-in-up"
                >
                  <button
                    onClick={() => handleChannelSelect('')}
                    className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors ${
                      channel === '' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-300 hover:bg-white/5'
                    }`}
                  >
                    <span>全部渠道</span>
                    {channel === '' && <Check size={12} className="text-cyan-400" />}
                  </button>
                  {channelList.map(ch => (
                    <button
                      key={ch}
                      onClick={() => handleChannelSelect(ch)}
                      className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors ${
                        channel === ch ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-300 hover:bg-white/5'
                      }`}
                    >
                      <span>{ch}</span>
                      {channel === ch && <Check size={12} className="text-cyan-400" />}
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            {/* 周期切换 */}
            <div className="flex items-center bg-slate-800/50 rounded-lg p-0.5 border border-white/5">
              {([7, 14, 30] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => handlePresetPeriod(p)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    periodMode === 'preset' && period === p
                      ? 'bg-violet-500 text-white shadow-lg'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {p}天
                </button>
              ))}
            </div>
            
            {/* 自定义日期按钮 */}
            <div className="relative">
              <button
                ref={calendarButtonRef}
                onClick={handleOpenCalendar}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all text-xs ${
                  periodMode === 'custom'
                    ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                    : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Calendar size={14} />
                <span>{periodMode === 'custom' && startDate && endDate ? `${startDate} ~ ${endDate}` : '自定义'}</span>
              </button>
              
              {/* 日历面板 */}
              {calendarOpen && (
                <div 
                  ref={calendarDropdownRef}
                  className="absolute top-full right-0 mt-2 p-5 rounded-xl border shadow-2xl bg-slate-900 border-white/10 z-50"
                  style={{ width: '580px' }}
                >
                  <style>{`
                    .health-calendar .rdp-months {
                      display: flex !important;
                      flex-direction: row !important;
                      gap: 2rem !important;
                    }
                    .health-calendar .rdp-month {
                      margin: 0 !important;
                    }
                  `}</style>
                  {storeDateRange?.min_date && storeDateRange?.max_date && (
                    <div className="mb-4 px-3 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                      <p className="text-xs text-indigo-300">
                        📅 可选数据范围: {storeDateRange.min_date} ~ {storeDateRange.max_date}
                      </p>
                    </div>
                  )}
                  <div className="health-calendar" style={{ display: 'flex', justifyContent: 'center' }}>
                    <DayPicker
                      mode="range"
                      numberOfMonths={2}
                      selected={selectedRange}
                      onSelect={setSelectedRange}
                      locale={zhCN}
                      disabled={isDateDisabled}
                      defaultMonth={maxDate ? new Date(maxDate.getFullYear(), maxDate.getMonth() - 1) : new Date()}
                      startMonth={minDate}
                      endMonth={maxDate}
                      showOutsideDays={false}
                      classNames={{
                        months: 'flex flex-row gap-8',
                        month_caption: 'flex justify-center items-center h-10 font-semibold text-sm text-slate-100',
                        nav: 'absolute top-0 left-0 right-0 flex justify-between px-2',
                        button_previous: 'w-8 h-8 rounded-lg bg-white/5 text-slate-400 flex items-center justify-center hover:bg-white/10 hover:text-slate-100',
                        button_next: 'w-8 h-8 rounded-lg bg-white/5 text-slate-400 flex items-center justify-center hover:bg-white/10 hover:text-slate-100',
                        weekday: 'text-slate-500 text-xs font-medium py-2',
                        day: 'w-9 h-9',
                        day_button: 'w-9 h-9 rounded-lg text-slate-300 text-sm hover:bg-white/10 hover:text-white transition-colors',
                        today: 'text-indigo-400 ring-1 ring-indigo-500 rounded-lg',
                        selected: 'bg-indigo-500 text-white rounded-lg',
                        range_start: 'bg-indigo-500 text-white rounded-l-lg rounded-r-none',
                        range_end: 'bg-indigo-500 text-white rounded-r-lg rounded-l-none',
                        range_middle: 'bg-indigo-500/20 text-indigo-300 rounded-none',
                        disabled: 'text-slate-600 opacity-40 cursor-not-allowed',
                        outside: 'text-slate-600 opacity-50',
                      }}
                      components={{
                        Chevron: ({ orientation }) => 
                          orientation === 'left' ? <ChevronLeft size={18} /> : <ChevronRight size={18} />,
                      }}
                    />
                  </div>
                  <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                    <div className="text-xs text-slate-400">
                      {selectedRange?.from && selectedRange?.to ? (
                        <span className="text-emerald-400 font-medium">
                          已选: {format(selectedRange.from, 'yyyy-MM-dd')} ~ {format(selectedRange.to, 'yyyy-MM-dd')}
                        </span>
                      ) : selectedRange?.from ? (
                        <span className="text-amber-400">请选择结束日期</span>
                      ) : (
                        <span>点击选择开始日期</span>
                      )}
                    </div>
                    <div className="flex gap-3">
                      <button onClick={() => setCalendarOpen(false)} className="px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors">取消</button>
                      <button
                        onClick={handleConfirmDate}
                        disabled={!selectedRange?.from || !selectedRange?.to}
                        className="px-5 py-2 bg-indigo-500 text-white rounded-lg text-xs font-medium hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        确认选择
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* 刷新按钮 */}
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="p-2 bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white border border-white/5 rounded-lg transition-all"
              title="刷新并重置排序"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-10 rounded-2xl">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-auto flex-1 relative">
        <table className="w-full divide-y divide-white/5 border-collapse" style={{ tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '140px' }} /> {/* 分类名称 */}
            <col style={{ width: '110px' }} /> {/* 销售额 */}
            <col style={{ width: '100px' }} /> {/* 销售环比 */}
            <col style={{ width: '80px' }} />  {/* 销量 */}
            <col style={{ width: '100px' }} /> {/* 销量环比 */}
            <col style={{ width: '110px' }} /> {/* 波动 */}
            <col style={{ width: '110px' }} /> {/* 折扣 */}
            <col style={{ width: '80px' }} />  {/* 利润率 */}
            <col style={{ width: '80px' }} />  {/* 趋势 */}
            {!drillCategory && <col style={{ width: '60px' }} />} {/* 操作 */}
          </colgroup>
          <thead className="sticky top-0 z-20">
            <tr className="bg-slate-900">
              <th className="px-3 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider font-mono sticky left-0 z-30 bg-slate-900 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.3)]">
                {drillCategory ? '三级分类' : '一级分类'}
              </th>
              <th 
                className="px-3 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('current_revenue')}
              >
                <div className="flex items-center justify-end gap-1">
                  销售额 <SortIcon column="current_revenue" />
                </div>
              </th>
              <th 
                className="px-3 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('growth_rate')}
              >
                <div className="flex items-center justify-end gap-1">
                  销售环比 <SortIcon column="growth_rate" />
                </div>
              </th>
              <th 
                className="px-3 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('current_quantity')}
              >
                <div className="flex items-center justify-end gap-1">
                  销量 <SortIcon column="current_quantity" />
                </div>
              </th>
              <th 
                className="px-3 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('quantity_growth_rate')}
              >
                <div className="flex items-center justify-end gap-1">
                  销量环比 <SortIcon column="quantity_growth_rate" />
                </div>
              </th>
              <th 
                className="px-3 py-3 text-center text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('volatility')}
              >
                <div className="flex items-center justify-center gap-1">
                  波动 <SortIcon column="volatility" />
                </div>
              </th>
              <th 
                className="px-3 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('avg_discount')}
              >
                <div className="flex items-center justify-end gap-1">
                  折扣 <SortIcon column="avg_discount" />
                </div>
              </th>
              <th 
                className="px-3 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono cursor-pointer hover:text-white transition-colors bg-slate-900"
                onClick={() => handleSort('profit_margin')}
              >
                <div className="flex items-center justify-end gap-1">
                  利润率 <SortIcon column="profit_margin" />
                </div>
              </th>
              <th className="px-3 py-3 text-center text-xs font-bold text-slate-400 uppercase tracking-wider font-mono bg-slate-900">
                趋势
              </th>
              {!drillCategory && (
                <th className="px-2 py-3 text-center text-xs font-bold text-slate-400 uppercase tracking-wider font-mono bg-slate-900">
                  操作
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={drillCategory ? 9 : 10} className="px-4 py-12 text-center text-slate-500">
                  暂无数据
                </td>
              </tr>
            ) : (
              sortedData.map((item, index) => (
                <tr 
                  key={item.name} 
                  className="hover:bg-white/[0.02] transition-colors group"
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  {/* 分类名称 - 冻结列 */}
                  <td className="px-3 py-3 whitespace-nowrap sticky left-0 z-10 bg-slate-900 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.3)] group-hover:bg-slate-800 overflow-hidden">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded flex items-center justify-center text-xs font-bold bg-violet-500/20 border border-violet-500/30 text-violet-300 flex-shrink-0">
                        {index + 1}
                      </div>
                      <span className="text-sm font-medium text-slate-200 truncate">{item.name}</span>
                    </div>
                  </td>
                  
                  {/* 销售额 */}
                  <td className="px-3 py-3 whitespace-nowrap text-right">
                    <span className="text-sm font-mono text-slate-300">
                      ¥{item.current_revenue.toLocaleString()}
                    </span>
                  </td>
                  
                  {/* 销售环比增长 */}
                  <td className="px-3 py-3 whitespace-nowrap text-right">
                    {renderGrowth(item.growth_rate)}
                  </td>
                  
                  {/* 销量 */}
                  <td className="px-3 py-3 whitespace-nowrap text-right">
                    <span className="text-sm font-mono text-slate-300">
                      {item.current_quantity.toLocaleString()}
                    </span>
                  </td>
                  
                  {/* 销量环比增长 */}
                  <td className="px-3 py-3 whitespace-nowrap text-right">
                    {renderGrowth(item.quantity_growth_rate)}
                  </td>
                  
                  {/* 波动系数 */}
                  <td className="px-3 py-3 whitespace-nowrap text-center">
                    {renderVolatility(item.volatility_level, item.volatility)}
                  </td>
                  
                  {/* 平均折扣 */}
                  <td className="px-3 py-3 whitespace-nowrap text-right">
                    {renderDiscount(item.avg_discount, item.discount_change)}
                  </td>
                  
                  {/* 利润率 */}
                  <td className="px-3 py-3 whitespace-nowrap text-right">
                    {renderProfitMargin(item.profit_margin)}
                  </td>
                  
                  {/* 趋势图 */}
                  <td className="px-3 py-3 whitespace-nowrap text-center">
                    <div className="flex justify-center">
                      {renderSparkline(item.daily_revenue)}
                    </div>
                  </td>
                  
                  {/* 下钻按钮 */}
                  {!drillCategory && (
                    <td className="px-2 py-3 text-center">
                      <button
                        onClick={() => handleDrill(item.name)}
                        className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-violet-400 hover:bg-violet-500/10 rounded transition-all mx-auto"
                      >
                        <Layers size={12} />
                        下钻
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-white/5 bg-slate-900/20 flex items-center justify-between">
        <span className="text-xs text-slate-500 font-mono">
          共 {data.length} 个{drillCategory ? '三级' : '一级'}分类
        </span>
        <span className="text-xs text-slate-500">
          点击表头可排序 · 点击「下钻」查看三级分类
        </span>
      </div>
    </div>
  );
};

export default CategoryHealthTable;
