import React, { useEffect, useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Loader2 } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  change?: number;  // 可选，undefined时不显示环比
  subtext: string;
  icon: React.ReactNode;
  trendColor?: 'green' | 'red';
  iconColor?: 'emerald' | 'indigo' | 'violet' | 'amber' | 'cyan' | 'rose' | 'orange' | 'pink';  // 🆕 图标颜色
  theme?: 'dark' | 'light';
  loading?: boolean;
  compact?: boolean;  // 紧凑模式，用于6卡片一排
  isPercentChange?: boolean;  // 是否是百分点变化（利润率用）
}

const useCountUp = (endValue: string, duration: number = 1500) => {
  const [displayValue, setDisplayValue] = useState(endValue);
  
  useEffect(() => {
    // 如果是占位符或无效值，直接显示
    if (endValue === '-' || endValue === '0' || !endValue) {
      setDisplayValue(endValue);
      return;
    }
    
    const numericPart = parseFloat(endValue.replace(/[^0-9.-]/g, ''));
    if (isNaN(numericPart)) {
      setDisplayValue(endValue);
      return;
    }
    
    const prefix = endValue.includes('¥') ? '¥' : '';
    const suffix = endValue.includes('k') ? 'k' : '';
    const isFloat = endValue.includes('.');
    const isNegative = numericPart < 0;
    
    let startTime: number | null = null;
    let animationFrameId: number;
    let isCancelled = false;

    const animate = (timestamp: number) => {
      if (isCancelled) return;
      
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 5);
      
      const currentVal = Math.abs(numericPart) * easeProgress;
      const formattedVal = isFloat 
        ? currentVal.toFixed(1) 
        : Math.round(currentVal).toLocaleString();
      
      setDisplayValue(`${prefix}${isNegative ? '-' : ''}${formattedVal}${suffix}`);
      
      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        // 动画结束时确保显示最终值
        setDisplayValue(endValue);
      }
    };

    // 立即设置初始值为0，然后开始动画
    const initialVal = `${prefix}${isNegative ? '-' : ''}0${suffix}`;
    setDisplayValue(initialVal);
    
    // 使用 setTimeout 确保初始值渲染后再开始动画
    const timeoutId = setTimeout(() => {
      animationFrameId = requestAnimationFrame(animate);
    }, 16);
    
    return () => {
      isCancelled = true;
      clearTimeout(timeoutId);
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [endValue, duration]);

  return displayValue;
};

// 🆕 图标颜色映射
const iconColorMap: Record<string, string> = {
  emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  violet: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  orange: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  pink: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
};

// 🆕 悬浮光晕颜色映射
const glowColorMap: Record<string, string> = {
  emerald: 'bg-emerald-600',
  indigo: 'bg-indigo-600',
  violet: 'bg-violet-600',
  amber: 'bg-amber-600',
  cyan: 'bg-cyan-600',
  rose: 'bg-rose-600',
  orange: 'bg-orange-600',
  pink: 'bg-pink-600',
};

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  change, 
  subtext, 
  icon, 
  trendColor = 'green',
  iconColor,  // 🆕 新增
  theme = 'dark', 
  loading = false,
  compact = false,
  isPercentChange = false
}) => {
  const hasChange = change !== undefined;
  const isPositive = hasChange ? change >= 0 : true;
  // 🔧 修复：loading 时显示占位符，数据加载完成后触发动画
  const displayValue = loading ? '-' : value;
  const animatedValue = useCountUp(displayValue);
  const isDark = theme === 'dark';

  // 🆕 优先使用 iconColor，否则根据 trendColor 回退
  const resolvedIconColor = iconColor || (trendColor === 'red' ? 'rose' : 'emerald');
  const iconBg = iconColorMap[resolvedIconColor] || iconColorMap.emerald;
  const glowBg = glowColorMap[resolvedIconColor] || glowColorMap.emerald;
  
  const textColor = isDark ? 'text-white' : 'text-slate-900';
  const subTextColor = isDark ? 'text-slate-400' : 'text-slate-500';

  // 紧凑模式的样式
  const containerPadding = compact ? 'p-4' : 'p-6';
  const titleSize = compact ? 'text-[10px]' : 'text-[11px]';
  const valueSize = compact ? 'text-xl' : 'text-3xl';
  const iconPadding = compact ? 'p-2' : 'p-3';

  // 格式化变化值
  const formatChange = () => {
    if (!hasChange) return '';
    if (isPercentChange) {
      // 利润率用百分点
      return `${change >= 0 ? '+' : ''}${change.toFixed(1)}pp`;
    }
    return `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`;
  };

  return (
    <div className="relative group rounded-2xl transition-all duration-500 hover:shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)]">
      
      <div className={`glass-panel rounded-2xl ${containerPadding} h-full relative overflow-hidden transition-colors ${isDark ? 'group-hover:border-white/10' : 'group-hover:border-black/5'}`}>
          
          <div className={`absolute top-0 bottom-0 left-0 w-1/2 bg-gradient-to-r from-transparent ${isDark ? 'via-white/5' : 'via-black/5'} to-transparent skew-x-[-15deg] animate-shimmer pointer-events-none`}></div>

          {/* 🆕 使用动态光晕颜色 */}
          <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-[60px] opacity-0 transition-all duration-700 group-hover:opacity-15 group-hover:scale-110 ${glowBg}`}></div>

          <div className="flex justify-between items-start mb-3 relative z-10">
            <div className="flex-1 min-w-0">
              <p className={`${titleSize} font-bold uppercase tracking-widest mb-1 font-mono ${subTextColor} truncate`}>{title}</p>
              {loading ? (
                <div className="flex items-center gap-2">
                  <Loader2 size={compact ? 16 : 24} className={`animate-spin ${subTextColor}`} />
                </div>
              ) : (
                <h3 className={`${valueSize} font-bold font-mono tracking-tight drop-shadow-lg tabular-nums ${textColor} truncate`}>
                  {animatedValue}
                </h3>
              )}
            </div>
            <div className={`${iconPadding} rounded-xl border backdrop-blur-md transition-transform duration-300 group-hover:rotate-6 ${iconBg} flex-shrink-0`}>
              {icon}
            </div>
          </div>
          
          <div className="flex items-center justify-between relative z-10 mt-2">
            {hasChange ? (
              <div className={`flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md border backdrop-blur-sm ${
                isPositive 
                  ? 'bg-emerald-500/5 text-emerald-400 border-emerald-500/20' 
                  : 'bg-rose-500/5 text-rose-400 border-rose-500/20'
              }`}>
                {isPositive ? <ArrowUpRight size={12} className="mr-0.5" /> : <ArrowDownRight size={12} className="mr-0.5" />}
                <span className="font-mono">{formatChange()}</span>
              </div>
            ) : (
              <div className={`flex items-center text-[10px] font-medium px-2 py-0.5 rounded-md border backdrop-blur-sm ${
                isDark 
                  ? 'bg-slate-500/5 text-slate-400 border-slate-500/20' 
                  : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}>
                <span className="font-mono">无数据</span>
              </div>
            )}
            <div className={`flex items-center gap-1 text-[10px] font-medium tracking-wide ${subTextColor}`}>
              <Activity size={10} className="opacity-50" />
              {subtext}
            </div>
          </div>
      </div>
    </div>
  );
};

export default StatCard;
