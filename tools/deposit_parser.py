import re
import pandas as pd

HTML_PATH = "sravni_vklady_static.html"

def get_best_deposits():
    with open(HTML_PATH, "r", encoding="utf-8") as file:
        html_content = file.read()
    bank_pattern = r'"bankFullName":"([^"]+)"'
    profit_pattern = r'"Доходность","displayValue":"([^"]+)"'
    term_pattern = r'"Срок","displayValue":"([^"]+)"'
    amount_pattern = r'"Сумма","displayValue":"([^"]+)"'
    deposits = re.split(r'(?=\{"searchResultId")', html_content)[1:]
    data = []
    for deposit in deposits:
        bank_match = re.search(bank_pattern, deposit)
        profit_match = re.search(profit_pattern, deposit)
        term_match = re.search(term_pattern, deposit)
        amount_match = re.search(amount_pattern, deposit)
        if bank_match and profit_match and term_match and amount_match:
            data.append({
                "Банк": bank_match.group(1),
                "Доходность": profit_match.group(1),
                "Срок": term_match.group(1),
                "Мин. сумма": amount_match.group(1)
            })
    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=["Банк"], keep="first")
    return df.to_dict(orient="records") 