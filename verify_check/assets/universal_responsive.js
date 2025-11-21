/**
 * 通用响应式增强脚本
 * 功能：支持所有图表组件的响应式自适应
 * 组件类型：
 * 1. ECharts 图表
 * 2. Plotly 图表
 * 3. Dash Table 表格
 * 4. 普通 HTML 容器
 */

(function() {
    'use strict';
    
    // 开发模式控制（生产环境设为false）
    const DEBUG_MODE = window.DEBUG_MODE || false;
    
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
                default: '300px',
                table: '400px'
            },
            tablet: {
                default: '400px',
                table: '500px'
            },
            desktop: {
                default: '450px',
                table: '600px'
            }
        },
        
        // 防抖延迟（ms）
        debounceDelay: 300,
        
        // 组件选择器
        selectors: {
            echarts: '[id*="echarts"]',
            plotly: '.js-plotly-plot',
            dashTable: '.dash-table-container',
            dashGraph: '.dash-graph'
        }
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
    
    // ==================== ECharts 处理 ====================
    
    /**
     * 获取所有ECharts实例
     */
    function getAllEChartsInstances() {
        const instances = [];
        
        if (!window.echarts) {
            return instances;
        }
        
        const containers = document.querySelectorAll(CONFIG.selectors.echarts);
        
        containers.forEach(container => {
            const instance = window.echarts.getInstanceByDom(container);
            if (instance) {
                instances.push({
                    type: 'echarts',
                    id: container.id,
                    instance: instance,
                    container: container
                });
            }
        });
        
        return instances;
    }
    
    /**
     * 重绘所有ECharts图表
     */
    function resizeECharts() {
        const instances = getAllEChartsInstances();
        
        if (instances.length === 0) {
            return 0;
        }
        
        let successCount = 0;
        instances.forEach(({id, instance}) => {
            try {
                instance.resize();
                successCount++;
            } catch (error) {
                console.error(`❌ ECharts重绘失败 [${id}]:`, error);
            }
        });
        
        return successCount;
    }
    
    // ==================== Plotly 处理 ====================
    
    /**
     * 获取所有Plotly图表
     */
    function getAllPlotlyCharts() {
        const charts = [];
        const containers = document.querySelectorAll(CONFIG.selectors.plotly);
        
        containers.forEach(container => {
            // Plotly会在容器上附加.data属性
            if (container.data || container.layout) {
                charts.push({
                    type: 'plotly',
                    id: container.id || 'plotly-' + Math.random().toString(36).substr(2, 9),
                    container: container
                });
            }
        });
        
        return charts;
    }
    
    /**
     * 重绘所有Plotly图表
     */
    function resizePlotly() {
        const charts = getAllPlotlyCharts();
        
        if (charts.length === 0) {
            return 0;
        }
        
        let successCount = 0;
        charts.forEach(({id, container}) => {
            try {
                if (window.Plotly) {
                    window.Plotly.Plots.resize(container);
                    successCount++;
                }
            } catch (error) {
                console.error(`❌ Plotly重绘失败 [${id}]:`, error);
            }
        });
        
        return successCount;
    }
    
    // ==================== Dash Table 处理 ====================
    
    /**
     * 获取所有Dash Table
     */
    function getAllDashTables() {
        const tables = [];
        const containers = document.querySelectorAll(CONFIG.selectors.dashTable);
        
        containers.forEach(container => {
            tables.push({
                type: 'dash-table',
                id: container.id || 'table-' + Math.random().toString(36).substr(2, 9),
                container: container
            });
        });
        
        return tables;
    }
    
    /**
     * 调整Dash Table布局
     */
    function resizeDashTables() {
        const tables = getAllDashTables();
        
        if (tables.length === 0) {
            return 0;
        }
        
        const deviceType = getDeviceType();
        const height = CONFIG.chartHeights[deviceType].table;
        
        let successCount = 0;
        tables.forEach(({id, container}) => {
            try {
                // 调整表格容器高度
                container.style.maxHeight = height;
                
                // 触发表格重新计算（通过临时修改display）
                const display = container.style.display;
                container.style.display = 'none';
                container.offsetHeight; // 强制重排
                container.style.display = display;
                
                successCount++;
            } catch (error) {
                console.error(`❌ Table调整失败 [${id}]:`, error);
            }
        });
        
        return successCount;
    }
    
    // ==================== 通用容器处理 ====================
    
    /**
     * 调整所有dash-graph容器高度
     */
    function adjustDashGraphHeights() {
        const deviceType = getDeviceType();
        const height = CONFIG.chartHeights[deviceType].default;
        
        const containers = document.querySelectorAll(CONFIG.selectors.dashGraph);
        
        let adjustedCount = 0;
        containers.forEach(container => {
            // 如果容器内有Plotly或ECharts，调整其高度
            if (container.querySelector('.js-plotly-plot') || 
                container.querySelector('[id*="echarts"]')) {
                container.style.height = height;
                adjustedCount++;
            }
        });
        
        return adjustedCount;
    }
    
    // ==================== 统一响应式处理 ====================
    
    /**
     * 重绘所有组件
     */
    function resizeAllComponents() {
        const stats = {
            echarts: 0,
            plotly: 0,
            tables: 0,
            containers: 0
        };
        
        // 1. 调整容器高度
        stats.containers = adjustDashGraphHeights();
        
        // 2. 重绘ECharts
        stats.echarts = resizeECharts();
        
        // 3. 重绘Plotly
        stats.plotly = resizePlotly();
        
        // 4. 调整Table
        stats.tables = resizeDashTables();
        
        return stats;
    }
    
    /**
     * 完整的响应式处理
     */
    function handleResponsive() {
        const deviceType = getDeviceType();
        
        if (DEBUG_MODE) {
            console.log('═══════════════════════════════════════');
            console.log('🎯 通用响应式处理触发');
            console.log(`📱 设备类型: ${deviceType} | 窗口尺寸: ${window.innerWidth}×${window.innerHeight}`);
        }
        
        // 等待DOM更新后重绘
        setTimeout(() => {
            const stats = resizeAllComponents();
            
            const total = stats.echarts + stats.plotly + stats.tables + stats.containers;
            
            if (DEBUG_MODE) {
                if (total > 0) {
                    console.log('📊 组件统计:');
                    if (stats.echarts > 0) console.log(`  - ECharts: ${stats.echarts} 个`);
                    if (stats.plotly > 0) console.log(`  - Plotly: ${stats.plotly} 个`);
                    if (stats.tables > 0) console.log(`  - Tables: ${stats.tables} 个`);
                    if (stats.containers > 0) console.log(`  - 容器调整: ${stats.containers} 个`);
                    console.log('✅ 响应式处理完成');
                } else {
                    console.log('ℹ️ 未找到需要处理的组件（可能正在加载中）');
                }
                console.log('═══════════════════════════════════════');
            }
        }, 100);
    }
    
    // ==================== 智能检测 ====================
    
    /**
     * 检测组件类型变化
     */
    function detectComponentChanges(mutations) {
        let hasChanges = false;
        
        mutations.forEach(mutation => {
            const addedNodes = Array.from(mutation.addedNodes);
            
            // 检测ECharts
            if (addedNodes.some(node => node.id && node.id.includes('echarts'))) {
                hasChanges = true;
            }
            
            // 检测Plotly
            if (addedNodes.some(node => node.classList && 
                node.classList.contains('js-plotly-plot'))) {
                hasChanges = true;
            }
            
            // 检测Table
            if (addedNodes.some(node => node.classList && 
                node.classList.contains('dash-table-container'))) {
                hasChanges = true;
            }
        });
        
        return hasChanges;
    }
    
    // ==================== 初始化 ====================
    
    /**
     * 初始化响应式监听
     */
    function initialize() {
        if (DEBUG_MODE) {
            console.log('🚀 通用响应式增强脚本已加载');
            console.log('📋 支持组件: ECharts, Plotly, Dash Table');
            console.log('📏 响应式断点:', CONFIG.breakpoints);
        }
        
        // 1. 窗口resize监听（防抖）
        const debouncedResize = debounce(handleResponsive, CONFIG.debounceDelay);
        window.addEventListener('resize', debouncedResize);
        if (DEBUG_MODE) console.log('✅ 窗口resize监听已启用（防抖: ' + CONFIG.debounceDelay + 'ms）');
        
        // 2. 初始化时执行一次
        setTimeout(() => {
            handleResponsive();
        }, 1000);
        
        // 3. 监听DOM变化
        const observer = new MutationObserver(debounce(function(mutations) {
            if (detectComponentChanges(mutations)) {
                if (DEBUG_MODE) console.log('🔍 检测到组件更新，触发响应式处理');
                setTimeout(handleResponsive, 200);
            }
        }, 500));
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        if (DEBUG_MODE) console.log('✅ DOM变化监听已启用');
        
        // 4. 监听Tab切换（针对Dash Tabs）
        document.addEventListener('click', function(e) {
            const target = e.target;
            // 检测是否是Tab按钮
            if (target.classList && 
                (target.classList.contains('tab') || 
                 target.closest('.tab'))) {
                if (DEBUG_MODE) console.log('🔄 Tab切换检测，延迟触发响应式处理');
                setTimeout(handleResponsive, 300);
            }
        });
        if (DEBUG_MODE) console.log('✅ Tab切换监听已启用');
    }
    
    // ==================== 暴露全局API ====================
    window.UniversalResponsive = {
        resize: resizeAllComponents,
        resizeECharts: resizeECharts,
        resizePlotly: resizePlotly,
        resizeTables: resizeDashTables,
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
