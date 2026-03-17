from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from auth_routes import router as auth_router
from database import init_db
from routes import router

app = FastAPI(title="Expense Tracker")

init_db()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login")
def serve_login():
    return FileResponse(FRONTEND_DIR / "login.html")


app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
