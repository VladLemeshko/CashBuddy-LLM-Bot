from fastapi import FastAPI, Request
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

MODEL_NAME = "yandex/YandexGPT-5-Lite-8B-instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="cuda",  # или "cpu" если нет GPU
    torch_dtype="auto",
)

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    user_history = data.get("user_history", "")
    user_goals = data.get("user_goals", "")
    question = data.get("question", "")
    messages = [
        {"role": "system", "content": (
            "Ты — дружелюбный, заботливый и мотивирующий финансовый ассистент. "
            "Отвечай развернуто, с примерами, объясняй свои советы простым языком, поддерживай пользователя, используй эмодзи для дружелюбия. "
            "Не ограничивайся одним предложением. Не повторяй вопрос."
        )}
    ]
    if user_history:
        messages.append({"role": "user", "content": f"История финансов пользователя:\n{user_history}"})
    if user_goals:
        messages.append({"role": "user", "content": f"Финансовые цели пользователя:\n{user_goals}"})
    messages.append({"role": "user", "content": (
        f"{question}\n"
        "Пиши развернуто, с примерами, объясняй свои советы, используй эмодзи, поддерживай пользователя, не ограничивайся одним предложением."
    )})
    input_ids = tokenizer.apply_chat_template(messages, tokenize=True, return_tensors="pt").to(model.device)
    outputs = model.generate(input_ids, max_new_tokens=768, pad_token_id=tokenizer.eos_token_id)
    answer = tokenizer.decode(outputs[0][input_ids.size(1):], skip_special_tokens=True)
    return {"answer": answer}