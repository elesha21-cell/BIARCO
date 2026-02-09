import json
from datetime import datetime
import html
import os
import re
from bs4 import BeautifulSoup
# со 2.02.26
INPUT_FILE = 'rez_ind.json'
OUTPUT_HTML = 'index.html'

# CSS стили для медиафайлов
MEDIA_CSS = """
    .media-container {
        margin-top: 15px;
        border-top: 1px dashed #ccc;
        padding-top: 10px;
    }
    .media {
        background: #f8f8f8;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        font-size: 0.9em;
    }
    .media-type {
        font-weight: bold;
        color: #2c5282;
        margin-bottom: 5px;
    }
    .media-info {
        color: #555;
    }
    .media-info div {
        margin: 2px 0;
    }
    .text-link {
        color: #1a73e8;
        text-decoration: underline;
        cursor: pointer;
    }
    .text-link:hover {
        color: #0d62c9;
    }
    .media-url {
        color: #1a73e8;
        text-decoration: underline;
        cursor: pointer;
        font-weight: normal;
        display: inline-block;
        margin-left: 5px;
    }
    .media-url:hover {
        color: #0d62c9;
    }
"""

def make_links_clickable(text: str) -> str:
    """
    Преобразует URL в тексте в кликабельные ссылки.
    Открывает ссылки в новом окне.
    """
    if not text:
        return text
    
    # Экранируем HTML специальные символы
    text = html.escape(text)
    
    # Регулярное выражение для поиска URL
    # Поддерживает http, https, www
    url_pattern = re.compile(
        r'(https?://[^\s<>"]+|www\.[^\s<>"]+\.[^\s<>"]+)'
    )
    
    def replace_url(match):
        url = match.group(0)
        # Если URL начинается с www, добавляем http://
        if url.startswith('www.'):
            url = 'http://' + url
        return f'<a href="{url}" class="text-link" target="_blank" rel="noopener noreferrer">{url}</a>'
    
    # Заменяем все URL на ссылки
    result = url_pattern.sub(replace_url, text)
    
    return result

def generate_media_html(item):
    """
    Генерирует HTML-код для медиафайлов из данных JSON
    Включает кликабельные URL для медиафайлов
    """
    media_html = ""
    
    # Изображения
    if 'images' in item and item['images']:
        for i, img in enumerate(item['images']):
            url_html = ""
            if 'url' in img and img['url']:
                url_html = f'<div>Ссылка: <a href="{img["url"]}" class="media-url" target="_blank" rel="noopener noreferrer">Открыть изображение</a></div>'
            
            media_html += f"""
            <div class="media">
                <div class="media-type">🖼️ Изображение {i+1}</div>
                <div class="media-info">
                    <div>Размер: {img.get('width', '?')}x{img.get('height', '?')}</div>
                    <div>Объем: {img.get('file_size', 0) // 1024 if img.get('file_size') else '?'} KB</div>
                    <div>ID: {img.get('file_id', '')[:20]}...</div>
                    {url_html}
                </div>
            </div>
            """
    
    # Видео
    if 'video' in item and item['video']:
        video = item['video']
        url_html = ""
        if 'url' in video and video['url']:
            url_html = f'<div>Ссылка: <a href="{video["url"]}" class="media-url" target="_blank" rel="noopener noreferrer">Открыть видео</a></div>'
        
        media_html += f"""
        <div class="media">
            <div class="media-type">🎥 Видео</div>
            <div class="media-info">
                <div>Разрешение: {video.get('width', '?')}x{video.get('height', '?')}</div>
                <div>Длительность: {video.get('duration', '?')} сек</div>
                <div>Объем: {video.get('file_size', 0) // 1024 if video.get('file_size') else '?'} KB</div>
                <div>Тип: {video.get('mime_type', 'неизвестно')}</div>
                <div>ID: {video.get('file_id', '')[:20]}...</div>
                {url_html}
            </div>
        </div>
        """
    
    # Файлы (документы и аудио)
    if 'files' in item and item['files']:
        for file in item['files']:
            # Определяем тип файла
            mime_type = file.get('mime_type', '')
            file_name = file.get('file_name', '')
            
            url_html = ""
            if 'url' in file and file['url']:
                url_html = f'<div>Ссылка: <a href="{file["url"]}" class="media-url" target="_blank" rel="noopener noreferrer">Открыть файл</a></div>'
            
            if mime_type.startswith('audio/') or 'audio' in mime_type:
                media_type = "🎵 Аудио"
                title = file.get('title') or 'Без названия'
                performer = file.get('performer', 'Неизвестный исполнитель')
                media_html += f"""
                <div class="media">
                    <div class="media-type">{media_type}</div>
                    <div class="media-info">
                        <div>Название: {html.escape(str(title))}</div>
                        <div>Исполнитель: {html.escape(str(performer))}</div>
                        <div>Длительность: {file.get('duration', '?')} сек</div>
                        <div>Объем: {file.get('file_size', 0) // 1024 if file.get('file_size') else '?'} KB</div>
                        <div>Тип: {mime_type}</div>
                        {url_html}
                    </div>
                </div>
                """
            else:
                media_type = "📄 Файл"
                media_html += f"""
                <div class="media">
                    <div class="media-type">{media_type}</div>
                    <div class="media-info">
                        <div>Имя файла: {html.escape(str(file_name))}</div>
                        <div>Объем: {file.get('file_size', 0) // 1024 if file.get('file_size') else '?'} KB</div>
                        <div>Тип: {mime_type}</div>
                        {url_html}
                    </div>
                </div>
                """
    
    # Голосовые сообщения
    if 'voice' in item and item['voice']:
        voice = item['voice']
        url_html = ""
        if 'url' in voice and voice['url']:
            url_html = f'<div>Ссылка: <a href="{voice["url"]}" class="media-url" target="_blank" rel="noopener noreferrer">Открыть голосовое сообщение</a></div>'
        
        media_html += f"""
        <div class="media">
            <div class="media-type">🎤 Голосовое сообщение</div>
            <div class="media-info">
                <div>Длительность: {voice.get('duration', '?')} сек</div>
                <div>Объем: {voice.get('file_size', 0) // 1024 if voice.get('file_size') else '?'} KB</div>
                <div>Тип: {voice.get('mime_type', 'неизвестно')}</div>
                {url_html}
            </div>
        </div>
        """
    
    # Стикеры
    if 'sticker' in item and item['sticker']:
        sticker = item['sticker']
        url_html = ""
        if 'url' in sticker and sticker['url']:
            url_html = f'<div>Ссылка: <a href="{sticker["url"]}" class="media-url" target="_blank" rel="noopener noreferrer">Открыть стикер</a></div>'
        
        media_html += f"""
        <div class="media">
            <div class="media-type">😺 Стикер</div>
            <div class="media-info">
                <div>Размер: {sticker.get('width', '?')}x{sticker.get('height', '?')}</div>
                <div>Эмодзи: {sticker.get('emoji', 'нет')}</div>
                <div>Набор: {sticker.get('set_name', 'неизвестно')}</div>
                {url_html}
            </div>
        </div>
        """
    
    if media_html:
        return f'<div class="media-container">{media_html}</div>'
    return ""

def format_summary(summary: str) -> str:
    if not summary:
        return ""
    
    # Сначала делаем ссылки кликабельными
    summary = make_links_clickable(summary)
    
    # Проверяем нумерованные списки
    if any(marker in summary for marker in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']):
        # Используем регулярное выражение для разбиения по номерам
        import re
        # Паттерн для поиска нумерованных пунктов
        parts = re.split(r'(\n?\s*\d+\.\s*)', summary)
        if len(parts) > 1:
            result = []
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    result.append(f"{parts[i]}{parts[i+1]}")
            return '<br>'.join(result)
    
    # Если есть переносы строк, заменяем их на <br>
    if '\n' in summary:
        lines = [line.strip() for line in summary.split('\n') if line.strip()]
        return '<br>'.join(lines)
    
    return summary

def extract_existing_ids(html_file: str) -> set:
    existing_ids = set()
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        post_id_elements = soup.find_all(class_='post-id')
        for element in post_id_elements:
            text = element.get_text(strip=True)
            if text.startswith('ID:'):
                id_str = text.replace('ID:', '').strip()
                if id_str:
                    existing_ids.add(id_str)
    except Exception as e:
        print(f"Ошибка при чтении существующего HTML: {e}")
    return existing_ids

# JS код вынесен в константу для удобства обновления в обоих случаях (новый файл / обновление)
# new
JS_CODE = """
    let selectedTags = new Set();

    function toggleFullText(id) {
        const el = document.getElementById(id);
        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
    }

    // Вспомогательные функции для дат (оставляем без изменений)
    function getWeekNumber(date) {
        const d = new Date(date);
        d.setHours(0, 0, 0, 0);
        d.setDate(d.getDate() + 4 - (d.getDay() || 7));
        const yearStart = new Date(d.getFullYear(), 0, 1);
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }

    function filterByTag(tag, event) {
        const isMultiSelect = event && (event.ctrlKey || event.metaKey);
        const tagElements = document.querySelectorAll('.tag');

        if (tag === 'all') {
            selectedTags.clear();
            tagElements.forEach(el => el.classList.remove('active-tag'));
        } else {
            if (isMultiSelect) {
                if (selectedTags.has(tag)) {
                    selectedTags.delete(tag);
                } else {
                    selectedTags.add(tag);
                }
            } else {
                // Обычный клик - сброс остальных и выбор одного
                selectedTags.clear();
                selectedTags.add(tag);
            }
        }

        // Обновляем визуальный вид тегов
        tagElements.forEach(el => {
            // Проверяем текст внутри тега или атрибут (зависит от того, как выводится)
            // Для точности ищем по тексту до тире или полному соответствию
            const elTag = el.textContent.split(' — ')[0].trim();
            if (selectedTags.has(elTag)) {
                el.classList.add('active-tag');
            } else {
                el.classList.remove('active-tag');
            }
        });

        applyAllFilters();
    }
    function matchesTimeFilter(post) {
        const period = document.getElementById('period-select').value;
        if (period === 'all') return true;

        const dateStr = post.getAttribute('data-date'); // YYYY-MM-DD
        if (!dateStr) return true;

        const postDate = new Date(dateStr + 'T00:00:00'); // чтобы не было сдвигов по времени
        const postYear = String(postDate.getFullYear());
        const postMonth = String(postDate.getMonth() + 1).padStart(2, '0');
        const postYearMonth = `${postYear}-${postMonth}`;

        if (period === 'date') {
            const selectedDate = document.getElementById('date-input').value; // YYYY-MM-DD
            return selectedDate ? (dateStr === selectedDate) : true;
        }

        // Для year/quarter/month/week нужен year-input (как у вас задумано)
        const selectedYear = document.getElementById('year-input').value;
        if (!selectedYear) return true;

        if (period === 'year') {
            return postYear === selectedYear;
        }

        if (period === 'quarter') {
            const q = document.getElementById('quarter-input').value; // "1".."4"
            if (!q) return true;
            const quarter = Math.floor((postDate.getMonth()) / 3) + 1;
            return postYear === selectedYear && String(quarter) === String(q);
        }

        if (period === 'month') {
            const selectedMonth = document.getElementById('month-input').value; // YYYY-MM
            return selectedMonth ? (postYearMonth === selectedMonth) : true;
        }

        if (period === 'week') {
            const selectedWeek = document.getElementById('week-input').value; // YYYY-W
            if (!selectedWeek) return true;
            const week = getWeekNumber(postDate);
            const key = `${postDate.getFullYear()}-${week}`;
            return key === selectedWeek;
        }

        return true;
    }
    function applyAllFilters() {
        const posts = document.querySelectorAll('.post');

        posts.forEach(post => {
            const postTags = JSON.parse(post.getAttribute('data-tags') || '[]');

        // теги: ИЛИ (как у вас)
            const matchesTag = selectedTags.size === 0 || postTags.some(t => selectedTags.has(t));

        // время:
            const matchesTime = matchesTimeFilter(post);

            post.style.display = (matchesTag && matchesTime) ? 'block' : 'none';
        });
    }

    // Функции заполнения фильтров дат (остаются как были в вашем коде)
    function populateYears() {
        const yearSelect = document.getElementById('year-input');
        const years = new Set();
        document.querySelectorAll('.post').forEach(post => {
            const dateStr = post.getAttribute('data-date');
            if (dateStr) years.add(dateStr.split('-')[0]);
        });
        yearSelect.innerHTML = '<option value="">Выберите год</option>';
        Array.from(years).sort().reverse().forEach(year => {
            const option = document.createElement('option');
            option.value = year; option.textContent = year;
            yearSelect.appendChild(option);
        });
    }
    
    function populateDates() {
        const dateSelect = document.getElementById('date-input');
        const dates = new Set();
        document.querySelectorAll('.post').forEach(post => {
            const dateStr = post.getAttribute('data-date');
            if (dateStr) dates.add(dateStr);
        });
        dateSelect.innerHTML = '<option value="">Выберите дату</option>';
        Array.from(dates).sort().reverse().forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            const [y, m, d] = date.split('-');
            option.textContent = `${d}.${m}.${y}`;
            dateSelect.appendChild(option);
        });
    }

    function populateMonths() {
        const monthSelect = document.getElementById('month-input');
        monthSelect.innerHTML = '<option value="">Выберите месяц</option>';
        const monthsSet = new Set();
        document.querySelectorAll('.post').forEach(post => {
            const dateStr = post.getAttribute('data-date');
            if (dateStr) {
                const [year, month] = dateStr.split('-');
                monthsSet.add(`${year}-${month}`);
            }
        });
        Array.from(monthsSet).sort().reverse().forEach(month => {
            const [year, monthNum] = month.split('-');
            const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
            const option = document.createElement('option');
            option.value = month;
            option.textContent = `${monthNames[parseInt(monthNum)-1]} ${year}`;
            monthSelect.appendChild(option);
        });
    }

    function populateWeeks() {
        const weekSelect = document.getElementById('week-input');
        weekSelect.innerHTML = '<option value="">Выберите неделю</option>';
        const weeksSet = new Set();
        document.querySelectorAll('.post').forEach(post => {
            const dateStr = post.getAttribute('data-date');
            if (dateStr) {
                const d = new Date(dateStr);
                const week = getWeekNumber(d);
                const year = d.getFullYear();
                weeksSet.add(`${year}-${week}`);
            }
        });
        Array.from(weeksSet).sort().reverse().forEach(week => {
            const [year, weekNum] = week.split('-');
            const option = document.createElement('option');
            option.value = week;
            option.textContent = `Неделя ${weekNum}, ${year}`;
            weekSelect.appendChild(option);
        });
    }

    function togglePeriodInputs() {
        ['year-input', 'quarter-input', 'month-input', 'week-input', 'date-input'].forEach(id => {
            document.getElementById(id).style.display = 'none';
        });
        const period = document.getElementById('period-select').value;
        if (period === 'date') {
            document.getElementById('date-input').style.display = 'inline-block';
        } else if (period !== 'all') {
            document.getElementById('year-input').style.display = 'inline-block';
            if (period !== 'year') document.getElementById(period + '-input').style.display = 'inline-block';
        }
        applyAllFilters();
    }

    function applyTimeFilter() {
        // Упрощенная логика совмещения фильтров может быть добавлена здесь
        applyAllFilters(); 
    }

    function resetTimeFilter() {
        document.getElementById('period-select').value = 'all';
        togglePeriodInputs();
        selectedTags.clear();
        document.querySelectorAll('.tag').forEach(el => el.classList.remove('active-tag'));
        applyAllFilters();
    }

    document.addEventListener('DOMContentLoaded', () => {
        populateYears();
        populateDates();
        populateMonths();
        populateWeeks();
        togglePeriodInputs();
    });
"""
# new
def generate_new_posts_html(data, existing_ids):
    new_posts_html = ""
    tag_to_name = {}
    
    # Фильтруем данные перед обработкой
    filtered_data = [item for item in data if item.get('text') != "Текст отсутствует"]
    
    for item in filtered_data:
        if str(item.get('id', '')) not in existing_ids:
            for t, n in zip(item.get('tags', []), item.get('name', [])):
                if t not in tag_to_name: tag_to_name[t] = n
    
    all_tags = sorted(list(tag_to_name.keys()))
    tag_filter_html = '<span class="tag" onclick="filterByTag(\'all\')">Все теги</span>'
    for tag in all_tags:
        tag_filter_html += f'<span class="tag" title="{html.escape(tag_to_name[tag])}" onclick="filterByTag(\'{tag}\', event)">{tag}</span>'
    
    for item in filtered_data:
        record_id = str(item.get('id', ''))
        if record_id in existing_ids: continue
        
        post_date = datetime.fromisoformat(item['date']).strftime('%d %B %Y, %H:%M')
        iso_date = item['date'][:10]
        tags_html = ''.join([f'<span class="tag" onclick="filterByTag(\'{t}\', event)">{t} — {n}</span>' for t, n in zip(item.get('tags', []), item.get('name', []))])
        
        summary_text = item.get('summary_processed') or item.get('summary', '')
        formatted_summary = format_summary(summary_text)
        
        heading = html.escape(item.get('heading', 'Без заголовка'))
        raw_text = item.get('text', '')
        processed_text = make_links_clickable(raw_text)
        
        text_id = f"text-{record_id}"
        media_html = generate_media_html(item)
        
        new_posts_html += f"""
        <div class="post" data-tags='{json.dumps(item["tags"])}' data-date='{iso_date}'>
            <div class="post-id">ID: {record_id}</div>
            <div class="post-date">📅 {post_date}</div>
            <div class="post-heading" onclick="toggleFullText('{text_id}')">{heading}</div>
            <div id="{text_id}" class="full-text">
                <div class="text-content">{processed_text}</div>
                {media_html}
            </div>
            <div class="post-summary">{formatted_summary}</div>
            <div class="post-tags">🏷️ {tags_html}</div>
        </div>
        """
    return new_posts_html, tag_filter_html

def generate_html():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # ГЛАВНОЕ ИЗМЕНЕНИЕ: Исключаем записи с текстом "Текст отсутствует"
    data = [item for item in data if item.get('text') != "Текст отсутствует"]
    # сортировка по дате в обратном порядке - делаю до этого скрипта
    #data.sort(key=lambda x: x.get('date', ''), reverse=True)        
    
    if os.path.exists(OUTPUT_HTML):
        existing_ids = extract_existing_ids(OUTPUT_HTML)
        new_posts_html, _ = generate_new_posts_html(data, existing_ids)
        
        if new_posts_html:
            with open(OUTPUT_HTML, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            posts_container = soup.find('div', id='posts-container')
            if posts_container:
                new_content = BeautifulSoup(new_posts_html, 'html.parser')
                posts_container.insert(0, new_content)
            
            # Обновление стилей и скриптов (как в вашем коде)
            style_tag = soup.find('style')
            if style_tag and '.text-link' not in style_tag.string:
                style_tag.string += MEDIA_CSS
            
            scripts = soup.find_all('script')
            if scripts: scripts[-1].string = JS_CODE
            
            with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"Обновлено. Добавлены новые записи, кроме пустых.")
    else:
        # Логика создания нового файла (также с отфильтрованными данными)
        tag_to_name = {}
        for item in data:
            for t, n in zip(item.get('tags', []), item.get('name', [])):
                if t not in tag_to_name: tag_to_name[t] = n
        
        tags_html = "".join([f'<span class="tag" title="{html.escape(tag_to_name[t])}" onclick="filterByTag(\'{t}\', event)">{t}</span>' for t in sorted(tag_to_name.keys())])
        
        posts_html = ""
        for idx, item in enumerate(data):
            record_id = item.get('id', '')
            post_date = datetime.fromisoformat(item['date']).strftime('%d %B %Y, %H:%M')
            iso_date = item['date'][:10]
            tags_block = "".join([f'<span class="tag" onclick="filterByTag(\'{t}\', event)">{t} — {n}</span>' for t, n in zip(item.get('tags', []), item.get('name', []))])
            text_id = f"text-{record_id}"
            
            summary_text = item.get('summary_processed') or item.get('summary', '')
            formatted_summary = format_summary(summary_text)
            processed_text = make_links_clickable(item.get('text', ''))
            media_html = generate_media_html(item)
            
            posts_html += f"""
            <div class="post" data-tags='{json.dumps(item["tags"])}' data-date='{iso_date}'>
                <div class="post-id">ID: {record_id}</div>
                <div class="post-date">📅 {post_date}</div>
                <div class="post-heading" onclick="toggleFullText('{text_id}')">{html.escape(item.get('heading', ''))}</div>
                <div id="{text_id}" class="full-text">
                    <div class="text-content">{processed_text}</div>
                    {media_html}
                </div>
                <div class="post-summary">{formatted_summary}</div>
                <div class="post-tags">🏷️ {tags_block}</div>
            </div>
            """

        # ... (сборка full_html и запись в файл аналогично оригиналу) ...
        # new
        full_html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><title>Дайджест</title>
<style>
    body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f9f9f9; }}
    .post {{ background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .post-heading {{ color: #2c5282; font-weight: bold; cursor: pointer; text-decoration: underline; }}
    .full-text {{ display: none; background: #f0f4f8; padding: 15px; margin: 10px 0; }}
    .text-content {{ white-space: pre-wrap; word-wrap: break-word; }}
    .tag {{ cursor: pointer; background: #eef6ff; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 0.8em; }}
    .tag.active-tag {{ background: #2c5282; color: white; font-weight: bold; }}   /* теги фильтра */
    #time-filter, #tag-filter {{ background: #fff; padding: 15px; margin-bottom: 10px; border-radius: 8px; }}
    .post-id {{ display: none; }}
    #date-input, #year-input, #quarter-input, #month-input, #week-input {{ display: none; }}
    {MEDIA_CSS}
</style>
</head><body>
<div id="time-filter">
    <select id="period-select" onchange="togglePeriodInputs()">
        <option value="all">Всё</option><option value="year">За год</option>
        <option value="quarter">За квартал</option><option value="month">За месяц</option>
        <option value="week">За неделю</option><option value="date">Дата</option>
    </select>
    <select id="year-input"></select>
    <select id="quarter-input"><option value="">Квартал</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option></select>
    <select id="month-input"></select><select id="week-input"></select><select id="date-input"></select>
    <button onclick="applyTimeFilter()">Применить</button><button onclick="resetTimeFilter()">Сброс</button>
</div>
<div id="tag-filter"><span class="tag" onclick="filterByTag('all')">Все</span>{tags_html}</div>
<div id="posts-container">{posts_html}</div>
<script>{JS_CODE}</script></body></html>"""
        
        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print("Создан новый файл.")

if __name__ == '__main__':
    generate_html()