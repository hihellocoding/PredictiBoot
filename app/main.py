import sys
import os
from fastapi import FastAPI

# Add project root to Python path to enable absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.routers import prediction, international

app = FastAPI()

app.include_router(prediction.router)
app.include_router(international.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to PredictiBoot"}