import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { Store, ChevronDown, ChevronUp } from 'lucide-react';
import { ordersApi, type AllStoresOverviewItem } from '@/api/orders';
import { useGlobalContext } from '@/store/GlobalContext';
import StoreOverviewCard from '../StoreOverviewCard';
import MultiChannelDropdown from '@/components/ui/MultiChannelDropdown';

// ==================== 组件 ====================

interface Props {
    theme: 'dark' | 'light';
}

// 默认显示数量：6 = LCM(1,2,3)，在所有列数下都恰好填满整行
const DEFAULT_VISIBLE = 6;

const AllStoresOverviewChart: React.FC<Props> = ({ theme }) => {
    const [data, setData] = useState<AllStoresOverviewItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [expanded, setExpanded] = useState(false);
    // 本地多选渠道状态（不影响全局 selectedChannel）
    // 空数组 = 全部渠道
    const [selectedChannels, setSelectedChannels] = useState<string[]>([]);

    const { selectedStore, setSelectedStore, dateRange, channelList } = useGlobalContext();

    const isDark = theme === 'dark';

    // 获取数据 — 响应日期范围 & 渠道变化
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const params: { start_date?: string; end_date?: string; channels?: string } = {};
                if (dateRange.type !== 'all' && dateRange.start && dateRange.end) {
                    params.start_date = dateRange.start;
                    params.end_date = dateRange.end;
                }
                if (selectedChannels.length > 0) {
                    params.channels = selectedChannels.join(',');
                }
                const res = await ordersApi.getAllStoresOverview(params);
                if (res.success && res.data?.stores) {
                    setData(res.data.stores);
                }
            } catch (error) {
                console.error('获取全门店总览数据失败:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [dateRange.type, dateRange.start, dateRange.end, selectedChannels]);

    // 按销售额排序（后端已排序，这里做二次保障）
    const sortedData = useMemo(() => {
        return [...data].sort((a, b) => b.total_sales - a.total_sales);
    }, [data]);

    const hasMore = sortedData.length > DEFAULT_VISIBLE;

    // 缩短门店名
    const shortenStoreName = useCallback((name: string) => {
        const prefixes = ['惠宜选超市（', '惠宜选超市-', '惠宜选-', '共橙超市-'];
        for (const prefix of prefixes) {
            if (name.startsWith(prefix)) {
                let short = name.slice(prefix.length);
                if (short.endsWith('）')) short = short.slice(0, -1);
                return short;
            }
        }
        const match = name.match(/[（(](.+?)[）)]/);
        if (match && name.length > 8) return match[1];
        return name;
    }, []);

    // Toggle 点击逻辑
    const handleCardClick = useCallback((storeName: string) => {
        if (selectedStore === storeName) {
            setSelectedStore('');
        } else {
            setSelectedStore(storeName);
        }
    }, [selectedStore, setSelectedStore]);

    return (
        <div className="glass-panel rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
            {/* 背景装饰 */}
            <div className="absolute top-0 left-0 w-full h-20 bg-gradient-to-b from-violet-500/5 to-transparent pointer-events-none"></div>

            {/* 标题行 & 渠道选择器 */}
            <div className="mb-4 relative z-10">
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <h3 className={`text-lg font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                            <span className="w-1 h-5 bg-gradient-to-b from-violet-400 to-violet-600 rounded-full shadow-[0_0_10px_#a78bfa]"></span>
                            全门店经营总览
                            {data.length > 0 && (
                                <span className="text-xs bg-violet-500/20 text-violet-300 px-2 py-0.5 rounded-md font-mono">
                                    {data.length} 门店
                                </span>
                            )}
                        </h3>
                    </div>

                    {/* 渠道多选下拉选择器 */}
                    <MultiChannelDropdown
                        selectedChannels={selectedChannels}
                        channelList={channelList}
                        onSelect={setSelectedChannels}
                        isDark={isDark}
                        accentColor="indigo"
                    />
                </div>
            </div>

            {/* 副标题 */}
            <p className={`text-xs mb-4 font-mono tracking-wide opacity-60 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                点击卡片切换门店 · 再次点击恢复全量 · 响应日期与渠道筛选
            </p>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-16">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
                </div>
            )}

            {/* 空状态 */}
            {!loading && data.length === 0 && (
                <div className="flex items-center justify-center py-16">
                    <div className="text-center opacity-50">
                        <Store size={36} className={`mx-auto mb-3 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
                        <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>暂无门店数据</p>
                    </div>
                </div>
            )}

            {/* 卡片网格 */}
            {!loading && data.length > 0 && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                        {sortedData.map((store, index) => {
                            const rank = index + 1;
                            const isExtraCard = index >= DEFAULT_VISIBLE;
                            const displayStore = {
                                ...store,
                                store_name: shortenStoreName(store.store_name)
                            };

                            return (
                                <div
                                    key={store.store_name}
                                    className="transition-all duration-500 ease-out"
                                    style={{
                                        // 超出默认数量的卡片：展开时淡入滑入，收起时隐藏
                                        ...(isExtraCard ? {
                                            maxHeight: expanded ? '500px' : '0px',
                                            opacity: expanded ? 1 : 0,
                                            transform: expanded ? 'translateY(0)' : 'translateY(-12px)',
                                            overflow: 'hidden',
                                            marginTop: expanded ? undefined : '-8px',
                                            // 展开时每张卡片有递进延迟
                                            transitionDelay: expanded
                                                ? `${(index - DEFAULT_VISIBLE) * 60}ms`
                                                : '0ms',
                                        } : {})
                                    }}
                                >
                                    <StoreOverviewCard
                                        store={displayStore}
                                        rank={rank}
                                        isActive={selectedStore === store.store_name}
                                        onClick={() => handleCardClick(store.store_name)}
                                    />
                                </div>
                            );
                        })}
                    </div>

                    {/* 展开/收起按钮 */}
                    {hasMore && (
                        <div className="flex justify-center mt-4">
                            <button
                                onClick={() => setExpanded(!expanded)}
                                className={`group flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-medium transition-all duration-300 ${isDark
                                    ? 'bg-slate-800/60 border border-white/5 text-slate-400 hover:text-white hover:border-violet-500/40 hover:bg-slate-700/60 hover:shadow-lg hover:shadow-violet-500/5'
                                    : 'bg-white/60 border border-black/5 text-slate-500 hover:text-slate-900 hover:border-violet-300/50 hover:shadow-lg'
                                    }`}
                            >
                                {expanded ? (
                                    <>收起 <ChevronUp size={14} className="transition-transform duration-300 group-hover:-translate-y-0.5" /></>
                                ) : (
                                    <>查看全部 {sortedData.length} 门店 <ChevronDown size={14} className="transition-transform duration-300 group-hover:translate-y-0.5" /></>
                                )}
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default AllStoresOverviewChart;
