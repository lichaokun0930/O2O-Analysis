/**
 * 渠道下拉选择器组件
 * 复用于：销售趋势分析、营销成本趋势等图表
 */
import React, { useState, useRef, useEffect } from 'react';
import { Filter, ChevronDown, Check } from 'lucide-react';

interface ChannelDropdownProps {
  selectedChannel: string;
  channelList: string[];
  onSelect: (channel: string) => void;
  isDark: boolean;
  /** 高亮颜色主题，默认 indigo */
  accentColor?: 'indigo' | 'pink' | 'cyan' | 'emerald';
}

const accentColors = {
  indigo: { bg: 'bg-indigo-500/20', text: 'text-indigo-300', icon: 'text-indigo-400' },
  pink: { bg: 'bg-pink-500/20', text: 'text-pink-300', icon: 'text-pink-400' },
  cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-300', icon: 'text-cyan-400' },
  emerald: { bg: 'bg-emerald-500/20', text: 'text-emerald-300', icon: 'text-emerald-400' },
};

const ChannelDropdown: React.FC<ChannelDropdownProps> = ({ 
  selectedChannel, 
  channelList, 
  onSelect, 
  isDark,
  accentColor = 'indigo'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const colors = accentColors[accentColor];

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (isOpen && 
          buttonRef.current && !buttonRef.current.contains(target) &&
          dropdownRef.current && !dropdownRef.current.contains(target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const displayName = selectedChannel === 'all' ? '全部渠道' : selectedChannel;

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-200 ${
          isDark 
            ? 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300' 
            : 'bg-black/5 hover:bg-black/10 border-black/10 text-slate-600'
        }`}
      >
        <Filter size={12} className={colors.icon} />
        <span className="max-w-[80px] truncate">{displayName}</span>
        <ChevronDown size={12} className={`text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div 
          ref={dropdownRef}
          className={`absolute top-full right-0 mt-2 w-40 rounded-xl border shadow-2xl z-50 overflow-hidden animate-fade-in-up ${
            isDark 
              ? 'bg-slate-900 border-white/10' 
              : 'bg-white border-black/10'
          }`}
        >
          <div className="max-h-64 overflow-y-auto custom-scrollbar">
            {/* 全部渠道选项 */}
            <button
              onClick={() => { onSelect('all'); setIsOpen(false); }}
              className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors ${
                selectedChannel === 'all' 
                  ? `${colors.bg} ${colors.text}` 
                  : isDark ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 hover:bg-black/5'
              }`}
            >
              <span>全部渠道</span>
              {selectedChannel === 'all' && <Check size={12} className={colors.icon} />}
            </button>
            
            {/* 渠道列表 */}
            {channelList.map(ch => (
              <button
                key={ch}
                onClick={() => { onSelect(ch); setIsOpen(false); }}
                className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors ${
                  selectedChannel === ch 
                    ? `${colors.bg} ${colors.text}` 
                    : isDark ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 hover:bg-black/5'
                }`}
              >
                <span>{ch}</span>
                {selectedChannel === ch && <Check size={12} className={colors.icon} />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChannelDropdown;
