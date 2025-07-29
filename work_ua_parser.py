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
            
            resume_details = {}
            
            # Основная информация - заголовок резюме (должность)
            try:
                # Пробуем разные селекторы для заголовка резюме
                title_selectors = ["h1.card-title", "h1", ".resume-header h1", ".card-header h1"]
                title_found = False
                
                for selector in title_selectors:
                    try:
                        title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_element.text.strip()
                        if title_text and len(title_text) > 3:
                            resume_details['full_title'] = title_text
                            title_found = True
                            break
                    except:
                        continue
                
                if not title_found:
                    resume_details['full_title'] = "Не указано"
            except:
                resume_details['full_title'] = "Не указано"
            
            # Полное имя - ищем в разных местах
            try:
                name_found = False
                
                # Ищем имя в специальных блоках
                name_selectors = [".card-body .strong-600", ".personal-info .name", "h2.name", ".candidate-name"]
                
                for selector in name_selectors:
                    try:
                        name_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for name_elem in name_elements:
                            name_text = name_elem.text.strip()
                            # Проверяем, что это действительно имя (не содержит "грн", цифры в больших количествах)
                            if name_text and "грн" not in name_text and len(name_text.split()) <= 3:
                                resume_details['full_name'] = name_text
                                name_found = True
                                break
                        if name_found:
                            break
                    except:
                        continue
                
                if not name_found:
                    resume_details['full_name'] = "Не указано"
            except:
                resume_details['full_name'] = "Не указано"
            
            # Зарплатные ожидания - улучшенный поиск
            try:
                salary_selectors = [".salary-value", ".salary", ".expected-salary", "span:contains('грн')", ".strong-600"]
                salary_found = False
                
                for selector in salary_selectors:
                    try:
                        salary_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for sal_elem in salary_elements:
                            sal_text = sal_elem.text.strip()
                            if "грн" in sal_text:
                                resume_details['expected_salary'] = sal_text
                                salary_found = True
                                break
                        if salary_found:
                            break
                    except:
                        continue
                
                if not salary_found:
                    resume_details['expected_salary'] = "Не указана"
            except:
                resume_details['expected_salary'] = "Не указана"
            
            # Детальный опыт работы - улучшенный парсинг
            try:
                experience_list = []
                
                # Ищем блоки с опытом работы
                experience_selectors = [
                    ".work-experience li",
                    ".experience .card-body ul li", 
                    ".experience-item",
                    "ul.list-unstyled li",
                    ".timeline-item"
                ]
                
                for selector in experience_selectors:
                    try:
                        exp_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for exp in exp_elements[:5]:  # Берем первые 5
                            exp_text = exp.text.strip()
                            # Фильтруем: должно быть достаточно длинное и содержать информацию о работе
                            if (exp_text and len(exp_text) > 20 and 
                                any(word in exp_text.lower() for word in ["бухгалтер", "робота", "досвід", "компанія", "рік", "місяць"])):
                                experience_list.append(exp_text)
                        
                        if experience_list:  # Если нашли опыт, прекращаем поиск
                            break
                    except:
                        continue
                
                # Если не нашли в специальных блоках, ищем в основном тексте
                if not experience_list:
                    try:
                        all_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "p, div")
                        for p in all_paragraphs:
                            p_text = p.text.strip()
                            if (len(p_text) > 30 and len(p_text) < 200 and
                                any(word in p_text.lower() for word in ["досвід", "працював", "робота", "компанія"])):
                                experience_list.append(p_text)
                                if len(experience_list) >= 3:
                                    break
                    except:
                        pass
                
                resume_details['detailed_experience'] = experience_list
            except:
                resume_details['detailed_experience'] = []
            
            # Образование - улучшенный поиск
            try:
                education_info = []
                
                # Ищем информацию об образовании
                all_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                education_keywords = ["освіта", "університет", "інститут", "коледж", "технікум", "диплом"]
                
                # Ищем параграфы с образованием
                all_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "p, div, li")
                for p in all_paragraphs:
                    p_text = p.text.strip()
                    if (p_text and len(p_text) > 10 and len(p_text) < 150 and
                        any(keyword in p_text.lower() for keyword in education_keywords)):
                        education_info.append(p_text)
                        if len(education_info) >= 2:
                            break
                
                if not education_info:
                    # Общий поиск упоминаний образования
                    found_keywords = [kw for kw in education_keywords if kw in all_text]
                    if found_keywords:
                        education_info = [f"Найдено упоминание: {', '.join(found_keywords)}"]
                    else:
                        education_info = ["Не указано"]
                
                resume_details['education'] = education_info
            except:
                resume_details['education'] = ["Не указано"]
            
            # Навыки - расширенный поиск
            try:
                skills_list = []
                
                # Ищем ключевые навыки бухгалтера в тексте
                full_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                accounting_keywords = [
                    "1c", "excel", "бухгалтерія", "звітність", "податки", "баланс", 
                    "документооборот", "зарплата", "облік", "аудит", "касса", "банк",
                    "пдв", "фінанси", "економіка", "планування"
                ]
                
                found_skills = []
                for keyword in accounting_keywords:
                    if keyword in full_text:
                        found_skills.append(keyword)
                
                if found_skills:
                    skills_list = [f"Найденные навыки: {', '.join(found_skills[:8])}"]  # Первые 8
                else:
                    skills_list = ["Навыки не найдены в тексте"]
                
                resume_details['skills'] = skills_list
            except:
                resume_details['skills'] = ["Не указаны"]
            
            # Контактная информация - ищем аккуратно
            try:
                resume_details['contact_info'] = ["Скрыто для конфиденциальности"]
            except:
                resume_details['contact_info'] = ["Скрыто"]
            
            # Дополнительная информация - ищем возраст, город, статус
            try:
                additional_info = []
                
                # Ищем информацию в разных элементах
                info_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, span, div")
                for info in info_elements:
                    info_text = info.text.strip()
                    # Ищем полезную дополнительную информацию
                    if (info_text and len(info_text) < 50 and
                        any(word in info_text.lower() for word in ["рік", "років", "місто", "київ", "харків", "одеса", "дніпро"])):
                        additional_info.append(info_text)
                        if len(additional_info) >= 3:
                            break
                
                resume_details['additional_info'] = additional_info if additional_info else ["Базовая информация"]
            except:
                resume_details['additional_info'] = ["Нет дополнительной информации"]
            
            # URL резюме
            resume_details['resume_url'] = current_url
            
            print("✅ Детальная информация извлечена")
            return resume_details
            
        except Exception as e:
            print(f"❌ Ошибка при извлечении детальной информации: {e}")
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
                        
                        # Извлекаем детальную информацию
                        details = self.parse_resume_details()
                        
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
                            print(f"   Навыки: {', '.join(details['skills'][:1])}")
                            print(f"   Опыт: {len(details['detailed_experience'])} записей")
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


if __name__ == "__main__":
    parser = WorkUaParser()
    print("Work.ua Parser инициализирован")
    
    # Тестируем массовую обработку карточек (демо версия - первые 3)
    if parser.setup_driver():
        print("Драйвер готов к работе")
        
        if parser.open_page():
            print("✅ Страница успешно открыта")
            
            # Находим все карточки
            cards = parser.find_resume_cards()
            if cards:
                print(f"🎯 Найдено {len(cards)} карточек")
                
                print(f"\n🧪 ТЕСТИРУЕМ МАССОВУЮ ОБРАБОТКУ (первые 3 карточки):")
                print("📝 Для демо ограничиваем до 3 карточек, чтобы не перегружать тест")
                
                # Используем исправленную логику из process_all_cards
                processed_resumes = []
                successful_count = 0
                failed_count = 0
                total_cards = min(3, len(cards))  # Ограничиваем до 3
                
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
                            
                            # Извлекаем детальную информацию
                            details = parser.parse_resume_details()
                            
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
                                print(f"   Навыки: {details['skills'][0] if details['skills'] else 'Нет'}")
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
                
                # Итоги демо-теста
                print(f"\n{'='*50}")
                print(f"📊 ИТОГИ ДЕМО-ТЕСТА")
                print(f"{'='*50}")
                print(f"✅ Успешно: {successful_count}")
                print(f"❌ Ошибок: {failed_count}")
                print(f"📋 Всего: {total_cards}")
                print(f"📈 Успешность: {(successful_count/total_cards)*100:.1f}%")
                print(f"📚 Обработано резюме: {len(processed_resumes)}")
                print(f"{'='*50}")
                
            else:
                print("❌ Карточки не найдены")
                
        else:
            print("❌ Не удалось открыть страницу")
            
        parser.close_driver()
    else:
        print("Не удалось инициализировать драйвер") 