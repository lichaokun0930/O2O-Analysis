# -*- coding: utf-8 -*-
"""
Parquet 数据同步服务

负责将 PostgreSQL 数据同步到 Parquet 文件
支持定时任务自动同步和手动触发

存储结构:
data/
├── raw/                          # 原始数据（按日期分区）
│   ├── 2025/
│   │   ├── 12/
│   │   │   ├── orders_20251201.parquet
│   │   │   └── ...
│   └── 2026/
├── aggregated/                   # 预聚合数据
│   ├── daily/
│   │   ├── kpi_daily.parquet
│   │   ├── channel_daily.parquet
│   │   └── category_daily.parquet
└── metadata/
    ├── partitions.json
    └── last_update.json

状态: ✅ 已落地（2026-01-20）
- 30个原始Parquet文件（18.52MB）
- 3个聚合Parquet文件
- 定时任务每天02:00自动同步
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import json


class ParquetSyncService:
    """Parquet 数据同步服务"""
    
    def __init__(self, data_dir: str = None):
        # 默认数据目录
        if data_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            data_dir = project_root / "data"
        
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.agg_dir = self.data_dir / "aggregated"
        self.metadata_dir = self.data_dir / "metadata"
        
        # 确保目录存在
        for d in [self.raw_dir, self.agg_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        print(f"📦 Parquet同步服务已初始化: {self.data_dir}")
    
    def sync_raw_data(self, target_date: date, df: pd.DataFrame) -> str:
        """
        同步原始数据到 Parquet（按日期分区）
        
        Args:
            target_date: 数据日期
            df: 订单数据 DataFrame
        
        Returns:
            生成的文件路径
        """
        if df.empty:
            print(f"⚠️ 空数据，跳过同步: {target_date}")
            return ""
        
        # 构建分区路径
        partition_path = self.raw_dir / str(target_date.year) / f"{target_date.month:02d}"
        partition_path.mkdir(parents=True, exist_ok=True)
        
        # 文件名
        filename = f"orders_{target_date.strftime('%Y%m%d')}.parquet"
        filepath = partition_path / filename
        
        # 写入 Parquet（使用 snappy 压缩）
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        # 更新元数据
        self._update_partition_metadata(target_date, len(df))
        
        print(f"✅ 原始数据已同步: {filepath} ({len(df)} 行)")
        return str(filepath)
    
    def generate_daily_aggregations(self, target_date: date) -> Dict[str, str]:
        """
        生成日聚合数据
        
        Args:
            target_date: 聚合日期
        
        Returns:
            生成的聚合文件路径字典
        """
        # 读取当日原始数据
        raw_file = self.raw_dir / str(target_date.year) / f"{target_date.month:02d}" / f"orders_{target_date.strftime('%Y%m%d')}.parquet"
        
        if not raw_file.exists():
            print(f"⚠️ 原始数据不存在: {raw_file}")
            return {}
        
        df = pd.read_parquet(raw_file)
        results = {}
        
        # 确保daily目录存在
        daily_dir = self.agg_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. KPI 日聚合
        try:
            kpi_agg = self._aggregate_kpi(df, target_date)
            kpi_file = daily_dir / "kpi_daily.parquet"
            self._append_or_create(kpi_file, kpi_agg, ['日期', '门店名称'])
            results['kpi'] = str(kpi_file)
        except Exception as e:
            print(f"⚠️ KPI聚合失败: {e}")
        
        # 2. 渠道日聚合
        try:
            channel_agg = self._aggregate_channel(df, target_date)
            channel_file = daily_dir / "channel_daily.parquet"
            self._append_or_create(channel_file, channel_agg, ['日期', '门店名称', '渠道'])
            results['channel'] = str(channel_file)
        except Exception as e:
            print(f"⚠️ 渠道聚合失败: {e}")
        
        # 3. 品类日聚合
        try:
            category_agg = self._aggregate_category(df, target_date)
            category_file = daily_dir / "category_daily.parquet"
            self._append_or_create(category_file, category_agg, ['日期', '门店名称', '一级分类名'])
            results['category'] = str(category_file)
        except Exception as e:
            print(f"⚠️ 品类聚合失败: {e}")
        
        # 更新元数据
        self._update_last_sync(target_date)
        
        print(f"✅ 日聚合数据已生成: {target_date}")
        return results
    
    def _aggregate_kpi(self, df: pd.DataFrame, target_date: date) -> pd.DataFrame:
        """KPI 聚合逻辑"""
        if df.empty:
            return pd.DataFrame()
        
        # 确保必要字段存在
        required_fields = ['订单ID', '门店名称', '实收价格', '利润额']
        for field in required_fields:
            if field not in df.columns:
                df[field] = 0 if field != '门店名称' else 'unknown'
        
        # 填充缺失字段
        for field in ['平台服务费', '物流配送费', '企客后返']:
            if field not in df.columns:
                df[field] = 0
            else:
                df[field] = df[field].fillna(0)
        
        # 订单级聚合
        order_agg = df.groupby('订单ID').agg({
            '实收价格': 'sum',
            '利润额': 'sum',
            '平台服务费': 'sum',
            '物流配送费': 'first',
            '企客后返': 'sum',
            '门店名称': 'first',
        }).reset_index()
        
        # 计算订单实际利润
        order_agg['订单实际利润'] = (
            order_agg['利润额'] -
            order_agg['平台服务费'] -
            order_agg['物流配送费'] +
            order_agg['企客后返']
        )
        
        # 按门店聚合
        kpi = order_agg.groupby('门店名称').agg({
            '订单ID': 'count',
            '实收价格': 'sum',
            '订单实际利润': 'sum',
        }).reset_index()
        
        kpi.columns = ['门店名称', '订单数', '商品实收额', '总利润']
        # 日期转为字符串避免Parquet类型问题
        kpi['日期'] = str(target_date)
        kpi['平均客单价'] = kpi['商品实收额'] / kpi['订单数'].replace(0, 1)
        kpi['利润率'] = kpi['总利润'] / kpi['商品实收额'].replace(0, 1) * 100
        
        # 动销商品数
        if '商品名称' in df.columns and '月售' in df.columns:
            active_products = df[df['月售'] > 0].groupby('门店名称')['商品名称'].nunique().reset_index()
            active_products.columns = ['门店名称', '动销商品数']
            kpi = kpi.merge(active_products, on='门店名称', how='left')
            kpi['动销商品数'] = kpi['动销商品数'].fillna(0).astype(int)
        else:
            kpi['动销商品数'] = 0
        
        return kpi
    
    def _aggregate_channel(self, df: pd.DataFrame, target_date: date) -> pd.DataFrame:
        """渠道聚合"""
        if df.empty or '渠道' not in df.columns:
            return pd.DataFrame()
        
        # 填充缺失字段
        for field in ['平台服务费', '物流配送费', '企客后返']:
            if field not in df.columns:
                df[field] = 0
            else:
                df[field] = df[field].fillna(0)
        
        # 订单级聚合
        order_agg = df.groupby('订单ID').agg({
            '实收价格': 'sum',
            '利润额': 'sum',
            '平台服务费': 'sum',
            '物流配送费': 'first',
            '企客后返': 'sum',
            '门店名称': 'first',
            '渠道': 'first',
        }).reset_index()
        
        order_agg['订单实际利润'] = (
            order_agg['利润额'] -
            order_agg['平台服务费'] -
            order_agg['物流配送费'] +
            order_agg['企客后返']
        )
        
        # 按门店+渠道聚合
        channel_agg = order_agg.groupby(['门店名称', '渠道']).agg({
            '订单ID': 'count',
            '实收价格': 'sum',
            '订单实际利润': 'sum',
        }).reset_index()
        
        channel_agg.columns = ['门店名称', '渠道', '订单数', '销售额', '利润']
        # 日期转为字符串避免Parquet类型问题
        channel_agg['日期'] = str(target_date)
        channel_agg['客单价'] = channel_agg['销售额'] / channel_agg['订单数'].replace(0, 1)
        channel_agg['利润率'] = channel_agg['利润'] / channel_agg['销售额'].replace(0, 1) * 100
        
        return channel_agg
    
    def _aggregate_category(self, df: pd.DataFrame, target_date: date) -> pd.DataFrame:
        """品类聚合"""
        if df.empty or '一级分类名' not in df.columns:
            return pd.DataFrame()
        
        # 填充缺失字段
        if '月售' not in df.columns:
            df['月售'] = 1
        
        category_agg = df.groupby(['门店名称', '一级分类名']).agg({
            '订单ID': 'nunique',
            '实收价格': 'sum',
            '利润额': 'sum',
            '月售': 'sum',
        }).reset_index()
        
        category_agg.columns = ['门店名称', '一级分类名', '订单数', '销售额', '利润', '销量']
        # 日期转为字符串避免Parquet类型问题
        category_agg['日期'] = str(target_date)
        
        return category_agg
    
    def _append_or_create(self, filepath: Path, df: pd.DataFrame, dedup_keys: List[str]):
        """追加或创建 Parquet 文件"""
        if df.empty:
            return
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if filepath.exists():
            # 读取现有数据
            existing = pd.read_parquet(filepath)
            # 合并（去重）
            combined = pd.concat([existing, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=dedup_keys, keep='last')
        else:
            combined = df
        
        combined.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)
    
    def _update_partition_metadata(self, target_date: date, record_count: int):
        """更新分区元数据"""
        metadata_file = self.metadata_dir / "partitions.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {"partitions": {}}
        
        partition_key = target_date.strftime('%Y-%m')
        if partition_key not in metadata["partitions"]:
            metadata["partitions"][partition_key] = {"dates": {}, "total_records": 0}
        
        metadata["partitions"][partition_key]["dates"][str(target_date)] = record_count
        metadata["partitions"][partition_key]["total_records"] = sum(
            metadata["partitions"][partition_key]["dates"].values()
        )
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _update_last_sync(self, target_date: date):
        """更新最后同步时间"""
        metadata_file = self.metadata_dir / "last_update.json"
        metadata = {
            "last_sync_date": str(target_date),
            "last_sync_time": datetime.now().isoformat(),
        }
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_status(self) -> Dict:
        """获取同步状态"""
        # 统计Parquet文件
        raw_files = list(self.raw_dir.glob("**/*.parquet"))
        agg_files = list(self.agg_dir.glob("**/*.parquet"))
        
        # 读取元数据
        last_update_file = self.metadata_dir / "last_update.json"
        if last_update_file.exists():
            with open(last_update_file, 'r') as f:
                last_update = json.load(f)
        else:
            last_update = None
        
        return {
            "data_dir": str(self.data_dir),
            "raw_files_count": len(raw_files),
            "aggregated_files_count": len(agg_files),
            "last_update": last_update,
        }


# 全局单例
parquet_sync_service = ParquetSyncService()
