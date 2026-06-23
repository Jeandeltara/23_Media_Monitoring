import os
import glob
import re
import datetime
import requests
from bs4 import BeautifulSoup
from groq import Groq

# --- Настройка API ---
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- Parsers library ---
def clean_content(element):
    if not element:
        return ""
    for tag in element(['script', 'style', 'noscript', 'iframe', 'ins', 'header', 'footer', 'nav']):
        tag.extract()
    return element.get_text(separator=" ", strip=True)

def parse_itvmg(soup):
    return clean_content(soup.find('div', itemprop='articleBody'))

def parse_rivne1(soup):
    return clean_content(soup.find('div', class_='articleBody'))

def parse_rp_rv(soup):
    return clean_content(soup.find('div', class_='entry-content'))

def parse_rayon(soup):
    return clean_content(soup.find('article'))

def parse_teza(soup):
    return clean_content(soup.find('div', class_='post-content'))

def parse_horyn(soup):
    return clean_content(soup.find('div', class_='entry-content'))

def parse_rivnepost(soup):
    # Пытаемся найти основной контент
    content = soup.find('div', class_='article-body') or soup.find('article')
    return clean_content(content) if content else soup.get_text(separator=" ", strip=True)

def parse_rivnemedia(soup):
    content = soup.find('div', class_='news-content') or soup.find('div', class_='content')
    return clean_content(content) if content else soup.get_text(separator=" ", strip=True)

def get_parser_by_url(url):
    if 'itvmg.com' in url: return parse_itvmg
    if 'rivne1.tv' in url: return parse_rivne1
    if 'rp.rv.ua' in url: return parse_rp_rv
    if 'rayon.in.ua' in url: return parse_rayon
    if 'teza.tv' in url: return parse_teza
    if 'horyn.info' in url: return parse_horyn
    if 'rivnepost.rv.ua' in url: return parse_rivnepost
    if 'rivne.media' in url: return parse_rivnemedia
    return None

# --- Main logic ---
def send_to_ai(prompt_text):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt_text}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def get_latest_report():
    files = glob.glob("*_report.txt")
    return max(files, key=os.path.getctime) if files else None

def extract_urls(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Ищем любую ссылку, начинающуюся с http
    return re.findall(r'https?://\S+', content)

def process_and_create_prompt():
    report_file = get_latest_report()
    if not report_file:
        print("No report file found.")
        return

    print(f"DEBUG: Анализирую файл: {report_file}")
    urls = extract_urls(report_file)
    print(f"DEBUG: Найдено ссылок: {len(urls)}")
    
    articles_data = []
    for url in urls:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, timeout=15, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            parser = get_parser_by_url(url)
            
            # Если парсера нет, берем весь текст страницы
            text = parser(soup) if parser else clean_content(soup.find('body'))
            title = soup.title.string.strip() if soup.title else "No Title"
            
            if len(text) > 50: # Сохраняем, если вытянули хоть что-то осмысленное
                articles_data.append(f"### Заголовок: {title}\nИсточник: {url}\nТекст: {text}\n---")
        except Exception as e:
            print(f"Error processing {url}: {e}")

    if not articles_data:
        print("No content extracted from links.")
        return

    # Загружаем промпт
    base_prompt = "Проанализируй следующие статьи:"
    if os.path.exists('prompt.txt'):
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            base_prompt = f.read()

    full_prompt = (base_prompt + "\n\n" + "\n".join(articles_data))

    with open('prompt_w.txt', 'w', encoding='utf-8') as f:
        f.write(full_prompt)

    # Обработка через Groq
    analysis_result = send_to_ai(full_prompt)
    
    date_str = datetime.datetime.now().strftime("%y%m%d")
    with open(f"{date_str}_media_analysis.txt", 'w', encoding='utf-8') as f:
        f.write(analysis_result)

if __name__ == "__main__":
    process_and_create_prompt()
