/**
 * Property-Based Tests for Marketing Cost Structure Sankey Chart
 * 
 * Feature: marketing-cost-structure
 * Property 6: 桑基图连线过滤零值
 * Validates: Requirements 2.6
 */
import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { transformToSankeyData } from './ProfitChart';
import type { ChannelMarketingData, MarketingCosts } from '@/types';

// Generator for marketing costs with some zero values
const marketingCostsArbitrary = fc.record({
  delivery_discount: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  full_reduction: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  product_discount: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  merchant_voucher: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  merchant_share: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  gift_amount: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  other_discount: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
  new_customer_discount: fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })),
}) as fc.Arbitrary<MarketingCosts>;

// Generator for channel marketing data
const channelMarketingDataArbitrary = fc.record({
  channel: fc.stringMatching(/^[a-zA-Z\u4e00-\u9fa5]{2,10}$/),
  order_count: fc.integer({ min: 1, max: 10000 }),
  revenue: fc.float({ min: 0, max: 1000000, noNaN: true }),
  marketing_costs: marketingCostsArbitrary,
  total_marketing_cost: fc.float({ min: 0, max: 100000, noNaN: true }),
}) as fc.Arbitrary<ChannelMarketingData>;

// Generator for array of channel marketing data
const channelsArbitrary = fc.array(channelMarketingDataArbitrary, { minLength: 1, maxLength: 5 });

describe('Marketing Cost Structure Sankey Chart - Property Tests', () => {
  /**
   * Property 6: 桑基图连线过滤零值
   * *For any* 生成的桑基图links数据，不 SHALL 包含value为0的连线
   * Validates: Requirements 2.6
   */
  it('Property 6: Sankey links should not contain zero-value connections', () => {
    fc.assert(
      fc.property(channelsArbitrary, (channels) => {
        const { links } = transformToSankeyData(channels, true, '#a5b4fc');
        
        // All links should have value > 0
        const hasZeroValueLink = links.some(link => link.value === 0);
        expect(hasZeroValueLink).toBe(false);
        
        // Additional check: all link values should be positive
        links.forEach(link => {
          expect(link.value).toBeGreaterThan(0);
        });
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Link count matches non-zero marketing costs
   * For any channel data, the number of links should equal the count of non-zero marketing cost fields
   */
  it('Property: Link count equals non-zero marketing cost field count', () => {
    fc.assert(
      fc.property(channelsArbitrary, (channels) => {
        const { links } = transformToSankeyData(channels, true, '#a5b4fc');
        
        // Count expected non-zero links
        let expectedLinkCount = 0;
        channels.forEach(ch => {
          const costs = ch.marketing_costs;
          if (costs.delivery_discount > 0) expectedLinkCount++;
          if (costs.full_reduction > 0) expectedLinkCount++;
          if (costs.product_discount > 0) expectedLinkCount++;
          if (costs.merchant_voucher > 0) expectedLinkCount++;
          if (costs.merchant_share > 0) expectedLinkCount++;
          if (costs.gift_amount > 0) expectedLinkCount++;
          if (costs.other_discount > 0) expectedLinkCount++;
          if (costs.new_customer_discount > 0) expectedLinkCount++;
        });
        
        expect(links.length).toBe(expectedLinkCount);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Node count is correct
   * For any channel data, nodes should only include channels and marketing types that have data
   * (not all 8 marketing types, only those with non-zero values)
   */
  it('Property: Node count equals active channels + active marketing types', () => {
    fc.assert(
      fc.property(channelsArbitrary, (channels) => {
        const { nodes, links } = transformToSankeyData(channels, true, '#a5b4fc');
        
        // Count active channels (channels that have at least one non-zero marketing cost)
        const activeChannels = new Set<string>();
        const activeMarketingTypes = new Set<string>();
        
        channels.forEach(ch => {
          const costs = ch.marketing_costs;
          let hasAnyMarketingCost = false;
          
          if (costs.delivery_discount > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('配送费减免'); }
          if (costs.full_reduction > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('满减金额'); }
          if (costs.product_discount > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('商品减免'); }
          if (costs.merchant_voucher > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('商家代金券'); }
          if (costs.merchant_share > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('商家承担券'); }
          if (costs.gift_amount > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('满赠金额'); }
          if (costs.other_discount > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('商家其他优惠'); }
          if (costs.new_customer_discount > 0) { hasAnyMarketingCost = true; activeMarketingTypes.add('新客减免'); }
          
          if (hasAnyMarketingCost) {
            activeChannels.add(ch.channel);
          }
        });
        
        // Expected: number of active channels + number of active marketing types
        const expectedNodeCount = activeChannels.size + activeMarketingTypes.size;
        expect(nodes.length).toBe(expectedNodeCount);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: All links have valid source and target
   * For any generated links, source should be a channel name and target should be a marketing type
   */
  it('Property: All links have valid source (channel) and target (marketing type)', () => {
    const marketingTypes = [
      '配送费减免', '满减金额', '商品减免', '商家代金券',
      '商家承担券', '满赠金额', '商家其他优惠', '新客减免'
    ];
    
    fc.assert(
      fc.property(channelsArbitrary, (channels) => {
        const { links } = transformToSankeyData(channels, true, '#a5b4fc');
        const channelNames = channels.map(ch => ch.channel);
        
        links.forEach(link => {
          // Source should be a channel name
          expect(channelNames).toContain(link.source);
          // Target should be a marketing type
          expect(marketingTypes).toContain(link.target);
        });
      }),
      { numRuns: 100 }
    );
  });
});
