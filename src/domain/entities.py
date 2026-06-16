from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PDFBook:
    """
    Οντότητα που αναπαριστά ένα βιβλίο PDF στο σύστημά μας.
    """
    id: Optional[int]
    title: str
    file_path: str
    thumbnail_path: Optional[str]
    added_at: datetime
    file_size_mb: float
