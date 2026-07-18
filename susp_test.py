import os
import re
import time
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
from curl_cffi import requests


# ===== ВАШИ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
suspilne_links = []
suspilne_report_brief = []
suspilne_report_for_analysis = []
suspilne_err = []


# ===== SUSPILNE PARSING =====

def parse_suspilne_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from suspilne.media within a specified time range.
    With full response diagnostics.
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
    
    print("\n🔍 DIAGNOSTIC: Starting suspilne.media requests")
    
    while True:
        url = f"{base_url}/rivne/latest/?page={page}"
        try:
            print(f"\n📡 Requesting page {page}: {url}")
            
            # Используем curl_cffi с имитацией Chrome 120
            response = requests.get(
                url, 
                headers=headers, 
                timeout=30, 
                impersonate="chrome120"
            )
            
            # Детальная диагностика ответа
            print(f"   Status code: {response.status_code}")
            print(f"   Content length: {len(response.text)} bytes")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            
            # Проверка на блокировку
            text_lower = response.text.lower()
            if "captcha" in text_lower or "robot" in text_lower or "access denied" in text_lower:
                suspilne_err.append(f"Page {page}: BLOCKED - captcha or robot detection")
                print("   ⚠️  BLOCKED: captcha or robot detection")
                # Сохраняем HTML для анализа
                with open(f"suspilne_blocked_page_{page}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                break
            
            if response.status_code != 200:
                suspilne_err.append(f"Page {page}: HTTP {response.status_code}")
                print(f"   ❌ HTTP error: {response.status_code}")
                break
            
            # Если контент слишком маленький - подозрительно
            if len(response.text) < 5000:
                suspilne_err.append(f"Page {page}: suspiciously small content ({len(response.text)} bytes)")
                print(f"   ⚠️  Suspiciously small content, saving HTML for inspection")
                with open(f"suspilne_small_page_{page}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                # Продолжаем, возможно это просто нет статей
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Ищем статьи по вашему селектору
            articles = soup.find_all("article", class_=lambda x: x and "c-article-card" in x)
            print(f"   Found {len(articles)} articles with class 'c-article-card'")
            
            # Если не нашли, попробуем другие селекторы для диагностики
            if not articles:
                all_articles = soup.find_all("article")
                print(f"   All <article> tags on page: {len(all_articles)}")
                if all_articles:
                    # Посмотрим классы первых трёх
                    classes = [art.get("class") for art in all_articles[:3]]
                    print(f"   Sample classes: {classes}")
                
                # Сохраним HTML для диагностики
                if page <= 3:
                    with open(f"suspilne_debug_page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print(f"   💾 HTML saved to suspilne_debug_page_{page}.html")
            
            if not articles:
                # Если нет статей, возможно сайт вернул пустую страницу (нет новостей)
                # Проверим наличие какого-либо контента
                body_text = soup.find("body")
                if body_text:
                    body_len = len(body_text.get_text(strip=True))
                    print(f"   Body text length: {body_len} chars")
                    if body_len < 100:
                        suspilne_err.append(f"Page {page}: almost empty body, possible block")
                        break
                # Всё равно прерываем, так как статьи не найдены
                break
            
            # Обработка найденных статей (ваш оригинальный код)
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
                print(f"   Found articles older than start_time, stopping")
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_suspilne_site: page {page} - {type(e).__name__}: {e}"
            suspilne_err.append(error_msg)
            print(f"   ❌ Exception: {error_msg}")
            break
    
    print(f"\n📊 Diagnostic summary:")
    print(f"   Total collected links: {len(collected_links)}")
    print(f"   Errors logged: {len(suspilne_err)}")
    
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
