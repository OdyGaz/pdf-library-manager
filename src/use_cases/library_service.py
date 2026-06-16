import os
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
        """
        Διαγράφει το βιβλίο από τη βάση και τη μικρογραφία του.
        Αν delete_physical=True, στέλνει το πραγματικό αρχείο PDF στον Κάδο Ανακύκλωσης.
        """
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
        """Καθαρίζει ολόκληρη τη βιβλιοθήκη (μόνο βάση και thumbnails, όχι τα PDF του χρήστη)"""
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
