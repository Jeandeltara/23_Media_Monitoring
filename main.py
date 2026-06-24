import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser

# --- CONFIGURATION ---
# Keywords for content filtering (use regex or plain strings)
KEYWORDS_LIST = [r"23.{0,4} інженерно"]

def get_soup(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# --- PARSERS ---

def parse_rivnepost(start_time, end_time):
    found_urls = []
    page = 1
    while True:
        url = "https://rivnepost.rv.ua/category/news" if page == 1 else f"https://rivnepost.rv.ua/category/news/page/{page}/"
        soup = get_soup(url)
        if not soup: break
        articles = soup.select('div.list-item')
        if not articles: break
        
        stop = False
        for art in articles:
            time_tag = art.find("time")
            if time_tag and time_tag.get("datetime"):
                dt = parser.parse(time_tag["datetime"]).replace(tzinfo=None)
                if dt < start_time: stop = True; break
                if start_time <= dt < end_time: found_urls.append(art.find("a")["href"])
        if stop: break
        page += 1
    return found_urls

def parse_ogo(start_time, end_time):
    found_urls = []
    page = 1
    while True:
        url = "https://ogo.ua/rubrics/view/region" if page == 1 else f"https://ogo.ua/rubrics/view/region/page/{page}/"
        soup = get_soup(url)
        if not soup: break
        articles = soup.find_all("article")
        if not articles: break
        
        stop = False
        for art in articles:
            time_tag = art.find("time")
            if time_tag and time_tag.get("datetime"):
                dt = parser.parse(time_tag["datetime"]).replace(tzinfo=None)
                if dt < start_time: stop = True; break
                if start_time <= dt < end_time: found_urls.append(art.find("a")["href"])
        if stop: break
        page += 1
    return found_urls

def parse_7dniv(start_time, end_time):
    # Логика аналогична WordPress-структуре
    found_urls = []
    page = 1
    while True:
        url = "https://7dniv.rv.ua/news/" if page == 1 else f"https://7dniv.rv.ua/news/page/{page}/"
        soup = get_soup(url)
        if not soup: break
        articles = soup.find_all("div", class_="post-item") # Селектор может потребовать уточнения
        if not articles: break
        # ... (аналогичная логика с циклом и проверкой времени) ...
        page += 1
    return found_urls

# (Аналогично создаются функции для rivne1, itvmg, teza с учетом их специфических селекторов)

# --- FILTERING & REPORTING ---

def filter_results(urls, keywords, start_time, end_time):
    results = []
    for url in urls:
        # Здесь логика глубокого парсинга контента
        pass
    return results

def main():
    end_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(days=1)
    
    print("="*70)
    print("STARTING MEDIA MONITORING")
    print(f"Target interval: {start_time} to {end_time}")
    print("="*70)

    all_links = []
    # Call all parsers here
    # all_links.extend(parse_rivnepost(start_time, end_time))
    
    # Deduplication and filtering
    # ...
    
    # Reporting in Ukrainian
    print("\n" + "="*70)
    print("ЗВІТ МОНІТОРИНГУ ПРЕСИ")
    print("="*70)

if __name__ == "__main__":
    main()
