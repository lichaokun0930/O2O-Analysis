/**
 * 全局门店洞察分析面板
 * 
 * 功能：
 * - 展示全量门店的统计分析报告
 * - 包含整体概况、门店分群、异常检测、头尾对比、归因分析、趋势分析、策略建议
 * - 支持折叠/展开各分析模块
 * - 关键数据高亮显示
 */
import React, { useEffect, useState, useCallback } from 'react';
import { 
  Brain, ChevronDown, ChevronRight, RefreshCw, 
  BarChart3, Users, AlertTriangle, GitCompare, 
  TrendingUp, Lightbulb, Activity
} from 'lucide-react';
import { storeComparisonApi } from '../api/storeComparison';
import type { GlobalInsightsData } from '../types';

interface GlobalInsightsPanelProps {
  startDate: string;
  endDate: string;
  channel?: string;
  theme?: 'dark' | 'light';
}

const GlobalInsightsPanel: React.FC<GlobalInsightsPanelProps> = ({
  startDate,
  endDate,
  channel,
  theme = 'dark'
}) => {
  const [insights, setInsights] = useState<GlobalInsightsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['overview', 'anomalies', 'recommendations'])
  );

  // 加载洞察数据
  const loadInsights = useCallback(async () => {
    if (!startDate || !endDate) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await storeComparisonApi.getGlobalInsights({
        start_date: startDate,
        end_date: endDate,
        channel: channel === 'all' ? undefined : channel,
        include_trends: true
      });
      
      if (res.success && res.data) {
        setInsights(res.data);
      } else {
        setError(res.message || '获取洞察数据失败');
      }
    } catch (err) {
      console.error('获取洞察数据失败:', err);
      setError('获取洞察数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, channel]);

  useEffect(() => {
    loadInsights();
  }, [loadInsights]);

  // 切换折叠状态
  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  // 高亮文本中的关键数据
  const highlightText = (text: string) => {
    return text
      .replace(/(\d+\.?\d*%)/g, '<span class="text-cyan-400 font-semibold">$1</span>')
      .replace(/(¥[\d,]+\.?\d*)/g, '<span class="text-emerald-400 font-semibold">$1</span>')
      .replace(/(\d{1,3}(,\d{3})*(\.\d+)?(?=\s*(家|笔|个|条)))/g, '<span class="text-amber-400 font-semibold">$1</span>');
  };

  // 可折叠区块组件
  const CollapsibleSection: React.FC<{
    id: string;
    title: string;
    icon: React.ReactNode;
    iconColor: string;
    children: React.ReactNode;
  }> = ({ id, title, icon, iconColor, children }) => {
    const isExpanded = expandedSections.has(id);
    
    return (
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection(id)}
          className="w-full flex items-center justify-between p-4 bg-slate-800/50 hover:bg-slate-800 transition-colors"
        >
          <div className="flex items-center gap-3">
            <span className={iconColor}>{icon}</span>
            <span className="font-medium text-white">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronDown size={20} className="text-slate-400" />
          ) : (
            <ChevronRight size={20} className="text-slate-400" />
          )}
        </button>
        {isExpanded && (
          <div className="p-4 bg-slate-900/30">
            {children}
          </div>
        )}
      </div>
    );
  };

  // 报告文本组件
  const ReportText: React.FC<{ text: string }> = ({ text }) => (
    <div 
      className="text-slate-300 leading-relaxed whitespace-pre-line text-sm"
      dangerouslySetInnerHTML={{ __html: highlightText(text) }}
    />
  );

  // 加载状态
  if (loading) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-center gap-3 py-12">
          <RefreshCw size={24} className="text-purple-400 animate-spin" />
          <span className="text-slate-400">正在生成洞察分析报告...</span>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-center gap-3 py-12 text-red-400">
          <AlertTriangle size={24} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  // 无数据状态
  if (!insights) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-center gap-3 py-12 text-slate-400">
          <Brain size={24} />
          <span>暂无洞察数据</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Brain size={24} className="text-purple-400" />
          全局门店洞察分析
        </h2>
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-500">
            生成时间: {insights.generated_at}
          </span>
          <button
            onClick={loadInsights}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 
                       text-purple-400 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            刷新
          </button>
        </div>
      </div>

      {/* 分析模块 */}
      <div className="space-y-4">
        {/* 整体概况 */}
        <CollapsibleSection
          id="overview"
          title="整体概况"
          icon={<BarChart3 size={18} />}
          iconColor="text-blue-400"
        >
          <ReportText text={insights.overview.summary_text} />
        </CollapsibleSection>

        {/* 门店分群 */}
        <CollapsibleSection
          id="clustering"
          title="门店分群"
          icon={<Users size={18} />}
          iconColor="text-green-400"
        >
          <ReportText text={insights.clustering.summary_text} />
        </CollapsibleSection>

        {/* 异常检测 */}
        <CollapsibleSection
          id="anomalies"
          title={`异常检测 (${insights.anomalies.total_anomaly_stores}家)`}
          icon={<AlertTriangle size={18} />}
          iconColor={insights.anomalies.total_anomaly_stores > 0 ? "text-amber-400" : "text-emerald-400"}
        >
          <ReportText text={insights.anomalies.summary_text} />
        </CollapsibleSection>

        {/* 头尾对比 */}
        <CollapsibleSection
          id="comparison"
          title="头尾对比"
          icon={<GitCompare size={18} />}
          iconColor="text-indigo-400"
        >
          <ReportText text={insights.head_tail_comparison.summary_text} />
        </CollapsibleSection>

        {/* 归因分析 */}
        <CollapsibleSection
          id="attribution"
          title="归因分析"
          icon={<Activity size={18} />}
          iconColor="text-pink-400"
        >
          <ReportText text={insights.attribution.summary_text} />
        </CollapsibleSection>

        {/* 趋势分析 */}
        <CollapsibleSection
          id="trends"
          title="趋势分析"
          icon={<TrendingUp size={18} />}
          iconColor="text-cyan-400"
        >
          <ReportText text={insights.trends.summary_text} />
        </CollapsibleSection>

        {/* 健康度评分 */}
        {insights.health_scores && (
          <CollapsibleSection
            id="health"
            title={`健康度评分 (平均${insights.health_scores.avg_score}分)`}
            icon={<Activity size={18} />}
            iconColor="text-emerald-400"
          >
            <ReportText text={insights.health_scores.summary_text} />
          </CollapsibleSection>
        )}

        {/* 成本结构分析 */}
        {insights.cost_structure && (
          <CollapsibleSection
            id="cost"
            title="成本结构分析"
            icon={<BarChart3 size={18} />}
            iconColor="text-orange-400"
          >
            <ReportText text={insights.cost_structure.summary_text} />
          </CollapsibleSection>
        )}

        {/* 策略建议 */}
        <CollapsibleSection
          id="recommendations"
          title={`策略建议 (${insights.recommendations.urgent.length + insights.recommendations.important.length + insights.recommendations.general.length}条)`}
          icon={<Lightbulb size={18} />}
          iconColor="text-yellow-400"
        >
          <ReportText text={insights.recommendations.summary_text} />
          
          {/* 详细建议列表 */}
          {insights.recommendations.urgent.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium text-red-400">🔴 紧急建议</h4>
              {insights.recommendations.urgent.map((rec, idx) => (
                <div key={idx} className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                  <div className="font-medium text-white text-sm">{rec.title}</div>
                  <div className="text-slate-400 text-xs mt-1">{rec.description}</div>
                  {rec.action_items.length > 0 && (
                    <ul className="mt-2 text-xs text-slate-300 list-disc list-inside">
                      {rec.action_items.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  )}
                  {rec.affected_stores.length > 0 && (
                    <div className="mt-2 text-xs text-slate-500">
                      涉及门店: {rec.affected_stores.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {insights.recommendations.important.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium text-amber-400">🟠 重要建议</h4>
              {insights.recommendations.important.map((rec, idx) => (
                <div key={idx} className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                  <div className="font-medium text-white text-sm">{rec.title}</div>
                  <div className="text-slate-400 text-xs mt-1">{rec.description}</div>
                  {rec.action_items.length > 0 && (
                    <ul className="mt-2 text-xs text-slate-300 list-disc list-inside">
                      {rec.action_items.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}
        </CollapsibleSection>
      </div>
    </div>
  );
};

export default GlobalInsightsPanel;
