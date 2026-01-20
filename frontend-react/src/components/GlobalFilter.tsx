/**
 * 全局筛选器组件 - 门店选择 + 日期范围 + 双月日历选择器
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Store, Calendar, ChevronDown, Check, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import { format, isAfter, isBefore, isValid, parse } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { useGlobalContext, type DateRangeType } from '../store/GlobalContext';
import 'react-day-picker/style.css';

interface DateRangeSelection {
  from: Date | undefined;
  to?: Date | undefined;
}

const dateOptions: { type: DateRangeType; label: string }[] = [
  { type: 'all', label: '全部时间' },
  { type: 'yesterday', label: '昨日' },
  { type: '7days', label: '近7天' },
  { type: '30days', label: '近30天' },
  { type: 'thisWeek', label: '本周' },
  { type: 'thisMonth', label: '本月' },
];

const GlobalFilter: React.FC = () => {
  const { 
    stores, 
    selectedStore, 
    setSelectedStore, 
    storesLoading,
    dateRange,
    setQuickDateRange,
    setDateRange,
    storeDateRange
  } = useGlobalContext();

  const [storeDropdownOpen, setStoreDropdownOpen] = useState(false);
  const [dateDropdownOpen, setDateDropdownOpen] = useState(false);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRange, setSelectedRange] = useState<DateRangeSelection | undefined>();
  
  const storeButtonRef = useRef<HTMLButtonElement>(null);
  const dateButtonRef = useRef<HTMLButtonElement>(null);
  const calendarButtonRef = useRef<HTMLButtonElement>(null);
  
  const storeDropdownRef = useRef<HTMLDivElement>(null);
  const dateDropdownRef = useRef<HTMLDivElement>(null);
  const calendarDropdownRef = useRef<HTMLDivElement>(null);

  // 解析门店数据日期范围
  const minDate = storeDateRange?.min_date ? parse(storeDateRange.min_date, 'yyyy-MM-dd', new Date()) : undefined;
  const maxDate = storeDateRange?.max_date ? parse(storeDateRange.max_date, 'yyyy-MM-dd', new Date()) : undefined;

  // 点击外部关闭 - 使用 mousedown 而不是 click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      
      // 门店下拉框
      if (storeDropdownOpen && 
          storeButtonRef.current && !storeButtonRef.current.contains(target) &&
          storeDropdownRef.current && !storeDropdownRef.current.contains(target)) {
        setStoreDropdownOpen(false);
      }
      
      // 日期下拉框
      if (dateDropdownOpen && 
          dateButtonRef.current && !dateButtonRef.current.contains(target) &&
          dateDropdownRef.current && !dateDropdownRef.current.contains(target)) {
        setDateDropdownOpen(false);
      }
      
      // 日历下拉框
      if (calendarOpen && 
          calendarButtonRef.current && !calendarButtonRef.current.contains(target) &&
          calendarDropdownRef.current && !calendarDropdownRef.current.contains(target)) {
        setCalendarOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [storeDropdownOpen, dateDropdownOpen, calendarOpen]);

  // 去掉门店名称中的订单数后缀，如 "门店名 (19,477单)" -> "门店名"
  const cleanStoreName = (label: string) => {
    return label.replace(/\s*\([0-9,]+单\)\s*$/, '').trim();
  };

  // 过滤门店
  const filteredStores = stores.filter(store => 
    cleanStoreName(store.label).toLowerCase().includes(searchTerm.toLowerCase())
  );

  // 获取当前选中的门店名称
  const selectedStoreName = selectedStore 
    ? cleanStoreName(stores.find(s => s.value === selectedStore)?.label || selectedStore)
    : '选择门店';

  // 获取当前日期范围标签
  const currentDateLabel = dateRange.type === 'custom' 
    ? `${dateRange.start} ~ ${dateRange.end}`
    : dateOptions.find(d => d.type === dateRange.type)?.label || '全部';

  // 处理门店选择
  const handleStoreSelect = useCallback((storeValue: string) => {
    setSelectedStore(storeValue);
    setStoreDropdownOpen(false);
    setSearchTerm('');
  }, [setSelectedStore]);

  // 处理日期快捷选择
  const handleDateSelect = useCallback((type: DateRangeType) => {
    setQuickDateRange(type);
    setDateDropdownOpen(false);
  }, [setQuickDateRange]);

  // 处理日历日期选择
  const handleRangeSelect = useCallback((range: DateRangeSelection | undefined) => {
    setSelectedRange(range);
  }, []);

  // 确认日期选择
  const handleConfirm = useCallback(() => {
    if (selectedRange?.from && selectedRange?.to) {
      setDateRange({
        type: 'custom',
        start: format(selectedRange.from, 'yyyy-MM-dd'),
        end: format(selectedRange.to, 'yyyy-MM-dd')
      });
      setCalendarOpen(false);
    }
  }, [selectedRange, setDateRange]);

  // 打开日历
  const handleOpenCalendar = useCallback(() => {
    if (dateRange.type === 'custom' && dateRange.start && dateRange.end) {
      const from = parse(dateRange.start, 'yyyy-MM-dd', new Date());
      const to = parse(dateRange.end, 'yyyy-MM-dd', new Date());
      if (isValid(from) && isValid(to)) {
        setSelectedRange({ from, to });
      }
    } else {
      setSelectedRange(undefined);
    }
    setCalendarOpen(true);
  }, [dateRange]);

  // 判断日期是否禁用
  const isDateDisabled = useCallback((date: Date) => {
    if (minDate && isBefore(date, minDate)) return true;
    if (maxDate && isAfter(date, maxDate)) return true;
    return false;
  }, [minDate, maxDate]);

  // 计算下拉框位置
  const getDropdownPosition = (buttonRef: React.RefObject<HTMLButtonElement>) => {
    if (!buttonRef.current) return { top: 0, left: 0 };
    const rect = buttonRef.current.getBoundingClientRect();
    return {
      top: rect.bottom + 8,
      left: rect.left
    };
  };

  return (
    <div className="flex items-center gap-3">
      {/* ========== 门店选择器 ========== */}
      <div className="relative">
        <button
          ref={storeButtonRef}
          onClick={() => setStoreDropdownOpen(!storeDropdownOpen)}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white transition-all"
        >
          <Store size={16} className="text-indigo-400" />
          <span className="max-w-[120px] truncate">{selectedStoreName}</span>
          <ChevronDown size={14} className={`text-slate-400 transition-transform ${storeDropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {storeDropdownOpen && createPortal(
          <div 
            ref={storeDropdownRef}
            style={getDropdownPosition(storeButtonRef)}
            className="fixed w-64 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-[9999] overflow-hidden animate-fade-in-up"
          >
            {/* 搜索框 */}
            <div className="p-2 border-b border-white/10">
              <div className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg">
                <Search size={14} className="text-slate-400" />
                <input
                  type="text"
                  placeholder="搜索门店..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                  autoFocus
                />
              </div>
            </div>

            {/* 门店列表 */}
            <div className="max-h-64 overflow-y-auto custom-scrollbar">
              {/* 提示选择门店 */}
              <div className="px-4 py-2 text-xs text-slate-500 border-b border-white/5">
                请选择一个门店查看数据
              </div>

              {storesLoading ? (
                <div className="px-4 py-8 text-center text-slate-500 text-sm">加载中...</div>
              ) : filteredStores.length === 0 ? (
                <div className="px-4 py-8 text-center text-slate-500 text-sm">
                  {searchTerm ? '未找到匹配的门店' : '暂无门店数据'}
                </div>
              ) : (
                filteredStores.map(store => (
                  <button
                    key={store.value}
                    onClick={() => handleStoreSelect(store.value)}
                    className={`w-full flex items-center justify-between px-4 py-2.5 text-sm transition-colors ${
                      selectedStore === store.value ? 'bg-indigo-500/20 text-indigo-300' : 'text-slate-300 hover:bg-white/5'
                    }`}
                  >
                    <span>{cleanStoreName(store.label)}</span>
                    {selectedStore === store.value && <Check size={14} className="text-indigo-400" />}
                  </button>
                ))
              )}
            </div>
          </div>,
          document.body
        )}
      </div>

      {/* ========== 日期快捷选择器 ========== */}
      <div className="relative">
        <button
          ref={dateButtonRef}
          onClick={() => setDateDropdownOpen(!dateDropdownOpen)}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white transition-all"
        >
          <Calendar size={16} className="text-emerald-400" />
          <span className="max-w-[180px] truncate">{currentDateLabel}</span>
          <ChevronDown size={14} className={`text-slate-400 transition-transform ${dateDropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {dateDropdownOpen && createPortal(
          <div 
            ref={dateDropdownRef}
            style={getDropdownPosition(dateButtonRef)}
            className="fixed w-40 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-[9999] overflow-hidden animate-fade-in-up"
          >
            {dateOptions.map(({ type, label }) => (
              <button
                key={type}
                onClick={() => handleDateSelect(type)}
                className={`w-full flex items-center justify-between px-4 py-2.5 text-sm transition-colors ${
                  dateRange.type === type ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-300 hover:bg-white/5'
                }`}
              >
                <span>{label}</span>
                {dateRange.type === type && <Check size={14} className="text-emerald-400" />}
              </button>
            ))}
          </div>,
          document.body
        )}
      </div>

      {/* ========== 日历选择器按钮 ========== */}
      <button
        ref={calendarButtonRef}
        onClick={handleOpenCalendar}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${
          dateRange.type === 'custom'
            ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
            : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white hover:border-white/20'
        }`}
      >
        <Calendar size={16} className={dateRange.type === 'custom' ? 'text-indigo-400' : 'text-slate-400'} />
        <span className="text-sm">自定义</span>
      </button>

      {/* ========== 双月日历面板 ========== */}
      {calendarOpen && createPortal(
        <div 
          ref={calendarDropdownRef}
          style={{
            top: calendarButtonRef.current?.getBoundingClientRect().bottom! + 8,
            left: Math.min(
              calendarButtonRef.current?.getBoundingClientRect().left || 0,
              window.innerWidth - 620
            )
          }}
          className="fixed z-[9999] p-5 rounded-xl border shadow-2xl bg-slate-900 border-white/10"
        >
          {/* 数据范围提示 */}
          {storeDateRange?.min_date && storeDateRange?.max_date && (
            <div className="mb-4 px-3 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
              <p className="text-xs text-indigo-300">
                📅 可选数据范围: {storeDateRange.min_date} ~ {storeDateRange.max_date}
              </p>
            </div>
          )}

          {/* 日历样式 */}
          <style>{`
            .calendar-container .rdp-root {
              --rdp-accent-color: #6366f1;
              --rdp-accent-background-color: rgba(99, 102, 241, 0.2);
            }
            .calendar-container .rdp-months {
              display: flex;
              gap: 2rem;
            }
            .calendar-container .rdp-month_caption {
              display: flex;
              justify-content: center;
              align-items: center;
              height: 40px;
              font-weight: 600;
              font-size: 14px;
              color: #f1f5f9;
            }
            .calendar-container .rdp-nav {
              position: absolute;
              top: 0;
              left: 0;
              right: 0;
              display: flex;
              justify-content: space-between;
              padding: 0 8px;
            }
            .calendar-container .rdp-button_previous,
            .calendar-container .rdp-button_next {
              width: 32px;
              height: 32px;
              border-radius: 8px;
              background: rgba(255, 255, 255, 0.05);
              color: #94a3b8;
              display: flex;
              align-items: center;
              justify-content: center;
              border: none;
              cursor: pointer;
              transition: all 0.15s;
            }
            .calendar-container .rdp-button_previous:hover,
            .calendar-container .rdp-button_next:hover {
              background: rgba(255, 255, 255, 0.1);
              color: #f1f5f9;
            }
            .calendar-container .rdp-weekday {
              color: #64748b;
              font-size: 12px;
              font-weight: 500;
              padding: 8px 0;
            }
            .calendar-container .rdp-day {
              width: 36px;
              height: 36px;
            }
            .calendar-container .rdp-day button {
              width: 36px;
              height: 36px;
              border-radius: 8px;
              color: #cbd5e1;
              font-weight: 400;
              font-size: 13px;
              transition: all 0.15s;
              border: none;
              background: transparent;
              cursor: pointer;
            }
            .calendar-container .rdp-day button:hover:not(:disabled) {
              background: rgba(255, 255, 255, 0.08);
              color: #f1f5f9;
            }
            .calendar-container .rdp-today button {
              color: #818cf8;
              box-shadow: inset 0 0 0 1px #6366f1;
            }
            .calendar-container .rdp-selected button,
            .calendar-container .rdp-range_start button,
            .calendar-container .rdp-range_end button {
              background: #6366f1 !important;
              color: white !important;
            }
            .calendar-container .rdp-range_middle button {
              background: rgba(99, 102, 241, 0.2) !important;
              color: #a5b4fc !important;
              border-radius: 0 !important;
            }
            .calendar-container .rdp-range_start button {
              border-radius: 8px 0 0 8px !important;
            }
            .calendar-container .rdp-range_end button {
              border-radius: 0 8px 8px 0 !important;
            }
            .calendar-container .rdp-disabled button {
              color: #334155 !important;
              opacity: 0.4;
              cursor: not-allowed !important;
            }
            .calendar-container .rdp-disabled button:hover {
              background: transparent !important;
            }
            .calendar-container .rdp-outside button {
              color: #475569;
              opacity: 0.5;
            }
          `}</style>
          
          {/* 双月日历 */}
          <div className="calendar-container">
            <DayPicker
              mode="range"
              numberOfMonths={2}
              selected={selectedRange}
              onSelect={handleRangeSelect}
              locale={zhCN}
              disabled={isDateDisabled}
              defaultMonth={maxDate ? new Date(maxDate.getFullYear(), maxDate.getMonth() - 1) : new Date()}
              startMonth={minDate}
              endMonth={maxDate}
              showOutsideDays={false}
              components={{
                Chevron: ({ orientation }) => 
                  orientation === 'left' ? <ChevronLeft size={18} /> : <ChevronRight size={18} />,
              }}
            />
          </div>

          {/* 底部操作栏 */}
          <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
            <div className="text-sm text-slate-400">
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
              <button
                onClick={() => setCalendarOpen(false)}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleConfirm}
                disabled={!selectedRange?.from || !selectedRange?.to}
                className="px-5 py-2 bg-indigo-500 text-white rounded-lg text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                确认选择
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default GlobalFilter;
