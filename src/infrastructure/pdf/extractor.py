import fitz  # PyMuPDF
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
