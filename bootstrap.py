import os
from pathlib import Path

# Ορισμός της δομής και των περιεχομένων v3
FILES_TO_CREATE = {}

# ----------------- 1. SETTING UP CONFIGS -----------------

FILES_TO_CREATE["pyproject.toml"] = """[tool.poetry]
name = "pdf-library-manager"
version = "0.3.0"
description = "A modern local PDF library organizer with Neumorphic UI"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.110.0"
uvicorn = "^0.28.0"
sqlalchemy = "^2.0.28"
pymupdf = "^1.23.26"
pydantic = "^2.6.4"
jinja2 = "^3.1.3"
aiofiles = "^23.2.1"
python-multipart = "^0.0.9"
send2trash = "^1.8.2"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""

FILES_TO_CREATE["requirements.txt"] = """fastapi>=0.110.0
uvicorn>=0.28.0
sqlalchemy>=2.0.28
pymupdf>=1.23.26
pydantic>=2.6.4
jinja2>=3.1.3
aiofiles>=23.2.1
python-multipart>=0.0.9
send2trash>=1.8.2
"""

# ----------------- 2. DOMAIN LAYER -----------------

FILES_TO_CREATE["src/domain/__init__.py"] = ""

FILES_TO_CREATE["src/domain/entities.py"] = """from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PDFBook:
    \"\"\"
    Οντότητα που αναπαριστά ένα βιβλίο PDF στο σύστημά μας.
    \"\"\"
    id: Optional[int]
    title: str
    file_path: str
    thumbnail_path: Optional[str]
    added_at: datetime
    file_size_mb: float
"""

# ----------------- 3. INFRASTRUCTURE LAYER -----------------

FILES_TO_CREATE["src/infrastructure/__init__.py"] = ""
FILES_TO_CREATE["src/infrastructure/db/__init__.py"] = ""

FILES_TO_CREATE["src/infrastructure/db/connection.py"] = """from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///data/library.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

FILES_TO_CREATE["src/infrastructure/db/models.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float
from src.infrastructure.db.connection import Base

class PDFBookModel(Base):
    __tablename__ = "pdf_books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    file_path = Column(String, unique=True, nullable=False)
    thumbnail_path = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    file_size_mb = Column(Float, nullable=False)
"""

FILES_TO_CREATE["src/infrastructure/db/repository.py"] = """from sqlalchemy.orm import Session
from src.infrastructure.db.models import PDFBookModel
from src.domain.entities import PDFBook

class PDFBookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[PDFBookModel]:
        return self.db.query(PDFBookModel).order_by(PDFBookModel.added_at.desc()).all()

    def get_by_file_path(self, file_path: str) -> PDFBookModel | None:
        return self.db.query(PDFBookModel).filter(PDFBookModel.file_path == file_path).first()

    def get_by_id(self, book_id: int) -> PDFBookModel | None:
        return self.db.query(PDFBookModel).filter(PDFBookModel.id == book_id).first()

    def add(self, book_data: PDFBook) -> PDFBookModel:
        db_book = PDFBookModel(
            title=book_data.title,
            file_path=book_data.file_path,
            thumbnail_path=book_data.thumbnail_path,
            added_at=book_data.added_at,
            file_size_mb=book_data.file_size_mb
        )
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    def delete(self, book_id: int) -> bool:
        book = self.get_by_id(book_id)
        if book:
            self.db.delete(book)
            self.db.commit()
            return True
        return False
"""

FILES_TO_CREATE["src/infrastructure/pdf/__init__.py"] = ""

FILES_TO_CREATE["src/infrastructure/pdf/extractor.py"] = """import fitz  # PyMuPDF
from pathlib import Path

class PDFThumbnailExtractor:
    @staticmethod
    def extract_first_page_as_png(pdf_path: str, output_dir: str) -> str | None:
        try:
            pdf_path_obj = Path(pdf_path)
            if not pdf_path_obj.exists():
                return None

            thumbnail_name = f"{pdf_path_obj.stem}_cover.png"
            output_path = Path(output_dir) / thumbnail_name

            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                return None

            page = doc[0]
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            pix.save(str(output_path))
            doc.close()

            return f"/static/thumbnails/{thumbnail_name}"
        except Exception as e:
            print(f"Σφάλμα κατά την εξαγωγή εξωφύλλου: {e}")
            return None
"""

# ----------------- 4. USE CASES LAYER -----------------

FILES_TO_CREATE["src/use_cases/__init__.py"] = ""

FILES_TO_CREATE["src/use_cases/scanner.py"] = """import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from src.domain.entities import PDFBook
from src.infrastructure.db.repository import PDFBookRepository
from src.infrastructure.pdf.extractor import PDFThumbnailExtractor

class PDFScannerUseCase:
    def __init__(self, db: Session, thumbnail_dir: str):
        self.repo = PDFBookRepository(db)
        self.thumbnail_dir = thumbnail_dir

    def scan_directory(self, directory_path: str) -> int:
        clean_path = directory_path.replace("\\\\", "/").replace("\\\\", "/")
        path = Path(clean_path)
        
        if not path.exists() or not path.is_dir():
            raise ValueError("Η διαδρομή δεν υπάρχει ή δεν είναι έγκυρος φάκελος.")

        imported_count = 0
        for file in path.glob("**/*.pdf"):
            existing = self.repo.get_by_file_path(str(file))
            if existing:
                continue

            file_size_mb = round(file.stat().st_size / (1024 * 1024), 2)

            thumb_path = PDFThumbnailExtractor.extract_first_page_as_png(
                str(file), self.thumbnail_dir
            )

            new_book = PDFBook(
                id=None,
                title=file.stem,
                file_path=str(file),
                thumbnail_path=thumb_path,
                added_at=datetime.utcnow(),
                file_size_mb=file_size_mb
            )

            self.repo.add(new_book)
            imported_count += 1

        return imported_count
"""

FILES_TO_CREATE["src/use_cases/library_service.py"] = """import os
from sqlalchemy.orm import Session
from src.infrastructure.db.repository import PDFBookRepository
from src.infrastructure.db.models import PDFBookModel

class LibraryServiceUseCase:
    def __init__(self, db: Session):
        self.repo = PDFBookRepository(db)

    def get_all_books(self) -> list[PDFBookModel]:
        return self.repo.get_all()

    def get_book_by_id(self, book_id: int) -> PDFBookModel | None:
        return self.repo.get_by_id(book_id)

    def delete_book(self, book_id: int, delete_physical: bool = False) -> bool:
        \"\"\"
        Διαγράφει το βιβλίο από τη βάση και τη μικρογραφία του.
        Αν delete_physical=True, στέλνει το πραγματικό αρχείο PDF στον Κάδο Ανακύκλωσης.
        \"\"\"
        book = self.repo.get_by_id(book_id)
        if not book:
            return False
            
        # Αν ζητηθεί, στέλνουμε το φυσικό αρχείο στον κάδο ανακύκλωσης των Windows
        if delete_physical and os.path.exists(book.file_path):
            try:
                from send2trash import send2trash
                send2trash(book.file_path)
            except Exception as e:
                print(f"Σφάλμα κατά τη μεταφορά του αρχείου στον κάδο: {e}")
                return False

        # Διαγραφή της μικρογραφίας από το δίσκο (αν υπάρχει)
        if book.thumbnail_path:
            relative_thumb_path = book.thumbnail_path.lstrip('/')
            actual_thumb_path = relative_thumb_path.replace("static/thumbnails", "data/thumbnails")
            if os.path.exists(actual_thumb_path):
                try:
                    os.remove(actual_thumb_path)
                except Exception as e:
                    print(f"Σφάλμα κατά τη διαγραφή της μικρογραφίας: {e}")
        
        # Διαγραφή από τη βάση δεδομένων
        return self.repo.delete(book_id)

    def clear_library(self) -> bool:
        \"\"\"Καθαρίζει ολόκληρη τη βιβλιοθήκη (μόνο βάση και thumbnails, όχι τα PDF του χρήστη)\"\"\"
        books = self.repo.get_all()
        for book in books:
            if book.thumbnail_path:
                relative_thumb_path = book.thumbnail_path.lstrip('/')
                actual_thumb_path = relative_thumb_path.replace("static/thumbnails", "data/thumbnails")
                if os.path.exists(actual_thumb_path):
                    try:
                        os.remove(actual_thumb_path)
                    except Exception as e:
                        print(f"Σφάλμα κατά τη διαγραφή της μικρογραφίας: {e}")
            self.repo.delete(book.id)
        return True
"""

# ----------------- 5. PRESENTATION LAYER (WEB UI) -----------------

FILES_TO_CREATE["src/presentation/__init__.py"] = ""
FILES_TO_CREATE["src/presentation/web/__init__.py"] = ""

FILES_TO_CREATE["src/presentation/web/router.py"] = """import os
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
    \"\"\"Ανοίγει το PDF αρχείο με την προεπιλεγμένη εφαρμογή των Windows\"\"\"
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
    \"\"\"Αφαιρεί το βιβλίο από τη βιβλιοθήκη ή το διαγράφει στον Κάδο\"\"\"
    service = LibraryServiceUseCase(db)
    success = service.delete_book(book_id, delete_physical=delete_physical)
    if success:
        msg = "Το αρχείο στάλθηκε στον Κάδο Ανακύκλωσης" if delete_physical else "Το βιβλίο αφαιρέθηκε από τη λίστα"
        return RedirectResponse(url=f"/?success=true&msg={msg}", status_code=303)
    return RedirectResponse(url="/?error=Αποτυχία διαγραφής βιβλίου", status_code=303)

@router.post("/library/clear")
def clear_library(db: Session = Depends(get_db)):
    \"\"\"Καθαρίζει ολόκληρη τη βιβλιοθήκη (μόνο μεταδεδομένα και thumbnails)\"\"\"
    service = LibraryServiceUseCase(db)
    service.clear_library()
    return RedirectResponse(url="/?success=true&msg=Η βιβλιοθήκη καθαρίστηκε επιτυχώς", status_code=303)
"""

FILES_TO_CREATE["src/presentation/web/static/css/style.css"] = """/* Neumorphic Design με χρωματική παλέτα */
body {
    background-color: #EAEAEA;
    color: #26282B;
}

/* Neumorphic Card */
.neumorphic-card {
    background: #EAEAEA;
    box-shadow: 12px 12px 24px #bebebe, 
                -12px -12px 24px #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Neumorphic Input */
.neumorphic-input {
    background: #EAEAEA;
    box-shadow: inset 6px 6px 12px #bebebe, 
                inset -6px -6px 12px #ffffff;
    border: none;
    color: #26282B;
    transition: all 0.3s ease;
}

.neumorphic-input:focus {
    box-shadow: inset 3px 3px 6px #bebebe, 
                inset -3px -3px 6px #ffffff;
}

/* Accent Button (#FF555D) */
.accent-btn {
    background: #FF555D;
    box-shadow: 6px 6px 12px rgba(255, 85, 93, 0.3), 
                -6px -6px 12px #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.accent-btn:hover {
    background: #e04b52;
    box-shadow: 3px 3px 6px rgba(255, 85, 93, 0.4), 
                -3px -3px 6px #ffffff;
}

.accent-btn:active {
    box-shadow: inset 3px 3px 6px rgba(0, 0, 0, 0.2);
}
"""

FILES_TO_CREATE["src/presentation/web/templates/index.html"] = """<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Library Organizer</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        neumorphic_bg: '#EAEAEA',
                        neumorphic_dark: '#26282B',
                        accent: '#FF555D',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-[#EAEAEA] text-[#26282B] min-h-screen font-sans p-6">
    <div class="max-w-6xl mx-auto">
        <!-- Header -->
        <header class="mb-10 text-center">
            <h1 class="text-4xl font-extrabold tracking-tight mb-2 text-[#26282B]">Ψηφιακή Βιβλιοθήκη PDF</h1>
            <p class="text-gray-600">Αυτόματη οργάνωση και προβολή εξωφύλλων</p>
        </header>

        <!-- Import Form -->
        <section class="neumorphic-card p-6 mb-10 rounded-2xl max-w-2xl mx-auto">
            <h2 class="text-xl font-bold mb-4">Εισαγωγή Νέων PDF</h2>
            <form action="/import" method="POST" class="flex flex-col gap-4">
                <div>
                    <label class="block text-sm font-semibold mb-2" for="directory">
                        Επιλογή Φακέλου:
                    </label>
                    <div class="flex gap-3">
                        <input 
                            type="text" 
                            id="directory" 
                            name="directory" 
                            placeholder="Κάντε κλικ στο Browse για επιλογή φακέλου..." 
                            required 
                            class="neumorphic-input flex-grow p-3 rounded-xl focus:outline-none"
                        >
                        <button 
                            type="button" 
                            onclick="browseFolder()" 
                            class="neumorphic-card px-5 py-3 rounded-xl font-bold hover:bg-gray-200 transition-all text-sm"
                        >
                            Browse...
                        </button>
                    </div>
                </div>
                <button type="submit" class="accent-btn py-3 px-6 rounded-xl font-bold text-white transition-all self-end">
                    Σάρωση και Εισαγωγή
                </button>
            </form>
        </section>

        <!-- Notifications -->
        {% if request.query_params.get('success') %}
            <div class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-8 rounded-r-xl shadow-sm max-w-2xl mx-auto" role="alert">
                <p class="font-bold">Επιτυχία!</p>
                {% if request.query_params.get('msg') %}
                    <p>{{ request.query_params.get('msg') }}</p>
                {% elif request.query_params.get('imported') %}
                    <p>Εισήχθησαν επιτυχώς {{ request.query_params.get('imported') }} νέα βιβλία στη βιβλιοθήκη.</p>
                {% else %}
                    <p>Η ενέργεια ολοκληρώθηκε με επιτυχία.</p>
                {% endif %}
            </div>
        {% endif %}
        {% if request.query_params.get('error') %}
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-8 rounded-r-xl shadow-sm max-w-2xl mx-auto" role="alert">
                <p class="font-bold">Σφάλμα</p>
                <p>{{ request.query_params.get('error') }}</p>
            </div>
        {% endif %}

        <!-- Books Grid Header with Clear Button -->
        <main>
            <div class="flex justify-between items-center mb-6 border-b pb-2 border-gray-300">
                <h2 class="text-2xl font-bold">Τα Βιβλία μου ({{ books|length }})</h2>
                {% if books|length > 0 %}
                    <form action="/library/clear" method="POST" onsubmit="return confirm('ΠΡΟΣΟΧΗ: Είστε σίγουροι ότι θέλετε να αδειάσετε ολόκληρη τη βιβλιοθήκη; (Τα πραγματικά PDF αρχεία σας ΔΕΝ θα διαγραφούν).');">
                        <button type="submit" class="text-xs font-bold bg-[#FF555D] text-white px-4 py-2 rounded-xl hover:bg-red-600 transition-all shadow-sm">
                            Καθαρισμός Βιβλιοθήκης
                        </button>
                    </form>
                {% endif %}
            </div>
            
            {% if books|length == 0 %}
                <div class="text-center py-12 text-gray-500">
                    <p class="text-lg">Δεν υπάρχουν ακόμη βιβλία στη βιβλιοθήκη σας.</p>
                    <p class="text-sm">Επιλέξτε έναν φάκελο παραπάνω για να ξεκινήσετε.</p>
                </div>
            {% else %}
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
                    {% for book in books %}
                        <div class="neumorphic-card p-4 rounded-2xl flex flex-col justify-between transition-transform duration-300 hover:scale-105">
                            <!-- Κλικ στο εξώφυλλο για άνοιγμα με την default εφαρμογή -->
                            <div onclick="openLocalPdf({{ book.id }})" class="w-full h-64 bg-[#dfdfdf] rounded-xl mb-4 overflow-hidden relative shadow-inner cursor-pointer" title="Κάντε κλικ για άνοιγμα στα Windows">
                                {% if book.thumbnail_path %}
                                    <img src="{{ book.thumbnail_path }}" alt="{{ book.title }}" class="w-full h-full object-cover">
                                {% else %}
                                    <span class="text-gray-400 text-xs text-center p-2 flex items-center justify-center h-full">Δεν είναι διαθέσιμο εξώφυλλο</span>
                                {% endif %}
                            </div>
                            <div>
                                <h3 class="font-bold text-sm line-clamp-2 text-[#26282B] mb-2 cursor-pointer" onclick="openLocalPdf({{ book.id }})" title="{{ book.title }}">
                                    {{ book.title }}
                                </h3>
                                <div class="flex justify-between items-center text-xs text-gray-500 mb-4">
                                    <span>{{ book.file_size_mb }} MB</span>
                                    <span class="truncate max-w-[120px] text-right" title="{{ book.file_path }}">{{ book.file_path }}</span>
                                </div>
                                
                                <!-- Διπλά Κουμπιά Διαγραφής/Αφαίρεσης -->
                                <div class="flex justify-between items-center border-t pt-2 border-gray-200 gap-2">
                                    <form action="/books/{{ book.id }}/delete" method="POST" onsubmit="return confirm('Θέλετε να αφαιρέσετε αυτό το PDF από τη βιβλιοθήκη; Το αρχείο θα παραμείνει στο PC σας.');">
                                        <input type="hidden" name="delete_physical" value="false">
                                        <button type="submit" class="text-xs font-bold text-gray-500 hover:text-gray-700 transition-all">
                                            Αφαίρεση
                                        </button>
                                    </form>
                                    <form action="/books/{{ book.id }}/delete" method="POST" onsubmit="return confirm('ΠΡΟΣΟΧΗ: Θέλετε να στείλετε το αρχείο PDF στον Κάδο Ανακύκλωσης του υπολογιστή σας;');">
                                        <input type="hidden" name="delete_physical" value="true">
                                        <button type="submit" class="text-xs font-bold text-[#FF555D] hover:underline transition-all">
                                            Διαγραφή (Κάδος)
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        </main>
    </div>

    <!-- Scripts -->
    <script>
        async function browseFolder() {
            try {
                const response = await fetch('/api/browse-folder');
                const data = await response.json();
                if (data.path) {
                    document.getElementById('directory').value = data.path;
                }
            } catch (err) {
                console.error("Σφάλμα κατά την επιλογή φακέλου:", err);
                alert("Αποτυχία ανοίγματος του folder browser.");
            }
        }

        async function openLocalPdf(bookId) {
            try {
                const response = await fetch(`/books/${bookId}/open-local`, { method: 'POST' });
                const data = await response.json();
                if (data.status === 'error') {
                    alert("Σφάλμα κατά το άνοιγμα: " + data.message);
                }
            } catch (err) {
                console.error("Σφάλμα δικτύου:", err);
            }
        }
    </script>
</body>
</html>
"""

# ----------------- 6. ENTRYPOINT -----------------

FILES_TO_CREATE["src/main.py"] = """import os
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
"""


def main():
    print("Ξεκινάει η δημιουργία της αναβαθμισμένης δομής του project (v3)...")
    
    for file_path_str, content in FILES_TO_CREATE.items():
        file_path = Path(file_path_str)
        # Δημιουργία γονικών φακέλων αν δεν υπάρχουν
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Συγγραφή του αρχείου
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Δημιουργήθηκε: {file_path_str}")

    # Δημιουργία του data φακέλου
    os.makedirs("data/thumbnails", exist_ok=True)
    print("Δημιουργήθηκε ο φάκελος: data/thumbnails")
    
    print("\\nΤο αναβαθμισμένο project (v3) δημιουργήθηκε επιτυχώς!")
    print("Βήματα για εκτέλεση:")
    print("1. Εγκαταστήστε τις βιβλιοθήκες: pip install -r requirements.txt")
    print("2. Εκκινήστε την εφαρμογή: python -m src.main")
    print("3. Ανοίξτε τον browser στο: http://127.0.0.1:8000")


if __name__ == "__main__":
    main()