import os
import re
import time
import random
import asyncio
from datetime import datetime, timedelta, date, time as dt_time
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from dateutil import parser
from curl_cffi import requests
import requests as simple_requests
from playwright.sync_api import sync_playwright


# ============================================================================
# REQUEST HELPER WITH RETRY
# ============================================================================

def fetch_with_retry(url: str, headers: dict, timeout: int = 30, max_retries: int = 2) -> requests.Response:
    """
    Fetch URL with retry logic. First attempt: 30s timeout, second: 100s timeout.
    
    Args:
        url: URL to fetch
        headers: Request headers
        timeout: Initial timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 2)
    
    Returns:
        requests.Response: Response object
    
    Raises:
        Exception: If all attempts fail
    """
    timeouts = [timeout, 100]  # First: 30s, Second: 100s
    
    for attempt in range(min(max_retries, len(timeouts))):
        current_timeout = timeouts[attempt]
        
        try:
            if attempt > 0:
                print(f"🔄 Retry {attempt+1}/{max_retries} for {url[:60]}... with {current_timeout}s timeout")
            
            response = requests.get(url, headers=headers, timeout=current_timeout)
            response.raise_for_status()
            return response
            
        except requests.Timeout:
            if attempt == max_retries - 1:
                raise Exception(f"Timeout after {max_retries} attempts for {url}")
            time.sleep(2)
            continue
        
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2)
            continue
    
    raise Exception(f"All {max_retries} attempts failed for {url}")


# ============================================================================
# VARIABLES
# ============================================================================

keywords_list = [r'\bрівн\w*']
#keywords_list = [r"23(?:-й|-го|-му|й)?[\s-](?:окрем\S*\s)?інженерн[^\s]*|А0451"]
end_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
start_time = end_time - timedelta(days=1)
all_links = []

#RAYON_VARIABLES
links_from_rayon = []
rayon_report_brief = []
rayon_report_for_analysis = []
rayon_err = [] 
rayon_sites = ["https://rivne.rayon.in.ua", "https://dubno.rayon.in.ua"]

#CHARIVNE_VARIABLES
links_from_charivne = []
charivne_report_brief = []
charivne_report_for_analysis = []
charivne_err = []

#RADIOTREK_VARIABLES
links_from_radiotrek = []
radiotrek_report_brief = []
radiotrek_report_for_analysis = []
radiotrek_err = []

#SUSPILNE_VARIABLES
links_from_suspilne = []
suspilne_report_brief = []
suspilne_report_for_analysis = []
suspilne_err = []

#VSE_RV_VARIABLES
links_from_vse_rv = []
vse_rv_report_brief = []
vse_rv_report_for_analysis = []
vse_rv_err = []

#RIVNEPOST_VARIABLES
links_from_rivnepost = []
rivnepost_report_brief = []
rivnepost_report_for_analysis = []
rivnepost_err = []

#OGO_VARIABLES
links_from_ogo = []
ogo_report_brief = []
ogo_report_for_analysis = []
ogo_err = []

#7DNIV_VARIABLES
links_from_sevendniv = []
sevendniv_report_brief = []
sevendniv_report_for_analysis = []
sevendniv_err = []

#RIVNEMEDIA_VARIABLES
links_from_rivnemedia = []
rivnemedia_report_brief = []
rivnemedia_report_for_analysis = []
rivnemedia_err = []

#HORYN_VARIABLES
links_from_horyn = []
horyn_report_brief = []
horyn_report_for_analysis = []
horyn_err = []

#RIVNE1_VARIABLES
links_from_rivne1 = []
rivne1_report_brief = []
rivne1_report_for_analysis = []
rivne1_err = []

#RP_RV_UA_VARIABLES
links_from_rp_rv_ua = []
rp_rv_ua_report_brief = []
rp_rv_ua_report_for_analysis = []
rp_rv_ua_err = []

#ITVMG_VARIABLES
links_from_itvmg = []
itvmg_report_brief = []
itvmg_report_for_analysis = []
itvmg_err = []

media_names = {"rayon" :"Район.in.ua", 
               "charivne": "ЧаРівне.інфо", 
               "radiotrek": "Радіо ТРЕК", 
               "suspilne": "Суспільне Рівне", 
               "vse_rv": "Все Рівне", 
               "rivnepost": "Рівне вечірнє", 
               "ogo": "OGO.ua", 
               "sevendniv": "Сім днів", 
               "rivnemedia": "Рівне Медіа", 
               "horyn": "Горинь.info", 
               "rivne1": "Рівне 1", 
               "rp_rv_ua": "Рівненська правда", 
               "itvmg": "ITV"}

MAX_WORKERS = 5


# ============================================================================
# FUNCTIONS
# ============================================================================

def run_rayon():
    global links_from_rayon, rayon_report_brief, rayon_report_for_analysis, rayon_err
    for site in rayon_sites:
        collected, brief, analysis = parse_rayon_articles(site, start_time, end_time, keywords_list)


def run_charivne():
    global links_from_charivne, charivne_report_brief, charivne_report_for_analysis, charivne_err
    links_from_charivne = parse_charivne_site(start_time, end_time)
    for url in links_from_charivne:
        parse_charivne_article(url, keywords_list)
        time.sleep(1)


def run_radiotrek():
    global links_from_radiotrek, radiotrek_report_brief, radiotrek_report_for_analysis, radiotrek_err
    links_from_radiotrek = parse_radiotrek_site(start_time, end_time)
    for url in links_from_radiotrek:
        parse_radiotrek_article(url, keywords_list)
        time.sleep(1)


def run_suspilne():
    global links_from_suspilne, suspilne_report_brief, suspilne_report_for_analysis, suspilne_err
    links_from_suspilne = parse_suspilne_site(start_time, end_time)
    for url in links_from_suspilne:
        parse_suspilne_article(url, keywords_list)
        time.sleep(1)


def run_vse_rv():
    global links_from_vse_rv, vse_rv_report_brief, vse_rv_report_for_analysis, vse_rv_err
    links_from_vse_rv = parse_vse_rv_site(start_time, end_time)
    for url in links_from_vse_rv:
        parse_vse_rv_article(url, keywords_list)
        time.sleep(1)


def run_rivnepost():
    global links_from_rivnepost, rivnepost_report_brief, rivnepost_report_for_analysis, rivnepost_err
    links_from_rivnepost = parse_rivnepost_site(start_time, end_time)
    for url in links_from_rivnepost:
        parse_rivnepost_article(url, keywords_list)
        time.sleep(1)


def run_ogo():
    global links_from_ogo, ogo_report_brief, ogo_report_for_analysis, ogo_err
    links_from_ogo = parse_ogo_site(start_time, end_time)
    for url in links_from_ogo:
        parse_ogo_article(url, keywords_list)
        time.sleep(1)


def run_sevendniv():
    global links_from_sevendniv, sevendniv_report_brief, sevendniv_report_for_analysis, sevendniv_err
    parse_7dniv(start_time, end_time, keywords_list)


def run_rivnemedia():
    global links_from_rivnemedia, rivnemedia_report_brief, rivnemedia_report_for_analysis, rivnemedia_err
    links_from_rivnemedia = parse_rivnemedia_sitemap(start_time, end_time)
    for url in links_from_rivnemedia:
        parse_rivnemedia_article(url, keywords_list)
        time.sleep(1)


def run_horyn():
    global links_from_horyn, horyn_report_brief, horyn_report_for_analysis, horyn_err
    links_from_horyn = get_horyn_news(start_time, end_time)
    for url in links_from_horyn:
        parse_horyn_article(url, keywords_list)
        time.sleep(1)


def run_rivne1():
    global links_from_rivne1, rivne1_report_brief, rivne1_report_for_analysis, rivne1_err
    links_from_rivne1 = parse_rivne1_site(start_time, end_time)
    for url in links_from_rivne1:
        parse_rivne1_article(url, keywords_list)
        time.sleep(1)


def run_rp_rv_ua():
    global links_from_rp_rv_ua, rp_rv_ua_report_brief, rp_rv_ua_report_for_analysis, rp_rv_ua_err
    links_from_rp_rv_ua = parse_rp_rv_ua(start_time, end_time)
    for url in links_from_rp_rv_ua:
        parse_rp_rv_ua_article(url, keywords_list)
        time.sleep(1)


def run_itvmg():
    global links_from_itvmg, itvmg_report_brief, itvmg_report_for_analysis, itvmg_err
    links_from_itvmg = parse_itvmg_site(start_time, end_time)
    for url in links_from_itvmg:
        parse_itvmg_article(url, keywords_list)
        time.sleep(1)

tasks = [
    run_rayon,
    run_charivne,
    run_radiotrek,
    run_suspilne,
    run_vse_rv,
    run_rivnepost,
    run_ogo,
    run_sevendniv,
    run_rivnemedia,
    run_horyn,
    run_rivne1,
    run_rp_rv_ua,
    run_itvmg
]


# ============================================================================
# RAYON PARSING
# ============================================================================

def parse_rayon_articles(base_url, start_time, end_time, keywords):
    """
    Parse news articles from rayon.in.ua subdomains AND analyze their content.
    
    Stage 1 - Collection Phase:
        1. Iterates through paginated news listings from the rayon site
        2. Extracts publication dates from newsCard elements
        3. Collects only articles published within [start_time, end_time]
        4. Stops when encountering an article older than start_time
    
    Stage 2 - Analysis Phase:
        5. Fetches each article with retry logic and extended timeout
        6. Extracts title and main content from articleContent container
        7. Removes metadata elements (info, date, author, social, share, time, button)
        8. Searches for keyword patterns in full text
        9. Appends matches to global reports
    
    Args:
        base_url (str): Base URL of the rayon site
        start_time (datetime): Start of time range (inclusive)
        end_time (datetime): End of time range (inclusive)
        keywords (list): List of regex patterns to search for
    
    Returns:
        tuple: (collected_links, brief_reports, analysis_reports)
    """
    global rayon_err, rayon_report_brief, rayon_report_for_analysis, links_from_rayon
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    collected_links = []
    page = 1
    
    while True:
        target_url = f"{base_url.rstrip('/')}/news?page={page}"
        try:
            response = fetch_with_retry(target_url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("a", class_="newsCard")
            
            if not cards:
                break
                
            news_time = None
            for card in cards:
                time_tag = card.find("time", class_="newsCard__time")
                if not time_tag:
                    continue
                
                date_str = time_tag.get_text(strip=True)
                try:
                    news_time = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
                except ValueError as e:
                    rayon_err.append(f"Date parsing error '{date_str}': {e} - {base_url}")
                    continue
                
                if news_time < start_time:
                    break
                
                if news_time <= end_time:
                    link = card.get("href")
                    if link.startswith("/"):
                        link = base_url.rstrip('/') + link
                        
                    if link not in collected_links:
                        collected_links.append(link)
            
            if news_time and news_time < start_time:
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            rayon_err.append(f"Error on page {page}: {type(e).__name__} - {e} - {base_url}")
            break
    
    links_from_rayon.extend(collected_links)

    
    # ===== RAYON ARTICLES =====

    for url in collected_links:
        success = False
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Fetch article with extended timeout and retry
                response = fetch_with_retry(url, headers, timeout=30)
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                container = soup.find('div', class_='articleContent')
                if not container:
                    rayon_err.append(f"Container not found: {url}")
                    break
                
                title_tag = container.find('h1', class_='articleContent__title')
                title = title_tag.get_text(strip=True) if title_tag else "No title"
                
                content_copy = container.__copy__()
                header_to_remove = content_copy.find('h1', class_='articleContent__title')
                if header_to_remove:
                    header_to_remove.decompose()
                
                for unwanted in content_copy.find_all(['div', 'span'], class_=re.compile(r'(info|date|author|social|share|time|button)')):
                    unwanted.decompose()
                
                text = content_copy.get_text(separator=' ', strip=True)
                text = ' '.join(text.split())
                full_text = title + " " + text
                
                found_keywords = []
                for pattern in keywords:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        found_keywords.append(pattern)
                
                if found_keywords:
                    rayon_report_brief.append({
                        'title': title,
                        'link': url,
                        'keywords': found_keywords
                    })
                    
                    rayon_report_for_analysis.append({
                        'title': title,
                        'link': url,
                        'text': text,
                        'keywords': found_keywords
                    })
                
                success = True
                break  # Success, exit retry loop
                
            except Exception as e:
                wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                rayon_err.append(f"Error (attempt {attempt + 1}/{max_retries}) for {url}: {type(e).__name__}")
                time.sleep(wait_time)
        
        if not success:
            rayon_err.append(f"Failed to process {url} after {max_retries} attempts")
        
        time.sleep(2)  # Increased delay between requests
    
    return collected_links, rayon_report_brief, rayon_report_for_analysis


# ============================================================================
# CHARIVNE PARSING
# ============================================================================

def parse_charivne_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from charivne.info within a specified time range.
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global charivne_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://charivne.info"
    collected_links = []
    page = 1

    while True:
        url = f"{base_url}/category/novini-rivnoho?page={page}"
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            news_items = soup.find_all("div", class_="entry-header")
            
            if not news_items:
                break
                
            found_older = False
            
            for item in news_items:
                link_tag = item.find("a", class_="entry-title-link")
                if not link_tag:
                    continue
                
                time_tag = item.find("time", class_="published")
                if not time_tag:
                    continue
                
                date_str = time_tag.get_text(strip=True)
                news_date = datetime.strptime(date_str, "%d %m %Y, %H:%M")
                
                if news_date < start_time:
                    found_older = True
                    break
                
                if start_time <= news_date <= end_time:
                    full_url = link_tag["href"]
                    if full_url not in collected_links:
                        collected_links.append(full_url)
            
            if found_older:
                break
                
            page += 1
            time.sleep(1.5)
            
        except Exception as e:
            error_msg = f"parse_charivne_site: page {page} - {type(e).__name__}: {e}"
            charivne_err.append(error_msg)
            break
            
    return collected_links


def parse_charivne_article(url: str, keywords: List[str]):
    """
    Parse a single article from charivne.info and search for keyword patterns.
    Results are appended to global charivne_report_brief and charivne_report_for_analysis.
    """
    global charivne_err, charivne_report_brief, charivne_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article', class_='blog-post')
        
        if not article:
            error_msg = f"parse_charivne_article: {url} - ARTICLE CONTAINER NOT FOUND"
            charivne_err.append(error_msg)
            return
        
        title_tag = article.find('h1', class_='post-title')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_container = article.find('div', class_='post-body', id='post-body')
        if not content_container:
            error_msg = f"parse_charivne_article: {url} - CONTENT CONTAINER NOT FOUND"
            charivne_err.append(error_msg)
            return
        
        content_copy = content_container.__copy__()
        
        for img in content_copy.find_all('img'):
            img.decompose()
        
        for separator in content_copy.find_all('div', class_='separator'):
            if not separator.get_text(strip=True):
                separator.decompose()
            else:
                for img in separator.find_all('img'):
                    img.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            charivne_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            charivne_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_charivne_article: {url} - {type(e).__name__}: {e}"
        charivne_err.append(error_msg)


# ============================================================================
# RADIOTREK PARSING
# ============================================================================

def parse_radiotrek_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from radiotrek.rv.ua within a specified time range.
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global radiotrek_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://radiotrek.rv.ua"
    collected_links = []
    
    offset = 0

    while True:
        url = f"{base_url}/news/?st={offset}" if offset > 0 else f"{base_url}/news/"
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            articles = soup.find_all("article")
            if not articles:
                break
                
            found_older = False
            
            for article in articles:
                time_tag = article.find("time")
                link_tag = article.find("h3").find("a") if article.find("h3") else None
                
                if not time_tag or not link_tag:
                    continue
                
                date_str = time_tag["datetime"]
                news_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                
                if news_date < start_time:
                    found_older = True
                    break
                
                if start_time <= news_date <= end_time:
                    link = link_tag["href"]
                    full_url = base_url + link if link.startswith("/") else link
                    
                    if full_url not in collected_links:
                        collected_links.append(full_url)
            
            if found_older:
                break
                
            offset += 100
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_radiotrek_site: offset {offset} - {type(e).__name__}: {e}"
            radiotrek_err.append(error_msg)
            break
            
    return collected_links


def parse_radiotrek_article(url: str, keywords: List[str]):
    """
    Parse a single article from radiotrek.rv.ua and search for keyword patterns.
    Results are appended to global radiotrek_report_brief and radiotrek_report_for_analysis.
    """
    global radiotrek_err, radiotrek_report_brief, radiotrek_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        main = soup.find('main', id='page-main')
        
        if not main:
            error_msg = f"parse_radiotrek_article: {url} - MAIN CONTAINER NOT FOUND"
            radiotrek_err.append(error_msg)
            return
        
        title_tag = main.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_copy = main.__copy__()
        
        h1_tag = content_copy.find('h1')
        if h1_tag:
            h1_tag.decompose()
        
        time_tag = content_copy.find('time')
        if time_tag:
            time_tag.decompose()
        
        for embed in content_copy.find_all('div', {'data-embed': True}):
            embed.decompose()
        
        for ad in content_copy.find_all('p', class_='ad'):
            ad.decompose()
        for ad in content_copy.find_all('div', class_='ad'):
            ad.decompose()
        
        caption = content_copy.find('div', class_='post-caption')
        if caption:
            caption.decompose()
        
        tags = content_copy.find('div', class_='tags')
        if tags:
            tags.decompose()
        
        for img in content_copy.find_all('img', src=lambda x: x and 'register_view' in x):
            img.decompose()
        
        for share in content_copy.find_all('p', style=lambda x: x and 'text-align: center' in x):
            if share.find('a', class_='share-facebook'):
                share.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            radiotrek_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            radiotrek_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_radiotrek_article: {url} - {type(e).__name__}: {e}"
        radiotrek_err.append(error_msg)


# ============================================================================
# SUSPILNE PARSING
# ============================================================================

def parse_suspilne_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from suspilne.media within a specified time range.
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global suspilne_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://suspilne.media"
    collected_links = []
    page = 1
    
    while True:
        url = f"{base_url}/rivne/latest/?page={page}"
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article", class_=lambda x: x and "c-article-card" in x)
            
            if not articles:
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
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_suspilne_site: page {page} - {type(e).__name__}: {e}"
            suspilne_err.append(error_msg)
            break
            
    return collected_links


def parse_suspilne_article(url: str, keywords: List[str]):
    """
    Parse a single article from suspilne.media and search for keyword patterns.
    Results are appended to global suspilne_report_brief and suspilne_report_for_analysis.
    """
    global suspilne_err, suspilne_report_brief, suspilne_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
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
        
    except Exception as e:
        error_msg = f"parse_suspilne_article: {url} - {type(e).__name__}: {e}"
        suspilne_err.append(error_msg)


# ============================================================================
# VSE_RV PARSING
# ============================================================================

def parse_vse_rv_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from vse.rv.ua within a specified time range.
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global vse_rv_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://vse.rv.ua"
    collected_links = []
    page = 1

    while True:
        url = f"{base_url}/strichka.html?page={page}&per-page=9"
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("div", class_="article__item")
            
            if not articles:
                break
                
            found_older = False
            
            for art in articles:
                meta_date = art.find("meta", itemprop="datePublished dateModified")
                if not meta_date:
                    continue
                
                news_date = datetime.strptime(meta_date["content"], "%Y-%m-%d")
                
                if news_date < start_time:
                    found_older = True
                    break
                
                link_tag = art.find("a", class_="article__link")
                if start_time <= news_date <= end_time and link_tag:
                    full_url = base_url + link_tag["href"]
                    if full_url not in collected_links:
                        collected_links.append(full_url)
            
            if found_older:
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_vse_rv_site: page {page} - {type(e).__name__}: {e}"
            vse_rv_err.append(error_msg)
            break
            
    return collected_links


def parse_vse_rv_article(url: str, keywords: List[str]):
    """
    Parse a single article from vse.rv.ua and search for keyword patterns.
    Results are appended to global vse_rv_report_brief and vse_rv_report_for_analysis.
    """
    global vse_rv_err, vse_rv_report_brief, vse_rv_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_='section')
        
        if not container:
            error_msg = f"parse_vse_rv_article: {url} - CONTAINER NOT FOUND"
            vse_rv_err.append(error_msg)
            return
        
        title_tag = container.find('h1', class_='breadcrumbs__title')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_container = container.find('div', class_='article-inner__content', itemprop='articleBody')
        if not content_container:
            error_msg = f"parse_vse_rv_article: {url} - CONTENT CONTAINER NOT FOUND"
            vse_rv_err.append(error_msg)
            return
        
        content_copy = content_container.__copy__()
        
        for img in content_copy.find_all('img'):
            img.decompose()
        
        for ad in content_copy.find_all('div', class_='within-ads'):
            ad.decompose()
        for ad in content_copy.find_all('div', class_='video-adv-wrapper'):
            ad.decompose()
        
        for p in content_copy.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            vse_rv_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            vse_rv_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_vse_rv_article: {url} - {type(e).__name__}: {e}"
        vse_rv_err.append(error_msg)


# ============================================================================
# RIVNEPOST PARSING
# ============================================================================

def parse_rivnepost_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from rivnepost.rv.ua within a specified time range.
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global rivnepost_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://rivnepost.rv.ua"
    collected_links = []
    page = 1
    
    while True:
        url = f"{base_url}/category/news/page/{page}/" if page > 1 else f"{base_url}/category/news/"
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("div", class_="p-wrap")
            
            if not articles:
                break
                
            found_older = False
            
            for art in articles:
                time_tag = art.find("time", class_="published")
                link_tag = art.find("a", class_="p-flink")
                
                if not time_tag or not link_tag:
                    continue
                
                date_iso = time_tag["datetime"]
                news_date = datetime.fromisoformat(date_iso.split('+')[0])
                
                if news_date < start_time:
                    found_older = True
                    break
                
                if start_time <= news_date <= end_time:
                    full_url = link_tag["href"]
                    if full_url not in collected_links:
                        collected_links.append(full_url)
            
            if found_older:
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_rivnepost_site: page {page} - {type(e).__name__}: {e}"
            rivnepost_err.append(error_msg)
            break
            
    return collected_links


def parse_rivnepost_article(url: str, keywords: List[str]):
    """
    Parse a single article from rivnepost.rv.ua and search for keyword patterns.
    Results are appended to global rivnepost_report_brief and rivnepost_report_for_analysis.
    """
    global rivnepost_err, rivnepost_report_brief, rivnepost_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article', id=re.compile(r'post-\d+'))
        
        if not article:
            error_msg = f"parse_rivnepost_article: {url} - ARTICLE CONTAINER NOT FOUND"
            rivnepost_err.append(error_msg)
            return
        
        title_tag = article.find('h1', class_='s-title')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_container = article.find('div', class_='entry-content')
        if not content_container:
            error_msg = f"parse_rivnepost_article: {url} - CONTENT CONTAINER NOT FOUND"
            rivnepost_err.append(error_msg)
            return
        
        content_copy = content_container.__copy__()
        
        for toc in content_copy.find_all('div', class_='ruby-table-contents'):
            toc.decompose()
        
        for ad in content_copy.find_all('div', class_='inline-single-ad'):
            ad.decompose()
        for ad in content_copy.find_all('div', class_='ad-wrap'):
            ad.decompose()
        
        for script in content_copy.find_all('script'):
            script.decompose()
        for iframe in content_copy.find_all('iframe'):
            iframe.decompose()
        
        for p in content_copy.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            rivnepost_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            rivnepost_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_rivnepost_article: {url} - {type(e).__name__}: {e}"
        rivnepost_err.append(error_msg)


# ============================================================================
# OGO PARSING
# ============================================================================

def parse_ogo_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from ogo.ua within a specified time range.
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global ogo_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://ogo.ua"
    collected_links = []
    page = 1
    
    while True:
        url = f"{base_url}/rubrics/view/region/page/{page}/" if page > 1 else f"{base_url}/rubrics/view/region/"
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article", class_="post")
            
            if not articles:
                break
                
            found_older = False
            
            for art in articles:
                time_tag = art.find("time", class_="entry-date")
                link_tag = art.find("h2", class_="entry-title").find("a")
                
                if not time_tag or not link_tag:
                    continue
                
                date_iso = time_tag["datetime"]
                news_date = datetime.fromisoformat(date_iso.split('+')[0])
                
                if news_date < start_time:
                    found_older = True
                    break
                
                if start_time <= news_date <= end_time:
                    full_url = link_tag["href"]
                    if full_url not in collected_links:
                        collected_links.append(full_url)
            
            if found_older:
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_ogo_site: page {page} - {type(e).__name__}: {e}"
            ogo_err.append(error_msg)
            break
            
    return collected_links


def parse_ogo_article(url: str, keywords: List[str]):
    """
    Parse a single article from ogo.ua and search for keyword patterns.
    Results are appended to global ogo_report_brief and ogo_report_for_analysis.
    """
    global ogo_err, ogo_report_brief, ogo_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_='ast-post-format-')
        
        if not container:
            error_msg = f"parse_ogo_article: {url} - CONTAINER NOT FOUND"
            ogo_err.append(error_msg)
            return
        
        title_tag = container.find('h1', class_='entry-title')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_container = container.find('div', class_='entry-content')
        if not content_container:
            error_msg = f"parse_ogo_article: {url} - CONTENT CONTAINER NOT FOUND"
            ogo_err.append(error_msg)
            return
        
        content_copy = content_container.__copy__()
        
        for ad in content_copy.find_all('div', class_='ogo-inarticle-ad'):
            ad.decompose()
        
        for script in content_copy.find_all('script'):
            script.decompose()
        
        for img in content_copy.find_all('img'):
            img.decompose()
        
        for views in content_copy.find_all('div', class_='post-views'):
            views.decompose()
        
        for author in content_copy.find_all('div', class_='post-author'):
            author.decompose()
        for tags in content_copy.find_all('div', class_='post-tags'):
            tags.decompose()
        
        for p in content_copy.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            ogo_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            ogo_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_ogo_article: {url} - {type(e).__name__}: {e}"
        ogo_err.append(error_msg)


# ============================================================================
# 7DNIV PARSING
# ============================================================================

def parse_7dniv(start_time: datetime, end_time: datetime, keywords: List[str]):
    """
    Fetch and parse articles from 7dniv via WordPress REST API.
    
    Args:
        start_time: Start of the time range (inclusive)
        end_time: End of the time range (inclusive)
        keywords: List of regex patterns to search for
    
    Returns:
        None: Results are appended to global sevendniv_report_brief and sevendniv_report_for_analysis
    """
    global sevendniv_err, sevendniv_report_brief, sevendniv_report_for_analysis, links_from_sevendniv
    
    api_url = "https://7dniv.rv.ua/wp-json/wp/v2/posts"
    
    params = {
        "per_page": 100,
        "after": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "before": end_time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    page = 1
    
    while True:
        params["page"] = page
        try:
            response = fetch_with_retry(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            
            posts = response.json()
            if not posts:
                break
            
            for post in posts:
                link = post.get('link', '')
                links_from_sevendniv.append(link)
                
                title = post.get('title', {}).get('rendered', 'No title')
                content_html = post.get('content', {}).get('rendered', '')
                
                soup = BeautifulSoup(content_html, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                for img in soup.find_all('img'):
                    img.decompose()
                for ad in soup.find_all('div', class_=re.compile(r'ad|banner|code-block')):
                    ad.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = ' '.join(text.split())
                full_text = title + " " + text
                
                found_keywords = []
                for pattern in keywords:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        found_keywords.append(pattern)
                
                if found_keywords:
                    sevendniv_report_brief.append({
                        'title': title,
                        'link': link,
                        'keywords': found_keywords
                    })
                    
                    sevendniv_report_for_analysis.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'keywords': found_keywords
                    })
            
            page += 1
            time.sleep(0.5)
            
        except Exception as e:
            error_msg = f"parse_7dniv: page {page} - {type(e).__name__}: {e}"
            sevendniv_err.append(error_msg)
            break


# ============================================================================
# RIVNEMEDIA PARSING
# ============================================================================

def parse_rivnemedia_sitemap(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from rivne.media sitemap within a specified time range.
    
    Args:
        start_time: Start of the time range (inclusive)
        end_time: End of the time range (inclusive)
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global rivnemedia_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = "https://rivne.media"
    collected_links = []
    
    try:
        response = fetch_with_retry(f"{base_url}/sitemap.xml", headers, timeout=30)
        soup = BeautifulSoup(response.text, "xml")
        sitemap_urls = [s.text for s in soup.find_all("loc")]
        
        for sm_url in reversed(sitemap_urls):
            try:
                resp_sm = fetch_with_retry(sm_url, headers, timeout=30)
                soup_sm = BeautifulSoup(resp_sm.text, "xml")
                urls = soup_sm.find_all("url")
                
                for u in urls:
                    loc_tag = u.find("loc")
                    lastmod_tag = u.find("lastmod")
                    
                    if not loc_tag or not lastmod_tag:
                        continue
                        
                    loc = loc_tag.text
                    date_str = lastmod_tag.text.split('+')[0].split('Z')[0]
                    news_date = datetime.fromisoformat(date_str)
                    
                    if start_time <= news_date <= end_time:
                        if loc not in collected_links:
                            collected_links.append(loc)
                
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"parse_rivnemedia_sitemap: Пропускаем {sm_url} - {type(e).__name__}"
                rivnemedia_err.append(error_msg)
                continue
            
    except Exception as e:
        error_msg = f"parse_rivnemedia_sitemap: {type(e).__name__}: {e}"
        rivnemedia_err.append(error_msg)
        
    return collected_links


def parse_rivnemedia_article(url: str, keywords: List[str]):
    """
    Parse a single article from rivne.media and search for keyword patterns.
    Results are appended to global rivnemedia_report_brief and rivnemedia_report_for_analysis.
    """
    global rivnemedia_err, rivnemedia_report_brief, rivnemedia_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article', class_='article')
        if not article:
            article = soup.find('article', itemtype='http://schema.org/Article')
        if not article:
            error_msg = f"parse_rivnemedia_article: {url} - ARTICLE CONTAINER NOT FOUND"
            rivnemedia_err.append(error_msg)
            return
        
        title_tag = article.find('h1', itemprop='headline')
        if not title_tag:
            title_tag = article.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_container = article.find('div', itemprop='articleBody')
        if not content_container:
            content_container = article.find('div', class_='article__body')
        if not content_container:
            content_container = article
        
        content_copy = content_container.__copy__()
        
        for img in content_copy.find_all('img'):
            img.decompose()
        for picture in content_copy.find_all('picture'):
            picture.decompose()
        
        for a in content_copy.find_all('a', href=True):
            if 'sunmare' in a.get('href', ''):
                a.decompose()
        
        for p in content_copy.find_all('p'):
            if p.find('a', href=lambda x: x and 'sunmare' in x):
                p.decompose()
        
        for p in content_copy.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            rivnemedia_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            rivnemedia_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_rivnemedia_article: {url} - {type(e).__name__}: {e}"
        rivnemedia_err.append(error_msg)


# ============================================================================
# HORYN PARSING
# ============================================================================

def get_horyn_news(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from horyn.info within a specified time range.
    
    Args:
        start_time: Start of the time range (inclusive)
        end_time: End of the time range (inclusive)
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global horyn_err
    
    months = {"січня": "01", "лютого": "02", "березня": "03", "квітня": "04", 
              "травня": "05", "червня": "06", "липня": "07", "серпня": "08", 
              "вересня": "09", "жовтня": "10", "листопада": "11", "грудня": "12"}
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
    links = []
    page = 1
    
    while True:
        url = f"https://horyn.info/news/?pages={page}" if page > 1 else "https://horyn.info/news/"
        try:
            soup = BeautifulSoup(fetch_with_retry(url, headers, timeout=30).text, "html.parser")
            items = soup.select(".sidebar__wrapper a.news-card")
            
            if not items:
                break
            
            for item in items:
                link = item.get("href")
                try:
                    art_soup = BeautifulSoup(fetch_with_retry(link, headers, timeout=30).text, "html.parser")
                    
                    date_tag = art_soup.find("p", class_="post-single__date")
                    if date_tag:
                        parts = date_tag.text.lower().replace(",", "").split()
                        dt = datetime.strptime(f"2026-{months[parts[2]]}-{parts[1].zfill(2)} {parts[0]}", "%Y-%m-%d %H:%M")
                        
                        if start_time <= dt <= end_time:
                            links.append(link)
                        elif dt < start_time:
                            return links
                except Exception as e:
                    error_msg = f"get_horyn_news: {link} - {type(e).__name__}: {e}"
                    horyn_err.append(error_msg)
                    continue
            
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"get_horyn_news: page {page} - {type(e).__name__}: {e}"
            horyn_err.append(error_msg)
            break
            
    return links


def parse_horyn_article(url: str, keywords: List[str]):
    """
    Parse a single article from horyn.info and search for keyword patterns.
    Results are appended to global horyn_report_brief and horyn_report_for_analysis.
    """
    global horyn_err, horyn_report_brief, horyn_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_='padding-wrapper--post-single')
        
        if not container:
            error_msg = f"parse_horyn_article: {url} - CONTAINER NOT FOUND"
            horyn_err.append(error_msg)
            return
        
        title_tag = container.find('h1', class_='title--post-single-news')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_copy = container.__copy__()
        
        h1_tag = content_copy.find('h1', class_='title--post-single-news')
        if h1_tag:
            h1_tag.decompose()
        
        section_title = content_copy.find('p', class_='title--section')
        if section_title:
            section_title.decompose()
        
        date_tag = content_copy.find('p', class_='post-single__date')
        if date_tag:
            date_tag.decompose()
        
        social_buttons = content_copy.find('div', class_='social-buttons')
        if social_buttons:
            social_buttons.decompose()
        
        img_tag = content_copy.find('img', class_='post-single__media')
        if img_tag:
            img_tag.decompose()
        
        picture = content_copy.find('picture')
        if picture:
            picture.decompose()
        
        for em in content_copy.find_all('em'):
            if em.find_parent('p'):
                em.find_parent('p').decompose()
        
        sidebar = content_copy.find('div', class_='sidebar')
        if sidebar:
            sidebar.decompose()
        
        hashtags = content_copy.find('div', class_='hashtags')
        if hashtags:
            hashtags.decompose()
        
        for banner in content_copy.find_all('p', class_='banner-label'):
            banner.decompose()
        for a in content_copy.find_all('a', href=True):
            if 'vstup.oa.edu.ua' in a.get('href', ''):
                a.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            horyn_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            horyn_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_horyn_article: {url} - {type(e).__name__}: {e}"
        horyn_err.append(error_msg)


# ============================================================================
# RIVNE1 PARSING
# ============================================================================

def parse_rivne1_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from rivne1.tv within a specified time range.
    
    Args:
        start_time: Start of the time range (inclusive)
        end_time: End of the time range (inclusive)
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global rivne1_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    base_url = "https://rivne1.tv"
    category_path = "/category/61-novini"
    collected_links = []
    
    month_map = {
        'січня': 1, 'лютого': 2, 'березня': 3, 'квітня': 4,
        'травня': 5, 'червня': 6, 'липня': 7, 'серпня': 8,
        'вересня': 9, 'жовтня': 10, 'листопада': 11, 'грудня': 12
    }
    
    last_known_date = date.today()
    offset = 0

    while True:
        url = f"{base_url}{category_path}" + (f"/{offset}" if offset > 0 else "")
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            news_list = soup.find("ul", class_="list-st-3")
            
            if not news_list:
                break
                
            items = news_list.find_all("li", recursive=False)
            found_any_on_page = False
            
            for item in items:
                date_strong = item.find("strong", style="font-size:25px;")
                if date_strong:
                    text = date_strong.get_text(strip=True).lower()
                    try:
                        parts = text.split()
                        day = int(parts[0])
                        month = month_map.get(parts[1])
                        year = int(parts[2])
                        last_known_date = date(year, month, day)
                    except:
                        pass
                    continue
                
                link_tag = item.find("a")
                time_span = item.find("span")
                
                if link_tag and time_span:
                    try:
                        t_parts = time_span.get_text(strip=True).split(':')
                        news_time = dt_time(int(t_parts[0]), int(t_parts[1]))
                        news_datetime = datetime.combine(last_known_date, news_time)
                        
                        if start_time <= news_datetime <= end_time:
                            full_url = base_url + link_tag["href"]
                            if full_url not in collected_links:
                                collected_links.append(full_url)
                        
                        if news_datetime < start_time:
                            return collected_links
                        
                        found_any_on_page = True
                    except:
                        continue
            
            if not found_any_on_page:
                break
                
            offset += 30
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_rivne1_site: offset {offset} - {type(e).__name__}: {e}"
            rivne1_err.append(error_msg)
            break
            
    return collected_links


def parse_rivne1_article(url: str, keywords: List[str]):
    """
    Parse a single article from rivne1.tv and search for keyword patterns.
    Results are appended to global rivne1_report_brief and rivne1_report_for_analysis.
    """
    global rivne1_err, rivne1_report_brief, rivne1_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        container = soup.find('div', class_='articleBody')
        if not container:
            error_msg = f"parse_rivne1_article: {url} - CONTAINER NOT FOUND"
            rivne1_err.append(error_msg)
            return
        
        content_copy = container.__copy__()
        
        for a in content_copy.find_all('a', class_='article-img-title'):
            a.decompose()
        for img in content_copy.find_all('img'):
            img.decompose()
        
        info_block = content_copy.find('div', class_='info')
        if info_block:
            info_block.decompose()
        
        for ad in content_copy.find_all('div', class_='google-auto-placed'):
            ad.decompose()
        for ad in content_copy.find_all('ins', class_='adsbygoogle'):
            ad.decompose()
        
        for p in content_copy.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            rivne1_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            rivne1_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_rivne1_article: {url} - {type(e).__name__}: {e}"
        rivne1_err.append(error_msg)


# ============================================================================
# RP_RV_UA PARSING
# ============================================================================

def parse_rp_rv_ua(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from rp.rv.ua within a specified time range.
    
    Args:
        start_time: Start of the time range (inclusive)
        end_time: End of the time range (inclusive)
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global rp_rv_ua_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    base_url = "https://www.rp.rv.ua"
    collected_links = []
    
    page = 1

    while True:
        url = f"{base_url}/page/{page}" if page > 1 else base_url
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            posts = soup.find_all("div", class_="post")
            
            if not posts:
                break
                
            page_processed = False
            
            for post in posts:
                link_tag = post.find("h2", class_="post-title").find("a")
                date_tag = post.find("a", class_="post-date")
                
                if link_tag and date_tag:
                    date_str = date_tag.get_text(strip=True)
                    try:
                        news_date = datetime.strptime(date_str, "%d.%m.%Y")
                        
                        if news_date > end_time:
                            continue
                        
                        if news_date < start_time:
                            return collected_links
                        
                        full_url = link_tag["href"]
                        if full_url not in collected_links:
                            collected_links.append(full_url)
                        
                        page_processed = True
                    except Exception:
                        continue
            
            if not page_processed:
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_rp_rv_ua: page {page} - {type(e).__name__}: {e}"
            rp_rv_ua_err.append(error_msg)
            break
            
    return collected_links


def parse_rp_rv_ua_article(url: str, keywords: List[str]):
    """
    Parse a single article from rp.rv.ua and search for keyword patterns.
    Results are appended to global rp_rv_ua_report_brief and rp_rv_ua_report_for_analysis.
    """
    global rp_rv_ua_err, rp_rv_ua_report_brief, rp_rv_ua_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('div', id=re.compile(r'^post-\d+'))
        
        if not article:
            error_msg = f"parse_rp_rv_ua_article: {url} - ARTICLE CONTAINER NOT FOUND"
            rp_rv_ua_err.append(error_msg)
            return
        
        header = article.find('div', class_='post-header')
        if not header:
            error_msg = f"parse_rp_rv_ua_article: {url} - POST HEADER NOT FOUND"
            rp_rv_ua_err.append(error_msg)
            return
        
        title_tag = header.find('h1', class_='post-title')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        content_container = article.find('div', class_='post-content')
        if not content_container:
            error_msg = f"parse_rp_rv_ua_article: {url} - CONTENT CONTAINER NOT FOUND"
            rp_rv_ua_err.append(error_msg)
            return
        
        content_copy = content_container.__copy__()
        
        for img in content_copy.find_all('img'):
            img.decompose()
        
        for p in content_copy.find_all('p'):
            text = p.get_text(strip=True)
            if text.startswith('©') or 'charivne.info' in text:
                p.decompose()
        
        for clear in content_copy.find_all('div', class_='clear'):
            clear.decompose()
        
        text = content_copy.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            rp_rv_ua_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            rp_rv_ua_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception as e:
        error_msg = f"parse_rp_rv_ua_article: {url} - {type(e).__name__}: {e}"
        rp_rv_ua_err.append(error_msg)


# ============================================================================
# ITVMG PARSING
# ============================================================================

def parse_itvmg_site(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Parse news articles from itvmg.com within a specified time range.
    
    Args:
        start_time: Start of the time range (inclusive)
        end_time: End of the time range (inclusive)
    
    Returns:
        list: List of article URLs collected within the specified time range
    """
    global itvmg_err
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    base_url = "https://itvmg.com"
    category_path = "/novini"
    collected_links = []
    
    offset = 0
    step = 21

    while True:
        url = f"{base_url}{category_path}" + (f"/{offset}" if offset > 0 else "")
        
        try:
            response = fetch_with_retry(url, headers, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            news_items = soup.find_all("a", class_="reset-link")
            
            if not news_items:
                break
                
            found_in_range = False
            
            for item in news_items:
                href = item.get("href")
                span = item.find("span")
                
                if href and span:
                    date_str = span.get_text(strip=True)
                    try:
                        news_datetime = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
                        
                        if start_time <= news_datetime <= end_time:
                            full_url = base_url + href
                            if full_url not in collected_links:
                                collected_links.append(full_url)
                        
                        if news_datetime < start_time:
                            return collected_links
                        
                        found_in_range = True
                    except Exception:
                        continue
            
            if not found_in_range:
                break
                
            offset += step
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"parse_itvmg_site: offset {offset} - {type(e).__name__}: {e}"
            itvmg_err.append(error_msg)
            break
            
    return collected_links


def parse_itvmg_article(url: str, keywords: List[str]):
    """
    Parse a single article from itvmg.com and search for keyword patterns.
    Results are appended to global itvmg_report_brief and itvmg_report_for_analysis.
    """
    global itvmg_err, itvmg_report_brief, itvmg_report_for_analysis
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        if url in [item['link'] for item in itvmg_report_brief]:
            return
        
        response = fetch_with_retry(url, headers, timeout=30)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h1')
        if not title_tag:
            return
        
        title = title_tag.get_text(strip=True)
        
        article_body = soup.find('div', {'itemprop': 'articleBody'})
        
        if article_body:
            text_parts = []
            for p in article_body.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    text_parts.append(text)
            text = ' '.join(text_parts)
        else:
            text_parts = []
            current = title_tag.find_next_sibling()
            
            while current:
                if current.name == 'div' and 'article__gallery' in current.get('class', []):
                    break
                if current.name == 'p':
                    text = current.get_text(strip=True)
                    if text:
                        text_parts.append(text)
                current = current.find_next_sibling()
            
            text = ' '.join(text_parts)
        
        full_text = title + " " + text
        
        found_keywords = []
        for pattern in keywords:
            if re.search(pattern, full_text, re.IGNORECASE):
                found_keywords.append(pattern)
        
        if found_keywords:
            itvmg_report_brief.append({
                'title': title,
                'link': url,
                'keywords': found_keywords
            })
            
            itvmg_report_for_analysis.append({
                'title': title,
                'link': url,
                'text': text,
                'keywords': found_keywords
            })
        
    except Exception:
        pass


# ============================================================================
# THREAD POOL EXECUTION
# ============================================================================

print(f"\nStarting {len(tasks)} tasks with {MAX_WORKERS} workers...")
print("=" * 70)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(task): task.__name__ for task in tasks}
    
    for future in as_completed(futures):
        task_name = futures[future]
        try:
            future.result()
            print(f"[OK] {task_name} completed")
        except Exception as e:
            print(f"[ERROR] {task_name} failed: {e}")

print("=" * 70)
print("All tasks completed")


# ============================================================================
# BUILD REPORTS
# ============================================================================

list_brief = [
    rayon_report_brief,
    charivne_report_brief,
    radiotrek_report_brief,
    suspilne_report_brief,
    vse_rv_report_brief,
    rivnepost_report_brief,
    ogo_report_brief,
    sevendniv_report_brief,
    rivnemedia_report_brief,
    horyn_report_brief,
    rivne1_report_brief,
    rp_rv_ua_report_brief,
    itvmg_report_brief
]

list_for_analysis = [
    rayon_report_for_analysis,
    charivne_report_for_analysis,
    radiotrek_report_for_analysis,
    suspilne_report_for_analysis,
    vse_rv_report_for_analysis,
    rivnepost_report_for_analysis,
    ogo_report_for_analysis,
    sevendniv_report_for_analysis,
    rivnemedia_report_for_analysis,
    horyn_report_for_analysis,
    rivne1_report_for_analysis,
    rp_rv_ua_report_for_analysis,
    itvmg_report_for_analysis
]

list_err = [
    rayon_err,
    charivne_err,
    radiotrek_err,
    suspilne_err,
    vse_rv_err,
    rivnepost_err,
    ogo_err,
    sevendniv_err,
    rivnemedia_err,
    horyn_err,
    rivne1_err,
    rp_rv_ua_err,
    itvmg_err
]

media_keys = ["rayon", "charivne", "radiotrek", "suspilne", "vse_rv", 
              "rivnepost", "ogo", "sevendniv", "rivnemedia", "horyn", 
              "rivne1", "rp_rv_ua", "itvmg"]

# Build the brief report
brief_report = f"{end_time.strftime('%d.%m')}\n"
has_any_publication = False

for i, report_list in enumerate(list_brief):
    if report_list:
        has_any_publication = True
        media_key = media_keys[i]
        media_name = media_names[media_key]
        
        brief_report += f"{media_name}\n"
        
        for item in report_list:
            brief_report += f"{item['title']}\n"
            brief_report += f"{item['link']}\n"

if not has_any_publication:
    brief_report += "Публікації у медіа відсутні"

# Build the full report
full_report = f"{end_time.strftime('%d.%m')}\n"
has_any_publication_full = False

for i, report_list in enumerate(list_for_analysis):
    if report_list:
        has_any_publication_full = True
        media_key = media_keys[i]
        media_name = media_names[media_key]
        
        full_report += f"{media_name}\n"
        
        for item in report_list:
            full_report += "\n\n"
            full_report += f"{item['title']}\n"
            full_report += f"{item['link']}\n"
            full_report += f"{item['text']}\n"

if not has_any_publication_full:
    full_report += "Публікації у медіа відсутні"

# Build the error report
error_report = f"{end_time.strftime('%d.%m')}\n"
has_any_error = False

for i, error_list in enumerate(list_err):
    if error_list:
        has_any_error = True
        media_key = media_keys[i]
        media_name = media_names[media_key]
        
        error_report += f"{media_name}\n"
        
        for error in error_list:
            error_report += f"{error}\n"


# ============================================================================
# REPORTS SAVING
# ============================================================================

error_text = str(error_report) if error_report else ""
has_errors = len(error_text.strip()) > 10
warning = "-- Увага! під час обробки зафіксовані помилки. Ймовірно результати не повні.\n\n"

full_content = '\n'.join(full_report) if isinstance(full_report, list) else str(full_report)
brief_content = '\n'.join(brief_report) if isinstance(brief_report, list) else str(brief_report)

with open('full_report.txt', 'w', encoding='utf-8') as f:
    f.write((warning if has_errors else '') + full_content)

with open('brief_report.txt', 'w', encoding='utf-8') as f:
    f.write((warning if has_errors else '') + brief_content)

with open('error_report.txt', 'w', encoding='utf-8') as f:
    f.write(error_text if error_text else "No errors recorded")

print(f"\n✅ Reports saved at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
if has_errors:
    print("⚠️ WARNING: Errors were recorded during processing")
