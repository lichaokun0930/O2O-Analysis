/**
 * 对比周期日期选择器组件
 * 复用GlobalFilter的UI外观和交互方式，但数据和逻辑独立
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Calendar, ChevronDown, Check, ChevronLeft, ChevronRight } from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import { format, isAfter, isBefore, isValid, parse, differenceInDays } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import 'react-day-picker/style.css';

interface DateRangeSelection {
  from: Date | undefined;
  to?: Date | undefined;
}

interface ComparisonDatePickerProps {
  currentStart: string;
  currentEnd: string;
  previousStart: string;
  previousEnd: string;
  minDate?: string;
  maxDate?: string;
  onApply: (start: string, end: string) => void;
  onReset: () => void;
}

const quickOptions = [
  { days: 1, label: '昨日' },
  { days: 7, label: '近7天' },
  { days: 15, label: '近15天' },
  { days: 30, label: '近30天' },
];

const ComparisonDatePicker: React.FC<ComparisonDatePickerProps> = ({
  currentStart,
  currentEnd,
  previousStart,
  previousEnd,
  minDate,
  maxDate,
  onApply,
  onReset
}) => {
  const [quickDropdownOpen, setQuickDropdownOpen] = useState(false);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [selectedRange, setSelectedRange] = useState<DateRangeSelection | undefined>();
  
  const quickButtonRef = useRef<HTMLButtonElement>(null);
  const calendarButtonRef = useRef<HTMLButtonElement>(null);
  const quickDropdownRef = useRef<HTMLDivElement>(null);
  const calendarDropdownRef = useRef<HTMLDivElement>(null);

  // 解析日期范围
  const minDateObj = minDate ? parse(minDate, 'yyyy-MM-dd', new Date()) : undefined;
  const maxDateObj = maxDate ? parse(maxDate, 'yyyy-MM-dd', new Date()) : undefined;

  // 计算当前选择的天数
  const currentDays = currentStart && currentEnd 
    ? differenceInDays(parse(currentEnd, 'yyyy-MM-dd', new Date()), parse(currentStart, 'yyyy-MM-dd', new Date())) + 1
    : 0;

  // 判断是否是快捷选项
  const matchedQuickOption = quickOptions.find(opt => opt.days === currentDays);
  const isCustomRange = !matchedQuickOption && currentStart && currentEnd;

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      
      if (quickDropdownOpen && 
          quickButtonRef.current && !quickButtonRef.current.contains(target) &&
          quickDropdownRef.current && !quickDropdownRef.current.contains(target)) {
        setQuickDropdownOpen(false);
      }
      
      if (calendarOpen && 
          calendarButtonRef.current && !calendarButtonRef.current.contains(target) &&
          calendarDropdownRef.current && !calendarDropdownRef.current.contains(target)) {
        setCalendarOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [quickDropdownOpen, calendarOpen]);

  // 处理快捷选择
  const handleQuickSelect = useCallback((days: number) => {
    if (!maxDate) return;
    
    const endDate = parse(maxDate, 'yyyy-MM-dd', new Date());
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - days + 1);
    
    onApply(format(startDate, 'yyyy-MM-dd'), format(endDate, 'yyyy-MM-dd'));
    setQuickDropdownOpen(false);
  }, [maxDate, onApply]);

  // 处理日历日期选择
  const handleRangeSelect = useCallback((range: DateRangeSelection | undefined) => {
    setSelectedRange(range);
  }, []);

  // 确认日期选择
  const handleConfirm = useCallback(() => {
    if (selectedRange?.from && selectedRange?.to) {
      onApply(
        format(selectedRange.from, 'yyyy-MM-dd'),
        format(selectedRange.to, 'yyyy-MM-dd')
      );
      setCalendarOpen(false);
    }
  }, [selectedRange, onApply]);

  // 打开日历
  const handleOpenCalendar = useCallback(() => {
    if (currentStart && currentEnd) {
      const from = parse(currentStart, 'yyyy-MM-dd', new Date());
      const to = parse(currentEnd, 'yyyy-MM-dd', new Date());
      if (isValid(from) && isValid(to)) {
        setSelectedRange({ from, to });
      }
    } else {
      setSelectedRange(undefined);
    }
    setCalendarOpen(true);
  }, [currentStart, currentEnd]);

  // 判断日期是否禁用
  const isDateDisabled = useCallback((date: Date) => {
    if (minDateObj && isBefore(date, minDateObj)) return true;
    if (maxDateObj && isAfter(date, maxDateObj)) return true;
    return false;
  }, [minDateObj, maxDateObj]);

  // 计算下拉框位置
  const getDropdownPosition = (buttonRef: React.RefObject<HTMLButtonElement>) => {
    if (!buttonRef.current) return { top: 0, left: 0 };
    const rect = buttonRef.current.getBoundingClientRect();
    return {
      top: rect.bottom + 8,
      left: rect.left
    };
  };

  // 获取当前显示的标签
  const getCurrentLabel = () => {
    if (matchedQuickOption) {
      return matchedQuickOption.label;
    }
    if (isCustomRange) {
      return `${currentStart} ~ ${currentEnd}`;
    }
    return '选择日期';
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <Calendar size={18} className="text-indigo-400" />
        <h3 className="text-sm font-semibold text-white">对比周期选择</h3>
      </div>
      
      <div className="space-y-3">
        {/* 快捷选择 + 自定义按钮 */}
        <div className="flex gap-2">
          {/* 快捷选择下拉框 */}
          <div className="relative flex-1">
            <button
              ref={quickButtonRef}
              onClick={() => setQuickDropdownOpen(!quickDropdownOpen)}
              className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-600 rounded-lg text-sm text-white transition-all"
            >
              <span className="truncate">{getCurrentLabel()}</span>
              <ChevronDown size={14} className={`text-slate-400 transition-transform flex-shrink-0 ${quickDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {quickDropdownOpen && createPortal(
              <div 
                ref={quickDropdownRef}
                style={getDropdownPosition(quickButtonRef)}
                className="fixed w-40 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-[9999] overflow-hidden animate-fade-in-up"
              >
                {quickOptions.map(({ days, label }) => (
                  <button
                    key={days}
                    onClick={() => handleQuickSelect(days)}
                    className={`w-full flex items-center justify-between px-4 py-2.5 text-sm transition-colors ${
                      currentDays === days ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-300 hover:bg-white/5'
                    }`}
                  >
                    <span>{label}</span>
                    {currentDays === days && <Check size={14} className="text-emerald-400" />}
                  </button>
                ))}
              </div>,
              document.body
            )}
          </div>

          {/* 自定义日历按钮 */}
          <button
            ref={calendarButtonRef}
            onClick={handleOpenCalendar}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${
              isCustomRange
                ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-900 border-slate-600 text-slate-400 hover:bg-slate-800 hover:text-white hover:border-slate-500'
            }`}
          >
            <Calendar size={16} className={isCustomRange ? 'text-indigo-400' : 'text-slate-400'} />
            <span className="text-sm">自定义</span>
          </button>
        </div>

        {/* 上期显示（自动计算） */}
        <div className="bg-slate-900/50 rounded p-3 text-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">本期：</span>
            <span className="text-indigo-300 font-mono">{currentStart} ~ {currentEnd}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">上期：</span>
            <span className="text-emerald-300 font-mono">{previousStart} ~ {previousEnd}</span>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <button
            onClick={onReset}
            className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors"
          >
            重置
          </button>
        </div>
      </div>

      {/* 双月日历面板 */}
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
          {minDate && maxDate && (
            <div className="mb-4 px-3 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
              <p className="text-xs text-indigo-300">
                📅 可选数据范围: {minDate} ~ {maxDate}
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
              defaultMonth={maxDateObj ? new Date(maxDateObj.getFullYear(), maxDateObj.getMonth() - 1) : new Date()}
              startMonth={minDateObj}
              endMonth={maxDateObj}
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

export default ComparisonDatePicker;
