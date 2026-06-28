from fastapi import APIRouter, HTTPException
from models.schemas import PortfolioSaveRequest, PortfolioValuation, HoldingValuation
from services.store_service import save_portfolio, get_portfolio
from services.amfi_service import get_latest_nav
from datetime import date

router = APIRouter()


@router.post("/{user_id}")
async def save_user_portfolio(user_id: str, body: PortfolioSaveRequest):
    holdings = [h.model_dump() for h in body.holdings]
    ok = await save_portfolio(user_id, holdings)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save portfolio.")
    return {"message": "Portfolio saved successfully.", "count": len(holdings)}


@router.get("/{user_id}/valuation", response_model=PortfolioValuation)
async def get_portfolio_valuation(user_id: str):
    portfolio = await get_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this user.")

    holdings_raw = portfolio.get("holdings", [])
    valuations = []
    total_invested = 0
    total_current = 0

    for h in holdings_raw:
        scheme_code = h["scheme_code"]
        nav_data = await get_latest_nav(scheme_code)
        if not nav_data:
            continue
        current_nav = nav_data["nav"]
        units = h["units"]
        buy_nav = h["buy_nav"]
        invested = units * buy_nav
        current_value = units * current_nav
        gain_loss = current_value - invested
        gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0

        valuations.append(HoldingValuation(
            scheme_code=scheme_code,
            fund_name=h.get("fund_name", nav_data.get("scheme_name", "")),
            amc=nav_data.get("amc"),
            category=nav_data.get("category"),
            units=units,
            buy_nav=buy_nav,
            current_nav=current_nav,
            nav_date=nav_data["nav_date"],
            invested_amount=round(invested, 2),
            current_value=round(current_value, 2),
            gain_loss=round(gain_loss, 2),
            gain_loss_pct=round(gain_loss_pct, 2),
        ))
        total_invested += invested
        total_current += current_value

    total_gain_loss = total_current - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0

    return PortfolioValuation(
        user_id=user_id,
        holdings=valuations,
        total_invested=round(total_invested, 2),
        total_current_value=round(total_current, 2),
        total_gain_loss=round(total_gain_loss, 2),
        total_gain_loss_pct=round(total_gain_loss_pct, 2),
        as_of_date=date.today().isoformat(),
    )
