# addendum-bot

**For Utah real-estate agents who fill out the same addendum over and over.**

An addendum to a Real Estate Purchase Contract is a short, repetitive
document: the same statutory form, the same boilerplate, and a handful of
deal-specific numbers. Agents fill them by hand in a PDF editor, often on a
phone, usually against a deadline -- and a wrong digit in a price or a date is
a legal problem rather than a formatting one.

This moves that job into Discord, where the agent already is. Answer seven
questions and it returns a filled, correctly formatted addendum PDF. Send it a
photo of an addendum that already exists and it reads the terms off that one,
so the next in the chain starts pre-filled instead of blank -- which is the
actual pain, since addenda come in sequences that mostly repeat each other.

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
