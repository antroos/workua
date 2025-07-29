"""
Тест LLM парсинга резюме
"""

import os
from work_ua_parser import WorkUaParser

def test_llm_parsing():
    """Тест парсинга одного резюме с помощью LLM"""
    
    # Проверяем API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Установите переменную окружения OPENAI_API_KEY")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    print("🚀 ТЕСТ LLM ПАРСИНГА")
    print("=" * 50)
    
    parser = WorkUaParser()
    
    try:
        # Инициализируем драйвер
        if not parser.setup_driver():
            print("❌ Ошибка инициализации драйвера")
            return False
            
        # Открываем страницу
        if not parser.open_page():
            print("❌ Ошибка открытия страницы")
            return False
            
        # Находим карточки
        cards = parser.find_resume_cards()
        if not cards:
            print("❌ Карточки не найдены")
            return False
            
        print(f"✅ Найдено {len(cards)} карточек")
        
        # Переходим в первую карточку
        if not parser.click_card(cards[0]):
            print("❌ Не удалось перейти в карточку")
            return False
            
        print("✅ Перешли в резюме")
        
        # ТЕСТИРУЕМ LLM ПАРСИНГ
        print("\n🤖 ТЕСТИРУЕМ LLM ПАРСИНГ...")
        llm_result = parser.parse_resume_with_llm()
        
        if llm_result:
            print("🎉 LLM ПАРСИНГ УСПЕШЕН!")
            print("=" * 50)
            print("📊 ИЗВЛЕЧЕННАЯ ИНФОРМАЦИЯ:")
            print("=" * 50)
            
            for key, value in llm_result.items():
                if isinstance(value, list):
                    # Преобразуем все элементы в строки перед склеиванием
                    value_strings = [str(item) for item in value]
                    print(f"{key}: {', '.join(value_strings)}")
                else:
                    print(f"{key}: {value}")
                    
            print("=" * 50)
            return True
        else:
            print("❌ LLM парсинг не удался")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        parser.close_driver()

if __name__ == "__main__":
    test_llm_parsing() 