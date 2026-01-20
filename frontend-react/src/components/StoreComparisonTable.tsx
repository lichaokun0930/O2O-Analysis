/**
 * 门店对比数据表格
 * 
 * 功能：
 * - 展示所有门店的关键指标
 * - 支持排序
 * - 所有指标都显示环比数据
 * - 排名展示
 * - 异常门店标识
 * - 点击行查看详情
 * 
 * 优化点：
 * - 添加异常标识
 * - 添加综合评分列
 * - 点击行交互
 * - 响应式优化
 */
import React from 'react';
import { ArrowUp, ArrowDown, TrendingUp, TrendingDown, Minus, AlertTriangle, Award } from 'lucide-react';
import type { StoreComparisonData, StoreAnomaly } from '../types';

interface StoreComparisonTableProps {
  stores: (StoreComparisonData & { 
    weekOverWeek?: any;
  })[];
  theme?: 'dark' | 'light';
  loading?: boolean;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSort: (field: 'revenue' | 'profit' | 'profit_margin' | 'order_count', order: 'asc' | 'desc') => void;
  onStoreClick?: (storeName: string) => void;
}

const StoreComparisonTable: React.FC<StoreComparisonTableProps> = ({
  stores,
  theme = 'dark',
  loading = false,
  sortBy,
  sortOrder,
  onSort,
  onStoreClick
}) => {
  const handleSort = (field: 'revenue' | 'profit' | 'profit_margin' | 'order_count') => {
    if (sortBy === field) {
      onSort(field, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      onSort(field, 'desc');
    }
  };
  
  const renderSortIcon = (field: string) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />;
  };
  
  const renderChange = (value: number | undefined, isPercent: boolean = true) => {
    if (value === undefined || value === 0) {
      return <span className="text-slate-600 flex items-center gap-1 text-[10px]"><Minus size={10} /> -</span>;
    }
    
    const isPositive = value > 0;
    const color = isPositive ? 'text-emerald-400' : 'text-red-400';
    const Icon = isPositive ? TrendingUp : TrendingDown;
    
    return (
      <span className={`${color} flex items-center gap-1 text-[10px] font-medium`}>
        <Icon size={10} />
        {isPositive ? '+' : ''}{value.toFixed(1)}{isPercent ? '%' : ''}
      </span>
    );
  };
  
  const getAnomalySeverityColor = (anomalies?: StoreAnomaly[]) => {
    if (!anomalies || anomalies.length === 0) return '';
    const hasHigh = anomalies.some(a => a.severity === 'high');
    const hasMedium = anomalies.some(a => a.severity === 'medium');
    if (hasHigh) return 'border-l-2 border-l-red-500';
    if (hasMedium) return 'border-l-2 border-l-amber-500';
    return 'border-l-2 border-l-blue-500';
  };
  
  if (loading) {
    return (
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex items-center justify-center gap-2 text-slate-400">
          <div className="w-4 h-4 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin" />
          加载中...
        </div>
      </div>
    );
  }
  
  if (stores.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6">
        <div className="text-slate-400 text-center py-8">
          <Award size={32} className="mx-auto mb-2 opacity-50" />
          暂无数据
        </div>
      </div>
    );
  }
  
  return (
    <div className="glass-panel rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">门店详细数据</h3>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 bg-red-500 rounded-full" />
            高风险
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 bg-amber-500 rounded-full" />
            中风险
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
            正常
          </span>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-slate-400 font-medium">排名</th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">门店名称</th>
              <th 
                className="text-right py-3 px-4 text-slate-400 font-medium cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('order_count')}
              >
                <div className="flex items-center justify-end gap-1">
                  订单量 {renderSortIcon('order_count')}
                </div>
              </th>
              <th 
                className="text-right py-3 px-4 text-slate-400 font-medium cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('revenue')}
              >
                <div className="flex items-center justify-end gap-1">
                  销售额 {renderSortIcon('revenue')}
                </div>
              </th>
              <th 
                className="text-right py-3 px-4 text-slate-400 font-medium cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('profit')}
              >
                <div className="flex items-center justify-end gap-1">
                  利润 {renderSortIcon('profit')}
                </div>
              </th>
              <th 
                className="text-right py-3 px-4 text-slate-400 font-medium cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('profit_margin')}
              >
                <div className="flex items-center justify-end gap-1">
                  利润率 {renderSortIcon('profit_margin')}
                </div>
              </th>
              <th className="text-right py-3 px-4 text-slate-400 font-medium">客单价</th>
              <th className="text-right py-3 px-4 text-slate-400 font-medium">单均配送费</th>
              <th className="text-right py-3 px-4 text-slate-400 font-medium">单均营销费</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((store, index) => (
              <tr 
                key={store.store_name} 
                className={`border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer
                           ${getAnomalySeverityColor(store.anomalies)}`}
                onClick={() => onStoreClick?.(store.store_name)}
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    {index < 3 ? (
                      <span className={`
                        w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                        ${index === 0 ? 'bg-amber-500/20 text-amber-400' : ''}
                        ${index === 1 ? 'bg-slate-400/20 text-slate-300' : ''}
                        ${index === 2 ? 'bg-orange-600/20 text-orange-400' : ''}
                      `}>
                        {index + 1}
                      </span>
                    ) : (
                      <span className="text-slate-500 text-xs w-6 text-center">{index + 1}</span>
                    )}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{store.store_name}</span>
                    {store.anomalies && store.anomalies.length > 0 && (
                      <span title={store.anomalies.map(a => a.message).join('\n')}>
                        <AlertTriangle 
                          size={14} 
                          className={
                            store.anomalies.some(a => a.severity === 'high') ? 'text-red-400' :
                            store.anomalies.some(a => a.severity === 'medium') ? 'text-amber-400' :
                            'text-blue-400'
                          }
                        />
                      </span>
                    )}
                  </div>
                </td>
                
                {/* 订单量 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-slate-300">{store.order_count.toLocaleString()}</span>
                    {renderChange(store.weekOverWeek?.order_count)}
                  </div>
                </td>
                
                {/* 销售额 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-slate-300">¥{store.total_revenue.toLocaleString()}</span>
                    {renderChange(store.weekOverWeek?.revenue)}
                  </div>
                </td>
                
                {/* 利润 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-slate-300">¥{store.total_profit.toLocaleString()}</span>
                    {renderChange(store.weekOverWeek?.profit)}
                  </div>
                </td>
                
                {/* 利润率 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className={`
                      ${store.profit_margin >= 30 ? 'text-emerald-400' : ''}
                      ${store.profit_margin >= 20 && store.profit_margin < 30 ? 'text-cyan-400' : ''}
                      ${store.profit_margin >= 10 && store.profit_margin < 20 ? 'text-amber-400' : ''}
                      ${store.profit_margin < 10 ? 'text-red-400' : ''}
                    `}>
                      {store.profit_margin.toFixed(1)}%
                    </span>
                    {renderChange(store.weekOverWeek?.profit_margin, false)}
                  </div>
                </td>
                
                {/* 客单价 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-slate-300">¥{store.aov.toFixed(1)}</span>
                    {renderChange(store.weekOverWeek?.aov)}
                  </div>
                </td>
                
                {/* 单均配送费 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-slate-300">¥{store.avg_delivery_fee.toFixed(1)}</span>
                    {renderChange(store.weekOverWeek?.avg_delivery_fee)}
                  </div>
                </td>
                
                {/* 单均营销费 + 环比 */}
                <td className="py-3 px-4 text-right">
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-slate-300">¥{store.avg_marketing_cost.toFixed(1)}</span>
                    {renderChange(store.weekOverWeek?.avg_marketing_cost)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* 表格底部统计 */}
      <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
        <span>共 {stores.length} 个门店</span>
        <span>
          异常门店: {stores.filter(s => s.anomalies && s.anomalies.length > 0).length} 个
        </span>
      </div>
    </div>
  );
};

export default StoreComparisonTable;
