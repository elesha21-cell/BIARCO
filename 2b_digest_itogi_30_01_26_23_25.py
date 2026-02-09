#pip install beautifulsoup4 lxml

import os
import json
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import yt_dlp

# Загружаем API-ключ из .env файла
load_dotenv()

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY', "").strip()
print(f"Длина ключа: {len(YANDEX_API_KEY)}")
YANDEX_CATALOG_ID = os.environ.get('YANDEX_CATALOG_ID')

# new


def get_youtube_data(url: str) -> Dict[str, str]:
    """Извлекает заголовок и описание видео через yt-dlp."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', ''),
                'description': info.get('description', '')
            }
    except Exception as e:
        print(f"  [YouTube Error]: {e}")
        return {'title': '', 'description': ''}

def is_youtube_url(url: str) -> bool:
    return 'youtube.com' in url or 'youtu.be' in url
# new

# добавила
def is_service_sentence(text: str) -> bool:
    """
    Проверяет, является ли предложение служебным (цифры, Часть, Пост, РЕЗЮМЕ).
    """
    if not text:
        return False
    # Очищаем от знаков препинания и лишних пробелов для проверки сути
    clean_text = re.sub(r'[.!?:]', '', text).strip()
    # Паттерн: только цифры (араб/рим), слова Пост/Часть/РЕЗЮМЕ и пробелы
    # Добавлен флаг re.IGNORECASE для гибкости
    pattern = r'^([\d]+|[IVXLCDM]+|Часть|Пост|РЕЗЮМЕ|\s)+$'
    return bool(re.match(pattern, clean_text, re.IGNORECASE))
# добавила
def extract_heading(record: Dict[str, Any]) -> str:
    """
    Улучшенная версия: если в тексте только теги и URL, извлекает заголовок со страницы.
    """
    text = record.get('text', '')
    caption = record.get('caption', '')
    source_text = (text if text and text.strip() else caption) or ""
    # ПРОВЕРКА НА YOUTUBE
    if is_youtube_url(source_text):
        return "Видео с Youtube"   
    if not source_text:
        return ""

    lines = source_text.split('\n')
    valid_content = []
    found_urls = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Коллекционируем ссылки на случай, если содержательного текста не будет
        urls_in_line = find_urls_in_text(stripped)
        if urls_in_line:
            found_urls.extend(urls_in_line)

        # Пропускаем теги
        if re.match(r'^(#\w+\s*)+$', stripped):
            continue
            
        # Пропускаем чистые ссылки для формирования текстового заголовка
        if stripped.startswith('http'):
            continue
            
        valid_content.append(stripped)

    # ЛОГИКА ДЛЯ СЛУЧАЯ С SAP: Если содержательного текста нет, но есть ссылка
    if not valid_content and found_urls:
        print(f"  [Инфо] Содержательный текст не найден, переход по ссылке: {found_urls[0]}")
        return extract_title_from_url(found_urls[0])

    if not valid_content:
        return ""

    # Стандартная обработка первой строки (как в вашем коде)
    first_line = valid_content[0]
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', first_line) if s.strip()]
    if not sentences:
        return first_line[:100]

    first_sentence = sentences[0]

    if is_service_sentence(first_sentence):
        if len(sentences) >= 2:
            heading = f"{first_sentence} {sentences[1]}"
        elif len(valid_content) >= 2:
            second_line_first_sentence = re.split(r'(?<=[.!?])\s+', valid_content[1])[0]
            heading = f"{first_line} {second_line_first_sentence}"
        else:
            heading = first_line
    else:
        heading = first_sentence

    heading = re.sub(r'^[📌💥⚠️]\s*', '', heading).strip()
    return heading
# - new
def process_digest_data(input_file: str = "digest_data.json", 
                        output_file: str = "digest_itogi.json"):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, record in enumerate(data, 1):
            print(f"Обработка записи {i}/{len(data)} (ID: {record.get('id')})...")
            
            # Добавляем поле text если его нет, но есть caption
            if 'text' not in record and 'caption' in record:
                record['text'] = record['caption']
            
            # 1. Сначала извлекаем заголовок (теперь учитывает ссылки внутри)
            heading = extract_heading(record)
            record['heading'] = heading
            
            # 2. Извлекаем текст для саммари
            # Функция extract_text_from_record уже имеет логику обхода по ссылкам, 
            # если 'text' и 'caption' не дали результата.
            text_to_summarize = extract_text_from_record(record)
            # new
            if text_to_summarize == "YOUTUBE_MARKER":
                record['heading'] = "Видео с Youtube"
                record['summary'] = "Видео с Youtube"
            elif text_to_summarize:
            # Обычная логика создания саммари через YandexGPT
            # new    
                summary = create_summary(text_to_summarize)
                record['summary'] = summary
            else:
                record['summary'] = "Не удалось извлечь текст для саммаризации"
                
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Готово! Результаты сохранены в {output_file}")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
# добавила

def extract_text_from_url(url: str) -> str:
    """
    Извлекает текст с веб-страницы по ссылке
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Удаляем ненужные элементы
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Получаем текст из основных тегов
        text_elements = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'main']):
            text = tag.get_text(strip=True)
            if text and len(text) > 20:  # Фильтруем короткие фрагменты
                text_elements.append(text)
        
        # Если не нашли контент в основных тегах, берем весь текст body
        if not text_elements:
            body = soup.find('body')
            if body:
                text = body.get_text(strip=True, separator=' ')
                if len(text) > 100:
                    text_elements = [text]
        
        return ' '.join(text_elements[:10])  # Берем первые 10 элементов чтобы не перегружать
        
    except Exception as e:
        print(f"Ошибка при извлечении текста из {url}: {str(e)}")
        return ""

def find_urls_in_text(text: str) -> List[str]:
    """
    Находит все URL в тексте
    """
    url_pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls
# new
def extract_title_from_url(url: str) -> str:
    """
    Извлекает заголовок страницы по ссылке
    """
    if is_youtube_url(url):
        data = get_youtube_data(url)
        return data['title']
    
    # ... далее ваш старый код для обычных сайтов ...
    # new

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Пытаемся найти заголовок в тегах title, h1, h2
        title = ""
        
        # Ищем тег title
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        # Если title не найден или слишком короткий, ищем h1
        if not title or len(title) < 10:
            h1_tags = soup.find_all('h1')
            if h1_tags:
                for h1 in h1_tags:
                    if h1.text.strip():
                        title = h1.text.strip()
                        break
        
        # Если все еще нет, ищем первый значимый текст
        if not title or len(title) < 10:
            for tag in soup.find_all(['p', 'div', 'span']):
                text = tag.get_text(strip=True)
                if text and len(text) > 20 and len(text) < 200:
                    title = text
                    break
        
        return title if title else ""
        
    except Exception as e:
        print(f"Ошибка при извлечении заголовка из {url}: {str(e)}")
        return ""
# добавила

def extract_text_from_record(record: Dict[str, Any]) -> str:
    """
    Извлекает текст из записи. 
    Если текст состоит только из хештегов и ссылок — извлекает контент по ссылкам.
    """

    text = str(record.get('text', '')).strip()
    caption = str(record.get('caption', '')).strip()
    
    source_text = text if text else caption
    
    if not source_text:
        return ""
# Если в тексте есть ссылка на YouTube
    if is_youtube_url(source_text):
        return "YOUTUBE_MARKER" # Специальный флаг
    
    # Проверка: является ли текст "пустым" (только хештеги и ссылки)
    # Удаляем ссылки
    clean_check = re.sub(r'https?://[^\s]+', '', source_text)
    # Удаляем хештеги
    clean_check = re.sub(r'#\w+', '', clean_check)
    # Удаляем лишние пробелы и переносы
    clean_check = clean_check.replace('\n', ' ').strip()

    # Если после очистки осталось меньше 10 символов — считаем текст "ссылочным"
    if len(clean_check) < 10:
        urls = find_urls_in_text(source_text)
        if urls and is_youtube_url(urls[0]):
            return "YOUTUBE_MARKER"
        elif urls:
            return extract_text_from_url(urls[0])
            
    return source_text


def create_summary(text: str) -> str:
    """
    Создает тезисное саммари через YandexGPT.
    """
    if not text or len(text.strip()) < 20: 
        return "Текст слишком короткий для саммаризации"

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }
    #-lite",
    prompt = {
        "modelUri": f"gpt://{YANDEX_CATALOG_ID}/yandexgpt-lite/latest",  
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": "2000"
        },
        "messages": [
        {
        "role": "system",
        "text": "Ты — профессиональный редактор. Твоя задача — кратко и нейтрально пересказать текст (2-3 пункта). Если текст касается экономики или политики, сохраняй объективность изложения исходного материала."
        },
        {
        "role": "user",
        "text": f"Извлеки ключевые моменты из этого текста:\n\n{text}"
        }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=prompt, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Извлекаем текст ответа из структуры YandexGPT
        summary = result['result']['alternatives'][0]['message']['text']
        if "не могу обсуждать эту тему" in summary or "не могу ответить" in summary:
            # Возможно, стоит попробовать отправить запрос еще раз с другим промптом 
            # или просто пометить запись как "Контент отклонен фильтрами безопасности"
            summary = "Контент отклонен фильтрами безопасности: тема признана чувствительной"  #Отказ модели
        return clean_summary(summary)
        
    except Exception as e:
        print(f"  [Ошибка API]: {str(e)}")
        return f"Ошибка при генерации саммари: {str(e)}"
# добавила

def clean_summary(summary: str) -> str:
    """
    Очищает саммари от лишних частей
    """
    # Убираем возможные префиксы вроде "Саммари:"
    prefixes = ["Саммари:", "Тезисы:", "Ключевые идеи:"]
    for prefix in prefixes:
        if summary.startswith(prefix):
            summary = summary[len(prefix):].strip()
    
    # Убираем нумерацию если она не нужна в итоговом выводе
    # Но можно оставить для структурированности
    
    return summary

def validate_environment():
    """
    Проверяет наличие необходимых переменных окружения
    """
    if not YANDEX_API_KEY:
        print("❌ ОШИБКА: YANDEX_API_KEY не найден в .env файле")
        print("Добавьте в файл .env строку:")
        print("YANDEX_API_KEY=ваш_ключ_здесь")
        return False
    
    if not YANDEX_CATALOG_ID:
        print("❌ ОШИБКА: YANDEX_CATALOG_ID не найден в .env файле")
        print("Добавьте в файл .env строку:")
        print("YANDEX_CATALOG_ID=ваш_catalog_id")
        return False
    
    # Проверяем, что файл digest_data.json существует
    if not os.path.exists("digest_data.json"):
        print("❌ ОШИБКА: Файл digest_data.json не найден")
        print("Создайте файл digest_data.json с данными для обработки")
        return False
    
    return True

if __name__ == "__main__":
    print("=== YANDEX Саммаризатор с извлечением заголовков ===")
    print("Автоматическая обработка digest_data.json")
    print("-" * 40)
    
    if validate_environment():
        # Запускаем обработку
        process_digest_data()