from datetime import datetime
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
