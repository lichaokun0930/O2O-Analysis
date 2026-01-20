import React, { useEffect, useState } from 'react';
import { X, PackageX, TrendingDown, RefreshCw } from 'lucide-react';
import { SkuRiskMetric } from '@/types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  itemName: string;
  riskType: 'OUT_OF_STOCK' | 'SLOW_MOVING' | null;
  data: SkuRiskMetric[];
  loading?: boolean;
}

const RiskDetailDrawer: React.FC<Props> = ({ isOpen, onClose, itemName, riskType, data, loading = false }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      // 不再锁定 body 滚动，抽屉有自己的滚动区域和 backdrop
    } else {
      const timer = setTimeout(() => setIsVisible(false), 200);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isVisible && !isOpen) return null;

  const isOOS = riskType === 'OUT_OF_STOCK';
  const totalImpact = data.reduce((acc, item) => acc + (item.impactValue || 0), 0);

  // 滞销等级配置
  const severityConfig = {
    light: { label: '轻度', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
    medium: { label: '中度', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
    heavy: { label: '重度', color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30' },
    critical: { label: '超重度', color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  };

  // 按滞销等级分组
  const groupedByLevel = !isOOS ? {
    light: data.filter(d => d.severity === 'light'),
    medium: data.filter(d => d.severity === 'medium'),
    heavy: data.filter(d => d.severity === 'heavy'),
    critical: data.filter(d => d.severity === 'critical'),
  } : null;

  return (
    <div className="fixed inset-0 z-[60] flex justify-end">
      {/* Backdrop */}
      <div 
        className={`absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-200 ${isOpen ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div 
        className={`relative w-full max-w-lg h-full bg-slate-900 border-l border-white/10 shadow-2xl transform transition-transform duration-200 ease-out flex flex-col ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {/* Header */}
        <div className={`px-5 py-4 border-b flex items-center justify-between ${isOOS ? 'border-rose-500/20 bg-rose-500/5' : 'border-orange-500/20 bg-orange-500/5'}`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isOOS ? 'bg-rose-500/20' : 'bg-orange-500/20'}`}>
              {isOOS ? <PackageX size={18} className="text-rose-400" /> : <TrendingDown size={18} className="text-orange-400" />}
            </div>
            <div>
              <h2 className="text-base font-bold text-white">{itemName}</h2>
              <p className={`text-xs ${isOOS ? 'text-rose-400' : 'text-orange-400'}`}>
                {isOOS ? '售罄品明细' : '滞销品明细'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Summary */}
        <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between bg-slate-800/30">
          <div className="flex items-center gap-6">
            <div>
              <p className="text-[10px] text-slate-500 uppercase">商品数</p>
              <p className="text-lg font-bold text-white font-mono">{data.length}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">{isOOS ? '潜在损失' : '积压资金'}</p>
              <p className={`text-lg font-bold font-mono ${isOOS ? 'text-rose-400' : 'text-orange-400'}`}>
                ¥{totalImpact.toLocaleString()}
              </p>
            </div>
          </div>
          {loading && (
            <RefreshCw size={16} className="text-indigo-400 animate-spin" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <RefreshCw size={24} className="text-indigo-400 animate-spin" />
            </div>
          ) : data.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-slate-500">
              <span className="text-sm">暂无数据</span>
            </div>
          ) : isOOS ? (
            /* 售罄品表格 */
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-800/95 z-10">
                <tr className="border-b border-white/5">
                  <th className="text-left py-3 px-4 text-[10px] text-slate-500 font-medium uppercase">商品名称</th>
                  <th className="text-right py-3 px-4 text-[10px] text-slate-500 font-medium uppercase w-24">影响金额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {data.map((item, idx) => (
                  <tr key={item.id || idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4">
                      <div className="text-slate-200 font-medium truncate max-w-[280px]" title={item.skuName}>
                        {item.skuName}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{item.reason}</div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-rose-400 font-mono font-medium">
                        ¥{(item.impactValue || 0).toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            /* 滞销品分级表格 */
            <div className="space-y-4 p-4">
              {(['critical', 'heavy', 'medium', 'light'] as const).map(level => {
                const items = groupedByLevel?.[level] || [];
                if (items.length === 0) return null;
                
                const config = severityConfig[level];
                const levelTotal = items.reduce((sum, item) => sum + (item.impactValue || 0), 0);
                
                return (
                  <div key={level} className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden`}>
                    {/* 等级标题 */}
                    <div className="px-4 py-2 flex items-center justify-between border-b border-white/5">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold ${config.color}`}>{config.label}滞销</span>
                        <span className="text-[10px] text-slate-500">
                          {level === 'light' && '(7天)'}
                          {level === 'medium' && '(8-15天)'}
                          {level === 'heavy' && '(16-30天)'}
                          {level === 'critical' && '(>30天)'}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-slate-400">{items.length}件</span>
                        <span className={`font-mono ${config.color}`}>¥{levelTotal.toLocaleString()}</span>
                      </div>
                    </div>
                    
                    {/* 商品列表 */}
                    <table className="w-full text-sm">
                      <tbody className="divide-y divide-white/5">
                        {items.map((item, idx) => (
                          <tr key={item.id || idx} className="hover:bg-white/[0.02] transition-colors">
                            <td className="py-2.5 px-4">
                              <div className="text-slate-200 text-xs truncate max-w-[240px]" title={item.skuName}>
                                {item.skuName}
                              </div>
                            </td>
                            <td className="py-2.5 px-4 text-right whitespace-nowrap">
                              <span className={`text-xs font-mono ${config.color}`}>
                                {item.duration}
                              </span>
                            </td>
                            <td className="py-2.5 px-4 text-right whitespace-nowrap">
                              <span className="text-xs text-slate-400 font-mono">
                                ¥{(item.impactValue || 0).toLocaleString()}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskDetailDrawer;
