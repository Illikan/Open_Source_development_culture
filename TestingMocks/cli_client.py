import questionary
import requests
import json 


BASE_URL = "http://127.0.0.1:8000/users"


def handle_response(response):
    """Обрабатывает ответ от сервера и выводит информацию."""
    print("-" * 30)
    if response.status_code >= 200 and response.status_code < 300:
        print(f"Успех! Статус: {response.status_code}")
        try:
            data = response.json()
            print("Ответ сервера:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except requests.exceptions.JSONDecodeError:
            print("Ответ сервера не в формате JSON, но запрос успешен.")
    else:
        print(questionary.Style([('question', 'bold'), ('answer', 'fg:red')]))
        print(f"Ошибка! Статус: {response.status_code}")
        try:
            error_data = response.json()
            print("Ошибка от сервера:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except requests.exceptions.JSONDecodeError:
            print("Детали ошибки не в формате JSON:", response.text)
    print("-" * 30)
    return response.status_code < 300 

def check_server_connection():
    """Проверяет доступность сервера."""
    try:
        response = requests.get(BASE_URL.replace("/users", "/docs"), timeout=2) 
        if response.status_code == 200:
            print(questionary.Style([('answer', 'fg:green')]))
            print("Соединение с сервером установлено.")
            return True
    except requests.exceptions.ConnectionError:
        pass 
    except requests.exceptions.Timeout:
        print(questionary.Style([('answer', 'fg:red')]))
        print("Сервер не ответил вовремя.")
        return False

    print(questionary.Style([('answer', 'fg:red')]))
    print(f"Не удалось подключиться к серверу по адресу: {BASE_URL.replace('/users', '')}")
    print("Убедитесь, что FastAPI сервер запущен.")
    return False


def register_user():
    """Регистрирует нового пользователя."""
    print("\n--- Регистрация нового пользователя ---")
    username = questionary.text(
        "Введите имя пользователя:",
        validate=lambda text: True if len(text) > 0 else "Имя пользователя не может быть пустым."
    ).ask()

    if username is None: return

    try:
        response = requests.post(f"{BASE_URL}/register", json={"username": username})
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения при регистрации: {e}")

def list_all_users():
    """Получает и выводит список всех пользователей."""
    print("\n--- Список всех зарегистрированных пользователей ---")
    try:
        response = requests.get(f"{BASE_URL}/all")
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения при получении списка пользователей: {e}")

def upload_csv_data():
    """Загружает CSV-файл для указанного пользователя."""
    print("\n--- Загрузка CSV данных для пользователя ---")
    username = questionary.text(
        "Введите имя пользователя, для которого загружаются данные:",
        validate=lambda text: True if len(text) > 0 else "Имя пользователя не может быть пустым."
    ).ask()
    if username is None: return

    dataset_name = questionary.text(
        "Введите имя для этого набора данных (например, 'отчет_март', 'контакты'):",
        validate=lambda text: True if len(text) > 0 else "Имя набора данных не может быть пустым."
    ).ask()
    if dataset_name is None: return

    file_path = questionary.path(
        "Укажите путь к CSV файлу:",
        validate=lambda path: True if path.endswith('.csv') else "Пожалуйста, выберите CSV файл (.csv)"
    ).ask()
    if file_path is None: return

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.split('/')[-1], f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/{username}/data/{dataset_name}", files=files)
        handle_response(response)
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения при загрузке CSV: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


def list_user_datasets():
    """Получает и выводит список имен наборов данных для пользователя."""
    print("\n--- Список наборов данных пользователя ---")
    username = questionary.text(
        "Введите имя пользователя, чьи наборы данных вы хотите просмотреть:",
        validate=lambda text: True if len(text) > 0 else "Имя пользователя не может быть пустым."
    ).ask()
    if username is None: return

    try:
        response = requests.get(f"{BASE_URL}/{username}/datasets")
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения при получении списка наборов данных: {e}")

def get_user_data():
    """Получает и выводит конкретный набор данных пользователя."""
    print("\n--- Получение данных пользователя ---")
    username = questionary.text(
        "Введите имя пользователя:",
        validate=lambda text: True if len(text) > 0 else "Имя пользователя не может быть пустым."
    ).ask()
    if username is None: return

    try:
        response_datasets = requests.get(f"{BASE_URL}/{username}/datasets")
        if response_datasets.status_code == 200:
            datasets_info = response_datasets.json()
            available_datasets = datasets_info.get("available_datasets", [])
            if not available_datasets:
                print(f"У пользователя '{username}' нет загруженных наборов данных.")
                return
            
            dataset_name = questionary.select(
                "Выберите набор данных для просмотра:",
                choices=available_datasets
            ).ask()
            if dataset_name is None: return

        elif response_datasets.status_code == 404: 
            handle_response(response_datasets)
            return
        else: 
            print("Не удалось получить список наборов данных для пользователя.")
            handle_response(response_datasets)
            return

    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения при получении списка наборов данных: {e}")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/{username}/data/{dataset_name}")
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения при получении данных '{dataset_name}': {e}")


def main_menu():
    """Отображает главное меню и обрабатывает выбор пользователя."""
    if not check_server_connection():
        return

    actions = {
        "Зарегистрировать нового пользователя": register_user,
        "Показать всех пользователей": list_all_users,
        "Загрузить CSV данные для пользователя": upload_csv_data,
        "Показать имена наборов данных пользователя": list_user_datasets,
        "Получить данные пользователя по имени набора": get_user_data,
        "Выход": lambda: print("До свидания!")
    }

    while True:
        print("\n" + "="*10 + " ГЛАВНОЕ МЕНЮ " + "="*10)
        choice = questionary.select(
            "Выберите действие:",
            choices=list(actions.keys())
        ).ask()

        if choice is None or choice == "Выход":
            actions["Выход"]()
            break
        
        action_func = actions.get(choice)
        if action_func:
            action_func()
        else:
            print("Неизвестный выбор.")

if __name__ == "__main__":
    main_menu()