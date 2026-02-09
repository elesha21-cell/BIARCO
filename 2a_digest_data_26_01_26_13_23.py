
#Bash
##pip install pandas numpy matplotlib
##pip install python-telegram-bot 

#pip install yake 
#python-dotenv
#pip install requests 
#pip install python-dotenv
#pip install stop-words
#pip install pymorphy2[fast]
#лемматизация 
#pip install --upgrade pip
#pip install --upgrade setuptools
#pip install pymorphy2
#pip install pymorphy2-dicts-ru
#pip install beautifulsoup4 lxml

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from stop_words import get_stop_words
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
# добавила чтение параметров окружения из файла .env
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup

# лемматизация 
#import pymorphy2
#morph = pymorphy2.MorphAnalyzer()
# работа с Excel
import pandas as pd # Не забудьте установить: pip install pandas openpyxl
# добавила 
try:
    import yake
except Exception as e:  # pragma: no cover - оставить понятное сообщение пользователю
    print("Модуль 'yake' не найден. Установите его: pip install yake", file=sys.stderr)
    raise

#Настройки по умолчанию
RUS_STOPWORDS = set(get_stop_words("russian"))
DEFAULT_HF_MODEL = "facebook/bart-large-cnn"  # модель для отправки текста "на анализ" (можно заменить)
HF_API_URL_TEMPLATE = "https://api-inference.huggingface.co/models/{model}"
HF_API_KEY_ENV = "HUGGINGFACE_API_KEY"

#Параметры YAKE для русского языка и извлечения коротких ключевых слов
YAKE_PARAMS = {
    "language": "ru",
    "max_ngram_size": 2,  # 1-2 слова в тегах
    "deduplication_threshold": 0.7,  # было 0.9
    "numOfKeywords": 50,  # захватим больше и затем отфильтруем/сократим - было вначале 10. Хорошо 20-50
}

##--добавить свои слова
RUS_STOPWORDS.update({"ссылка"})

# Дополнительные настройки
URL_PATTERN = re.compile(r'https?://\S+')
# Хештеги только в начале записи, отделенные пробелами или служебными символами
HASHTAG_PATTERN = re.compile(r'^(?:[\s\n]*#([а-яА-ЯёЁ\w]+))+')

_token_pattern = re.compile(r"[а-яёА-ЯЁ0-9-]+")

def extract_leading_hashtags(text: str) -> Tuple[List[str], str]:
    """
    Извлекает хештеги только из начала записи.
    Возвращает (список хештегов, текст без хештегов в начале)
    """
    if not text:
        return [], ""
    
    # Ищем хештеги в начале текста
    match = HASHTAG_PATTERN.match(text)
    if not match:
        return [], text
    
    # Извлекаем все хештеги из найденной последовательности
    hashtags = []
    hashtag_text = match.group(0)
    
    # Удаляем найденные хештеги из текста
    remaining_text = text[len(hashtag_text):].lstrip()
    
    # Извлекаем отдельные хештеги из найденной последовательности
    hashtag_matches = re.findall(r'#([а-яА-ЯёЁ\w]+)', hashtag_text)
    hashtags.extend(hashtag_matches)
    
    return hashtags, remaining_text

def extract_all_urls(text: str) -> List[str]:
    """Извлекает все ссылки из текста"""
    if not text:
        return []
    return URL_PATTERN.findall(text)

def fetch_webpage_content(url: str) -> Optional[str]:
    """Получает содержимое веб-страницы по URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Используем BeautifulSoup для извлечения текста
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Получаем текст
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Ошибка при получении контента по URL {url}: {e}", file=sys.stderr)
        return None

def extract_tags_from_multiple_urls(urls: List[str], max_tags: int = 10) -> List[str]:
    """Извлекает теги из текста каждой ссылки"""

    unique_tags = []
    
    return unique_tags
'''
def process_record_with_hashtags_and_urls(
    record: Dict[str, Any], 
    tag_before: List[str],
    hf_model: str,
    hf_api_key: Optional[str],
    max_tags_per_item: int = 10
) -> Tuple[Dict[str, Any], List[str], bool]:
    """
    Обрабатывает запись с учетом хештегов и URL
    Возвращает: (результат, новые теги для следующей записи, нужно ли пропустить текущую запись)
    """
    text = choose_text_from_record(record)
    
    if not text:
        return {**record, "tags": []}, tag_before, False
    
    # Извлекаем хештеги только из начала записи
    leading_hashtags, text_without_leading_hashtags = extract_leading_hashtags(text)
    
    # Извлекаем все URL из оставшегося текста
    urls = extract_all_urls(text_without_leading_hashtags)
    
    # Все хештеги (из начала + из предыдущей записи)
    all_hashtags = list(set(leading_hashtags + tag_before))
    
    # Случай 1: Есть хештеги в начале, но нет текста и URL после них
    if leading_hashtags and not text_without_leading_hashtags.strip():
        # Запоминаем хештеги и пропускаем текущую запись
        return None, all_hashtags, True
  
    # Теги из текста (без хештегов и URL)
    text_without_urls = re.sub(URL_PATTERN, '', text_without_leading_hashtags)
    #tags_from_text = extract_tags_with_yake(text_without_urls, max_tags_per_item)
    
    # Теги из всех URL
    tags_from_urls = extract_tags_from_multiple_urls(urls, max_tags_per_item)
  
    # Объединяем все теги: сначала хештеги, затем остальные
    #other_tags = list(set(tags_from_text + tags_from_urls))[:max_tags_per_item]
    all_tags = all_hashtags #+ other_tags
    # all_name - формируем поле "name"
    # Опционально: отправляем в HuggingFace
    if hf_api_key:
        # Отправляем либо текст без хештегов, либо контент первой ссылки
        analysis_text = text_without_leading_hashtags
        if urls:
            webpage_content = fetch_webpage_content(urls[0])
            if webpage_content:
                analysis_text = webpage_content
        _ = call_huggingface_analysis(analysis_text, hf_model, hf_api_key)
    
    result = {**record, "tags": all_tags}
    return result, [], False
'''
# добавила 
# Дополнительные настройки
#
def tokenize_russian(text: str) -> List[str]:
    return _token_pattern.findall(text.lower())

def remove_stopwords_from_text(text: str) -> str:
    tokens = tokenize_russian(text)
    filtered = [t for t in tokens if t not in RUS_STOPWORDS]
    return " ".join(filtered)

## -- добавить свои слова
# лемматизация 
try:
    import inspect
    from collections import namedtuple
    # Если отсутствует ArgSpec — создаём совместимую структуру
    if not hasattr(inspect, "ArgSpec"):
        ArgSpec = namedtuple("ArgSpec", ["args", "varargs", "keywords", "defaults"])
        inspect.ArgSpec = ArgSpec  # type: ignore[attr-defined]
    # Если отсутствует getargspec — реализуем через getfullargspec
    if not hasattr(inspect, "getargspec"):
        def _getargspec(func):
            full = inspect.getfullargspec(func)
            return inspect.ArgSpec(args=full.args, varargs=full.varargs,
                                   keywords=full.varkw, defaults=full.defaults)
        inspect.getargspec = _getargspec  # type: ignore[attr-defined]
except Exception:
    # В случае непредвиденной ошибки — продолжим без патча
    pass

    #перед использованием morph
try:
    import pymorphy2
    morph = pymorphy2.MorphAnalyzer()
    def lemmatize_phrase(phrase: str) -> str:
        return " ".join(morph.parse(w)[0].normal_form for w in tokenize_russian(phrase))
    def is_good_token(tok: str) -> bool:
        p = morph.parse(tok)[0]
            # принимаем существительные и прилагательные
        return p.tag.POS in {"NOUN", "ADJF", "ADJ"} and tok not in RUS_STOPWORDS and len(tok) > 2
    def normalize_tag(tag: str) -> str:
        toks = tokenize_russian(tag)
        good = [morph.parse(t)[0].normal_form for t in toks if is_good_token(t)]
        return " ".join(good)
except Exception as e:
    print("pymorphy2 не инициализировался:", e, file=sys.stderr)
    # упрощённый fallback — без лемматизации, но скрипт продолжит работу
    def lemmatize_phrase(phrase: str) -> str:
        return " ".join(tokenize_russian(phrase))
    def is_good_token(tok: str) -> bool:
        return tok not in RUS_STOPWORDS and len(tok) > 2
    def normalize_tag(tag: str) -> str:
        return " ".join(t for t in tokenize_russian(tag) if is_good_token(t))
#перед использованием morph

# лемматизация 
def read_messages(input_path: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    with open(input_path, "r", encoding=encoding) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Ожидается, что messages.json содержит JSON-массив объектов.")
    return data

def choose_text_from_record(record: Dict[str, Any]) -> Optional[str]:
    # Приоритет: text, затем caption
    for key in ("text", "caption"):
        val = record.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None

def call_huggingface_analysis(text: str, model: str, api_key: Optional[str], timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    Отправляет текст в Hugging Face Inference API.
    Возвращает распарсенный JSON-ответ (если есть), или None при ошибке.
    Скрипт продолжит работу даже если HF недоступен; это вспомогательный шаг "анализ/лог".
    """
    if not api_key:
        # Без ключа не выполняем запрос, но не прерываем работу
        return None

    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    url = HF_API_URL_TEMPLATE.format(model=model)
    payload = {"inputs": text}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except Exception:
        return None

    if resp.status_code != 200:
    # Если модель занята/ошибка, вернем None
        return None
    try:
        return resp.json()
    except Exception:
        return None
# добавила 26.01
# ... (предыдущий импорт и настройки) ...

def load_tags_mapping(filepath: str) -> Dict[str, str]:
    """
    Загружает маппинг хэштегов и наименований из Excel файла.
    Очищает хэштеги от символа '#' и пробелов для сопоставления.
    """
    try:
        # Читаем Excel, предполагаем, что колонки называются 'Хэштег' и 'Наименование'
        # Если файл имеет сложную структуру как в дампе, можно указать skiprows
        df = pd.read_excel(filepath)
        
        # Создаем словарь: ключ - хэштег без #, значение - наименование
        mapping = {}
        for _, row in df.iterrows():
            tag = str(row['Хэштег']).strip()
            if tag.startswith('#'):
                tag = tag[1:]
            name = str(row['Наименование']).strip()
            mapping[tag] = name
        return mapping
    except Exception as e:
        print(f"Предупреждение: Не удалось загрузить файл тегов {filepath}: {e}")
        return {}

def process_record_with_hashtags_and_urls(
    record: Dict[str, Any], 
    tag_before: List[str],
    hf_model: str,
    hf_api_key: Optional[str],
    tags_map: Dict[str, str], # Передаем сюда справочник
    max_tags_per_item: int = 10
) -> Tuple[Dict[str, Any], List[str], bool]:
    
    text = choose_text_from_record(record)
    if not text:
        return {**record, "tags": [], "name": []}, tag_before, False
    
    leading_hashtags, text_without_leading_hashtags = extract_leading_hashtags(text)
    
    # Собираем все теги (сохраняя порядок: сначала новые, потом из предыдущих записей)
    all_tags = []
    seen = set()
    for t in (leading_hashtags + tag_before):
        if t not in seen:
            all_tags.append(t)
            seen.add(t)

    # Формируем список имен в той же последовательности
    # Если тега нет в Excel, записываем сам тег
    names = [tags_map.get(tag, tag) for tag in all_tags]

    # Если это только хэштеги без текста — пропускаем (как в оригинальном коде)
    if leading_hashtags and not text_without_leading_hashtags.strip():
        return None, all_tags, True

    # Моделируем результат
    result = {
        **record, 
        "tags": all_tags,
        "name": names  # Новое поле
    }
    
    return result, [], False

def process_messages(
    input_path: str, 
    output_path: str, 
    hf_model: str, 
    hf_api_key: Optional[str], 
    max_tags_per_item: int = 10,
    encoding: str = "utf-8", 
    sleep_between_calls: float = 0.2
) -> None:
    # 1. Загружаем справочник тегов один раз перед циклом
    tags_map = load_tags_mapping("Теги канала.xlsx")
    
    messages = read_messages(input_path, encoding=encoding)
    out: List[Dict[str, Any]] = []
    tag_before = []
    
    for idx, rec in enumerate(messages):
        try:
            # 2. Передаем tags_map в функцию обработки
            result, new_tag_before, should_skip = process_record_with_hashtags_and_urls(
                rec, tag_before, hf_model, hf_api_key, tags_map, max_tags_per_item
            )
            
            if should_skip:
                tag_before = new_tag_before
                continue
            
            if result:
                out.append(result)
            
            tag_before = new_tag_before
            
        except Exception as e:
            print(f"Ошибка в сообщении {idx}: {e}")
            out.append({**rec, "tags": [], "name": []})
    
    with open(output_path, "w", encoding=encoding) as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

# ... остальной код main ...
# добавила 26.01    
'''
def extract_tags_with_yake(text: str, max_tags: int = 10) -> List[str]:
    tags: List[str] = []

    return tags
'''
"""
    Использует YAKE для извлечения ключевых слов.
    Возвращает список тегов в нижнем регистре, 1-2 слова, без дублирования.
"""
## -- добавить свои слова
    # предварительная очистка: удалим/скроем стоп-слова, чтобы YAKE их не учитывал
'''
    cleaned_text = remove_stopwords_from_text(text)
    kw_extractor = yake.KeywordExtractor(**YAKE_PARAMS)
    keywords = kw_extractor.extract_keywords(cleaned_text)
## -- добавить свои слова    
#    kw_extractor = yake.KeywordExtractor(**YAKE_PARAMS)
#    keywords = kw_extractor.extract_keywords(text)
    #print("text", text," ->","Yake-keywords", keywords) -- на 1 тексте ошибка выходит не мэппинг
    tags: List[str] = []

    return tags
'''
'''
def process_messages(
    input_path: str, 
    output_path: str, 
    hf_model: str, 
    hf_api_key: Optional[str], 
    max_tags_per_item: int = 10,  # Изменено на 10 согласно требованию
    encoding: str = "utf-8", 
    sleep_between_calls: float = 0.2
) -> None:
    messages = read_messages(input_path, encoding=encoding)
    out: List[Dict[str, Any]] = []
    
    tag_before = []  # Теги из предыдущей записи с хештегами
    total_messages = len(messages)
    processed_count = 0
    skipped_count = 0
    
    for idx, rec in enumerate(messages):
        try:
            result, new_tag_before, should_skip = process_record_with_hashtags_and_urls(
                rec, tag_before, hf_model, hf_api_key, max_tags_per_item
            )
            
            if should_skip:
                # Пропускаем текущую запись, но сохраняем теги для следующей
                tag_before = new_tag_before
                skipped_count += 1
                print(f"Сообщение {idx + 1}: Пропущено, сохранены теги: {new_tag_before}")
                continue
            
            if result:
                out.append(result)
                processed_count += 1
            
            # Обновляем теги для следующей записи
            tag_before = new_tag_before
            
            # Пауза для API
            if hf_api_key:
                time.sleep(sleep_between_calls)
                
        except Exception as e:
            print(f"Ошибка при обработке сообщения {idx}: {e}", file=sys.stderr)
            out.append({**rec, "tags": []})
    
    # Сохраняем результат
    with open(output_path, "w", encoding=encoding) as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    print(f"Обработано: {processed_count}, Пропущено: {skipped_count}")
'''
def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Processor: извлекает теги из сообщений и сохраняет digest_data.json")
    p.add_argument("--input", "-i", default="messages.json", help="Входной JSON-файл (список сообщений)")
    p.add_argument("--output", "-o", default="digest_data.json", help="Выходной JSON-файл с тегами")
    p.add_argument("--hf-model", default=DEFAULT_HF_MODEL, help="Модель Hugging Face для отправки текста (по умолчанию %(default)s)")
    p.add_argument("--max-tags", type=int, default=10, help="Максимальное число тегов (кроме хештегов) для каждой записи")  # Изменено описание
    p.add_argument("--encoding", default="utf-8", help="Кодировка входного/выходного файлов")
    return p

def main(argv: Optional[List[str]] = None) -> int:
    args = build_argparser().parse_args(argv)

# добавила
# Загружаем переменные окружения из .env файла
    load_dotenv()
    hf_api_key = os.environ.get(HF_API_KEY_ENV)
    if not hf_api_key:
        print(f"Переменная окружения {HF_API_KEY_ENV} не задана. Скрипт будет работать локально (без вызовов Hugging Face).", file=sys.stderr)

    try:
        process_messages(
            input_path=args.input,
            output_path=args.output,
            hf_model=args.hf_model,
            hf_api_key=hf_api_key,
            max_tags_per_item=args.max_tags,
            encoding=args.encoding,
        )
    except Exception as e:
        print("Ошибка при обработке сообщений:", e, file=sys.stderr)
        return 2

    print(f"Готово. Результат сохранен в {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())