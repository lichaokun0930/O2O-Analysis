/**
 * ECharts 响应式增强脚本
 * 功能：
 * 1. 窗口resize时自动重绘所有ECharts图表
 * 2. 响应式断点：移动端/平板/桌面自适应
 * 3. 防抖优化：避免频繁重绘
 */

(function() {
    'use strict';
    
    // ==================== 配置项 ====================
    const CONFIG = {
        // 响应式断点（单位：px）
        breakpoints: {
            mobile: 576,    // 小于576px为手机
            tablet: 768,    // 576-768px为平板
            desktop: 992    // 大于768px为桌面
        },
        
        // 不同设备的高度配置
        chartHeights: {
            mobile: {
                'chart-slot-distribution': '300px',
                'chart-scene-distribution': '300px',
                'chart-revenue-top10': '350px',
                'chart-period-comparison': '350px'
            },
            tablet: {
                'chart-slot-distribution': '400px',
                'chart-scene-distribution': '400px',
                'chart-revenue-top10': '400px',
                'chart-period-comparison': '400px'
            },
            desktop: {
                'chart-slot-distribution': '450px',
                'chart-scene-distribution': '450px',
                'chart-revenue-top10': '450px',
                'chart-period-comparison': '450px'
            }
        },
        
        // 防抖延迟（ms）
        debounceDelay: 300
    };
    
    // ==================== 工具函数 ====================
    
    /**
     * 防抖函数
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * 获取当前设备类型
     */
    function getDeviceType() {
        const width = window.innerWidth;
        if (width < CONFIG.breakpoints.mobile) {
            return 'mobile';
        } else if (width < CONFIG.breakpoints.desktop) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }
    
    /**
     * 获取所有ECharts实例
     */
    function getAllEChartsInstances() {
        const instances = [];
        
        // 查找所有ECharts容器
        const echartsContainers = document.querySelectorAll('[id*="echarts"]');
        
        echartsContainers.forEach(container => {
            // 尝试从全局echarts对象获取实例
            if (window.echarts) {
                const instance = window.echarts.getInstanceByDom(container);
                if (instance) {
                    instances.push({
                        id: container.id,
                        instance: instance,
                        container: container
                    });
                }
            }
        });
        
        return instances;
    }
    
    /**
     * 调整图表容器高度（响应式断点）
     */
    function adjustChartHeights() {
        const deviceType = getDeviceType();
        const heights = CONFIG.chartHeights[deviceType];
        
        console.log(`📱 当前设备类型: ${deviceType} (宽度: ${window.innerWidth}px)`);
        
        // 遍历所有图表容器，应用对应高度
        Object.keys(heights).forEach(chartId => {
            const container = document.getElementById(chartId);
            if (container) {
                const newHeight = heights[chartId];
                container.style.height = newHeight;
                console.log(`  📊 调整 ${chartId} 高度: ${newHeight}`);
            }
        });
    }
    
    /**
     * 重绘所有ECharts图表
     */
    function resizeAllCharts() {
        const instances = getAllEChartsInstances();
        
        if (instances.length === 0) {
            console.log('⚠️ 未找到ECharts实例');
            return;
        }
        
        console.log(`🔄 重绘 ${instances.length} 个ECharts图表...`);
        
        instances.forEach(({id, instance}) => {
            try {
                instance.resize();
                console.log(`  ✅ ${id} 重绘成功`);
            } catch (error) {
                console.error(`  ❌ ${id} 重绘失败:`, error);
            }
        });
    }
    
    /**
     * 完整的响应式处理
     */
    function handleResponsive() {
        console.log('═══════════════════════════════════════');
        console.log('🎯 ECharts响应式处理触发');
        console.log(`📏 窗口尺寸: ${window.innerWidth}×${window.innerHeight}`);
        
        // 1. 调整容器高度
        adjustChartHeights();
        
        // 2. 等待DOM更新后重绘图表
        setTimeout(() => {
            resizeAllCharts();
            console.log('✅ 响应式处理完成');
            console.log('═══════════════════════════════════════');
        }, 100);
    }
    
    // ==================== 初始化 ====================
    
    /**
     * 初始化响应式监听
     */
    function initialize() {
        console.log('🚀 ECharts响应式增强脚本已加载');
        console.log('📋 配置断点:', CONFIG.breakpoints);
        
        // 1. 窗口resize监听（防抖）
        const debouncedResize = debounce(handleResponsive, CONFIG.debounceDelay);
        window.addEventListener('resize', debouncedResize);
        console.log('✅ 窗口resize监听已启用（防抖延迟: ' + CONFIG.debounceDelay + 'ms）');
        
        // 2. 初始化时执行一次
        setTimeout(() => {
            handleResponsive();
        }, 1000); // 等待图表渲染完成
        
        // 3. 监听Dash回调完成（使用MutationObserver）
        const observer = new MutationObserver(debounce(function(mutations) {
            // 检测是否有ECharts图表更新
            const hasEChartsUpdate = mutations.some(mutation => {
                return Array.from(mutation.addedNodes).some(node => {
                    return node.id && node.id.includes('echarts');
                });
            });
            
            if (hasEChartsUpdate) {
                console.log('🔍 检测到ECharts图表更新，触发响应式处理');
                setTimeout(handleResponsive, 200);
            }
        }, 500));
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        console.log('✅ DOM变化监听已启用');
    }
    
    // ==================== 暴露全局API ====================
    window.EChartsResponsive = {
        resize: resizeAllCharts,
        adjustHeights: adjustChartHeights,
        handleResponsive: handleResponsive,
        getDeviceType: getDeviceType,
        config: CONFIG
    };
    
    // ==================== 启动 ====================
    
    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
})();
