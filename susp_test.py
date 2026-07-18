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
    Parse news articles from suspilne.media within a specified time range.
    """
    global suspilne_err
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    base_url = "https://suspilne.media"
    collected_links = []
    page = 1
    
    print("🔍 Starting suspilne.media with curl_cffi...")
    
    while True:
        url = f"{base_url}/rivne/latest/?page={page}"
        try:
            print(f"   Requesting page {page}...")
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=30, 
                impersonate="chrome120"
            )
            
            print(f"   Status: {response.status_code}, Length: {len(response.text)}")
            
            if response.status_code != 200:
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article", class_=lambda x: x and "c-article-card" in x)
            print(f"   Found {len(articles)} articles")
            
            if not articles:
                # Если не нашли статьи, возможно капча
                if "captcha" in response.text.lower():
                    suspilne_err.append(f"Page {page}: CAPTCHA detected")
                    print("   ❌ CAPTCHA detected!")
                    break
                break
            
            found_older = False
            
            for art in articles:
                time_tag = art.find("time", class_=lambda x: x and "time" in x)
                link_tag = art.find("a", class_=lambda x: x and "headline" in x)
                
                if not time_tag or not link_tag:
                    continue
                
                date_iso = time_tag["datetime"]
                news_date = datetime.fromisoformat(date_iso.split('+')[0])
                
                if news_date < start_time:
                    found_older = True
                    break
                
                if start_time <= news_date <= end_time:
                    full_url = link_tag["href"]
                    if not full_url.startswith("http"):
                        full_url = base_url + full_url
                    
                    if full_url not in collected_links:
                        collected_links.append(full_url)
            
            if found_older:
                print(f"   Found older articles, stopping")
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            suspilne_err.append(f"parse_suspilne_site: page {page} - {type(e).__name__}: {e}")
            print(f"   ❌ {e}")
            break
    
    print(f"   Total: {len(collected_links)} links")
    return collected_links


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
