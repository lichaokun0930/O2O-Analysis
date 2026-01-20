import React, { useMemo } from 'react';
import * as echarts from 'echarts';
import { ChannelMarketingData } from '@/types';
import { useChart } from '@/hooks/useChart';

interface Props {
  data: ChannelMarketingData[];
  theme: 'dark' | 'light';
}

// 8个营销类型的颜色配置 - Requirements 2.4
const MARKETING_TYPE_COLORS: Record<string, string> = {
  '配送费减免': '#f43f5e',      // 玫红
  '满减金额': '#f59e0b',        // 橙色
  '商品减免': '#eab308',        // 黄色
  '商家代金券': '#22c55e',      // 绿色
  '商家承担券': '#14b8a6',      // 青色
  '满赠金额': '#3b82f6',        // 蓝色
  '商家其他优惠': '#8b5cf6',    // 紫色
  '新客减免': '#ec4899',        // 粉色
};

// 营销字段到显示名称的映射
const MARKETING_FIELD_MAPPING: Array<[keyof ChannelMarketingData['marketing_costs'], string]> = [
  ['delivery_discount', '配送费减免'],
  ['full_reduction', '满减金额'],
  ['product_discount', '商品减免'],
  ['merchant_voucher', '商家代金券'],
  ['merchant_share', '商家承担券'],
  ['gift_amount', '满赠金额'],
  ['other_discount', '商家其他优惠'],
  ['new_customer_discount', '新客减免'],
];

interface SankeyNode {
  name: string;
  itemStyle?: {
    color: string;
    borderColor?: string;
    borderWidth?: number;
    shadowBlur?: number;
    shadowColor?: string;
    opacity?: number;
  };
  label?: {
    position: 'left' | 'right';
  };
}

interface SankeyLink {
  source: string;
  target: string;
  value: number;
  lineStyle?: {
    color: echarts.graphic.LinearGradient;
    opacity: number;
    curveness: number;
  };
}

/**
 * 将渠道营销数据转换为桑基图数据格式
 * Requirements: 2.1, 2.2, 2.3, 2.6
 * Property 6: 桑基图连线过滤零值
 * 
 * 优化：只显示有数据的渠道和营销类型节点
 */
export function transformToSankeyData(
  channels: ChannelMarketingData[],
  isDark: boolean,
  borderColor: string
): { nodes: SankeyNode[]; links: SankeyLink[] } {
  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];
  const channelColor = '#6366f1';

  // 用于收集有数据的渠道和营销类型
  const activeChannels = new Set<string>();
  const activeMarketingTypes = new Set<string>();

  // 1. 先遍历数据，收集有数据的渠道和营销类型
  channels.forEach((ch) => {
    const costs = ch.marketing_costs;
    let hasAnyMarketingCost = false;

    MARKETING_FIELD_MAPPING.forEach(([field, displayName]) => {
      const value = costs[field];
      if (value > 0) {
        hasAnyMarketingCost = true;
        activeMarketingTypes.add(displayName);
      }
    });

    // 只有当渠道有营销成本时才添加
    if (hasAnyMarketingCost) {
      activeChannels.add(ch.channel);
    }
  });

  // 2. 添加有数据的渠道节点（左侧）- Requirements 2.1
  channels.forEach((ch) => {
    if (activeChannels.has(ch.channel)) {
      nodes.push({
        name: ch.channel,
        itemStyle: {
          color: channelColor,
          opacity: 1,
          borderColor: borderColor,
          shadowBlur: 10,
          shadowColor: channelColor,
        },
        label: { position: 'left' },
      });
    }
  });

  // 3. 只添加有数据的营销类型节点（右侧）- Requirements 2.2
  MARKETING_FIELD_MAPPING.forEach(([, displayName]) => {
    if (activeMarketingTypes.has(displayName)) {
      const color = MARKETING_TYPE_COLORS[displayName];
      nodes.push({
        name: displayName,
        itemStyle: {
          color: color,
          borderColor: isDark ? '#fff' : '#fff',
          borderWidth: 1,
          shadowBlur: 15,
          shadowColor: color,
        },
        label: { position: 'right' },
      });
    }
  });

  // 4. 添加连线（过滤零值）- Requirements 2.3, 2.6
  // Property 6: 桑基图连线过滤零值
  channels.forEach((ch) => {
    if (!activeChannels.has(ch.channel)) return;
    
    const costs = ch.marketing_costs;

    MARKETING_FIELD_MAPPING.forEach(([field, displayName]) => {
      const value = costs[field];
      // 只添加非零值的连线 - Requirements 2.6
      if (value > 0) {
        const targetColor = MARKETING_TYPE_COLORS[displayName];
        links.push({
          source: ch.channel,
          target: displayName,
          value: value,
          lineStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: channelColor },
              { offset: 1, color: targetColor },
            ]),
            opacity: 0.4,
            curveness: 0.5,
          },
        });
      }
    });
  });

  return { nodes, links };
}

/**
 * 营销成本结构桑基图组件
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.1, 5.3, 5.4
 */
const MarketingCostStructureChart: React.FC<Props> = ({ data, theme }) => {
  const isDark = theme === 'dark';
  const textColor = isDark ? '#cbd5e1' : '#475569';
  const titleColor = isDark ? '#fff' : '#0f172a';
  const borderColor = isDark ? '#a5b4fc' : '#6366f1';

  const { nodes, links } = useMemo(() => {
    return transformToSankeyData(data, isDark, borderColor);
  }, [data, isDark, borderColor]);

  const option: echarts.EChartsOption = useMemo(() => {
    // 如果没有数据，返回空配置
    if (!nodes.length || !links.length) {
      return { series: [] };
    }

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        padding: 12,
        extraCssText: 'backdrop-filter: blur(10px);',
        textStyle: {
          color: isDark ? '#f8fafc' : '#0f172a',
          fontFamily: 'JetBrains Mono',
          fontSize: 12,
        },
        // Requirements 2.5: tooltip显示渠道名称、营销类型、金额
        formatter: (params: any) => {
          if (!params || !params.data) return '';
          if (params.dataType === 'node') {
            return `<b>${params.data.name}</b>`;
          }
          if (params.dataType === 'edge') {
            return `${params.data.source} → ${params.data.target}<br/>¥${params.data.value?.toLocaleString() || 0}`;
          }
          return '';
        },
      },
      series: [
        {
          type: 'sankey',
          left: 120,
          right: 100,
          top: 20,
          bottom: 20,
          nodeAlign: 'justify',
          draggable: false,
          data: nodes,
          links: links,
          emphasis: { focus: 'adjacency' },
          label: {
            color: textColor,
            fontSize: 11,
            fontFamily: 'Inter',
          },
          lineStyle: { color: 'source', curveness: 0.5 },
          itemStyle: { borderWidth: 0 },
        },
      ],
    };
  }, [nodes, links, isDark, textColor]);

  const chartRef = useChart(option, [nodes, links, theme], theme);

  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col relative group">
      <div className="mb-2 shrink-0 relative z-10 pointer-events-none">
        {/* Requirements 5.3: 更新组件标题为"营销成本结构" */}
        <h3 className="text-lg font-bold flex items-center gap-2" style={{ color: titleColor }}>
          <span className="w-1 h-5 bg-neon-blue rounded-full shadow-[0_0_10px_#60a5fa]"></span>
          营销成本结构
        </h3>
        {/* Requirements 5.4: 更新副标题 */}
        <p
          className="text-xs mt-1 font-mono uppercase tracking-wider opacity-70"
          style={{ color: textColor }}
        >
          MARKETING COST FLOW: CHANNEL → TYPE
        </p>
      </div>

      <div className="flex-1 w-full min-h-[300px] relative z-0">
        <div ref={chartRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default MarketingCostStructureChart;
