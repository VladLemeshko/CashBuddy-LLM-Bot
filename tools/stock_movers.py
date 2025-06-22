import yfinance as yf
import requests
from bs4 import BeautifulSoup

def get_top_us_movers(tickers, count=5):
    movers = []
    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="2d")
            if len(hist) < 2:
                continue
            change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
            movers.append((ticker_symbol, float(change)))
        except Exception as e:
            print(f"Ошибка при получении данных для {ticker_symbol}: {e}")
            continue
    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    return movers[:count]

# Заготовка для российских акций (можно доработать под конкретный источник)
def get_top_ru_movers(count=5):
    # Пример: парсинг https://www.moex.com/ или https://ru.investing.com/equities/russia
    # Здесь только заглушка:
    return [
        ("SBER", 2.1),
        ("GAZP", -1.5),
        ("LKOH", 1.8),
        ("YNDX", -2.3),
        ("TCSG", 3.2)
    ][:count]

if __name__ == "__main__":
    print("US movers:", get_top_us_movers(["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "SBUX"]))
    print("RU movers:", get_top_ru_movers()) 