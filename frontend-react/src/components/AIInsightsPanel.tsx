import React, { useEffect, useState } from 'react';
import { AlertTriangle, Clock, Activity, Cpu, Target, Sparkles, ChevronRight, MousePointerClick } from 'lucide-react';
import { DashboardData, AIInsight, FocusArea } from '@/types';

interface Props {
  data: DashboardData;
  onLocate?: (area: FocusArea) => void;
  activeFocus: FocusArea;
}

const AIInsightsPanel: React.FC<Props> = ({ data, onLocate, activeFocus }) => {
  const [insight, setInsight] = useState<AIInsight | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // 模拟AI分析
    setLoading(true);
    const timer = setTimeout(() => {
      setInsight({
        summary: "检测到外卖渠道营销成本过高，拖累整体利润。建议优化满减策略。",
        costProblem: "饿了么渠道营销补贴占比达 20%，建议缩减满减力度。",
        timeOpportunity: "午高峰 (11:00-13:00) 订单密集但超时严重，建议增加运力调度。",
        actionSuggestion: "立即复盘距离在 3km+ 的订单毛利，考虑缩小配送范围。"
      });
      setLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, [data.lastUpdated]);

  if (loading) {
    return (
      <div className="w-full h-full glass-panel border-neon-purple/30 rounded-2xl flex flex-col items-center justify-center animate-pulse gap-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-4 border-neon-purple/30 border-t-neon-purple animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Cpu size={20} className="text-neon-purple animate-pulse" />
          </div>
        </div>
        <p className="text-neon-purple font-mono text-xs tracking-widest">AI NEURAL ENGINE PROCESSING...</p>
      </div>
    );
  }

  if (!insight) return null;

  return (
    <div className="w-full h-full glass-panel rounded-2xl p-[1px] relative overflow-hidden group flex flex-col shadow-[0_0_30px_rgba(124,58,237,0.1)]">
      <div className="absolute inset-0 bg-gradient-to-br from-neon-purple via-neon-cyan to-transparent opacity-30 group-hover:opacity-60 transition-opacity duration-1000 blur-lg"></div>
      
      <div className="bg-slate-950/90 backdrop-blur-xl rounded-xl p-6 relative z-10 flex flex-col h-full">
        
        <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg shadow-purple-500/20">
              <Sparkles size={18} className="text-white fill-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide leading-tight">AI 决策大脑</h3>
              <p className="text-[11px] text-slate-400 font-mono">CLICK TO LOCATE ISSUES</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-neon-green font-mono">ACTIVE</span>
            <div className="h-2 w-2 bg-neon-green rounded-full shadow-[0_0_10px_#4ade80] animate-pulse"></div>
          </div>
        </div>

        <div className="mb-6 relative">
          <div className="absolute -left-2 top-0 bottom-0 w-1 bg-gradient-to-b from-neon-purple to-transparent rounded-full opacity-50"></div>
          <p className="pl-4 text-lg font-medium text-white leading-relaxed italic">
            "{insight.summary}"
          </p>
        </div>

        <div className="flex-1 flex flex-col gap-3 overflow-y-auto pr-1 custom-scrollbar">
          <InsightItem 
            icon={<AlertTriangle size={14} className={activeFocus === 'cost' ? 'text-white' : 'text-neon-rose'} />}
            tag="成本检测"
            value={insight.costProblem}
            color="rose"
            onClick={() => onLocate && onLocate('cost')}
            isActive={activeFocus === 'cost'}
          />
          <InsightItem 
            icon={<Clock size={14} className={activeFocus === 'efficiency' ? 'text-white' : 'text-neon-yellow'} />}
            tag="效率诊断"
            value={insight.timeOpportunity}
            color="yellow"
            onClick={() => onLocate && onLocate('efficiency')}
            isActive={activeFocus === 'efficiency'}
          />
          <InsightItem 
            icon={<Activity size={14} className={activeFocus === 'profit' ? 'text-white' : 'text-neon-green'} />}
            tag="增长建议"
            value={insight.actionSuggestion}
            color="green"
            onClick={() => onLocate && onLocate('profit')}
            isActive={activeFocus === 'profit'}
          />
        </div>

        <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-xs text-slate-400 group/btn cursor-pointer hover:text-white transition-colors">
          <span className="font-mono">GENERATE_REPORT.PDF</span>
          <ChevronRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
        </div>
      </div>
    </div>
  );
};

interface InsightItemProps {
  icon: React.ReactNode;
  tag: string;
  value: string;
  color: string;
  onClick?: () => void;
  isActive: boolean;
}

const InsightItem = ({ icon, tag, value, color, onClick, isActive }: InsightItemProps) => {
  const colorMap: Record<string, string> = {
    rose: 'hover:bg-rose-500/10 hover:border-rose-500/40',
    yellow: 'hover:bg-yellow-500/10 hover:border-yellow-500/40',
    green: 'hover:bg-emerald-500/10 hover:border-emerald-500/40'
  };

  const tagColorMap: Record<string, string> = {
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    green: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
  }

  const activeClassMap: Record<string, string> = {
    rose: 'bg-rose-500 border-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.3)]',
    yellow: 'bg-yellow-500 border-yellow-400 shadow-[0_0_20px_rgba(250,204,21,0.3)]',
    green: 'bg-emerald-500 border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.3)]'
  };

  return (
    <button 
      onClick={onClick}
      className={`relative p-3.5 rounded-xl border text-left transition-all duration-300 group/item flex flex-col gap-2 outline-none
        ${isActive 
          ? `${activeClassMap[color]} scale-[1.02] z-10 border-transparent` 
          : `border-white/5 bg-white/[0.02] ${colorMap[color]} hover:scale-[1.01]`
        }
      `}
    >
      <div className="flex items-center justify-between w-full">
        <div className={`flex items-center gap-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${isActive ? 'bg-white/20 text-white border-transparent' : tagColorMap[color]}`}>
          {icon}
          {tag}
        </div>
        
        {isActive ? (
          <Target size={14} className="text-white animate-pulse" />
        ) : (
          <MousePointerClick size={14} className="text-slate-600 group-hover/item:text-white transition-colors opacity-0 group-hover/item:opacity-100" />
        )}
      </div>
      <p className={`text-xs leading-relaxed transition-colors ${isActive ? 'text-white/95 font-medium' : 'text-slate-400 group-hover/item:text-slate-200'}`}>
        {value}
      </p>
    </button>
  );
};

export default AIInsightsPanel;
