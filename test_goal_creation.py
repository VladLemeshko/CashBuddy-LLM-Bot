import asyncio
import aiosqlite
from db import DB_PATH

async def test_goal_creation():
    # Тестовые данные
    user_id = 231160776  # Замените на ваш user_id
    goal_name = "Тестовая цель"
    target_amount = 10000.0
    deadline = "2024-12-31"
    period = "ежемесячно"
    strategy_value = 1000.0
    priority = 1
    
    print("Попытка создания цели...")
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем, есть ли пользователь
            cursor = await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
            user_exists = await cursor.fetchone()
            
            if not user_exists:
                print(f"Создаем пользователя {user_id}...")
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await db.commit()
            
            # Создаем цель
            await db.execute(
                "INSERT INTO goals (user_id, goal_name, target_amount, deadline, period, strategy_value, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, goal_name, target_amount, deadline, period, strategy_value, priority)
            )
            await db.commit()
            print("✅ Цель успешно создана!")
            
            # Проверяем, что цель сохранилась
            cursor = await db.execute("SELECT * FROM goals WHERE user_id=?", (user_id,))
            goals = await cursor.fetchall()
            print(f"Целей в базе: {len(goals)}")
            for goal in goals:
                print(f"ID: {goal[0]}, User: {goal[1]}, Name: {goal[2]}, Target: {goal[3]}, Current: {goal[4]}")
                
    except Exception as e:
        print(f"❌ Ошибка при создании цели: {e}")

if __name__ == "__main__":
    asyncio.run(test_goal_creation()) 