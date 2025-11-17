# Инструкция по деплою Telegram MiniApp Crypto Alerts

Подробная инструкция по развертыванию проекта на сервере.

## Требования к серверу

- Ubuntu 20.04+ / Debian 11+ или другой Linux дистрибутив
- Python 3.9+
- Node.js 18+ и npm
- Nginx (для проксирования и статики)
- SSL сертификат (Let's Encrypt)
- Домен с настроенными DNS записями

## Шаг 1: Подготовка сервера

### Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### Установка необходимых пакетов

```bash
# Python и pip
sudo apt install python3 python3-pip python3-venv -y

# Node.js и npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Nginx
sudo apt install nginx -y

# Certbot для SSL
sudo apt install certbot python3-certbot-nginx -y

# Git (если еще не установлен)
sudo apt install git -y
```

## Шаг 2: Клонирование проекта

```bash
# Переходим в домашнюю директорию
cd ~

# Клонируем репозиторий
git clone https://github.com/ShcoderDev/crypto_alerts_bot.git

# Переходим в директорию проекта
cd crypto_alerts_bot
```

## Шаг 3: Настройка Python окружения

```bash
cd ~/crypto_alerts_bot

# Создаем виртуальное окружение (если еще не создано)
python3 -m venv .venv

# Активируем окружение
source .venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

## Шаг 4: Настройка переменных окружения

```bash
cd ~/crypto_alerts_bot

# Копируем пример файла .env
cp .env.example .env

# Редактируем файл .env
nano .env
```

Добавьте в файл:

```env
BOT_TOKEN=ваш_токен_бота_от_BotFather
MINIAPP_URL=https://ваш-домен.com
```

**Важно:** Замените `ваш_токен_бота_от_BotFather` на реальный токен от @BotFather в Telegram, а `ваш-домен.com` на ваш домен.

## Шаг 5: Сборка фронтенда

```bash
cd ~/crypto_alerts_bot/webapp/frontend

# Устанавливаем зависимости (если еще не установлены)
npm install

# Собираем проект для продакшена
npm run build
```

После сборки файлы будут в `webapp/frontend/dist/`

**Примечание:** Если `dist` уже существует, пересоберите проект после обновления кода.

## Шаг 6: Настройка systemd сервисов

### Сервис для бота

```bash
sudo nano /etc/systemd/system/crypto-alerts-bot.service
```

Добавьте:

```ini
[Unit]
Description=Crypto Alerts Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/crypto_alerts_bot
Environment="PATH=/root/crypto_alerts_bot/.venv/bin"
ExecStart=/root/crypto_alerts_bot/.venv/bin/python /root/crypto_alerts_bot/start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Сервис для веб-приложения

```bash
sudo nano /etc/systemd/system/crypto-alerts-webapp.service
```

Добавьте:

```ini
[Unit]
Description=Crypto Alerts WebApp
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/crypto_alerts_bot
Environment="PATH=/root/crypto_alerts_bot/.venv/bin"
ExecStart=/root/crypto_alerts_bot/.venv/bin/uvicorn webapp.backend.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Установка прав доступа

```bash
# Убедитесь, что у вас есть права на запись в директорию проекта
chmod -R 755 ~/crypto_alerts_bot
```

### Запуск сервисов

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable crypto-alerts-bot.service
sudo systemctl enable crypto-alerts-webapp.service

# Запускаем сервисы
sudo systemctl start crypto-alerts-bot.service
sudo systemctl start crypto-alerts-webapp.service

# Проверяем статус
sudo systemctl status crypto-alerts-bot.service
sudo systemctl status crypto-alerts-webapp.service
```

## Шаг 7: Настройка Nginx

### Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/crypto-alerts
```

Добавьте конфигурацию:

```nginx
server {
    listen 80;
    server_name ваш-домен.com;

    # Редирект на HTTPS (будет работать после настройки SSL)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ваш-домен.com;

    # SSL сертификаты (будут настроены через certbot)
    ssl_certificate /etc/letsencrypt/live/ваш-домен.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ваш-домен.com/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Максимальный размер загружаемых файлов
    client_max_body_size 10M;

    # Проксирование API запросов к FastAPI
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Статические файлы фронтенда
    location / {
        root /root/crypto_alerts_bot/webapp/frontend/dist;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "public, max-age=3600";
    }

    # Кеширование статических ресурсов
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /root/crypto_alerts_bot/webapp/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Важно:** Замените `ваш-домен.com` на ваш реальный домен.

### Активация конфигурации

```bash
# Создаем симлинк
sudo ln -s /etc/nginx/sites-available/crypto-alerts /etc/nginx/sites-enabled/

# Удаляем дефолтную конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверяем конфигурацию
sudo nginx -t

# Перезапускаем Nginx
sudo systemctl restart nginx
```

## Шаг 8: Настройка SSL сертификата

```bash
# Получаем SSL сертификат от Let's Encrypt
sudo certbot --nginx -d ваш-домен.com

# Следуйте инструкциям certbot
# Укажите email для уведомлений
# Согласитесь с условиями использования
```

Certbot автоматически обновит конфигурацию Nginx и настроит автоматическое обновление сертификата.

## Шаг 9: Настройка Telegram Bot

1. Откройте Telegram и найдите @BotFather
2. Отправьте команду `/newbot` или `/mybots` для редактирования существующего бота
3. Выберите вашего бота
4. Выберите "Bot Settings" → "Menu Button"
5. Нажмите "Configure Menu Button"
6. Введите URL вашего MiniApp: `https://ваш-домен.com`
7. Сохраните изменения

## Шаг 10: Настройка файрвола (если используется)

```bash
# Разрешаем HTTP и HTTPS
sudo ufw allow 'Nginx Full'

# Или отдельно
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверяем статус
sudo ufw status
```

## Шаг 11: Проверка работы

### Проверка бота

```bash
# Смотрим логи бота
sudo journalctl -u crypto-alerts-bot.service -f

# Проверяем статус
sudo systemctl status crypto-alerts-bot.service
```

### Проверка веб-приложения

```bash
# Смотрим логи веб-приложения
sudo journalctl -u crypto-alerts-webapp.service -f

# Проверяем статус
sudo systemctl status crypto-alerts-webapp.service

# Проверяем доступность API
curl https://ваш-домен.com/api/cryptocurrencies
```

### Проверка в браузере

Откройте в браузере: `https://ваш-домен.com`

Должна открыться страница MiniApp.

## Шаг 12: Обновление проекта

При обновлении кода:

```bash
cd ~/crypto_alerts_bot

# Активируем виртуальное окружение
source .venv/bin/activate

# Обновляем код из репозитория
git pull

# Обновляем Python зависимости (если изменились)
pip install -r requirements.txt

# Пересобираем фронтенд (если изменился)
cd webapp/frontend
npm install
npm run build
cd ../..

# Перезапускаем сервисы
sudo systemctl restart crypto-alerts-bot.service
sudo systemctl restart crypto-alerts-webapp.service
```

## Управление сервисами

### Просмотр логов

```bash
# Логи бота
sudo journalctl -u crypto-alerts-bot.service -n 100 -f

# Логи веб-приложения
sudo journalctl -u crypto-alerts-webapp.service -n 100 -f
```

### Перезапуск сервисов

```bash
sudo systemctl restart crypto-alerts-bot.service
sudo systemctl restart crypto-alerts-webapp.service
```

### Остановка сервисов

```bash
sudo systemctl stop crypto-alerts-bot.service
sudo systemctl stop crypto-alerts-webapp.service
```

### Запуск сервисов

```bash
sudo systemctl start crypto-alerts-bot.service
sudo systemctl start crypto-alerts-webapp.service
```

## Резервное копирование

Рекомендуется настроить автоматическое резервное копирование базы данных:

```bash
# Создаем скрипт для бэкапа
sudo nano /usr/local/bin/backup-crypto-alerts.sh
```

Добавьте:

```bash
#!/bin/bash
BACKUP_DIR="/root/backups/crypto-alerts"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp /root/crypto_alerts_bot/database.db $BACKUP_DIR/database_$DATE.db

# Удаляем старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "database_*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Сделайте скрипт исполняемым:

```bash
sudo chmod +x /usr/local/bin/backup-crypto-alerts.sh
```

Добавьте в crontab для ежедневного бэкапа:

```bash
sudo crontab -e
```

Добавьте строку:

```
0 2 * * * /usr/local/bin/backup-crypto-alerts.sh
```

## Мониторинг

Для мониторинга можно использовать:

- `htop` или `top` для мониторинга ресурсов
- `journalctl` для просмотра логов
- Настроить мониторинг через Prometheus/Grafana (опционально)

## Решение проблем

### Бот не запускается

1. Проверьте токен в `.env`
2. Проверьте логи: `sudo journalctl -u crypto-alerts-bot.service -n 50`
3. Убедитесь, что база данных создана и доступна

### Веб-приложение не работает

1. Проверьте, что порт 8000 не занят: `sudo netstat -tlnp | grep 8000`
2. Проверьте логи: `sudo journalctl -u crypto-alerts-webapp.service -n 50`
3. Проверьте конфигурацию Nginx: `sudo nginx -t`

### SSL сертификат не работает

1. Проверьте DNS записи для домена
2. Убедитесь, что порты 80 и 443 открыты
3. Проверьте логи certbot: `sudo certbot certificates`

### База данных не создается

1. Проверьте права доступа: `ls -la ~/crypto_alerts_bot/database.db`
2. Убедитесь, что директория доступна для записи: `ls -la ~/crypto_alerts_bot/`
3. Проверьте логи на ошибки создания БД

## Дополнительные настройки

### Оптимизация производительности

Для высоких нагрузок можно:

1. Использовать Gunicorn с несколькими воркерами вместо uvicorn
2. Настроить кеширование в Nginx
3. Использовать Redis для кеширования (опционально)
4. Настроить CDN для статических файлов

### Безопасность

1. Регулярно обновляйте систему и зависимости
2. Используйте сильные пароли
3. Настройте fail2ban для защиты от брутфорса
4. Регулярно проверяйте логи на подозрительную активность

## Поддержка

При возникновении проблем проверьте:
- Логи сервисов
- Логи Nginx: `sudo tail -f /var/log/nginx/error.log`
- Статус сервисов: `sudo systemctl status crypto-alerts-*.service`

