#!/usr/bin/env python3
"""
Bulletproof Work.ua Parser - НЕУБИВАЕМАЯ ВЕРСИЯ
✅ Recovery механизм при падении драйвера
✅ Детальные логи для отладки
✅ Checkpoint система для возобновления
✅ Проверка живости драйвера
✅ Graceful degradation
"""

import time
import json
import logging
import os
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from work_ua_parser import WorkUaParser
from config import PARSING_CONFIG, BROWSER_CONFIG

class BulletproofWorkUaParser:
    def __init__(self):
        self.setup_logging()
        self.parser = None
        self.driver_restarts = 0
        self.max_driver_restarts = 3
        
        # Checkpoint система
        self.checkpoint_file = f"parsing_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.session_state = {
            'current_page': 1,
            'processed_urls': set(),
            'failed_urls': set(),
            'successful_resumes': 0,
            'errors': [],
            'last_checkpoint': None
        }
        
        # Результаты
        self.all_resumes = []
        
        # Настройки устойчивости
        self.driver_health_check_interval = 10  # проверка каждые 10 операций
        self.operations_count = 0
        self.max_consecutive_errors = 5
        self.consecutive_errors = 0
        
        self.logger.info("🚀 Bulletproof Parser инициализирован")
    
    def setup_logging(self):
        """Настройка детального логирования"""
        log_filename = f"bulletproof_parsing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Консольный хендлер
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Файловый хендлер
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Настройка логгера
        self.logger = logging.getLogger('BulletproofParser')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"📝 Логи сохраняются в: {log_filename}")
    
    def save_checkpoint(self):
        """Сохранение checkpoint для возобновления"""
        try:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'current_page': self.session_state['current_page'],
                'processed_urls': list(self.session_state['processed_urls']),
                'failed_urls': list(self.session_state['failed_urls']),
                'successful_resumes': self.session_state['successful_resumes'],
                'driver_restarts': self.driver_restarts,
                'all_resumes': self.all_resumes
            }
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                
            self.session_state['last_checkpoint'] = datetime.now().isoformat()
            self.logger.debug(f"💾 Checkpoint сохранен: {self.checkpoint_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения checkpoint: {e}")
    
    def load_checkpoint(self, checkpoint_file):
        """Загрузка checkpoint для продолжения"""
        try:
            if not os.path.exists(checkpoint_file):
                self.logger.warning(f"⚠️ Checkpoint файл не найден: {checkpoint_file}")
                return False
                
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            self.session_state['current_page'] = checkpoint_data.get('current_page', 1)
            self.session_state['processed_urls'] = set(checkpoint_data.get('processed_urls', []))
            self.session_state['failed_urls'] = set(checkpoint_data.get('failed_urls', []))
            self.session_state['successful_resumes'] = checkpoint_data.get('successful_resumes', 0)
            self.driver_restarts = checkpoint_data.get('driver_restarts', 0)
            self.all_resumes = checkpoint_data.get('all_resumes', [])
            
            self.logger.info(f"📂 Checkpoint загружен: страница {self.session_state['current_page']}, "
                           f"обработано {len(self.session_state['processed_urls'])} URL")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки checkpoint: {e}")
            return False
    
    def is_driver_alive(self):
        """Проверка живости драйвера"""
        try:
            if not self.parser or not self.parser.driver:
                return False
            
            # Пытаемся получить title страницы
            _ = self.parser.driver.title
            self.logger.debug("💓 Драйвер жив")
            return True
            
        except WebDriverException as e:
            self.logger.warning(f"💀 Драйвер не отвечает: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки драйвера: {e}")
            return False
    
    def restart_driver(self):
        """Перезапуск драйвера"""
        self.logger.warning("🔄 Перезапуск драйвера...")
        
        try:
            # Закрываем старый драйвер
            if self.parser and self.parser.driver:
                try:
                    self.parser.driver.quit()
                    self.logger.debug("🗑️ Старый драйвер закрыт")
                except:
                    pass
            
            # Создаем новый парсер
            self.parser = WorkUaParser()
            
            # ВАЖНО: Инициализируем драйвер!
            if not self.parser.setup_driver():
                self.logger.error("❌ Не удалось инициализировать драйвер")
                return False
            
            # Переходим на страницу с резюме
            self.logger.info("🌐 Восстанавливаем страницу с резюме...")
            base_url = "https://www.work.ua/resumes-%D0%B1%D1%83%D1%85%D0%B3%D0%B0%D0%BB%D1%82%D0%B5%D1%80/"
            self.parser.driver.get(base_url)
                
            self.driver_restarts += 1
            
            # Ждем стабилизации
            time.sleep(5)  # Больше времени после рестарта
            
            if self.is_driver_alive():
                self.logger.info(f"✅ Драйвер перезапущен успешно (рестарт #{self.driver_restarts})")
                self.consecutive_errors = 0
                return True
            else:
                self.logger.error("❌ Новый драйвер не работает")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка перезапуска драйвера: {e}")
            return False
    
    def execute_with_recovery(self, operation_name, operation_func, *args, **kwargs):
        """Выполнение операции с recovery механизмом"""
        self.operations_count += 1
        
        # Периодическая проверка здоровья драйвера
        if self.operations_count % self.driver_health_check_interval == 0:
            if not self.is_driver_alive():
                self.logger.warning(f"🏥 Плановая проверка: драйвер не отвечает")
                if not self.restart_driver():
                    raise Exception("Не удалось восстановить драйвер")
        
        for attempt in range(3):  # 3 попытки
            try:
                self.logger.debug(f"🎯 {operation_name} (попытка {attempt + 1})")
                result = operation_func(*args, **kwargs)
                
                if self.consecutive_errors > 0:
                    self.logger.info(f"✅ Операция успешна после {self.consecutive_errors} ошибок")
                    self.consecutive_errors = 0
                
                return result
                
            except WebDriverException as e:
                self.consecutive_errors += 1
                self.logger.warning(f"⚠️ {operation_name} ошибка #{self.consecutive_errors}: {e}")
                
                # Если слишком много ошибок подряд - рестарт
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self.logger.error(f"🚨 Критично: {self.consecutive_errors} ошибок подряд, рестарт драйвера")
                    
                    if self.driver_restarts >= self.max_driver_restarts:
                        raise Exception(f"Превышен лимит рестартов драйвера: {self.max_driver_restarts}")
                    
                    if not self.restart_driver():
                        raise Exception("Не удалось восстановить драйвер")
                    
                    # После рестарта нужно восстановить состояние
                    self.logger.info("🔄 Пытаемся восстановить состояние после рестарта...")
                    continue
                
                # Небольшая пауза перед повтором
                time.sleep(2 ** attempt)  # экспоненциальная задержка
                
            except Exception as e:
                self.logger.error(f"❌ {operation_name} критическая ошибка: {e}")
                raise
        
        raise Exception(f"Операция {operation_name} не удалась после 3 попыток")
    
    def safe_open_tab(self, url, title):
        """Безопасное открытие вкладки"""
        def _open_tab():
            self.parser.driver.execute_script(f"window.open('{url}', '_blank');")
            handles = self.parser.driver.window_handles
            self.logger.debug(f"📂 Вкладка открыта: {title} | Всего вкладок: {len(handles)}")
            return len(handles)
        
        return self.execute_with_recovery(f"Открытие вкладки: {title}", _open_tab)
    
    def safe_switch_to_tab(self, tab_index):
        """Безопасное переключение на вкладку"""
        def _switch_tab():
            handles = self.parser.driver.window_handles
            if tab_index < len(handles):
                self.parser.driver.switch_to.window(handles[tab_index])
                self.logger.debug(f"🔄 Переключились на вкладку {tab_index}")
                return True
            return False
        
        return self.execute_with_recovery(f"Переключение на вкладку {tab_index}", _switch_tab)
    
    def safe_close_tab(self):
        """Безопасное закрытие вкладки"""
        def _close_tab():
            self.parser.driver.close()
            self.logger.debug("🗑️ Вкладка закрыта")
            return True
        
        return self.execute_with_recovery("Закрытие вкладки", _close_tab)
    
    def safe_get_page_cards(self):
        """Безопасное получение карточек на странице"""
        def _get_cards():
            cards = self.parser.driver.find_elements(By.CSS_SELECTOR, ".card.resume-link")
            self.logger.debug(f"🔍 Найдено карточек: {len(cards)}")
            
            card_data = []
            for i, card in enumerate(cards):
                try:
                    # Используем правильный селектор как в рабочем коде
                    title_element = card.find_element(By.CSS_SELECTOR, "h2 a")
                    
                    url = title_element.get_attribute("href")
                    title = title_element.text.strip()
                    
                    card_data.append({
                        'index': i,
                        'url': url,
                        'title': title
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка обработки карточки {i}: {e}")
                    continue
            
            return card_data
        
        return self.execute_with_recovery("Получение карточек", _get_cards)
    
    def bulletproof_multitab_parsing(self, max_pages=2, max_cards_per_page=5):
        """Неубиваемый multitab парсинг"""
        self.logger.info(f"🚀 Начинаем bulletproof парсинг: {max_pages} страниц, {max_cards_per_page} карточек на страницу")
        
        try:
            # Инициализация парсера
            if not self.parser:
                self.parser = WorkUaParser()
                
                # ВАЖНО: Инициализируем драйвер!
                self.logger.info("🔧 Инициализация драйвера...")
                if not self.parser.setup_driver():
                    raise Exception("❌ Не удалось инициализировать драйвер")
                
                # Переходим на страницу с резюме
                self.logger.info("🌐 Переход на страницу с резюме...")
                base_url = "https://www.work.ua/resumes-%D0%B1%D1%83%D1%85%D0%B3%D0%B0%D0%BB%D1%82%D0%B5%D1%80/"
                self.parser.driver.get(base_url)
                
                # Ждем загрузки
                time.sleep(3)
                
                self.logger.info("✅ Драйвер готов к работе")
            
            for page_num in range(self.session_state['current_page'], max_pages + 1):
                self.logger.info(f"\n{'='*80}")
                self.logger.info(f"📄 СТРАНИЦА {page_num}")
                self.logger.info(f"{'='*80}")
                
                self.session_state['current_page'] = page_num
                
                try:
                    # Получаем карточки на странице
                    all_cards = self.safe_get_page_cards()
                    
                    # Фильтруем уже обработанные
                    new_cards = []
                    for card in all_cards:
                        if card['url'] not in self.session_state['processed_urls']:
                            new_cards.append(card)
                        else:
                            self.logger.debug(f"⏭️ Пропускаем дубликат: {card['title']}")
                    
                    cards_to_process = new_cards[:max_cards_per_page]
                    self.logger.info(f"🎯 К обработке: {len(cards_to_process)} из {len(all_cards)} карточек")
                    
                    if not cards_to_process:
                        self.logger.info("⏭️ Нет новых карточек для обработки")
                        continue
                    
                    # Открываем вкладки партиями по 2
                    batch_size = 2
                    for batch_start in range(0, len(cards_to_process), batch_size):
                        batch = cards_to_process[batch_start:batch_start + batch_size]
                        self.logger.info(f"\n📦 Партия {batch_start//batch_size + 1}: {len(batch)} резюме")
                        
                        # Открываем вкладки
                        opened_tabs = []
                        for card in batch:
                            try:
                                tabs_before = len(self.parser.driver.window_handles)
                                self.safe_open_tab(card['url'], card['title'])
                                opened_tabs.append(card)
                                
                                # Человекоподобная пауза
                                pause = random.uniform(0.5, 1.5)
                                self.logger.debug(f"⏱️ Пауза {pause:.1f}s...")
                                time.sleep(pause)
                                
                            except Exception as e:
                                self.logger.error(f"❌ Не удалось открыть {card['title']}: {e}")
                                self.session_state['failed_urls'].add(card['url'])
                        
                        # Парсим открытые вкладки
                        main_tab = 0
                        for i, card in enumerate(opened_tabs, 1):
                            try:
                                self.safe_switch_to_tab(i)
                                
                                # Здесь будет парсинг резюме
                                self.logger.info(f"📋 Парсим: {card['title']}")
                                # TODO: Добавить реальный парсинг резюме
                                
                                # Имитация парсинга
                                time.sleep(random.uniform(1, 3))
                                
                                self.session_state['processed_urls'].add(card['url'])
                                self.session_state['successful_resumes'] += 1
                                
                                self.safe_close_tab()
                                
                            except Exception as e:
                                self.logger.error(f"❌ Ошибка парсинга {card['title']}: {e}")
                                self.session_state['failed_urls'].add(card['url'])
                        
                        # Возвращаемся на главную вкладку
                        self.safe_switch_to_tab(main_tab)
                        
                        # Сохраняем checkpoint
                        self.save_checkpoint()
                        
                        # Пауза между партиями
                        if batch_start + batch_size < len(cards_to_process):
                            pause = random.uniform(3, 7)
                            self.logger.info(f"⏸️ Пауза между партиями {pause:.1f}s...")
                            time.sleep(pause)
                    
                    self.logger.info(f"✅ Страница {page_num} обработана")
                    
                    # Переход на следующую страницу (если не последняя)
                    if page_num < max_pages:
                        self.logger.info(f"⏭️ Переходим на страницу {page_num + 1}...")
                        # TODO: Добавить реальную навигацию
                        time.sleep(random.uniform(2, 4))
                
                except Exception as e:
                    self.logger.error(f"❌ Критическая ошибка на странице {page_num}: {e}")
                    continue
            
            # Финальная статистика
            self.print_final_stats()
            return True
            
        except Exception as e:
            self.logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА ПАРСИНГА: {e}")
            self.save_checkpoint()
            return False
        
        finally:
            self.cleanup()
    
    def print_final_stats(self):
        """Печать финальной статистики"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🎉 ИТОГИ BULLETPROOF ПАРСИНГА")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"✅ Успешно обработано: {self.session_state['successful_resumes']} резюме")
        self.logger.info(f"⏭️ Пропущено дубликатов: {len(self.session_state['processed_urls']) - self.session_state['successful_resumes']}")
        self.logger.info(f"❌ Неудачных попыток: {len(self.session_state['failed_urls'])}")
        self.logger.info(f"🔄 Рестартов драйвера: {self.driver_restarts}")
        self.logger.info(f"📄 Обработано страниц: {self.session_state['current_page']}")
        self.logger.info(f"💾 Checkpoint файл: {self.checkpoint_file}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.parser and self.parser.driver:
                self.parser.driver.quit()
                self.logger.info("🧹 Драйвер закрыт")
        except:
            pass

if __name__ == "__main__":
    parser = BulletproofWorkUaParser()
    
    # Можно загрузить checkpoint для продолжения
    # parser.load_checkpoint("parsing_checkpoint_20250731_170000.json")
    
    success = parser.bulletproof_multitab_parsing(max_pages=3, max_cards_per_page=4)
    
    if success:
        print("\n🎊 BULLETPROOF ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
    else:
        print("\n💀 BULLETPROOF ПАРСИНГ ПРЕРВАН, НО CHECKPOINT СОХРАНЕН!")