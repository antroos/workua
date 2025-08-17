#!/usr/bin/env python3
"""
Создание CSV файла точно как в веб-интерфейсе
Те же поля, та же структура данных
"""

import json
import pandas as pd
import re
from datetime import datetime

def create_web_interface_csv():
    """Создает CSV с теми же полями что в веб-интерфейсе"""
    print("📊 СОЗДАНИЕ CSV КАК В ВЕБ-ИНТЕРФЕЙСЕ")
    print("=" * 50)
    
    # Загружаем исходные данные (те же что использует веб-интерфейс)
    with open('resume_data_20250801_024557.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📂 Загружено резюме: {len(data):,}")
    
    # Обрабатываем данные точно как в веб-интерфейсе (JavaScript код)
    export_data = []
    
    for index, item in enumerate(data):
        # Извлекаем возраст и город из age_location (как в JavaScript)
        age = 'Не указан'
        location = 'Не указан'
        
        if item.get('age_location'):
            parts = item['age_location'].split(', ')
            if len(parts) >= 2:
                age = parts[0]  # "41 рік"
                location = ', '.join(parts[1:])  # "Тернівка"
            else:
                location = item['age_location']
        
        # Извлекаем навыки из full_text (как в JavaScript)
        skills = []
        if item.get('full_text'):
            # Ищем секцию навыков
            skills_match = re.search(r'Знання і навички\s*([\s\S]*?)(?:\n\n|\nДодаткова інформація|\nЗапропонувати вакансію|$)', 
                                   item['full_text'], re.IGNORECASE)
            if skills_match and skills_match.group(1):
                skills_text = skills_match.group(1)
                skills = [s.strip() for s in skills_text.split('\n') if s.strip() and len(s.strip()) > 1]
        
        # Создаем подробную информацию (как в модальном окне веб-интерфейса)
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
            for skill in skills[:15]:  # Первые 15 навыков
                detailed_info.append(f"  • {skill}")
            if len(skills) > 15:
                detailed_info.append(f"  ... и еще {len(skills) - 15} навыков")
        
        # Полный текст (сокращенный)
        if item.get('full_text'):
            full_text_preview = item['full_text'][:500]
            detailed_info.append(f"\n📄 Полная информация: {full_text_preview}...")
        
        # Создаем строку точно как в веб-интерфейсе
        row = {
            'ID': index + 1,
            'Имя': item.get('name', 'Не указано'),
            'Должность': item.get('title', 'Не указано'),
            'Зарплата': item.get('salary', 'Не указана'),
            'Город': location,
            'Возраст': age,
            'Навыки': ', '.join(skills[:10]) if skills else 'Не указаны',  # Первые 10 навыков
            'Количество_навыков': len(skills),
            'Опыт': ', '.join(item.get('experience', [])) if isinstance(item.get('experience'), list) else str(item.get('experience', 'Не указан')),
            'Образование': item.get('education_employment', 'Не указано'),
            'URL': item.get('url', item.get('link', '#')),
            'Подробно': '\n'.join(detailed_info),  # Полная детальная информация
        }
        
        export_data.append(row)
    
    # Создаем DataFrame и экспортируем
    df = pd.DataFrame(export_data)
    
    # Имя файла с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'web_interface_resume_data_{timestamp}.csv'
    
    # Сохраняем CSV (с BOM для корректного отображения в Excel)
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    
    # Статистика
    total = len(df)
    with_names = len(df[df['Имя'] != 'Не указано'])
    with_skills = len(df[df['Навыки'] != 'Не указаны'])
    with_salary = len(df[df['Зарплата'] != 'Не указана'])
    
    print()
    print("📈 СТАТИСТИКА CSV:")
    print(f"   📚 Всего записей: {total:,}")
    print(f"   👤 С именами: {with_names:,} ({with_names/total*100:.1f}%)")
    print(f"   🔧 С навыками: {with_skills:,} ({with_skills/total*100:.1f}%)")
    print(f"   💰 С зарплатой: {with_salary:,} ({with_salary/total*100:.1f}%)")
    print()
    print(f"✅ CSV файл создан: {csv_filename}")
    
    # Показываем первые несколько записей для проверки
    print()
    print("📋 ПРИМЕРЫ ДАННЫХ (первые 5 записей):")
    print(df.head().to_string(index=False))
    
    return csv_filename

def main():
    """Главная функция"""
    csv_file = create_web_interface_csv()
    print()
    print("🎉 CSV файл готов!")
    print(f"📁 Файл: {csv_file}")
    print("📊 Структура точно как в веб-интерфейсе")

if __name__ == "__main__":
    main()