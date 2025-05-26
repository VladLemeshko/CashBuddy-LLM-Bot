import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv(".env")

LOCAL_LLM_URL = "http://localhost:8000/generate"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "meta-llama/Llama-2-7b-chat-hf"

async def ask_agent(user_history: str, user_goals: str, question: str) -> str:
    prompt = (
        "Ты — персональный финансовый агент. Вот история пользователя (доходы, расходы):\n"
        f"{user_history}\n"
        "Вот его финансовые цели:\n"
        f"{user_goals}\n"
        f"Вопрос пользователя: {question}\n"
        "Ответь максимально полезно, персонализировано и понятно."
    )
    data = {"prompt": prompt}
    logger.info("[LLM] PROMPT отправлен в локальный LLM:\n%s", prompt)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(LOCAL_LLM_URL, json=data, timeout=300)
            logger.info("[LLM] Статус ответа: %s", response.status_code)
            logger.info("[LLM] Тело ответа: %s", response.text)
            if response.status_code == 200:
                result = response.json()
                return result.get("answer", "Нет ответа от агента.").strip()
            else:
                logger.error("[LLM] Ошибка ответа: %s %s", response.status_code, response.text)
    except Exception as e:
        logger.exception("[LLM] Исключение при запросе к LLM: %s", e)
    return "Извините, не удалось получить ответ от агента. Попробуйте позже."
