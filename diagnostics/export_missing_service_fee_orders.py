from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_PATH = Path("实际数据/2025-10-16 00_00_00至2025-11-14 23_59_59订单明细数据导出汇总 (1).xlsx")
OUTPUT_DIR = Path("diagnostics")
OUTPUT_CSV = OUTPUT_DIR / "platform_fee_missing_orders.csv"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(DATA_PATH)
    df["订单ID"] = df["订单ID"].astype(str)

    for col in ["平台服务费", "平台佣金"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    order_level = df.groupby("订单ID").agg({"平台服务费": "sum", "平台佣金": "max"})
    order_level["平台服务费"] = order_level["平台服务费"].fillna(0)
    order_level["平台佣金"] = order_level["平台佣金"].fillna(0)

    missing_mask = order_level["平台服务费"] == 0
    order_level["佣金兜底金额"] = order_level["平台佣金"].where(missing_mask, 0)

    summary = {
        "order_count": len(order_level),
        "missing_service_fee_orders": int(missing_mask.sum()),
        "service_fee_sum": float(order_level["平台服务费"].sum()),
        "fallback_commission_sum": float(order_level["佣金兜底金额"].sum()),
        "total_platform_cost": float(order_level["平台服务费"].sum() + order_level["佣金兜底金额"].sum()),
    }

    missing_orders = order_level[missing_mask].copy()
    missing_orders = missing_orders.sort_values("平台佣金", ascending=False)
    missing_orders[["平台服务费", "平台佣金", "佣金兜底金额"]].to_csv(
        OUTPUT_CSV, encoding="utf-8-sig"
    )

    print(
        "总订单数: {order_count:,}\n"
        "缺失平台服务费的订单数: {missing_service_fee_orders:,}\n"
        "平台服务费合计: {service_fee_sum:,.2f}\n"
        "缺失订单兜底佣金合计: {fallback_commission_sum:,.2f}\n"
        "利润中使用的平台总费用: {total_platform_cost:,.2f}\n"
        "缺失订单列表已写入: {csv_path}"
    .format(
        csv_path=OUTPUT_CSV,
        **summary,
    ))


if __name__ == "__main__":
    main()
