// ====================================================
// 订单聚合Worker - 智能门店看板专用
// 功能: 在后台线程聚合大量订单数据
// 性能: 6万条订单约2秒,不阻塞UI
// ====================================================

// 开发模式控制（生产环境设为false）
const DEBUG_MODE = false;

// 只在第一次加载且开发模式时打印
let isInitialized = false;
if (!isInitialized && DEBUG_MODE) {
    console.log('🚀 订单聚合Worker已加载');
    isInitialized = true;
}

self.onmessage = function(e) {
    // 静默处理无效消息（避免大量日志）
    if (!e.data || typeof e.data !== 'object') {
        return;  // 直接忽略,不打印日志
    }
    
    const { orders, groupBy, options } = e.data;
    
    // 静默验证必要字段
    if (!orders || !Array.isArray(orders)) {
        return;  // 直接忽略,不打印日志
    }
    
    if (!groupBy || !Array.isArray(groupBy)) {
        return;  // 直接忽略,不打印日志
    }
    
    // 只有收到有效数据且在开发模式才打印详细日志
    if (DEBUG_MODE) {
        console.log(`⚙️ Worker开始处理 ${orders.length} 条订单...`);
        console.log(`📊 聚合维度: ${groupBy.join(', ')}`);
    }
    
    const startTime = performance.now();
    
    try {
        const result = {
            success: true,
            data: {},
            meta: {
                total_orders: orders.length,
                processing_time_ms: 0,
                timestamp: new Date().toISOString()
            }
        };
        
        // 按商品聚合
        if (groupBy.includes('product')) {
            result.data.byProduct = aggregateByProduct(orders, options);
            if (DEBUG_MODE) console.log(`✅ 商品聚合完成: ${result.data.byProduct.length} 个商品`);
        }
        
        // 按日期聚合
        if (groupBy.includes('date')) {
            result.data.byDate = aggregateByDate(orders, options);
            if (DEBUG_MODE) console.log(`✅ 日期聚合完成: ${result.data.byDate.length} 天`);
        }
        
        // 按场景聚合
        if (groupBy.includes('scene')) {
            result.data.byScene = aggregateByScene(orders, options);
            if (DEBUG_MODE) console.log(`✅ 场景聚合完成: ${result.data.byScene.length} 个场景`);
        }
        
        // 按时段聚合
        if (groupBy.includes('time_period')) {
            result.data.byTimePeriod = aggregateByTimePeriod(orders, options);
            if (DEBUG_MODE) console.log(`✅ 时段聚合完成: ${result.data.byTimePeriod.length} 个时段`);
        }
        
        // 按渠道聚合
        if (groupBy.includes('channel')) {
            result.data.byChannel = aggregateByChannel(orders, options);
            if (DEBUG_MODE) console.log(`✅ 渠道聚合完成: ${result.data.byChannel.length} 个渠道`);
        }
        
        const duration = performance.now() - startTime;
        result.meta.processing_time_ms = Math.round(duration);
        
        if (DEBUG_MODE) console.log(`🎉 Worker聚合完成,耗时 ${result.meta.processing_time_ms}ms`);
        
        self.postMessage(result);
        
    } catch (error) {
        console.error('❌ Worker聚合失败:', error);
        self.postMessage({
            success: false,
            error: error.message,
            stack: error.stack
        });
    }
};

// ====================================================
// 聚合函数
// ====================================================

/**
 * 按商品聚合
 */
function aggregateByProduct(orders, options = {}) {
    const { topN = null, sortBy = 'sales' } = options;
    const productMap = {};
    
    orders.forEach(order => {
        const key = order.product_name || '未知商品';
        
        if (!productMap[key]) {
            productMap[key] = {
                product_name: key,
                barcode: order.barcode || '',
                category_level1: order.category_level1 || '',
                category_level3: order.category_level3 || '',
                total_sales: 0,
                total_profit: 0,
                total_quantity: 0,
                total_cost: 0,
                order_count: 0,
                avg_price: 0,
                profit_margin: 0
            };
        }
        
        const item = productMap[key];
        item.total_sales += (order.amount || order.price * order.quantity || 0);
        item.total_profit += (order.profit || 0);
        item.total_quantity += (order.quantity || 0);
        item.total_cost += ((order.cost || 0) * (order.quantity || 0));
        item.order_count += 1;
    });
    
    // 计算衍生指标
    let products = Object.values(productMap);
    products.forEach(p => {
        p.avg_price = p.total_quantity > 0 ? p.total_sales / p.total_quantity : 0;
        p.profit_margin = p.total_sales > 0 ? (p.total_profit / p.total_sales * 100) : 0;
    });
    
    // 排序
    const sortField = {
        'sales': 'total_sales',
        'profit': 'total_profit',
        'quantity': 'total_quantity',
        'orders': 'order_count'
    }[sortBy] || 'total_sales';
    
    products.sort((a, b) => b[sortField] - a[sortField]);
    
    // 取TopN
    if (topN && topN > 0) {
        products = products.slice(0, topN);
    }
    
    return products;
}

/**
 * 按日期聚合
 */
function aggregateByDate(orders, options = {}) {
    const dateMap = {};
    
    orders.forEach(order => {
        // 提取日期部分 (YYYY-MM-DD)
        let date = order.date;
        if (typeof date === 'string') {
            date = date.split(' ')[0];
        } else if (date instanceof Date) {
            date = date.toISOString().split('T')[0];
        } else {
            date = '未知日期';
        }
        
        if (!dateMap[date]) {
            dateMap[date] = {
                date: date,
                sales: 0,
                profit: 0,
                cost: 0,
                orders: 0,
                quantity: 0,
                avg_order_value: 0
            };
        }
        
        const item = dateMap[date];
        item.sales += (order.amount || order.price * order.quantity || 0);
        item.profit += (order.profit || 0);
        item.cost += ((order.cost || 0) * (order.quantity || 0));
        item.orders += 1;
        item.quantity += (order.quantity || 0);
    });
    
    // 计算平均订单金额
    let dates = Object.values(dateMap);
    dates.forEach(d => {
        d.avg_order_value = d.orders > 0 ? d.sales / d.orders : 0;
    });
    
    // 按日期排序
    dates.sort((a, b) => {
        if (a.date < b.date) return -1;
        if (a.date > b.date) return 1;
        return 0;
    });
    
    return dates;
}

/**
 * 按场景聚合
 */
function aggregateByScene(orders, options = {}) {
    const sceneMap = {};
    
    orders.forEach(order => {
        const scene = order.scene || '未分类';
        
        if (!sceneMap[scene]) {
            sceneMap[scene] = {
                scene: scene,
                sales: 0,
                profit: 0,
                orders: 0,
                quantity: 0,
                avg_order_value: 0
            };
        }
        
        const item = sceneMap[scene];
        item.sales += (order.amount || order.price * order.quantity || 0);
        item.profit += (order.profit || 0);
        item.orders += 1;
        item.quantity += (order.quantity || 0);
    });
    
    let scenes = Object.values(sceneMap);
    scenes.forEach(s => {
        s.avg_order_value = s.orders > 0 ? s.sales / s.orders : 0;
    });
    
    // 按销售额排序
    scenes.sort((a, b) => b.sales - a.sales);
    
    return scenes;
}

/**
 * 按时段聚合
 */
function aggregateByTimePeriod(orders, options = {}) {
    const timeMap = {};
    
    orders.forEach(order => {
        const timePeriod = order.time_period || '未知时段';
        
        if (!timeMap[timePeriod]) {
            timeMap[timePeriod] = {
                time_period: timePeriod,
                sales: 0,
                profit: 0,
                orders: 0,
                quantity: 0
            };
        }
        
        const item = timeMap[timePeriod];
        item.sales += (order.amount || order.price * order.quantity || 0);
        item.profit += (order.profit || 0);
        item.orders += 1;
        item.quantity += (order.quantity || 0);
    });
    
    let timePeriods = Object.values(timeMap);
    
    // 按时段排序(可以自定义顺序)
    const timeOrder = {
        '清晨(6-9点)': 1,
        '上午(9-12点)': 2,
        '正午(12-14点)': 3,
        '下午(14-18点)': 4,
        '傍晚(18-21点)': 5,
        '晚间(21-24点)': 6,
        '深夜(0-3点)': 7,
        '凌晨(3-6点)': 8
    };
    
    timePeriods.sort((a, b) => {
        const orderA = timeOrder[a.time_period] || 999;
        const orderB = timeOrder[b.time_period] || 999;
        return orderA - orderB;
    });
    
    return timePeriods;
}

/**
 * 按渠道聚合
 */
function aggregateByChannel(orders, options = {}) {
    const channelMap = {};
    
    orders.forEach(order => {
        const channel = order.channel || '未知渠道';
        
        if (!channelMap[channel]) {
            channelMap[channel] = {
                channel: channel,
                sales: 0,
                profit: 0,
                orders: 0,
                quantity: 0,
                avg_order_value: 0
            };
        }
        
        const item = channelMap[channel];
        item.sales += (order.amount || order.price * order.quantity || 0);
        item.profit += (order.profit || 0);
        item.orders += 1;
        item.quantity += (order.quantity || 0);
    });
    
    let channels = Object.values(channelMap);
    channels.forEach(c => {
        c.avg_order_value = c.orders > 0 ? c.sales / c.orders : 0;
    });
    
    // 按销售额排序
    channels.sort((a, b) => b.sales - a.sales);
    
    return channels;
}

console.log('✅ 订单聚合Worker准备就绪');
