import React, { useMemo, useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useChart } from '@/hooks/useChart';
import { Layers, ChevronDown, Check, Search, X } from 'lucide-react';
import { ordersApi, CategoryHourlyTrend } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';

interface Props {
  selectedDate: string | null;
  selectedDateRange?: { start: string; end: string } | null;  // 🆕 日期范围选择（从销售趋势图点击）
  theme: 'dark' | 'light';
}

const CategoryTrendChart: React.FC<Props> = ({ selectedDate, selectedDateRange, theme }) => {
  const [data, setData] = useState<CategoryHourlyTrend | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);  // 用户选择的分类
  
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
        // 🆕 优先级：销售趋势图点击的日期范围 > 销售趋势图点击的单日期 > 全局日期范围 > 默认近7天
        const params: { store_name: string; date?: string; start_date?: string; end_date?: string } = {
          store_name: selectedStore
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
        // 否则不传日期参数，后端返回默认近7天数据
        
        const res = await ordersApi.getCategoryHourlyTrend(params);
        if (res.success && res.data) {
          setData(res.data);
          // 重置选择（使用默认 TOP5）
          setSelectedCategories([]);
        }
      } catch (error) {
        console.error('获取品类趋势数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [selectedStore, selectedDate, selectedDateRange, dateRange.type, dateRange.start, dateRange.end]);

  // 计算要显示的分类（用户选择的 或 默认TOP5）
  const displayCategories = useMemo(() => {
    if (!data || data.categories.length === 0) return [];
    
    if (selectedCategories.length > 0) {
      // 🆕 用户选择了分类，只显示用户选择的（不补齐）
      return data.categories.filter(c => selectedCategories.includes(c));
    }
    
    // 默认显示 TOP5（API 已按销售额排序）
    return data.categories.slice(0, 5);
  }, [data, selectedCategories]);

  // 过滤后的 series 数据
  const filteredSeries = useMemo(() => {
    if (!data) return [];
    return data.series.filter(s => displayCategories.includes(s.name));
  }, [data, displayCategories]);

  // 构建ECharts配置
  const option: echarts.EChartsOption = useMemo(() => {
    if (!data || data.labels.length === 0 || filteredSeries.length === 0) {
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

    const colors = ['#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1'];

    // 🆕 构建完整的 series 配置，确保只包含选中的分类
    const seriesConfig = filteredSeries.map((s, index) => ({
      name: s.name,
      type: 'line' as const,
      stack: 'Total',
      smooth: true,
      areaStyle: { opacity: 0.8 },
      emphasis: { focus: 'series' as const },
      showSymbol: false,
      data: s.data,
      itemStyle: { color: colors[index % colors.length] }
    }));

    return {
      color: colors,
      graphic: [],  // 清除"暂无数据"
      grid: { left: 10, right: 10, top: 40, bottom: 10, containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        textStyle: { color: isDark ? '#fff' : '#0f172a' },
        borderWidth: 0,
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return '';
          const dateStr = params[0].axisValue;
          const dataIndex = params[0].dataIndex;
          
          // 🆕 从所有分类中获取该时间点的数据，按销售额排序取TOP5
          const allCategoryData = data.series.map(s => ({
            name: s.name,
            value: s.data[dataIndex] || 0
          })).filter(item => item.value > 0)  // 过滤掉销售额为0的
            .sort((a, b) => b.value - a.value);  // 按销售额降序
          
          // 计算所有分类总销售额
          const allCategoriesTotal = allCategoryData.reduce((sum, item) => sum + item.value, 0);
          
          // 如果用户选择了分类，显示选择的分类；否则显示该时间点的TOP5
          const isUserSelected = selectedCategories.length > 0;
          const displayData = isUserSelected 
            ? allCategoryData.filter(item => selectedCategories.includes(item.name))
            : allCategoryData.slice(0, 5);
          
          // 计算显示分类的合计
          const displayTotal = displayData.reduce((sum, item) => sum + item.value, 0);
          
          let html = `<div style="font-size:12px;font-weight:bold;margin-bottom:8px;color:${subTitleColor}">${dateStr} 合计: ¥${displayTotal.toLocaleString()}</div>`;
          
          displayData.forEach((item, index) => {
            const percentage = allCategoriesTotal > 0 ? ((item.value / allCategoriesTotal) * 100).toFixed(1) : '0.0';
            const color = colors[index % colors.length];
            html += `
              <div style="display:flex;justify-content:space-between;align-items:center;gap:24px;font-size:12px;margin-bottom:4px">
                <div style="display:flex;align-items:center;gap:6px">
                  <span style="width:8px;height:8px;border-radius:50%;background:${color}"></span>
                  <span style="color:${isDark ? '#e2e8f0' : '#475569'}">${item.name}</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px">
                  <span style="font-weight:bold;color:${isDark ? '#fff' : '#0f172a'}">¥${item.value.toLocaleString()}</span>
                  <span style="font-size:10px;width:40px;text-align:right;color:${subTitleColor}">${percentage}%</span>
                </div>
              </div>
            `;
          });
          return html;
        }
      },
      legend: {
        data: displayCategories,
        top: 0,
        textStyle: { color: subTitleColor, fontSize: 11 },
        icon: 'roundRect'
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.labels,
        axisLabel: { color: subTitleColor, fontSize: 10 },
        axisLine: { show: false }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { type: 'dashed', color: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' } },
        axisLabel: { color: subTitleColor, fontSize: 10, formatter: (val: number) => `¥${val/1000}k` }
      },
      series: seriesConfig
    };
  }, [data, filteredSeries, displayCategories, isDark, subTitleColor]);

  const chartRef = useChart(option, [data, theme, selectedCategories, displayCategories.length], theme);

  // 处理分类选择
  const handleCategoryToggle = (category: string) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  // 重置为默认 TOP5
  const handleResetCategories = () => {
    setSelectedCategories([]);
  };

  // 🆕 计算当前显示的日期范围描述
  const dateRangeLabel = useMemo(() => {
    if (selectedDateRange) {
      // 如果起止日期相同，只显示单个日期
      if (selectedDateRange.start === selectedDateRange.end) {
        return `${selectedDateRange.start.slice(5)} 品类销售走势`;
      }
      return `${selectedDateRange.start.slice(5)} ~ ${selectedDateRange.end.slice(5)} 品类销售走势`;
    }
    if (selectedDate) {
      return `${selectedDate.slice(5)} 分时段品类走势`;
    }
    if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
      // 如果起止日期相同，只显示单个日期
      if (dateRange.start === dateRange.end) {
        return `${dateRange.start.slice(5)} 品类销售走势`;
      }
      return `${dateRange.start.slice(5)} ~ ${dateRange.end.slice(5)} 品类销售走势`;
    }
    return '近7天品类销售占比';
  }, [selectedDateRange, selectedDate, dateRange]);

  const dateRangeMode = useMemo(() => {
    if (selectedDateRange || (dateRange.type !== 'all' && dateRange.start && dateRange.end)) {
      return 'DATE RANGE TREND';
    }
    if (selectedDate) {
      return 'HOURLY TREND & SHARE';
    }
    return 'CATEGORY REVENUE COMPOSITION';
  }, [selectedDateRange, selectedDate, dateRange]);

  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col relative overflow-hidden transition-all duration-500">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/10 z-20 rounded-2xl">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
        </div>
      )}
      
      <div className="mb-2 flex justify-between items-start">
        <div>
          <h3 className="text-lg font-bold flex items-center gap-2" style={{color: titleColor}}>
            <Layers size={18} className="text-violet-400" />
            {dateRangeLabel}
          </h3>
          <p className="text-xs mt-1 font-mono uppercase tracking-wider opacity-70" style={{color: subTitleColor}}>
            {dateRangeMode} · 
            {selectedCategories.length > 0 
              ? ` 已选 ${selectedCategories.length} 个分类` 
              : ` TOP ${displayCategories.length}`}
          </p>
        </div>
        
        {/* 分类选择器 */}
        <CategorySelector
          categories={data?.categories || []}
          selectedCategories={selectedCategories}
          onToggle={handleCategoryToggle}
          onReset={handleResetCategories}
          isDark={isDark}
        />
      </div>
      
      <div className="flex-1 w-full min-h-[250px]">
        <div ref={chartRef} className="w-full h-full" />
      </div>
    </div>
  );
};

// 分类选择器组件（带搜索框）
interface CategorySelectorProps {
  categories: string[];
  selectedCategories: string[];
  onToggle: (category: string) => void;
  onReset: () => void;
  isDark: boolean;
}

const CategorySelector: React.FC<CategorySelectorProps> = ({ 
  categories, 
  selectedCategories, 
  onToggle, 
  onReset,
  isDark 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (isOpen && 
          buttonRef.current && !buttonRef.current.contains(target) &&
          dropdownRef.current && !dropdownRef.current.contains(target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // 打开时聚焦搜索框
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // 过滤分类
  const filteredCategories = useMemo(() => {
    if (!searchTerm) return categories;
    const term = searchTerm.toLowerCase();
    return categories.filter(c => c.toLowerCase().includes(term));
  }, [categories, searchTerm]);

  const displayText = selectedCategories.length > 0 
    ? `已选 ${selectedCategories.length} 项` 
    : 'TOP 5';

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-200 ${
          isDark 
            ? 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300' 
            : 'bg-black/5 hover:bg-black/10 border-black/10 text-slate-600'
        } ${selectedCategories.length > 0 ? 'border-violet-500/50 bg-violet-500/10' : ''}`}
      >
        <Layers size={12} className="text-violet-400" />
        <span>{displayText}</span>
        <ChevronDown size={12} className={`text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div 
          ref={dropdownRef}
          className={`absolute top-full right-0 mt-2 w-56 rounded-xl border shadow-2xl z-50 overflow-hidden animate-fade-in-up ${
            isDark 
              ? 'bg-slate-900 border-white/10' 
              : 'bg-white border-black/10'
          }`}
        >
          {/* 搜索框 */}
          <div className={`p-2 border-b ${isDark ? 'border-white/10' : 'border-black/10'}`}>
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${isDark ? 'bg-white/5' : 'bg-black/5'}`}>
              <Search size={14} className="text-slate-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索分类..."
                className={`flex-1 bg-transparent text-xs outline-none ${isDark ? 'text-white placeholder-slate-500' : 'text-slate-900 placeholder-slate-400'}`}
              />
              {searchTerm && (
                <button onClick={() => setSearchTerm('')} className="text-slate-400 hover:text-slate-300">
                  <X size={12} />
                </button>
              )}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className={`px-2 py-1.5 border-b flex justify-between items-center ${isDark ? 'border-white/10' : 'border-black/10'}`}>
            <span className={`text-[10px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              {filteredCategories.length} 个分类
            </span>
            {selectedCategories.length > 0 && (
              <button
                onClick={onReset}
                className="text-[10px] text-violet-400 hover:text-violet-300"
              >
                重置为 TOP5
              </button>
            )}
          </div>

          {/* 分类列表 */}
          <div className="max-h-64 overflow-y-auto custom-scrollbar">
            {filteredCategories.length === 0 ? (
              <div className={`px-4 py-3 text-xs text-center ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                未找到匹配的分类
              </div>
            ) : (
              filteredCategories.map((category) => {
                const isSelected = selectedCategories.includes(category);
                // 只有在没有搜索且没有手动选择时，才显示 TOP 标记
                const originalIndex = categories.indexOf(category);
                const isTop5 = !searchTerm && selectedCategories.length === 0 && originalIndex < 5 && originalIndex >= 0;
                
                return (
                  <button
                    key={category}
                    onClick={() => onToggle(category)}
                    className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors ${
                      isSelected || isTop5
                        ? 'bg-violet-500/20 text-violet-300' 
                        : isDark ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 hover:bg-black/5'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${isSelected || isTop5 ? 'bg-violet-400' : isDark ? 'bg-slate-600' : 'bg-slate-300'}`}></span>
                      <span className="truncate max-w-[140px]">{category}</span>
                      {isTop5 && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-violet-500/30 text-violet-300">TOP{originalIndex + 1}</span>
                      )}
                    </div>
                    {isSelected && <Check size={12} className="text-violet-400" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryTrendChart;
