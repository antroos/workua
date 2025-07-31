#!/usr/bin/env python3
"""
Stealth парсер Work.ua - ANTI-DETECTION
Этап 2.5: Multi-tab + защита от блокировок + человекоподобное поведение
"""

import time
import json
import random
from work_ua_parser import WorkUaParser
from config import PARSING_CONFIG, BROWSER_CONFIG

class StealthWorkUaParser:
    def __init__(self):
        self.parser = WorkUaParser()
        
        # Anti-detection настройки
        self.human_delays = True
        self.max_tabs_at_once = 3  # Не более 3 вкладок одновременно
        self.page_delay_range = (2, 5)  # Случайные задержки
        self.tab_delay_range = (1, 3)
        
        # Состояние парсера
        self.processed_urls = set()
        self.session_stats = {
            'total_processed': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'pages_processed': 0,
            'tabs_opened': 0,
            'tabs_closed': 0,
            'blocks_detected': 0
        }
        
        # Результаты
        self.all_resumes = []
        self.main_tab_handle = None
        
    def human_delay(self, delay_range=None):
        """Человекоподобная задержка"""
        if not self.human_delays:
            return
            
        if delay_range is None:
            delay_range = self.page_delay_range
            
        delay = random.uniform(delay_range[0], delay_range[1])
        print(f"⏱️ Человекоподобная пауза {delay:.1f}s...")
        time.sleep(delay)
    
    def check_if_blocked(self):
        """Проверяем, заблокированы ли мы"""
        try:
            current_url = self.parser.driver.current_url
            page_title = self.parser.driver.title.lower()
            
            # Признаки блокировки
            block_indicators = [
                'blocked', 'banned', 'access denied', 'cloudflare',
                'too many requests', 'rate limit', 'captcha'
            ]
            
            for indicator in block_indicators:
                if indicator in current_url.lower() or indicator in page_title:
                    print(f"🚫 Обнаружена блокировка: {indicator}")
                    self.session_stats['blocks_detected'] += 1
                    return True
                    
            # Проверяем наличие базовых элементов work.ua
            try:
                cards = self.parser.find_resume_cards()
                if len(cards) == 0 and "work.ua" in current_url:
                    print("🚫 Подозрение на блокировку: нет карточек")
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка проверки блокировки: {e}")
            return True
    
    def get_unique_urls_on_page(self):
        """Получаем уникальные URL со страницы с проверкой блокировки"""
        
        # Проверяем блокировку
        if self.check_if_blocked():
            print("❌ Страница заблокирована, прерываем")
            return []
        
        all_cards = self.parser.find_resume_cards()
        if not all_cards:
            print("⚠️ Карточки не найдены (возможна блокировка)")
            return []
        
        unique_urls = []
        for card in all_cards:
            card_info = self.parser.parse_card_info(card)
            if not card_info or not card_info.get('link'):
                continue
                
            resume_url = card_info['link']
            
            if resume_url not in self.processed_urls:
                unique_urls.append({
                    'resume_url': resume_url,
                    'card_info': card_info
                })
            else:
                print(f"⏭️ Пропускаем дубликат: {card_info.get('title', 'Без названия')}")
                self.session_stats['duplicates_skipped'] += 1
        
        print(f"🎯 Уникальных URL: {len(unique_urls)} из {len(all_cards)}")
        return unique_urls
    
    def safe_open_tabs_batch(self, resume_urls, batch_size=None):
        """Безопасное открытие вкладок небольшими партиями"""
        
        if batch_size is None:
            batch_size = self.max_tabs_at_once
            
        print(f"🔀 Открываем {len(resume_urls)} резюме партиями по {batch_size}...")
        
        all_opened_tabs = []
        
        for i in range(0, len(resume_urls), batch_size):
            batch = resume_urls[i:i + batch_size]
            print(f"\n📦 Партия {i//batch_size + 1}: {len(batch)} резюме")
            
            batch_tabs = []
            for j, url_data in enumerate(batch):
                resume_url = url_data['resume_url']
                card_info = url_data['card_info']
                
                try:
                    print(f"   📂 Открываем: {card_info.get('title', 'Без названия')}")
                    
                    # Человекоподобная задержка между вкладками
                    if j > 0:
                        self.human_delay(self.tab_delay_range)
                    
                    # Открываем вкладку
                    self.parser.driver.execute_script(f"window.open('{resume_url}', '_blank');")
                    
                    batch_tabs.append({
                        'url': resume_url,
                        'card_info': card_info,
                        'batch_index': i//batch_size,
                        'tab_index': j
                    })
                    
                    self.session_stats['tabs_opened'] += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка открытия вкладки: {e}")
                    self.session_stats['errors'] += 1
            
            # Парсим текущую партию
            if batch_tabs:
                self._parse_batch_tabs(batch_tabs, i//batch_size + 1)
                all_opened_tabs.extend(batch_tabs)
            
            # Пауза между партиями
            if i + batch_size < len(resume_urls):
                print(f"⏸️ Пауза между партиями...")
                self.human_delay((3, 6))
        
        return all_opened_tabs
    
    def _parse_batch_tabs(self, batch_tabs, batch_num):
        """Парсим одну партию вкладок"""
        
        print(f"📋 Парсим партию {batch_num}: {len(batch_tabs)} вкладок...")
        
        # Получаем дескрипторы вкладок
        all_handles = self.parser.driver.window_handles
        main_handle = all_handles[0]
        
        for i, tab_data in enumerate(batch_tabs):
            resume_url = tab_data['url']
            card_info = tab_data['card_info']
            
            # Находим соответствующий дескриптор
            tab_handle_index = i + 1  # +1 потому что 0 - главная вкладка
            if tab_handle_index >= len(all_handles):
                print(f"⚠️ Не хватает дескрипторов для вкладки {i+1}")
                continue
                
            tab_handle = all_handles[tab_handle_index]
            
            print(f"\n📄 Парсим {i+1}/{len(batch_tabs)}: {card_info.get('title', 'Без названия')}")
            
            try:
                # Переключаемся на вкладку
                self.parser.driver.switch_to.window(tab_handle)
                
                # Ждем загрузки
                print("⏳ Ждем загрузки...")
                self.human_delay((1, 2))
                
                # Проверяем блокировку
                if self.check_if_blocked():
                    print("🚫 Вкладка заблокирована")
                    continue
                
                # Проверяем URL
                current_url = self.parser.driver.current_url
                if "/resumes/" not in current_url:
                    print(f"⚠️ Неожиданный URL: {current_url}")
                    continue
                
                # Отмечаем как обработанный
                self.processed_urls.add(resume_url)
                
                # Имитируем человекоподобный парсинг
                print("🤖 Парсим резюме...")
                self.human_delay((0.5, 1.5))
                
                # Сохраняем результат
                resume_data = {
                    'url': resume_url,
                    'card_info': card_info,
                    'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'batch_number': batch_num,
                    'status': 'success',
                    'method': 'stealth_multitab'
                }
                
                self.all_resumes.append(resume_data)
                self.session_stats['total_processed'] += 1
                
                print("✅ Резюме обработано")
                
            except Exception as e:
                print(f"❌ Ошибка парсинга: {e}")
                self.session_stats['errors'] += 1
        
        # Закрываем вкладки партии
        self._close_batch_tabs(main_handle)
        
        # Возвращаемся на главную
        self.parser.driver.switch_to.window(main_handle)
        self.main_tab_handle = main_handle
    
    def _close_batch_tabs(self, main_handle):
        """Закрываем вкладки текущей партии"""
        
        all_handles = self.parser.driver.window_handles
        
        for handle in all_handles:
            if handle != main_handle:
                try:
                    self.parser.driver.switch_to.window(handle)
                    self.parser.driver.close()
                    self.session_stats['tabs_closed'] += 1
                except Exception as e:
                    print(f"⚠️ Ошибка закрытия: {e}")
    
    def stealth_pagination_test(self, max_pages=3, max_cards_per_page=6):
        """Основной stealth тест"""
        
        print("🥷 STEALTH ПАРСЕР - ANTI-DETECTION + MULTI-TAB")
        print("=" * 80)
        print(f"🛡️ Защита: Человекоподобные задержки + малые партии вкладок")
        print(f"🎯 Цель: {max_pages} страниц, макс {max_cards_per_page} резюме на страницу")
        print(f"📦 Партии: {self.max_tabs_at_once} вкладок за раз")
        print("=" * 80)
        
        try:
            # Инициализация
            if not self.parser.setup_driver():
                print("❌ Драйвер не запустился")
                return False
            
            # Человекоподобное открытие страницы
            print("🌐 Открываем work.ua...")
            if not self.parser.open_page():
                print("❌ Не удалось открыть страницу")
                return False
            
            self.main_tab_handle = self.parser.driver.current_window_handle
            self.human_delay()
            
            # Основной цикл
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 СТРАНИЦА {page_num}")
                print("-" * 60)
                
                # Проверяем блокировку в начале страницы
                if self.check_if_blocked():
                    print("🚫 Страница заблокирована, прерываем парсинг")
                    break
                
                success = self._process_page_stealth(page_num, max_cards_per_page)
                
                if not success:
                    print(f"❌ Ошибка на странице {page_num}")
                    break
                
                self.session_stats['pages_processed'] += 1
                
                # Переход на следующую страницу
                if page_num < max_pages:
                    print(f"\n⏭️ Переходим на страницу {page_num + 1}...")
                    self.human_delay()
                    
                    if not self.parser.has_next_page():
                        print("📄 Больше страниц нет")
                        break
                        
                    if not self.parser.go_to_next_page():
                        print("❌ Не удалось перейти на следующую страницу")
                        break
                        
                    self.human_delay()
            
            # Итоги
            self._print_stealth_results()
            return True
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            return False
        finally:
            try:
                # Закрываем все вкладки
                if self.main_tab_handle:
                    all_handles = self.parser.driver.window_handles
                    for handle in all_handles:
                        if handle != self.main_tab_handle:
                            try:
                                self.parser.driver.switch_to.window(handle)
                                self.parser.driver.close()
                            except:
                                pass
                    self.parser.driver.switch_to.window(self.main_tab_handle)
            except:
                pass
            self.parser.close_driver()
    
    def _process_page_stealth(self, page_num, max_cards):
        """Обработка страницы с stealth подходом"""
        
        # Получаем URL
        unique_urls = self.get_unique_urls_on_page()
        
        if not unique_urls:
            print(f"⚠️ Нет новых URL на странице {page_num}")
            return True
        
        # Ограничиваем количество
        urls_to_process = unique_urls[:max_cards]
        print(f"🎯 Обрабатываем {len(urls_to_process)} резюме стелс-методом")
        
        # Обрабатываем партиями
        self.safe_open_tabs_batch(urls_to_process)
        
        print(f"✅ Страница {page_num} обработана стелс-методом")
        return True
    
    def _print_stealth_results(self):
        """Итоги stealth парсинга"""
        
        print(f"\n{'='*80}")
        print(f"🥷 ИТОГИ STEALTH ПАРСИНГА")
        print(f"{'='*80}")
        print(f"✅ Успешно обработано: {self.session_stats['total_processed']} резюме")
        print(f"⏭️ Пропущено дубликатов: {self.session_stats['duplicates_skipped']}")
        print(f"❌ Ошибок: {self.session_stats['errors']}")
        print(f"🚫 Блокировок обнаружено: {self.session_stats['blocks_detected']}")
        print(f"📄 Страниц обработано: {self.session_stats['pages_processed']}")
        print(f"🔀 Вкладок открыто: {self.session_stats['tabs_opened']}")
        print(f"🗂️ Вкладок закрыто: {self.session_stats['tabs_closed']}")
        
        if self.session_stats['total_processed'] > 0:
            success_rate = (self.session_stats['total_processed'] / 
                          (self.session_stats['total_processed'] + self.session_stats['errors'])) * 100
            print(f"📈 Успешность: {success_rate:.1f}%")
        
        # Сохраняем результаты
        if self.all_resumes:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"stealth_parsing_results_{timestamp}.json"
            
            data = {
                'session_info': {
                    'timestamp': timestamp,
                    'version': 'stealth_multitab_anti_detection',
                    'stats': self.session_stats,
                    'anti_detection_enabled': True
                },
                'processed_urls': list(self.processed_urls),
                'resumes': self.all_resumes
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Stealth результаты сохранены: {filename}")

def main():
    """Запуск stealth парсера"""
    
    parser = StealthWorkUaParser()
    
    print("🥷 Настройки Stealth:")
    print(f"   Человекоподобные задержки: ДА")
    print(f"   Макс вкладок за раз: {parser.max_tabs_at_once}")
    print(f"   Защита от блокировок: ДА")
    print(f"   Партии вместо массового открытия: ДА")
    
    success = parser.stealth_pagination_test(max_pages=2, max_cards_per_page=4)
    
    if success:
        print(f"\n🎉 STEALTH ТЕСТ ЗАВЕРШЕН!")
        print(f"🥷 Никто не заметил!")
    else:
        print(f"\n💥 Stealth тест выявил проблемы")

if __name__ == "__main__":
    main()