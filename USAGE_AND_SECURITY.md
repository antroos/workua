# Руководство по использованию парсера Work.ua

## 1. Быстрый старт

### 1.1 Установка
```bash
# Клонируем репозиторий
git clone https://github.com/antroos/workua.git
cd workua

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 1.2 Базовый запуск
```bash
# Запуск парсера
python ultimate_parser.py

# Просмотр результатов через веб-интерфейс
python start_viewer.py
# Откройте в браузере: http://localhost:8000/view_database.html
```

## 2. Стратегии парсинга

### 2.1 Пошаговый парсинг
1. Начните с малого количества страниц (10-20)
2. Проверьте качество данных
3. Постепенно увеличивайте объем
4. Используйте чекпоинты для возможности продолжения

```python
# config.py
PARSING_CONFIG = {
    "max_pages": 20,  # Начните с малого
    "enable_checkpoints": True
}
```

### 2.2 Оптимальные настройки
- Время между страницами: 2-3 секунды
- Время между карточками: 1-2 секунды
- Параллельные вкладки: 2-3
- Размер пакета: 100-200 резюме

## 3. Механизмы защиты и их обход

### 3.1 Защита от блокировки IP

#### Используемые механизмы:
1. Динамические задержки
```python
# work_ua_parser.py
def random_delay(self):
    """Случайная задержка между запросами"""
    base_delay = self.config["delay_between_pages"]
    variation = random.uniform(0.5, 1.5)
    time.sleep(base_delay * variation)
```

2. Ротация User-Agent
```python
# Список реальных User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    # ... другие
]
```

3. Имитация человеческого поведения
```python
def simulate_human_behavior(self):
    """Имитация действий человека"""
    # Случайный скролл
    scroll_amount = random.randint(100, 500)
    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
    
    # Случайные паузы между действиями
    time.sleep(random.uniform(0.5, 2.0))
```

### 3.2 Обход CAPTCHA

#### Стратегии:
1. Автоматическое определение CAPTCHA
```python
def check_captcha(self):
    """Проверка наличия CAPTCHA"""
    captcha_patterns = [
        "captcha",
        "security check",
        "перевірка безпеки"
    ]
    page_source = self.driver.page_source.lower()
    return any(pattern in page_source for pattern in captcha_patterns)
```

2. Действия при обнаружении CAPTCHA
```python
def handle_captcha(self):
    """Обработка CAPTCHA"""
    if self.check_captcha():
        # 1. Сохраняем состояние
        self.save_checkpoint()
        
        # 2. Ждем некоторое время
        long_delay = random.uniform(300, 600)  # 5-10 минут
        time.sleep(long_delay)
        
        # 3. Пробуем с нового IP (если настроен прокси)
        self.rotate_proxy()
        
        # 4. Восстанавливаем сессию
        self.restore_checkpoint()
```

### 3.3 Обход динамической защиты

1. Адаптивные селекторы
```python
def adapt_selectors(self):
    """Адаптация селекторов при изменении структуры страницы"""
    selectors = {
        'name': [
            'h1.add-top-sm',
            'div.card-header h1',
            '//h1[contains(@class, "title")]'
        ],
        'salary': [
            'span.money',
            '//span[contains(@class, "salary")]'
        ]
    }
    
    for key, selector_list in selectors.items():
        for selector in selector_list:
            try:
                element = self.find_element(selector)
                if element:
                    self.current_selectors[key] = selector
                    break
            except:
                continue
```

2. Обработка динамического контента
```python
def wait_for_content(self):
    """Ожидание загрузки динамического контента"""
    WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "card-content"))
    )
```

### 3.4 Защита от дублирования

1. Проверка уникальности
```python
def is_duplicate(self, url):
    """Проверка на дубликат"""
    # Проверка URL
    if url in self.processed_urls:
        return True
    
    # Проверка контента
    content_hash = self.get_content_hash()
    if content_hash in self.content_hashes:
        return True
    
    return False
```

2. Хранение уникальных записей
```python
def save_resume(self, data):
    """Сохранение с проверкой уникальности"""
    if not self.is_duplicate(data['url']):
        self.resume_data.append(data)
        self.processed_urls.add(data['url'])
        self.content_hashes.add(self.get_content_hash())
```

## 4. Обработка ошибок

### 4.1 Автоматическое восстановление

1. Сохранение состояния
```python
def save_checkpoint(self):
    """Сохранение контрольной точки"""
    checkpoint = {
        'current_page': self.current_page,
        'processed_urls': list(self.processed_urls),
        'timestamp': time.time()
    }
    with open('checkpoint.json', 'w') as f:
        json.dump(checkpoint, f)
```

2. Восстановление после сбоя
```python
def restore_session(self):
    """Восстановление сессии"""
    if os.path.exists('checkpoint.json'):
        with open('checkpoint.json', 'r') as f:
            checkpoint = json.load(f)
        
        self.current_page = checkpoint['current_page']
        self.processed_urls = set(checkpoint['processed_urls'])
        
        return True
    return False
```

### 4.2 Обработка сетевых ошибок
```python
def handle_network_error(self):
    """Обработка сетевых ошибок"""
    max_retries = 3
    retry_delay = 60  # секунды
    
    for attempt in range(max_retries):
        try:
            self.driver.refresh()
            return True
        except:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                self.save_checkpoint()
                return False
```

## 5. Мониторинг и поддержка

### 5.1 Логирование
```python
def setup_logging(self):
    """Настройка логирования"""
    logging.basicConfig(
        filename='parser.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
```

### 5.2 Статистика парсинга
```python
def show_stats(self):
    """Показ статистики"""
    stats = {
        'total_processed': len(self.processed_urls),
        'unique_resumes': len(self.resume_data),
        'failed_attempts': len(self.failed_urls),
        'success_rate': len(self.resume_data) / len(self.processed_urls) * 100
    }
    return stats
```

## 6. Рекомендации по использованию

### 6.1 Оптимальные практики
1. Начинайте с малых объемов
2. Регулярно проверяйте качество данных
3. Используйте чекпоинты
4. Следите за логами
5. Регулярно делайте бэкапы

### 6.2 Избегайте
1. Слишком частых запросов
2. Параллельного запуска множества инстансов
3. Игнорирования ошибок
4. Парсинга без задержек

### 6.3 Настройка под свои нужды
1. Измените конфигурацию под свои требования
2. Настройте селекторы при изменении структуры сайта
3. Адаптируйте задержки под свой IP/прокси
4. Настройте формат выходных данных

## 7. Решение проблем

### 7.1 Частые проблемы и решения
1. Блокировка IP
   - Увеличьте задержки
   - Используйте прокси
   - Добавьте случайность в поведение

2. Пропуск данных
   - Проверьте селекторы
   - Увеличьте таймауты
   - Добавьте доп. проверки

3. Ошибки сети
   - Настройте повторные попытки
   - Используйте чекпоинты
   - Проверьте стабильность соединения

### 7.2 Поддержка работоспособности
1. Регулярно обновляйте User-Agent
2. Проверяйте актуальность селекторов
3. Мониторьте качество данных
4. Обновляйте прокси при необходимости
