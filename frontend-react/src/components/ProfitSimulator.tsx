import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCcw, TrendingUp, TrendingDown, Sparkles } from 'lucide-react';
import { DashboardData } from '@/types';

interface Props {
  data: DashboardData;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

const CyberSlider = ({ label, value, onChange, min, max, leftLabel, rightLabel }: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  leftLabel: string;
  rightLabel: string;
}) => {
  const percentage = ((value - min) / (max - min)) * 100;
  return (
    <div className="group">
      <div className="flex justify-between text-xs font-medium mb-3 items-end">
        <span className="text-slate-300 font-mono tracking-wide">{label}</span>
        <span className={`text-base font-bold font-mono transition-colors duration-300 ${value > 0 ? 'text-rose-400' : value < 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
          {value > 0 ? '+' : ''}{value}%
        </span>
      </div>
      <div className="relative h-4 w-full flex items-center">
        <div className="absolute w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-slate-600"></div>
        </div>
        <input 
          type="range" min={min} max={max} step="5" value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="absolute w-full h-full opacity-0 cursor-pointer z-20"
        />
        <div className="absolute top-1/2 -translate-y-1/2 h-1.5 pointer-events-none transition-all duration-500 ease-out z-10 rounded-full opacity-80"
          style={{
            left: value >= 0 ? '50%' : `${percentage}%`,
            width: Math.abs(value) === 0 ? '0%' : `${Math.abs(percentage - 50)}%`,
            backgroundColor: value > 0 ? '#f43f5e' : '#34d399'
          }}
        ></div>
        <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border-2 border-slate-900 shadow-lg transition-all duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] z-10 pointer-events-none group-hover:scale-125"
          style={{ left: `calc(${percentage}% - 8px)` }}
        ></div>
      </div>
      <div className="flex justify-between text-[10px] text-slate-500 mt-2 font-mono uppercase">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </div>
  );
};

const ProfitSimulator: React.FC<Props> = ({ data }) => {
  const [marketingAdjustment, setMarketingAdjustment] = useState(0); 
  const [deliveryAdjustment, setDeliveryAdjustment] = useState(0);   
  const [aiLoading, setAiLoading] = useState(false);
  
  const debouncedMarketing = useDebounce(marketingAdjustment, 200);
  const debouncedDelivery = useDebounce(deliveryAdjustment, 200);

  const [projectedProfit, setProjectedProfit] = useState(data.totalProfit);
  const [profitDelta, setProfitDelta] = useState(0);

  const baseMarketing = data.channels.reduce((acc, c) => acc + c.costs.marketing, 0);
  const baseDelivery = data.channels.reduce((acc, c) => acc + c.costs.delivery, 0);
  const baseProfit = data.totalProfit;

  useEffect(() => {
    const marketingMultiplier = 1 + (debouncedMarketing / 100);
    const deliveryMultiplier = 1 + (debouncedDelivery / 100);
    const newMarketingCost = baseMarketing * marketingMultiplier;
    const newDeliveryCost = baseDelivery * deliveryMultiplier;
    const marketingRevenueImpact = debouncedMarketing * 0.5;
    const newRevenue = data.totalRevenue * (1 + marketingRevenueImpact / 100);
    const baseOtherCosts = data.totalRevenue - baseProfit - baseMarketing - baseDelivery;
    const newOtherCosts = baseOtherCosts * (1 + marketingRevenueImpact / 100);
    const newProfit = newRevenue - newOtherCosts - newMarketingCost - newDeliveryCost;
    setProjectedProfit(newProfit);
    setProfitDelta(newProfit - baseProfit);
  }, [debouncedMarketing, debouncedDelivery, data, baseMarketing, baseDelivery, baseProfit]);

  const reset = () => {
    setMarketingAdjustment(0);
    setDeliveryAdjustment(0);
  };

  const handleAISolve = async () => {
    setAiLoading(true);
    await new Promise(r => setTimeout(r, 1200));
    setMarketingAdjustment(-10);
    setDeliveryAdjustment(-5);
    setAiLoading(false);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between h-full group">
      <div className="absolute inset-0 bg-[size:20px_20px] pointer-events-none opacity-5" style={{backgroundImage: 'linear-gradient(currentColor 1px, transparent 1px)'}}></div>
      
      <div className="mb-6 relative z-10 flex justify-between items-start">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-neon-green rounded-full animate-pulse"></span>
            经营沙盘推演
          </h3>
          <p className="text-xs text-slate-400 mt-1 font-mono uppercase tracking-wider opacity-70">AI SOLVER ENABLED</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleAISolve}
            disabled={aiLoading}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold transition-all ${
              aiLoading ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/50' : 'bg-indigo-600 hover:bg-indigo-500 text-white border-transparent shadow-[0_0_15px_rgba(99,102,241,0.4)]'
            }`}
          >
            <Sparkles size={14} className={aiLoading ? 'animate-spin' : ''} />
            {aiLoading ? 'COMPUTING...' : 'AI 求解'}
          </button>
          <button onClick={reset} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all border border-white/5">
            <RefreshCcw size={14} />
          </button>
        </div>
      </div>

      <div className="space-y-8 relative z-10 flex-1 flex flex-col justify-center">
        <CyberSlider label="营销预算投入" value={marketingAdjustment} onChange={setMarketingAdjustment} min={-30} max={30} leftLabel="节流保利" rightLabel="激进扩张" />
        <CyberSlider label="履约成本浮动" value={deliveryAdjustment} onChange={setDeliveryAdjustment} min={-20} max={20} leftLabel="运力提效" rightLabel="运力紧张" />
      </div>

      <div className="mt-auto pt-6 border-t border-white/10 relative z-10">
        <div className={`p-5 rounded-xl border backdrop-blur-xl transition-all duration-500 relative overflow-hidden ${profitDelta >= 0 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
          <div className="flex justify-between items-end mb-2 relative z-10">
            <span className="text-xs text-slate-300 font-bold uppercase font-mono tracking-wider">预计净利润</span>
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-bold border ${profitDelta >= 0 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/20' : 'bg-rose-500/20 text-rose-300 border-rose-500/20'}`}>
              {profitDelta >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              <span className="font-mono">{profitDelta >= 0 ? '+' : ''}¥{Math.abs(profitDelta).toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono flex items-baseline gap-1 relative z-10 tabular-nums">
            <span className="text-lg opacity-40 font-sans">¥</span>{projectedProfit.toLocaleString(undefined, {maximumFractionDigits: 0})}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfitSimulator;
