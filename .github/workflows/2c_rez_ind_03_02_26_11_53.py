import json
from datetime import datetime

# Константы файлов
INPUT_DIGEST = 'digest_itogi.json'
BASE_REZ = 'rez_ind.json'
OUTPUT_FILE = 'rez_ind.json'

def process_data():
    # 1. Загрузка данных
    try:
        with open(INPUT_DIGEST, 'r', encoding='utf-8') as f:
            digest_data = json.load(f)
    except FileNotFoundError:
        print(f"Файл {INPUT_DIGEST} не найден.")
        return

    try:
        with open(BASE_REZ, 'r', encoding='utf-8') as f:
            rez_data = json.load(f)
    except FileNotFoundError:
        rez_data = []

    # 2. Сортировка digest_itogi.json по уменьшению дат
    # Используем reverse=True для сортировки от новых к старым
    digest_data.sort(key=lambda x: x.get('date', ''), reverse=True)

    filtered_digest = []

    for item in digest_data:
        # Извлекаем поля для удобства
        text = item.get('text', '').strip()
        caption = item.get('caption', '').strip()
        heading = item.get('heading', '').strip()
        url = item.get('url', '').strip()
        summary = item.get('summary', '').strip()

        # Проверка на наличие контента
        has_text_content = (text != "" and text != "Текст отсутствует") or \
                           (caption != "" and caption != "Текст отсутствует")
        
        has_url = url != ""
        
        bad_summary = (summary == "Не удалось извлечь текст для саммаризации")

        # УСЛОВИЕ ИСКЛЮЧЕНИЯ:
        # Если (нет текста и нет заголовка) И (нет URL и плохое саммари) -> Пропускаем
        if not has_text_content and heading == "" and not has_url and bad_summary:
            continue

        # ЛОГИКА ТРАНСФОРМАЦИИ ПЕРЕД ДОБАВЛЕНИЕМ:
        
        # Если "summary" плохое и "heading" пустое, но есть URL
        if bad_summary and heading == "" and has_url:
            item['summary'] = "Ссылка"
            item['heading'] = "Ссылка"
        
        # Если "summary" плохое, но заголовок есть И (есть URL или какой-то текст)
        elif bad_summary and heading != "" and (has_url or has_text_content):
            item['summary'] = item['heading']

        filtered_digest.append(item)

    # 3. Добавление в начало (Сначала новые данные из диджеста, потом старые из индекса)
    # Чтобы избежать дубликатов (если скрипт запущен повторно), можно проверять по id
    existing_ids = {entry.get('id') for entry in rez_data}
    new_entries = [d for d in filtered_digest if d.get('id') not in existing_ids]

    final_data = new_entries + rez_data

    # 4. Сохранение результата
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"Обработка завершена. Добавлено новых записей: {len(new_entries)}")

if __name__ == "__main__":
    process_data()