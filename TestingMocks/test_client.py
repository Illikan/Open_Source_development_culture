import pytest
import requests_mock # Для мока HTTP запросов
from unittest import mock # Для мока questionary
from .cli_client import * # Импортируем модуль клиента

# Тесты для функции регистрации
@mock.patch('questionary.text') # Мокаем ввод пользователя
@mock.patch('requests.post')    # Мокаем HTTP POST запрос
def test_register_user_success(mock_post, mock_questionary_text, capsys):
    # Настраиваем мок questionary: он вернет 'newuser' при вызове .ask()
    mock_questionary_text.return_value.ask.return_value = "newuser"
    
    # Настраиваем мок requests.post: он вернет успешный ответ
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {
        "message": "User registered successfully", "username": "newuser"
    }
    
    register_user() # Вызываем тестируемую функцию
    
    # Проверяем, что requests.post был вызван с правильными аргументами
    mock_post.assert_called_once_with(
        f"{BASE_URL}/register", json={"username": "newuser"}
    )
    
    # Проверяем вывод в консоль
    captured = capsys.readouterr()
    assert "Успех! Статус: 201" in captured.out
    assert '"username": "newuser"' in captured.out

@mock.patch('questionary.text')
@mock.patch('requests.post')
def test_register_user_failure_server_error(mock_post, mock_questionary_text, capsys):
    mock_questionary_text.return_value.ask.return_value = "existinguser"
    
    mock_post.return_value.status_code = 400
    mock_post.return_value.json.return_value = {"detail": "Username already exists"}
    
    register_user()
    
    mock_post.assert_called_once_with(
        f"{BASE_URL}/register", json={"username": "existinguser"}
    )
    
    captured = capsys.readouterr()
    assert "Ошибка! Статус: 400" in captured.out
    assert '"detail": "Username already exists"' in captured.out

@mock.patch('questionary.text')
@mock.patch('requests.post')
def test_register_user_connection_error(mock_post, mock_questionary_text, capsys):
    mock_questionary_text.return_value.ask.return_value = "anyuser"
    
    # Имитируем ошибку соединения
    mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
    
    register_user()
    
    captured = capsys.readouterr()
    assert "Ошибка подключения при регистрации: Connection failed" in captured.out

# Тесты для функции получения списка пользователей
@mock.patch('requests.get')
def test_list_all_users_success(mock_get, capsys):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"registered_users": ["user1", "user2"]}
    
    list_all_users()
    
    mock_get.assert_called_once_with(f"{BASE_URL}/all")
    captured = capsys.readouterr()
    assert "Успех! Статус: 200" in captured.out
    assert '"registered_users": [\n    "user1",\n    "user2"\n  ]' in captured.out # Проверяем форматированный JSON

# Тесты для загрузки CSV
def test_upload_csv_data_file_not_found(capsys):
    with mock.patch('questionary.text') as mock_text, \
         mock.patch('questionary.path') as mock_path:
        
        mock_text_gen = (val for val in ["testuser", "mydata"])
        mock_text.return_value.ask.side_effect = lambda: next(mock_text_gen)
        mock_path.return_value.ask.return_value = "nonexistent.csv"

        # Мокаем open, чтобы он вызвал FileNotFoundError
        with mock.patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            upload_csv_data()

        captured = capsys.readouterr()
        assert "Ошибка: Файл не найден по пути: nonexistent.csv" in captured.out


# Тесты для получения списка датасетов пользователя
@mock.patch('questionary.text')
@mock.patch('requests.get')
def test_list_user_datasets_success(mock_get, mock_questionary_text, capsys):
    mock_questionary_text.return_value.ask.return_value = "user1"
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "username": "user1", "available_datasets": ["dataA", "dataB"]
    }

    list_user_datasets()

    mock_get.assert_called_once_with(f"{BASE_URL}/user1/datasets")
    captured = capsys.readouterr()
    assert "Успех! Статус: 200" in captured.out
    assert '"available_datasets": [\n    "dataA",\n    "dataB"\n  ]' in captured.out

# Тесты для получения конкретных данных
@mock.patch('questionary.text')      
@mock.patch('questionary.select')   
@mock.patch('requests.get') 
def test_get_user_data_success(mock_get, mock_questionary_select, mock_questionary_text, capsys):

    mock_questionary_text.return_value.ask.return_value = "datauser" 
    mock_questionary_select.return_value.ask.return_value = "report1" 

    mock_response_datasets = mock.Mock()
    mock_response_datasets.status_code = 200
    mock_response_datasets.json.return_value = {
        "username": "datauser", "available_datasets": ["report1", "report2"]
    }

    mock_response_data = mock.Mock()
    mock_response_data.status_code = 200
    mock_response_data.json.return_value = [{"col": "val"}]

    mock_get.side_effect = [mock_response_datasets, mock_response_data]

    get_user_data()

    expected_calls = [
        mock.call(f"{BASE_URL}/datauser/datasets"),
        mock.call(f"{BASE_URL}/datauser/data/report1")
    ]
    assert mock_get.call_args_list == expected_calls
    

    mock_questionary_select.assert_called_once_with(
        "Выберите набор данных для просмотра:",
        choices=["report1", "report2"]
    )

    captured = capsys.readouterr()
    assert "Успех! Статус: 200" in captured.out 
    assert '"col": "val"' in captured.out

@mock.patch('questionary.text')
@mock.patch('requests.get')
def test_get_user_data_no_datasets(mock_get, mock_questionary_text, capsys):
    mock_questionary_text.return_value.ask.return_value = "nodatauser"
    
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "username": "nodatauser", "available_datasets": []
    }

    get_user_data()
    
    mock_get.assert_called_once_with(f"{BASE_URL}/nodatauser/datasets")
    captured = capsys.readouterr()
    assert "У пользователя 'nodatauser' нет загруженных наборов данных." in captured.out