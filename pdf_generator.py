"""
pdf_generator.py
Generates a filled Utah Real Estate REPC Addendum PDF matching the official Edge Homes format.
"""

import os
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import textwrap

OUTPUT_DIR = Path(os.getenv("ADDENDUM_OUTPUT_DIR", "/tmp/addendum-downloads"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def checkbox(c, x, y, checked=False, size=9):
    c.rect(x, y - 1, size, size)
    if checked:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 1, y, "X")


def generate_addendum(data: dict) -> str:
    num         = data.get("addendum_number", "___")
    is_counter  = data.get("doc_type", "addendum").lower() == "counteroffer"
    ref_date    = data.get("offer_ref_date", "")
    buyer       = data.get("buyer_name", "")
    seller      = data.get("seller_name", "Edge Homes Utah, LLC")
    address     = data.get("property_address", "")
    terms_raw   = data.get("terms", "")
    accept_time = data.get("accept_time", "")
    accept_date = data.get("accept_date", "")

    safe_buyer = buyer.split()[0] if buyer else "draft"
    filename = OUTPUT_DIR / f"addendum_{num}_{safe_buyer}.pdf"

    c = canvas.Canvas(str(filename), pagesize=letter)
    W, H = letter
    ML = 0.85 * inch
    MR = W - 0.85 * inch
    CW = MR - ML
    y = H - 0.65 * inch

    def nl(pts=13):
        nonlocal y
        y -= pts

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, y, f"ADDENDUM NO. {num}")
    nl(17)
    c.drawCentredString(W / 2, y, "TO REAL ESTATE PURCHASE CONTRACT")
    nl(20)

    c.setFont("Helvetica-Bold", 10)
    x = ML
    c.drawString(x, y, "THIS IS AN ")
    x += c.stringWidth("THIS IS AN ", "Helvetica-Bold", 10)
    checkbox(c, x, y, checked=not is_counter)
    x += 13
    c.drawString(x, y, " ADDENDUM ")
    x += c.stringWidth(" ADDENDUM ", "Helvetica-Bold", 10)
    checkbox(c, x, y, checked=is_counter)
    x += 13
    c.drawString(x, y, " COUNTEROFFER")
    x += c.stringWidth(" COUNTEROFFER", "Helvetica-Bold", 10)
    c.setFont("Helvetica", 10)
    rest = f' to that REAL ESTATE PURCHASE CONTRACT (the "REPC") with a Reference'
    if x + c.stringWidth(rest, "Helvetica", 10) > MR:
        nl(13)
        c.drawString(ML, y, rest.strip())
    else:
        c.drawString(x, y, rest)
    nl(13)

    date_label = "Date of "
    c.setFont("Helvetica", 10)
    c.drawString(ML, y, date_label)
    x = ML + c.stringWidth(date_label, "Helvetica", 10)
    c.drawString(x, y, ref_date)
    date_w = c.stringWidth(ref_date, "Helvetica", 10)
    c.line(x, y - 1, x + max(date_w, 100), y - 1)
    x2 = x + max(date_w, 100) + 4
    c.drawString(x2, y, " including all prior addenda and counteroffers, between")
    nl(13)

    c.drawString(ML, y, buyer)
    buyer_w = c.stringWidth(buyer, "Helvetica", 10)
    c.line(ML, y - 1, ML + max(buyer_w, 180), y - 1)
    x2 = ML + max(buyer_w, 180) + 4
    c.drawString(x2, y, " as Buyers, and")
    nl(13)

    c.drawString(ML, y, seller)
    sel_w = c.stringWidth(seller, "Helvetica", 10)
    c.line(ML, y - 1, ML + max(sel_w, 160), y - 1)
    x2 = ML + max(sel_w, 160) + 4
    c.drawString(x2, y, " as Seller, regarding the Property located at")
    nl(13)

    avg_char = c.stringWidth("n", "Helvetica", 10)
    max_chars = int(CW / avg_char)
    addr_lines = textwrap.wrap(address + ".", width=max_chars)
    for addr_line in addr_lines:
        c.drawString(ML, y, addr_line)
        c.line(ML, y - 1, MR, y - 1)
        nl(13)
    nl(3)

    c.drawString(ML, y, "The following items are hereby incorporated as part of the REPC:")
    nl(16)

    c.setFont("Helvetica", 10)
    for line in terms_raw.strip().split("\n"):
        if not line.strip():
            nl(6)
            continue
        wrapped = textwrap.wrap(line.strip(), width=85)
        for i, wl in enumerate(wrapped):
            indent = 15 if i > 0 else 0
            c.drawString(ML + indent, y, wl)
            nl(13)
    nl(8)

    c.setFont("Helvetica-Bold", 10)
    deadlines_title = (
        "BUYER AND SELLER AGREE THAT THE CONTRACT DEADLINES REFERENCED IN SECTION 39 OF"
        " THE REPC (CHECK APPLICABLE BOX):"
    )
    for line in textwrap.wrap(deadlines_title, width=85):
        c.drawString(ML, y, line)
        nl(13)

    x = ML
    checkbox(c, x, y, checked=True)
    x += 13
    c.drawString(x, y, " REMAIN UNCHANGED")
    x += c.stringWidth(" REMAIN UNCHANGED", "Helvetica-Bold", 10) + 10
    checkbox(c, x, y, checked=False)
    x += 13
    c.drawString(x, y, " ARE CHANGED AS FOLLOWS:")
    nl(16)

    c.line(ML, y, MR, y)
    nl(16)
    c.line(ML, y, MR, y)
    nl(20)

    c.setFont("Helvetica", 10)
    boiler = (
        "To the extent the terms of this addendum modify or conflict with any provisions of the REPC, "
        "including all prior addenda and counteroffers, these terms shall control. All other terms of the "
        "REPC, including all prior addenda and counteroffers, not modified by this addendum shall remain the same."
    )
    for line in textwrap.wrap(boiler, width=95):
        c.drawString(ML, y, line)
        nl(13)
    nl(8)

    def ul(text, x_pos, font="Helvetica", size=10):
        w = c.stringWidth(text, font, size)
        c.setFont(font, size)
        c.drawString(x_pos, y, text)
        c.line(x_pos, y - 1, x_pos + w, y - 1)
        return x_pos + w

    time_str = accept_time if accept_time and accept_time != "N/A" else "_________"
    date_str = accept_date if accept_date and accept_date != "N/A" else "_____________"

    x = ML
    x = ul("Seller", x)
    c.drawString(x, y, " shall have until ")
    x += c.stringWidth(" shall have until ", "Helvetica", 10)
    x = ul(time_str, x)
    c.drawString(x, y, " Mountain Time on ")
    x += c.stringWidth(" Mountain Time on ", "Helvetica", 10)
    x = ul(date_str, x)
    c.drawString(x, y, " to accept the terms of this addendum in accordance with the")
    nl(13)
    c.drawString(ML, y, "provisions of Section 36 of the REPC. Unless so accepted, the offer as set forth in this ")
    x = ML + c.stringWidth("provisions of Section 36 of the REPC. Unless so accepted, the offer as set forth in this ", "Helvetica", 10)
    x = ul("addendum", x)
    c.drawString(x, y, " shall lapse.")
    nl(20)

    col1_x = ML
    col2_x = ML + CW / 2 + 10
    sig_width = CW / 2 - 20

    for col_x in [col1_x, col2_x]:
        c.line(col_x, y, col_x + sig_width, y)
    nl(11)
    c.setFont("Helvetica", 8)

    buyers = [b.strip() for b in buyer.replace(" and ", "|").split("|")]
    buyer1 = buyers[0] if len(buyers) > 0 else ""
    buyer2 = buyers[1] if len(buyers) > 1 else ""

    c.drawString(col1_x, y, buyer1)
    if buyer2:
        c.drawString(col2_x, y, buyer2)
    nl(8)
    c.setFont("Helvetica", 8)
    for col_x in [col1_x, col2_x]:
        c.drawString(col_x, y, "(date)")
        c.drawString(col_x + 55, y, "(time)")
    nl(25)

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, y, "ACCEPTANCE/COUNTEROFFER/REJECTION")
    nl(16)

    c.setFont("Helvetica", 10)
    x = ML
    checkbox(c, x, y, checked=False)
    x += 13
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, " ACCEPTANCE:")
    x += c.stringWidth(" ACCEPTANCE:", "Helvetica-Bold", 10)
    c.setFont("Helvetica", 10)
    c.drawString(x, y, " Seller hereby accepts the terms of this addendum.")
    nl(14)

    x = ML
    checkbox(c, x, y, checked=False)
    x += 13
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, " COUNTEROFFER:")
    x += c.stringWidth(" COUNTEROFFER:", "Helvetica-Bold", 10)
    c.setFont("Helvetica", 10)
    c.drawString(x, y, " Seller presents as a counteroffer the terms of attached ADDENDUM NO. ______.")
    nl(14)

    x = ML
    checkbox(c, x, y, checked=False)
    x += 13
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, " REJECTION:")
    x += c.stringWidth(" REJECTION:", "Helvetica-Bold", 10)
    c.setFont("Helvetica", 10)
    c.drawString(x, y, " Seller hereby rejects the foregoing addendum.")
    nl(20)

    c.line(ML, y, ML + 160, y)
    c.line(ML + 175, y, ML + 255, y)
    c.line(ML + 270, y, ML + 330, y)
    nl(10)
    c.setFont("Helvetica", 8)
    c.drawString(ML, y, "(date)")
    c.drawString(ML + 175, y, "(date)")
    c.drawString(ML + 270, y, "(time)")
    nl(30)

    footer_y = 0.9 * inch
    box_w, box_h = 40, 30
    spacing = CW / 3

    for i, label in enumerate(["Initials", "Initials", "Seller"]):
        bx = ML + i * spacing
        c.rect(bx, footer_y, box_w, box_h)
        c.setFont("Helvetica", 7)
        c.line(bx, footer_y - 8, bx + box_w + 40, footer_y - 8)
        c.drawString(bx, footer_y - 18, "(initials)")
        c.drawString(bx + box_w + 5, footer_y - 18, label)

    c.setFont("Helvetica", 8)
    c.drawString(ML, 0.5 * inch, "Page 1 of 1")
    c.save()
    return str(filename)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            with open(sys.argv[1]) as f:
                data = json.load(f)
    else:
        data = {
            "addendum_number": "2",
            "doc_type": "addendum",
            "offer_ref_date": "04/02/2026",
            "buyer_name": "Bryson Anderson and Ashley Anderson",
            "seller_name": "Edge Homes Utah, LLC",
            "property_address": "554 S 2650 West St, Lehi, UT 84043",
            "terms": "1. Purchase price to be $903,900.\n2. All other terms remain the same.",
            "accept_time": "",
            "accept_date": "",
        }
    out = generate_addendum(data)
    print(out)
