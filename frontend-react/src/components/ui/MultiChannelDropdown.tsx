/**
 * 多选渠道下拉选择器组件
 * 专用于：全门店经营总览（支持同时选择多个渠道名）
 */
import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Filter, ChevronDown, Check, X } from 'lucide-react';

interface MultiChannelDropdownProps {
    selectedChannels: string[];
    channelList: string[];
    onSelect: (channels: string[]) => void;
    isDark: boolean;
    /** 高亮颜色主题，默认 indigo */
    accentColor?: 'indigo' | 'pink' | 'cyan' | 'emerald';
}

const accentColors = {
    indigo: { bg: 'bg-indigo-500/20', text: 'text-indigo-300', icon: 'text-indigo-400', border: 'border-indigo-500/30' },
    pink: { bg: 'bg-pink-500/20', text: 'text-pink-300', icon: 'text-pink-400', border: 'border-pink-500/30' },
    cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-300', icon: 'text-cyan-400', border: 'border-cyan-500/30' },
    emerald: { bg: 'bg-emerald-500/20', text: 'text-emerald-300', icon: 'text-emerald-400', border: 'border-emerald-500/30' },
};

const MultiChannelDropdown: React.FC<MultiChannelDropdownProps> = ({
    selectedChannels,
    channelList,
    onSelect,
    isDark,
    accentColor = 'indigo'
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const colors = accentColors[accentColor];

    const isAllSelected = selectedChannels.length === 0;

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

    // 显示文本
    const displayName = useMemo(() => {
        if (isAllSelected) return '全部渠道';
        if (selectedChannels.length === 1) return selectedChannels[0];
        return `已选 ${selectedChannels.length} 个渠道`;
    }, [selectedChannels, isAllSelected]);

    // 切换某个渠道的选中状态
    const toggleChannel = (ch: string) => {
        if (selectedChannels.includes(ch)) {
            // 取消选中 → 如果只剩一个被取消则回到全部
            const next = selectedChannels.filter(c => c !== ch);
            onSelect(next); // 空数组 = 全部
        } else {
            onSelect([...selectedChannels, ch]);
        }
    };

    // 全选/全不选
    const handleSelectAll = () => {
        onSelect([]); // 空数组 = 全部渠道
    };

    // 清除选择（回到全部）
    const handleClear = (e: React.MouseEvent) => {
        e.stopPropagation();
        onSelect([]);
    };

    return (
        <div className="relative">
            <button
                ref={buttonRef}
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-200 ${isDark
                    ? 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300'
                    : 'bg-black/5 hover:bg-black/10 border-black/10 text-slate-600'
                    } ${!isAllSelected ? colors.border : ''}`}
            >
                <Filter size={12} className={colors.icon} />
                <span className="max-w-[120px] truncate">{displayName}</span>
                {!isAllSelected && (
                    <span
                        onClick={handleClear}
                        className={`flex items-center justify-center w-4 h-4 rounded-full hover:bg-white/20 cursor-pointer ${colors.icon}`}
                        title="清除筛选"
                    >
                        <X size={10} />
                    </span>
                )}
                <ChevronDown size={12} className={`text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div
                    ref={dropdownRef}
                    className={`absolute top-full right-0 mt-2 w-48 rounded-xl border shadow-2xl z-50 overflow-hidden animate-fade-in-up ${isDark
                        ? 'bg-slate-900 border-white/10'
                        : 'bg-white border-black/10'
                        }`}
                >
                    <div className="max-h-72 overflow-y-auto custom-scrollbar">
                        {/* 全部渠道选项 */}
                        <button
                            onClick={handleSelectAll}
                            className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors border-b ${isDark ? 'border-white/5' : 'border-black/5'} ${isAllSelected
                                ? `${colors.bg} ${colors.text}`
                                : isDark ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 hover:bg-black/5'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-all ${isAllSelected
                                    ? `${colors.bg} ${colors.border} ${colors.icon}`
                                    : isDark ? 'border-white/20' : 'border-black/20'
                                    }`}>
                                    {isAllSelected && <Check size={10} />}
                                </div>
                                <span>全部渠道</span>
                            </div>
                        </button>

                        {/* 渠道列表 */}
                        {channelList.map(ch => {
                            const isChecked = selectedChannels.includes(ch);
                            return (
                                <button
                                    key={ch}
                                    onClick={() => toggleChannel(ch)}
                                    className={`w-full flex items-center justify-between px-4 py-2.5 text-xs transition-colors ${isChecked
                                        ? `${colors.bg} ${colors.text}`
                                        : isDark ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 hover:bg-black/5'
                                        }`}
                                >
                                    <div className="flex items-center gap-2">
                                        <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-all ${isChecked
                                            ? `${colors.bg} ${colors.border} ${colors.icon}`
                                            : isDark ? 'border-white/20' : 'border-black/20'
                                            }`}>
                                            {isChecked && <Check size={10} />}
                                        </div>
                                        <span>{ch}</span>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MultiChannelDropdown;
