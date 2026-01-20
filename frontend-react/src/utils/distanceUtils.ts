/**
 * 距离区间工具函数
 * 
 * 用于计算距离值对应的距离区间索引
 * Property 4: Highlight Distance Mapping
 * Validates: Requirements 6.2
 */

import type { DistanceBandMetric } from '@/types';

/**
 * 默认的7个距离区间定义
 * 与后端 DISTANCE_BANDS 保持一致
 */
export const DISTANCE_BANDS = [
  { label: '0-1km', min: 0, max: 1 },
  { label: '1-2km', min: 1, max: 2 },
  { label: '2-3km', min: 2, max: 3 },
  { label: '3-4km', min: 3, max: 4 },
  { label: '4-5km', min: 4, max: 5 },
  { label: '5-6km', min: 5, max: 6 },
  { label: '6km+', min: 6, max: Infinity },
];

/**
 * 根据距离值计算对应的距离区间索引
 * 
 * Property 4: Highlight Distance Mapping
 * *For any* highlightDistance value in the range [0, ∞), exactly one distance band 
 * SHALL be highlighted, and that band SHALL be the one where 
 * min_distance ≤ highlightDistance < max_distance.
 * 
 * @param distance - 距离值 (km)
 * @param bands - 距离区间数组（可选，默认使用 DISTANCE_BANDS）
 * @returns 对应的区间索引，如果距离无效则返回 -1
 */
export function getDistanceBandIndex(
  distance: number | null | undefined,
  bands: Array<{ min_distance: number; max_distance: number }> = DISTANCE_BANDS.map(b => ({
    min_distance: b.min,
    max_distance: b.max
  }))
): number {
  // 处理无效输入
  if (distance === null || distance === undefined || isNaN(distance)) {
    return -1;
  }

  // 负数距离无效
  if (distance < 0) {
    return -1;
  }

  // 遍历区间，找到匹配的区间
  for (let i = 0; i < bands.length; i++) {
    const band = bands[i];
    if (distance >= band.min_distance && distance < band.max_distance) {
      return i;
    }
  }

  // 如果距离 >= 最后一个区间的 min_distance，返回最后一个区间
  // 这处理了 distance >= 6 的情况（6km+ 区间）
  const lastBand = bands[bands.length - 1];
  if (distance >= lastBand.min_distance) {
    return bands.length - 1;
  }

  return -1;
}

/**
 * 根据距离值获取对应的距离区间标签
 * 
 * @param distance - 距离值 (km)
 * @returns 对应的区间标签，如果距离无效则返回 null
 */
export function getDistanceBandLabel(distance: number | null | undefined): string | null {
  const index = getDistanceBandIndex(distance);
  if (index === -1) {
    return null;
  }
  return DISTANCE_BANDS[index].label;
}

/**
 * 验证距离区间映射的正确性
 * 用于属性测试
 * 
 * @param distance - 距离值 (km)
 * @param expectedIndex - 期望的区间索引
 * @returns 是否匹配
 */
export function validateDistanceBandMapping(distance: number, expectedIndex: number): boolean {
  const actualIndex = getDistanceBandIndex(distance);
  return actualIndex === expectedIndex;
}
