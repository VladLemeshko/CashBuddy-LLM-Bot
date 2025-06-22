import aiosqlite

DB_PATH = 'finance.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                type TEXT CHECK(type IN ('income', 'expense')),
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                goal_name TEXT,
                target_amount REAL,
                current_amount REAL DEFAULT 0,
                deadline TEXT,
                period TEXT DEFAULT 'ежемесячно',
                strategy_value REAL DEFAULT 0,
                priority INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS goal_deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                user_id INTEGER,
                amount REAL,
                date TEXT,
                source TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                income_type TEXT,
                monthly_income REAL,
                has_deposits INTEGER,
                deposit_bank TEXT,
                deposit_interest REAL,
                deposit_amount REAL,
                deposit_term TEXT,
                deposit_date TEXT,
                has_loans INTEGER,
                loans_total REAL,
                loans_interest REAL,
                has_investments INTEGER,
                investments_amount REAL,
                investments_profit REAL,
                financial_mood TEXT,
                has_regular_payments INTEGER,
                regular_payments_list TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS credit_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                age INTEGER,
                marital_status INTEGER,
                housing INTEGER,
                loan INTEGER,
                job_category TEXT,
                education TEXT,
                duration INTEGER,
                campaign INTEGER,
                credit_probability REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.commit()

async def save_credit_application(user_id: int, credit_data: dict, probability: float):
    """Сохраняет заявку на кредит в базу данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO credit_applications 
            (user_id, age, marital_status, housing, loan, job_category, education, duration, campaign, credit_probability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, credit_data['age'], credit_data['marital'], credit_data['housing'],
            credit_data['loan'], credit_data['job_category'], credit_data['education'],
            credit_data['duration'], credit_data['campaign'], probability
        ))
        await db.commit()

async def get_user_credit_history(user_id: int):
    """Получает историю кредитных заявок пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT * FROM credit_applications 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()
