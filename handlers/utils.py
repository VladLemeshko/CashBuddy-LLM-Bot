import re

def beautify_answer(text: str) -> str:
    # Удаляем жирный (**текст** -> текст)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    # Заменяем нумерацию на эмодзи (1. -> 🔹, 2. -> 🔸, 3. -> 🔹 ...)
    lines = text.splitlines()
    emoji_cycle = ["🔹", "🔸", "🔷", "🔶", "🟢", "🟣", "🟠", "🔺", "🔻", "🔵"]
    for i, line in enumerate(lines):
        if re.match(r"^\d+\. ", line):
            emoji = emoji_cycle[i % len(emoji_cycle)]
            lines[i] = re.sub(r"^\d+\. ", f"{emoji} ", line)
    return "\n".join(lines) 