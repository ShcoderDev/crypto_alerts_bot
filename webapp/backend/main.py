from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import httpx

from webapp.backend.database import Database
from bot.config import CRYPTOCURRENCIES

app = FastAPI(title="Crypto Alerts MiniApp API")

# CORS для работы с Telegram MiniApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()


# Pydantic модели для валидации
class AlertCreate(BaseModel):
    cryptocurrency: str
    target_price: float
    is_above: bool


class AlertUpdate(BaseModel):
    cryptocurrency: Optional[str] = None
    target_price: Optional[float] = None
    is_above: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    user_id: int
    cryptocurrency: str
    target_price: float
    is_above: bool
    created_at: str
    is_active: bool

    class Config:
        from_attributes = True


@app.on_event("startup")
async def startup():
    """Инициализация базы данных при запуске"""
    await db.init_db()


@app.get("/api/cryptocurrencies")
async def get_cryptocurrencies():
    """Получение списка доступных криптовалют"""
    return {"cryptocurrencies": CRYPTOCURRENCIES}


@app.get("/api/candles")
async def get_candles(symbol: str = Query(..., description="Символ криптовалюты (например, BTCUSDT)"), 
                      interval: str = Query("1m", description="Интервал свечей"),
                      limit: int = Query(60, description="Количество свечей")):
    """Получение исторических данных свечей от Binance"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.binance.com/api/v3/klines",
                params={
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Преобразуем данные в нужный формат
            candles = []
            for kline in data:
                candles.append({
                    "time": kline[0] / 1000,  # Unix timestamp в секундах
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5])
                })
            
            return {"candles": candles}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Binance API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts(user_id: int):
    """Получение всех алертов пользователя"""
    alerts = await db.get_user_alerts(user_id)
    return [
        AlertResponse(
            id=alert.id,
            user_id=alert.user_id,
            cryptocurrency=alert.cryptocurrency,
            target_price=alert.target_price,
            is_above=alert.is_above,
            created_at=alert.created_at.isoformat(),
            is_active=alert.is_active
        )
        for alert in alerts
    ]


@app.post("/api/alerts", response_model=AlertResponse)
async def create_alert(user_id: int, alert_data: AlertCreate):
    """Создание нового алерта"""
    # Валидация криптовалюты
    if alert_data.cryptocurrency.upper() not in [c.upper() for c in CRYPTOCURRENCIES]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая криптовалюта")
    
    # Валидация цены
    if alert_data.target_price <= 0:
        raise HTTPException(status_code=400, detail="Цена должна быть положительным числом")
    
    alert = await db.create_alert(
        user_id=user_id,
        cryptocurrency=alert_data.cryptocurrency.upper(),
        target_price=alert_data.target_price,
        is_above=alert_data.is_above
    )
    
    return AlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        cryptocurrency=alert.cryptocurrency,
        target_price=alert.target_price,
        is_above=alert.is_above,
        created_at=alert.created_at.isoformat(),
        is_active=alert.is_active
    )


@app.put("/api/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: int, user_id: int, alert_data: AlertUpdate):
    """Обновление алерта"""
    # Проверяем, что алерт принадлежит пользователю
    alert = await db.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Алерт не найден")
    
    if alert.user_id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому алерту")
    
    # Валидация криптовалюты, если она указана
    if alert_data.cryptocurrency and alert_data.cryptocurrency.upper() not in [c.upper() for c in CRYPTOCURRENCIES]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая криптовалюта")
    
    # Валидация цены, если она указана
    if alert_data.target_price is not None and alert_data.target_price <= 0:
        raise HTTPException(status_code=400, detail="Цена должна быть положительным числом")
    
    await db.update_alert(
        alert_id=alert_id,
        cryptocurrency=alert_data.cryptocurrency.upper() if alert_data.cryptocurrency else None,
        target_price=alert_data.target_price,
        is_above=alert_data.is_above
    )
    
    updated_alert = await db.get_alert(alert_id)
    return AlertResponse(
        id=updated_alert.id,
        user_id=updated_alert.user_id,
        cryptocurrency=updated_alert.cryptocurrency,
        target_price=updated_alert.target_price,
        is_above=updated_alert.is_above,
        created_at=updated_alert.created_at.isoformat(),
        is_active=updated_alert.is_active
    )


@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: int, user_id: int):
    """Удаление алерта"""
    # Проверяем, что алерт принадлежит пользователю
    alert = await db.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Алерт не найден")
    
    if alert.user_id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому алерту")
    
    success = await db.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка при удалении алерта")
    
    return {"message": "Алерт успешно удален"}


# Статические файлы для фронтенда
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Отдача фронтенда для всех остальных путей"""
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Для SPA - возвращаем index.html
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404)

