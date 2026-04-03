import re

def parse_user_query(text):
    text = text.lower()
    extracted = {}

    # Map of "What to look for" : "Regex Pattern"
    patterns = {
        "units": r'(\d+)\s*unit',
        "load_kw": r'(\d+\.?\d*)\s*(kw|load)',
        "billing_days": r'(\d+)\s*day',
        "current_balance": r'(?:balance|credit|wallet|money)\s*(?:of|is)?\s*(\d+)',
        "peak_units": r'(\d+)\s*peak',
        "off_peak_units": r'(\d+)\s*off[- ]?peak',
        "installments": r'(\d+)\s*installment',
        "arrears": r'(?:arrears|due)\s*(?:of)?\s*(\d+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted[key] = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))

    # Categorization Logic
    if any(x in text for x in ["shop", "commercial", "nds"]): extracted["category"] = "NDS-II"
    elif any(x in text for x in ["home", "domestic", "ds"]): extracted["category"] = "DS-II"
    elif any(x in text for x in ["factory", "industrial", "ht"]): extracted["category"] = "HTS-I"
    
    # Mode Logic
    if "postpaid" in text: extracted["mode"] = "Postpaid"
    elif "prepaid" in text: extracted["mode"] = "Prepaid"

    return extracted