Дайджест новостей тематической информации клуба BIARCO — «Бизнес ИТ Архитектурные Концепции» (на русском языке).

Создан AI- Workflow – с помощью Телеграм–бота скачиваются обновления сообщений телеграм-канала, для каждого сообщения на основе API-ключа создаются саммари и определяются теги. Затем из этих записей формируются обновления сайта, где самые свежие записи всегда размещаются вверху. В шапке сайта размещено облако тегов из записей и условия фильтров по дате или по тегам.

Данный Workflow запускается автоматически на Github каждое утро.
Этот проект объединяет в себе работу с API, обработку текста с помощью ИИ и веб-разработку. Процесс разбит на несколько логических этапов.

Общая концепция (Архитектура)

Воркфлоу состоит из трех основных компонентов:

1.	Сборщик данных (Data Collector): Телеграм-бот подключается к каналу заказчика и сохраняет все новые сообщения.
2.	Обработчик данных и AI (Data Processor & AI): Скрипт совместно с модулем AI  периодически (раз в день) забирает сохраненные сообщения, извлекает из них теги, даты и основную мысль, а затем структурирует их.
3.	Генератор страницы (Page Generator): Инструмент, который берёт обработанные данные и добавляет их в статическую HTML-страницу (дайджест).
   
Используется связка из Python для бота и обработки данных, API-ключ в YandexGpt для получения саммари и GitHub Pages для бесплатного хостинга веб-страницы дайджеста.
*******************************************************************************************************************************************************************************

News Digest of thematic information from the BIARCO Club — "Business IT Architectural Concepts" (in Russian).

An AI workflow has been created: a Telegram bot downloads updates from a Telegram channel, and for each message, a summary and tags are generated via an API key. These records are then used to update a website, where the most recent entries are always displayed at the top. The website header features a tag cloud derived from the posts, along with filter options by date or tag.

This workflow runs automatically on GitHub every morning.
The project combines API integration, AI-powered text processing, and web development. The process is divided into several logical stages.

General Concept (Architecture)

The workflow consists of three main components:

1. Data Collector: A Telegram bot connects to the client's channel and saves all new messages.
2. Data Processor & AI: A script, working with an AI module, periodically (once a day) retrieves the saved messages, extracts tags, dates, and key insights, and then structures the data.
3. Page Generator: A tool that takes the processed data and adds it to a static HTML page (digest).
   
The system uses a combination of Python for the bot and data processing, a YandexGPT API key for generating summaries, and GitHub Pages for free hosting of the digest webpage.
