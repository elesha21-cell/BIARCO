
#Bash
#pip install python-telegram-bot python-dotenv

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot, File
from typing import Optional, Set, List, Dict, Any

OUTPUT_FILE = 'messages.json'
SEEN_MESSAGES_FILE = 'seen_messages.txt'  # Для отслеживания уже обработанных сообщений

def extract_heading(text: str) -> str:
    """
    Извлекает заголовок из текста сообщения.
    Заголовок - это первая жирная строка после тегов, если они есть.
    Жирный текст определяется по разметке Markdown (**текст**) или HTML (<b>текст</b>).
    """
    if not text:
        return ""
    
    # Убираем начальные и конечные пробелы
    text = text.strip()
    
    # Сначала ищем жирный текст в Markdown формате
    lines = text.split('\n')
    
    # Пропускаем строки с тегами (они обычно в начале или в конце)
    # Теги обычно начинаются с # или содержат тег в квадратных скобках
    for i, line in enumerate(lines):
        line_trimmed = line.strip()
        
        # Пропускаем пустые строки
        if not line_trimmed:
            continue
            
        # Пропускаем строки с тегами
        if line_trimmed.startswith('#') or '[' in line_trimmed and ']' in line_trimmed:
            continue
            
        # Проверяем, является ли строка жирной в Markdown
        # Жирный текст: **текст** или __текст__
        if line_trimmed.startswith('**') and line_trimmed.endswith('**'):
            # Убираем ** с обеих сторон
            heading = line_trimmed[2:-2].strip()
            if heading:
                return heading
        elif line_trimmed.startswith('__') and line_trimmed.endswith('__'):
            # Убираем __ с обеих сторон
            heading = line_trimmed[2:-2].strip()
            if heading:
                return heading
                
        # Проверяем, является ли строка жирной в HTML
        elif line_trimmed.startswith('<b>') and line_trimmed.endswith('</b>'):
            # Убираем <b> и </b>
            heading = line_trimmed[3:-4].strip()
            if heading:
                return heading
        elif line_trimmed.startswith('<strong>') and line_trimmed.endswith('</strong>'):
            # Убираем <strong> и </strong>
            heading = line_trimmed[8:-9].strip()
            if heading:
                return heading
    
    # Если не нашли жирную строку, берем первую непустую строку без тегов
    for i, line in enumerate(lines):
        line_trimmed = line.strip()
        
        # Пропускаем пустые строки и строки с тегами
        if not line_trimmed:
            continue
        if line_trimmed.startswith('#') or '[' in line_trimmed and ']' in line_trimmed:
            continue
            
        # Если строка содержит жирный текст внутри (не полностью жирная)
        # Извлекаем жирный текст из строки
        import re
        
        # Ищем **текст** в строке
        bold_matches = re.findall(r'\*\*(.*?)\*\*', line_trimmed)
        if bold_matches:
            return bold_matches[0].strip()
            
        # Ищем __текст__ в строке
        bold_matches = re.findall(r'__(.*?)__', line_trimmed)
        if bold_matches:
            return bold_matches[0].strip()
            
        # Ищем <b>текст</b> в строке
        bold_matches = re.findall(r'<b>(.*?)</b>', line_trimmed)
        if bold_matches:
            return bold_matches[0].strip()
            
        # Ищем <strong>текст</strong> в строке
        bold_matches = re.findall(r'<strong>(.*?)</strong>', line_trimmed)
        if bold_matches:
            return bold_matches[0].strip()
    
    # Если ничего не нашли, возвращаем пустую строку
    return ""

async def get_media_url(bot: Bot, file_id: str, token: str) -> Optional[str]:
    """
    Получает HTTP-адрес медиафайла по его file_id
    """
    try:
        # Получаем информацию о файле
        file: File = await bot.get_file(file_id)
        
        # Формируем HTTP-адрес для скачивания
        # Формат: https://api.telegram.org/file/bot<TOKEN>/<file_path>
        file_path = file.file_path
        if file_path:
            url = f"https://api.telegram.org/file/bot{token}/{file_path}"
            return url
        else:
            print(f"⚠️ Не удалось получить file_path для file_id: {file_id}")
            return None
    except Exception as e:
        print(f"⚠️ Ошибка при получении URL для файла {file_id}: {e}")
        return None

async def poll_channel_posts(token: str, channel_id: Optional[int] = None):
    """
    Асинхронно опрашивает канал Telegram на новые сообщения
    Args:
        token: Токен бота Telegram
        channel_id: Опциональный ID канала для фильтрации
    """
    bot = Bot(token=token)
    offset = None
    
    # Загружаем уже обработанные сообщения (чтобы избежать дубликатов)
    seen_message_ids: Set[int] = set()
    if os.path.exists(SEEN_MESSAGES_FILE):
        try:
            with open(SEEN_MESSAGES_FILE, 'r') as f:
                seen_message_ids = {int(line.strip()) for line in f if line.strip()}
        except Exception as e:
            print(f"⚠️ Не удалось загрузить seen_messages: {e}")
    
    # Загружаем существующие сообщения (если файл уже есть)
    all_messages = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                all_messages = json.load(f)
                # Сохраняем ID всех уже сохраненных сообщений
                seen_message_ids.update(msg['id'] for msg in all_messages)
            print(f"📂 Файл {OUTPUT_FILE} найден. Загружено сообщений: {len(all_messages)}")
        except Exception as e:
            print(f"⚠️ Файл {OUTPUT_FILE} поврежден или пуст: {e}")
    else:
        print(f"📝 Файл {OUTPUT_FILE} ещё не создан (будет создан при получении новых сообщений). ")  #Нажмите Ctrl+C для остановки
 
    try:
        # Проверяем авторизацию в начале
        try:
            me = await bot.get_me()
            print(f"✅ Бот авторизован как @{me.username}")
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            await bot.close()
            sys.exit(1)
        
        #while True:
# Устанавливаем флаг для выхода
        has_more_updates = True
        
        while has_more_updates:
            try:
                # Получаем обновления (timeout ставим маленький, так как нам нужны текущие данные)
                updates = await bot.get_updates(
                    offset=offset, 
                    timeout=1, 
                    allowed_updates=['channel_post', 'message']
                )
            except Exception as e:
                print(f"❌ Фатальная ошибка при получении updates: {e}")
                await bot.close()
                sys.exit(1)
            
            if not updates:
                # Если обновлений больше нет, выходим из цикла
                has_more_updates = False
                continue
            new_messages = []
            for upd in updates:
                offset = upd.update_id + 1
                
                if upd.channel_post:
                    post = upd.channel_post
                    
                    # Пропускаем уже обработанные сообщения
                    if post.message_id in seen_message_ids:
                        continue
                    
                    # Фильтрация по channel_id если указан
                    if channel_id is not None and post.chat.id != channel_id:
                        continue
                    
                    print(f"Channel post: chat_id={post.chat.id}, "
                          f"message_id={post.message_id}, "
                          f"date={post.date.isoformat()}")
                    
                    # Собираем информацию о сообщении
                    message_data = {
                        'id': post.message_id,
                        'chat_id': post.chat.id,
                        'date': post.date.isoformat(),
                        'type': 'channel_post'
                    }
                    
                    # Получаем текст сообщения (текст или подпись)
                    message_text = None
                    if post.text:
                        message_text = post.text
                        message_data['text'] = post.text
                        print(f"    Text: {post.text[:100]}...")
                    elif post.caption:
                        message_text = post.caption
                        message_data['caption'] = post.caption
                        print(f"    Caption: {post.caption[:100]}...")
                    
                    # Извлекаем заголовок из текста
                    if message_text:
                        heading = extract_heading(message_text)
                        if heading:
                            message_data['heading'] = heading
                            print(f"    Heading: {heading}")
                    
                    # Добавляем информацию о медиафайлах
                    # Изображения
                    if post.photo:
                        images = []
                        # photo - это список PhotoSize объектов (разные размеры)
                        # Берем фото с максимальным размером (последний в списке)
                        largest_photo = post.photo[-1]
                        image_info = {
                            'file_id': largest_photo.file_id,
                            'file_unique_id': largest_photo.file_unique_id,
                            'width': largest_photo.width,
                            'height': largest_photo.height,
                            'file_size': getattr(largest_photo, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для изображения
                        image_url = await get_media_url(bot, largest_photo.file_id, token)
                        if image_url:
                            image_info['url'] = image_url
                            print(f"    Image URL: {image_url}")
                        
                        images.append(image_info)
                        message_data['images'] = images
                        print(f"    Has {len(post.photo)} photo(s), saved largest one: {largest_photo.width}x{largest_photo.height}")
                    
                    # Видео
                    if post.video:
                        video_info = {
                            'file_id': post.video.file_id,
                            'file_unique_id': post.video.file_unique_id,
                            'width': post.video.width,
                            'height': post.video.height,
                            'duration': post.video.duration,
                            'mime_type': getattr(post.video, 'mime_type', None),
                            'file_size': getattr(post.video, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для видео
                        video_url = await get_media_url(bot, post.video.file_id, token)
                        if video_url:
                            video_info['url'] = video_url
                            print(f"    Video URL: {video_url}")
                        
                        message_data['video'] = video_info
                        print(f"    Has video: {post.video.width}x{post.video.height}, {post.video.duration}s")
                    
                    # Документы (файлы)
                    if post.document:
                        document_info = {
                            'file_id': post.document.file_id,
                            'file_unique_id': post.document.file_unique_id,
                            'file_name': post.document.file_name,
                            'mime_type': getattr(post.document, 'mime_type', None),
                            'file_size': getattr(post.document, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для документа
                        document_url = await get_media_url(bot, post.document.file_id, token)
                        if document_url:
                            document_info['url'] = document_url
                            print(f"    Document URL: {document_url}")
                        
                        # Создаем поле 'files' как список документов
                        message_data['files'] = [document_info]
                        print(f"    Document: {post.document.file_name}")
                    
                    # Аудио
                    if post.audio:
                        audio_info = {
                            'file_id': post.audio.file_id,
                            'file_unique_id': post.audio.file_unique_id,
                            'duration': post.audio.duration,
                            'performer': getattr(post.audio, 'performer', None),
                            'title': getattr(post.audio, 'title', None),
                            'mime_type': getattr(post.audio, 'mime_type', None),
                            'file_size': getattr(post.audio, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для аудио
                        audio_url = await get_media_url(bot, post.audio.file_id, token)
                        if audio_url:
                            audio_info['url'] = audio_url
                            print(f"    Audio URL: {audio_url}")
                        
                        # Добавляем аудио в список файлов или создаем отдельное поле
                        if 'files' not in message_data:
                            message_data['files'] = []
                        message_data['files'].append(audio_info)
                        print(f"    Audio: {getattr(post.audio, 'title', 'Untitled')}")
                    
                    # Голосовые сообщения
                    if post.voice:
                        voice_info = {
                            'file_id': post.voice.file_id,
                            'file_unique_id': post.voice.file_unique_id,
                            'duration': post.voice.duration,
                            'mime_type': getattr(post.voice, 'mime_type', None),
                            'file_size': getattr(post.voice, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для голосового сообщения
                        voice_url = await get_media_url(bot, post.voice.file_id, token)
                        if voice_url:
                            voice_info['url'] = voice_url
                            print(f"    Voice URL: {voice_url}")
                        
                        message_data['voice'] = voice_info
                        print(f"    Voice message: {post.voice.duration}s")
                    
                    # Стикеры
                    if post.sticker:
                        sticker_info = {
                            'file_id': post.sticker.file_id,
                            'file_unique_id': post.sticker.file_unique_id,
                            'width': post.sticker.width,
                            'height': post.sticker.height,
                            'emoji': getattr(post.sticker, 'emoji', None),
                            'set_name': getattr(post.sticker, 'set_name', None)
                        }
                        
                        # Получаем HTTP-адрес для стикера
                        sticker_url = await get_media_url(bot, post.sticker.file_id, token)
                        if sticker_url:
                            sticker_info['url'] = sticker_url
                            print(f"    Sticker URL: {sticker_url}")
                        
                        message_data['sticker'] = sticker_info
                        print(f"    Sticker: {getattr(post.sticker, 'emoji', '')}")
                    
                    new_messages.append(message_data)
                    seen_message_ids.add(post.message_id)
                
                elif upd.message:
                    msg = upd.message
                    # Пропускаем уже обработанные сообщения
                    if msg.message_id in seen_message_ids:
                        continue
                    
                    print(f"Message: chat_id={msg.chat.id}, "
                          f"message_id={msg.message_id}")
                    
                    message_data = {
                        'id': msg.message_id,
                        'chat_id': msg.chat.id,
                        'date': msg.date.isoformat(),
                        'type': 'private_message',
                        'from_user_id': msg.from_user.id if msg.from_user else None,
                        'from_user_name': msg.from_user.username if msg.from_user else None
                    }
                    
                    if msg.text:
                        message_data['text'] = msg.text
                        print(f"    Text: {msg.text[:100]}...")
                        
                        # Извлекаем заголовок из текста
                        heading = extract_heading(msg.text)
                        if heading:
                            message_data['heading'] = heading
                            print(f"    Heading: {heading}")
                    
                    # Обработка медиа в личных сообщениях
                    # Изображения
                    if msg.photo:
                        images = []
                        largest_photo = msg.photo[-1]
                        image_info = {
                            'file_id': largest_photo.file_id,
                            'file_unique_id': largest_photo.file_unique_id,
                            'width': largest_photo.width,
                            'height': largest_photo.height,
                            'file_size': getattr(largest_photo, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для изображения
                        image_url = await get_media_url(bot, largest_photo.file_id, token)
                        if image_url:
                            image_info['url'] = image_url
                            print(f"    Image URL: {image_url}")
                        
                        images.append(image_info)
                        message_data['images'] = images
                        print(f"    Has {len(msg.photo)} photo(s)")
                    
                    # Документы (файлы)
                    if msg.document:
                        document_info = {
                            'file_id': msg.document.file_id,
                            'file_unique_id': msg.document.file_unique_id,
                            'file_name': msg.document.file_name,
                            'mime_type': getattr(msg.document, 'mime_type', None),
                            'file_size': getattr(msg.document, 'file_size', None)
                        }
                        
                        # Получаем HTTP-адрес для документа
                        document_url = await get_media_url(bot, msg.document.file_id, token)
                        if document_url:
                            document_info['url'] = document_url
                            print(f"    Document URL: {document_url}")
                        
                        message_data['files'] = [document_info]
                        print(f"    Document: {msg.document.file_name}")
                    
                    new_messages.append(message_data)
                    seen_message_ids.add(msg.message_id)
            
            # Сохраняем новые сообщения, если они есть
            if new_messages:
                # Добавляем новые сообщения к существующим
                all_messages.extend(new_messages)
                
                # Сортируем по ID (хронологически)
                all_messages.sort(key=lambda x: x['id'])
                
                # Сохраняем в файл
                try:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(all_messages, f, ensure_ascii=False, indent=4, 
                                 default=str)  # default=str для обработки дат
                    
                    print(f"✅ Сохранено {len(new_messages)} новых сообщений")
                    print(f"📊 Всего сообщений в файле: {len(all_messages)}")
                    
                    # Обновляем файл с обработанными ID
                    with open(SEEN_MESSAGES_FILE, 'w') as f:
                        for msg_id in sorted(seen_message_ids):
                            f.write(f"{msg_id}\n")
                    
                except Exception as e:
                    print(f"❌ Ошибка при сохранении в файл: {e}")
            
            await asyncio.sleep(1)  # Пауза между проверками - порекомендовал AI
            # ВАЖНО: После обработки первой порции обновлений 
            # мы можем либо сразу выйти, либо проверить, нет ли еще данных.
            # По умолчанию Telegram отдает до 100 сообщений за раз.
            # Если вернулось меньше 100, скорее всего, это всё.
            if len(updates) < 100:
                has_more_updates = False

        print("✅ Все актуальные сообщения получены и сохранены. Завершение работы...")
            
    except asyncio.CancelledError:
        print("\n🛑 Опрос отменен")
        raise
    except Exception as e:
        print(f"❌ Фатальная ошибка в poll_channel_posts: {e}")
        sys.exit(1)
    finally:
        try:
            await bot.close()
        except Exception:
            pass
        finally:
            print("✅ Ресурсы освобождены")


if __name__ == '__main__':
    # 1. Загружаем переменные из файла .env (если он есть)
    load_dotenv()

    # 2. Получаем токен из переменных окружения
    # Убедитесь, что в вашем .env файле есть строка: TELEGRAM_TOKEN=ваш_токен
    token = os.getenv("TELEGRAM_TOKEN")
    
    # 3. Теперь проверка на существование token сработает корректно
    if not token:
        print("❌ TELEGRAM_TOKEN не задан в окружении.")
        print("Создайте файл .env и добавьте туда: TELEGRAM_TOKEN=ваш_токен_бота")
        sys.exit(1)
    
    try:
        print(f"✅ Запуск опроса с токеном длиной {len(token)} символов✅ ")
        print(f"Сообщения будут сохраняться в: {OUTPUT_FILE}\n")
        #print("Нажмите Ctrl+C для остановки\n") 
        
        asyncio.run(poll_channel_posts(token))
        
    except KeyboardInterrupt:
        print("\n✅ Программа остановлена пользователем")
        sys.exit(0)
    except SystemExit as e:
        # Это предотвращает повторный вывод ошибки при sys.exit(1)
        pass 
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)