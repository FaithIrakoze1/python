from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from routes import router  
from database import Base, engine

app = FastAPI(title="Expense Tracker")

# Create tables
Base.metadata.create_all(bind=engine)

# -------- FRONTEND SETUP --------
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

# -------- API SETUP --------
app.include_router(router, prefix="/api")
