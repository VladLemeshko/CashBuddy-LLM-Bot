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
    prompt = data["prompt"]
    input_ids = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**input_ids, max_new_tokens=512)
    answer = tokenizer.decode(outputs[0][input_ids["input_ids"].size(1):], skip_special_tokens=True)
    return {"answer": answer}