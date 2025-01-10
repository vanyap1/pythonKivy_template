# Python Kivy Template Project

## Опис
Цей проект є шаблоном для створення графічного інтерфейсу користувача (GUI) за допомогою Kivy. Він включає в себе серверну частину для обробки HTTP та UDP запитів, а також фоновий процес для виконання завдань у фоновому режимі.

## Вимоги
- Python 3
- Kivy
- systemd (для створення сервісу)

## Структура проекту
- `main.py`: Основний файл проекту, який запускає GUI та серверні компоненти.
- `remoteCtrlServer/udpService.py`: Модуль для обробки UDP запитів.
- `remoteCtrlServer/httpserver.py`: Модуль для обробки HTTP запитів.
- `backgroundServices/backgroundProcessor.py`: Модуль для виконання завдань у фоновому режимі.
- `install.sh`: Скрипт для створення та управління системним сервісом.

## Інсталяція
1. Клонуйте репозиторій:
   ```sh
   git clone https://github.com/yourusername/pythonKivy_template.git
   cd pythonKivy_template
   ```

2. Встановіть необхідні залежності:
   ```sh
   pip install kivy
   ```

3. Запустіть проект:
   ```sh
   python main.py
   ```

## Створення та управління сервісом
Для автоматичного запуску проекту при завантаженні системи, ви можете створити системний сервіс за допомогою скрипта `install.sh`.

### Використання скрипта `install.sh`
1. Зробіть скрипт виконуваним:
   ```sh
   chmod +x install.sh
   ```

2. Використовуйте скрипт з аргументами:
   - Для видалення попереднього сервісу та встановлення нового:
     ```sh
     ./install.sh -f
     ```
   - Для відключення автозапуску та видалення сервісу:
     ```sh
     ./install.sh -r
     ```
   - Для відображення списку аргументів:
     ```sh
     ./install.sh -? 
     ```
     або
     ```sh
     ./install.sh -help
     ```

### Приклад сервісного файлу
Скрипт `install.sh` створює сервісний файл з наступним вмістом:
```ini
[Unit]
Description=My Python Project Service
After=network.target

[Service]
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 /home/vanya/pythonKivy_template/main.py
WorkingDirectory=/home/vanya/pythonKivy_template
StandardOutput=inherit
StandardError=inherit
Restart=always
User=yourusername

[Install]
WantedBy=multi-user.target
```

## Файли проекту
### `main.py`
Основний файл проекту, який запускає GUI та серверні компоненти. Він включає в себе:
- Ініціалізацію GUI за допомогою Kivy.
- Запуск HTTP та UDP серверів.
- Фоновий процес для виконання завдань.

### `remoteCtrlServer/udpService.py`
Модуль для обробки UDP запитів. Він включає в себе:
- Клас `UdpAsyncClient` для обробки UDP запитів.
- Методи для відправки та отримання UDP пакетів.

### `remoteCtrlServer/httpserver.py`
Модуль для обробки HTTP запитів. Він включає в себе:
- Клас `HttpServer` для обробки HTTP запитів.
- Методи для обробки GET та POST запитів.

### `backgroundServices/backgroundProcessor.py`
Модуль для виконання завдань у фоновому режимі. Він включає в себе:
- Клас `BackgroundWorker` для виконання завдань у фоновому режимі.
- Методи для запуску, зупинки та призупинення фонових завдань.

### `install.sh`
Скрипт для створення та управління системним сервісом. Він включає в себе:
- Функції для створення, включення та відключення сервісу.
- Інструкції для використання скрипта з аргументами.

## Ліцензія
Цей проект ліцензований під ліцензією MIT. Дивіться файл `LICENSE` для отримання додаткової інформації.