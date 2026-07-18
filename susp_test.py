import os
import re
import time
import random
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
from curl_cffi import requests


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
            # ❌ Убираем задержки! Собираем ссылки БЫСТРО
            # time.sleep(delay)
            
            print(f"   Requesting page {page}...")
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=30, 
                impersonate="chrome120"
            )
            
            print(f"   Status: {response.status_code}, Length: {len(response.text)}")
            
            if response.status_code != 200:
                if response.status_code == 403:
                    suspilne_err.append(f"Page {page}: BLOCKED (403)")
                    print("   ❌ Blocked (403)!")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article", class_=lambda x: x and "c-article-card" in x)
            print(f"   Found {len(articles)} articles")
            
            if not articles:
                if "captcha" in response.text.lower():
                    suspilne_err.append(f"Page {page}: CAPTCHA detected")
                    print("   ❌ CAPTCHA detected!")
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
            
            # ⚠️ Только маленькая задержка 0.5-1 секунда между страницами
            # Чтобы не выглядеть как DDoS
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            suspilne_err.append(f"parse_suspilne_site: page {page} - {type(e).__name__}: {e}")
            print(f"   ❌ {e}")
            break
    
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
        response = requests.get(url, headers=headers, timeout=15, impersonate="chrome120")
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
    
    # Парсинг статей с задержкой 3-6 секунд ПОСЛЕ каждой статьи
    for i, url in enumerate(suspilne_links, 1):
        print(f"\n📄 [{i}/{len(suspilne_links)}] Parsing article...")
        parse_suspilne_article(url, keywords_list)
        
        # Задержка после каждой статьи (кроме последней)
        if i < len(suspilne_links):
            delay = random.uniform(3, 6)
            print(f"   ⏰ Waiting {delay:.1f}s before next article...")
            time.sleep(delay)
    
    print(f"\nНайдено статей с ключевыми словами: {len(suspilne_report_brief)}")
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
