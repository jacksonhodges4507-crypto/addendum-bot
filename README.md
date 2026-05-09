# addendum-bot

Discord bot that generates filled REPC addendum PDFs. Slash commands:
- `/addendum` — answer 7 questions, get a PDF.
- `/upload_addendum` — upload a photo or PDF of an existing addendum to pre-fill the next one.

Deployed on Railway. Built with `discord.py` + `reportlab` + `pdfplumber` + `pytesseract`.

---

## Deploy to Railway

1. Push this repo to GitHub (instructions below if you haven't).
2. On Railway, **New Project → Deploy from GitHub repo → addendum-bot**.
3. Set the environment variable in **Variables**:
   - `DISCORD_TOKEN` — from [discord.com/developers/applications](https://discord.com/developers/applications)
4. Railway will detect [`nixpacks.toml`](nixpacks.toml) and install Python + Tesseract + libheif automatically. Deploy.

That's it. No port to configure — this is a worker (background process), not a web service.

---

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in DISCORD_TOKEN
python bot.py
```

You also need `tesseract` installed on your machine for `/upload_addendum` OCR — `winget install UB-Mannheim.TesseractOCR` on Windows.

---

## Files

- [`bot.py`](bot.py) — Discord client and command handlers.
- [`pdf_generator.py`](pdf_generator.py) — builds the PDF with `reportlab`. Output dir is `$ADDENDUM_OUTPUT_DIR` (default `/tmp/addendum-downloads`).
- [`parse_addendum.py`](parse_addendum.py) — extracts fields from existing PDFs/photos via `pdfplumber` + Tesseract OCR.
- [`nixpacks.toml`](nixpacks.toml) — tells Railway to install `tesseract-ocr` and `libheif` system packages.
- [`railway.json`](railway.json) — Railway build/deploy config.
- [`.env.example`](.env.example) — required env vars.
