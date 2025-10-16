# Telegram Kick Tool

Скрипт для массового удаления участников из Telegram каналов.

## Установка

```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Деактивация виртуального окружения (когда закончите)
deactivate
```

## Настройка

1. Получите API ключи на https://my.telegram.org/
2. Отредактируйте `config.py`:
```python
API_ID = "your_api_id"
API_HASH = "your_api_hash" 
PHONE_NUMBER = "+78005553535"
```

## Использование

```bash
python kick.py
```

### Параметры:
- **Канал** - любой @username канала
- **Количество** - сколько участников удалить

### Пример:
- Канал: @mychannel
- Удалить: 1000 участников

## Важно

- Нужны права администратора в канале
- Одна авторизация для всех операций
- Можно отменить в любой момент (Ctrl+C)

## Файлы

- `kick.py` - основной скрипт
- `config.py` - настройки API
- `requirements.txt` - зависимости
- `session.session` - автогенерируемый файл сессии
