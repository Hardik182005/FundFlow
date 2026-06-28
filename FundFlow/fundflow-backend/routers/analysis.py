from fastapi import APIRouter, HTTPException, Response
from models.schemas import AnalysisFundRequest, AnalysisResponse, CompareRequest
from services.amfi_service import get_latest_nav, get_nav_history
from services.ai_service import analyze_fund, compare_funds, generate_fund_report_pdf

router = APIRouter()


@router.post("/fund", response_model=AnalysisResponse)
async def analyze_single_fund(body: AnalysisFundRequest):
    nav_data = await get_latest_nav(body.scheme_code)
    if not nav_data:
        raise HTTPException(status_code=404, detail="NAV data not available.")
    nav_history = await get_nav_history(body.scheme_code, 365)
    result = await analyze_fund(
        scheme_code=body.scheme_code,
        fund_name=body.fund_name,
        category=body.category or nav_data.get("category", ""),
        units=body.units,
        buy_nav=body.buy_nav,
        current_nav=nav_data["nav"],
        nav_history=nav_history,
    )
    return result


@router.post("/fund/report")
async def generate_fund_report(body: AnalysisFundRequest):
    nav_data = await get_latest_nav(body.scheme_code)
    if not nav_data:
        raise HTTPException(status_code=404, detail="NAV data not available.")
    nav_history = await get_nav_history(body.scheme_code, 365)
    category = body.category or nav_data.get("category", "")
    result = await analyze_fund(
        scheme_code=body.scheme_code,
        fund_name=body.fund_name,
        category=category,
        units=body.units,
        buy_nav=body.buy_nav,
        current_nav=nav_data["nav"],
        nav_history=nav_history,
    )

    pdf_bytes = await generate_fund_report_pdf(
        scheme_code=body.scheme_code,
        fund_name=body.fund_name,
        category=category,
        units=body.units,
        buy_nav=body.buy_nav,
        metrics=result["metrics"],
        ai_analysis=result["ai_analysis"],
        nav_history=nav_history,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{body.scheme_code}_report.pdf"'},
    )


@router.post("/compare")
async def compare_multiple_funds(body: CompareRequest):
    if len(body.scheme_codes) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 funds can be compared.")
    fund_data_list = []
    for code in body.scheme_codes:
        nav_data = await get_latest_nav(code)
        if nav_data:
            fund_data_list.append(nav_data)
    if not fund_data_list:
        raise HTTPException(status_code=404, detail="No fund data found.")
    comparison = await compare_funds(fund_data_list)
    return {"comparison": comparison}
