from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    retugit rn {"message": "Hello, World!"}