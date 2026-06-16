import os
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import tkinter as tk
from tkinter import filedialog
from src.infrastructure.db.connection import get_db
from src.use_cases.library_service import LibraryServiceUseCase
from src.use_cases.scanner import PDFScannerUseCase

router = APIRouter()
templates = Jinja2Templates(directory="src/presentation/web/templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    service = LibraryServiceUseCase(db)
    books = service.get_all_books()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"books": books}
    )

@router.post("/import")
def import_pdfs(directory: str = Form(...), db: Session = Depends(get_db)):
    thumbnail_dir = "data/thumbnails"
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    scanner = PDFScannerUseCase(db, thumbnail_dir)
    try:
        imported = scanner.scan_directory(directory)
        return RedirectResponse(url=f"/?success=true&imported={imported}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@router.get("/api/browse-folder")
def browse_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory()
    root.destroy()
    return {"path": folder_path}

@router.post("/books/{book_id}/open-local")
def open_local_pdf(book_id: int, db: Session = Depends(get_db)):
    """Ανοίγει το PDF αρχείο με την προεπιλεγμένη εφαρμογή των Windows"""
    service = LibraryServiceUseCase(db)
    book = service.get_book_by_id(book_id)
    if not book or not os.path.exists(book.file_path):
        return {"status": "error", "message": "Το αρχείο PDF δεν βρέθηκε."}
    
    try:
        if hasattr(os, "startfile"):
            os.startfile(book.file_path)
        else:
            # Fallback για Linux/MacOS αν χρειαστεί
            import subprocess
            import platform
            if platform.system() == "Darwin":
                subprocess.run(["open", book.file_path])
            else:
                subprocess.run(["xdg-open", book.file_path])
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/books/{book_id}/delete")
def delete_book(book_id: int, delete_physical: bool = Form(False), db: Session = Depends(get_db)):
    """Αφαιρεί το βιβλίο από τη βιβλιοθήκη ή το διαγράφει στον Κάδο"""
    service = LibraryServiceUseCase(db)
    success = service.delete_book(book_id, delete_physical=delete_physical)
    if success:
        msg = "Το αρχείο στάλθηκε στον Κάδο Ανακύκλωσης" if delete_physical else "Το βιβλίο αφαιρέθηκε από τη λίστα"
        return RedirectResponse(url=f"/?success=true&msg={msg}", status_code=303)
    return RedirectResponse(url="/?error=Αποτυχία διαγραφής βιβλίου", status_code=303)

@router.post("/library/clear")
def clear_library(db: Session = Depends(get_db)):
    """Καθαρίζει ολόκληρη τη βιβλιοθήκη (μόνο μεταδεδομένα και thumbnails)"""
    service = LibraryServiceUseCase(db)
    service.clear_library()
    return RedirectResponse(url="/?success=true&msg=Η βιβλιοθήκη καθαρίστηκε επιτυχώς", status_code=303)
