"""
Work.ua Resume Parser
Парсер резюме с сайта work.ua
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import csv
import logging
import datetime
import openai
from config import BROWSER_CONFIG, PARSING_CONFIG


class WorkUaParser:
    def __init__(self):
        """Инициализация парсера"""
        self.driver = None
        self.base_url = "https://www.work.ua/resumes-%D0%B1%D1%83%D1%85%D0%B3%D0%B0%D0%BB%D1%82%D0%B5%D1%80/"
        self.setup_logging()
        self.max_retries = 3
        self.retry_delay = 2
        
    def setup_logging(self):
        """Настройка системы логирования"""
        log_filename = f"work_ua_parser_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Work.ua Parser инициализирован")
        
    def retry_operation(self, operation, operation_name, max_retries=None):
        """Универсальная функция для повторения операций при ошибках"""
        if max_retries is None:
            max_retries = self.max_retries
            
        for attempt in range(max_retries + 1):
            try:
                result = operation()
                if attempt > 0:
                    self.logger.info(f"✅ {operation_name} успешно выполнена с попытки {attempt + 1}")
                return result
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"⚠️ {operation_name} неудачна (попытка {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"❌ {operation_name} провалена после {max_retries + 1} попыток: {e}")
                    raise e
        
    def setup_driver(self):
        """Настройка и запуск Chrome драйвера"""
        def _setup():
            self.logger.info("Настройка Chrome драйвера...")
            
            # Настройки Chrome
            chrome_options = Options()
            
            # Устанавливаем размер окна
            chrome_options.add_argument(f"--window-size={BROWSER_CONFIG['window_size'][0]},{BROWSER_CONFIG['window_size'][1]}")
            
            # Если нужен headless режим
            if BROWSER_CONFIG['headless']:
                chrome_options.add_argument("--headless")
                
            # Дополнительные настройки для стабильности
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            
            try:
                # 🔧 BULLETPROOF инициализация драйвера с таймаутом
                self.logger.info("🔄 Попытка инициализации ChromeDriverManager...")
                
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("ChromeDriverManager завис!")
                
                # Устанавливаем таймаут на 15 секунд
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(15)
                
                try:
                    service = Service(ChromeDriverManager().install())
                    signal.alarm(0)  # Отключаем таймаут
                    self.logger.info("✅ ChromeDriverManager успешно завершен")
                except (TimeoutError, KeyboardInterrupt):
                    signal.alarm(0)  # Отключаем таймаут
                    self.logger.warning("⚠️ ChromeDriverManager завис, используем локальный драйвер...")
                    # Fallback на системный chromedriver
                    service = Service()  # Использует системный PATH
                
                # Инициализируем драйвер
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Устанавливаем таймауты
                self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
                self.driver.implicitly_wait(BROWSER_CONFIG['implicit_wait'])
                
                self.logger.info("✅ Chrome драйвер успешно инициализирован")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка при инициализации драйвера: {e}")
                raise e
        
        try:
            return self.retry_operation(_setup, "Инициализация драйвера")
        except Exception as e:
            self.logger.critical(f"❌ Критическая ошибка инициализации драйвера: {e}")
            return False
        
    def open_page(self):
        """Открытие страницы с резюме"""
        if not self.driver:
            self.logger.error("❌ Драйвер не инициализирован")
            return False
            
        def _open():
            self.logger.info(f"Открываем страницу: {self.base_url}")
            
            try:
                self.driver.get(self.base_url)
                
                # Ждем загрузки страницы с WebDriverWait
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Проверяем, что страница загружена
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                self.logger.info(f"✅ Страница загружена:")
                self.logger.info(f"   URL: {current_url}")
                self.logger.info(f"   Заголовок: {page_title}")
                
                # Проверяем, что мы на правильной странице
                if "work.ua" in current_url and ("резюме" in page_title.lower() or "resume" in current_url):
                    self.logger.info("✅ Мы на правильной странице work.ua")
                    return True
                else:
                    self.logger.warning("⚠️ Возможно, мы не на той странице")
                    return False
                    
            except TimeoutException:
                self.logger.error("❌ Таймаут при загрузке страницы")
                raise
            except Exception as e:
                self.logger.error(f"❌ Ошибка при открытии страницы: {e}")
                raise
        
        try:
            return self.retry_operation(_open, "Открытие страницы")
        except Exception as e:
            self.logger.critical(f"❌ Критическая ошибка открытия страницы: {e}")
            return False
        
    def find_resume_cards(self):
        """Поиск карточек резюме на странице"""
        if not self.driver:
            print("❌ Драйвер не инициализирован")
            return []
            
        try:
            print("Ищем карточки резюме на странице...")
            
            # Используем селектор из конфига
            from config import SELECTORS
            card_selector = SELECTORS['resume_cards']
            print(f"Используем селектор: {card_selector}")
            
            # Ждем появления карточек
            time.sleep(3)
            
            # Ищем все карточки
            cards = self.driver.find_elements(By.CSS_SELECTOR, card_selector)
            print(f"✅ Найдено карточек резюме: {len(cards)}")
            
            # Дополнительная диагностика
            if len(cards) < 5:  # Если карточек мало, проверим альтернативные селекторы
                print("🔍 Проверяем альтернативные селекторы...")
                
                # Пробуем более простой селектор
                alt_cards1 = self.driver.find_elements(By.CSS_SELECTOR, ".card.resume-link")
                print(f"   Альтернативный селектор '.card.resume-link': {len(alt_cards1)} карточек")
                
                alt_cards2 = self.driver.find_elements(By.CSS_SELECTOR, "div.card")
                print(f"   Селектор 'div.card': {len(alt_cards2)} элементов")
                
                # Проверим контейнер со списком резюме
                container = self.driver.find_elements(By.ID, "pjax-resume-list")
                if container:
                    print(f"   Контейнер #pjax-resume-list найден")
                    # Ищем все div внутри контейнера
                    divs_in_container = container[0].find_elements(By.TAG_NAME, "div")
                    print(f"   Всего div внутри контейнера: {len(divs_in_container)}")
                else:
                    print("   ⚠️ Контейнер #pjax-resume-list НЕ НАЙДЕН")
                
                # АВТОМАТИЧЕСКАЯ АДАПТАЦИЯ СЕЛЕКТОРОВ с LLM
                if len(cards) <= 2 and hasattr(self, '_initial_cards_count') and self._initial_cards_count > 5:
                    print("🤖 АКТИВИРУЕМ АВТОАДАПТАЦИЮ СЕЛЕКТОРОВ...")
                    new_cards = self._auto_adapt_selectors_with_llm()
                    if new_cards and len(new_cards) > len(cards):
                        print(f"✅ LLM нашел лучшие селекторы! Карточек: {len(new_cards)}")
                        return new_cards
            
            # Запоминаем количество карточек при первом запуске
            if not hasattr(self, '_initial_cards_count') and len(cards) > 5:
                self._initial_cards_count = len(cards)
                print(f"📝 Запомнили начальное количество карточек: {len(cards)}")
            
            if len(cards) > 0:
                print("📋 Первые несколько карточек:")
                for i, card in enumerate(cards[:3]):  # Показываем первые 3
                    try:
                        # Пытаемся получить заголовок карточки
                        title_element = card.find_element(By.CSS_SELECTOR, "h2 a")
                        title = title_element.text.strip()
                        link = title_element.get_attribute("href")
                        print(f"   {i+1}. {title}")
                        print(f"      Ссылка: {link}")
                    except Exception as e:
                        print(f"   {i+1}. [Не удалось получить заголовок: {e}]")
                        
                return cards
            else:
                print("⚠️ Карточки резюме не найдены")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка при поиске карточек: {e}")
            return []
        
    def _fast_find_element(self, parent, selector, timeout=0.5):
        """Быстрый поиск элемента с коротким таймаутом"""
        old_timeout = self.driver.timeouts.implicit_wait
        try:
            self.driver.implicitly_wait(timeout)
            return parent.find_element(By.CSS_SELECTOR, selector)
        except:
            return None
        finally:
            self.driver.implicitly_wait(old_timeout)
    
    def _fast_find_elements(self, parent, selector, timeout=0.5):
        """Быстрый поиск элементов с коротким таймаутом"""
        old_timeout = self.driver.timeouts.implicit_wait
        try:
            self.driver.implicitly_wait(timeout)
            return parent.find_elements(By.CSS_SELECTOR, selector)
        except:
            return []
        finally:
            self.driver.implicitly_wait(old_timeout)

    def parse_card_info(self, card):
        """⚡ БЫСТРОЕ извлечение информации из карточки"""
        if not card:
            return None
            
        try:
            card_info = {}
            
            # Заголовок резюме и ссылка - БЕЗ долгих ожиданий
            title_element = self._fast_find_element(card, "h2 a")
            if title_element:
                card_info['title'] = title_element.text.strip()
                card_info['link'] = title_element.get_attribute("href")
                card_info['url'] = title_element.get_attribute("href")  # Для совместимости с ULTIMATE парсером
            else:
                card_info['title'] = "Не указано"
                card_info['link'] = ""
                card_info['url'] = ""
            
            # Зарплата - быстро
            salary_element = self._fast_find_element(card, ".h5.strong-600")
            card_info['salary'] = salary_element.text.strip() if salary_element else "Не указана"
            
            # Имя, возраст, город - быстро
            personal_paragraphs = self._fast_find_elements(card, "p.mt-xs.mb-0")
            personal_info_found = False
            
            for p in personal_paragraphs:
                text = p.text.strip()
                # Проверяем, что это строка с именем (содержит strong-600 и не содержит "грн")
                if text and "грн" not in text and len(text.split(",")) >= 2:
                    card_info['personal_info'] = text
                    parts = text.split(', ')
                    card_info['name'] = parts[0] if len(parts) >= 1 else "Не указано"
                    card_info['age_location'] = ', '.join(parts[1:]) if len(parts) >= 2 else "Не указано"
                    personal_info_found = True
                    break
            
            if not personal_info_found:
                card_info['personal_info'] = "Не указано"
                card_info['name'] = "Не указано"
                card_info['age_location'] = "Не указано"
            
            # Опыт работы - быстро
            experience_elements = self._fast_find_elements(card, "ul.mt-lg.mb-0 li")
            experience_list = []
            for exp in experience_elements[:3]:  # Берем первые 3 записи опыта
                exp_text = exp.text.strip()
                # Фильтруем служебные элементы
                if exp_text and exp_text not in ["PRO", "Файл", ""]:
                    experience_list.append(exp_text)
            card_info['experience'] = experience_list
            
            # Образование/тип занятости - быстро
            education_elements = self._fast_find_elements(card, "p.mb-0.mt-xs.text-default-7")
            card_info['education_employment'] = education_elements[0].text.strip() if education_elements else "Не указано"
            
            return card_info
            
        except Exception as e:
            print(f"❌ Ошибка при извлечении информации из карточки: {e}")
            return None

    def _auto_adapt_selectors_with_llm(self):
        """🤖 АВТОМАТИЧЕСКАЯ АДАПТАЦИЯ СЕЛЕКТОРОВ с помощью LLM"""
        print("🔍 Анализируем DOM структуру с помощью LLM...")
        
        try:
            # Получаем текущий HTML страницы (урезанный для LLM)
            page_source = self.driver.page_source
            
            # Берем только нужную часть HTML для экономии токенов
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Ищем потенциальные контейнеры с резюме
            potential_containers = []
            
            # 1. Ищем элементы с "resume" в id/class
            for elem in soup.find_all(attrs={'class': True}):
                classes = ' '.join(elem.get('class', []))
                if 'resume' in classes.lower() or 'card' in classes.lower():
                    potential_containers.append({
                        'tag': elem.name,
                        'classes': classes,
                        'id': elem.get('id', ''),
                        'text_sample': elem.get_text()[:100] if elem.get_text() else ''
                    })
            
            # 2. Берем только первые 10 самых релевантных
            potential_containers = potential_containers[:10]
            
            # 3. Формируем HTML снимок для LLM
            html_analysis = "АНАЛИЗ DOM СТРУКТУРЫ:\n"
            html_analysis += f"Всего найдено потенциальных элементов: {len(potential_containers)}\n\n"
            
            for i, container in enumerate(potential_containers[:5]):
                html_analysis += f"{i+1}. Тег: <{container['tag']}>\n"
                html_analysis += f"   Классы: {container['classes']}\n"
                html_analysis += f"   ID: {container['id']}\n"
                html_analysis += f"   Текст: {container['text_sample'][:50]}...\n\n"
            
            # 4. Запрос к LLM для анализа селекторов
            analysis_prompt = f"""Анализируй HTML структуру сайта work.ua с резюме бухгалтеров.

ЗАДАЧА: Найти правильные CSS селекторы для карточек резюме.

ТЕКУЩАЯ ПРОБЛЕМА: 
- Старый селектор ".card.resume-link" находит только 1 карточку вместо 14
- Контейнер "#pjax-resume-list" пропал после PJAX навигации

{html_analysis}

ВЕРНИ JSON с новыми селекторами:
{{
    "container_selector": "новый селектор контейнера",
    "card_selector": "новый селектор карточек",
    "confidence": "высокая/средняя/низкая",
    "reasoning": "объяснение выбора селекторов"
}}

Селекторы должны быть УНИВЕРСАЛЬНЫМИ и работать после PJAX загрузки."""

            # 5. Вызов LLM
            response = self.call_llm_for_analysis(analysis_prompt)
            
            if response and 'card_selector' in response:
                new_selector = response['card_selector']
                print(f"🤖 LLM предложил селектор: {new_selector}")
                print(f"📊 Уверенность: {response.get('confidence', 'неизвестна')}")
                print(f"💭 Объяснение: {response.get('reasoning', 'не указано')}")
                
                # 6. Тестируем новый селектор
                test_cards = self.driver.find_elements(By.CSS_SELECTOR, new_selector)
                print(f"🧪 Тест нового селектора: найдено {len(test_cards)} карточек")
                
                if len(test_cards) > 2:
                    # Обновляем селектор в конфиге для будущих запусков
                    self._update_selector_config(new_selector)
                    return test_cards
                    
            print("❌ LLM не смог найти лучшие селекторы")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка автоадаптации: {e}")
            return None
    
    def call_llm_for_analysis(self, prompt):
        """Вызов LLM для анализа DOM структуры"""
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты эксперт по веб-скрейпингу и CSS селекторам. Анализируй HTML и возвращай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Парсим JSON ответ
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Ошибка LLM анализа: {e}")
            return None
    
    def _update_selector_config(self, new_selector):
        """Обновление селектора в конфигурации"""
        try:
            # Читаем конфиг
            with open('config.py', 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Заменяем селектор
            import re
            pattern = r"'resume_cards':\s*'[^']+'"
            replacement = f"'resume_cards': '{new_selector}'"
            
            updated_config = re.sub(pattern, replacement, config_content)
            
            # Сохраняем
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(updated_config)
                
            print(f"💾 Селектор обновлен в config.py: {new_selector}")
            
            # Также создаем backup файл
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"selector_backup_{timestamp}.txt"
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.write(f"Дата: {datetime.datetime.now()}\n")
                f.write(f"Новый селектор: {new_selector}\n")
                f.write(f"Причина: Автоадаптация LLM\n")
            
            print(f"💾 Создан backup: {backup_filename}")
            
        except Exception as e:
            print(f"❌ Ошибка обновления конфига: {e}")

    # ========================================
    # МЕТОДЫ ПАГИНАЦИИ С АВТОАДАПТАЦИЕЙ
    # ========================================
    
    def has_next_page(self):
        """Проверяет наличие следующей страницы с автоадаптацией селекторов"""
        try:
            # Используем основной селектор
            from config import SELECTORS, PARSING_CONFIG
            main_selector = SELECTORS['pagination_next']
            
            print(f"🔍 Проверяем наличие следующей страницы...")
            print(f"   Селектор: {main_selector}")
            
            # Проверяем основной селектор
            next_elements = self.driver.find_elements(By.CSS_SELECTOR, main_selector)
            
            if next_elements:
                # Проверяем что элемент активен (не disabled)
                next_element = next_elements[0]
                if not next_element.get_attribute("class") or "disabled" not in next_element.get_attribute("class"):
                    print(f"✅ Найдена следующая страница: основной селектор")
                    return True
            
            # Если основной селектор не работает, пробуем альтернативные
            print(f"⚠️ Основной селектор не найден, пробуем альтернативные...")
            
            alt_selectors = SELECTORS.get('pagination_next_alt', [])
            for i, alt_selector in enumerate(alt_selectors):
                try:
                    alt_elements = self.driver.find_elements(By.CSS_SELECTOR, alt_selector)
                    if alt_elements:
                        print(f"✅ Найдена следующая страница: альтернативный селектор #{i+1}")
                        # Обновляем основной селектор для будущих использований
                        self._update_pagination_selector(alt_selector)
                        return True
                except Exception as e:
                    continue
            
            # Если ничего не найдено и включена автоадаптация, используем LLM
            if PARSING_CONFIG.get('pagination_auto_adapt', True):
                print(f"🤖 Активируем LLM автоадаптацию для пагинации...")
                return self._auto_adapt_pagination_selectors()
            
            print(f"❌ Следующая страница не найдена")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка проверки следующей страницы: {e}")
            return False
    
    def go_to_next_page(self):
        """Переходит на следующую страницу с автоадаптацией"""
        try:
            from config import SELECTORS, PARSING_CONFIG
            
            print(f"📄 Переходим на следующую страницу...")
            
            # Сохраняем текущий URL для проверки
            current_url = self.driver.current_url
            
            # Ищем кнопку следующей страницы
            main_selector = SELECTORS['pagination_next']
            next_elements = self.driver.find_elements(By.CSS_SELECTOR, main_selector)
            
            if not next_elements:
                # Пробуем альтернативные селекторы
                alt_selectors = SELECTORS.get('pagination_next_alt', [])
                for alt_selector in alt_selectors:
                    try:
                        next_elements = self.driver.find_elements(By.CSS_SELECTOR, alt_selector)
                        if next_elements:
                            main_selector = alt_selector
                            break
                    except Exception:
                        continue
            
            if not next_elements:
                print(f"❌ Кнопка следующей страницы не найдена")
                return False
            
            next_button = next_elements[0]
            
            # Прокручиваем к элементу и делаем его видимым
            print(f"📜 Прокручиваем к кнопке пагинации...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
            time.sleep(2)
            
            # Проверяем кликабельность элемента
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, main_selector))
                )
                print(f"✅ Элемент готов к клику")
            except TimeoutException:
                print(f"⚠️ Элемент не кликабельный, пробуем JavaScript click...")
            
            # Кликаем на кнопку (пробуем несколько способов)
            print(f"🖱️ Кликаем на кнопку следующей страницы...")
            
            # Способ 1: Обычный клик
            try:
                next_button.click()
                print(f"✅ Обычный клик успешен")
            except Exception as e1:
                print(f"⚠️ Обычный клик не сработал: {e1}")
                
                # Способ 2: JavaScript клик
                try:
                    print(f"🔧 Пробуем JavaScript клик...")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    print(f"✅ JavaScript клик успешен")
                except Exception as e2:
                    print(f"⚠️ JavaScript клик не сработал: {e2}")
                    
                    # Способ 3: Клик по ссылке внутри элемента
                    try:
                        print(f"🔧 Ищем ссылку внутри элемента...")
                        link_inside = next_button.find_element(By.TAG_NAME, "a")
                        if link_inside:
                            print(f"🔗 Найдена ссылка, кликаем по ней...")
                            self.driver.execute_script("arguments[0].click();", link_inside)
                            print(f"✅ Клик по ссылке успешен")
                        else:
                            raise Exception("Ссылка не найдена")
                    except Exception as e3:
                        print(f"❌ Все способы клика не сработали")
                        # Активируем LLM автоадаптацию
                        if PARSING_CONFIG.get('pagination_auto_adapt', True):
                            print(f"🤖 Активируем LLM автоадаптацию селекторов...")
                            if self._auto_adapt_pagination_selectors():
                                # Пробуем еще раз с новым селектором
                                return self.go_to_next_page()
                        raise Exception(f"Не удалось кликнуть: {e1}, {e2}, {e3}")
            
            # Ждем загрузки страницы
            timeout = PARSING_CONFIG.get('pagination_wait_timeout', 15)
            print(f"⏳ Ожидаем загрузки следующей страницы ({timeout}s)...")
            
            # Ждем изменения URL или содержимого
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.current_url != current_url or 
                self._page_content_changed(current_url)
            )
            
            # Дополнительное ожидание PJAX загрузки
            time.sleep(PARSING_CONFIG.get('delay_between_pages', 2))
            
            # Ждем загрузки PJAX контейнера
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "pjax-resume-list"))
                )
                print(f"✅ PJAX контейнер загружен")
                
                # Ждем появления карточек резюме
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['resume_cards']))
                )
                print(f"✅ Карточки резюме загружены")
                
            except TimeoutException:
                print(f"⚠️ PJAX контейнер не загрузился за отведенное время")
                # Принудительное обновление
                self.driver.refresh()
                time.sleep(3)
            
            new_url = self.driver.current_url
            print(f"✅ Успешно перешли на следующую страницу")
            print(f"   Новый URL: {new_url}")
            
            return True
            
        except TimeoutException:
            print(f"❌ Таймаут при переходе на следующую страницу")
            return False
        except Exception as e:
            print(f"❌ Ошибка при переходе на следующую страницу: {e}")
            return False
    
    def _page_content_changed(self, original_url):
        """Проверяет изменилось ли содержимое страницы"""
        try:
            from config import SELECTORS
            
            # Если URL изменился, страница точно изменилась
            if self.driver.current_url != original_url:
                return True
            
            # Проверяем наличие карточек (если страница обновилась через PJAX)
            cards = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['resume_cards'])
            return len(cards) > 0
            
        except Exception:
            return False
    
    def _auto_adapt_pagination_selectors(self):
        """Автоматическая адаптация селекторов пагинации через LLM"""
        print("🤖 LLM анализ селекторов пагинации...")
        
        try:
            # Получаем HTML страницы
            page_source = self.driver.page_source
            
            # Анализируем пагинацию с помощью BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Ищем потенциальные элементы пагинации
            pagination_elements = []
            
            # Ищем nav, pagination, page-link и т.д.
            for elem in soup.find_all(['nav', 'ul', 'div'], attrs={'class': True}):
                classes = ' '.join(elem.get('class', []))
                if any(keyword in classes.lower() for keyword in ['pagination', 'page', 'nav']):
                    pagination_elements.append({
                        'tag': elem.name,
                        'classes': classes,
                        'id': elem.get('id', ''),
                        'text_sample': elem.get_text()[:100] if elem.get_text() else ''
                    })
            
            if not pagination_elements:
                print("❌ Не найдены элементы пагинации для анализа")
                return False
            
            # Формируем HTML анализ для LLM
            html_analysis = "АНАЛИЗ ПАГИНАЦИИ:\n"
            html_analysis += f"Найдено элементов: {len(pagination_elements)}\n\n"
            
            for i, elem in enumerate(pagination_elements[:5]):
                html_analysis += f"{i+1}. Тег: <{elem['tag']}>\n"
                html_analysis += f"   Классы: {elem['classes']}\n"
                html_analysis += f"   ID: {elem['id']}\n"
                html_analysis += f"   Текст: {elem['text_sample'][:50]}...\n\n"
            
            # Запрос к LLM
            analysis_prompt = f"""Анализируй HTML пагинацию на сайте work.ua.

ЗАДАЧА: Найти CSS селектор для кнопки "Следующая страница".

ПРОБЛЕМА: Селектор "#pjax-resume-list > nav > ul.pagination.pagination-small.visible-xs-block > li.circle-style.add-left-sm" не работает.

{html_analysis}

ВЕРНИ JSON с новым селектором:
{{
    "next_page_selector": "селектор для кнопки следующей страницы",
    "confidence": "высокая/средняя/низкая",
    "reasoning": "объяснение выбора"
}}

Селектор должен указывать на кликабельную кнопку/ссылку для перехода на следующую страницу."""

            # Вызов LLM
            response = self.call_llm_for_analysis(analysis_prompt)
            
            if response and 'next_page_selector' in response:
                new_selector = response['next_page_selector']
                print(f"🤖 LLM предложил селектор пагинации: {new_selector}")
                
                # Тестируем новый селектор
                test_elements = self.driver.find_elements(By.CSS_SELECTOR, new_selector)
                if test_elements:
                    print(f"✅ Новый селектор пагинации работает!")
                    self._update_pagination_selector(new_selector)
                    return True
                else:
                    print(f"❌ Новый селектор пагинации не работает")
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка LLM анализа пагинации: {e}")
            return False
    
    def _update_pagination_selector(self, new_selector):
        """Обновляет селектор пагинации в конфигурации"""
        try:
            # Читаем конфиг
            with open('config.py', 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Заменяем селектор пагинации
            import re
            pattern = r'"pagination_next":\s*"[^"]+"'
            replacement = f'"pagination_next": "{new_selector}"'
            
            updated_config = re.sub(pattern, replacement, config_content)
            
            # Сохраняем
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(updated_config)
                
            print(f"💾 Селектор пагинации обновлен: {new_selector}")
            
        except Exception as e:
            print(f"❌ Ошибка обновления селектора пагинации: {e}")
        
    def click_card(self, card):
        """Переход внутрь карточки"""
        if not card or not self.driver:
            self.logger.error("❌ Карточка или драйвер не доступны")
            return False
            
        def _click():
            try:
                # Проверяем состояние драйвера
                self.driver.current_url  # Проверка связи с браузером
                
                # Находим ссылку внутри карточки
                link_element = card.find_element(By.CSS_SELECTOR, "h2 a")
                link_url = link_element.get_attribute("href")
                title = link_element.text.strip()
                
                self.logger.info(f"🔗 Переходим в резюме: '{title}'")
                self.logger.info(f"   URL: {link_url}")
                
                # Кликаем по ссылке
                link_element.click()
                
                # Ждем загрузки новой страницы с timeout
                wait = WebDriverWait(self.driver, 15)
                wait.until(lambda driver: "/resumes/" in driver.current_url)
                
                # Проверяем, что мы перешли на страницу резюме
                current_url = self.driver.current_url
                if "/resumes/" in current_url and current_url != self.base_url:
                    self.logger.info("✅ Успешно перешли на страницу резюме")
                    self.logger.info(f"   Текущий URL: {current_url}")
                    return True
                else:
                    self.logger.warning("⚠️ Возможно, переход не удался")
                    self.logger.warning(f"   Текущий URL: {current_url}")
                    return False
                    
            except TimeoutException:
                self.logger.error("❌ Таймаут при переходе в карточку")
                raise
            except StaleElementReferenceException:
                self.logger.error("❌ Stale element при клике по карточке")
                raise
            except Exception as e:
                self.logger.error(f"❌ Ошибка при клике по карточке: {e}")
                raise
        
        try:
            return self.retry_operation(_click, "Переход в карточку", max_retries=2)
        except Exception as e:
            self.logger.error(f"❌ Не удалось перейти в карточку после попыток: {e}")
            return False

    def go_back(self):
        """Возврат на предыдущую страницу"""
        if not self.driver:
            self.logger.error("❌ Драйвер не доступен")
            return False
            
        def _go_back():
            try:
                self.logger.info("⬅️ Возвращаемся назад...")
                
                # Проверяем состояние драйвера перед операцией
                current_url_before = self.driver.current_url
                self.logger.info(f"URL до возврата: {current_url_before}")
                
                # Возвращаемся назад с коротким timeout
                self.driver.set_page_load_timeout(10)  # Уменьшаем timeout для возврата
                self.driver.back()
                
                # Ждем загрузки с WebDriverWait
                wait = WebDriverWait(self.driver, 10)
                wait.until(lambda driver: driver.current_url != current_url_before)
                
                # Дополнительное ожидание стабилизации страницы
                time.sleep(2)
                
                # Проверяем, что мы вернулись
                current_url_after = self.driver.current_url
                self.logger.info(f"URL после возврата: {current_url_after}")
                
                if current_url_after != current_url_before:
                    self.logger.info("✅ Успешно вернулись назад")
                    
                    # КРИТИЧЕСКИ ВАЖНО: Ждем загрузки PJAX контейнера и карточек
                    self.logger.info("⏳ Ожидаем загрузки PJAX контейнера...")
                    pjax_wait = WebDriverWait(self.driver, 15)
                    
                    try:
                        # Ждем появления PJAX контейнера
                        pjax_wait.until(EC.presence_of_element_located((By.ID, "pjax-resume-list")))
                        self.logger.info("✅ PJAX контейнер загружен")
                        
                        # Дополнительно ждем появления карточек внутри контейнера
                        pjax_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#pjax-resume-list .card.resume-link")))
                        self.logger.info("✅ Карточки резюме загружены")
                        
                        # Дополнительная пауза для полной стабилизации
                        time.sleep(1)
                        
                    except TimeoutException:
                        self.logger.warning("⚠️ PJAX контейнер или карточки не загрузились за 15 секунд")
                        # Пробуем принудительно вернуться на основную страницу
                        self.logger.info("🔄 Принудительный переход на основную страницу...")
                        try:
                            self.driver.get(self.base_url)
                            time.sleep(3)
                            # Проверяем что карточки появились
                            wait_cards = WebDriverWait(self.driver, 10)
                            wait_cards.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card.resume-link")))
                            self.logger.info("✅ Страница восстановлена")
                        except Exception as e:
                            self.logger.error(f"❌ Не удалось восстановить страницу: {e}")
                    
                    # Восстанавливаем обычный timeout
                    self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
                    return True
                else:
                    self.logger.warning("⚠️ URL не изменился, возможно возврат не удался")
                    return False
                    
            except TimeoutException:
                self.logger.error("❌ Таймаут при возврате назад")
                # Восстанавливаем timeout даже при ошибке
                try:
                    self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
                except:
                    pass
                raise
            except Exception as e:
                self.logger.error(f"❌ Ошибка при возврате назад: {e}")
                # Восстанавливаем timeout даже при ошибке  
                try:
                    self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
                except:
                    pass
                raise
        
        try:
            return self.retry_operation(_go_back, "Возврат назад", max_retries=2)
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка возврата: {e}")
            # Проверяем, жив ли еще драйвер
            try:
                self.driver.current_url
                self.logger.info("Драйвер еще работает")
            except:
                self.logger.critical("❌ Драйвер больше не отвечает, требуется перезапуск")
            return False
            
    def check_driver_alive(self):
        """Проверка состояния драйвера"""
        try:
            if self.driver:
                self.driver.current_url
                return True
            return False
        except Exception as e:
            self.logger.error(f"Драйвер не отвечает: {e}")
            return False

    def parse_resume_details(self):
        """Извлечение детальной информации со страницы резюме"""
        if not self.driver:
            print("❌ Драйвер не доступен")
            return None
            
        try:
            # Проверяем, что мы на странице резюме
            current_url = self.driver.current_url
            if "/resumes/" not in current_url:
                print("⚠️ Мы не на странице резюме")
                return None
            
            print("📋 Извлекаем детальную информацию с страницы резюме...")
            
            # ПРОСТО БЕРЕМ ВЕСЬ ТЕКСТ СТРАНИЦЫ - БЕЗ ЛИШНЕЙ ФИГНИ
            try:
                # Получаем весь текст страницы одним вызовом
                full_page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                resume_details = {
                    'full_text': full_page_text,
                    'resume_url': current_url,
                    'parsing_time': '< 1 секунды вместо 2 минут!'
                }
            except Exception as e:
                print(f"❌ Ошибка извлечения текста: {e}")
                resume_details = {
                    'full_text': 'Ошибка извлечения',
                    'resume_url': current_url
                }
            
            print("✅ Детальная информация извлечена")
            return resume_details
            
        except Exception as e:
            print(f"❌ Ошибка при извлечении детальной информации: {e}")
            return None

    def parse_resume_with_llm(self):
        """Извлечение информации со страницы резюме с помощью LLM"""
        if not self.driver:
            self.logger.error("❌ Драйвер не доступен")
            return None
            
        try:
            # Проверяем, что мы на странице резюме
            current_url = self.driver.current_url
            if "/resumes/" not in current_url:
                self.logger.warning("⚠️ Мы не на странице резюме")
                return None
            
            self.logger.info("🤖 Извлекаем HTML страницы для LLM обработки...")
            
            # Получаем весь HTML страницы
            page_html = self.driver.page_source
            
            # Очищаем HTML от лишнего (скрипты, стили)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Берем только текстовое содержимое основной области
            main_content = soup.get_text(separator=' ', strip=True)
            
            # Ограничиваем размер текста (ChatGPT имеет лимиты)
            if len(main_content) > 8000:
                main_content = main_content[:8000] + "..."
            
            self.logger.info(f"📄 Подготовлен текст длиной {len(main_content)} символов")
            
            # Формируем prompt для ChatGPT
            prompt = f"""
Извлеки ПОЛНУЮ детальную информацию из резюме в JSON формате:

{main_content}

Формат ответа:
{{
    "full_name": "полное имя",
    "position": "должность", 
    "salary": "зарплата",
    "age": "возраст",
    "location": "город",
    "birth_date": "дата рождения",
    "address": "полный адрес",
    "phone": "телефон (если есть)",
    "education": [
        "ПОЛНАЯ информация об образовании с годами, учебными заведениями, квалификациями"
    ],
    "experience": [
        "ДЕТАЛЬНАЯ информация о каждом месте работы с должностными обязанностями, компанией, периодом"
    ],
    "professional_skills": [
        "ПОДРОБНЫЕ профессиональные навыки, знание программ, технологий"
    ],
    "personal_skills": [
        "Личные качества, характеристики"
    ],
    "languages": [
        "Знание языков с уровнем"
    ],
    "additional_info": "ВСЯ дополнительная информация",
    "detailed_description": "Полное описание кандидата"
}}

КРИТИЧЕСКИ ВАЖНО: 
- Извлекай ВСЮ доступную информацию БЕЗ сокращений
- В education - ПОЛНЫЕ названия учебных заведений с годами и специальностями
- В experience - ДЕТАЛЬНЫЕ должностные обязанности для каждого места работы
- В professional_skills - ВСЕ упомянутые программы, технологии, навыки
- Сохраняй ВЕСЬ оригинальный текст важных разделов
- Если информация большая - включай её полностью
- Ответь ТОЛЬКО JSON
"""

            # Отправляем запрос в OpenAI
            self.logger.info("🚀 Отправляем запрос в OpenAI...")
            
            try:
                client = openai.OpenAI()
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты эксперт по анализу резюме. Извлекаешь ПОЛНУЮ структурированную информацию из текста резюме БЕЗ сокращений."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,  # Увеличиваем лимит токенов для детальной информации
                    temperature=0.1
                )
                
                # Парсим ответ
                llm_response = response.choices[0].message.content.strip()
                self.logger.info("✅ Получен ответ от OpenAI")
                
                # Очищаем ответ от markdown разметки
                if llm_response.startswith('```json'):
                    llm_response = llm_response[7:]  # Убираем ```json
                if llm_response.startswith('```'):
                    llm_response = llm_response[3:]   # Убираем ```
                if llm_response.endswith('```'):
                    llm_response = llm_response[:-3]  # Убираем ```
                llm_response = llm_response.strip()
                
                # Парсим JSON
                try:
                    resume_data = json.loads(llm_response)
                    resume_data['resume_url'] = current_url
                    resume_data['parsed_with'] = 'OpenAI GPT-3.5'
                    
                    self.logger.info("🎉 Информация успешно извлечена с помощью LLM")
                    return resume_data
                    
                except json.JSONDecodeError as e:
                    self.logger.warning("⚠️ Неполный JSON от OpenAI, пытаемся восстановить...")
                    self.logger.warning(f"Ошибка: {e}")
                    
                    # Пытаемся восстановить неполный JSON
                    try:
                        # Добавляем недостающие закрывающие скобки
                        fixed_json = self._fix_incomplete_json(llm_response)
                        if fixed_json:
                            resume_data = json.loads(fixed_json)
                            resume_data['resume_url'] = current_url
                            resume_data['parsed_with'] = 'OpenAI GPT-3.5 (fixed)'
                            
                            self.logger.info("🛠️ JSON восстановлен и обработан")
                            return resume_data
                    except:
                        pass
                    
                    self.logger.error("❌ Не удалось восстановить JSON от OpenAI")
                    self.logger.error(f"Неполный ответ: {llm_response[:500]}...")
                    return None
                    
            except Exception as e:
                self.logger.error(f"❌ Ошибка запроса к OpenAI: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка в parse_resume_with_llm: {e}")
            return None
    
    def _fix_incomplete_json(self, broken_json: str) -> str:
        """Пытается восстановить неполный JSON"""
        try:
            # Удаляем лишние символы в конце
            broken_json = broken_json.strip()
            
            # Считаем открытые/закрытые скобки
            open_braces = broken_json.count('{')
            close_braces = broken_json.count('}')
            open_brackets = broken_json.count('[')
            close_brackets = broken_json.count(']')
            
            # Если JSON обрывается на значении строки, завершаем её
            if broken_json.endswith('"') and not broken_json.endswith('",') and not broken_json.endswith('"]'):
                pass  # JSON уже корректно завершен
            elif not broken_json.endswith('"') and not broken_json.endswith(',') and not broken_json.endswith('}') and not broken_json.endswith(']'):
                # Если обрывается посередине значения, добавляем кавычку
                if '"' in broken_json.split('\n')[-1]:
                    broken_json += '"'
            
            # Добавляем недостающие закрывающие скобки
            for _ in range(open_brackets - close_brackets):
                broken_json += ']'
            
            for _ in range(open_braces - close_braces):
                broken_json += '}'
            
            # Проверяем что получился валидный JSON
            json.loads(broken_json)
            return broken_json
            
        except Exception as e:
            self.logger.debug(f"Не удалось восстановить JSON: {e}")
            return None

    def process_all_cards(self):
        """Обработка всех карточек резюме на текущей странице"""
        if not self.driver:
            print("❌ Драйвер не доступен")
            return []
            
        try:
            print("🔄 Начинаем массовую обработку карточек...")
            
            # Находим все карточки
            cards = self.find_resume_cards()
            if not cards:
                print("❌ Карточки не найдены")
                return []
            
            total_cards = len(cards)
            print(f"📊 Найдено {total_cards} карточек для обработки")
            
            processed_resumes = []
            successful_count = 0
            failed_count = 0
            
            # Обрабатываем каждую карточку по индексу (избегаем stale reference)
            for i in range(total_cards):
                try:
                    print(f"\n{'='*60}")
                    print(f"🎯 ОБРАБАТЫВАЕМ КАРТОЧКУ {i+1}/{total_cards}")
                    print(f"{'='*60}")
                    
                    # ЗАНОВО находим карточки для избежания stale reference
                    current_cards = self.find_resume_cards()
                    if not current_cards or i >= len(current_cards):
                        print(f"⚠️ Карточка {i+1} больше не доступна")
                        failed_count += 1
                        continue
                    
                    current_card = current_cards[i]
                    
                    # Извлекаем краткую информацию с карточки
                    card_info = self.parse_card_info(current_card)
                    if not card_info:
                        print(f"⚠️ Не удалось извлечь информацию из карточки {i+1}")
                        failed_count += 1
                        continue
                    
                    print(f"📋 Карточка: {card_info['title']}")
                    print(f"👤 Имя: {card_info['name']}")
                    print(f"💰 Зарплата: {card_info['salary']}")
                    
                    # Переходим в резюме
                    if self.click_card(current_card):
                        print(f"✅ Перешли в резюме {i+1}")
                        
                        # Извлекаем детальную информацию с помощью LLM
                        details = self.parse_resume_with_llm()
                        
                        if details:
                            # Объединяем краткую и детальную информацию
                            full_resume_data = {
                                'card_number': i+1,
                                'card_info': card_info,
                                'detailed_info': details,
                                'processing_status': 'success'
                            }
                            
                            processed_resumes.append(full_resume_data)
                            successful_count += 1
                            
                            print(f"✅ Резюме {i+1} успешно обработано")
                            print(f"   Полное имя: {details['full_name']}")
                            # Безопасный доступ к навыкам
                            prof_skills = details.get('professional_skills', [])
                            if prof_skills and len(prof_skills) > 0:
                                print(f"   Навыки: {prof_skills[0]}")
                            else:
                                print(f"   Навыки: Не указаны")
                        else:
                            print(f"⚠️ Не удалось извлечь детали резюме {i+1}")
                            # Сохраняем хотя бы краткую информацию
                            partial_data = {
                                'card_number': i+1,
                                'card_info': card_info,
                                'detailed_info': None,
                                'processing_status': 'partial'
                            }
                            processed_resumes.append(partial_data)
                            failed_count += 1
                        
                        # Возвращаемся назад
                        if self.go_back():
                            print(f"↩️ Вернулись на список после карточки {i+1}")
                            time.sleep(1.5)  # Увеличенная пауза для стабилизации
                        else:
                            print(f"❌ Не удалось вернуться после карточки {i+1}")
                            break  # Прекращаем обработку, если не можем вернуться
                            
                    else:
                        print(f"❌ Не удалось перейти в карточку {i+1}")
                        failed_count += 1
                        continue
                    
                    # Прогресс
                    progress = ((i+1) / total_cards) * 100
                    print(f"📈 Прогресс: {progress:.1f}% ({i+1}/{total_cards})")
                    
                    # Небольшая пауза между обработкой карточек
                    if i < total_cards - 1:
                        time.sleep(0.5)
                        
                except Exception as e:
                    print(f"❌ Ошибка при обработке карточки {i+1}: {e}")
                    failed_count += 1
                    continue
            
            # Итоговая статистика
            print(f"\n{'='*60}")
            print(f"📊 ИТОГИ МАССОВОЙ ОБРАБОТКИ")
            print(f"{'='*60}")
            print(f"✅ Успешно обработано: {successful_count}")
            print(f"❌ Ошибок: {failed_count}")
            print(f"📋 Всего карточек: {total_cards}")
            print(f"📈 Успешность: {(successful_count/total_cards)*100:.1f}%")
            print(f"{'='*60}")
            
            return processed_resumes
            
        except Exception as e:
            print(f"❌ Критическая ошибка в массовой обработке: {e}")
            return []

    def close_driver(self):
        """Закрытие браузера"""
        try:
            if self.driver:
                self.logger.info("Закрытие браузера...")
                
                # Проверяем, отвечает ли драйвер
                try:
                    self.driver.current_url
                    self.driver.quit()
                    self.logger.info("✅ Браузер корректно закрыт")
                except Exception as e:
                    self.logger.warning(f"Браузер не отвечал, принудительное закрытие: {e}")
                    try:
                        self.driver.quit()
                    except:
                        pass
                
                self.driver = None
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии браузера: {e}")
        finally:
            self.driver = None


if __name__ == "__main__":
    parser = WorkUaParser()
    print("Work.ua Parser инициализирован")
    
    # Тестируем массовую обработку карточек (демо версия - первые 3)
    if parser.setup_driver():
        print("Драйвер готов к работе")
        
        if parser.open_page():
            print("✅ Страница успешно открыта")
            
            # НОВАЯ СИСТЕМА ПАГИНАЦИИ
            processed_resumes = []
            successful_count = 0
            failed_count = 0
            total_pages_processed = 0
            total_cards_across_pages = 0
            
            max_pages = PARSING_CONFIG.get('max_pages', 10)
            pagination_enabled = PARSING_CONFIG.get('enable_pagination', True)
            
            print(f"\n🚀 ЗАПУСКАЕМ ПОЛНУЮ ОБРАБОТКУ С ПАГИНАЦИЕЙ:")
            print(f"📄 Максимум страниц: {max_pages}")
            print(f"🔄 Пагинация: {'Включена' if pagination_enabled else 'Отключена'}")
            print(f"{'='*50}")
            
            # ОСНОВНОЙ ЦИКЛ ПАГИНАЦИИ
            current_page = 1
            while current_page <= max_pages:
                print(f"\n📄 ОБРАБАТЫВАЕМ СТРАНИЦУ {current_page}/{max_pages}")
                print(f"{'='*50}")
                
                # Находим карточки на текущей странице
                cards = parser.find_resume_cards()
                if not cards:
                    print(f"❌ Карточки не найдены на странице {current_page}")
                    break
                
                print(f"🎯 Найдено {len(cards)} карточек на странице {current_page}")
                total_cards_across_pages += len(cards)
                
                # Ограничиваем количество карточек для тестирования
                max_cards_per_page = PARSING_CONFIG.get('max_cards_per_page', len(cards))
                total_cards = min(len(cards), max_cards_per_page)
                
                print(f"🎯 Обрабатываем {total_cards} из {len(cards)} карточек (лимит: {max_cards_per_page})")
                
                # Обрабатываем по индексу, а не по элементу
                for i in range(total_cards):
                    try:
                        print(f"\n{'='*50}")
                        print(f"🎯 ОБРАБАТЫВАЕМ КАРТОЧКУ {i+1}/{total_cards}")
                        print(f"{'='*50}")
                        
                        # ЗАНОВО находим карточки для избежания stale reference
                        current_cards = parser.find_resume_cards()
                        if not current_cards or i >= len(current_cards):
                            print(f"⚠️ Карточка {i+1} больше не доступна")
                            failed_count += 1
                            continue
                        
                        current_card = current_cards[i]
                        
                        # Извлекаем краткую информацию
                        card_info = parser.parse_card_info(current_card)
                        if not card_info:
                            print(f"⚠️ Не удалось извлечь информацию из карточки {i+1}")
                            failed_count += 1
                            continue
                        
                        print(f"📋 Карточка: {card_info['title']}")
                        print(f"👤 Имя: {card_info['name']}")
                        
                        # Переходим в резюме
                        if parser.click_card(current_card):
                            print(f"✅ Перешли в резюме {i+1}")
                            
                            # Извлекаем детальную информацию с помощью LLM
                            details = parser.parse_resume_with_llm()
                            
                            if details:
                                full_data = {
                                    'card_number': i+1,
                                    'card_info': card_info,
                                    'detailed_info': details
                                }
                                processed_resumes.append(full_data)
                                successful_count += 1
                                
                                print(f"✅ Резюме {i+1} обработано!")
                                print(f"   Детали: {details['full_name']}")
                                # Безопасный доступ к навыкам
                                prof_skills = details.get('professional_skills', [])
                                if prof_skills and len(prof_skills) > 0:
                                    print(f"   Навыки: {prof_skills[0]}")
                                else:
                                    print(f"   Навыки: Нет")
                            else:
                                failed_count += 1
                            
                            # Возвращаемся назад
                            if parser.go_back():
                                print(f"↩️ Вернулись на список")
                                time.sleep(1.5)  # Увеличенная пауза
                            else:
                                print(f"❌ Проблема с возвратом")
                                break
                                
                        else:
                            print(f"❌ Не удалось перейти в карточку {i+1}")
                            failed_count += 1
                            
                        progress = ((i+1) / total_cards) * 100
                        print(f"📈 Прогресс: {progress:.1f}%")
                        
                    except Exception as e:
                        print(f"❌ Ошибка: {e}")
                        failed_count += 1
                
                # ОБРАБОТКА СТРАНИЦЫ ЗАВЕРШЕНА
                total_pages_processed += 1
                print(f"\n📄 Страница {current_page} обработана!")
                print(f"   ✅ Успешно: {successful_count}")
                print(f"   ❌ Ошибок: {failed_count}")
                print(f"   📋 Карточек на странице: {total_cards}")
                
                # ПЕРЕХОД НА СЛЕДУЮЩУЮ СТРАНИЦУ
                if pagination_enabled and current_page < max_pages:
                    print(f"\n🔍 Проверяем наличие следующей страницы...")
                    
                    if parser.has_next_page():
                        print(f"✅ Найдена следующая страница")
                        if parser.go_to_next_page():
                            current_page += 1
                            print(f"📄 Перешли на страницу {current_page}")
                            time.sleep(PARSING_CONFIG.get('delay_between_pages', 2))
                        else:
                            print(f"❌ Не удалось перейти на следующую страницу")
                            break
                    else:
                        print(f"🏁 Следующая страница не найдена - достигнут конец")
                        break
                else:
                    if not pagination_enabled:
                        print(f"⏹️ Пагинация отключена - останавливаемся")
                    else:
                        print(f"🏁 Достигнут лимит страниц ({max_pages})")
                    break
            
            # ИТОГИ ПОЛНОЙ ОБРАБОТКИ ВСЕХ СТРАНИЦ
            print(f"\n{'='*50}")
            print(f"📊 ИТОГИ ПОЛНОЙ ОБРАБОТКИ С ПАГИНАЦИЕЙ")
            print(f"{'='*50}")
            print(f"📄 Страниц обработано: {total_pages_processed}")
            print(f"📋 Всего карточек: {total_cards_across_pages}")
            print(f"✅ Успешно: {successful_count}")
            print(f"❌ Ошибок: {failed_count}")
            if total_cards_across_pages > 0:
                print(f"📈 Успешность: {(successful_count/total_cards_across_pages)*100:.1f}%")
            print(f"📚 Обработано резюме: {len(processed_resumes)}")
            print(f"{'='*50}")
            
            # Сохраняем результаты в JSON файл
            if processed_resumes:
                output_filename = f"work_ua_resumes_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(processed_resumes, f, ensure_ascii=False, indent=2)
                print(f"💾 Результаты сохранены в файл: {output_filename}")
            else:
                print("⚠️ Нет данных для сохранения")
                
        else:
            print("❌ Не удалось открыть страницу")
            
        parser.close_driver()
    else:
        print("Не удалось инициализировать драйвер") 