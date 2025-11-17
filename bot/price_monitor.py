import asyncio
import json
import websockets
from typing import Dict
from bot.database import Database
from bot.config import CRYPTOCURRENCIES
from aiogram import Bot


class PriceMonitor:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self.running = False
        self.current_prices: Dict[str, float] = {}

    async def start(self):
        """Запуск мониторинга цен"""
        self.running = True
        active_tasks: Dict[str, asyncio.Task] = {}
        
        while self.running:
            try:
                # Получаем все активные алерты
                alerts = await self.db.get_all_active_alerts()
                
                # Определяем, какие криптовалюты нужно отслеживать
                cryptos_to_monitor = set()
                for alert in alerts:
                    cryptos_to_monitor.add(alert.cryptocurrency.upper())
                
                # Запускаем задачи для новых криптовалют
                for crypto in cryptos_to_monitor:
                    if crypto not in active_tasks or active_tasks[crypto].done():
                        active_tasks[crypto] = asyncio.create_task(self._monitor_crypto(crypto))
                
                # Удаляем задачи для криптовалют, которые больше не нужны
                cryptos_to_remove = set(active_tasks.keys()) - cryptos_to_monitor
                for crypto in cryptos_to_remove:
                    if crypto in active_tasks:
                        active_tasks[crypto].cancel()
                        try:
                            await active_tasks[crypto]
                        except asyncio.CancelledError:
                            pass
                        del active_tasks[crypto]
                
                await asyncio.sleep(10)  # Проверяем каждые 10 секунд
                    
            except Exception as e:
                print(f"Ошибка в мониторинге: {e}")
                await asyncio.sleep(5)

    async def _monitor_crypto(self, cryptocurrency: str):
        """Мониторинг одной криптовалюты"""
        symbol = f"{cryptocurrency.lower()}usdt"
        url = f"wss://stream.binance.com:9443/ws/{symbol}@ticker"
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    print(f"Подключено к WebSocket для {cryptocurrency}")
                    
                    async for message in ws:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            price = float(data.get("c", 0))
                            
                            if price > 0:
                                self.current_prices[cryptocurrency] = price
                                await self._check_alerts(cryptocurrency, price)
                        except (json.JSONDecodeError, ValueError, KeyError) as e:
                            print(f"Ошибка обработки данных для {cryptocurrency}: {e}")
                            continue
                            
            except websockets.exceptions.ConnectionClosed:
                print(f"Соединение закрыто для {cryptocurrency}, переподключение...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Ошибка подключения для {cryptocurrency}: {e}")
                await asyncio.sleep(5)

    async def _check_alerts(self, cryptocurrency: str, current_price: float):
        """Проверка алертов для конкретной криптовалюты"""
        alerts = await self.db.get_all_active_alerts()
        
        for alert in alerts:
            if alert.cryptocurrency.upper() != cryptocurrency.upper():
                continue
            
            triggered = False
            
            if alert.is_above:
                # Алерт срабатывает, если цена стала выше целевой
                if current_price >= alert.target_price:
                    triggered = True
            else:
                # Алерт срабатывает, если цена стала ниже целевой
                if current_price <= alert.target_price:
                    triggered = True
            
            if triggered:
                # Отправляем уведомление
                direction = "выше" if alert.is_above else "ниже"
                message = (
                    f"🔔 Уведомление о цене!\n\n"
                    f"Криптовалюта: {alert.cryptocurrency}\n"
                    f"Текущая цена: ${current_price:,.2f}\n"
                    f"Целевая цена: ${alert.target_price:,.2f}\n"
                    f"Цена достигла значения {direction} целевой цены!"
                )
                
                try:
                    await self.bot.send_message(alert.user_id, message)
                    # Деактивируем алерт после срабатывания
                    await self.db.deactivate_alert(alert.id)
                    print(f"Отправлено уведомление пользователю {alert.user_id} для {alert.cryptocurrency}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")

    async def stop(self):
        """Остановка мониторинга"""
        self.running = False

