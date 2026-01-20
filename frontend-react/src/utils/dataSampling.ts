/**
 * 数据采样工具
 * 
 * 用于优化大数据量图表渲染性能
 * 当数据点过多时，智能采样保留关键特征
 */

export interface DataPoint {
  [key: string]: any;
}

/**
 * 时间序列数据采样（保留趋势特征）
 * 
 * @param data 原始数据数组
 * @param maxPoints 最大保留点数（默认100）
 * @param xKey X轴字段名（默认'date'）
 * @returns 采样后的数据
 */
export function sampleTimeSeriesData<T extends DataPoint>(
  data: T[],
  maxPoints: number = 100,
  xKey: string = 'date'
): T[] {
  if (!data || data.length <= maxPoints) {
    return data;
  }

  const step = Math.ceil(data.length / maxPoints);
  const sampled: T[] = [];

  // 使用最大值-最小值采样（LTTB算法简化版）
  for (let i = 0; i < data.length; i += step) {
    const chunk = data.slice(i, Math.min(i + step, data.length));
    
    // 保留该区间的中间点
    const midIndex = Math.floor(chunk.length / 2);
    sampled.push(chunk[midIndex]);
  }

  // 确保保留首尾点
  if (sampled[0] !== data[0]) {
    sampled.unshift(data[0]);
  }
  if (sampled[sampled.length - 1] !== data[data.length - 1]) {
    sampled.push(data[data.length - 1]);
  }

  console.log(`📊 数据采样: ${data.length} -> ${sampled.length} 点 (${((1 - sampled.length / data.length) * 100).toFixed(1)}% 减少)`);
  
  return sampled;
}

/**
 * 散点图数据采样（随机采样）
 * 
 * @param data 原始数据数组
 * @param maxPoints 最大保留点数（默认1000）
 * @returns 采样后的数据
 */
export function sampleScatterData<T extends DataPoint>(
  data: T[],
  maxPoints: number = 1000
): T[] {
  if (!data || data.length <= maxPoints) {
    return data;
  }

  // 随机采样
  const sampled: T[] = [];
  const step = data.length / maxPoints;
  
  for (let i = 0; i < maxPoints; i++) {
    const index = Math.floor(i * step);
    sampled.push(data[index]);
  }

  console.log(`📊 散点图采样: ${data.length} -> ${sampled.length} 点`);
  
  return sampled;
}

/**
 * 柱状图数据采样（聚合采样）
 * 
 * @param data 原始数据数组
 * @param maxBars 最大柱数（默认50）
 * @param xKey X轴字段名
 * @param yKey Y轴字段名（需要聚合的值）
 * @param aggregation 聚合方式：'sum' | 'avg' | 'max' | 'min'
 * @returns 采样后的数据
 */
export function sampleBarData<T extends DataPoint>(
  data: T[],
  maxBars: number = 50,
  xKey: string,
  yKey: string,
  aggregation: 'sum' | 'avg' | 'max' | 'min' = 'sum'
): T[] {
  if (!data || data.length <= maxBars) {
    return data;
  }

  const chunkSize = Math.ceil(data.length / maxBars);
  const sampled: T[] = [];

  for (let i = 0; i < data.length; i += chunkSize) {
    const chunk = data.slice(i, Math.min(i + chunkSize, data.length));
    
    if (chunk.length === 0) continue;

    // 聚合计算
    let aggregatedValue: number;
    const values = chunk.map(item => Number(item[yKey]) || 0);
    
    switch (aggregation) {
      case 'sum':
        aggregatedValue = values.reduce((a, b) => a + b, 0);
        break;
      case 'avg':
        aggregatedValue = values.reduce((a, b) => a + b, 0) / values.length;
        break;
      case 'max':
        aggregatedValue = Math.max(...values);
        break;
      case 'min':
        aggregatedValue = Math.min(...values);
        break;
      default:
        aggregatedValue = values[0];
    }

    // 使用第一个元素作为基础，更新聚合值
    const aggregatedItem: any = { ...chunk[0] };
    aggregatedItem[yKey] = aggregatedValue;
    
    // 如果是日期范围，可以使用范围标签
    if (chunk.length > 1) {
      aggregatedItem[xKey] = `${chunk[0][xKey]}-${chunk[chunk.length - 1][xKey]}`;
    }
    
    sampled.push(aggregatedItem as T);
  }

  console.log(`📊 柱状图采样: ${data.length} -> ${sampled.length} 柱 (${aggregation})`);
  
  return sampled;
}

/**
 * 智能采样（根据数据类型自动选择采样策略）
 * 
 * @param data 原始数据
 * @param chartType 图表类型：'line' | 'scatter' | 'bar'
 * @param maxPoints 最大点数
 * @returns 采样后的数据
 */
export function smartSample<T extends DataPoint>(
  data: T[],
  chartType: 'line' | 'scatter' | 'bar' = 'line',
  maxPoints?: number
): T[] {
  switch (chartType) {
    case 'line':
      return sampleTimeSeriesData(data, maxPoints || 100);
    case 'scatter':
      return sampleScatterData(data, maxPoints || 1000);
    case 'bar':
      return data; // 柱状图需要指定字段，使用sampleBarData
    default:
      return data;
  }
}

/**
 * 检查是否需要采样
 * 
 * @param dataLength 数据长度
 * @param threshold 阈值
 * @returns 是否需要采样
 */
export function shouldSample(dataLength: number, threshold: number = 100): boolean {
  return dataLength > threshold;
}
