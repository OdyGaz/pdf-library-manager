import os
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
        clean_path = directory_path.replace("\\", "/").replace("\\", "/")
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
