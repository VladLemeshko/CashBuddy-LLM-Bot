import requests

def get_crypto_rates():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd,rub"
    }
    response = requests.get(url, params=params)
    data = response.json()
    result = []
    for sym, name in [("bitcoin", "BTC"), ("ethereum", "ETH")]:
        if sym in data:
            result.append({
                "name": name,
                "usd": data[sym].get("usd"),
                "rub": data[sym].get("rub")
            })
    return result

if __name__ == "__main__":
    print(get_crypto_rates()) 