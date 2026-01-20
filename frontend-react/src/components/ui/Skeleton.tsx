import React from 'react';

// ============================================
// 🌟 基础光效组件：带动态扫光动画的灰色块
// ============================================
export const ShimmerBlock = ({ 
  className = "", 
  style = {} 
}: { 
  className?: string, 
  style?: React.CSSProperties 
}) => (
  <div 
    className={`relative overflow-hidden bg-white/5 rounded-lg ${className}`}
    style={style}
  >
    {/* 扫光动画层：从左向右滑动的渐变光带 */}
    <div 
      className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent"
      style={{
        animation: 'shimmer 1.5s infinite',
      }}
    />
  </div>
);

// ============================================
// 📊 图表骨架：模拟左侧标题、右侧图例、底部柱状图
// ============================================
export const ChartSkeleton = ({ height = 'h-full' }: { height?: string }) => (
  <div className={`glass-panel rounded-2xl p-6 ${height} flex flex-col gap-4`}>
    {/* 头部：标题 + 操作按钮 */}
    <div className="flex justify-between items-start">
      <div className="space-y-2">
        <ShimmerBlock className="h-5 w-32" />
        <ShimmerBlock className="h-3 w-24 opacity-60" />
      </div>
      <ShimmerBlock className="h-8 w-20 rounded-full" />
    </div>
    
    {/* 图表区域：随机高度柱状条模拟真实数据感 */}
    <div className="flex-1 w-full flex items-end gap-2 pt-4">
      {[...Array(12)].map((_, i) => (
        <ShimmerBlock 
          key={i} 
          className="flex-1 rounded-t-sm" 
          style={{ height: `${Math.random() * 60 + 20}%` }} 
        />
      ))}
    </div>
    
    {/* 底部图例 */}
    <div className="flex justify-center gap-6 pt-2">
      <ShimmerBlock className="h-3 w-16" />
      <ShimmerBlock className="h-3 w-16" />
      <ShimmerBlock className="h-3 w-16" />
    </div>
  </div>
);

// ============================================
// 📈 KPI卡片骨架：模拟数字和趋势图标
// ============================================
export const KpiSkeleton = () => (
  <div className="glass-panel rounded-2xl p-5 h-full flex flex-col justify-between">
    <div className="flex justify-between items-start">
      <div className="space-y-3">
        <ShimmerBlock className="h-3 w-20 opacity-70" />
        <ShimmerBlock className="h-7 w-28" />
      </div>
      <ShimmerBlock className="h-10 w-10 rounded-xl" />
    </div>
    <div className="flex gap-2 mt-4">
      <ShimmerBlock className="h-5 w-14 rounded-md" />
      <ShimmerBlock className="h-5 w-20 rounded-md opacity-50" />
    </div>
  </div>
);

// ============================================
// 🤖 AI面板骨架
// ============================================
export const AIPanelSkeleton = () => (
  <div className="glass-panel rounded-2xl p-6 h-full flex flex-col gap-4">
    {/* 头部 */}
    <div className="flex items-center gap-3">
      <ShimmerBlock className="h-10 w-10 rounded-xl" />
      <div className="space-y-2 flex-1">
        <ShimmerBlock className="h-5 w-32" />
        <ShimmerBlock className="h-3 w-24 opacity-60" />
      </div>
    </div>
    
    {/* 洞察卡片 */}
    <div className="space-y-3 flex-1">
      <ShimmerBlock className="h-20 w-full rounded-xl" />
      <ShimmerBlock className="h-20 w-full rounded-xl" />
      <ShimmerBlock className="h-20 w-full rounded-xl" />
      <ShimmerBlock className="h-16 w-full rounded-xl opacity-60" />
    </div>
    
    {/* 底部操作 */}
    <ShimmerBlock className="h-10 w-full rounded-lg" />
  </div>
);

// ============================================
// 📋 表格骨架
// ============================================
export const TableSkeleton = () => (
  <div className="glass-panel rounded-2xl p-6">
    {/* 表头 */}
    <div className="flex gap-4 mb-4 pb-4 border-b border-white/5">
      <ShimmerBlock className="h-4 w-24" />
      <ShimmerBlock className="h-4 w-20" />
      <ShimmerBlock className="h-4 w-16" />
      <ShimmerBlock className="h-4 w-20" />
      <ShimmerBlock className="h-4 w-16 ml-auto" />
    </div>
    
    {/* 表格行 */}
    {[...Array(5)].map((_, i) => (
      <div key={i} className="flex gap-4 py-3 border-b border-white/5 last:border-0">
        <ShimmerBlock className="h-4 w-28" />
        <ShimmerBlock className="h-4 w-20" />
        <ShimmerBlock className="h-4 w-16" />
        <ShimmerBlock className="h-4 w-24" />
        <ShimmerBlock className="h-4 w-12 ml-auto" />
      </div>
    ))}
  </div>
);

// ============================================
// 🎯 仪表盘整体骨架：1:1 复刻首页 Grid 布局
// ============================================
export const DashboardSkeleton = () => {
  return (
    <div className="grid grid-cols-12 gap-6 w-full pb-12">
      {/* Row 1: 6个KPI卡片 - 与真实布局完全一致 */}
      {[...Array(6)].map((_, i) => (
        <div 
          key={i} 
          className="col-span-6 lg:col-span-2 h-[120px] animate-fade-in-up"
          style={{ animationDelay: `${i * 50}ms` }}
        >
          <KpiSkeleton />
        </div>
      ))}

      {/* Row 2: 主图表 + AI面板 */}
      <div 
        className="col-span-12 xl:col-span-8 h-[550px] animate-fade-in-up"
        style={{ animationDelay: '300ms' }}
      >
        <ChartSkeleton />
      </div>
      <div 
        className="col-span-12 xl:col-span-4 h-[550px] animate-fade-in-up"
        style={{ animationDelay: '350ms' }}
      >
        <AIPanelSkeleton />
      </div>

      {/* Row 3: 次要图表 */}
      <div 
        className="col-span-12 xl:col-span-5 h-[450px] animate-fade-in-up"
        style={{ animationDelay: '400ms' }}
      >
        <ChartSkeleton />
      </div>
      <div 
        className="col-span-12 xl:col-span-7 h-[450px] animate-fade-in-up"
        style={{ animationDelay: '450ms' }}
      >
        <ChartSkeleton />
      </div>
    </div>
  );
};

// ============================================
// 🔄 通用加载占位符
// ============================================
export const LoadingPlaceholder = ({ 
  text = "加载中...",
  className = ""
}: { 
  text?: string,
  className?: string 
}) => (
  <div className={`flex flex-col items-center justify-center gap-4 ${className}`}>
    <div className="relative">
      <div className="w-12 h-12 rounded-full border-2 border-white/10 border-t-indigo-500 animate-spin" />
      <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-transparent border-b-purple-500 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
    </div>
    <p className="text-sm text-slate-400 font-mono animate-pulse">{text}</p>
  </div>
);

export default DashboardSkeleton;
