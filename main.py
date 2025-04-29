from fastapi import FastAPI
import datetime
from routers import auth, chemical
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Chemical Inventory API",
    description="API for managing chemical inventory.",
    version="1.0.1",
    contact={
        "name": "Yashraj221B",
        "email": "developer221b@gmail.com"
    },
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chemical.router, prefix="/chemicals", tags=["chemicals"])

@app.get("/")
def health_check():
    return {
        "status":"OK",
        "time":datetime.datetime.now()
    }