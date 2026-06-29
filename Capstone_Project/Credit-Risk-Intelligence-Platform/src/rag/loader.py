# src/rag/loader.py
# ============================================================
# Document loader with automatic OCR fallback.
#
# Processing pipeline per document:
#   1. PyMuPDF   — fast text extraction (digital PDFs)
#   2. pypdf     — fallback if PyMuPDF fails
#   3. Tesseract — OCR fallback for image-based / scanned PDFs
#
# OCR is triggered automatically when extracted text is below
# OCR_MIN_CHARS_PER_PAGE characters per page on average.
# Set OCR_ENABLED=false in .env to disable if Tesseract is
# not installed on your system.
# ============================================================

from __future__ import annotations

import re
from pathlib import Path

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Minimum average characters per page before OCR kicks in
_OCR_THRESHOLD = settings.OCR_MIN_CHARS_PER_PAGE


class DocumentLoader:
    """
    Extracts clean text from PDF documents.
    Automatically falls back to Tesseract OCR for scanned/image PDFs.
    """

    def load(self, file_path: str | Path) -> tuple[str, int]:
        """
        Extract text from a PDF file.

        Returns
        -------
        tuple[str, int]
            (cleaned_text, page_count)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        logger.info("Loading document: %s", path.name)

        # Step 1 — PyMuPDF (primary)
        text, page_count = "", 0
        try:
            text, page_count = self._load_with_pymupdf(path)
            logger.debug("PyMuPDF extracted %d chars from %s", len(text), path.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("PyMuPDF failed (%s), trying pypdf", exc)
            try:
                text, page_count = self._load_with_pypdf(path)
                logger.debug("pypdf extracted %d chars", len(text))
            except Exception as exc2:
                logger.error("Both standard loaders failed: %s", exc2)

        # Step 2 — Check if OCR is needed
        if self._needs_ocr(text, page_count):
            logger.info(
                "Document '%s' appears image-based (%.1f chars/page avg). "
                "Attempting Tesseract OCR.",
                path.name,
                len(text) / max(page_count, 1),
            )
            ocr_text, ocr_pages = self._load_with_ocr(path)
            if ocr_text.strip():
                logger.info(
                    "OCR extracted %d chars from %s", len(ocr_text), path.name
                )
                return ocr_text, ocr_pages
            else:
                logger.warning(
                    "OCR produced no text for %s. "
                    "Check Tesseract installation or document quality.",
                    path.name,
                )

        if not text.strip():
            raise RuntimeError(
                f"Could not extract any text from '{path.name}'. "
                "The file may be corrupted or entirely image-based without OCR support."
            )

        return text, page_count

    # ── PyMuPDF ───────────────────────────────────────────────

    def _load_with_pymupdf(self, path: Path) -> tuple[str, int]:
        import fitz  # PyMuPDF

        doc = fitz.open(str(path))
        pages: list[str] = []
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if page_text.strip():
                pages.append(f"[Page {page_num}]\n{page_text}")
        page_count = len(doc)
        doc.close()
        return self._clean_text("\n\n".join(pages)), page_count

    # ── pypdf fallback ────────────────────────────────────────

    def _load_with_pypdf(self, path: Path) -> tuple[str, int]:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"[Page {i}]\n{page_text}")
        return self._clean_text("\n\n".join(pages)), len(reader.pages)

    # ── Tesseract OCR ─────────────────────────────────────────

    def _load_with_ocr(self, path: Path) -> tuple[str, int]:
        """
        Convert each PDF page to an image then run Tesseract OCR.
        Requires: tesseract (system install) + pytesseract + pdf2image.
        """
        if not settings.OCR_ENABLED:
            logger.info("OCR disabled in settings (OCR_ENABLED=false). Skipping.")
            return "", 0

        try:
            import pytesseract
            from pdf2image import convert_from_path

            # Set custom Tesseract path if provided (needed on Windows)
            if settings.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

            # Convert PDF pages to PIL images at 300 DPI for good OCR quality
            images = convert_from_path(str(path), dpi=300)
            pages: list[str] = []

            for i, image in enumerate(images, start=1):
                # Run Tesseract — 'eng' language, PSM 3 (fully automatic page segmentation)
                page_text = pytesseract.image_to_string(
                    image, lang="eng", config="--psm 3"
                )
                if page_text.strip():
                    pages.append(f"[Page {i} — OCR]\n{page_text}")
                logger.debug("OCR page %d: %d chars", i, len(page_text))

            return self._clean_text("\n\n".join(pages)), len(images)

        except ImportError as exc:
            logger.error(
                "OCR dependencies missing: %s\n"
                "Install with: pip install pytesseract pdf2image Pillow\n"
                "Then install Tesseract: see TESSERACT_INSTALL.md",
                exc,
            )
            return "", 0
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Tesseract OCR failed for %s: %s\n"
                "Is Tesseract installed? Run: tesseract --version",
                path.name,
                exc,
            )
            return "", 0

    # ── Helpers ───────────────────────────────────────────────

    def _needs_ocr(self, text: str, page_count: int) -> bool:
        """
        Returns True if the extracted text is suspiciously sparse,
        indicating the PDF is likely image-based (scanned).
        """
        if not settings.OCR_ENABLED:
            return False
        if page_count == 0:
            return True
        avg_chars = len(text.strip()) / page_count
        return avg_chars < _OCR_THRESHOLD

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalise whitespace and strip non-printable characters."""
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)
        return text.strip()
