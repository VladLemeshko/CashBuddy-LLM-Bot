#!/bin/bash

# Останавливаем предыдущие процессы
pkill -f "uvicorn local_llm_api:app"
pkill -f "python bot.py"

# Запускаем LLM API в фоне
nohup uvicorn local_llm_api:app --host 0.0.0.0 --port 8000 > llm.log 2>&1 &
echo "LLM API запущен на порту 8000"

# Ждем немного для запуска API
sleep 3

# Запускаем бота в фоне
nohup python bot.py > bot.log 2>&1 &
echo "Бот запущен"

# Показываем статус
echo "Процессы запущены:"
echo "LLM API PID: $(pgrep -f 'uvicorn local_llm_api:app')"
echo "Bot PID: $(pgrep -f 'python bot.py')"
echo ""
echo "Логи:"
echo "LLM API: tail -f llm.log"
echo "Bot: tail -f bot.log" 