from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def fetch_sravni_vklady_html(save_path="sravni_vklady_static.html"):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    url = "https://www.sravni.ru/vklady/top/"
    try:
        driver.get(url)
        time.sleep(3)
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(driver.page_source)
        print(f"HTML сохранён в '{save_path}'")
    finally:
        driver.quit() 