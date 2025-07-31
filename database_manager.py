"""
Database Manager для хранения данных резюме
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

class ResumeDatabase:
    """Менеджер базы данных для хранения данных резюме"""
    
    def __init__(self, db_path: str = "resumes.db"):
        """
        Инициализация подключения к базе данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Создание таблицы если не существует"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Создаем таблицу резюме
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resumes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resume_url TEXT UNIQUE NOT NULL,
                        resume_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем индекс для быстрого поиска по URL
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_resume_url 
                    ON resumes(resume_url)
                ''')
                
                conn.commit()
                self.logger.info("✅ База данных инициализирована")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    def save_resume(self, resume_url: str, resume_data: Dict) -> bool:
        """
        Сохранение данных резюме в базу
        
        Args:
            resume_url: URL резюме
            resume_data: Данные резюме в виде словаря
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            # Конвертируем данные в JSON
            resume_json = json.dumps(resume_data, ensure_ascii=False, indent=2)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Используем INSERT OR REPLACE для обновления существующих записей
                cursor.execute('''
                    INSERT OR REPLACE INTO resumes 
                    (resume_url, resume_data, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (resume_url, resume_json))
                
                conn.commit()
                
                # Проверяем было ли это обновление или новая запись
                if cursor.rowcount > 0:
                    action = "обновлено" if self.resume_exists(resume_url) else "добавлено"
                    self.logger.info(f"✅ Резюме {action}: {resume_url}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Резюме не сохранено: {resume_url}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения резюме {resume_url}: {e}")
            return False
    
    def resume_exists(self, resume_url: str) -> bool:
        """Проверка существования резюме в базе"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM resumes WHERE resume_url = ?', (resume_url,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки существования: {e}")
            return False
    
    def get_resume(self, resume_url: str) -> Optional[Dict]:
        """Получение данных резюме по URL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT resume_data FROM resumes 
                    WHERE resume_url = ?
                ''', (resume_url,))
                
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения резюме: {e}")
            return None
    
    def get_all_resumes(self) -> List[Dict]:
        """Получение всех резюме из базы"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT resume_url, resume_data, created_at, updated_at 
                    FROM resumes 
                    ORDER BY updated_at DESC
                ''')
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'resume_url': row[0],
                        'resume_data': json.loads(row[1]),
                        'created_at': row[2],
                        'updated_at': row[3]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения всех резюме: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Получение статистики базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество
                cursor.execute('SELECT COUNT(*) FROM resumes')
                total_count = cursor.fetchone()[0]
                
                # Последнее обновление
                cursor.execute('SELECT MAX(updated_at) FROM resumes')
                last_update = cursor.fetchone()[0]
                
                # Размер базы
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    'total_resumes': total_count,
                    'last_update': last_update,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / 1024 / 1024, 2)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def export_to_json(self, output_file: str = None) -> str:
        """Экспорт всех данных в JSON файл"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"resumes_export_{timestamp}.json"
        
        try:
            resumes = self.get_all_resumes()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resumes, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Экспорт завершен: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка экспорта: {e}")
            return ""
    
    def clear_database(self):
        """Очистка всех данных (осторожно!)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM resumes')
                conn.commit()
                self.logger.info("⚠️ База данных очищена")
        except Exception as e:
            self.logger.error(f"❌ Ошибка очистки БД: {e}")

if __name__ == "__main__":
    # Тестирование базы данных
    logging.basicConfig(level=logging.INFO)
    
    db = ResumeDatabase("test_resumes.db")
    
    # Тестовые данные
    test_data = {
        'full_name': 'Тестовый Кандидат',
        'position': 'Тестовая должность',
        'salary': '50000 грн',
        'skills': ['Python', 'SQL']
    }
    
    # Сохраняем
    db.save_resume("https://test.com/resume/1", test_data)
    
    # Получаем статистику
    stats = db.get_stats()
    print(f"📊 Статистика: {stats}")
    
    print("✅ Тестирование завершено") 