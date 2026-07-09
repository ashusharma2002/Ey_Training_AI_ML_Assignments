"""
ingest.py
Loads PDF files from a folder and extracts raw text, page by page.
"""

import os
from pypdf import PdfReader


def load_pdfs(folder_path: str):
    """
    Reads all PDFs in a folder and returns a list of dicts:
    [{"source": "file.pdf", "page": 1, "text": "..."}, ...]
    """
    documents = []

    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return documents

    for filename in pdf_files:
        filepath = os.path.join(folder_path, filename)
        print(f"Reading: {filename}")
        reader = PdfReader(filepath)

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:  # skip empty pages
                documents.append({
                    "source": filename,
                    "page": page_num,
                    "text": text
                })

    print(f"Loaded {len(documents)} pages from {len(pdf_files)} PDF(s).")
    return documents


if __name__ == "__main__":
    # Quick manual test: run this file directly to see extracted text
    docs = load_pdfs("data/pdfs")
    for d in docs[:2]:  # print first 2 pages as a sanity check
        print("\n---")
        print(f"Source: {d['source']} | Page: {d['page']}")
        print(d["text"][:300])  # first 300 chars
