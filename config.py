"""
Конфигурация для Work.ua Parser
"""

# URL настройки
BASE_URL = "https://www.work.ua/resumes-%D0%B1%D1%83%D1%85%D0%B3%D0%B0%D0%BB%D1%82%D0%B5%D1%80/"

# Селекторы для элементов на странице
SELECTORS = {
    "resume_cards": ".card.resume-link",  # Обновленный селектор - работает лучше
    "card_title": "h2 a",
    "card_salary": ".h5.strong-600",
    "card_name": ".strong-600",
    "card_age": "p:nth-child(4)",
    "card_location": "p:nth-child(4)",
    "card_experience": "ul li",
    
    # Селекторы пагинации с автоадаптацией
    "pagination_next": ".pagination li:last-child",  # РАБОЧИЙ СЕЛЕКТОР! Найден через тестирование
    "pagination_container": "#pjax-resume-list > nav",
    "pagination_current": "li.active",
    "pagination_links": "ul.pagination li",
    
    # Альтернативные селекторы пагинации (fallback)
    "pagination_next_alt": [
        ".pagination .next",
        "a[rel='next']", 
        ".page-link:contains('Наступна')",
        ".page-link:contains('>')",
        "li:last-child a",
        ".pagination li:last-child"
    ]
}

# Настройки браузера
BROWSER_CONFIG = {
    "headless": False,  # Показывать браузер или нет
    "window_size": (1920, 1080),
    "page_load_timeout": 30,
    "implicit_wait": 10
}

# Настройки парсинга
PARSING_CONFIG = {
    "delay_between_pages": 2,  # секунды
    "delay_between_cards": 1,  # секунды
    "max_retries": 3,
    
    # Настройки пагинации
    "max_pages": 10,  # Максимальное количество страниц для парсинга (10 страниц)
    "max_cards_per_page": 14,  # Максимальное количество карточек на странице (все карточки)
    "pagination_wait_timeout": 15,  # Время ожидания загрузки страницы
    "pagination_retry_attempts": 3,  # Попытки при ошибках пагинации
    "enable_pagination": True,  # Включить обработку пагинации
    "pagination_auto_adapt": True  # Автоматическая адаптация селекторов пагинации
}

# Настройки сохранения данных
OUTPUT_CONFIG = {
    "csv_filename": "work_ua_resumes.csv",
    "json_filename": "work_ua_resumes.json"
} 