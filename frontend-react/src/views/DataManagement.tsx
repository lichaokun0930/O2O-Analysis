/**
 * 数据管理页面 - 重新设计版本
 * 单页面卡片式布局，以用户任务为中心
 */
import React, { useState } from 'react';
import { 
  Database, Upload, Trash2, RefreshCw, HardDrive, Settings,
  FileSpreadsheet, X, ChevronDown, ChevronRight, CheckCircle,
  AlertCircle, AlertTriangle, ExternalLink, Search
} from 'lucide-react';
import { useGlobalContext } from '../store/GlobalContext';
import { dataApi } from '../api/data';
import { useNavigate } from 'react-router-dom';

const formatNumber = (num: number | undefined) => {
  if (num === undefined || num === null) return '0';
  return num.toLocaleString();
};

const DataManagement: React.FC = () => {
  const navigate = useNavigate();
  const { stats, statsLoading, systemStatus, stores, refreshAll, refreshStats } = useGlobalContext();
  
  // 上传状态
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<string[]>([]);
  
  // 门店管理状态
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingStore, setDeletingStore] = useState<string | null>(null);
  const [deleteModalStore, setDeleteModalStore] = useState<{ value: string; label: string } | null>(null);
  
  // 系统维护状态
  const [showMaintenance, setShowMaintenance] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [clearingCache, setClearingCache] = useState(false);

  // 文件处理
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    setFiles(prev => [...prev, ...selectedFiles].slice(0, 5));
    setUploadResults([]);
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      f => f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
    );
    setFiles(prev => [...prev, ...droppedFiles].slice(0, 5));
    setUploadResults([]);
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setUploadResults([]);
    const results: string[] = [];
    let successCount = 0;
    
    for (const file of files) {
      try {
        const res = await dataApi.uploadOrders(file, { mode: 'replace' });
        if (res.success) {
          successCount++;
          results.push(`✅ ${file.name}: 成功导入 ${res.rows_inserted} 条数据`);
        } else {
          results.push(`❌ ${file.name}: 上传失败`);
        }
      } catch (error: any) {
        results.push(`❌ ${file.name}: ${error.message || '上传失败'}`);
      }
    }
    
    setUploadResults(results);
    setUploading(false);
    
    if (successCount > 0) {
      setFiles([]);
      refreshAll();
    }
  };

  // 删除门店
  const handleDeleteStore = async (storeName: string) => {
    setDeletingStore(storeName);
    try {
      const res = await dataApi.deleteStoreData(storeName);
      if (res.success) {
        setDeleteModalStore(null);
        refreshAll();
      }
    } catch (error) {
      alert('删除失败');
    } finally {
      setDeletingStore(null);
    }
  };

  // 清除缓存
  const handleClearCache = async () => {
    setClearingCache(true);
    try {
      await dataApi.clearCache();
      alert('缓存已清除');
    } catch (error) {
      alert('清除失败');
    } finally {
      setClearingCache(false);
    }
  };

  // 优化数据库
  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await dataApi.optimizeDatabase();
      alert(res.message || '优化完成');
    } catch (error) {
      alert('优化失败');
    } finally {
      setOptimizing(false);
    }
  };

  // 过滤门店
  const filteredStores = stores.filter(store => 
    store.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // 系统状态
  const isDbConnected = systemStatus.database === 'connected';
  const isRedisConnected = systemStatus.redis === 'connected';


  return (
    <div className="flex flex-col gap-6 w-full">
      {/* 删除确认对话框 */}
      {deleteModalStore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 w-[400px] shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-rose-500/20 flex items-center justify-center">
                <AlertTriangle size={20} className="text-rose-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold">确认删除</h3>
                <p className="text-slate-400 text-sm">此操作不可撤销</p>
              </div>
            </div>
            <p className="text-slate-300 mb-6">
              确定要删除门店 <span className="text-rose-400 font-medium">"{deleteModalStore.label}"</span> 的所有数据吗？
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteModalStore(null)}
                className="flex-1 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleDeleteStore(deleteModalStore.value)}
                disabled={deletingStore === deleteModalStore.value}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-500 hover:bg-rose-600 disabled:bg-rose-500/50 text-white rounded-lg font-medium transition-colors"
              >
                {deletingStore === deleteModalStore.value ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    删除中...
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    确认删除
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 页面标题 + 系统状态 */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Database size={24} className="text-indigo-400" />
            数据管理中心
          </h2>
          <p className="text-slate-400 text-xs mt-1 font-mono">DATA MANAGEMENT CENTER</p>
        </div>
        
        {/* 连接状态卡片 */}
        <div className="flex gap-3">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${
            isDbConnected 
              ? 'bg-emerald-500/10 border-emerald-500/30' 
              : 'bg-rose-500/10 border-rose-500/30'
          }`}>
            {isDbConnected ? (
              <CheckCircle size={16} className="text-emerald-400" />
            ) : (
              <AlertCircle size={16} className="text-rose-400" />
            )}
            <span className={`text-sm font-medium ${isDbConnected ? 'text-emerald-300' : 'text-rose-300'}`}>
              PostgreSQL {isDbConnected ? '已连接' : '未连接'}
            </span>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${
            isRedisConnected 
              ? 'bg-emerald-500/10 border-emerald-500/30' 
              : 'bg-amber-500/10 border-amber-500/30'
          }`}>
            {isRedisConnected ? (
              <CheckCircle size={16} className="text-emerald-400" />
            ) : (
              <AlertTriangle size={16} className="text-amber-400" />
            )}
            <span className={`text-sm font-medium ${isRedisConnected ? 'text-emerald-300' : 'text-amber-300'}`}>
              Redis {isRedisConnected ? '已连接' : '未连接'}
            </span>
          </div>
        </div>
      </div>

      {/* 数据库未连接警告 */}
      {!isDbConnected && (
        <div className="flex items-center gap-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl">
          <AlertCircle size={24} className="text-rose-400 flex-shrink-0" />
          <div className="flex-1">
            <div className="text-rose-300 font-medium">数据库连接失败</div>
            <div className="text-rose-400/70 text-sm mt-1">
              请检查 PostgreSQL 服务是否启动，或联系管理员。数据管理功能暂时不可用。
            </div>
          </div>
          <button 
            onClick={() => refreshStats()}
            className="px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 rounded-lg text-sm font-medium transition-colors"
          >
            重试连接
          </button>
        </div>
      )}

      {/* 数据总览 */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            📊 数据总览
          </h3>
          <button 
            onClick={() => refreshAll()}
            disabled={statsLoading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw size={14} className={statsLoading ? 'animate-spin' : ''} />
            刷新
          </button>
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          {[
            { icon: '📦', label: '订单总数', value: formatNumber(stats?.total_orders), color: 'text-indigo-400' },
            { icon: '🏪', label: '门店数量', value: stats?.total_stores || 0, color: 'text-emerald-400' },
            { icon: '🛒', label: '商品种类', value: formatNumber(stats?.total_products), color: 'text-amber-400' },
            { icon: '📅', label: '数据新鲜度', value: stats?.data_freshness || '-', color: 'text-cyan-400' },
          ].map(({ icon, label, value, color }) => (
            <div key={label} className="bg-slate-800/50 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <div>
                  <div className={`text-xl font-bold ${color}`}>{value}</div>
                  <div className="text-sm text-slate-500">{label}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 两列布局：导入数据 + 门店管理 */}
      <div className="grid grid-cols-2 gap-6">
        {/* 导入数据 */}
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
            <Upload size={20} className="text-indigo-400" />
            导入数据
          </h3>
          
          {/* 上传区域 */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className="border-2 border-dashed border-white/20 hover:border-indigo-500/50 rounded-xl p-8 text-center transition-all cursor-pointer group"
          >
            <FileSpreadsheet size={40} className="mx-auto mb-3 text-slate-500 group-hover:text-indigo-400 transition-colors" />
            <div className="text-white font-medium mb-1">拖拽 Excel 文件到这里</div>
            <div className="text-slate-500 text-sm mb-4">支持 .xlsx / .xls 格式</div>
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              disabled={!isDbConnected}
            />
            <label
              htmlFor="file-upload"
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                isDbConnected 
                  ? 'bg-indigo-500 hover:bg-indigo-600 text-white' 
                  : 'bg-slate-700 text-slate-500 cursor-not-allowed'
              }`}
            >
              <Upload size={16} />
              选择文件
            </label>
          </div>

          {/* 已选文件 */}
          {files.length > 0 && (
            <div className="mt-4 space-y-2">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet size={18} className="text-emerald-400" />
                    <span className="text-white text-sm">{file.name}</span>
                    <span className="text-slate-500 text-xs">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button onClick={() => removeFile(index)} className="text-slate-500 hover:text-rose-400">
                    <X size={16} />
                  </button>
                </div>
              ))}
              <div className="flex gap-3 mt-3">
                <button
                  onClick={handleUpload}
                  disabled={uploading || !isDbConnected}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 disabled:bg-indigo-500/50 text-white rounded-lg font-medium transition-all"
                >
                  {uploading ? <RefreshCw size={16} className="animate-spin" /> : <Upload size={16} />}
                  {uploading ? '上传中...' : `上传 ${files.length} 个文件`}
                </button>
                <button
                  onClick={() => setFiles([])}
                  className="px-4 py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg"
                >
                  清空
                </button>
              </div>
            </div>
          )}

          {/* 上传结果 */}
          {uploadResults.length > 0 && (
            <div className="mt-4 p-4 bg-slate-800/50 rounded-xl space-y-1">
              {uploadResults.map((result, index) => (
                <div key={index} className={`text-sm ${result.startsWith('✅') ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {result}
                </div>
              ))}
              {uploadResults.some(r => r.startsWith('✅')) && (
                <button
                  onClick={() => navigate('/')}
                  className="mt-3 flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm"
                >
                  前往看板查看 <ExternalLink size={14} />
                </button>
              )}
            </div>
          )}
        </div>


        {/* 门店管理 */}
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
            🏪 门店数据
          </h3>
          
          {/* 搜索框 */}
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg mb-4">
            <Search size={16} className="text-slate-500" />
            <input
              type="text"
              placeholder="搜索门店..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 bg-transparent text-white text-sm placeholder-slate-500 outline-none"
            />
          </div>

          {/* 门店列表 */}
          <div className="space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
            {filteredStores.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                {searchTerm ? '未找到匹配的门店' : '暂无门店数据'}
              </div>
            ) : (
              filteredStores.map(store => (
                <div key={store.value} className="bg-slate-800/50 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">{store.label}</div>
                      <div className="text-slate-500 text-sm mt-1">
                        {formatNumber(store.order_count)} 条订单
                      </div>
                    </div>
                    
                    {deletingStore === store.value ? (
                      <RefreshCw size={16} className="text-slate-400 animate-spin" />
                    ) : (
                      <button
                        onClick={() => setDeleteModalStore({ value: store.value, label: store.label })}
                        disabled={!isDbConnected}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <Trash2 size={14} />
                        删除
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 系统维护（可折叠） */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
        <button
          onClick={() => setShowMaintenance(!showMaintenance)}
          className="w-full flex items-center justify-between p-5 text-left"
        >
          <div className="flex items-center gap-3">
            <Settings size={20} className="text-slate-400" />
            <span className="text-white font-medium">系统维护</span>
            <span className="text-slate-500 text-sm">缓存管理、数据库优化</span>
          </div>
          {showMaintenance ? (
            <ChevronDown size={20} className="text-slate-400" />
          ) : (
            <ChevronRight size={20} className="text-slate-400" />
          )}
        </button>
        
        {showMaintenance && (
          <div className="px-5 pb-5 border-t border-white/5 pt-4">
            <div className="grid grid-cols-2 gap-4">
              {/* 缓存管理 */}
              <div className="bg-slate-800/30 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white font-medium mb-3">
                  <HardDrive size={16} className="text-amber-400" />
                  缓存管理
                </div>
                <p className="text-slate-500 text-sm mb-4">
                  清除系统缓存，解决数据不一致问题
                </p>
                <button
                  onClick={handleClearCache}
                  disabled={clearingCache}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {clearingCache ? <RefreshCw size={14} className="animate-spin" /> : <Trash2 size={14} />}
                  {clearingCache ? '清除中...' : '清除全部缓存'}
                </button>
              </div>

              {/* 数据库优化 */}
              <div className="bg-slate-800/30 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white font-medium mb-3">
                  <Database size={16} className="text-emerald-400" />
                  数据库优化
                </div>
                <p className="text-slate-500 text-sm mb-4">
                  清理碎片、重建索引，提升查询性能
                </p>
                <button
                  onClick={handleOptimize}
                  disabled={optimizing || !isDbConnected}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {optimizing ? <RefreshCw size={14} className="animate-spin" /> : <Settings size={14} />}
                  {optimizing ? '优化中...' : '优化数据库'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataManagement;
