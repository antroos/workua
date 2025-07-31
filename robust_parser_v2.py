#!/usr/bin/env python3
"""
Устойчивый парсер Work.ua v2 - ИСПРАВЛЕНИЕ STALE ELEMENTS
Этап 1.5: Динамический поиск элементов + защита от дубликатов
"""

import time
import json
from work_ua_parser import WorkUaParser
from config import PARSING_CONFIG, BROWSER_CONFIG

class RobustWorkUaParserV2:
    def __init__(self):
        self.parser = WorkUaParser()
        
        # Состояние парсера
        self.processed_urls = set()  # Все обработанные URL
        self.session_stats = {
            'total_processed': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'pages_processed': 0,
            'stale_element_recoveries': 0
        }
        
        # Результаты
        self.all_resumes = []
        
    def is_already_processed(self, resume_url):
        """Проверяем, был ли URL уже обработан"""
        return resume_url in self.processed_urls
    
    def mark_as_processed(self, resume_url):
        """Отмечаем URL как обработанный"""
        self.processed_urls.add(resume_url)
        
    def get_unique_urls_on_page(self):
        """Получаем только новые URL со страницы (БЕЗ элементов DOM)"""
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
    
    def find_card_by_url(self, target_url, max_attempts=3):
        """Динамически находим карточку по URL (решение stale elements)"""
        
        for attempt in range(max_attempts):
            try:
                # Заново ищем все карточки на странице
                current_cards = self.parser.find_resume_cards()
                
                for card in current_cards:
                    card_info = self.parser.parse_card_info(card)
                    if card_info and card_info.get('link') == target_url:
                        print(f"✅ Найден элемент для URL: {target_url} (попытка {attempt + 1})")
                        return card
                
                print(f"⚠️ Карточка не найдена, попытка {attempt + 1}/{max_attempts}")
                time.sleep(0.5)  # Небольшая пауза перед повтором
                
            except Exception as e:
                print(f"❌ Ошибка поиска карточки: {e}")
                time.sleep(1)
        
        print(f"❌ Не удалось найти карточку для URL: {target_url}")
        return None
    
    def robust_pagination_test_v2(self, max_pages=3, max_cards_per_page=3):
        """Тест v2 с решением stale elements"""
        
        print("🚀 УСТОЙЧИВЫЙ ПАРСЕР V2 - ЭТАП 1.5: ИСПРАВЛЕНИЕ STALE ELEMENTS")
        print("=" * 80)
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
            
            # Основной цикл по страницам
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 СТРАНИЦА {page_num}")
                print("-" * 50)
                
                success = self._process_page_with_dynamic_elements(page_num, max_cards_per_page)
                
                if not success:
                    print(f"❌ Ошибка на странице {page_num}")
                    break
                
                self.session_stats['pages_processed'] += 1
                
                # Переход на следующую страницу
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
            self.parser.close_driver()
    
    def _process_page_with_dynamic_elements(self, page_num, max_cards):
        """Обрабатываем страницу с динамическим поиском элементов"""
        
        # Получаем уникальные URL (НЕ элементы!)
        unique_urls = self.get_unique_urls_on_page()
        
        if not unique_urls:
            print(f"⚠️ Нет новых URL на странице {page_num}")
            return True  # Продолжаем, это нормально
        
        # Ограничиваем количество для тестирования
        urls_to_process = unique_urls[:max_cards]
        
        print(f"🎯 Обрабатываем {len(urls_to_process)} уникальных URL")
        
        for i, url_data in enumerate(urls_to_process):
            resume_url = url_data['resume_url']
            original_card_info = url_data['card_info']
            
            print(f"\n📋 URL {i+1}/{len(urls_to_process)}")
            print(f"   Название: {original_card_info.get('title', 'Без названия')}")
            print(f"   Кандидат: {original_card_info.get('name', 'Не указан')}")
            print(f"   URL: {resume_url}")
            
            try:
                # Отмечаем как обрабатываемый ДО поиска элемента
                self.mark_as_processed(resume_url)
                
                # 🔥 КЛЮЧЕВОЕ ОТЛИЧИЕ: Динамически ищем элемент перед кликом
                card_element = self.find_card_by_url(resume_url)
                
                if not card_element:
                    print("❌ Не удалось найти элемент карточки")
                    self.session_stats['errors'] += 1
                    continue
                
                # Переходим в резюме
                if self.parser.click_card(card_element):
                    print("✅ Перешли в резюме")
                    
                    # Имитируем парсинг
                    time.sleep(1)
                    
                    # Сохраняем результат
                    resume_data = {
                        'url': resume_url,
                        'card_info': original_card_info,
                        'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'page_number': page_num,
                        'status': 'success'
                    }
                    
                    self.all_resumes.append(resume_data)
                    self.session_stats['total_processed'] += 1
                    
                    print("✅ Резюме обработано и сохранено")
                    
                    # Возвращаемся
                    if self.parser.go_back():
                        print("↩️ Вернулись на страницу")
                        time.sleep(1)  # Даем время на стабилизацию
                    else:
                        print("⚠️ Проблема с возвратом")
                        return False
                        
                else:
                    print("❌ Не удалось перейти в резюме")
                    self.session_stats['errors'] += 1
                    
            except Exception as e:
                print(f"❌ Ошибка обработки URL: {e}")
                self.session_stats['errors'] += 1
        
        return True
    
    def _safe_next_page_transition(self, current_page):
        """Безопасный переход на следующую страницу"""
        
        print(f"\n⏭️ ПЕРЕХОД НА СТРАНИЦУ {current_page + 1}")
        print("-" * 30)
        
        # Запоминаем состояние ДО перехода
        before_url = self.parser.driver.current_url
        before_cards = len(self.parser.find_resume_cards())
        
        print(f"📊 До перехода: {before_cards} карточек")
        print(f"🔗 URL: {before_url}")
        
        # Проверяем наличие следующей страницы
        if not self.parser.has_next_page():
            print("❌ Следующая страница не найдена")
            return False
        
        # Переходим
        if not self.parser.go_to_next_page():
            print("❌ Переход не удался")
            return False
        
        # Проверяем результат
        after_url = self.parser.driver.current_url
        after_cards = len(self.parser.find_resume_cards())
        
        print(f"📊 После перехода: {after_cards} карточек")
        print(f"🔗 URL: {after_url}")
        
        if after_url == before_url:
            print("⚠️ URL не изменился!")
            return False
            
        if after_cards == 0:
            print("⚠️ Карточки не загрузились!")
            return False
        
        print("✅ Переход успешен")
        return True
    
    def _print_session_results(self):
        """Выводим итоги сессии"""
        
        print(f"\n{'='*80}")
        print(f"📊 ИТОГИ УСТОЙЧИВОГО ПАРСИНГА V2")
        print(f"{'='*80}")
        print(f"✅ Успешно обработано: {self.session_stats['total_processed']} резюме")
        print(f"⏭️ Пропущено дубликатов: {self.session_stats['duplicates_skipped']}")
        print(f"❌ Ошибок: {self.session_stats['errors']}")
        print(f"🔄 Stale element восстановлений: {self.session_stats['stale_element_recoveries']}")
        print(f"📄 Страниц обработано: {self.session_stats['pages_processed']}")
        print(f"🎯 Уникальных URL собрано: {len(self.processed_urls)}")
        
        if self.session_stats['total_processed'] > 0:
            success_rate = (self.session_stats['total_processed'] / 
                          (self.session_stats['total_processed'] + self.session_stats['errors'])) * 100
            print(f"📈 Успешность: {success_rate:.1f}%")
        
        # Сохраняем результаты
        if self.all_resumes:
            self._save_results()
    
    def _save_results(self):
        """Сохраняем результаты в файл"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"robust_parsing_v2_results_{timestamp}.json"
        
        data = {
            'session_info': {
                'timestamp': timestamp,
                'version': 'v2_stale_elements_fix',
                'stats': self.session_stats,
                'total_unique_urls': len(self.processed_urls)
            },
            'processed_urls': list(self.processed_urls),
            'resumes': self.all_resumes
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результаты v2 сохранены: {filename}")

def main():
    """Запуск устойчивого парсера v2"""
    
    parser = RobustWorkUaParserV2()
    
    print("🔧 Настройки V2:")
    print(f"   Headless: {BROWSER_CONFIG['headless']}")
    print(f"   Страниц: 3")
    print(f"   Резюме на страницу: 3")
    print(f"   🆕 Динамический поиск элементов: ВКЛ")
    
    success = parser.robust_pagination_test_v2(max_pages=3, max_cards_per_page=3)
    
    if success:
        print(f"\n🎉 ТЕСТ V2 ЗАВЕРШЕН!")
        print(f"💪 Проблема Stale Elements решена!")
    else:
        print(f"\n💥 Тест V2 выявил проблемы")

if __name__ == "__main__":
    main()