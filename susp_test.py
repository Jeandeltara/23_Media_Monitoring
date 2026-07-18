import os
import re
import time
import json
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
from curl_cffi import requests
from playwright.sync_api import sync_playwright


# ============================================================================
# VARIABLES
# ============================================================================

keywords_list = [r'\bрівн\w*']

# Время за последние 7 дней для теста (можно изменить)
end_time = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
start_time = end_time - timedelta(days=7)

suspilne_links = []
suspilne_report_brief = []
suspilne_report_for_analysis = []
suspilne_err = []


# ============================================================================
# REQUEST HELPER
# ============================================================================

def fetch_with_retry(url: str, headers: dict, timeout: int = 30, max_retries: int = 2):
    """Fetch URL with retry logic."""
    timeouts = [timeout, 100]
    
    for attempt in range(min(max_retries, len(timeouts))):
        current_timeout = timeouts[attempt]
        try:
            if attempt > 0:
                print(f"🔄 Retry {attempt+1}/{max_retries} for {url[:60]}... with {current_timeout}s timeout")
            response = requests.get(url, headers=headers, timeout=current_timeout, impersonate="chrome")
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2)
    raise Exception(f"All attempts failed for {url}")


# ============================================================================
# SUSPILNE PARSING
# ============================================================================

def parse_suspilne_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from suspilne.media using Playwright (for JavaScript content).
    """
    global suspilne_err
    
    collected_links = []
    page = 1
    
    print(f"🔍 Starting suspilne.media parser")
    print(f"   Time range: {start_time} - {end_time}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page_playwright = context.new_page()
        
        while True:
            url = f"https://suspilne.media/rivne/latest/?page={page}"
            try:
                print(f"   Loading page {page}...")
                page_playwright.goto(url, timeout=30000, wait_until="networkidle")
                
                # Wait for content to load
                try:
                    page_playwright.wait_for_selector("article.c-article-card", timeout=10000)
                except:
                    print(f"   ⚠️ No articles found on page {page} (selector not found)")
                    break
                
                articles = page_playwright.locator("article.c-article-card").all()
                print(f"   Found {len(articles)} articles on page {page}")
                
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
                                full_url = "https://suspilne.media" + full_url
                            
                            if full_url not in collected_links:
                                collected_links.append(full_url)
                                print(f"      ✅ Added: {full_url}")
                    except Exception as e:
                        suspilne_err.append(f"parse_suspilne_site: article error - {e}")
                        continue
                
                if found_older:
                    print(f"   Found articles older than start_time, stopping")
                    break
                
                page += 1
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"parse_suspilne_site: page {page} - {type(e).__name__}: {e}"
                suspilne_err.append(error_msg)
                print(f"   ❌ {error_msg}")
                break
        
        browser.close()
    
    print(f"   Total links collected: {len(collected_links)}")
    return collected_links


def parse_suspilne_article(url: str, keywords: List[str]):
    """
    Parse a single article from suspilne.media.
    """
    global suspilne_err, suspilne_report_brief, suspilne_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"   Parsing article: {url[:80]}...")
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
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
            print(f"      ✅ Found keywords: {found_keywords}")
        
    except Exception as e:
        error_msg = f"parse_suspilne_article: {url} - {type(e).__name__}: {e}"
        suspilne_err.append(error_msg)
        print(f"      ❌ {error_msg}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 70)
    print("🎯 SUSPILNE PARSER (Standalone)")
    print("=" * 70)
    print(f"Start time: {start_time}")
    print(f"End time:   {end_time}")
    print(f"Keywords:   {keywords_list}")
    print("=" * 70)
    
    # Collect links
    print("\n📡 Collecting links from suspilne.media...")
    suspilne_links = parse_suspilne_site(start_time, end_time)
    
    if not suspilne_links:
        print("   ⚠️ No links found!")
        suspilne_err.append("No links found on suspilne.media")
    
    # Parse articles
    print(f"\n📝 Parsing {len(suspilne_links)} articles...")
    for i, url in enumerate(suspilne_links, 1):
        print(f"   [{i}/{len(suspilne_links)}]")
        parse_suspilne_article(url, keywords_list)
        time.sleep(1)
    
    # Build reports
    print("\n📊 Building reports...")
    
    # Brief report
    brief_report = f"{end_time.strftime('%d.%m')}\n"
    if suspilne_report_brief:
        brief_report += "Суспільне Рівне\n"
        for item in suspilne_report_brief:
            brief_report += f"{item['title']}\n"
            brief_report += f"{item['link']}\n"
    else:
        brief_report += "Публікації у медіа відсутні\n"
    
    # Full report
    full_report = f"{end_time.strftime('%d.%m')}\n"
    if suspilne_report_for_analysis:
        full_report += "Суспільне Рівне\n"
        for item in suspilne_report_for_analysis:
            full_report += "\n\n"
            full_report += f"{item['title']}\n"
            full_report += f"{item['link']}\n"
            full_report += f"{item['text']}\n"
    else:
        full_report += "Публікації у медіа відсутні\n"
    
    # Error report
    error_report = f"{end_time.strftime('%d.%m')}\n"
    if suspilne_err:
        error_report += "Суспільне Рівне\n"
        for error in suspilne_err:
            error_report += f"{error}\n"
    else:
        error_report += "Помилок не зафіксовано\n"
    
    # Save reports
    print("\n💾 Saving reports...")
    
    # Check errors
    error_text = str(error_report) if error_report else ""
    has_errors = len(error_text.strip()) > 10
    warning = "-- Увага! під час обробки зафіксовані помилки. Ймовірно результати не повні.\n\n"
    
    full_content = '\n'.join(full_report) if isinstance(full_report, list) else str(full_report)
    brief_content = '\n'.join(brief_report) if isinstance(brief_report, list) else str(brief_report)
    
    with open('suspilne_full_report.txt', 'w', encoding='utf-8') as f:
        f.write((warning if has_errors else '') + full_content)
    
    with open('suspilne_brief_report.txt', 'w', encoding='utf-8') as f:
        f.write((warning if has_errors else '') + brief_content)
    
    with open('suspilne_error_report.txt', 'w', encoding='utf-8') as f:
        f.write(error_text if error_text else "No errors recorded")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 RESULTS SUMMARY")
    print("=" * 70)
    print(f"Links found:       {len(suspilne_links)}")
    print(f"Brief entries:     {len(suspilne_report_brief)}")
    print(f"Analysis entries:  {len(suspilne_report_for_analysis)}")
    print(f"Errors:            {len(suspilne_err)}")
    print("=" * 70)
    print(f"✅ Reports saved at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if has_errors:
        print("⚠️ WARNING: Errors were recorded during processing")
        print("   Check suspilne_error_report.txt for details")


if __name__ == "__main__":
    main()
