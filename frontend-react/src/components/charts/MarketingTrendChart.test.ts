/**
 * Property-Based Tests for Marketing Cost Trend Chart
 * 
 * Feature: marketing-cost-trend
 * Properties: 4, 5, 6
 * Validates: Requirements 2.6, 3.2, 3.3
 */
import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { 
  filterZeroTypes, 
  calculatePercentages, 
  transformToStackedAreaData,
  MARKETING_FIELD_MAPPING,
  ViewMode
} from './MarketingTrendChart';
import type { MarketingTrendData, MarketingTrendSeries } from '@/types';

// Generator for marketing trend series with some zero values
const marketingTrendSeriesArbitrary = (length: number): fc.Arbitrary<MarketingTrendSeries> => 
  fc.record({
    delivery_discount: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    full_reduction: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    product_discount: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    merchant_voucher: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    merchant_share: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    gift_amount: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    other_discount: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
    new_customer_discount: fc.array(fc.oneof(fc.constant(0), fc.float({ min: 0, max: 10000, noNaN: true })), { minLength: length, maxLength: length }),
  }) as fc.Arbitrary<MarketingTrendSeries>;

/**
 * Calculate totals from series data (matching real API behavior)
 * In real data, totals[i] = sum of all marketing costs for day i
 */
function calculateTotalsFromSeries(series: MarketingTrendSeries, length: number): number[] {
  const totals: number[] = [];
  for (let i = 0; i < length; i++) {
    const dayTotal = 
      (series.delivery_discount?.[i] ?? 0) +
      (series.full_reduction?.[i] ?? 0) +
      (series.product_discount?.[i] ?? 0) +
      (series.merchant_voucher?.[i] ?? 0) +
      (series.merchant_share?.[i] ?? 0) +
      (series.gift_amount?.[i] ?? 0) +
      (series.other_discount?.[i] ?? 0) +
      (series.new_customer_discount?.[i] ?? 0);
    totals.push(dayTotal);
  }
  return totals;
}

// Generator for marketing trend data with consistent totals
// totals is calculated from series to match real API behavior
const marketingTrendDataArbitrary = fc.integer({ min: 3, max: 30 }).chain(length => 
  fc.tuple(
    fc.array(
      fc.date({ min: new Date('2024-01-01'), max: new Date('2024-12-31') })
        .map(d => d.toISOString().slice(0, 10)),
      { minLength: length, maxLength: length }
    ),
    marketingTrendSeriesArbitrary(length)
  ).map(([dates, series]) => ({
    dates,
    series,
    totals: calculateTotalsFromSeries(series, length)
  }))
) as fc.Arbitrary<MarketingTrendData>;

describe('Marketing Cost Trend Chart - Property Tests', () => {
  /**
   * Property 4: 零值类型过滤
   * *For any* 生成的图表series数据，不 SHALL 包含在整个时间范围内金额都为0的营销类型
   * Validates: Requirements 2.6
   */
  it('Property 4: Zero-value types should be filtered out', () => {
    fc.assert(
      fc.property(marketingTrendDataArbitrary, (data) => {
        const activeTypes = filterZeroTypes(data.series);
        
        // Each active type should have at least one non-zero value
        activeTypes.forEach(([field]) => {
          const values = data.series[field];
          if (values) {
            const hasNonZero = values.some(v => v > 0);
            expect(hasNonZero).toBe(true);
          }
        });
        
        // Types not in activeTypes should have all zero values
        const activeFields = activeTypes.map(([field]) => field);
        MARKETING_FIELD_MAPPING.forEach(([field]) => {
          if (!activeFields.includes(field)) {
            const values = data.series[field];
            if (values) {
              const allZero = values.every(v => v === 0);
              expect(allZero).toBe(true);
            }
          }
        });
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 5: 百分比计算正确性
   * *For any* 百分比视图下的每一天，各营销类型的占比之和 SHALL 等于100%（或当总金额为0时全为0）
   * Validates: Requirements 3.3
   */
  it('Property 5: Percentage values should sum to 100% (or 0 when total is 0)', () => {
    fc.assert(
      fc.property(marketingTrendDataArbitrary, (data) => {
        const { series, totals } = data;
        const length = totals.length;
        
        // Calculate percentages for each type
        const allPercentages: number[][] = MARKETING_FIELD_MAPPING.map(([field]) => {
          const fieldValues = series[field] ?? [];
          return calculatePercentages(fieldValues, totals);
        });
        
        // For each day, sum of percentages should be ~100% or 0
        for (let i = 0; i < length; i++) {
          const daySum = allPercentages.reduce((sum, typePercentages) => sum + typePercentages[i], 0);
          
          if (totals[i] === 0) {
            // When total is 0, all percentages should be 0
            expect(daySum).toBeCloseTo(0, 5);
          } else {
            // When total > 0, sum should be ~100%
            expect(daySum).toBeCloseTo(100, 1);
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 6: 绝对值视图数据一致性
   * *For any* 绝对值视图下的数据，各营销类型的值 SHALL 等于API返回的原始金额（不做百分比转换）
   * Validates: Requirements 3.2
   */
  it('Property 6: Absolute view should preserve original values', () => {
    fc.assert(
      fc.property(marketingTrendDataArbitrary, (data) => {
        const option = transformToStackedAreaData(data, 'absolute', true);
        const echartsSeries = option.series as any[];
        
        if (!echartsSeries || echartsSeries.length === 0) {
          // No active types, skip
          return;
        }
        
        // Get active types
        const activeTypes = filterZeroTypes(data.series);
        
        // Each series should have original values
        echartsSeries.forEach((s, index) => {
          const [field] = activeTypes[index];
          const originalValues = data.series[field] ?? [];
          const seriesData = s.data as number[];
          
          // Values should match original
          seriesData.forEach((val, i) => {
            expect(val).toBeCloseTo(originalValues[i] ?? 0, 5);
          });
        });
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Series count matches active types count
   */
  it('Property: Series count equals active marketing types count', () => {
    fc.assert(
      fc.property(marketingTrendDataArbitrary, (data) => {
        const option = transformToStackedAreaData(data, 'percentage', true);
        const echartsSeries = option.series as any[];
        const activeTypes = filterZeroTypes(data.series);
        
        expect(echartsSeries.length).toBe(activeTypes.length);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Percentage values are bounded [0, 100]
   */
  it('Property: Percentage values are bounded between 0 and 100', () => {
    fc.assert(
      fc.property(marketingTrendDataArbitrary, (data) => {
        const option = transformToStackedAreaData(data, 'percentage', true);
        const echartsSeries = option.series as any[];
        
        echartsSeries.forEach(s => {
          const seriesData = s.data as number[];
          seriesData.forEach(val => {
            expect(val).toBeGreaterThanOrEqual(0);
            expect(val).toBeLessThanOrEqual(100);
          });
        });
      }),
      { numRuns: 100 }
    );
  });
});
