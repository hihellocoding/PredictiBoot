from fastapi import FastAPI
from .routers import prediction, international

app = FastAPI()

app.include_router(prediction.router)
app.include_router(international.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to PredictiBoot"}
