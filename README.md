# PDF Library Manager

Μια σύγχρονη, τοπική (local) Web εφαρμογή γραμμένη σε Python για την αυτόματη οργάνωση αρχείων PDF σε ψηφιακή βιβλιοθήκη. Η εφαρμογή σαρώνει φακέλους, εξάγει αυτόματα την πρώτη σελίδα κάθε PDF ως εξώφυλλο (thumbnail) και επιτρέπει τη διαχείριση της βιβλιοθήκης μέσω ενός κομψού Neumorphic περιβάλλοντος εργασίας.

## 🌟 Χαρακτηριστικά

* **Ενσωματωμένος Folder Browser:** Επιλογή φακέλου απευθείας από το σύστημα αρχείων σας με το εγγενές παράθυρο διαλόγου (native folder dialog) των Windows.
* **Αυτόματη Εξαγωγή Εξωφύλλων:** Υψηλής ταχύτητας μετατροπή της 1ης σελίδας κάθε PDF σε εικόνα PNG (μέσω PyMuPDF).
* **Άνοιγμα στο Default App:** Κάνοντας κλικ στο εξώφυλλο, το PDF ανοίγει απευθείας στην προεπιλεγμένη εφαρμογή ανάγνωσης του υπολογιστή σας (π.χ. Adobe Acrobat, Edge).
* **Ασφαλής Διαγραφή (Κάδος):** Επιλογή για αφαίρεση του βιβλίου μόνο από τη λίστα ή για πλήρη διαγραφή και μεταφορά του φυσικού αρχείου PDF στον **Κάδο Ανακύκλωσης** (Recycle Bin) των Windows.
* **Καθαρισμός Βιβλιοθήκης:** Δυνατότητα αδειάσματος της λίστας και των thumbnails με ένα κλικ, χωρίς να επηρεαστούν τα αρχικά σας PDF.
* **Neumorphic UI:** Μοντέρνα σχεδίαση βασισμένη σε συγκεκριμένη χρωματική παλέτα (`#EAEAEA` για το background, `#26282B` για τα στοιχεία/κείμενα και `#FF555D` ως χρώμα έμφασης).

---

## 🏗️ Αρχιτεκτονική (Clean Architecture)

Η εφαρμογή ακολουθεί τις αρχές της **Καθαρής Αρχιτεκτονικής (Clean Architecture)** και τις αρχές **SOLID**, διασφαλίζοντας την αποσύνδεση της επιχειρηματικής λογικής από εξωτερικά εργαλεία και βιβλιοθήκες.

1. **Domain Layer (`src/domain`):** Περιλαμβάνει τις καθαρές οντότητες (Data Classes) της εφαρμογής χωρίς καμία εξωτερική εξάρτηση.
2. **Use Cases / Application Layer (`src/use_cases`):** Περιέχει τους κανόνες λειτουργίας (σάρωση φακέλου, διαγραφή βιβλίου, υπηρεσίες βιβλιοθήκης).
3. **Infrastructure Layer (`src/infrastructure`):** Υλοποιεί τις συνδέσεις με εξωτερικά εργαλεία (SQLite, SQLAlchemy ORM, PyMuPDF, Send2Trash).
4. **Presentation Layer (`src/presentation`):** Διαχειρίζεται το UI και το API (FastAPI, Jinja2 Templates, HTML/CSS).

---

## 📂 Δομή Project

```text
pdf-library-manager/
├── pyproject.toml              # Αρχείο ρυθμίσεων Poetry και εξαρτήσεων (dependencies)
├── poetry.lock                 # Κλειδωμένες εκδόσεις πακέτων για σταθερότητα
├── README.md                   # Τεκμηρίωση του project
├── data/                       # Τοπικός φάκελος δεδομένων (εκτός κώδικα)
│   ├── library.db              # Η τοπική βάση δεδομένων SQLite (παράγεται αυτόματα)
│   └── thumbnails/             # Φάκελος αποθήκευσης των εξωφύλλων των PDF σε μορφή PNG
└── src/                        # Ο κύριος φάκελος με τον πηγαίο κώδικα (Source Layout)
    ├── __init__.py
    ├── main.py                 # Το σημείο εισόδου της εφαρμογής (FastAPI startup)
    │
    ├── domain/                 # 1. Επίπεδο Τομέα (Domain Layer - Επιχειρηματικοί Κανόνες)
    │   ├── __init__.py
    │   └── entities.py         # Καθαρές κλάσεις/οντότητες Python (π.χ. PDFBook)
    │
    ├── use_cases/              # 2. Επίπεδο Χρήσης (Application Layer - Use Cases)
    │   ├── __init__.py
    │   ├── scanner.py          # Λογική σκαναρίσματος φακέλου για νέα PDF
    │   └── library_service.py  # Διαχείριση της βιβλιοθήκης (ανάκτηση, διαγραφή, ενημέρωση)
    │
    ├── infrastructure/         # 3. Επίπεδο Υποδομής (Infrastructure Layer - Εξωτερικά Εργαλεία)
    │   ├── __init__.py
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── connection.py   # Ρύθμιση της SQLite σύνδεσης με SQLAlchemy 2.0
    │   │   ├── models.py       # Τα ORM Μοντέλα της βάσης δεδομένων
    │   │   └── repository.py   # Υλοποίηση των CRUD λειτουργιών στη βάση
    │   └── pdf/
    │       ├── __init__.py
    │       └── extractor.py    # Υλοποίηση εξαγωγής εξωφύλλου (PyMuPDF / fitz)
    │
    └── presentation/           # 4. Επίπεδο Παρουσίασης (Presentation Layer - UI / API)
        ├── __init__.py
        └── web/
            ├── __init__.py
            ├── router.py       # Τα Endpoints του FastAPI
            ├── static/         # Στατικά αρχεία (CSS, JS)
            │   └── css/
            │       └── style.css # Neumorphic styling με τα χρώματα #EAEAEA, #26282B, #FF555D
            └── templates/      # HTML Templates (Jinja2)
                └── index.html  # Το κύριο interface της βιβλιοθήκης μας
```

---

## 🛠️ Τεχνολογική Στοίβα (Tech Stack)

* **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Ασύγχρονο, γρήγορο, βασισμένο σε Python type hints)
* **Database ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) με **SQLite** (Τοπική αποθήκευση, δεν απαιτείται εγκατάσταση server)
* **PDF Processing:** [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) (Εξαιρετικά γρήγορη εξαγωγή εξωφύλλων)
* **File Recycling:** [Send2Trash](https://github.com/arsenetar/send2trash) (Ασφαλής μεταφορά αρχείων στον Κάδο Ανακύκλωσης των Windows)
* **Frontend:** HTML5, CSS3 (Custom Neumorphic Shadows), Tailwind CSS (Layout/Grid), Jinja2 Templates