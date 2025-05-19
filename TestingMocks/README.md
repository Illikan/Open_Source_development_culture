# API для управления пользовательскими CSV-данными и CLI-клиент

Этот проект представляет собой простое FastAPI приложение для регистрации пользователей (без паролей) и управления именованными наборами CSV-данных, привязанными к каждому пользователю. Также в проект включен CLI-клиент для взаимодействия с этим API и набор тестов для сервера и клиента.

## Структура проекта

```
.
├── __init__.py             # Помечает директорию как пакет Python
├── cli_client.py           # Исходный код CLI-клиента
├── data.csv                # Пример CSV файла для загрузки
├── main.py                 # Исходный код FastAPI сервера
├── requirements.txt        # Зависимости проекта
├── test_client.py          # Тесты для CLI-клиента
└── test_server.py          # Тесты для FastAPI сервера
```

## 1. FastAPI Сервер (`main.py`)

Простой сервер на FastAPI, который позволяет:
*   Регистрировать пользователей (только по имени пользователя).
*   Загружать CSV-файлы для зарегистрированного пользователя, присваивая каждому файлу (набору данных) уникальное имя.
*   Получать список всех зарегистрированных пользователей.
*   Получать список имен всех наборов данных для конкретного пользователя.
*   Получать содержимое конкретного набора данных (в формате JSON) для конкретного пользователя.

### Хранение данных

Данные хранятся в памяти в виде Python словарей и множеств:
*   `registered_users = set()`: Множество для хранения уникальных имен зарегистрированных пользователей.
*   `user_data_db = {}`: Словарь, где ключ - `username`, а значение - другой словарь. Во вложенном словаре ключ - `dataset_name` (имя набора данных), а значение - `list[dict[str, str]]` (данные из CSV, распарсенные в список словарей).

### Ключевые эндпоинты

1.  **Регистрация пользователя:**
    *   **`POST /users/register`**
    *   Принимает JSON: `{"username": "имя_пользователя"}`
    *   Регистрирует пользователя, если имя еще не занято.
    *   **Пример реализации:**
        ```python
        registered_users = set()
        user_data_db = {}

        router = APIRouter(
            prefix="/users",
            tags=["users_no_password"], 
        )

        @router.post("/register", status_code=status.HTTP_201_CREATED)
        async def register_user(username: str = Body(..., embed=True)):
            if username in registered_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            registered_users.add(username)
            user_data_db[username] = {} # Инициализация хранилища для данных пользователя
            return {"message": "User registered successfully", "username": username}
        ```

2.  **Загрузка CSV-данных:**
    *   **`POST /users/{username}/data/{dataset_name}`**
    *   `username` и `dataset_name` передаются в пути.
    *   Файл CSV передается как `multipart/form-data`.
    *   Данные парсятся с помощью функции `parse_csv` и сохраняются.
    *   **Функция парсинга CSV (`parse_csv`):**
        ```python
        import csv
        import io

        def parse_csv(csv_string):
            data = []
            f = io.StringIO(csv_string.strip())
            reader = csv.reader(f)
            try:
                header = next(reader)
                header = [h.strip() for h in header]
            except StopIteration:
                return data
            for row in reader:
                if not row:
                    continue
                row_dict = {}
                for col_name, value in zip(header, row):
                    row_dict[col_name.strip()] = value.strip()
                data.append(row_dict)
            return data
        ```
    *   **Пример эндпоинта загрузки:**
        ```python
        @router.post("/{username}/data/{dataset_name}", status_code=status.HTTP_200_OK)
        async def upload_named_user_csv(
            username: str = Path(...),
            dataset_name: str = Path(...),
            file: UploadFile = File(...)
        ):
            if username not in registered_users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            if not file.filename.endswith('.csv'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Please upload a .csv file."
                )
            try:
                contents = await file.read()
                decoded_content = contents.decode('utf-8')
                data_list = parse_csv(decoded_content)
                user_data_db[username][dataset_name] = data_list
                return {
                    "message": f"Dataset '{dataset_name}' uploaded successfully for user '{username}'",
                    "username": username,
                    "dataset_name": dataset_name,
                    "filename": file.filename,
                    "rows_processed": len(data_list)
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process CSV file: {str(e)}"
                )
            finally:
                await file.close()
        ```
### Запуск сервера
Сервер запускается стандартной командой Uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 2. CLI-клиент (`cli_client.py`)

Консольный клиент для взаимодействия с API сервера. Использует библиотеку `questionary` для создания интерактивного меню и ввода данных, и `requests` для HTTP-запросов.

### Ключевые функции

*   **Проверка соединения с сервером:** Перед отображением меню клиент пытается подключиться к серверу.
*   **Меню действий:**
    *   Зарегистрировать нового пользователя
    *   Показать всех пользователей
    *   Загрузить CSV данные для пользователя
    *   Показать имена наборов данных пользователя
    *   Получить данные пользователя по имени набора
    *   Выход
*   **Обработка ответов:** Ответы сервера форматируются и выводятся в консоль, включая сообщения об ошибках.
*   **Пример взаимодействия с `questionary` и `requests` (регистрация):**
    ```python
    # cli_client.py
    import questionary
    import requests
    import json # Для красивого вывода

    BASE_URL = "http://127.0.0.1:8000/users" # URL API

    def handle_response(response):
        """Обрабатывает ответ от сервера и выводит информацию."""
        # ... (код для вывода ответа) ...
        pass

    def register_user():
        print("\n--- Регистрация нового пользователя ---")
        username = questionary.text(
            "Введите имя пользователя:",
            validate=lambda text: True if len(text) > 0 else "Имя пользователя не может быть пустым."
        ).ask()
        if username is None: return

        try:
            response = requests.post(f"{BASE_URL}/register", json={"username": username})
            handle_response(response) # Вспомогательная функция для вывода ответа
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения при регистрации: {e}")
    ```

### Запуск клиента
```bash
python cli_client.py
```

## 3. Тестирование

Проект включает тесты для сервера и клиента, написанные с использованием `pytest`.

### 3.1 Тестирование FastAPI сервера (`test_server.py`)

*   **Инструмент:** `fastapi.testclient.TestClient`. Это позволяет тестировать API без реального запуска HTTP-сервера, отправляя запросы приложению напрямую в памяти.
*   **Структура тестов:** Тесты сгруппированы по эндпоинтам.
*   **Ключевая фикстура:**
    ```python
    # test_server.py
    import pytest
    # Предполагается, что main.py находится в том же пакете/директории
    from .main import app, registered_users, user_data_db # Используем относительный импорт

    @pytest.fixture(autouse=True)
    def clear_data_stores():
        """Очищает хранилища данных перед каждым тестом."""
        registered_users.clear()
        user_data_db.clear()
        yield
    ```
    Эта фикстура с `autouse=True` гарантирует, что каждое тестовое выполнение начинается с чистого состояния хранилищ данных, обеспечивая изоляцию тестов.
*   **Пример теста (регистрация нового пользователя):**
    ```python
    # test_server.py
    from fastapi.testclient import TestClient
    # from .main import app # app импортируется выше

    client = TestClient(app) # client создается один раз на модуль

    def test_register_new_user():
        response = client.post("/users/register", json={"username": "testuser1"})
        assert response.status_code == 201
        assert response.json()["username"] == "testuser1"
        assert "testuser1" in registered_users # Проверка состояния хранилища
    ```
*   **Покрытие:** Тесты покрывают "счастливые пути", ошибочные сценарии (например, регистрация существующего пользователя, загрузка для несуществующего пользователя, неверный тип файла) и граничные случаи (например, пустой CSV, CSV только с заголовком).

### 3.2 Тестирование CLI-клиента (`test_client.py`)

*   **Инструменты:**
    *   `requests-mock`: Для мокирования HTTP-ответов от сервера. Это позволяет тестировать логику клиента изолированно, без необходимости запуска реального FastAPI сервера.
    *   `unittest.mock.patch`: Для мокирования ввода пользователя через `questionary` и встроенной функции `open` при тестировании загрузки файлов.
    *   `pytest` фикстура `capsys`: Для перехвата и проверки вывода клиента в консоль.
*   **Структура тестов:** Тесты написаны для каждой функции клиента, отвечающей за взаимодействие с определенной командой меню.
*   **Пример теста (регистрация пользователя, мокирование `questionary` и `requests`):**
    ```python
    # test_client.py
    from unittest import mock
    import cli_client # Импорт модуля клиента
    # import requests_mock # Для более сложных моков HTTP, если используется

    @mock.patch('cli_client.questionary.text') # Мокаем объект questionary.text в модуле cli_client
    @mock.patch('cli_client.requests.post')    # Мокаем requests.post в модуле cli_client
    def test_register_user_success(mock_post, mock_questionary_text, capsys):
        # Настраиваем мок questionary
        mock_questionary_text.return_value.ask.return_value = "newuser" # Мок ввода
        
        # Настраиваем мок requests.post
        mock_post.return_value.status_code = 201 # Мок ответа сервера
        mock_post.return_value.json.return_value = {
            "message": "User registered successfully", "username": "newuser"
        }

        cli_client.register_user() # Вызываем тестируемую функцию

        # Проверяем, что requests.post был вызван правильно
        mock_post.assert_called_once_with(
            f"{cli_client.BASE_URL}/register", json={"username": "newuser"}
        )
        # Проверяем вывод в консоль
        captured = capsys.readouterr()
        assert "Успех! Статус: 201" in captured.out
    ```
*   **Покрытие:** Тесты проверяют, что клиент корректно формирует запросы к мок-серверу на основе мок-ввода пользователя, правильно обрабатывает успешные и ошибочные мок-ответы от сервера, и корректно выводит информацию в консоль.

### Запуск тестов
Из корневой директории проекта (`TESTINGMOCKS`):
```bash
pytest
```

## Установка и запуск

1.  **Клонируйте репозиторий:**
    И перейдите в директорию `TESTINGMOCKS` согласно структуре.

2.  **Создайте и активируйте виртуальное окружение (рекомендуется):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Установите зависимости из `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```
    **Содержимое `requirements.txt`:**
    ```txt
    fastapi
    uvicorn
    requests
    questionary
    pytest
    requests-mock
    ```
4.  **Запустите FastAPI сервер:**
    ```bash
    python main.py
    ```
    Или альтернативно:
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    Сервер будет доступен по адресу `http://127.0.0.1:8000`.
    Документация API (Swagger UI) будет доступна по адресу `http://127.0.0.1:8000/docs`.

5.  **Запустите CLI-клиент (в другом терминале, после активации виртуального окружения):**
    ```bash
    python cli_client.py
    ```
6.  **Запустите тесты (после активации виртуального окружения):**
    ```bash
    pytest
    ```
