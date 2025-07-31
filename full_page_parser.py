"""
Полный парсер одной страницы Work.ua с сохранением в базу данных
"""

import os
import time
from work_ua_parser import WorkUaParser
from database_manager import ResumeDatabase

def process_full_page():
    """Полная обработка одной страницы с LLM парсингом и сохранением в БД"""
    
    # Проверяем API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Установите переменную окружения OPENAI_API_KEY")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    print("🚀 ПОЛНАЯ ОБРАБОТКА СТРАНИЦЫ С LLM + БАЗА ДАННЫХ")
    print("=" * 70)
    
    # Инициализация
    parser = WorkUaParser()
    db = ResumeDatabase("work_ua_resumes.db")
    
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    
    try:
        # Инициализируем драйвер
        print("🔧 Инициализация браузера...")
        if not parser.setup_driver():
            print("❌ Ошибка инициализации драйвера")
            return False
        
        # Открываем страницу
        print("🌐 Открытие страницы work.ua...")
        if not parser.open_page():
            print("❌ Ошибка открытия страницы")
            return False
        
        # Находим все карточки
        print("🔍 Поиск карточек резюме...")
        cards = parser.find_resume_cards()
        if not cards:
            print("❌ Карточки не найдены")
            return False
        
        total_cards = len(cards)
        print(f"✅ Найдено {total_cards} карточек резюме")
        print("=" * 70)
        
        # Обрабатываем каждую карточку
        for i in range(total_cards):
            print(f"\n📄 РЕЗЮМЕ {i+1}/{total_cards}")
            print("-" * 50)
            
            try:
                # Находим текущие карточки (обновляем список для избежания stale elements)
                current_cards = parser.find_resume_cards()
                if i >= len(current_cards):
                    print(f"⚠️ Карточка {i+1} больше недоступна")
                    skipped_count += 1
                    continue
                
                current_card = current_cards[i]
                
                # Извлекаем базовую информацию с карточки
                card_info = parser.parse_card_info(current_card)
                resume_url = card_info.get('link', '')
                
                if not resume_url:
                    print(f"⚠️ URL резюме не найден в карточке {i+1}")
                    skipped_count += 1
                    continue
                
                print(f"🔗 URL: {resume_url}")
                print(f"📋 Заголовок: {card_info.get('title', 'Не указан')}")
                
                # Проверяем, есть ли уже в базе
                if db.resume_exists(resume_url):
                    print(f"ℹ️ Резюме уже в базе, пропускаем...")
                    skipped_count += 1
                    continue
                
                # Переходим в резюме
                print("👆 Переход в детальное резюме...")
                if not parser.click_card(current_card):
                    print(f"❌ Не удалось перейти в резюме {i+1}")
                    failed_count += 1
                    continue
                
                print("✅ Перешли в резюме")
                
                # Извлекаем детальную информацию с помощью LLM
                print("🤖 Извлечение данных через LLM...")
                start_time = time.time()
                
                llm_details = parser.parse_resume_with_llm()
                
                llm_time = time.time() - start_time
                
                if llm_details:
                    print(f"🎉 LLM успешно извлек данные за {llm_time:.1f}с")
                    
                    # Объединяем карточку и LLM данные
                    full_resume_data = {
                        'card_info': card_info,
                        'llm_details': llm_details,
                        'processing_info': {
                            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'llm_processing_time': round(llm_time, 2),
                            'method': 'LLM_OpenAI_GPT35'
                        }
                    }
                    
                    # Сохраняем в базу данных
                    print("💾 Сохранение в базу данных...")
                    if db.save_resume(resume_url, full_resume_data):
                        print("✅ Сохранено в базу")
                        processed_count += 1
                        
                        # Краткая информация
                        name = llm_details.get('full_name', 'Не указано')
                        position = llm_details.get('position', 'Не указано')
                        print(f"👤 {name} - {position}")
                        
                    else:
                        print("❌ Ошибка сохранения в базу")
                        failed_count += 1
                else:
                    print("❌ LLM не смог извлечь данные")
                    failed_count += 1
                
                # Возвращаемся к списку
                print("🔙 Возврат к списку...")
                if parser.go_back():
                    print("✅ Вернулись к списку")
                    # Небольшая пауза для стабильности
                    time.sleep(1)
                else:
                    print("⚠️ Проблема с возвратом к списку")
                    # Переоткрываем страницу
                    print("🔄 Переоткрытие страницы...")
                    if not parser.open_page():
                        print("❌ Не удалось переоткрыть страницу")
                        break
                
            except Exception as e:
                print(f"❌ Ошибка обработки резюме {i+1}: {e}")
                failed_count += 1
                
                # Пытаемся вернуться к списку
                try:
                    parser.go_back()
                except:
                    parser.open_page()
        
        # Финальная статистика
        print(f"\n{'='*70}")
        print(f"🎯 ИТОГИ ПОЛНОЙ ОБРАБОТКИ СТРАНИЦЫ")
        print(f"{'='*70}")
        print(f"✅ Успешно обработано: {processed_count} резюме")
        print(f"❌ Ошибки обработки: {failed_count} резюме")
        print(f"⏭️ Пропущено: {skipped_count} резюме")
        print(f"📊 Всего найдено: {total_cards} резюме")
        
        # Статистика базы данных
        db_stats = db.get_stats()
        print(f"\n💾 СТАТИСТИКА БАЗЫ ДАННЫХ:")
        print(f"   📈 Всего резюме в базе: {db_stats.get('total_resumes', 0)}")
        print(f"   💿 Размер базы: {db_stats.get('database_size_mb', 0)} MB")
        print(f"   🕐 Последнее обновление: {db_stats.get('last_update', 'Неизвестно')}")
        
        # Экспорт в JSON
        if processed_count > 0:
            print(f"\n📄 Экспорт результатов...")
            export_file = db.export_to_json()
            if export_file:
                print(f"✅ Данные экспортированы в: {export_file}")
        
        return processed_count > 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False
        
    finally:
        print(f"\n🔒 Закрытие браузера...")
        parser.close_driver()

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ПОЛНОГО ПАРСЕРА WORK.UA")
    print("=" * 70)
    
    success = process_full_page()
    
    if success:
        print(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"💾 Данные сохранены в базу: work_ua_resumes.db")
        print(f"📄 JSON экспорт также создан")
    else:
        print(f"\n❌ Парсинг завершился с ошибками")
    
    print(f"\n🔗 Для просмотра данных используйте:")
    print(f"   python -c \"from database_manager import ResumeDatabase; db=ResumeDatabase('work_ua_resumes.db'); print(db.get_stats())\"")

if __name__ == "__main__":
    main() 