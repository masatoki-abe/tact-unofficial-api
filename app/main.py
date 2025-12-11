from fastapi import FastAPI
from .api import endpoints

app = FastAPI(title="TACT Unofficial API")

app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to TACT Unofficial API"}
