import { useEffect, useRef, useCallback } from 'react';
import * as echarts from 'echarts';
import { sampleTimeSeriesData, sampleScatterData, shouldSample } from '../utils/dataSampling';

// ============================================
// 🎨 主题注册（只执行一次）
// ============================================
let themesRegistered = false;

const registerThemes = () => {
  if (themesRegistered) return;
  
  // Neon Cyber (Dark Mode)
  echarts.registerTheme('neon-cyber', {
    backgroundColor: 'transparent',
    textStyle: { fontFamily: 'JetBrains Mono, Inter, sans-serif' },
    title: { textStyle: { color: '#f8fafc' }, subtextStyle: { color: '#94a3b8' } },
    line: { itemStyle: { borderWidth: 2 }, lineStyle: { width: 3 }, symbolSize: 8, symbol: 'circle', smooth: true },
    categoryAxis: { 
      axisLine: { show: false }, 
      axisTick: { show: false }, 
      axisLabel: { color: '#94a3b8', fontSize: 11 }, 
      splitLine: { show: false } 
    },
    valueAxis: { 
      axisLine: { show: false }, 
      axisTick: { show: false }, 
      axisLabel: { color: '#64748b', fontSize: 10 }, 
      splitLine: { show: true, lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } } 
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      textStyle: { color: '#f8fafc' },
      padding: 12,
      extraCssText: 'backdrop-filter: blur(10px); border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);',
    },
  });

  // Clean Light (Workstation Mode)
  echarts.registerTheme('clean-light', {
    backgroundColor: 'transparent',
    textStyle: { fontFamily: 'JetBrains Mono, Inter, sans-serif' },
    title: { textStyle: { color: '#0f172a' }, subtextStyle: { color: '#64748b' } },
    line: { itemStyle: { borderWidth: 2 }, lineStyle: { width: 3 }, symbolSize: 8, symbol: 'circle', smooth: true },
    categoryAxis: { 
      axisLine: { show: false }, 
      axisTick: { show: false }, 
      axisLabel: { color: '#64748b', fontSize: 11 }, 
      splitLine: { show: false } 
    },
    valueAxis: { 
      axisLine: { show: false }, 
      axisTick: { show: false }, 
      axisLabel: { color: '#64748b', fontSize: 10 }, 
      splitLine: { show: true, lineStyle: { color: 'rgba(0,0,0,0.06)', type: 'dashed' } } 
    },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: 'rgba(0, 0, 0, 0.1)',
      textStyle: { color: '#0f172a' },
      padding: 12,
      extraCssText: 'backdrop-filter: blur(10px); border-radius: 8px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);',
    },
  });
  
  themesRegistered = true;
};

// ============================================
// 🔧 防抖函数 - 消除布局抖动
// ============================================
function debounce<T extends (...args: unknown[]) => void>(
  fn: T, 
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

// ============================================
// 🚀 核心 Hook - 内核级优化版（带数据采样）
// ============================================
export const useChart = (
  option: echarts.EChartsOption, 
  dependencies: unknown[], 
  theme: 'dark' | 'light' = 'dark',
  onClick?: (params: unknown) => void,
  enableSampling: boolean = true  // ✅ 新增：是否启用数据采样
) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const isDisposed = useRef(false);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const debouncedResizeRef = useRef<(() => void) | null>(null);

  // ============================================
  // 📊 数据采样处理 - 优化大数据量渲染
  // ============================================
  const processedOption = useCallback((rawOption: echarts.EChartsOption): echarts.EChartsOption => {
    if (!enableSampling) return rawOption;
    
    const option = { ...rawOption };
    const seriesArray = option.series as any[];
    
    if (!Array.isArray(seriesArray)) return option;
    
    // 处理每个系列的数据
    option.series = seriesArray.map((series: any) => {
      if (!Array.isArray(series.data) || series.data.length === 0) {
        return series;
      }
      
      const dataLength = series.data.length;
      
      // 根据图表类型选择采样策略
      if (series.type === 'line' && shouldSample(dataLength, 100)) {
        // 折线图：保留趋势特征
        return {
          ...series,
          data: sampleTimeSeriesData(series.data, 100)
        };
      } else if (series.type === 'scatter' && shouldSample(dataLength, 1000)) {
        // 散点图：随机采样
        return {
          ...series,
          data: sampleScatterData(series.data, 1000)
        };
      }
      
      return series;
    });
    
    return option;
  }, [enableSampling]);

  // ============================================
  // 🛡️ 安全的 resize 处理 - 带防抖和存活检查
  // ============================================
  const safeResize = useCallback(() => {
    // 检查实例是否存活
    if (isDisposed.current || !chartInstance.current) return;
    
    try {
      // 检查 DOM 是否还在
      if (!chartRef.current || !document.body.contains(chartRef.current)) return;
      
      // 执行 resize，带平滑动画
      chartInstance.current.resize({
        animation: {
          duration: 200,
          easing: 'cubicOut'
        }
      });
    } catch (e) {
      // 静默处理，避免控制台报错
      console.debug('[useChart] Resize skipped:', e);
    }
  }, []);

  // ============================================
  // 🎯 初始化图表实例 - 严格生命周期管理
  // ============================================
  useEffect(() => {
    if (!chartRef.current) return;
    
    // 注册主题（全局只执行一次）
    registerThemes();
    
    const chartTheme = theme === 'light' ? 'clean-light' : 'neon-cyber';
    
    // 🔒 严格互斥：先销毁旧实例
    if (chartInstance.current) {
      try {
        chartInstance.current.dispose();
      } catch (e) {
        console.debug('[useChart] Dispose error:', e);
      }
      chartInstance.current = null;
    }
    
    // 标记为未销毁
    isDisposed.current = false;
    
    // 🚀 创建新实例
    chartInstance.current = echarts.init(chartRef.current, chartTheme, {
      renderer: 'canvas',
      useDirtyRect: true, // 脏矩形优化，减少重绘区域
    });
    
    // 🆕 不在初始化时设置 option，让 update effect 统一处理
    // 这样可以避免初始化和更新之间的竞态条件
    
    // 绑定点击事件
    if (onClick) {
      chartInstance.current.on('click', onClick);
    }

    // ============================================
    // 📐 防抖 Resize Observer - 消除布局抖动
    // ============================================
    debouncedResizeRef.current = debounce(safeResize, 100);
    
    resizeObserverRef.current = new ResizeObserver(() => {
      debouncedResizeRef.current?.();
    });
    
    resizeObserverRef.current.observe(chartRef.current);

    // ============================================
    // 🧹 清理函数 - 严格销毁
    // ============================================
    return () => {
      isDisposed.current = true;
      
      // 断开 ResizeObserver
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
      
      // 销毁图表实例
      if (chartInstance.current) {
        try {
          chartInstance.current.off('click');
          chartInstance.current.dispose();
        } catch (e) {
          console.debug('[useChart] Cleanup error:', e);
        }
        chartInstance.current = null;
      }
    };
  }, [theme, safeResize]); // 🔧 移除 onClick 依赖，避免重复创建实例

  // ============================================
  // 📊 更新配置 - 智能合并，避免无谓重绘
  // ============================================
  useEffect(() => {
    console.log('[useChart] 更新 effect 触发, chartRef:', !!chartRef.current, 'chartInstance:', !!chartInstance.current);
    
    // 🆕 如果 DOM 存在但图表实例不存在，先创建实例
    if (chartRef.current && !chartInstance.current && !isDisposed.current) {
      console.log('[useChart] 延迟创建图表实例');
      registerThemes();
      const chartTheme = theme === 'light' ? 'clean-light' : 'neon-cyber';
      chartInstance.current = echarts.init(chartRef.current, chartTheme, {
        renderer: 'canvas',
        useDirtyRect: true,
      });
      
      // 设置 ResizeObserver
      if (!resizeObserverRef.current) {
        debouncedResizeRef.current = debounce(safeResize, 100);
        resizeObserverRef.current = new ResizeObserver(() => {
          debouncedResizeRef.current?.();
        });
        resizeObserverRef.current.observe(chartRef.current);
      }
      
      // 绑定点击事件
      if (onClick) {
        chartInstance.current.on('click', onClick);
      }
    }
    
    if (isDisposed.current || !chartInstance.current) {
      console.log('[useChart] 跳过更新: isDisposed=', isDisposed.current, 'chartInstance=', !!chartInstance.current);
      return;
    }
    
    // 检查 option 是否为空对象（没有任何配置）
    const optionKeys = Object.keys(option || {});
    if (optionKeys.length === 0) {
      console.log('[useChart] 跳过更新: 空对象');
      return;
    }
    
    // 🆕 检查 option 是否有效（至少有 series）
    const seriesArray = (option as any)?.series;
    
    // 如果明确设置了空的 series 数组，跳过更新（保持当前状态）
    // 这样在数据加载过程中不会清空图表
    if (Array.isArray(seriesArray) && seriesArray.length === 0) {
      console.log('[useChart] 跳过更新: 空 series 数组');
      return;
    }
    
    // 如果没有 series 字段，检查是否有其他有效配置（如 polar, angleAxis 等）
    const hasOtherConfig = optionKeys.some(key => 
      key !== 'series' && (option as any)[key] !== undefined
    );
    
    if (!Array.isArray(seriesArray) && !hasOtherConfig) {
      console.log('[useChart] 跳过更新: 无 series 且无其他配置');
      return;
    }
    
    // 🆕 检查 series 中是否有数据
    // 支持多种数据格式：
    // 1. 简单数组: [1, 2, 3] 或 [0, 0, 5.2, 3.1]
    // 2. 对象数组: [{value: [...]}, {value: [...]}]
    // 3. 带 itemStyle 的对象数组: [{value: [...], itemStyle: {...}}]
    const hasData = Array.isArray(seriesArray) && seriesArray.some((s: any) => {
      if (!Array.isArray(s.data)) return false;
      if (s.data.length === 0) return false;
      // 检查第一个元素是否有效
      const firstItem = s.data[0];
      // 对象格式 {value: [...]} 或简单值（包括数字0）
      // 🔧 修复：数字0也是有效数据，只排除 undefined 和 null
      if (firstItem === undefined || firstItem === null) return false;
      // 如果是对象，检查 value 字段
      if (typeof firstItem === 'object' && 'value' in firstItem) {
        return firstItem.value !== undefined && firstItem.value !== null;
      }
      // 简单值（数字、字符串等）都是有效的
      return true;
    });
    
    console.log('[useChart] 数据检查: seriesCount=', seriesArray?.length, 'hasData=', hasData);
    
    // 如果有 series 但没有数据，跳过更新（保持当前状态）
    // 这样在数据加载过程中不会清空图表
    if (Array.isArray(seriesArray) && seriesArray.length > 0 && !hasData) {
      console.log('[useChart] 跳过更新: 有 series 但无数据');
      return;
    }
    
    try {
      console.log('[useChart] 执行 setOption, seriesCount:', seriesArray?.length);
      // ✅ 应用数据采样
      const finalOption = processedOption(option);
      
      // 使用 notMerge 完全替换，避免旧数据残留
      chartInstance.current.setOption(finalOption, {
        notMerge: true,     // 完全替换，避免旧数据残留
        lazyUpdate: false,  // 立即更新，确保图表正确渲染
        silent: false,      // 允许触发事件
      });
      console.log('[useChart] setOption 完成');
    } catch (e) {
      console.error('[useChart] setOption error:', e);
    }
    
    // 🆕 数据更新后触发 resize，确保图表正确渲染
    // 使用 requestAnimationFrame 确保 DOM 已更新
    requestAnimationFrame(() => {
      if (!isDisposed.current && chartInstance.current) {
        try {
          chartInstance.current.resize();
        } catch (e) {
          console.debug('[useChart] resize error:', e);
        }
      }
    });
  }, [option, theme, safeResize, processedOption, ...dependencies]); // 🔧 添加 processedOption 依赖

  // ============================================
  // 🖱️ 更新点击监听器 - 确保事件正确绑定
  // ============================================
  useEffect(() => {
    if (isDisposed.current || !chartInstance.current) return;
    
    // 先移除旧的点击事件
    chartInstance.current.off('click');
    
    // 绑定新的点击事件
    if (onClick) {
      chartInstance.current.on('click', onClick);
    }
    
    return () => {
      if (chartInstance.current) {
        chartInstance.current.off('click');
      }
    };
  }, [onClick]);

  return chartRef;
};

// ============================================
// 🔄 导出稳定的 option 比较工具
// ============================================
export const useStableOption = <T extends echarts.EChartsOption>(
  optionFactory: () => T,
  deps: unknown[]
): T => {
  const optionRef = useRef<T | null>(null);
  const depsRef = useRef<unknown[]>([]);
  
  // 浅比较依赖
  const depsChanged = deps.length !== depsRef.current.length || 
    deps.some((dep, i) => dep !== depsRef.current[i]);
  
  if (depsChanged || !optionRef.current) {
    optionRef.current = optionFactory();
    depsRef.current = deps;
  }
  
  return optionRef.current;
};
