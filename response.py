import re

def parse_user_query(text):
    """
    Extracts key billing parameters from natural language.
    Handles: Category, Units, Load, Mode, and Days.
    """
    text = text.lower()
    
    # 1. Extract Numbers (Units and Load)
    # Looking for: "300 units", "5kw", "2.5 kw", "15 days"
    units = re.search(r'(\d+)\s*unit', text)
    load = re.search(r'(\d+\.?\d*)\s*(kw|load)', text)
    days = re.search(r'(\d+)\s*day', text)
    balance = re.search(r'(balance|wallet)\s*(?:of\s*)?(\d+)', text)
    
    # 2. Identify Category (The "Smart" Mapper)
    category = "DS-II" # Default to Urban Domestic
    if any(word in text for word in ["shop", "commercial", "nds", "office", "business"]):
        category = "NDS-II"
    elif any(word in text for word in ["factory", "industrial", "ht", "hts", "high tension"]):
        category = "HTS-I"
    elif any(word in text for word in ["farm", "irrigation", "agri", "ias"]):
        category = "IAS"

    # 3. Identify Payment Mode
    mode = "Prepaid" # Default
    if "postpaid" in text or "bill after" in text:
        mode = "Postpaid"

    # 4. ToD Extraction (Basic)
    peak = re.search(r'(\d+)\s*peak', text)
    off_peak = re.search(r'(\d+)\s*off[- ]?peak', text)

    return {
        "category": category,
        "units": int(units.group(1)) if units else 0,
        "load_kw": float(load.group(1)) if load else 1.0, # Default 1kW
        "billing_days": int(days.group(1)) if days else 30, # Default 1 month
        "mode": mode,
        "peak_units": int(peak.group(1)) if peak else 0,
        "off_peak_units": int(off_peak.group(1)) if off_peak else 0,
        "current_balance": float(balance.group(2)) if balance else 0.0
    }

