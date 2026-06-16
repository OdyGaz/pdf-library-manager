from sqlalchemy.orm import Session
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
