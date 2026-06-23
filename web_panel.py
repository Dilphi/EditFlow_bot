from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальные переменные для доступа к данным бота
bot_data = {
    "stats": {
        "total_users": 0,
        "total_messages": 0,
        "processed_files": 0
    },
    "users": {},
    "modes_usage": {},
    "logs": []
}

def update_bot_data(handlers_module):
    """Обновляет данные бота из обработчиков."""
    global bot_data
    
    try:
        # Получаем данные из модуля handlers
        if hasattr(handlers_module, 'user_modes'):
            bot_data['users'] = dict(handlers_module.user_modes)
            bot_data['stats']['total_users'] = len(handlers_module.user_modes)
        
        # Подсчет использования режимов
        modes_usage = {}
        for mode in bot_data['users'].values():
            modes_usage[mode] = modes_usage.get(mode, 0) + 1
        bot_data['modes_usage'] = modes_usage
        
    except Exception as e:
        logger.error(f"Error updating bot data: {e}")

@app.route('/')
def dashboard():
    """Главная страница веб-панели."""
    return render_template('dashboard.html', data=bot_data)

@app.route('/api/stats')
def api_stats():
    """API для получения статистики."""
    return jsonify(bot_data['stats'])

@app.route('/api/users')
def api_users():
    """API для получения списка пользователей."""
    users_list = []
    for user_id, mode in bot_data['users'].items():
        users_list.append({
            'id': user_id,
            'mode': mode,
            'last_active': 'Сейчас'
        })
    return jsonify(users_list)

@app.route('/api/modes')
def api_modes():
    """API для получения статистики по режимам."""
    return jsonify(bot_data['modes_usage'])

@app.route('/api/logs')
def api_logs():
    """API для получения логов."""
    return jsonify(bot_data['logs'][-100:])  # Последние 100 записей

@app.route('/api/restart', methods=['POST'])
def api_restart():
    """Перезапуск бота (только для админов)."""
    # Здесь можно добавить логику перезапуска
    return jsonify({'status': 'success', 'message': 'Бот перезапущен'})

def run_web_panel(handlers_module, host='0.0.0.0', port=5000):
    """Запускает веб-панель в отдельном потоке."""
    def update_data():
        """Фоновое обновление данных."""
        while True:
            import time
            time.sleep(5)
            update_bot_data(handlers_module)
    
    # Запускаем фоновое обновление
    update_thread = threading.Thread(target=update_data, daemon=True)
    update_thread.start()
    
    logger.info(f"🌐 Веб-панель запущена на http://localhost:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)