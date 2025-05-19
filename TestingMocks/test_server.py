import pytest
from fastapi.testclient import TestClient

from .main import app, registered_users, user_data_db

client = TestClient(app)

# Вспомогательная функция для очистки данных между тестами
@pytest.fixture(autouse=True)
def clear_data_stores():
    """Очищает хранилища данных перед каждым тестом."""
    registered_users.clear()
    user_data_db.clear()
    yield 
# Тесты для эндпоинта регистрации
def test_register_new_user():
    response = client.post("/users/register", json={"username": "testuser1"})
    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully", "username": "testuser1"}
    assert "testuser1" in registered_users
    assert "testuser1" in user_data_db
    assert user_data_db["testuser1"] == {}

def test_register_existing_user():
    client.post("/users/register", json={"username": "testuser2"})
    response = client.post("/users/register", json={"username": "testuser2"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists"}

def test_register_user_invalid_payload():
    response = client.post("/users/register", json={})
    assert response.status_code == 422 # Ошибка валидации FastAPI

def test_get_all_users_empty():
    response = client.get("/users/all")
    assert response.status_code == 200
    assert response.json() == {"registered_users": []}

def test_get_all_users_with_data():
    client.post("/users/register", json={"username": "userA"})
    client.post("/users/register", json={"username": "userB"})
    response = client.get("/users/all")
    assert response.status_code == 200
    # Сортируем тк порядок может случайно быть не тем
    assert sorted(response.json()["registered_users"]) == sorted(["userA", "userB"])

# Тесты для загрузки CSV
def test_upload_csv_new_user_not_found():
    files = {'file': ('test.csv', 'col1,col2\nval1,val2', 'text/csv')}
    response = client.post("/users/nonexistentuser/data/mydataset", files=files)
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_upload_csv_invalid_file_type():
    client.post("/users/register", json={"username": "uploaduser"})
    files = {'file': ('test.txt', 'some text', 'text/plain')}
    response = client.post("/users/uploaduser/data/mydataset", files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type. Please upload a .csv file."}

def test_upload_csv_success():
    username = "csvuser"
    dataset_name = "report"
    client.post("/users/register", json={"username": username})
    
    csv_content = "ID,Name\n1,Alice\n2,Bob"
    files = {'file': ('data.csv', csv_content, 'text/csv')}
    
    response = client.post(f"/users/{username}/data/{dataset_name}", files=files)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == f"Dataset '{dataset_name}' uploaded successfully for user '{username}'"
    assert response_data["username"] == username
    assert response_data["dataset_name"] == dataset_name
    assert response_data["rows_processed"] == 2
    assert dataset_name in user_data_db[username]
    expected_parsed_data = [
        {"ID": "1", "Name": "Alice"},
        {"ID": "2", "Name": "Bob"}
    ]
    assert user_data_db[username][dataset_name] == expected_parsed_data

def test_upload_csv_empty_file():
    username = "emptycsvuser"
    dataset_name = "empty_report"
    client.post("/users/register", json={"username": username})
    
    csv_content = ""
    files = {'file': ('empty.csv', csv_content, 'text/csv')}
    
    response = client.post(f"/users/{username}/data/{dataset_name}", files=files)
    assert response.status_code == 200
    assert response.json()["rows_processed"] == 0
    assert user_data_db[username][dataset_name] == []

def test_upload_csv_only_header():
    username = "headeronlyuser"
    dataset_name = "header_report"
    client.post("/users/register", json={"username": username})
    
    csv_content = "Header1,Header2"
    files = {'file': ('header.csv', csv_content, 'text/csv')}
    
    response = client.post(f"/users/{username}/data/{dataset_name}", files=files)
    assert response.status_code == 200
    assert response.json()["rows_processed"] == 0
    assert user_data_db[username][dataset_name] == []

# Тесты для получения списка наборов данных пользователя
def test_get_user_datasets_user_not_found():
    response = client.get("/users/nosuchuser/datasets")
    assert response.status_code == 404

def test_get_user_datasets_empty():
    client.post("/users/register", json={"username": "userX"})
    response = client.get("/users/userX/datasets")
    assert response.status_code == 200
    assert response.json() == {"username": "userX", "available_datasets": []}

def test_get_user_datasets_with_data():
    username = "userY"
    client.post("/users/register", json={"username": username})
    client.post(f"/users/{username}/data/data1", files={'file': ('d1.csv', 'h\nv', 'text/csv')})
    client.post(f"/users/{username}/data/data2", files={'file': ('d2.csv', 'h\nv', 'text/csv')})
    
    response = client.get(f"/users/{username}/datasets")
    assert response.status_code == 200
    # Порядок не гарантирован, поэтому сортируем
    assert sorted(response.json()["available_datasets"]) == sorted(["data1", "data2"])

# Тесты для получения конкретного набора данных
def test_get_named_user_data_user_not_found():
    response = client.get("/users/nosuchuser/data/somedata")
    assert response.status_code == 404

def test_get_named_user_data_dataset_not_found():
    username = "userZ"
    client.post("/users/register", json={"username": username})
    response = client.get(f"/users/{username}/data/nosuchdataset")
    assert response.status_code == 404

def test_get_named_user_data_success():
    username = "userW"
    dataset_name = "final_report"
    client.post("/users/register", json={"username": username})
    
    csv_content = "Key,Value\nK1,V1"
    files = {'file': (f'{dataset_name}.csv', csv_content, 'text/csv')}
    client.post(f"/users/{username}/data/{dataset_name}", files=files)
    
    response = client.get(f"/users/{username}/data/{dataset_name}")
    assert response.status_code == 200
    expected_data = [{"Key": "K1", "Value": "V1"}]
    assert response.json() == expected_data