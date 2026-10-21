
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

# Default Windows Tesseract installation path.
TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


def extract_text(file_path: str) -> str:
    """Extract text from an image or PDF, including scanned PDFs."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("Leave-letter file not found.")

    suffix = path.suffix.lower()

    if suffix in {".jpg", ".jpeg", ".png"}:
        try:
            with Image.open(path) as image:
                return pytesseract.image_to_string(
                    image.convert("RGB")
                ).strip()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("Unable to read the uploaded image.") from exc

    if suffix == ".pdf":
        reader = PdfReader(str(path))

        # First try to extract embedded text.
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()

        if text:
            return text

        # If the PDF is scanned, convert its pages to images and run OCR.
        try:
            from pdf2image import convert_from_path

            pages = convert_from_path(
                str(path),
                dpi=200,
                first_page=1,
                last_page=min(len(reader.pages), 10),
            )

            return "\n".join(
                pytesseract.image_to_string(page).strip()
                for page in pages
            ).strip()

        except Exception as exc:
            raise ValueError(
                "Could not OCR the scanned PDF. Check that Poppler "
                "and Tesseract are installed correctly."
            ) from exc

    raise ValueError("Unsupported file type.")
