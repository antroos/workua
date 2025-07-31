#!/usr/bin/env python3
"""
Простой HTTP сервер для просмотра базы данных резюме
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Кастомный обработчик с CORS заголовками"""
    
    def end_headers(self):
        # Добавляем CORS заголовки
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Более красивое логирование"""
        print(f"📡 {self.address_string()} - {format % args}")

def start_server(port=8000):
    """Запуск HTTP сервера"""
    
    # Проверяем что нужные файлы существуют
    required_files = [
        'view_database.html',
        'resume_data_20250731_190906.json'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    try:
        # Создаем сервер
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 Запускаем веб-сервер...")
            print(f"📡 Адрес: http://localhost:{port}")
            print(f"📄 Страница: http://localhost:{port}/view_database.html")
            print(f"💾 База данных: {os.path.getsize('resume_data_20250731_190906.json')} байт")
            print()
            print(f"🔗 Откройте в браузере: http://localhost:{port}/view_database.html")
            print(f"⏹️  Для остановки нажмите Ctrl+C")
            print("="*60)
            
            # Автоматически открываем браузер через 2 секунды
            def open_browser():
                time.sleep(2)
                try:
                    webbrowser.open(f'http://localhost:{port}/view_database.html')
                    print(f"🌐 Браузер открыт автоматически")
                except:
                    print(f"ℹ️  Откройте браузер вручную")
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Запускаем сервер
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n👋 Сервер остановлен")
        return True
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Порт {port} уже занят. Попробуйте другой порт:")
            print(f"   python start_viewer.py {port + 1}")
        else:
            print(f"❌ Ошибка запуска сервера: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def show_stats():
    """Показать краткую статистику"""
    try:
        import json
        with open('resume_data_20250731_190906.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        quality_count = sum(1 for item in data if item.get('resume_data', {}).get('detailed_info'))
        
        print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ:")
        print(f"   📚 Всего записей: {len(data)}")
        print(f"   ✅ Качественных: {quality_count}")
        print(f"   💾 Размер файла: {os.path.getsize('resume_data_20250731_190906.json')} байт")
        print()
        
    except Exception as e:
        print(f"⚠️  Не удалось загрузить статистику: {e}")

if __name__ == "__main__":
    print("🗂️  ВЕБОРЩИЦА БАЗЫ ДАННЫХ РЕЗЮМЕ")
    print("="*40)
    
    # Показываем статистику
    show_stats()
    
    # Определяем порт
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ Неверный порт: {sys.argv[1]}. Используем 8000")
    
    # Запускаем сервер
    success = start_server(port)
    
    if not success:
        print("\n💡 АЛЬТЕРНАТИВНЫЕ СПОСОБЫ:")
        print("1. Попробуйте другой порт: python start_viewer.py 8001")
        print("2. Откройте файл view_database.html напрямую в браузере")
        print("3. Проверьте что файлы resume_data_20250731_190906.json и view_database.html существуют") 