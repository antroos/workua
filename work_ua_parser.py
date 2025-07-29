"""
Work.ua Resume Parser
Парсер резюме с сайта work.ua
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import csv
from config import BROWSER_CONFIG


class WorkUaParser:
    def __init__(self):
        """Инициализация парсера"""
        self.driver = None
        self.base_url = "https://www.work.ua/resumes-%D0%B1%D1%83%D1%85%D0%B3%D0%B0%D0%BB%D1%82%D0%B5%D1%80/"
        
    def setup_driver(self):
        """Настройка и запуск Chrome драйвера"""
        print("Настройка Chrome драйвера...")
        
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
        
        try:
            # Создаем сервис для Chrome драйвера
            service = Service(ChromeDriverManager().install())
            
            # Инициализируем драйвер
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Устанавливаем таймауты
            self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
            self.driver.implicitly_wait(BROWSER_CONFIG['implicit_wait'])
            
            print("✅ Chrome драйвер успешно инициализирован")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации драйвера: {e}")
            return False
        
    def open_page(self):
        """Открытие страницы с резюме"""
        if not self.driver:
            print("❌ Драйвер не инициализирован")
            return False
            
        try:
            print(f"Открываем страницу: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Ждем загрузки страницы
            time.sleep(3)
            
            # Проверяем, что страница загружена
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            print(f"✅ Страница загружена:")
            print(f"   URL: {current_url}")
            print(f"   Заголовок: {page_title}")
            
            # Проверяем, что мы на правильной странице
            if "work.ua" in current_url and ("резюме" in page_title.lower() or "resume" in current_url):
                print("✅ Мы на правильной странице work.ua")
                return True
            else:
                print("⚠️ Возможно, мы не на той странице")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при открытии страницы: {e}")
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
        
    def parse_card_info(self, card):
        """Извлечение информации из карточки"""
        if not card:
            return None
            
        try:
            card_info = {}
            
            # Заголовок резюме и ссылка
            try:
                title_element = card.find_element(By.CSS_SELECTOR, "h2 a")
                card_info['title'] = title_element.text.strip()
                card_info['link'] = title_element.get_attribute("href")
            except:
                card_info['title'] = "Не указано"
                card_info['link'] = ""
            
            # Зарплата
            try:
                salary_element = card.find_element(By.CSS_SELECTOR, ".h5.strong-600")
                card_info['salary'] = salary_element.text.strip()
            except:
                card_info['salary'] = "Не указана"
            
            # Имя, возраст, город - ищем более точно
            try:
                # Ищем параграф с информацией о человеке (содержит имя)
                personal_paragraphs = card.find_elements(By.CSS_SELECTOR, "p.mt-xs.mb-0")
                personal_info_found = False
                
                for p in personal_paragraphs:
                    text = p.text.strip()
                    # Проверяем, что это строка с именем (содержит strong-600 и не содержит "грн")
                    if text and "грн" not in text and len(text.split(",")) >= 2:
                        card_info['personal_info'] = text
                        parts = text.split(', ')
                        if len(parts) >= 1:
                            card_info['name'] = parts[0]
                        if len(parts) >= 2:
                            card_info['age_location'] = ', '.join(parts[1:])
                        personal_info_found = True
                        break
                
                if not personal_info_found:
                    card_info['personal_info'] = "Не указано"
                    card_info['name'] = "Не указано"
                    card_info['age_location'] = "Не указано"
                    
            except Exception as e:
                card_info['personal_info'] = "Ошибка извлечения"
                card_info['name'] = "Не указано"
                card_info['age_location'] = "Не указано"
            
            # Опыт работы - фильтруем лишние элементы
            try:
                experience_elements = card.find_elements(By.CSS_SELECTOR, "ul.mt-lg.mb-0 li")
                if experience_elements:
                    experience_list = []
                    for exp in experience_elements[:3]:  # Берем первые 3 записи опыта
                        exp_text = exp.text.strip()
                        # Фильтруем служебные элементы
                        if exp_text and exp_text not in ["PRO", "Файл", ""]:
                            experience_list.append(exp_text)
                    card_info['experience'] = experience_list
                else:
                    card_info['experience'] = []
            except:
                card_info['experience'] = []
            
            # Образование/тип занятости
            try:
                education_elements = card.find_elements(By.CSS_SELECTOR, "p.mb-0.mt-xs.text-default-7")
                if education_elements:
                    card_info['education_employment'] = education_elements[0].text.strip()
                else:
                    card_info['education_employment'] = "Не указано"
            except:
                card_info['education_employment'] = "Не указано"
            
            return card_info
            
        except Exception as e:
            print(f"❌ Ошибка при извлечении информации из карточки: {e}")
            return None
        
    def click_card(self, card):
        """Переход внутрь карточки"""
        if not card or not self.driver:
            print("❌ Карточка или драйвер не доступны")
            return False
            
        try:
            # Находим ссылку внутри карточки
            link_element = card.find_element(By.CSS_SELECTOR, "h2 a")
            link_url = link_element.get_attribute("href")
            title = link_element.text.strip()
            
            print(f"🔗 Переходим в резюме: '{title}'")
            print(f"   URL: {link_url}")
            
            # Кликаем по ссылке
            link_element.click()
            
            # Ждем загрузки новой страницы
            time.sleep(3)
            
            # Проверяем, что мы перешли на страницу резюме
            current_url = self.driver.current_url
            if "/resumes/" in current_url and current_url != self.base_url:
                print("✅ Успешно перешли на страницу резюме")
                print(f"   Текущий URL: {current_url}")
                return True
            else:
                print("⚠️ Возможно, переход не удался")
                print(f"   Текущий URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при клике по карточке: {e}")
            return False
        
    def go_back(self):
        """Возврат на предыдущую страницу"""
        if not self.driver:
            print("❌ Драйвер не доступен")
            return False
            
        try:
            print("⬅️ Возвращаемся назад...")
            current_url_before = self.driver.current_url
            
            # Возвращаемся назад
            self.driver.back()
            
            # Ждем загрузки
            time.sleep(2)
            
            # Проверяем, что мы вернулись
            current_url_after = self.driver.current_url
            
            if current_url_after != current_url_before:
                print("✅ Успешно вернулись назад")
                print(f"   Текущий URL: {current_url_after}")
                return True
            else:
                print("⚠️ Возможно, возврат не удался")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при возврате назад: {e}")
            return False
        
    def close_driver(self):
        """Закрытие браузера"""
        if self.driver:
            print("Закрытие браузера...")
            self.driver.quit()
            print("✅ Браузер закрыт")


if __name__ == "__main__":
    parser = WorkUaParser()
    print("Work.ua Parser инициализирован")
    
    # Тестируем полный цикл: драйвер + страница + поиск + парсинг + переход
    if parser.setup_driver():
        print("Драйвер готов к работе")
        
        if parser.open_page():
            print("✅ Страница успешно открыта")
            
            # Ищем карточки резюме
            cards = parser.find_resume_cards()
            if cards:
                print(f"🎯 Найдено {len(cards)} карточек")
                
                # Тестируем переход в первую карточку
                print(f"\n🧪 ТЕСТИРУЕМ ПЕРЕХОД В КАРТОЧКУ:")
                first_card = cards[0]
                
                # Парсим информацию о карточке
                card_info = parser.parse_card_info(first_card)
                if card_info:
                    print(f"Тестируем карточку: {card_info['title']}")
                
                # Переходим внутрь карточки
                if parser.click_card(first_card):
                    print("🎉 Переход успешен! Сейчас мы внутри резюме")
                    time.sleep(3)  # Даем время посмотреть страницу резюме
                    
                    # Возвращаемся назад
                    if parser.go_back():
                        print("🎉 Возврат успешен! Мы снова на списке резюме")
                        time.sleep(2)  # Даем время посмотреть
                        
                        # Проверяем, что карточки снова доступны
                        cards_after_return = parser.find_resume_cards()
                        if cards_after_return:
                            print(f"✅ После возврата найдено {len(cards_after_return)} карточек")
                        else:
                            print("⚠️ После возврата карточки не найдены")
                    else:
                        print("❌ Не удалось вернуться назад")
                else:
                    print("❌ Не удалось перейти в карточку")
                    
            else:
                print("❌ Карточки не найдены")
                
        else:
            print("❌ Не удалось открыть страницу")
            
        parser.close_driver()
    else:
        print("Не удалось инициализировать драйвер") 