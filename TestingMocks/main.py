import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, status, Body, File, UploadFile, Path
import csv

def parse_csv(csv_string):

    data = []
    lines = csv_string.strip().split("\n")
    if not lines:
        return data
    
    reader = csv.reader(lines)
    header = next(reader)

    for row in reader:
        row_dict = {}
        for col_name, value in zip(header, row):
            row_dict[col_name] = value.strip()
        data.append(row_dict)
    return data


registered_users = set()
user_data_db = {}

router = APIRouter(
    prefix="/users",
    tags=["users_no_password"],
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(username: str = Body(..., embed=True)): 
    """Регистрирует нового пользователя (без пароля)."""
    if username in registered_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    registered_users.add(username) 
    user_data_db[username] = {}    
    return {"message": "User registered successfully", "username": username}

@router.post("/{username}/data/{dataset_name}", status_code=status.HTTP_200_OK)
async def upload_named_user_csv(
    username: str = Path(...), 
    dataset_name: str = Path(...), 
    file: UploadFile = File(...) 
):
    """Загружает CSV файл для пользователя."""
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

@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_users():
    """Возвращает список имен всех зарегистрированных пользователей."""
    return {"registered_users": list(registered_users)} 

@router.get("/{username}/datasets", status_code=status.HTTP_200_OK)
async def get_user_dataset_names(username: str):
    """Возвращает список имен всех наборов данных для пользователя."""
    if username not in registered_users: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    dataset_names = list(user_data_db[username].keys())
    return {"username": username, "available_datasets": dataset_names}

@router.get("/{username}/data/{dataset_name}", status_code=status.HTTP_200_OK)
async def get_named_user_data(username: str, dataset_name: str):
    """Возвращает данные выбранного набора данных для пользователя."""
    if username not in registered_users: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
  
    if dataset_name not in user_data_db[username]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_name}' not found for user '{username}'"
        )
   
    user_specific_data = user_data_db[username][dataset_name]
    return user_specific_data

app = FastAPI(
    title="Simple User Registration",
    description="ayaya",
    version="0.1.1",
)
app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Simple User Registration"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)