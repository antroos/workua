"""
Тестирование всех инкрементов Work.ua Parser
Проверяем каждый шаг отдельно
"""

from work_ua_parser import WorkUaParser
import time

def test_increment_2_driver_setup():
    """Тест инкремента 2: Настройка драйвера"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ ИНКРЕМЕНТА 2: Настройка WebDriver")
    print("="*60)
    
    parser = WorkUaParser()
    
    if parser.setup_driver():
        print("✅ Драйвер успешно инициализирован")
        parser.close_driver()
        return True
    else:
        print("❌ Ошибка инициализации драйвера")
        return False

def test_increment_3_page_opening():
    """Тест инкремента 3: Открытие страницы"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ ИНКРЕМЕНТА 3: Открытие страницы work.ua")
    print("="*60)
    
    parser = WorkUaParser()
    
    if parser.setup_driver():
        if parser.open_page():
            print("✅ Страница успешно открыта и проверена")
            parser.close_driver()
            return True
        else:
            print("❌ Ошибка открытия страницы")
            parser.close_driver()
            return False
    else:
        print("❌ Ошибка инициализации драйвера")
        return False

def test_increment_4_cards_detection():
    """Тест инкремента 4: Поиск карточек"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ ИНКРЕМЕНТА 4: Поиск карточек резюме")
    print("="*60)
    
    parser = WorkUaParser()
    
    if parser.setup_driver() and parser.open_page():
        cards = parser.find_resume_cards()
        if cards and len(cards) > 0:
            print(f"✅ Найдено {len(cards)} карточек")
            print("📋 Первые 3 карточки:")
            for i in range(min(3, len(cards))):
                try:
                    title_elem = cards[i].find_element("css selector", "h2 a")
                    print(f"   {i+1}. {title_elem.text.strip()}")
                except:
                    print(f"   {i+1}. [Не удалось получить заголовок]")
            parser.close_driver()
            return True
        else:
            print("❌ Карточки не найдены")
            parser.close_driver()
            return False
    else:
        print("❌ Ошибка настройки или открытия страницы")
        return False

def test_increment_5_card_parsing():
    """Тест инкремента 5: Парсинг карточки"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ ИНКРЕМЕНТА 5: Парсинг информации из карточки")
    print("="*60)
    
    parser = WorkUaParser()
    
    if parser.setup_driver() and parser.open_page():
        cards = parser.find_resume_cards()
        if cards and len(cards) > 0:
            card_info = parser.parse_card_info(cards[0])
            if card_info:
                print("✅ Информация из карточки извлечена:")
                print(f"   Заголовок: {card_info['title']}")
                print(f"   Имя: {card_info['name']}")
                print(f"   Зарплата: {card_info['salary']}")
                print(f"   Ссылка: {card_info['link']}")
                parser.close_driver()
                return True
            else:
                print("❌ Не удалось извлечь информацию из карточки")
                parser.close_driver()
                return False
        else:
            print("❌ Карточки не найдены")
            parser.close_driver()
            return False
    else:
        print("❌ Ошибка настройки")
        return False

def test_increment_6_7_navigation():
    """Тест инкрементов 6-7: Переход в карточку и возврат"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ ИНКРЕМЕНТОВ 6-7: Переход в карточку и возврат")
    print("="*60)
    
    parser = WorkUaParser()
    
    if parser.setup_driver() and parser.open_page():
        cards = parser.find_resume_cards()
        if cards and len(cards) > 0:
            print("🔗 Переходим в первую карточку...")
            if parser.click_card(cards[0]):
                print("✅ Успешно перешли в резюме")
                time.sleep(2)
                
                if parser.go_back():
                    print("✅ Успешно вернулись назад")
                    parser.close_driver()
                    return True
                else:
                    print("❌ Не удалось вернуться назад")
                    parser.close_driver()
                    return False
            else:
                print("❌ Не удалось перейти в карточку")
                parser.close_driver()
                return False
        else:
            print("❌ Карточки не найдены")
            parser.close_driver()
            return False
    else:
        print("❌ Ошибка настройки")
        return False

def test_increment_8_detailed_parsing():
    """Тест инкремента 8: Детальный парсинг резюме"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ ИНКРЕМЕНТА 8: Детальный парсинг резюме")
    print("="*60)
    
    parser = WorkUaParser()
    
    if parser.setup_driver() and parser.open_page():
        cards = parser.find_resume_cards()
        if cards and len(cards) > 0:
            if parser.click_card(cards[0]):
                details = parser.parse_resume_details()
                if details:
                    print("✅ Детальная информация извлечена:")
                    print(f"   Полное название: {details['full_title']}")
                    print(f"   Полное имя: {details['full_name']}")
                    print(f"   Навыки: {details['skills'][:1]}")
                    print(f"   Образование: {details['education'][:1]}")
                    
                    parser.go_back()
                    parser.close_driver()
                    return True
                else:
                    print("❌ Не удалось извлечь детальную информацию")
                    parser.close_driver()
                    return False
            else:
                print("❌ Не удалось перейти в карточку")
                parser.close_driver()
                return False
        else:
            print("❌ Карточки не найдены")
            parser.close_driver()
            return False
    else:
        print("❌ Ошибка настройки")
        return False

def main():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ВСЕХ ИНКРЕМЕНТОВ")
    print("⏱️ Каждый тест займет 10-15 секунд")
    
    tests = [
        ("Инкремент 2", test_increment_2_driver_setup),
        ("Инкремент 3", test_increment_3_page_opening),
        ("Инкремент 4", test_increment_4_cards_detection),
        ("Инкремент 5", test_increment_5_card_parsing),
        ("Инкременты 6-7", test_increment_6_7_navigation),
        ("Инкремент 8", test_increment_8_detailed_parsing),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            time.sleep(1)  # Пауза между тестами
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"📈 РЕЗУЛЬТАТ: {passed}/{total} тестов прошло ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ВСЕ ИНКРЕМЕНТЫ РАБОТАЮТ ОТЛИЧНО!")
    elif passed >= total * 0.8:
        print("👍 БОЛЬШИНСТВО ИНКРЕМЕНТОВ РАБОТАЕТ ХОРОШО!")
    else:
        print("⚠️ НЕКОТОРЫЕ ИНКРЕМЕНТЫ ТРЕБУЮТ ВНИМАНИЯ")
    
    print("="*60)

if __name__ == "__main__":
    main() 