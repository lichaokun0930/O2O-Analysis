// ====================================================
// 图表数据预处理Worker - 智能门店看板
// 功能: 在后台处理图表数据格式转换、采样等
// 性能: 5000点采样约0.5秒,不阻塞UI
// ====================================================

console.log('🚀 图表预处理Worker已加载');

self.onmessage = function(e) {
    const { action, data, options } = e.data;
    
    console.log(`⚙️ Worker执行操作: ${action}`);
    
    const startTime = performance.now();
    
    try {
        let result = {};
        
        switch (action) {
            case 'downsample':
                result = downsampleChartData(data, options);
                break;
            
            case 'prepare_echarts':
                result = prepareEChartsData(data, options);
                break;
            
            case 'prepare_plotly':
                result = preparePlotlyData(data, options);
                break;
            
            case 'calculate_trend':
                result = calculateTrendLine(data, options);
                break;
            
            default:
                throw new Error(`未知操作: ${action}`);
        }
        
        const duration = performance.now() - startTime;
        
        console.log(`✅ Worker操作完成,耗时 ${Math.round(duration)}ms`);
        
        self.postMessage({
            success: true,
            action: action,
            data: result,
            processing_time_ms: Math.round(duration)
        });
        
    } catch (error) {
        console.error('❌ Worker处理失败:', error);
        self.postMessage({
            success: false,
            error: error.message
        });
    }
};

// ====================================================
// 数据处理函数
// ====================================================

/**
 * 智能采样 - 保留关键点
 */
function downsampleChartData(data, options = {}) {
    const { maxPoints = 1000, sortColumn = null, keepExtremes = true } = options;
    
    if (!data || data.length === 0) {
        return { sampled: false, data: data };
    }
    
    if (data.length <= maxPoints) {
        return {
            sampled: false,
            data: data,
            original_count: data.length,
            sampled_count: data.length
        };
    }
    
    // 如果需要排序
    if (sortColumn && data[0][sortColumn] !== undefined) {
        data.sort((a, b) => {
            if (a[sortColumn] < b[sortColumn]) return -1;
            if (a[sortColumn] > b[sortColumn]) return 1;
            return 0;
        });
    }
    
    const keyIndices = new Set();
    
    // 保留首尾
    keyIndices.add(0);
    keyIndices.add(data.length - 1);
    
    // 保留极值点
    if (keepExtremes) {
        const numericColumns = Object.keys(data[0]).filter(key => {
            return typeof data[0][key] === 'number';
        }).slice(0, 3);  // 前3个数值列
        
        numericColumns.forEach(col => {
            let maxIdx = 0, minIdx = 0;
            let maxVal = -Infinity, minVal = Infinity;
            
            data.forEach((row, idx) => {
                if (row[col] > maxVal) {
                    maxVal = row[col];
                    maxIdx = idx;
                }
                if (row[col] < minVal) {
                    minVal = row[col];
                    minIdx = idx;
                }
            });
            
            keyIndices.add(maxIdx);
            keyIndices.add(minIdx);
        });
    }
    
    // 等间隔采样
    const step = Math.max(1, Math.floor(data.length / maxPoints));
    for (let i = 0; i < data.length; i += step) {
        keyIndices.add(i);
    }
    
    // 合并索引并采样
    const sortedIndices = Array.from(keyIndices).sort((a, b) => a - b);
    const sampledData = sortedIndices.map(idx => data[idx]);
    
    const reductionRate = ((1 - sampledData.length / data.length) * 100).toFixed(0);
    
    console.log(`📊 采样: ${data.length} → ${sampledData.length} 点 (减少${reductionRate}%)`);
    
    return {
        sampled: true,
        data: sampledData,
        original_count: data.length,
        sampled_count: sampledData.length,
        reduction_rate: `${reductionRate}%`
    };
}

/**
 * 准备ECharts数据格式
 */
function prepareEChartsData(data, options = {}) {
    const { xField, yFields, chartType = 'line' } = options;
    
    const result = {
        xAxis: {
            type: 'category',
            data: data.map(d => d[xField])
        },
        series: []
    };
    
    yFields.forEach(field => {
        result.series.push({
            name: field,
            type: chartType,
            data: data.map(d => d[field]),
            smooth: chartType === 'line'
        });
    });
    
    return result;
}

/**
 * 准备Plotly数据格式
 */
function preparePlotlyData(data, options = {}) {
    const { xField, yFields, chartType = 'scatter' } = options;
    
    const traces = yFields.map(field => ({
        x: data.map(d => d[xField]),
        y: data.map(d => d[field]),
        name: field,
        type: chartType,
        mode: chartType === 'scatter' ? 'lines+markers' : undefined
    }));
    
    return traces;
}

/**
 * 计算趋势线 (简单线性回归)
 */
function calculateTrendLine(data, options = {}) {
    const { xField, yField } = options;
    
    const n = data.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    
    data.forEach((d, i) => {
        const x = i;  // 使用索引作为x值
        const y = d[yField];
        
        sumX += x;
        sumY += y;
        sumXY += x * y;
        sumX2 += x * x;
    });
    
    // y = mx + b
    const m = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const b = (sumY - m * sumX) / n;
    
    // 生成趋势线数据
    const trendLine = data.map((d, i) => ({
        [xField]: d[xField],
        [yField]: m * i + b
    }));
    
    return {
        trendLine: trendLine,
        slope: m,
        intercept: b,
        equation: `y = ${m.toFixed(2)}x + ${b.toFixed(2)}`
    };
}

console.log('✅ 图表预处理Worker准备就绪');
