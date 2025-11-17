# Telegram MiniApp Crypto Price Alerts

Telegram бот с MiniApp для отслеживания цен криптовалют через Binance WebSocket. Пользователи могут устанавливать ценовые алерты и получать уведомления в Telegram.

## Технологии

- **Bot**: aiogram 3.x, asyncio, websockets
- **Backend**: FastAPI, SQLite, websockets
- **Frontend**: Vue 3, TypeScript, Composition API
- **Database**: SQLite

## Установка

### 1. Установка Python зависимостей

```bash
pip install -r requirements.txt
```

### 2. Установка Node.js зависимостей для фронтенда

```bash
cd webapp/frontend
npm install
```

### 3. Настройка .env файла

Скопируйте файл `.env.example` в `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваши значения:

```env
BOT_TOKEN=your_telegram_bot_token_here
MINIAPP_URL=https://your-miniapp-url.com
```

## Запуск

### Запуск бота

```bash
python start_bot.py
```

### Запуск веб-приложения

В одном терминале (бэкенд):
```bash
python start_webapp.py
```

В другом терминале (фронтенд для разработки):
```bash
cd webapp/frontend
npm run dev
```

Для продакшена соберите фронтенд:
```bash
cd webapp/frontend
npm run build
```

## Структура проекта

```
miniapp/
├── start_bot.py              # Точка входа для бота
├── start_webapp.py           # Точка входа для веб-приложения
├── requirements.txt          # Python зависимости
├── .env                      # Конфигурация (токен бота, URL MiniApp)
├── database.db               # SQLite база данных (создается автоматически)
├── bot/                      # Логика бота
│   ├── config.py            # Конфигурация
│   ├── database.py          # Работа с БД
│   ├── models.py            # Модели данных
│   ├── price_monitor.py     # Мониторинг цен
│   └── handlers/            # Обработчики команд
│       └── commands.py
└── webapp/                   # Веб-приложение
    ├── backend/             # FastAPI бэкенд
    │   ├── main.py
    │   └── database.py
    └── frontend/            # Vue 3 фронтенд
        ├── src/
        │   ├── App.vue
        │   ├── main.ts
        │   ├── api.ts
        │   ├── types.ts
        │   └── components/
        │       ├── AlertForm.vue
        │       └── AlertItem.vue
        └── package.json
```

## Функциональность

### Бот
- `/start` - Регистрация пользователя и получение ссылки на MiniApp
- Автоматический мониторинг цен через Binance WebSocket
- Отправка уведомлений в Telegram при достижении целевой цены

### MiniApp
- Выбор криптовалюты из списка (10 основных)
- Установка целевой цены и направления (выше/ниже)
- Просмотр всех активных алертов
- Редактирование и удаление алертов
- Красивый минималистичный дизайн

## Поддерживаемые криптовалюты

- BTC (Bitcoin)
- ETH (Ethereum)
- BNB (Binance Coin)
- SOL (Solana)
- XRP (Ripple)
- ADA (Cardano)
- DOGE (Dogecoin)
- DOT (Polkadot)
- MATIC (Polygon)
- AVAX (Avalanche)

## Деплой на сервер

Подробная инструкция по развертыванию на продакшн сервере находится в файле [DEPLOY.md](DEPLOY.md).

