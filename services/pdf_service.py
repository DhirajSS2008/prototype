"""PDF document parsing service using pdfplumber."""

import re
import logging
from datetime import datetime
from typing import Optional
import pdfplumber

logger = logging.getLogger(__name__)

# Common date patterns
DATE_PATTERNS = [
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
    r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4})",
]

# Amount patterns
AMOUNT_PATTERN = re.compile(r"[\$₹€£]?\s*[\d,]+\.?\d{0,2}")

# Category keywords mapping
CATEGORY_KEYWORDS = {
    "Rent & Lease": ["rent", "lease", "property"],
    "Loan EMI": ["emi", "loan", "mortgage", "instalment", "installment"],
    "Supplier Payments": ["supplier", "vendor", "purchase order", "raw material"],
    "Office Supplies": ["stationery", "supplies", "office", "printer", "paper"],
    "Subscriptions": ["subscription", "saas", "monthly plan", "annual plan", "netflix", "aws"],
    "Travel & Transport": ["travel", "flight", "hotel", "taxi", "uber", "fuel", "transport"],
    "Marketing": ["marketing", "ads", "advertising", "campaign", "google ads", "facebook"],
    "Equipment & Tools": ["equipment", "tool", "hardware", "software", "laptop"],
    "Tax & Government": ["tax", "gst", "vat", "government", "excise", "customs"],
    "Health & Medical": ["health", "medical", "hospital", "insurance", "pharmacy"],
    "Entertainment": ["entertainment", "dining", "restaurant", "party"],
    "Legal & Compliance": ["legal", "lawyer", "compliance", "audit"],
}


def categorize_transaction(text: str) -> str:
    """Infer category from transaction text."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return "Other"


def parse_date(text: str) -> Optional[datetime]:
    """Try to parse a date from text."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y",
                        "%d/%m/%y", "%m/%d/%y", "%d %b %Y", "%d %B %Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    return None


def parse_amount(text: str) -> Optional[float]:
    """Extract monetary amount from text."""
    matches = AMOUNT_PATTERN.findall(text)
    amounts = []
    for m in matches:
        cleaned = re.sub(r"[^\d.]", "", m)
        if cleaned and cleaned != ".":
            try:
                amounts.append(float(cleaned))
            except ValueError:
                continue
    return max(amounts) if amounts else None


def extract_transactions_from_pdf(file_path: str) -> list[dict]:
    """Extract transaction data from a bank statement or invoice PDF.
    
    Returns a list of dicts with: date, amount, counterparty, category, confidence, raw_text
    """
    results = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Try extracting tables first (bank statements)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if not row or all(cell is None for cell in row):
                                continue
                            row_text = " | ".join(str(c) for c in row if c)
                            
                            date = None
                            amount = None
                            balance = None
                            counterparty = None
                            confidence = 0.0
                            
                            # Try to find date in first few columns
                            for cell in row[:3]:
                                if cell:
                                    parsed_date = parse_date(str(cell))
                                    if parsed_date:
                                        date = parsed_date
                                        confidence += 0.3
                                        break
                            
                            # Extract all numeric values from the row
<<<<<<< HEAD
=======
                            # Bank statements typically have: Date | Desc | Debit | Credit | Balance
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
                            numeric_values = []
                            for idx, cell in enumerate(row):
                                if cell:
                                    parsed_val = parse_amount(str(cell))
                                    if parsed_val is not None:
                                        numeric_values.append((idx, parsed_val))
                            
                            if len(numeric_values) >= 2:
<<<<<<< HEAD
                                balance = numeric_values[-1][1]
=======
                                # Last numeric column is usually "Balance"
                                balance = numeric_values[-1][1]
                                # Second-to-last (or first) numeric column is the amount
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
                                amount = numeric_values[-2][1]
                                confidence += 0.3
                            elif len(numeric_values) == 1:
                                amount = numeric_values[0][1]
                                confidence += 0.3
                            
                            # Middle columns likely contain description/counterparty
                            desc_cells = [str(c) for c in row[1:-1] if c]
                            if desc_cells:
                                counterparty = " ".join(desc_cells)[:255]
                                confidence += 0.2
                            
                            category = categorize_transaction(row_text)
                            if category != "Other":
                                confidence += 0.2
                            
<<<<<<< HEAD
                            # Determine if it's a credit or debit based on keywords
                            is_credit = any(k in row_text.lower() for k in ["sales", "income", "deposit", "interest", "refund", "credit", "received"])
                            
                            if date or amount is not None:
                                final_amount = abs(amount or 0.0)
                                if not is_credit:
                                    final_amount = -final_amount
                                    
                                results.append({
                                    "date": date,
                                    "amount": final_amount,
=======
                            if date or amount:
                                results.append({
                                    "date": date,
                                    "amount": -abs(amount) if amount else None,
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
                                    "balance": balance,
                                    "counterparty": counterparty,
                                    "category": category,
                                    "confidence": min(confidence, 1.0),
                                    "raw_text": row_text,
                                    "source": "pdf",
                                })
                
                # Fallback: extract text if no tables found
                if not tables:
                    text = page.extract_text()
                    if text:
                        lines = text.split("\n")
                        for line in lines:
                            line = line.strip()
                            if len(line) < 10:
                                continue
                            
                            date = parse_date(line)
                            amount = parse_amount(line)
                            
<<<<<<< HEAD
                            if date and amount is not None:
=======
                            if date and amount:
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
                                confidence = 0.6
                                category = categorize_transaction(line)
                                if category != "Other":
                                    confidence += 0.2
                                
<<<<<<< HEAD
                                is_credit = any(k in line.lower() for k in ["sales", "income", "deposit", "interest", "refund", "credit", "received"])
                                final_amount = abs(amount)
                                if not is_credit:
                                    final_amount = -final_amount
                                    
                                results.append({
                                    "date": date,
                                    "amount": final_amount,
=======
                                results.append({
                                    "date": date,
                                    "amount": -abs(amount),
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
                                    "counterparty": line[:255],
                                    "category": category,
                                    "confidence": min(confidence, 1.0),
                                    "raw_text": line,
                                    "source": "pdf",
                                })
                                
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise
    
    return results
