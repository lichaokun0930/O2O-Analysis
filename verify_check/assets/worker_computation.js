// ====================================================
// WebWorker JavaScript代码 - 智能门店看板
// 文件位置: assets/worker_computation.js
// 版本: v1.0 (阶段8)
// ====================================================

// 确保window.dash_clientside存在
if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        // 运行WebWorker计算的客户端函数(演示用)
        runWorkerComputation: function(n_clicks) {
            if (!n_clicks) return window.dash_clientside.no_update;
            
            return new Promise((resolve, reject) => {
                console.log("🚀 创建WebWorker线程...");
                
                // 创建Worker (内联方式)
                const workerCode = `
                    // Worker线程代码
                    self.onmessage = function(e) {
                        console.log('⚙️ Worker收到数据:', e.data);
                        
                        const startTime = performance.now();
                        
                        // ===== 模拟复杂计算 =====
                        let sum = 0;
                        const iterations = e.data.iterations || 100000000;
                        
                        for (let i = 0; i < iterations; i++) {
                            sum += Math.sqrt(i) * Math.sin(i);
                            
                            // 每1000万次报告进度
                            if (i % 10000000 === 0) {
                                self.postMessage({
                                    type: 'progress',
                                    percent: (i / iterations * 100).toFixed(1)
                                });
                            }
                        }
                        // ==========================
                        
                        const duration = (performance.now() - startTime) / 1000;
                        
                        // 返回结果
                        self.postMessage({
                            type: 'result',
                            count: iterations,
                            sum: sum,
                            duration: duration
                        });
                        
                        console.log('✅ Worker计算完成');
                    };
                `;
                
                // 创建Blob Worker
                const blob = new Blob([workerCode], { type: 'application/javascript' });
                const worker = new Worker(URL.createObjectURL(blob));
                
                // 监听Worker消息
                worker.onmessage = function(e) {
                    if (e.data.type === 'progress') {
                        console.log(`📊 计算进度: ${e.data.percent}%`);
                    } else if (e.data.type === 'result') {
                        console.log('✅ 收到Worker结果:', e.data);
                        worker.terminate();  // 终止Worker
                        resolve(e.data);     // 返回给Dash
                    }
                };
                
                worker.onerror = function(error) {
                    console.error('❌ Worker错误:', error);
                    worker.terminate();
                    reject(error);
                };
                
                // 启动计算
                worker.postMessage({ iterations: 100000000 });
                console.log('🎯 Worker已启动,主线程继续运行...');
            });
        }
    }
});

// ====================================================
// 实际应用: 智能门店看板的WebWorker计算
// ====================================================

window.dash_clientside.storeAnalytics = {
    /**
     * 订单聚合分析 (使用独立Worker文件)
     * @param {Array} orders - 原始订单数组
     * @param {Array} groupBy - 聚合维度 ['product', 'date', 'scene', 'time_period', 'channel']
     * @param {Object} options - 选项 {topN, sortBy}
     */
    aggregateOrders: function(orders, groupBy, options) {
        // 静默验证数据
        if (!orders || !Array.isArray(orders) || orders.length === 0) {
            return Promise.resolve(null);
        }
        
        // 检查Worker支持
        if (typeof(Worker) === 'undefined') {
            return Promise.resolve(null);
        }
        
        return new Promise((resolve, reject) => {
            console.log(`🚀 启动订单聚合Worker (${orders.length}条订单)`);
            
            let worker;
            try {
                worker = new Worker('/assets/workers/order_aggregator.js');
            } catch (error) {
                console.error('❌ 无法创建Worker:', error);
                return resolve(null);
            }
            
            // 设置超时保护
            const timeout = setTimeout(() => {
                if (worker) {
                    worker.terminate();
                    console.warn('⚠️ Worker超时,已终止');
                    resolve(null);
                }
            }, 30000); // 30秒超时
            
            worker.onmessage = function(e) {
                clearTimeout(timeout);
                if (e.data && e.data.success) {
                    console.log(`✅ 订单聚合完成: ${e.data.meta.processing_time_ms}ms`);
                    worker.terminate();
                    resolve(e.data);
                } else {
                    // 静默处理错误
                    worker.terminate();
                    resolve(null);
                }
            };
            
            worker.onerror = function(error) {
                clearTimeout(timeout);
                // 静默处理错误,避免大量日志
                worker.terminate();
                resolve(null);  // 返回null而不是reject
            };
            
            try {
                worker.postMessage({
                    orders: orders,
                    groupBy: groupBy || ['product', 'date', 'scene'],
                    options: options || { topN: 20, sortBy: 'sales' }
                });
            } catch (error) {
                clearTimeout(timeout);
                worker.terminate();
                resolve(null);
            }
        });
    },
    
    /**
     * 图表数据采样 (使用图表预处理Worker)
     * @param {Array} data - 图表数据
     * @param {Number} maxPoints - 最大点数
     */
    downsampleChartData: function(data, maxPoints) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            return Promise.resolve({ sampled: false, data: data });
        }
        
        if (typeof(Worker) === 'undefined') {
            return Promise.resolve({ sampled: false, data: data });
        }
        
        return new Promise((resolve, reject) => {
            let worker;
            try {
                worker = new Worker('/assets/workers/chart_preprocessor.js');
            } catch (error) {
                return resolve({ sampled: false, data: data });
            }
            
            const timeout = setTimeout(() => {
                if (worker) {
                    worker.terminate();
                    resolve({ sampled: false, data: data });
                }
            }, 10000);
            
            worker.onmessage = function(e) {
                clearTimeout(timeout);
                if (e.data && e.data.success) {
                    worker.terminate();
                    resolve(e.data.data);
                } else {
                    worker.terminate();
                    resolve({ sampled: false, data: data });
                }
            };
            
            worker.onerror = function(error) {
                clearTimeout(timeout);
                worker.terminate();
                resolve({ sampled: false, data: data });
            };
            
            try {
                worker.postMessage({
                    action: 'downsample',
                    data: data,
                    options: { maxPoints: maxPoints || 1000, keepExtremes: true }
                });
            } catch (error) {
                clearTimeout(timeout);
                worker.terminate();
                resolve({ sampled: false, data: data });
            }
        });
    },
    
    /**
     * ECharts数据准备
     */
    prepareEChartsData: function(data, xField, yFields, chartType) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            return Promise.resolve(null);
        }
        
        if (typeof(Worker) === 'undefined') {
            return Promise.resolve(null);
        }
        
        return new Promise((resolve, reject) => {
            let worker;
            try {
                worker = new Worker('/assets/workers/chart_preprocessor.js');
            } catch (error) {
                return resolve(null);
            }
            
            const timeout = setTimeout(() => {
                if (worker) {
                    worker.terminate();
                    resolve(null);
                }
            }, 10000);
            
            worker.onmessage = function(e) {
                clearTimeout(timeout);
                worker.terminate();
                resolve(e.data && e.data.success ? e.data.data : null);
            };
            
            worker.onerror = function(error) {
                clearTimeout(timeout);
                worker.terminate();
                resolve(null);
            };
            
            try {
                worker.postMessage({
                    action: 'prepare_echarts',
                    data: data,
                    options: { xField, yFields, chartType: chartType || 'line' }
                });
            } catch (error) {
                clearTimeout(timeout);
                worker.terminate();
                resolve(null);
            }
        });
    }
};

console.log('✅ 智能门店看板Worker客户端函数已加载');
