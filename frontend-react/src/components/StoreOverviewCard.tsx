import React from 'react';
import { Trophy, ArrowRight } from 'lucide-react';

// ==================== 数据类型 ====================

export interface StoreData {
    store_name: string;
    total_sales: number;
    order_count: number;
    total_profit: number;
    profit_rate: number;
    avg_order_value: number;
    marketing_cost_rate: number;
    avg_delivery_fee: number;
    avg_profit: number;
    // 每个指标的环比
    trend_sales?: number;
    trend_orders?: number;
    trend_profit?: number;
    trend_profit_rate?: number;
    trend_avg_value?: number;
    trend_marketing_rate?: number;
    trend_delivery_fee?: number;
    trend_avg_profit?: number;
}

// ==================== 环比标签组件 ====================

const TrendBadge: React.FC<{
    value: number | undefined;
    isPointDiff?: boolean;  // true = 百分点差值（率类指标），false = 百分比变化率
    inverse?: boolean;      // true = 数值上升为负面（如营销率、配送费）
}> = ({ value, isPointDiff = false, inverse = false }) => {
    if (value === undefined || value === null) return null;

    const isZero = Math.abs(value) < 0.05;
    const isUp = value > 0;

    // 判断颜色：默认上升=绿、下降=红；inverse 反转
    let colorClass: string;
    if (isZero) {
        colorClass = 'text-gray-500';
    } else if (inverse ? !isUp : isUp) {
        colorClass = 'text-emerald-400';
    } else {
        colorClass = 'text-rose-400';
    }

    const icon = isZero ? '—' : isUp ? '↗' : '↘';
    const label = isZero
        ? '持平'
        : isPointDiff
            ? `${value > 0 ? '+' : ''}${value.toFixed(1)}pt`
            : `${Math.abs(value).toFixed(1)}%`;

    return (
        <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium leading-none ${colorClass}`}>
            <span>{icon}</span>
            <span>{label}</span>
        </span>
    );
};

// ==================== 指标配置 ====================

type MetricKey = 'total_sales' | 'order_count' | 'total_profit' | 'profit_rate' | 'avg_order_value' | 'marketing_cost_rate' | 'avg_delivery_fee' | 'avg_profit';

type TrendKey = 'trend_sales' | 'trend_orders' | 'trend_profit' | 'trend_profit_rate' | 'trend_avg_value' | 'trend_marketing_rate' | 'trend_delivery_fee' | 'trend_avg_profit';

interface MetricConfig {
    key: MetricKey;
    trendKey: TrendKey;
    label: string;
    format: (v: number) => string;
    alert?: (v: number) => 'danger' | 'warning' | null;
    isPointDiff?: boolean;  // 率类指标用 pt 差值
    inverse?: boolean;      // 升为负面
}

// 主要指标（大字号 + 醒目）
const PRIMARY_METRICS: MetricConfig[] = [
    { key: 'total_sales', trendKey: 'trend_sales', label: '销售额', format: (v) => v >= 10000 ? `¥${(v / 10000).toFixed(1)}w` : `¥${v.toLocaleString()}` },
    { key: 'order_count', trendKey: 'trend_orders', label: '订单量', format: (v) => v.toLocaleString() },
    { key: 'total_profit', trendKey: 'trend_profit', label: '利润', format: (v) => v >= 10000 ? `¥${(v / 10000).toFixed(1)}w` : `¥${Math.round(v).toLocaleString()}` },
    {
        key: 'profit_rate', trendKey: 'trend_profit_rate', label: '利润率',
        format: (v) => `${v.toFixed(1)}%`, isPointDiff: true,
        alert: (v) => v < 10 ? 'danger' : null
    },
];

// 辅助指标（小字号 + 弱化）
const SECONDARY_METRICS: MetricConfig[] = [
    { key: 'avg_order_value', trendKey: 'trend_avg_value', label: '客单价', format: (v) => `¥${v.toFixed(1)}` },
    {
        key: 'marketing_cost_rate', trendKey: 'trend_marketing_rate', label: '营销率',
        format: (v) => `${v.toFixed(1)}%`, isPointDiff: true, inverse: true,
        alert: (v) => v > 12 ? 'warning' : null
    },
    {
        key: 'avg_delivery_fee', trendKey: 'trend_delivery_fee', label: '配送费',
        format: (v) => `¥${v.toFixed(2)}`, inverse: true,
        alert: (v) => v > 6 ? 'warning' : null
    },
    {
        key: 'avg_profit', trendKey: 'trend_avg_profit', label: '单均利润',
        format: (v) => `¥${v.toFixed(2)}`,
        alert: (v) => v < 0 ? 'danger' : null
    },
];

// ==================== Props ====================

interface StoreOverviewCardProps {
    store: StoreData;
    rank: number;
    isActive?: boolean;
    onClick?: () => void;
}

// ==================== 组件 ====================

const StoreOverviewCard: React.FC<StoreOverviewCardProps> = ({ store, rank, isActive = false, onClick }) => {

    // 排名奖杯
    const getRankBadge = (r: number) => {
        if (r === 1) return <Trophy className="w-5 h-5 text-yellow-400 drop-shadow-lg" fill="currentColor" />;
        if (r === 2) return <Trophy className="w-5 h-5 text-gray-300 drop-shadow-lg" fill="currentColor" />;
        if (r === 3) return <Trophy className="w-5 h-5 text-orange-400 drop-shadow-lg" fill="currentColor" />;
        return <span className="flex items-center justify-center w-6 h-6 text-xs font-bold text-gray-400 border border-gray-600/60 bg-gray-800/80 rounded-full">{r}</span>;
    };

    // 警告颜色 + 背景
    const getAlertStyle = (alertLevel: 'danger' | 'warning' | null, isPrimary?: boolean) => {
        if (alertLevel === 'danger') return {
            text: 'text-rose-400',
            bg: isPrimary ? 'bg-rose-500/10 rounded-lg' : 'bg-rose-500/10',
        };
        if (alertLevel === 'warning') return {
            text: 'text-amber-400',
            bg: isPrimary ? 'bg-amber-500/8 rounded-lg' : 'bg-amber-500/8',
        };
        return { text: isPrimary ? 'text-gray-100' : 'text-gray-300', bg: '' };
    };

    // 渲染指标格子
    const renderMetric = (metric: MetricConfig, isPrimary: boolean) => {
        const value = store[metric.key as keyof StoreData] as number;
        const trendValue = store[metric.trendKey as keyof StoreData] as number | undefined;
        const alertLevel = metric.alert ? metric.alert(value) : null;
        const style = getAlertStyle(alertLevel, isPrimary);

        return (
            <div
                key={metric.key}
                className={`flex flex-col items-center text-center py-1.5 px-1 rounded-md transition-all duration-200 ${alertLevel ? style.bg : ''}`}
            >
                <span className={`tracking-wider mb-0.5 ${isPrimary ? 'text-[10px] text-gray-500' : 'text-[9px] text-gray-600'}`}>
                    {metric.label}
                </span>
                <span className={`font-semibold font-mono leading-tight ${style.text} ${isPrimary ? 'text-[15px] font-bold' : 'text-xs'}`}>
                    {metric.format(value)}
                </span>
                {/* 环比标签 */}
                <div className="mt-0.5">
                    <TrendBadge value={trendValue} isPointDiff={metric.isPointDiff} inverse={metric.inverse} />
                </div>
                {/* 异常指示点 */}
                {alertLevel && (
                    <div className={`w-1 h-1 rounded-full mt-0.5 ${alertLevel === 'danger' ? 'bg-rose-400 shadow-[0_0_4px_#f87171]' : 'bg-amber-400 shadow-[0_0_4px_#fbbf24]'}`} />
                )}
            </div>
        );
    };

    return (
        <div
            className={`
                group relative flex flex-col overflow-hidden transition-all duration-300 border shadow-lg
                backdrop-blur-xl rounded-2xl cursor-pointer h-full
                active:scale-[0.98] active:shadow-inner
                ${isActive
                    ? 'bg-violet-950/40 border-violet-500/60 shadow-violet-500/20 ring-1 ring-violet-500/30'
                    : 'bg-gray-900/40 border-white/5 hover:-translate-y-1 hover:shadow-purple-500/10 hover:border-purple-500/30'
                }
            `}
            onClick={onClick}
        >
            {/* 选中指示条 */}
            {isActive && (
                <div className="absolute left-0 top-3 bottom-3 w-1 bg-gradient-to-b from-violet-400 to-violet-600 rounded-r-full shadow-[0_0_8px_#a78bfa]" />
            )}

            {/* 悬浮光效 */}
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            {/* ===== Header: 排名 + 门店名 + 箭头 ===== */}
            <div className="relative flex items-center justify-between px-4 py-2.5 border-b border-white/5 bg-gray-800/20">
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <div className="flex-shrink-0 flex items-center justify-center w-7 h-7 bg-black/20 rounded-lg shadow-inner">
                        {getRankBadge(rank)}
                    </div>
                    <span className="text-sm font-bold text-gray-100 truncate tracking-wide">{store.store_name}</span>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                    {/* 跳转箭头 */}
                    <div className={`transition-all duration-300 ${isActive ? 'opacity-100 translate-x-0' : 'opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0'}`}>
                        <ArrowRight className="w-4 h-4 text-purple-400" />
                    </div>
                </div>
            </div>

            {/* ===== Body: 主要指标（大字号 + 环比） ===== */}
            <div className="relative flex-1 px-4 pt-3 pb-3">
                <div className="grid grid-cols-4 gap-x-2">
                    {PRIMARY_METRICS.map((m) => renderMetric(m, true))}
                </div>

                {/* 分隔线 */}
                <div className="my-2 border-t border-white/5" />

                {/* 辅助指标（小字号 + 环比） */}
                <div className="grid grid-cols-4 gap-x-2">
                    {SECONDARY_METRICS.map((m) => renderMetric(m, false))}
                </div>
            </div>
        </div>
    );
};

export default StoreOverviewCard;
