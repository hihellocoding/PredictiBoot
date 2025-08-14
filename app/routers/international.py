from fastapi import APIRouter, Query, HTTPException
from ..international.crawler import get_historical_data_international

router = APIRouter(
    prefix="/stocks/international",
    tags=["international-stocks"],
)

@router.get("/historical")
async def get_international_historical_data(
    ticker: str = Query(..., description="Stock ticker (e.g., 'AAPL', 'MSFT')"),
    period: str = Query("1y", description="Data period (e.g., '1y', '5y', 'max')")
):
    """
    Get historical data for an international stock.
    """
    data = get_historical_data_international(ticker, period)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    if not data:
        raise HTTPException(status_code=404, detail="No historical data found for the given ticker and period.")
    return {"historical_data": data}
