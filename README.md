# Romantic Bot ❤️

Telegram‑бот, который помогает создавать настоящие эмоциональные события в отношениях.

## Структура проекта

```
romantic_bot/
├── alembic/                     # Конфигурация и миграции Alembic
│   ├── env.py
│   └── versions/
│       ├── b8d93fa9849e_add_reason_gifts.py
│       ├── bb0d4dc90537_fix_couple_foreign_key_to_telegram_id.py
│       └── f96f0cc118cd_create_users_table.py
├── bot/                         # Telegram‑специфичный код
│   ├── callbacks/
│   │   └── main.py
│   ├── handlers/
│   │   ├── couple.py
│   │   ├── profile.py
│   │   └── settings.py
│   ├── keyboards/
│   │   ├── common_kb.py
│   │   ├── couple_kb.py
│   │   ├── letter_delivery_kb.py
│   │   ├── letter_kb.py
│   │   ├── main_kb.py
│   │   ├── memory_kb.py
│   │   ├── reason_kb.py
│   │   └── settings_kb.py
│   ├── middlewares/
│   │   └── db.py
│   ├── states/
│   │   ├── couple.py
│   │   ├── letter.py
│   │   ├── memory.py
│   │   ├── reason.py
│   │   └── settings.py
│   └── utils/
│       ├── navigation.py
│       └── timezone_utils.py
├── database/                    # Работа с базой данных
│   ├── models/
│   │   ├── base.py
│   │   ├── couple.py
│   │   ├── reason.py
│   │   ├── tree.py
│   │   └── user.py
│   └── repositories/
│       ├── base.py
│       ├── couple.py
│       ├── letter.py
│       ├── memory.py
│       ├── reason.py
│       ├── tree.py
│       └── user.py
├── services/                    # Бизнес‑логика (не зависит от Telegram API)
│   ├── anniversary_service.py
│   ├── couple_service.py
│   ├── letter_service.py
│   ├── memory_service.py
│   ├── reason_reminder_service.py
│   ├── reason_service.py
│   ├── tree_service.py
│   └── user_service.py
├── collect_project.py           # Скрипт для сбора проекта в один файл
├── config.py                    # Конфигурация приложения (pydantic)
├── main.py                      # Точка входа, планировщик задач
├── requirements.txt             # Зависимости проекта
├── docker-compose.yml           # Docker‑композиция
└── .env.example                 # Шаблон переменных окружения
```

## Технологический стек

- **Python** 3.12
- **aiogram** 3.x – Telegram Bot API
- **SQLAlchemy** 2 (async) – ORM
- **PostgreSQL** – реляционная БД
- **Redis** – кэш/сессии
- **APScheduler** – планировщик фоновых задач
- **Alembic** – миграции БД

## Установка и запуск

```bash
# Клонируем репозиторий
git clone https://github.com/your-username/romantic-bot.git
cd romantic-bot

# Создаём и заполняем переменные окружения
cp .env.example .env
# Внесите свои значения (см. ниже)

# Запускаем контейнеры
docker compose up -d --build
```

После запуска контейнеров бот автоматически подключится к Telegram и начнёт выполнять фоновые задачи.

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен Telegram‑бота от @BotFather | `123456789:AAF...` |
| `POSTGRES_USER` | Пользователь PostgreSQL | `romantic_bot` |
| `POSTGRES_PASSWORD` | Пароль пользователя | `REPLACE_WITH_STRONG_PASSWORD` |
| `POSTGRES_DB` | Имя базы данных | `romantic_bot_db` |
| `POSTGRES_HOST` | Хост PostgreSQL (внутри Docker‑сети) | `postgres` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `REDIS_HOST` | Хост Redis (внутри Docker‑сети) | `redis` |
| `REDIS_PORT` | Порт Redis | `6379` |
| `REDIS_DB` | Номер базы Redis | `0` |
| `DB_ECHO` | Логировать ли SQL‑запросы (True/False) | `false` |

> **Важно:** Для локальной разработки необходимо задать собственный `BOT_TOKEN`. В `.env.example` он указан как `REPLACE_WITH_BOT_TOKEN`.

## Лицензия

MIT License.  
