from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from routes import router
from auth_routes import router as auth_router
from database import Base, engine

app = FastAPI(title="Expense Tracker")

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static"
)

@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login")
def serve_login():
    return FileResponse(FRONTEND_DIR / "login.html")


app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
