#!/usr/bin/env python3
"""
ULTIMATE Work.ua Parser - ЛУЧШЕЕ ИЗ ДВУХ МИРОВ
✅ Основной парсер: LLM автоадаптация + детальный парсинг + fallback селекторы
✅ Bulletproof логика: Multi-tab + recovery + checkpoint + детальные логи
✅ Революционный подход: Открываем все резюме в табах без PJAX проблем
"""

import time
import json
import logging
import os
import random
from datetime import datetime
from work_ua_parser import WorkUaParser

class UltimateWorkUaParser(WorkUaParser):
    def __init__(self):
        """Инициализация ULTIMATE парсера на базе основного"""
        super().__init__()  # Получаем все методы основного парсера
        
        self.setup_bulletproof_logging()
        
        # Bulletproof состояние
        self.driver_restarts = 0
        self.max_driver_restarts = 3
        self.operations_count = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        # Checkpoint система
        self.checkpoint_file = f"ultimate_parsing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.session_state = {
            'current_page': 1,
            'processed_urls': set(),
            'failed_urls': set(),
            'successful_resumes': 0,
            'last_checkpoint': None
        }
        
        # Multi-tab настройки  
        self.max_tabs_at_once = 3
        self.batch_size = 2
        self.main_tab_handle = None
        
        # 💾 Файл для сохранения детальных данных резюме
        self.data_file = f"resume_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.resume_data = []  # Список всех спарсенных резюме с полной информацией
        
        # Health check настройки
        self.health_check_interval = 3  # Проверка каждые 3 операции (чаще!)
        self.operations_since_check = 0
        
        # 🔄 Retry настройки для 100% обработки
        self.max_retries_per_card = 3  # Максимум попыток на одну карточку
        self.failed_cards_retry = []   # Карточки для повторной обработки
        
        self.logger.info("🚀 ULTIMATE Parser инициализирован (основной парсер + bulletproof логика)")
    
    def setup_bulletproof_logging(self):
        """Настройка детального логирования поверх основного"""
        log_filename = f"ultimate_parsing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Добавляем файловый хендлер к существующему логгеру
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info(f"📝 Bulletproof логи: {log_filename}")
    
    def parse_single_card_with_retry(self, card, tab_index):
        """🔄 Обработка одной карточки с retry механизмом"""
        max_attempts = self.max_retries_per_card
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"📋 ULTIMATE парсинг: {card['title']} (попытка {attempt}/{max_attempts})")
                
                # Проверяем health перед каждой попыткой
                if not self.auto_health_monitor():
                    self.logger.warning(f"❌ Health check провален для {card['title']} (попытка {attempt})")
                    if attempt < max_attempts:
                        self.logger.info(f"🔄 Перезапускаем драйвер перед повторной попыткой...")
                        if not self.restart_driver_bulletproof():
                            continue
                        # После рестарта нужно снова открыть вкладку
                        self.safe_open_tab(card['url'], card['title'])
                        self.safe_switch_to_tab(1)  # Переключаемся на новую вкладку
                    else:
                        continue
                
                # Используем детальный парсинг основного парсера!
                resume_details = self.parse_resume_details()
                
                if resume_details:
                    # Объединяем данные карточки и детали
                    full_resume = {**card['full_info'], **resume_details}
                    
                    # 💾 СОХРАНЯЕМ детальную информацию!
                    self.save_resume_data(full_resume)
                    
                    self.logger.info(f"✅ Успешно спарсено: {full_resume.get('title', 'Без названия')} (попытка {attempt})")
                    self.session_state['successful_resumes'] += 1
                    self.session_state['processed_urls'].add(card['url'])
                    
                    # Health check после успешной операции
                    self.auto_health_monitor()
                    return True  # Успешно обработано
                else:
                    self.logger.warning(f"⚠️ Частичные данные для: {card['title']} (попытка {attempt})")
                    if attempt < max_attempts:
                        continue
                    else:
                        self.session_state['processed_urls'].add(card['url'])
                        return False  # Не удалось получить детали
                        
            except Exception as e:
                self.logger.error(f"❌ Ошибка парсинга {card['title']} (попытка {attempt}): {e}")
                
                if attempt < max_attempts:
                    self.logger.info(f"🔄 Перезапускаем драйвер для повторной попытки...")
                    if self.restart_driver_bulletproof():
                        # После рестарта нужно снова открыть вкладку
                        try:
                            self.safe_open_tab(card['url'], card['title'])
                            self.safe_switch_to_tab(1)  # Переключаемся на новую вкладку
                        except:
                            continue
                    continue
                else:
                    self.logger.error(f"💀 Окончательно не удалось обработать {card['title']} после {max_attempts} попыток")
                    self.session_state['failed_urls'].add(card['url'])
                    return False
        
        return False  # Если все попытки исчерпаны

    def save_resume_data(self, resume_data):
        """💾 Сохранение детальных данных резюме в JSON файл"""
        try:
            self.resume_data.append(resume_data)
            
            # Сохраняем все данные в JSON файл
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.resume_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"💾 Резюме сохранено: {len(self.resume_data)} из {self.session_state['successful_resumes']}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения данных резюме: {e}")

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
                'data_file': self.data_file  # Ссылка на файл с детальными данными
            }
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                
            self.session_state['last_checkpoint'] = datetime.now().isoformat()
            self.logger.debug(f"💾 Checkpoint сохранен: {self.checkpoint_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения checkpoint: {e}")
    
    def is_driver_alive(self):
        """Проверка живости драйвера"""
        try:
            if not self.driver:
                return False
            
            # Пытаемся получить title страницы
            _ = self.driver.title
            self.logger.debug("💓 Драйвер жив")
            return True
            
        except Exception as e:
            self.logger.warning(f"💀 Драйвер не отвечает: {e}")
            return False
    
    def proactive_health_check(self):
        """🏥 Проактивная проверка здоровья драйвера"""
        try:
            if not self.driver:
                self.logger.warning("🚨 Драйвер None - требуется перезапуск")
                return False
                
            # Быстрая проверка жизни драйвера
            current_url = self.driver.current_url
            window_handles = self.driver.window_handles
            
            if not current_url or len(window_handles) == 0:
                self.logger.warning("🚨 Драйвер не отвечает корректно")
                return False
                
            # Скрытый health check - не логируем успешные проверки
            return True
            
        except Exception as e:
            self.logger.warning(f"🚨 Health check: драйвер мертв ({str(e)[:100]})")
            return False
    
    def auto_health_monitor(self):
        """🔄 Автоматический мониторинг с перезапуском при необходимости"""
        self.operations_since_check += 1
        
        # Проверяем каждые N операций
        if self.operations_since_check >= self.health_check_interval:
            self.operations_since_check = 0
            
            if not self.proactive_health_check():
                self.logger.warning("🏥 Плановая проверка: драйвер не отвечает")
                return self.restart_driver_bulletproof()
                
        return True

    def restart_driver_bulletproof(self):
        """Bulletproof перезапуск драйвера"""
        self.logger.warning("🔄 Bulletproof перезапуск драйвера...")
        
        try:
            # Закрываем старый драйвер
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.debug("🗑️ Старый драйвер закрыт")
                except:
                    pass
            
            # Используем метод основного парсера
            if not self.setup_driver():
                self.logger.error("❌ Не удалось перезапустить драйвер")
                return False
            
            # Переходим на правильную страницу с резюме
            current_page = self.session_state.get('current_page', 1)
            if current_page > 1:
                recovery_url = f"{self.base_url}?page={current_page}"
                self.logger.info(f"🌐 Восстанавливаем страницу с резюме: страница {current_page}")
                self.logger.info(f"🔗 URL восстановления: {recovery_url}")
            else:
                recovery_url = self.base_url
                self.logger.info("🌐 Восстанавливаем страницу с резюме: страница 1")
            
            self.driver.get(recovery_url)
            
            # Ждем загрузки страницы
            time.sleep(3)
            
            # Ждем загрузки карточек резюме
            try:
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.common.by import By
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".card.resume-link"))
                )
                self.logger.info("✅ Карточки резюме загружены после восстановления")
            except Exception as e:
                self.logger.warning(f"⚠️ Карточки не загрузились: {e}")
            
            self.driver_restarts += 1
            time.sleep(2)  # Дополнительная стабилизация
            
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
        if self.operations_count % 10 == 0:
            if not self.is_driver_alive():
                self.logger.warning(f"🏥 Плановая проверка: драйвер не отвечает")
                if not self.restart_driver_bulletproof():
                    raise Exception("Не удалось восстановить драйвер")
        
        for attempt in range(3):
            try:
                self.logger.debug(f"🎯 {operation_name} (попытка {attempt + 1})")
                result = operation_func(*args, **kwargs)
                
                if self.consecutive_errors > 0:
                    self.logger.info(f"✅ Операция успешна после {self.consecutive_errors} ошибок")
                    self.consecutive_errors = 0
                
                return result
                
            except Exception as e:
                self.consecutive_errors += 1
                self.logger.warning(f"⚠️ {operation_name} ошибка #{self.consecutive_errors}: {e}")
                
                # Если слишком много ошибок подряд - рестарт
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self.logger.error(f"🚨 Критично: {self.consecutive_errors} ошибок подряд")
                    
                    if self.driver_restarts >= self.max_driver_restarts:
                        raise Exception(f"Превышен лимит рестартов: {self.max_driver_restarts}")
                    
                    if not self.restart_driver_bulletproof():
                        raise Exception("Не удалось восстановить драйвер")
                    
                    continue
                
                # Экспоненциальная задержка
                time.sleep(2 ** attempt)
        
        raise Exception(f"Операция {operation_name} не удалась после 3 попыток")
    
    def safe_open_tab(self, url, title):
        """Безопасное открытие вкладки с recovery"""
        def _open_tab():
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            handles = self.driver.window_handles
            self.logger.debug(f"📂 Вкладка открыта: {title} | Всего: {len(handles)}")
            return len(handles)
        
        return self.execute_with_recovery(f"Открытие вкладки: {title}", _open_tab)
    
    def safe_switch_to_tab(self, tab_index):
        """Безопасное переключение на вкладку"""
        def _switch_tab():
            handles = self.driver.window_handles
            if tab_index < len(handles):
                self.driver.switch_to.window(handles[tab_index])
                self.logger.debug(f"🔄 Переключились на вкладку {tab_index}")
                return True
            return False
        
        return self.execute_with_recovery(f"Переключение на вкладку {tab_index}", _switch_tab)
    
    def safe_close_tab(self):
        """Безопасное закрытие вкладки"""
        def _close_tab():
            self.driver.close()
            self.logger.debug("🗑️ Вкладка закрыта")
            return True
        
        return self.execute_with_recovery("Закрытие вкладки", _close_tab)
    
    def get_cards_with_llm_fallback(self):
        """Получение карточек с LLM fallback из основного парсера"""
        def _get_cards():
            self.logger.info("🔍 Начинаем поиск карточек...")
            start_time = time.time()
            
            # Используем метод основного парсера с LLM автоадаптацией!
            self.logger.info("📡 Вызов find_resume_cards()...")
            cards = self.find_resume_cards()
            find_time = time.time() - start_time
            self.logger.info(f"✅ find_resume_cards() завершен за {find_time:.1f}с, найдено: {len(cards) if cards else 0}")
            
            if not cards:
                self.logger.warning("⚠️ Основной метод не нашел карточки")
                return []
            
            # Извлекаем данные из карточек
            self.logger.info(f"🔧 Начинаем обработку {len(cards)} карточек...")
            card_data = []
            for i, card in enumerate(cards):
                try:
                    card_start_time = time.time()
                    self.logger.info(f"🔄 Обработка карточки {i+1}/{len(cards)}...")
                    
                    # Используем метод основного парсера для извлечения данных
                    card_info = self.parse_card_info(card)
                    
                    card_time = time.time() - card_start_time
                    self.logger.info(f"✅ Карточка {i+1} обработана за {card_time:.1f}с")
                    
                    if card_info and card_info.get('url'):
                        card_data.append({
                            'index': i,
                            'url': card_info['url'],
                            'title': card_info.get('title', 'Без названия'),
                            'card_element': card,
                            'full_info': card_info
                        })
                        self.logger.info(f"📄 {card_info.get('title', 'Без названия')}")
                    else:
                        self.logger.warning(f"⚠️ Карточка {i+1}: нет URL или данных")
                
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка обработки карточки {i}: {e}")
                    continue
            
            total_time = time.time() - start_time
            self.logger.info(f"🔍 Извлечено данных: {len(card_data)} из {len(cards)} за {total_time:.1f}с")
            return card_data
        
        return self.execute_with_recovery("Получение карточек с LLM", _get_cards)
    
    def ultimate_multitab_parsing(self, max_pages=3, max_cards_per_page=5):
        """ULTIMATE Multi-tab парсинг с LLM + bulletproof"""
        self.logger.info(f"🚀 ULTIMATE парсинг: {max_pages} страниц, {max_cards_per_page} карточек")
        
        try:
            # Инициализация драйвера
            if not self.driver:
                self.logger.info("🔧 Инициализация ULTIMATE парсера...")
                if not self.setup_driver():
                    raise Exception("❌ Не удалось инициализировать драйвер")
                
                # Переходим на базовую страницу
                self.logger.info("🌐 Переход на страницу с резюме...")
                self.driver.get(self.base_url)
                time.sleep(3)
                
                self.main_tab_handle = self.driver.current_window_handle
                self.logger.info("✅ ULTIMATE парсер готов к работе")
            
            # Основной цикл по страницам
            for page_num in range(self.session_state['current_page'], max_pages + 1):
                self.logger.info(f"\n{'='*80}")
                self.logger.info(f"📄 ULTIMATE СТРАНИЦА {page_num}")
                self.logger.info(f"{'='*80}")
                
                # Критический health check в начале каждой страницы
                if not self.proactive_health_check():
                    self.logger.warning("🚨 Критический health check провален в начале страницы")
                    if not self.restart_driver_bulletproof():
                        self.logger.critical("💀 Невозможно восстановить драйвер - прерываем парсинг")
                        break
                
                self.session_state['current_page'] = page_num
                
                try:
                    # Получаем карточки с LLM автоадаптацией
                    all_cards = self.get_cards_with_llm_fallback()
                    
                    # Фильтруем дубликаты
                    new_cards = []
                    for card in all_cards:
                        if card['url'] not in self.session_state['processed_urls']:
                            new_cards.append(card)
                        else:
                            self.logger.debug(f"⏭️ Пропускаем дубликат: {card['title']}")
                    
                    cards_to_process = new_cards[:max_cards_per_page]
                    self.logger.info(f"🎯 К обработке: {len(cards_to_process)} из {len(all_cards)}")
                    
                    if not cards_to_process:
                        self.logger.info("⏭️ Нет новых карточек")
                        # НЕ используем continue - нужно все равно перейти на следующую страницу
                        successful_count = 0
                        failed_count = 0
                    else:
                        # 🔄 НОВЫЙ ПОДХОД: Обработка по одной карточке с retry
                        self.logger.info(f"\n🎯 НАДЕЖНАЯ ОБРАБОТКА: {len(cards_to_process)} карточек с retry механизмом")
                        
                        successful_count = 0
                        failed_count = 0
                        
                        for i, card in enumerate(cards_to_process, 1):
                            self.logger.info(f"\n📋 КАРТОЧКА {i}/{len(cards_to_process)}: {card['title']}")
                        
                            try:
                                # Открываем одну вкладку для карточки
                                self.safe_open_tab(card['url'], card['title'])
                                self.safe_switch_to_tab(1)  # Переключаемся на новую вкладку
                                
                                # Обрабатываем с retry механизмом  
                                success = self.parse_single_card_with_retry(card, 1)
                                
                                if success:
                                    successful_count += 1
                                    self.logger.info(f"✅ ИТОГО успешных: {successful_count}/{i}")
                                else:
                                    failed_count += 1
                                    self.logger.warning(f"❌ ИТОГО неудачных: {failed_count}/{i}")
                                
                                # Закрываем вкладку
                                try:
                                    self.safe_close_tab()
                                except:
                                    pass  # Вкладка могла уже закрыться при ошибке
                                
                                # Возвращаемся на главную вкладку
                                try:
                                    self.safe_switch_to_tab(0)
                                except:
                                    # Если не можем вернуться - перезапускаем драйвер
                                    self.restart_driver_bulletproof()
                                
                                # Сохраняем checkpoint после каждой карточки
                                self.save_checkpoint()
                                
                                # Человекоподобная пауза между карточками
                                if i < len(cards_to_process):
                                    pause = random.uniform(1, 3)
                                    self.logger.info(f"⏸️ Пауза {pause:.1f}s перед следующей карточкой...")
                                    time.sleep(pause)
                                    
                            except Exception as e:
                                self.logger.error(f"❌ Критическая ошибка с карточкой {card['title']}: {e}")
                                failed_count += 1
                                self.session_state['failed_urls'].add(card['url'])
                                
                                # Попытка восстановления
                                try:
                                    self.restart_driver_bulletproof()
                                except:
                                    pass
                    
                    self.logger.info(f"\n📊 ИТОГИ СТРАНИЦЫ: ✅ {successful_count} успешных, ❌ {failed_count} неудачных")
                    
                    self.logger.info(f"✅ ULTIMATE страница {page_num} обработана")
                    
                    # Переход на следующую страницу
                    if page_num < max_pages:
                        self.logger.info(f"⏭️ ULTIMATE переход на страницу {page_num + 1}...")
                        
                        # Используем метод основного парсера для навигации
                        if self.has_next_page():
                            if not self.go_to_next_page():
                                self.logger.error("❌ Не удалось перейти на следующую страницу")
                                break
                        else:
                            self.logger.info("📄 Больше страниц нет")
                            break
                        
                        time.sleep(random.uniform(2, 4))
                
                except Exception as e:
                    self.logger.error(f"❌ Критическая ошибка на странице {page_num}: {e}")
                    continue
            
            # Финальная статистика
            self.print_ultimate_stats()
            return True
            
        except Exception as e:
            self.logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА ULTIMATE ПАРСИНГА: {e}")
            self.save_checkpoint()
            return False
        
        finally:
            self.cleanup_ultimate()
    
    def print_ultimate_stats(self):
        """Финальная статистика ULTIMATE парсера"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🎉 ИТОГИ ULTIMATE ПАРСИНГА")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"✅ Успешно обработано: {self.session_state['successful_resumes']} резюме")
        self.logger.info(f"⏭️ Пропущено дубликатов: {len(self.session_state['processed_urls']) - self.session_state['successful_resumes']}")
        self.logger.info(f"❌ Неудачных попыток: {len(self.session_state['failed_urls'])}")
        self.logger.info(f"🔄 Рестартов драйвера: {self.driver_restarts}")
        self.logger.info(f"📄 Обработано страниц: {self.session_state['current_page']}")
        self.logger.info(f"💾 Checkpoint: {self.checkpoint_file}")
        self.logger.info(f"📋 ДЕТАЛЬНЫЕ ДАННЫЕ: {self.data_file} ({len(self.resume_data)} резюме)")
        self.logger.info(f"🎯 RETRY МЕХАНИЗМ: до {self.max_retries_per_card} попыток на карточку")
    
    def cleanup_ultimate(self):
        """Очистка ресурсов ULTIMATE парсера"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("🧹 ULTIMATE драйвер закрыт")
        except:
            pass

if __name__ == "__main__":
    parser = UltimateWorkUaParser()
    
    # Берем настройки из config.py
    from config import PARSING_CONFIG
    max_pages = PARSING_CONFIG.get('max_pages', 5)
    max_cards = PARSING_CONFIG.get('max_cards_per_page', 20)
    
    success = parser.ultimate_multitab_parsing(max_pages=max_pages, max_cards_per_page=max_cards)  # 🎯 НАСТРОЙКИ ИЗ CONFIG!
    
    if success:
        print("\n🎊 ULTIMATE ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
    else:
        print("\n💀 ULTIMATE ПАРСИНГ ПРЕРВАН, НО CHECKPOINT СОХРАНЕН!")