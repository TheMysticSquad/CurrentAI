# billing_engine.py

def get_tariff_config(category):
    """
    Hardcoded Bihar Tariff 2026-27 (Representative)
    Categories: 
    - DS-II (Domestic Urban)
    - NDS (Non-Domestic/Commercial)
    - IAS (Irrigation/Agriculture)
    - HTS-I (High Tension 11kV)
    """
    tariffs = {
        "DS-II": {"energy_rate": 7.42, "fixed_rate": 40.0, "type": "LT"},
        "NDS-II": {"energy_rate": 8.15, "fixed_rate": 180.0, "type": "LT"},
        "IAS": {"energy_rate": 5.55, "fixed_rate": 90.0, "type": "LT"},
        "HTS-I": {"energy_rate": 7.15, "fixed_rate": 450.0, "type": "HT"}
    }
    # Default to DS-II if category not found
    return tariffs.get(category.upper(), tariffs["DS-II"])

def calculate_bihar_billing_v2(
    category,
    units,
    load_kw,
    billing_days=30,
    peak_units=0,
    off_peak_units=0,
    mode="Prepaid",
    current_balance=0.0,
    installments=0,      # <--- ADD THIS
    **kwargs             # <--- PRO TIP: Add this to prevent future TypeErrors
):
    # 1. Fetch Category Config
    config = get_tariff_config(category)
    rate = config["energy_rate"]
    f_rate = config["fixed_rate"]
    conn_type = config["type"]

    # 2. Fixed Charge Logic
    if conn_type == "LT":
        fixed_charge = (load_kw * f_rate * billing_days) / 30
    else:
        fixed_charge = load_kw * f_rate

    # 3. Energy Charge with ToD
    normal_units = units - peak_units - off_peak_units
    energy_cost = (normal_units * rate) + \
                  (peak_units * rate * 1.10) + \
                  (off_peak_units * rate * 0.80)

    # 4. Installment Logic (New)
    # Assuming each installment is a flat ₹250 for this demo
    installment_total = installments * 250.0

    # 5. Rebates & Taxes
    prepaid_rebate = (energy_cost * 0.03) if mode == "Prepaid" and conn_type == "LT" else 0
    govt_duty = energy_cost * 0.06

    # 6. Final Totals
    total_bill = energy_cost + fixed_charge + govt_duty + installment_total - prepaid_rebate
    new_balance = current_balance - total_bill

    return {
        "meta": {
            "category": category,
            "connection_type": conn_type,
            "fixed_charge_logic": "Pro-rata (Daily)" if conn_type == "LT" else "Monthly Fixed"
        },
        "breakdown": {
            "energy_charges": round(energy_cost, 2),
            "fixed_charges": round(fixed_charge, 2),
            "govt_duty": round(govt_duty, 2),
            "installments": round(installment_total, 2), # Added to breakdown
            "prepaid_rebate": round(prepaid_rebate, 2),
            "total_payable": round(total_bill, 2)
        },
        "balance_sheet": {
            "opening": current_balance,
            "closing": round(new_balance, 2)
        }
    }