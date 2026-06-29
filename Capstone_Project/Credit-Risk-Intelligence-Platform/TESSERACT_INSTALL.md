# Tesseract OCR — Installation Guide

Tesseract is a free, open-source OCR engine. It must be installed as a
system program (not via pip) before the Credit Risk platform can process
scanned / image-based PDFs.

---

## Do I Need Tesseract?

Only if you plan to upload **scanned PDFs** — documents that are photos
of paper rather than digitally generated PDFs.

**You do NOT need Tesseract for:**
- PDFs exported from Word / Excel
- Digitally generated bank statements
- PDFs downloaded from websites

**You DO need Tesseract for:**
- Scanned physical documents
- Photographed bank statements or ITRs
- PDFs where copy-paste produces gibberish

If you are unsure, set `OCR_ENABLED=false` in your `.env` file. The
platform will still work for all digital PDFs.

---

## Windows Installation

1. Download the installer from the official Windows port:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Run the installer. When asked for install location, use:
   `C:\Program Files\Tesseract-OCR`

3. During installation, check **"Add to system PATH"** if prompted.

4. Open a new Command Prompt and verify:
   ```
   tesseract --version
   ```

5. If the PATH was not added automatically, add it manually:
   - Search "Environment Variables" in Windows Start menu
   - System Properties → Advanced → Environment Variables
   - Under "System variables", find "Path" → Edit → New
   - Add: `C:\Program Files\Tesseract-OCR`
   - Click OK on all dialogs
   - Restart your terminal

6. In your `.env` file, set:
   ```
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

---

## Mac Installation

```bash
brew install tesseract
```

Verify:
```bash
tesseract --version
```

No changes needed in `.env` — auto-detected from PATH.

---

## Ubuntu / Debian Linux

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

Verify:
```bash
tesseract --version
```

No changes needed in `.env` — auto-detected from PATH.

---

## Verify Everything Works

After installation, run this quick test from your project folder:

```bash
python3 -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

Expected output: `5.x.x` or `4.x.x`

If you see an error, Tesseract is not in your PATH. Follow the steps above.

---

## Disable OCR (If You Don't Need It)

In your `.env` file:
```
OCR_ENABLED=false
```

The platform will skip OCR entirely and only process digital PDFs.
