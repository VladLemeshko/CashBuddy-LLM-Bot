#!/bin/bash

# Запуск FastAPI-сервиса LLM в фоне
uvicorn local_llm_api:app --host 0.0.0.0 --port 8000 &
LLM_PID=$!

# Ждём, пока сервис поднимется (можно увеличить время при необходимости)
sleep 

# Запуск Telegram-бота
python bot.py

# После завершения бота останавливаем LLM-сервис
kill $LLM_PID 