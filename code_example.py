import asyncio
import json
import websockets

async def main():
    url = "wss://stream.binance.com:9443/ws/btcusdt@ticker"

    async with websockets.connect(url) as ws:
        print("Connected to Binance WebSocket…\n")

        while True:
            data = await ws.recv()
            data = json.loads(data)

            price = data["c"]
            print("BTC/USDT:", price)

asyncio.run(main())
