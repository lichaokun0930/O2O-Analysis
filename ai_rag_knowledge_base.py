#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量知识库 + RAG增强 (阶段3优化)
支持历史案例检索和最佳实践注入

功能:
1. 向量知识库构建 (ChromaDB)
2. 相似案例检索
3. RAG增强AI分析
4. 知识库管理 (增删改查)

依赖安装:
pip install chromadb sentence-transformers
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

# 尝试导入向量库
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    print("✅ ChromaDB可用")
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB未安装,请运行: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    print("✅ SentenceTransformers可用")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ SentenceTransformers未安装,请运行: pip install sentence-transformers")
except OSError as e:
    # Torch DLL 加载失败（Windows 常见问题）
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    if "DLL" in str(e) or "1114" in str(e):
        print("⚠️ SentenceTransformers依赖的Torch DLL加载失败")
        print("   解决方案: 安装 Visual C++ Redistributable")
        print("   下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    else:
        print(f"⚠️ SentenceTransformers加载失败: {e}")

# 导入AI分析器
try:
    from ai_analyzer import AIAnalyzer
    from ai_business_context import get_base_prompt
    AI_ANALYZER_AVAILABLE = True
except ImportError:
    AI_ANALYZER_AVAILABLE = False
    print("⚠️ ai_analyzer模块未找到")


# ==================== 向量知识库 ====================

class VectorKnowledgeBase:
    """向量知识库 - 存储和检索历史案例"""
    
    def __init__(self, persist_directory: str = "./knowledge_db", 
                 collection_name: str = "o2o_cases"):
        """初始化知识库
        
        Args:
            persist_directory: 知识库存储目录
            collection_name: 集合名称
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("请先安装ChromaDB: pip install chromadb")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("请先安装SentenceTransformers: pip install sentence-transformers")
        
        # 初始化ChromaDB客户端
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # 创建或获取集合
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ 已加载知识库: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "O2O业务历史案例库"}
            )
            print(f"✅ 已创建知识库: {collection_name}")
        
        # 初始化embedding模型 (多语言支持)
        self.encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Embedding模型已加载")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
    
    def add_case(self, 
                 case_id: str,
                 problem_description: str,
                 solution: str,
                 result: str,
                 metrics: Optional[Dict] = None,
                 tags: Optional[List[str]] = None) -> str:
        """添加案例到知识库
        
        Args:
            case_id: 案例唯一ID
            problem_description: 问题描述
            solution: 解决方案
            result: 实施结果
            metrics: 量化指标 (可选)
            tags: 标签 (如"利润下滑"、"客单价提升"等)
        
        Returns:
            案例ID
        """
        # 生成embedding
        embedding = self.encoder.encode(problem_description).tolist()
        
        # 构建metadata
        metadata = {
            "solution": solution,
            "result": result,
            "created_at": datetime.now().isoformat(),
            "tags": ",".join(tags) if tags else ""
        }
        
        if metrics:
            metadata["metrics"] = json.dumps(metrics, ensure_ascii=False)
        
        # 添加到数据库
        self.collection.add(
            ids=[case_id],
            embeddings=[embedding],
            documents=[problem_description],
            metadatas=[metadata]
        )
        
        print(f"✅ 案例已添加: {case_id}")
        return case_id
    
    def search_similar_cases(self, 
                            problem_description: str, 
                            top_k: int = 3,
                            filter_tags: Optional[List[str]] = None) -> Tuple[List[str], List[Dict]]:
        """检索相似案例
        
        Args:
            problem_description: 当前问题描述
            top_k: 返回最相似的K个案例
            filter_tags: 标签过滤 (可选)
        
        Returns:
            (案例描述列表, metadata列表)
        """
        # 生成查询embedding
        query_embedding = self.encoder.encode(problem_description).tolist()
        
        # 构建过滤条件
        where_filter = None
        if filter_tags:
            where_filter = {"tags": {"$contains": filter_tags[0]}}
        
        # 查询
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        
        print(f"🔍 找到{len(documents)}个相似案例")
        return documents, metadatas
    
    def get_case_by_id(self, case_id: str) -> Optional[Dict]:
        """根据ID获取案例"""
        try:
            result = self.collection.get(ids=[case_id])
            if result['ids']:
                return {
                    "id": result['ids'][0],
                    "problem": result['documents'][0],
                    "metadata": result['metadatas'][0]
                }
            return None
        except:
            return None
    
    def delete_case(self, case_id: str):
        """删除案例"""
        self.collection.delete(ids=[case_id])
        print(f"✅ 案例已删除: {case_id}")
    
    def get_all_cases(self) -> List[Dict]:
        """获取所有案例"""
        result = self.collection.get()
        cases = []
        for i in range(len(result['ids'])):
            cases.append({
                "id": result['ids'][i],
                "problem": result['documents'][i],
                "metadata": result['metadatas'][i]
            })
        return cases
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        all_cases = self.get_all_cases()
        
        # 统计标签分布
        tag_counts = {}
        for case in all_cases:
            tags = case['metadata'].get('tags', '').split(',')
            for tag in tags:
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_cases": len(all_cases),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "tag_distribution": tag_counts
        }
    
    def export_to_json(self, filepath: str = "knowledge_base_export.json"):
        """导出知识库到JSON文件"""
        all_cases = self.get_all_cases()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_cases, f, ensure_ascii=False, indent=2)
        print(f"✅ 知识库已导出: {filepath}")
    
    def import_from_json(self, filepath: str):
        """从JSON文件导入案例"""
        with open(filepath, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        for case in cases:
            self.add_case(
                case_id=case['id'],
                problem_description=case['problem'],
                solution=case['metadata'].get('solution', ''),
                result=case['metadata'].get('result', ''),
                metrics=json.loads(case['metadata'].get('metrics', '{}')),
                tags=case['metadata'].get('tags', '').split(',')
            )
        
        print(f"✅ 已导入{len(cases)}个案例")


# ==================== RAG增强分析器 ====================

class RAGAnalyzer:
    """RAG增强AI分析器 - 结合历史案例的智能分析"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_type: str = 'glm',
                 knowledge_base: Optional[VectorKnowledgeBase] = None):
        """初始化RAG分析器
        
        Args:
            api_key: API密钥
            model_type: 模型类型
            knowledge_base: 知识库实例 (可选,如不提供则创建新实例)
        """
        if not AI_ANALYZER_AVAILABLE:
            raise ImportError("ai_analyzer模块未找到")
        
        # 初始化AI分析器
        self.analyzer = AIAnalyzer(api_key=api_key, model_type=model_type)
        
        # 初始化知识库
        if knowledge_base:
            self.kb = knowledge_base
        else:
            self.kb = VectorKnowledgeBase()
        
        print("✅ RAG分析器初始化完成")
    
    def analyze_with_rag(self, 
                        problem_description: str,
                        data_summary: Dict,
                        task_name: str = "问题诊断与优化",
                        top_k_cases: int = 3) -> str:
        """RAG增强分析
        
        Args:
            problem_description: 问题描述
            data_summary: 数据摘要
            task_name: 任务名称
            top_k_cases: 检索案例数量
        
        Returns:
            分析报告
        """
        # 1. 检索相似案例
        print(f"🔍 正在检索相似案例...")
        similar_problems, metadatas = self.kb.search_similar_cases(
            problem_description, 
            top_k=top_k_cases
        )
        
        # 2. 构建RAG增强Prompt
        base_prompt = get_base_prompt()
        
        # 格式化相似案例
        cases_text = ""
        for i, (problem, meta) in enumerate(zip(similar_problems, metadatas)):
            cases_text += f"""
【案例{i+1}】
问题描述: {problem}
解决方案: {meta.get('solution', '无')}
实施结果: {meta.get('result', '无')}
标签: {meta.get('tags', '无')}
---
"""
        
        # 格式化数据摘要
        if isinstance(data_summary, dict):
            data_str = "\n".join([f"- {k}: {v}" for k, v in data_summary.items()])
        else:
            data_str = str(data_summary)
        
        # 构建完整Prompt
        rag_prompt = f"""{base_prompt}

【历史成功案例参考】
以下是从知识库中检索到的{len(similar_problems)}个相似案例,供参考:

{cases_text}

【当前问题】
{problem_description}

【当前数据概览】
{data_str}

【分析任务】
{task_name}

【输出要求】
请参考历史案例,但不要生搬硬套。根据当前实际数据,提供:
1. 数据验证 (确认数据计算正确性)
2. 问题定位 (核心矛盾是什么)
3. 归因分析 (根本原因是什么)
4. 解决方案 (3-5个具体可执行方案,按ROI排序)
5. 效果预估 (量化收益)
6. 执行建议 (P0/P1/P2优先级)
7. 风险提示 (潜在风险和注意事项)

特别注意:
- 历史案例仅供参考,当前问题可能有独特性
- 所有建议必须基于当前实际数据
- 优先级排序基于ROI,不是案例顺序
- 必须量化预期效果
"""
        
        # 3. 调用AI生成分析
        print(f"🤖 正在生成RAG增强分析...")
        analysis = self.analyzer._generate_content(rag_prompt)
        
        return analysis
    
    def analyze_and_save_case(self,
                             problem_description: str,
                             data_summary: Dict,
                             case_id: Optional[str] = None,
                             save_to_kb: bool = False) -> Dict:
        """分析问题并可选择性保存为案例
        
        Args:
            problem_description: 问题描述
            data_summary: 数据摘要
            case_id: 案例ID (可选,默认自动生成)
            save_to_kb: 是否保存到知识库 (需要人工验证后再保存)
        
        Returns:
            包含analysis和case_info的字典
        """
        # 执行RAG分析
        analysis = self.analyze_with_rag(problem_description, data_summary)
        
        # 准备案例信息
        case_info = {
            "id": case_id or f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "problem": problem_description,
            "data_summary": data_summary,
            "analysis": analysis,
            "created_at": datetime.now().isoformat()
        }
        
        if save_to_kb:
            # 注意: 实际使用时应该在验证效果后再保存
            print("⚠️ 建议先验证效果,再手动调用save_case()保存")
        
        return {
            "analysis": analysis,
            "case_info": case_info
        }
    
    def save_case(self, case_id: str, problem: str, solution: str, 
                  result: str, metrics: Dict, tags: List[str]):
        """保存验证成功的案例到知识库"""
        self.kb.add_case(
            case_id=case_id,
            problem_description=problem,
            solution=solution,
            result=result,
            metrics=metrics,
            tags=tags
        )
        print(f"✅ 案例已保存到知识库: {case_id}")


# ==================== 知识库预填充 ====================

def init_default_knowledge_base(kb: VectorKnowledgeBase):
    """初始化默认知识库 (预填充典型案例)"""
    
    # 案例1: 利润下滑
    kb.add_case(
        case_id="case_profit_decline_001",
        problem_description="""
门店利润率从12%急剧下滑至6.5%,GMV微增5%(950K→1000K)。
详细数据:商品成本占比从62%升至68%,履约成本从10%升至14%,营销成本从6%升至11%。
初步判断是成本侧问题,但不清楚哪个环节失控最严重。
""",
        solution="""
方案1: 控制流量品占比 (立即执行)
- 停止单品流量品促销,改为组合销售(流量品+利润品)
- 流量品占比从45%降至30%
- 预期: 商品成本降至62%(-6%), 利润率提升+3.5%

方案2: 砍掉亏损营销活动 (当天执行)
- 停止ROI<1的活动(占营销费用40%)
- 营销成本从11%降至6.6%(-4.4%)
- 预期: 利润率提升+4.4%

方案3: 提高起送金额 (1周AB测试)
- 从29元提升至39元
- 客单价提升+15%, 履约成本降至11%(-3%)
- 预期: 利润率提升+2.5%
""",
        result="""
实施3周后:
- 利润率从6.5%恢复至10.8%(提升+4.3%)
- 商品成本占比降至63%
- 履约成本降至11.5%
- 营销成本降至7%
- GMV略降3%(可接受,利润优先)

ROI: 4.2 (投入1元成本优化,带来4.2元利润提升)
""",
        metrics={
            "利润率_前": 6.5,
            "利润率_后": 10.8,
            "提升幅度": 4.3,
            "ROI": 4.2,
            "执行周期_天": 21
        },
        tags=["利润下滑", "成本优化", "高ROI"]
    )
    
    # 案例2: 客单价提升
    kb.add_case(
        case_id="case_customer_value_001",
        problem_description="""
客单价停滞在25元,目标提升至35元(+40%)。
现状:利润品占比仅28%(健康值>40%),平均1.2件商品/订单,关联推荐缺失。
用户主要购买单件流量品,利润品曝光不足。
""",
        solution="""
方案1: 设置满减阶梯 (ROI: 6.5)
- 满49减5 (拉动10%用户凑单)
- 满99减15 (拉动5%用户大额购买)
- 预期: 客单价+35%, 利润品占比+12%

方案2: 首页推荐利润品组合 (ROI: 5.8)
- 上架洗护套装、零食组合、应季礼盒
- 组合价优惠5-8%
- 预期: 客单价+20%, 利润品占比+8%

方案3: 购物车关联推荐 (ROI: 4.2)
- 买牛奶推荐面包、买洗发水推荐护发素
- 算法优先推荐高毛利商品
- 预期: 客单价+15%, 利润品占比+6%
""",
        result="""
实施2个月后:
- 客单价从25元提升至38元(+52%)
- 利润品占比从28%提升至45%(+17%)
- 订单利润从4.2元提升至9.5元(+126%)
- 复购率从45%提升至58%

综合ROI: 5.1
""",
        metrics={
            "客单价_前": 25,
            "客单价_后": 38,
            "提升幅度_%": 52,
            "利润品占比_前": 28,
            "利润品占比_后": 45,
            "ROI": 5.1
        },
        tags=["客单价提升", "利润品推广", "关联销售"]
    )
    
    # 案例3: 商品结构优化
    kb.add_case(
        case_id="case_product_structure_001",
        problem_description="""
商品结构失衡严重:流量品占比45%(健康值<30%),利润品占比28%(健康值>40%),滞销品9%。
平均毛利率仅22%,低于行业30%的水平。
过度依赖低价引流,盈利能力弱。
""",
        solution="""
方案1: 淘汰滞销低毛利品 (ROI: 8.0)
- 清退9%滞销品(约540个SKU)
- 释放库存资金和运营精力
- 预期: 平均毛利率+3%

方案2: 引入高毛利差异化商品 (ROI: 6.2)
- 增加300个利润品SKU
- 利润品占比提升至42%
- 预期: 平均毛利率+6%, 整体利润率+4%

方案3: 降低流量品曝光权重 (ROI: 5.5)
- 首页流量品占比从60%降至30%
- 搜索排序提升利润品权重
- 预期: 流量品占比降至32%, 平均毛利率+4%
""",
        result="""
实施2个月后:
- 平均毛利率从22%提升至35%(+13%)
- 整体利润率从8%提升至15%(+7%)
- 商品结构: 流量30%|利润45%|形象25% (达到健康比例)
- SKU精简10%,但销售额不降反升

投入产出比: 6.8
""",
        metrics={
            "毛利率_前": 22,
            "毛利率_后": 35,
            "利润率_前": 8,
            "利润率_后": 15,
            "ROI": 6.8
        },
        tags=["商品结构", "SKU优化", "毛利率提升"]
    )
    
    # 案例4: 营销ROI优化
    kb.add_case(
        case_id="case_marketing_roi_001",
        problem_description="""
营销成本占比11%(健康值<8%),存在严重烧钱问题。
20个营销活动中,8个ROI<1(亏损),平均ROI仅1.8。
折扣力度过大(最高满100减50),吸引了大量薅羊毛用户。
""",
        solution="""
方案1: 立即停止亏损活动 (ROI: 10.0)
- 停止8个ROI<1的活动
- 营销成本从11%降至6.5%(-4.5%)
- 预期: 利润率立即提升+4.5%

方案2: 优化折扣阶梯 (ROI: 4.5)
- 取消满100减50,改为满99减15
- 提高凑单门槛,引导多买利润品
- 预期: 营销成本降至5%, 利润品占比+10%

方案3: 精准营销 (ROI: 3.8)
- 高价值用户: 小额券(满减5-10元)
- 薅羊毛用户: 不再推送大额券
- 新用户: 首单优惠券(拉新)
- 预期: 营销ROI从1.8提升至3.5
""",
        result="""
实施1个月后:
- 营销成本从11%降至5.5%(-5.5%)
- 平均营销ROI从1.8提升至4.2
- 利润率从7%提升至12.5%(+5.5%)
- 高价值用户留存率提升15%

综合ROI: 6.2
""",
        metrics={
            "营销成本占比_前": 11,
            "营销成本占比_后": 5.5,
            "营销ROI_前": 1.8,
            "营销ROI_后": 4.2,
            "利润率提升": 5.5,
            "ROI": 6.2
        },
        tags=["营销优化", "ROI提升", "精准营销"]
    )
    
    # 案例5: 时段场景优化
    kb.add_case(
        case_id="case_period_scenario_001",
        problem_description="""
24小时营业模式下,深夜和凌晨时段(22:00-07:00)订单量占15%,但利润率仅2%。
履约成本在深夜时段高达18%(白天11%),存在亏损风险。
需要评估深夜营业的必要性。
""",
        solution="""
方案1: 深夜提高起送金额 (ROI: 5.2)
- 22:00-07:00起送金额从29元提至49元
- 客单价提升+30%, 履约成本降至13%
- 预期: 深夜时段利润率从2%提升至8%

方案2: 场景化商品推荐 (ROI: 4.8)
- 深夜主推高毛利应急商品(药品、应急食品)
- 凌晨主推早餐组合(牛奶+面包+鸡蛋)
- 预期: 毛利率+8%, 客单价+20%

方案3: 差异化定价 (ROI: 4.0)
- 深夜商品加价10-15%(应急溢价)
- 白天恢复正常价格
- 预期: 利润率提升+5%
""",
        result="""
实施1个月后:
- 深夜时段利润率从2%提升至9.5%(+7.5%)
- 深夜订单量下降20%(高客单价订单为主)
- 整体利润率提升+1.2%
- 深夜人力成本优化15%

投入产出比: 4.6
""",
        metrics={
            "深夜利润率_前": 2,
            "深夜利润率_后": 9.5,
            "整体利润率提升": 1.2,
            "ROI": 4.6
        },
        tags=["时段优化", "场景营销", "差异化定价"]
    )
    
    print(f"✅ 已预填充5个典型案例")


# ==================== 单元测试 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("向量知识库 + RAG增强测试")
    print("=" * 80)
    
    if not (CHROMADB_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE):
        print("⚠️ 缺少依赖,请安装:")
        print("   pip install chromadb sentence-transformers")
        exit(1)
    
    # 测试1: 创建知识库
    print("\n【测试1: 创建知识库】")
    kb = VectorKnowledgeBase(persist_directory="./test_knowledge_db")
    
    # 测试2: 预填充案例
    print("\n【测试2: 预填充案例】")
    init_default_knowledge_base(kb)
    
    # 测试3: 查看统计
    print("\n【测试3: 知识库统计】")
    stats = kb.get_stats()
    print(f"总案例数: {stats['total_cases']}")
    print(f"标签分布: {stats['tag_distribution']}")
    
    # 测试4: 检索相似案例
    print("\n【测试4: 检索相似案例】")
    test_problem = "我的门店利润率从10%降到了5%,主要是成本上升导致的,不知道该怎么办"
    problems, metas = kb.search_similar_cases(test_problem, top_k=2)
    
    print(f"\n查询: {test_problem}")
    print(f"\n找到{len(problems)}个相似案例:")
    for i, (prob, meta) in enumerate(zip(problems, metas)):
        print(f"\n案例{i+1}:")
        print(f"问题: {prob[:100]}...")
        print(f"标签: {meta.get('tags', '无')}")
        print(f"结果: {meta.get('result', '无')[:100]}...")
    
    # 测试5: 导出知识库
    print("\n【测试5: 导出知识库】")
    kb.export_to_json("test_kb_export.json")
    
    # 测试6: RAG分析 (需要API密钥)
    print("\n【测试6: RAG增强分析】")
    api_key = os.getenv('ZHIPU_API_KEY')
    if api_key and AI_ANALYZER_AVAILABLE:
        try:
            rag_analyzer = RAGAnalyzer(api_key=api_key, knowledge_base=kb)
            
            test_data = {
                "当前利润率": "5.2%",
                "历史利润率": "10.5%",
                "商品成本占比": "69%",
                "履约成本占比": "13%",
                "营销成本占比": "9%"
            }
            
            print(f"\n🔍 测试问题: {test_problem}")
            print(f"📊 测试数据: {test_data}")
            # result = rag_analyzer.analyze_with_rag(test_problem, test_data)
            # print(f"\n分析结果:\n{result}")
            print("(实际分析已注释,避免消耗API额度)")
            
        except Exception as e:
            print(f"⚠️ RAG测试跳过: {e}")
    else:
        print("⚠️ 未找到ZHIPU_API_KEY或ai_analyzer模块")
    
    print("\n✅ 测试完成!")
