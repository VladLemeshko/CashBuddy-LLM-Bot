import re
import pandas as pd

HTML_PATH = "sravni_vklady_static.html"

def get_best_deposits():
    with open(HTML_PATH, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    # Ищем банки и доходности (эти данные мы видели в отладке)
    bank_pattern = r'"bankFullName":"([^"]+)"'
    profit_pattern = r'"Доходность","displayValue":"([^"]+)"'
    
    banks = re.findall(bank_pattern, html_content)
    profits = re.findall(profit_pattern, html_content)
    
    print(f"Найдено банков: {len(banks)}")
    print(f"Найдено доходностей: {len(profits)}")
    
    # Создаем депозиты из найденных данных
    deposits = []
    max_len = min(len(banks), len(profits))
    
    for i in range(max_len):
        deposit = {
            'Банк': banks[i],
            'Доходность': profits[i],
            'Срок': '3-6 мес',  # Примерный срок
            'Мин. сумма': 'от 10 000 ₽'  # Примерная сумма
        }
        deposits.append(deposit)
    
    # Удаляем дубликаты по банку
    unique_deposits = []
    seen_banks = set()
    for deposit in deposits:
        if deposit['Банк'] not in seen_banks:
            unique_deposits.append(deposit)
            seen_banks.add(deposit['Банк'])
    
    # Сортируем по доходности (убираем % и сортируем по числу)
    def sort_key(deposit):
        try:
            return float(deposit['Доходность'].replace(' %', '').replace(',', '.'))
        except:
            return 0
    
    unique_deposits.sort(key=sort_key, reverse=True)
    
    return unique_deposits[:10]  # Возвращаем топ-10 