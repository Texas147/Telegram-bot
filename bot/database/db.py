import os
import asyncpg
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger("zb-bot.db")
DB_URL = os.getenv("DATABASE_URL")  # URL подключения к PostgreSQL (Supabase)

async def init_db():
    if not DB_URL:
        logger.error("DATABASE_URL не задан!")
        return
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id),
            status TEXT DEFAULT 'FREE',
            expires_at TIMESTAMP,
            daily_requests INT DEFAULT 0,
            last_request_date DATE DEFAULT CURRENT_DATE
        );
    """)
    await conn.close()
    logger.info("Облачная база PostgreSQL (Supabase) успешно подключена.")

async def get_or_create_user(telegram_id: int, username: str, full_name: str):
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("""
        INSERT INTO users (telegram_id, username, full_name) 
        VALUES ($1, $2, $3) ON CONFLICT (telegram_id) DO NOTHING
    """, telegram_id, username, full_name)
    
    await conn.execute("""
        INSERT INTO subscriptions (telegram_id) 
        VALUES ($1) ON CONFLICT (telegram_id) DO NOTHING
    """, telegram_id)
    await conn.close()

# Аналогично обновляются функции check_user_access, increment_usage, activate_premium
# с использованием синтаксиса asyncpg (conn.fetchrow, conn.execute).
