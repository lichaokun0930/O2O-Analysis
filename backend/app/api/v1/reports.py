# -*- coding: utf-8 -*-
"""
报表导出 API

提供:
- Excel导出
- CSV导出
- 各类报表生成
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date
import io

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_report_service,
    get_order_data,
    common_store_param,
    common_date_range_params,
)
from services import ReportService

router = APIRouter()


@router.post("/excel/orders")
async def export_orders_to_excel(
    store_name: Optional[str] = Depends(common_store_param),
    date_params: dict = Depends(common_date_range_params),
    service: ReportService = Depends(get_report_service)
):
    """
    导出订单报表到Excel
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.generate_order_report(
        df,
        store_name=store_name,
        start_date=date_params.get("start_date"),
        end_date=date_params.get("end_date"),
        format='excel'
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 如果返回的是文件路径
    if result.get("filepath"):
        return {
            "success": True,
            "filepath": result["filepath"],
            "filename": result["filename"]
        }
    
    # 如果返回的是buffer（用于下载）
    if result.get("buffer"):
        return StreamingResponse(
            result["buffer"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}"
            }
        )
    
    return {"success": True, "message": "导出成功"}


@router.post("/excel/diagnosis")
async def export_diagnosis_to_excel(
    store_name: Optional[str] = Depends(common_store_param),
    service: ReportService = Depends(get_report_service)
):
    """
    导出诊断报表到Excel
    
    包含：穿底订单、高配送费订单、汇总统计
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.generate_diagnosis_report(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "filepath": result.get("filepath"),
        "filename": result.get("filename")
    }


@router.post("/excel/products")
async def export_products_to_excel(
    top_n: int = Query(100, ge=1, le=1000, description="商品数量"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ReportService = Depends(get_report_service)
):
    """
    导出商品报表到Excel
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.generate_product_report(
        df,
        store_name=store_name,
        top_n=top_n
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "filepath": result.get("filepath"),
        "filename": result.get("filename")
    }


@router.post("/excel/comprehensive")
async def export_comprehensive_to_excel(
    store_name: Optional[str] = Depends(common_store_param),
    service: ReportService = Depends(get_report_service)
):
    """
    导出综合报表到Excel
    
    包含：KPI汇总、订单明细、商品排行、渠道分析
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.generate_comprehensive_report(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "filepath": result.get("filepath"),
        "filename": result.get("filename")
    }


@router.post("/csv/orders")
async def export_orders_to_csv(
    store_name: Optional[str] = Depends(common_store_param),
    date_params: dict = Depends(common_date_range_params),
    service: ReportService = Depends(get_report_service)
):
    """
    导出订单数据到CSV
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.generate_order_report(
        df,
        store_name=store_name,
        start_date=date_params.get("start_date"),
        end_date=date_params.get("end_date"),
        format='csv'
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "filepath": result.get("filepath"),
        "filename": result.get("filename")
    }


@router.get("/download/{filename}")
async def download_report(filename: str):
    """
    下载已生成的报表文件
    """
    import os
    
    # 安全检查：防止路径遍历
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    report_dir = './reports'
    filepath = os.path.join(report_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 确定MIME类型
    if filename.endswith('.xlsx'):
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename.endswith('.csv'):
        media_type = 'text/csv'
    else:
        media_type = 'application/octet-stream'
    
    with open(filepath, 'rb') as f:
        content = f.read()
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

