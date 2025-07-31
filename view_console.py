#!/usr/bin/env python3
"""
Консольный просмотр базы данных резюме
"""

import json
import os
from datetime import datetime
from collections import Counter

def load_database():
    """Загрузка данных из JSON файла"""
    try:
        with open('база_резюме_полная.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ Файл база_резюме_полная.json не найден")
        return []
    except json.JSONDecodeError:
        print("❌ Ошибка чтения JSON файла")
        return []

def format_resume(resume_data, index):
    """Форматирование резюме для вывода"""
    detailed = resume_data.get('resume_data', {}).get('detailed_info', {})
    card = resume_data.get('resume_data', {}).get('card_info', {})
    
    name = detailed.get('full_name', 'Не указано')
    position = detailed.get('position', card.get('title', 'Не указано'))
    salary = detailed.get('salary', 'Не указана')
    location = detailed.get('location', 'Не указан')
    age = detailed.get('age', 'Не указан')
    skills = detailed.get('skills', [])
    experience = detailed.get('experience', [])
    url = resume_data.get('resume_url', '#')
    
    # Форматируем вывод
    result = f"""
{index}. 👤 {name}
   💼 Должность: {position}
   💰 Зарплата: {salary}
   📍 Город: {location} | 🎂 Возраст: {age} лет
   🔧 Навыки: {' | '.join(skills[:4])}{'...' if len(skills) > 4 else ''}
   📋 Опыт: {len(experience)} позиций
   🔗 URL: {url}
"""
    return result

def show_stats(data):
    """Показать статистику"""
    print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    total = len(data)
    quality_resumes = [d for d in data if d.get('resume_data', {}).get('detailed_info')]
    
    # Собираем данные для статистики
    all_skills = []
    cities = []
    salaries = []
    positions = []
    
    for resume in quality_resumes:
        detailed = resume['resume_data']['detailed_info']
        
        # Навыки
        skills = detailed.get('skills', [])
        all_skills.extend(skills)
        
        # Города
        city = detailed.get('location', '')
        if city and city != 'Не указан':
            cities.append(city)
        
        # Зарплаты
        salary = detailed.get('salary', '')
        if salary and 'грн' in salary:
            try:
                salary_num = int(''.join(filter(str.isdigit, salary)))
                if salary_num > 0:
                    salaries.append(salary_num)
            except:
                pass
        
        # Должности
        position = detailed.get('position', '')
        if position and position != 'Не указано':
            positions.append(position)
    
    print(f"📚 Всего резюме: {total}")
    print(f"✅ Качественных: {len(quality_resumes)}")
    print(f"💾 Размер файла: {os.path.getsize('база_резюме_полная.json')} байт")
    
    if salaries:
        avg_salary = sum(salaries) // len(salaries)
        min_salary = min(salaries)
        max_salary = max(salaries)
        print(f"💰 Зарплаты: {min_salary:,} - {max_salary:,} грн (среднее: {avg_salary:,})")
    
    # Топ навыков
    skill_counter = Counter(all_skills)
    if skill_counter:
        print(f"\n🔧 ТОП-5 НАВЫКОВ:")
        for skill, count in skill_counter.most_common(5):
            print(f"   • {skill}: {count} раз")
    
    # Топ городов
    city_counter = Counter(cities)
    if city_counter:
        print(f"\n📍 ТОП ГОРОДОВ:")
        for city, count in city_counter.most_common(5):
            print(f"   • {city}: {count} кандидатов")
    
    # Топ должностей
    position_counter = Counter(positions)
    if position_counter:
        print(f"\n💼 ТОП ДОЛЖНОСТЕЙ:")
        for position, count in position_counter.most_common(5):
            print(f"   • {position}: {count} резюме")
    
    print("=" * 50)

def show_resumes(data, limit=10, filter_type=None, search_term=None):
    """Показать резюме с фильтрацией"""
    
    # Фильтрация
    filtered_data = data.copy()
    
    if filter_type == 'quality':
        filtered_data = [d for d in filtered_data if d.get('resume_data', {}).get('detailed_info')]
    elif filter_type == 'kiev':
        filtered_data = [d for d in filtered_data 
                        if 'київ' in d.get('resume_data', {}).get('detailed_info', {}).get('location', '').lower()]
    elif filter_type == 'salary':
        filtered_data = [d for d in filtered_data 
                        if 'грн' in d.get('resume_data', {}).get('detailed_info', {}).get('salary', '')]
    elif filter_type == '1c':
        filtered_data = [d for d in filtered_data 
                        if any('1с' in skill.lower() 
                              for skill in d.get('resume_data', {}).get('detailed_info', {}).get('skills', []))]
    
    # Текстовый поиск
    if search_term:
        search_lower = search_term.lower()
        filtered_data = [d for d in filtered_data
                        if search_lower in d.get('resume_data', {}).get('detailed_info', {}).get('full_name', '').lower()
                        or search_lower in d.get('resume_data', {}).get('detailed_info', {}).get('position', '').lower()
                        or any(search_lower in skill.lower() 
                              for skill in d.get('resume_data', {}).get('detailed_info', {}).get('skills', []))]
    
    # Показываем результаты
    if not filtered_data:
        print("🔍 Ничего не найдено по заданным критериям")
        return
    
    print(f"\n📋 РЕЗЮМЕ ({len(filtered_data)} найдено):")
    print("=" * 70)
    
    for i, resume in enumerate(filtered_data[:limit], 1):
        print(format_resume(resume, i))
    
    if len(filtered_data) > limit:
        print(f"... и еще {len(filtered_data) - limit} резюме")

def interactive_menu():
    """Интерактивное меню"""
    data = load_database()
    if not data:
        return
    
    while True:
        print("\n🗂️  БАЗА ДАННЫХ РЕЗЮМЕ БУХГАЛТЕРОВ")
        print("=" * 40)
        print("1. 📊 Статистика")
        print("2. 📋 Все резюме (10 штук)")
        print("3. ✅ Только качественные")
        print("4. 🏙️  Резюме из Киева")
        print("5. 💰 С указанной зарплатой")
        print("6. 🔧 Со знанием 1С")
        print("7. 🔍 Поиск по ключевому слову")
        print("8. 🌐 Запустить веб-интерфейс")
        print("9. ❌ Выход")
        print()
        
        choice = input("Выберите опцию (1-9): ").strip()
        
        if choice == '1':
            show_stats(data)
        elif choice == '2':
            show_resumes(data, limit=10)
        elif choice == '3':
            show_resumes(data, limit=10, filter_type='quality')
        elif choice == '4':
            show_resumes(data, limit=10, filter_type='kiev')
        elif choice == '5':
            show_resumes(data, limit=10, filter_type='salary')
        elif choice == '6':
            show_resumes(data, limit=10, filter_type='1c')
        elif choice == '7':
            search_term = input("Введите ключевое слово для поиска: ").strip()
            if search_term:
                show_resumes(data, limit=10, search_term=search_term)
        elif choice == '8':
            print("🌐 Запускаем веб-интерфейс...")
            os.system("python start_viewer.py 8002 &")
            print("📱 Откройте в браузере: http://localhost:8002/view_database.html")
        elif choice == '9':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    # Можно запускать с параметрами или в интерактивном режиме
    import sys
    
    if len(sys.argv) > 1:
        data = load_database()
        command = sys.argv[1].lower()
        
        if command == 'stats':
            show_stats(data)
        elif command == 'all':
            show_resumes(data, limit=20)
        elif command == 'quality':
            show_resumes(data, filter_type='quality')
        elif command == 'kiev':
            show_resumes(data, filter_type='kiev')
        elif command == 'salary':
            show_resumes(data, filter_type='salary')
        elif command == '1c':
            show_resumes(data, filter_type='1c')
        else:
            print("❌ Неизвестная команда. Доступные: stats, all, quality, kiev, salary, 1c")
    else:
        interactive_menu() 