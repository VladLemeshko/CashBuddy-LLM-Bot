#!/usr/bin/env python3

import re
import pandas as pd

HTML_PATH = "sravni_vklady_static.html"

def debug_deposits():
    with open(HTML_PATH, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    print(f"Размер HTML файла: {len(html_content)} символов")
    
    # Ищем паттерны
    bank_pattern = r'"bankFullName":"([^"]+)"'
    profit_pattern = r'"Доходность","displayValue":"([^"]+)"'
    term_pattern = r'"Срок","displayValue":"([^"]+)"'
    amount_pattern = r'"Сумма","displayValue":"([^"]+)"'
    
    # Проверяем количество совпадений
    banks = re.findall(bank_pattern, html_content)
    profits = re.findall(profit_pattern, html_content)
    terms = re.findall(term_pattern, html_content)
    amounts = re.findall(amount_pattern, html_content)
    
    print(f"Найдено банков: {len(banks)}")
    print(f"Найдено доходностей: {len(profits)}")
    print(f"Найдено сроков: {len(terms)}")
    print(f"Найдено сумм: {len(amounts)}")
    
    # Показываем первые несколько результатов
    if banks:
        print(f"Первые банки: {banks[:3]}")
    if profits:
        print(f"Первые доходности: {profits[:3]}")
    
    # Проверяем разделение на депозиты
    deposits = re.split(r'(?=\{"searchResultId")', html_content)[1:]
    print(f"Найдено депозитов: {len(deposits)}")
    
    if deposits:
        print(f"Первый депозит (первые 200 символов): {deposits[0][:200]}")

if __name__ == "__main__":
    debug_deposits() 