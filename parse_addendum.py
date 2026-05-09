"""
parse_addendum.py
Extracts fields from an existing addendum PDF using pdfplumber.
Handles both our generated PDFs and DocuSign-signed PDFs.
"""

import pdfplumber
import re
from PIL import Image
import pytesseract

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tiff"}


def extract_fields(file_path: str) -> dict:
    ext = "." + file_path.rsplit(".", 1)[-1].lower()

    if ext in IMAGE_EXTENSIONS:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
    else:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    data = {}

    m = re.search(r'ADDENDUM NO[.\s_]*\n?\s*(\d+)', text, re.IGNORECASE)
    data["addendum_number"] = m.group(1) if m else ""

    if re.search(r'X\s+COUNTEROFFER|✓\s*COUNTEROFFER', text, re.IGNORECASE):
        data["doc_type"] = "counteroffer"
    else:
        data["doc_type"] = "addendum"

    dates = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', text)
    data["offer_ref_date"] = dates[0] if dates else ""

    m = re.search(r'between\s+(.+?)\s+as Buyers?', text, re.IGNORECASE | re.DOTALL)
    if m:
        data["buyer_name"] = re.sub(r'\s+', ' ', m.group(1)).strip()

    seller_found = None
    parts = re.split(r'as Buyers?,\s*and\s*\n?', text, flags=re.IGNORECASE)
    for part in parts[1:]:
        after = part.strip()
        after = re.sub(r'^(/[^/]+/\s*)+', '', after).strip()
        m = re.match(r'(.+?)\s+as Seller', after, re.IGNORECASE | re.DOTALL)
        if m:
            candidate = re.sub(r'\s+', ' ', m.group(1)).strip()
            if not re.search(r'between|counteroffers|addenda', candidate, re.IGNORECASE):
                seller_found = candidate
                break
    if seller_found:
        data["seller_name"] = seller_found

    m = re.search(r'located at\s+(.+?)\.', text, re.IGNORECASE | re.DOTALL)
    if m:
        data["property_address"] = re.sub(r'\s+', ' ', m.group(1)).strip()

    m = re.search(
        r'incorporated as part of the REPC:\s*\n(.*?)(?:BUYER AND SELLER|To the extent)',
        text, re.IGNORECASE | re.DOTALL
    )
    if m:
        data["terms"] = re.sub(r'\n+', '\n', m.group(1).strip())

    m = re.search(r'have until\s+([\d:]+\s*(?:AM|PM))', text, re.IGNORECASE)
    data["accept_time"] = m.group(1).strip() if m else ""

    m = re.search(r'Mountain Time on\s+([A-Za-z]+\s+\d+\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})', text)
    data["accept_date"] = m.group(1).strip() if m else ""

    return data


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else input("PDF path: ")
    fields = extract_fields(path)
    print(json.dumps(fields, indent=2))
