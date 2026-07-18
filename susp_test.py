import os
import re
import time
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
from curl_cffi import requests
from playwright.sync_api import sync_playwright  # <-- ИМПОРТ ДЛЯ PLAYWRIGHT


# ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
suspilne_links = []
suspilne_report_brief = []
suspilne_report_for_analysis = []
suspilne_err = []


def parse_suspilne_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from suspilne.media using Playwright.
    """
    global suspilne_err
    
    base_url = "https://suspilne.media"
    collected_links = []
    page = 1
    
    print("🔍 Starting suspilne.media with Playwright...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="uk-UA",
            timezone_id="Europe/Kiev",
        )
        
        # Дополнительно прячем автоматизацию
        page_playwright = context.new_page()
        page_playwright.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        while True:
            url = f"{base_url}/rivne/latest/?page={page}"
            try:
                print(f"   Loading page {page}...")
                
                # Идем на страницу
                response = page_playwright.goto(url, timeout=30000, wait_until="networkidle")
                
                # Проверяем статус
                if response and response.status != 200:
                    suspilne_err.append(f"Page {page}: HTTP {response.status}")
                    break
                
                # Ждем появления контента
                try:
                    page_playwright.wait_for_selector("article.c-article-card", timeout=10000)
                except:
                    # Если нет статей, проверяем наличие капчи
                    if page_playwright.locator("text=captcha").count() > 0 or \
                       page_playwright.locator("text=robot").count() > 0:
                        suspilne_err.append(f"Page {page}: BLOCKED - captcha or robot detection")
                        print("   ❌ Blocked!")
                        break
                    
                    # Может быть просто нет новостей
                    articles_locator = page_playwright.locator("article")
                    count = articles_locator.count()
                    print(f"   No 'c-article-card' found, but found {count} article tags")
                    
                    if count == 0:
                        # Сохраняем HTML для диагностики
                        html = page_playwright.content()
                        with open(f"suspilne_playwright_debug_{page}.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        break
                
                # Получаем статьи
                articles = page_playwright.locator("article.c-article-card").all()
                print(f"   Found {len(articles)} articles")
                
                if not articles:
                    break
                
                found_older = False
                
                for art in articles:
                    try:
                        time_tag = art.locator("time.time")
                        link_tag = art.locator("a.headline")
                        
                        if time_tag.count() == 0 or link_tag.count() == 0:
                            continue
                        
                        date_iso = time_tag.get_attribute("datetime")
                        news_date = datetime.fromisoformat(date_iso.split('+')[0])
                        
                        if news_date < start_time:
                            found_older = True
                            break
                        
                        if start_time <= news_date <= end_time:
                            full_url = link_tag.get_attribute("href")
                            if not full_url.startswith("http"):
                                full_url = base_url + full_url
                            
                            if full_url not in collected_links:
                                collected_links.append(full_url)
                    except Exception as e:
                        continue
                
                if found_older:
                    print(f"   Found older articles, stopping")
                    break
                
                page += 1
                time.sleep(1)
                
            except Exception as e:
                suspilne_err.append(f"parse_suspilne_site: page {page} - {type(e).__name__}: {e}")
                print(f"   ❌ {e}")
                break
        
        browser.close()
    
    print(f"   Total: {len(collected_links)} links")
    return collected_links


def parse_suspilne_article(url: str, keywords: List[str]):
    """
    Parse a single article from suspilne.media and search for keyword patterns.
    """
    global suspilne_err, suspilne_report_brief, suspilne_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            error_msg = f"parse_suspilne_article: {url} - HTTP {response.status_code}"
            suspilne_err.append(error_msg)
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h1')
        if not title_tag:
            title_tag = soup.find('h1', class_=re.compile(r'title'))
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        article = soup.find('article', class_='post-body')
        if not article:
            article = soup.find('article')
        if not article:
            error_msg = f"parse_suspilne_article: {url} - ARTICLE CONTAINER NOT FOUND"
            suspilne_err.append(error_msg)
            return
        
        content_container = article.find('div', class_=re.compile(r'c-article-content'))
        if not content_container:
            content_container = article
        
        content_copy = content_container.__copy__()
        
        for unwanted in content_copy.find_all(['div'], class_=re.compile(r'(share|social|ad|banner|promo|sharing|info-share)')):
            unwanted.decompose()
        for img in content_copy.find_all('img'):
            img.decompose()
        for embed in content_copy.find_all('div', {'data-embed': True}):
            embed.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            suspilne_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            suspilne_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_suspilne_article: {url} - {type(e).__name__}: {e}"
        suspilne_err.append(error_msg)


# ===== ЗАПУСК =====

if __name__ == "__main__":
    # Время за последние 7 дней
    end_time = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    start_time = end_time - timedelta(days=7)
    keywords_list = [r'\bрівн\w*']
    
    print("=" * 60)
    print("Запуск парсера Суспільного")
    print(f"Период: {start_time} - {end_time}")
    print("=" * 60)
    
    # Сбор ссылок
    suspilne_links = parse_suspilne_site(start_time, end_time)
    print(f"Найдено ссылок: {len(suspilne_links)}")
    
    # Парсинг статей
    for url in suspilne_links:
        parse_suspilne_article(url, keywords_list)
        time.sleep(1)
    
    print(f"Найдено статей с ключевыми словами: {len(suspilne_report_brief)}")
    print(f"Ошибок: {len(suspilne_err)}")
    
    # Формирование отчетов
    brief_report = f"{end_time.strftime('%d.%m')}\n"
    if suspilne_report_brief:
        brief_report += "Суспільне Рівне\n"
        for item in suspilne_report_brief:
            brief_report += f"{item['title']}\n{item['link']}\n"
    else:
        brief_report += "Публікації у медіа відсутні\n"
    
    full_report = f"{end_time.strftime('%d.%m')}\n"
    if suspilne_report_for_analysis:
        full_report += "Суспільне Рівне\n"
        for item in suspilne_report_for_analysis:
            full_report += f"\n\n{item['title']}\n{item['link']}\n{item['text']}\n"
    else:
        full_report += "Публікації у медіа відсутні\n"
    
    error_report = f"{end_time.strftime('%d.%m')}\n"
    if suspilne_err:
        error_report += "Суспільне Рівне\n"
        for error in suspilne_err:
            error_report += f"{error}\n"
    else:
        error_report += "Помилок не зафіксовано\n"
    
    # Сохранение
    has_errors = len(suspilne_err) > 0
    warning = "-- Увага! під час обробки зафіксовані помилки. Ймовірно результати не повні.\n\n"
    
    with open('suspilne_full_report.txt', 'w', encoding='utf-8') as f:
        f.write((warning if has_errors else '') + full_report)
    
    with open('suspilne_brief_report.txt', 'w', encoding='utf-8') as f:
        f.write((warning if has_errors else '') + brief_report)
    
    with open('suspilne_error_report.txt', 'w', encoding='utf-8') as f:
        f.write(error_report)
    
    print("\n✅ Файлы сохранены:")
    print("   - suspilne_full_report.txt")
    print("   - suspilne_brief_report.txt")
    print("   - suspilne_error_report.txt")
