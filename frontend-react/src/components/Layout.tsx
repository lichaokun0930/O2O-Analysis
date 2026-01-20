import React, { ReactNode, useState, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, PieChart, TrendingUp, Settings, User, Bell, Zap, Sun, Moon, Database, AlertCircle, CheckCircle, ChevronRight, Store } from 'lucide-react';
import GlobalFilter from './GlobalFilter';
import { useGlobalContext } from '../store/GlobalContext';

// ============================================
// 🚀 意图预加载：鼠标悬停时预加载对应视图
// ============================================
const prefetchedRoutes = new Set<string>();

const prefetchRoute = (route: string) => {
  if (prefetchedRoutes.has(route)) return;
  prefetchedRoutes.add(route);
  
  // 根据路由预加载对应的视图组件（仅懒加载的组件）
  switch (route) {
    case '/data':
      import('../views/DataManagement');
      break;
    case '/stores':
      import('../views/StoreComparisonView');
      break;
    default:
      break;
  }
};

interface LayoutProps {
  children: ReactNode;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, theme, onToggleTheme }) => {
  const location = useLocation();
  const { systemStatus } = useGlobalContext();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // 系统状态文本
  const getStatusText = () => {
    if (systemStatus.database === 'checking') return 'CHECKING...';
    if (systemStatus.database === 'disconnected') return 'DB OFFLINE';
    if (systemStatus.redis === 'disconnected') return 'CACHE OFFLINE';
    return 'ONLINE';
  };
  
  const isSystemHealthy = systemStatus.database === 'connected';
  
  return (
    <div className="flex min-h-screen font-sans selection:bg-neon-purple selection:text-white relative transition-colors duration-500">
      
      {/* Sidebar - Glassy with smooth collapse animation */}
      <aside 
        className="hidden md:flex flex-col glass-panel border-r border-white/5 sticky top-0 h-screen z-40"
        style={{
          width: sidebarCollapsed ? '80px' : '256px',
          transition: 'width 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      >
        <div className="h-20 flex items-center border-b border-white/5 overflow-hidden" style={{ paddingLeft: sidebarCollapsed ? '0' : '24px', justifyContent: sidebarCollapsed ? 'center' : 'flex-start', transition: 'padding 0.35s cubic-bezier(0.4, 0, 0.2, 1)' }}>
          <div className="relative group cursor-pointer flex-shrink-0">
             <div className="absolute inset-0 bg-neon-purple blur-lg opacity-20 group-hover:opacity-40 transition-opacity"></div>
             <div className="relative bg-gradient-to-br from-indigo-600 to-purple-700 w-9 h-9 rounded-xl flex items-center justify-center shadow-lg border border-white/10 group-hover:scale-105 transition-transform">
                <Zap size={20} className="text-white fill-current" />
             </div>
          </div>
          <div 
            className="ml-3 overflow-hidden whitespace-nowrap"
            style={{
              opacity: sidebarCollapsed ? 0 : 1,
              width: sidebarCollapsed ? 0 : 'auto',
              transition: 'opacity 0.25s ease, width 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          >
            <span className="font-bold text-xl tracking-tight text-white font-mono">
              O2O<span className="text-neon-purple">Dashboard</span>
            </span>
            <div className="text-[10px] text-slate-400 uppercase tracking-widest">React v1.0</div>
          </div>
        </div>

        <nav className="flex-1 py-8 space-y-2 px-3 overflow-hidden">
          <NavItem to="/" icon={<LayoutDashboard size={20} />} label="经营总览" active={location.pathname === '/'} collapsed={sidebarCollapsed} />
          <NavItem to="/stores" icon={<Store size={20} />} label="全量门店对比" active={location.pathname === '/stores'} collapsed={sidebarCollapsed} />
          <NavItem to="/data" icon={<Database size={20} />} label="数据管理" active={location.pathname === '/data'} collapsed={sidebarCollapsed} />
          <NavItem to="/channels" icon={<PieChart size={20} />} label="渠道分析" active={location.pathname === '/channels'} collapsed={sidebarCollapsed} />
          <NavItem to="/trends" icon={<TrendingUp size={20} />} label="趋势洞察" active={location.pathname === '/trends'} collapsed={sidebarCollapsed} />
          <div className="my-4 border-t border-white/5 mx-2"></div>
          <NavItem to="/settings" icon={<Settings size={20} />} label="系统设置" active={location.pathname === '/settings'} collapsed={sidebarCollapsed} />
        </nav>

        {/* Theme Toggle & User */}
        <div className="p-4 border-t border-white/5 bg-gradient-to-t from-slate-900/10 to-transparent overflow-hidden">
          
          <button 
            onClick={onToggleTheme}
            className="w-full flex items-center gap-3 p-2 mb-4 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 transition-colors group"
            style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
          >
             <div className={`p-1.5 rounded-md flex-shrink-0 ${theme === 'dark' ? 'bg-indigo-500 text-white' : 'text-slate-400'}`}>
                <Moon size={14} />
             </div>
             <div 
               className="flex items-center gap-3 overflow-hidden whitespace-nowrap"
               style={{
                 opacity: sidebarCollapsed ? 0 : 1,
                 width: sidebarCollapsed ? 0 : 'auto',
                 transition: 'opacity 0.25s ease, width 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
               }}
             >
               <div className={`p-1.5 rounded-md ${theme === 'light' ? 'bg-amber-400 text-white' : 'text-slate-400'}`}>
                  <Sun size={14} />
               </div>
               <span className="text-xs font-medium text-slate-400 group-hover:text-white">
                  {theme === 'dark' ? 'Presentation' : 'Workstation'}
               </span>
             </div>
          </button>

          <div className="flex items-center gap-3" style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start', paddingLeft: sidebarCollapsed ? 0 : '8px' }}>
            <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center border border-white/10 shadow-inner ring-1 ring-white/5 flex-shrink-0">
              <User size={16} className="text-slate-300" />
            </div>
            <div 
              className="overflow-hidden whitespace-nowrap"
              style={{
                opacity: sidebarCollapsed ? 0 : 1,
                width: sidebarCollapsed ? 0 : 'auto',
                transition: 'opacity 0.25s ease, width 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              <p className="text-sm font-bold text-slate-100">Admin User</p>
              <p className="text-xs text-neon-cyan font-mono">OPERATOR_LVL_5</p>
            </div>
          </div>
          
          {/* 收缩按钮 */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full mt-4 flex items-center justify-center gap-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-slate-400 hover:text-white group"
            style={{ transition: 'all 0.2s ease' }}
          >
            <div style={{ transform: sidebarCollapsed ? 'rotate(0deg)' : 'rotate(180deg)', transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)' }}>
              <ChevronRight size={16} />
            </div>
            <span 
              className="text-xs overflow-hidden whitespace-nowrap"
              style={{
                opacity: sidebarCollapsed ? 0 : 1,
                width: sidebarCollapsed ? 0 : 'auto',
                transition: 'opacity 0.25s ease, width 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              收起侧栏
            </span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        
        {/* Top Header */}
        <header className="h-20 bg-transparent flex items-center justify-between px-6 md:px-8 sticky top-0 z-30 backdrop-blur-sm">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">全渠道经营复盘看板</h1>
            <p className={`text-xs font-mono mt-0.5 opacity-70 flex items-center gap-1.5 ${isSystemHealthy ? 'text-slate-400' : 'text-amber-400'}`}>
              {isSystemHealthy ? (
                <CheckCircle size={10} className="text-emerald-400" />
              ) : (
                <AlertCircle size={10} className="text-amber-400" />
              )}
              SYSTEM: {getStatusText()}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* 全局筛选器 */}
            <GlobalFilter />
            
            {/* 系统状态指示器 */}
            <div className={`hidden sm:flex items-center gap-2 glass-panel px-4 py-1.5 rounded-full border text-xs shadow-lg ${
              isSystemHealthy 
                ? 'border-white/10 text-neon-cyan' 
                : 'border-amber-500/30 text-amber-400'
            }`}>
              <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${isSystemHealthy ? 'bg-neon-cyan' : 'bg-amber-400'}`}></div>
              <span className="font-mono">{isSystemHealthy ? 'LIVE_DATA' : 'OFFLINE'}</span>
            </div>
            
            <button className="relative p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-slate-300 hover:text-white transition-all hover:shadow-[0_0_15px_rgba(255,255,255,0.1)] group">
              <Bell size={20} className="group-hover:rotate-12 transition-transform" />
              <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-neon-rose rounded-full border-2 border-slate-900"></span>
            </button>
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-auto p-4 md:p-8 z-10 custom-scrollbar">
          <div className="w-full h-full flex flex-col gap-8 pb-10">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
};

const NavItem = ({ to, icon, label, active = false, collapsed = false }: { to: string, icon: ReactNode, label: string, active?: boolean, collapsed?: boolean }) => {
  // 意图预加载：鼠标悬停时预加载对应路由
  const handleMouseEnter = useCallback(() => {
    prefetchRoute(to);
  }, [to]);

  return (
    <Link 
      to={to} 
      className={`relative group w-full flex items-center gap-3 px-3 py-3 rounded-xl overflow-hidden ${
        active 
          ? 'text-white shadow-[0_0_20px_rgba(139,92,246,0.15)] bg-white/5' 
          : 'text-slate-400 hover:text-white'
      }`}
      style={{ justifyContent: collapsed ? 'center' : 'flex-start', transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)' }}
      title={collapsed ? label : undefined}
      onMouseEnter={handleMouseEnter}
    >
      {active && (
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-neon-purple rounded-full shadow-[0_0_10px_#a78bfa]"></div>
      )}
      {!active && (
          <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors"></div>
      )}
      <div className={`relative z-10 flex-shrink-0 transition-transform group-hover:scale-110 ${active ? 'text-neon-purple' : 'group-hover:text-slate-200'}`}>
          {icon}
      </div>
      <span 
        className="relative z-10 text-sm font-medium tracking-wide whitespace-nowrap overflow-hidden"
        style={{
          opacity: collapsed ? 0 : 1,
          width: collapsed ? 0 : 'auto',
          transition: 'opacity 0.25s ease, width 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      >
        {label}
      </span>
      
      {/* 收起状态下的悬浮提示 */}
      {collapsed && (
        <div className="absolute left-full ml-2 px-3 py-1.5 bg-slate-800 text-white text-xs font-medium rounded-lg shadow-xl border border-white/10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
          {label}
          <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45 border-l border-b border-white/10"></div>
        </div>
      )}
    </Link>
  );
};

export default Layout;
