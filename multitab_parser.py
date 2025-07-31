#!/usr/bin/env python3
"""
Multi-Tab парсер Work.ua - РЕВОЛЮЦИОННЫЙ ПОДХОД
Этап 2: Открываем все резюме в новых вкладках, парсим без возврата
"""

import time
import json
from work_ua_parser import WorkUaParser
from config import PARSING_CONFIG, BROWSER_CONFIG

class MultiTabWorkUaParser:
    def __init__(self):
        self.parser = WorkUaParser()
        
        # Состояние парсера
        self.processed_urls = set()
        self.session_stats = {
            'total_processed': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'pages_processed': 0,
            'tabs_opened': 0,
            'tabs_closed': 0
        }
        
        # Результаты
        self.all_resumes = []
        
        # Главная вкладка (для навигации)
        self.main_tab_handle = None
        
    def is_already_processed(self, resume_url):
        """Проверяем, был ли URL уже обработан"""
        return resume_url in self.processed_urls
    
    def mark_as_processed(self, resume_url):
        """Отмечаем URL как обработанный"""
        self.processed_urls.add(resume_url)
        
    def get_unique_urls_on_page(self):
        """Получаем уникальные URL резюме со страницы"""
        all_cards = self.parser.find_resume_cards()
        if not all_cards:
            return []
        
        unique_urls = []
        for card in all_cards:
            card_info = self.parser.parse_card_info(card)
            if not card_info or not card_info.get('link'):
                continue
                
            resume_url = card_info['link']
            
            if not self.is_already_processed(resume_url):
                unique_urls.append({
                    'resume_url': resume_url,
                    'card_info': card_info
                })
            else:
                print(f"⏭️ Пропускаем дубликат: {card_info.get('title', 'Без названия')}")
                self.session_stats['duplicates_skipped'] += 1
        
        print(f"🎯 Уникальных URL на странице: {len(unique_urls)} из {len(all_cards)}")
        return unique_urls
    
    def open_resumes_in_tabs(self, resume_urls):
        """Открываем все резюме в новых вкладках"""
        
        print(f"🔀 Открываем {len(resume_urls)} резюме в новых вкладках...")
        
        opened_tabs = []
        
        for i, url_data in enumerate(resume_urls):
            resume_url = url_data['resume_url']
            card_info = url_data['card_info']
            
            try:
                print(f"   📂 Открываем вкладку {i+1}: {card_info.get('title', 'Без названия')}")
                
                # Открываем новую вкладку с резюме
                self.parser.driver.execute_script(f"window.open('{resume_url}', '_blank');")
                
                opened_tabs.append({
                    'url': resume_url,
                    'card_info': card_info,
                    'index': i
                })
                
                self.session_stats['tabs_opened'] += 1
                
                # Небольшая пауза между открытием вкладок
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ Ошибка открытия вкладки {i+1}: {e}")
                self.session_stats['errors'] += 1
        
        print(f"✅ Открыто {len(opened_tabs)} вкладок")
        return opened_tabs
    
    def parse_tabs_sequentially(self, opened_tabs, page_num):
        """Парсим резюме в каждой вкладке поочередно"""
        
        print(f"📋 Парсим {len(opened_tabs)} резюме в вкладках...")
        
        # Получаем все дескрипторы вкладок
        all_handles = self.parser.driver.window_handles
        main_handle = all_handles[0]  # Первая вкладка - главная
        resume_handles = all_handles[1:]  # Остальные - резюме
        
        print(f"🔍 Всего вкладок: {len(all_handles)} (1 главная + {len(resume_handles)} резюме)")
        
        for i, tab_data in enumerate(opened_tabs):
            if i >= len(resume_handles):
                print(f"⚠️ Не хватает дескрипторов вкладок для резюме {i+1}")
                break
                
            resume_url = tab_data['url']
            card_info = tab_data['card_info']
            tab_handle = resume_handles[i]
            
            print(f"\n📄 Парсим резюме {i+1}/{len(opened_tabs)}")
            print(f"   Название: {card_info.get('title', 'Без названия')}")
            print(f"   URL: {resume_url}")
            
            try:
                # Переключаемся на вкладку с резюме
                self.parser.driver.switch_to.window(tab_handle)
                
                # Ждем загрузки страницы
                print("⏳ Ждем загрузки резюме...")
                time.sleep(2)
                
                # Проверяем, что мы на правильной странице
                current_url = self.parser.driver.current_url
                if "/resumes/" not in current_url:
                    print(f"⚠️ Неожиданный URL: {current_url}")
                    self.session_stats['errors'] += 1
                    continue
                
                # Отмечаем как обработанный
                self.mark_as_processed(resume_url)
                
                # Имитируем парсинг резюме (можно заменить на реальный)
                print("🤖 Парсим резюме...")
                time.sleep(1)  # Имитация работы
                
                # Сохраняем результат
                resume_data = {
                    'url': resume_url,
                    'card_info': card_info,
                    'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'page_number': page_num,
                    'tab_index': i,
                    'status': 'success',
                    'method': 'multi_tab'
                }
                
                self.all_resumes.append(resume_data)
                self.session_stats['total_processed'] += 1
                
                print("✅ Резюме обработано успешно")
                
            except Exception as e:
                print(f"❌ Ошибка парсинга резюме {i+1}: {e}")
                self.session_stats['errors'] += 1
        
        # Возвращаемся на главную вкладку
        print(f"\n↩️ Возвращаемся на главную вкладку...")
        self.parser.driver.switch_to.window(main_handle)
        self.main_tab_handle = main_handle
        
        return True
    
    def close_resume_tabs(self):
        """Закрываем все вкладки с резюме, оставляем только главную"""
        
        print("🗂️ Закрываем вкладки с резюме...")
        
        all_handles = self.parser.driver.window_handles
        main_handle = self.main_tab_handle or all_handles[0]
        
        closed_count = 0
        for handle in all_handles:
            if handle != main_handle:
                try:
                    self.parser.driver.switch_to.window(handle)
                    self.parser.driver.close()
                    closed_count += 1
                    self.session_stats['tabs_closed'] += 1
                except Exception as e:
                    print(f"⚠️ Ошибка закрытия вкладки: {e}")
        
        # Возвращаемся на главную вкладку
        self.parser.driver.switch_to.window(main_handle)
        
        print(f"✅ Закрыто {closed_count} вкладок, остались на главной")
        return True
    
    def multitab_pagination_test(self, max_pages=3, max_cards_per_page=5):
        """Основной тест с multi-tab стратегией"""
        
        print("🚀 MULTI-TAB ПАРСЕР - ЭТАП 2: РЕВОЛЮЦИОННЫЙ ПОДХОД")
        print("=" * 80)
        print(f"Стратегия: Все резюме в новых вкладках → парсинг → закрытие → пагинация")
        print(f"Цель: {max_pages} страниц, макс {max_cards_per_page} резюме на страницу")
        print("=" * 80)
        
        try:
            # Инициализация
            if not self.parser.setup_driver():
                print("❌ Драйвер не запустился")
                return False
                
            if not self.parser.open_page():
                print("❌ Не удалось открыть страницу")
                return False
            
            # Сохраняем дескриптор главной вкладки
            self.main_tab_handle = self.parser.driver.current_window_handle
            
            # Основной цикл по страницам
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 СТРАНИЦА {page_num}")
                print("-" * 60)
                
                success = self._process_page_multitab(page_num, max_cards_per_page)
                
                if not success:
                    print(f"❌ Ошибка на странице {page_num}")
                    break
                
                self.session_stats['pages_processed'] += 1
                
                # Переход на следующую страницу (только если не последняя)
                if page_num < max_pages:
                    if not self._safe_next_page_transition(page_num):
                        print(f"❌ Не удалось перейти на страницу {page_num + 1}")
                        break
            
            # Итоги
            self._print_session_results()
            return True
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            return False
        finally:
            # Закрываем все лишние вкладки
            try:
                self.close_resume_tabs()
            except:
                pass
            self.parser.close_driver()
    
    def _process_page_multitab(self, page_num, max_cards):
        """Обработка одной страницы с multi-tab подходом"""
        
        # 1. Получаем уникальные URL на странице
        unique_urls = self.get_unique_urls_on_page()
        
        if not unique_urls:
            print(f"⚠️ Нет новых URL на странице {page_num}")
            return True
        
        # 2. Ограничиваем количество для тестирования
        urls_to_process = unique_urls[:max_cards]
        print(f"🎯 Будем обрабатывать {len(urls_to_process)} резюме")
        
        # 3. Открываем все резюме в новых вкладках
        opened_tabs = self.open_resumes_in_tabs(urls_to_process)
        
        if not opened_tabs:
            print("❌ Не удалось открыть вкладки")
            return False
        
        # 4. Парсим резюме в каждой вкладке
        parsing_success = self.parse_tabs_sequentially(opened_tabs, page_num)
        
        # 5. Закрываем вкладки с резюме
        self.close_resume_tabs()
        
        print(f"✅ Страница {page_num} обработана: {len(opened_tabs)} резюме")
        return parsing_success
    
    def _safe_next_page_transition(self, current_page):
        """Безопасный переход на следующую страницу"""
        
        print(f"\n⏭️ ПЕРЕХОД НА СТРАНИЦУ {current_page + 1}")
        print("-" * 40)
        
        # Убеждаемся, что мы на главной вкладке
        if self.main_tab_handle:
            self.parser.driver.switch_to.window(self.main_tab_handle)
        
        # Проверяем текущее состояние
        before_url = self.parser.driver.current_url
        print(f"🔗 Текущий URL: {before_url}")
        
        # Проверяем наличие следующей страницы
        if not self.parser.has_next_page():
            print("❌ Следующая страница не найдена")
            return False
        
        # Переходим на следующую страницу
        if not self.parser.go_to_next_page():
            print("❌ Переход не удался")
            return False
        
        # Проверяем результат
        after_url = self.parser.driver.current_url
        print(f"🔗 Новый URL: {after_url}")
        
        if after_url == before_url:
            print("⚠️ URL не изменился!")
            return False
        
        print("✅ Переход на следующую страницу успешен")
        return True
    
    def _print_session_results(self):
        """Выводим итоги сессии"""
        
        print(f"\n{'='*80}")
        print(f"📊 ИТОГИ MULTI-TAB ПАРСИНГА")
        print(f"{'='*80}")
        print(f"✅ Успешно обработано: {self.session_stats['total_processed']} резюме")
        print(f"⏭️ Пропущено дубликатов: {self.session_stats['duplicates_skipped']}")
        print(f"❌ Ошибок: {self.session_stats['errors']}")
        print(f"📄 Страниц обработано: {self.session_stats['pages_processed']}")
        print(f"🔀 Вкладок открыто: {self.session_stats['tabs_opened']}")
        print(f"🗂️ Вкладок закрыто: {self.session_stats['tabs_closed']}")
        print(f"🎯 Уникальных URL собрано: {len(self.processed_urls)}")
        
        if self.session_stats['total_processed'] > 0:
            success_rate = (self.session_stats['total_processed'] / 
                          (self.session_stats['total_processed'] + self.session_stats['errors'])) * 100
            print(f"📈 Успешность: {success_rate:.1f}%")
        
        print(f"\n💡 ПРЕИМУЩЕСТВА MULTI-TAB:")
        print(f"   🚫 Никаких Stale Elements")
        print(f"   🚫 Никаких PJAX проблем")
        print(f"   ⚡ Параллельная загрузка")
        print(f"   🎯 Стабильная пагинация")
        
        # Сохраняем результаты
        if self.all_resumes:
            self._save_results()
    
    def _save_results(self):
        """Сохраняем результаты в файл"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"multitab_parsing_results_{timestamp}.json"
        
        data = {
            'session_info': {
                'timestamp': timestamp,
                'version': 'multitab_strategy',
                'strategy': 'open_all_in_tabs_then_parse',
                'stats': self.session_stats,
                'total_unique_urls': len(self.processed_urls)
            },
            'processed_urls': list(self.processed_urls),
            'resumes': self.all_resumes
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Multi-tab результаты сохранены: {filename}")

def main():
    """Запуск multi-tab парсера"""
    
    parser = MultiTabWorkUaParser()
    
    print("🔧 Настройки Multi-Tab:")
    print(f"   Headless: {BROWSER_CONFIG['headless']}")
    print(f"   Страниц: 3")
    print(f"   Резюме на страницу: 5")
    print(f"   🆕 Multi-Tab стратегия: ВКЛ")
    print(f"   🎯 Никаких stale elements!")
    
    success = parser.multitab_pagination_test(max_pages=3, max_cards_per_page=5)
    
    if success:
        print(f"\n🎉 MULTI-TAB ТЕСТ ЗАВЕРШЕН!")
        print(f"🚀 Революционный подход работает!")
    else:
        print(f"\n💥 Multi-tab тест выявил проблемы")

if __name__ == "__main__":
    main()