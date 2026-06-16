import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.infrastructure.db.connection import engine, Base
from src.presentation.web.router import router as web_router

# Δημιουργία των απαραίτητων φακέλων κατά την εκκίνηση
os.makedirs("data/thumbnails", exist_ok=True)
os.makedirs("src/presentation/web/static/css", exist_ok=True)

# Δημιουργία των πινάκων στη SQLite βάση δεδομένων
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PDF Library Manager")

# Σύνδεση των στατικών αρχείων (CSS και Thumnails)
app.mount("/static/css", StaticFiles(directory="src/presentation/web/static/css"), name="static_css")
app.mount("/static/thumbnails", StaticFiles(directory="data/thumbnails"), name="static_thumbnails")

# Ενσωμάτωση του router
app.include_router(web_router)

if __name__ == "__main__":
    import uvicorn
    print("Η εφαρμογή ξεκινάει στο http://127.0.0.1:8000")
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
