from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_PATH = Path("实际数据/2025-10-16 00_00_00至2025-11-14 23_59_59订单明细数据导出汇总 (1).xlsx")

FIELDS = [
    "订单ID",
    "利润额",
    "物流配送费",
    "平台服务费",
    "企客后返",
    "用户支付配送费",
    "配送费减免金额",
    "平台佣金",
]


def main() -> None:
    df = pd.read_excel(DATA_PATH)
    missing = [c for c in FIELDS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df[FIELDS].copy()
    df["订单ID"] = df["订单ID"].astype(str)

    for col in FIELDS[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    agg = {
        "利润额": "sum",
        "物流配送费": "first",
        "平台服务费": "sum",
        "企客后返": "sum",
        "用户支付配送费": "first",
        "配送费减免金额": "first",
        "平台佣金": "first",
    }

    order = df.groupby("订单ID").agg(agg)

    delivery_total = (
        order["物流配送费"]
        - (order["用户支付配送费"] - order["配送费减免金额"])
        - order["企客后返"]
    ).sum()

    for col in ["利润额", "物流配送费", "平台服务费", "企客后返"]:
        if col in order.columns:
            print(f"{col} 汇总: {order[col].sum():,.2f}")

    filtered = order[order["平台服务费"] > 0]

    profit_filtered = (
        filtered["利润额"]
        - filtered["平台服务费"]
        - filtered["物流配送费"]
        + filtered["企客后返"]
    ).sum()

    delivery_filtered = (
        filtered["物流配送费"]
        - (filtered["用户支付配送费"] - filtered["配送费减免金额"])
        - filtered["企客后返"]
    ).sum()

    profit_no_fallback = (
        order["利润额"]
        - order["平台服务费"]
        - order["物流配送费"]
        + order["企客后返"]
    ).sum()

    platform_fee_with_fallback = order["平台服务费"].where(
        order["平台服务费"] != 0, order["平台佣金"]
    )

    profit_with_fallback = (
        order["利润额"]
        - platform_fee_with_fallback
        - order["物流配送费"]
        + order["企客后返"]
    ).sum()

    print(f"总订单数: {len(order):,}")
    print(f"平台服务费>0的订单数: {len(filtered):,}")
    print(f"平台服务费=0的订单数: {len(order) - len(filtered):,}")
    print(f"(全量, 无兜底)利润 = {profit_no_fallback:,.2f}")
    print(f"(全量, 含兜底)利润 = {profit_with_fallback:,.2f}")
    print(f"(仅平台费>0订单)利润 = {profit_filtered:,.2f}")
    print(f"配送净成本(全量订单) = {delivery_total:,.2f}")
    print(f"配送净成本(仅平台费>0订单) = {delivery_filtered:,.2f}")


if __name__ == "__main__":
    main()
