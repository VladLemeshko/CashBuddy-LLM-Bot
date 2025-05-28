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
        {"role": "system", "content": "Ты — персональный финансовый ассистент. Ты даёшь только полезные, конкретные и персонализированные советы по финансам. Не повторяй вопрос, не пиши лишних пояснений."}
    ]
    if user_history:
        messages.append({"role": "user", "content": f"История финансов пользователя:\n{user_history}"})
    if user_goals:
        messages.append({"role": "user", "content": f"Финансовые цели пользователя:\n{user_goals}"})
    messages.append({"role": "user", "content": f"{question}\nОтветь только по существу, не повторяй вопрос, не пиши лишних пояснений и инструкций. Дай конкретный, полезный и персонализированный совет. Если вопрос — просто дай ответ."})
    input_ids = tokenizer.apply_chat_template(messages, tokenize=True, return_tensors="pt").to(model.device)
    outputs = model.generate(input_ids, max_new_tokens=512, pad_token_id=tokenizer.eos_token_id)
    answer = tokenizer.decode(outputs[0][input_ids.size(1):], skip_special_tokens=True)
    return {"answer": answer}