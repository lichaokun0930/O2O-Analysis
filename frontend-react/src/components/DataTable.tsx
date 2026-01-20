import React, { useState, useMemo } from 'react';
import { ChannelMetrics } from '@/types';
import { Download, AlertCircle, MoreHorizontal, ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  data: ChannelMetrics[];
}

const DataTable: React.FC<Props> = ({ data }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  const handleExport = () => {
    console.log("Exporting data...");
  };

  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return data.slice(start, start + pageSize);
  }, [data, currentPage]);

  const totalPages = Math.ceil(data.length / pageSize);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  }

  const MobileCard = ({ channel }: { channel: ChannelMetrics }) => {
    const highMarketing = channel.marketingRate > 0.20;
    return (
      <div className="glass-panel p-4 mb-3 rounded-xl">
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 bg-indigo-500 rounded-full"></div>
            <h4 className="font-bold text-white">{channel.name}</h4>
          </div>
          <span className="text-neon-green font-mono font-bold">¥{channel.profit.toLocaleString()}</span>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between text-slate-400 items-center">
            <span>营收贡献</span>
            <span className="text-slate-200 font-mono">¥{channel.revenue.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-slate-400 items-center">
            <span>营销占比</span>
            <div className="flex items-center gap-2">
              {highMarketing && <AlertCircle size={12} className="text-neon-rose" />}
              <span className={`${highMarketing ? 'text-neon-rose' : 'text-slate-200'} font-mono`}>
                {(channel.marketingRate * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={`h-full ${highMarketing ? 'bg-neon-rose' : 'bg-indigo-500'}`} 
              style={{width: `${Math.min(channel.marketingRate * 100 * 2, 100)}%`}}
            ></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-panel rounded-2xl overflow-hidden flex flex-col h-full">
      <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            渠道效益矩阵
            <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-white/5">LIVE</span>
          </h3>
        </div>
        <button 
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/5 rounded-lg text-xs font-medium transition-all"
        >
          <Download size={14} />
          <span className="hidden sm:inline">导出数据</span>
        </button>
      </div>
      
      {/* Mobile View */}
      <div className="md:hidden p-4">
        {paginatedData.map(c => <MobileCard key={c.id} channel={c} />)}
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto flex-1">
        <table className="min-w-full divide-y divide-white/5">
          <thead>
            <tr className="bg-slate-950/30">
              <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">渠道名称</th>
              <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">GMV 营收</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider font-mono pl-10">营销效率 (Marketing %)</th>
              <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">履约成本</th>
              <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">净利润</th>
              <th className="px-4 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 bg-slate-900/10">
            {paginatedData.map((channel) => {
              const highMarketing = channel.marketingRate > 0.20; 
              const marketingPercent = channel.marketingRate * 100;
              const barWidth = Math.min(marketingPercent * 3, 100); 

              return (
                <tr key={channel.id} className="hover:bg-white/[0.02] transition-colors group">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold bg-slate-800 border border-white/5 text-slate-300`}>
                        {channel.name.charAt(0)}
                      </div>
                      <span className="text-sm font-medium text-slate-200">{channel.name}</span>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="text-sm font-mono text-slate-300">¥{channel.revenue.toLocaleString()}</span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap pl-10">
                    <div className="flex flex-col gap-1.5 w-32">
                      <div className="flex justify-between items-center text-xs">
                        <span className={`font-mono ${highMarketing ? 'text-neon-rose font-bold' : 'text-slate-400'}`}>
                          {marketingPercent.toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          style={{width: `${barWidth}%`}} 
                          className={`h-full rounded-full transition-all duration-500 ${highMarketing ? 'bg-neon-rose shadow-[0_0_8px_rgba(244,63,94,0.5)]' : 'bg-indigo-500'}`}
                        ></div>
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex flex-col items-end">
                      <span className="text-sm font-mono text-slate-300">¥{channel.costs.delivery.toLocaleString()}</span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        单均 ¥{channel.avgDeliveryCost.toFixed(1)}
                      </span>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="text-sm font-bold font-mono text-neon-green">
                      ¥{channel.profit.toLocaleString()}
                    </span>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <button className="text-slate-600 hover:text-white transition-colors">
                      <MoreHorizontal size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="p-3 border-t border-white/5 bg-slate-900/20 flex items-center justify-end gap-3">
          <span className="text-xs text-slate-400 font-mono">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex gap-1">
            <button 
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-white/5 disabled:opacity-30 text-slate-300 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={16} />
            </button>
            <button 
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-white/5 disabled:opacity-30 text-slate-300 disabled:cursor-not-allowed"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;
