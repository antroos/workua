#!/usr/bin/env python3
"""
Очистка полного текста резюме от служебной информации сайта
"""

import json
import pandas as pd
import re
from datetime import datetime

def clean_full_text(text):
    """Очищает полный текст от служебной информации сайта"""
    if not text:
        return text
    
    # Список служебных фраз для удаления
    cleanup_patterns = [
        # Навигация сайта
        r'Шукачу\s*',
        r'Українська\s*',
        r'Знайти кандидатів\s*',
        r'Створити вакансію\s*',
        r'Увійти\s*',
        r'Кандидати\s*',
        r'у [А-ЯІЇЄа-яіїє\s]+\s*',
        r'Запропонувати вакансію\s*',
        r'Зберегти\s*',
        r'Ще\s*',
        r'Файл\s*',
        
        # Контактная информация (служебная)
        r'Контактна інформація\s*',
        r'Шукач вказав телефон\s*',
        r'та ел\. пошту\.?\s*',
        r'Прізвище, контакти та світлина доступні тільки для зареєстрованих роботодавців\..*?(?=\n|$)',
        r'Щоб отримати доступ до особистих даних кандидатів.*?(?=\n|$)',
        r'Шукач приховав свої особисті дані.*?(?=\n|$)',
        r'але ви зможете надіслати йому повідомлення.*?(?=\n|$)',
        r'але йому можна надіслати повідомлення.*?(?=\n|$)',
        
        # Другие служебные элементы
        r'Резюме від \d+ [а-яіїє]+ \d+\s*',
        r'PRO\s*',
        r'VIP\s*',
        r'TOP\s*',
        
        # Схожі кандидати и футер
        r'Схожі кандидати.*$',
        r'Кандидати у категорії.*$',
        r'Кандидати за містами.*$',
        r'Порівняйте свої вимоги.*$',
        r'Вакансії.*$',
        r'Послуги сайту.*$',
        r'Про нас.*$',
        r'Контакти.*$',
        r'© \d+-\d+ Work\.ua.*$',
        r'Зроблено в компанії.*$',
        r'Освіта в Україні.*$',
        r'Typing tutor.*$',
    ]
    
    cleaned_text = text
    
    # Применяем паттерны очистки
    for pattern in cleanup_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Убираем лишние пробелы и переносы строк
    cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)  # Двойные переносы
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)  # Пробелы в начале/конце строк
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def create_cleaned_csv():
    """Создает CSV с очищенным полным текстом"""
    print("🧹 ОЧИСТКА ПОЛНОГО ТЕКСТА ОТ СЛУЖЕБНОЙ ИНФОРМАЦИИ")
    print("=" * 60)
    
    # Загружаем исходные данные
    with open('resume_data_20250801_024557.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📂 Загружено резюме: {len(data):,}")
    
    # Обрабатываем данные
    export_data = []
    cleaned_count = 0
    
    for index, item in enumerate(data):
        # Извлекаем возраст и город из age_location
        age = 'Не указан'
        location = 'Не указан'
        
        if item.get('age_location'):
            parts = item['age_location'].split(', ')
            if len(parts) >= 2:
                age = parts[0]
                location = ', '.join(parts[1:])
            else:
                location = item['age_location']
        
        # Извлекаем навыки из full_text
        skills = []
        if item.get('full_text'):
            skills_match = re.search(r'Знання і навички\s*([\s\S]*?)(?:\n\n|\nДодаткова інформація|\nЗапропонувати вакансію|$)', 
                                   item['full_text'], re.IGNORECASE)
            if skills_match and skills_match.group(1):
                skills_text = skills_match.group(1)
                skills = [s.strip() for s in skills_text.split('\n') if s.strip() and len(s.strip()) > 1]
        
        # ОЧИЩАЕМ полный текст
        original_full_text = item.get('full_text', '')
        cleaned_full_text = clean_full_text(original_full_text)
        
        if len(cleaned_full_text) < len(original_full_text):
            cleaned_count += 1
        
        # Создаем подробную информацию с ОЧИЩЕННЫМ текстом
        detailed_info = []
        
        # Основная информация
        detailed_info.append(f"👤 Имя: {item.get('name', 'Не указано')}")
        detailed_info.append(f"💼 Должность: {item.get('title', 'Не указано')}")
        detailed_info.append(f"💰 Зарплата: {item.get('salary', 'Не указана')}")
        detailed_info.append(f"📍 Возраст и локация: {item.get('age_location', 'Не указано')}")
        detailed_info.append(f"🔗 URL: {item.get('url', item.get('link', '#'))}")
        
        # Опыт работы
        if item.get('experience'):
            detailed_info.append("\n📋 Опыт работы:")
            if isinstance(item['experience'], list):
                for exp in item['experience']:
                    detailed_info.append(f"  • {exp}")
            else:
                detailed_info.append(f"  • {item['experience']}")
        
        # Образование
        if item.get('education_employment'):
            detailed_info.append(f"\n🎓 Образование: {item['education_employment']}")
        
        # Навыки
        if skills:
            detailed_info.append(f"\n🔧 Навыки ({len(skills)}):")
            for skill in skills[:15]:
                detailed_info.append(f"  • {skill}")
            if len(skills) > 15:
                detailed_info.append(f"  ... и еще {len(skills) - 15} навыков")
        
        # ОЧИЩЕННЫЙ полный текст (ограниченный)
        if cleaned_full_text:
            preview_text = cleaned_full_text[:800] if len(cleaned_full_text) > 800 else cleaned_full_text
            detailed_info.append(f"\n📄 Полная информация (очищено): {preview_text}")
            if len(cleaned_full_text) > 800:
                detailed_info.append("...")
        
        # Создаем строку
        row = {
            'ID': index + 1,
            'Имя': item.get('name', 'Не указано'),
            'Должность': item.get('title', 'Не указано'),
            'Зарплата': item.get('salary', 'Не указана'),
            'Город': location,
            'Возраст': age,
            'Навыки': ', '.join(skills[:10]) if skills else 'Не указаны',
            'Количество_навыков': len(skills),
            'Опыт': ', '.join(item.get('experience', [])) if isinstance(item.get('experience'), list) else str(item.get('experience', 'Не указан')),
            'Образование': item.get('education_employment', 'Не указано'),
            'URL': item.get('url', item.get('link', '#')),
            'Подробно': '\n'.join(detailed_info),
        }
        
        export_data.append(row)
        
        # Прогресс
        if (index + 1) % 1000 == 0:
            print(f"⏳ Обработано: {index + 1:,}/{len(data):,}")
    
    # Создаем DataFrame и экспортируем
    df = pd.DataFrame(export_data)
    
    # Имя файла с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'resume_data_CLEANED_{timestamp}.csv'
    
    # Сохраняем CSV
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    
    # Статистика
    total = len(df)
    with_names = len(df[df['Имя'] != 'Не указано'])
    with_skills = len(df[df['Навыки'] != 'Не указаны'])
    with_salary = len(df[df['Зарплата'] != 'Не указана'])
    
    print()
    print("📊 СТАТИСТИКА ОЧИСТКИ:")
    print(f"   📚 Всего записей: {total:,}")
    print(f"   🧹 Очищено текстов: {cleaned_count:,} ({cleaned_count/total*100:.1f}%)")
    print(f"   👤 С именами: {with_names:,} ({with_names/total*100:.1f}%)")
    print(f"   🔧 С навыками: {with_skills:,} ({with_skills/total*100:.1f}%)")
    print(f"   💰 С зарплатой: {with_salary:,} ({with_salary/total*100:.1f}%)")
    print()
    print(f"✅ Очищенный CSV создан: {csv_filename}")
    
    return csv_filename

def main():
    """Главная функция"""
    csv_file = create_cleaned_csv()
    print()
    print("🎉 ОЧИСТКА ЗАВЕРШЕНА!")
    print(f"📁 Файл: {csv_file}")
    print("🧹 Служебная информация сайта удалена")
    print("📋 Полная информация очищена и готова к использованию")

if __name__ == "__main__":
    main()