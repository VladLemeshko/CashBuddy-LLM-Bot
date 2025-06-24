import asyncio
import aiosqlite
from db import DB_PATH

async def test_goal_display():
    # Тестовый user_id (замените на ваш)
    user_id = 231160776
    
    print(f"Проверяем цели для пользователя {user_id}...")
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем все цели в базе
            cursor = await db.execute("SELECT * FROM goals")
            all_goals = await cursor.fetchall()
            print(f"Всего целей в базе: {len(all_goals)}")
            
            # Проверяем цели конкретного пользователя
            cursor = await db.execute("SELECT goal_name, target_amount, current_amount, deadline, period, strategy_value, priority FROM goals WHERE user_id=?", (user_id,))
            user_goals = await cursor.fetchall()
            print(f"Целей у пользователя {user_id}: {len(user_goals)}")
            
            for goal in user_goals:
                name, target, current, deadline, period, strategy, priority = goal
                print(f"Цель: {name}, Целевая сумма: {target}, Текущая: {current}, Дедлайн: {deadline}")
                
            # Проверяем пользователей
            cursor = await db.execute("SELECT user_id FROM users")
            users = await cursor.fetchall()
            print(f"Пользователей в базе: {len(users)}")
            for user in users:
                print(f"User ID: {user[0]}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_goal_display()) 