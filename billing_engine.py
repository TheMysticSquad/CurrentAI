# ==========================================
# 1. TARIFF CONFIGURATION
# ==========================================
TARIFF_RATES = {
    "DS-II": {
        "fixed_charge_per_kw_per_month": 40.0,
        "slabs": [(100, 6.10), (float('inf'), 6.40)] 
    },
    "NDS-II": {
        "fixed_charge_per_kw_per_month": 150.0,
        "slabs": [(float('inf'), 7.40)] 
    },
    "HTS-I": {
        "fixed_charge_per_kw_per_month": 300.0,
        "slabs": [(float('inf'), 7.00)] 
    },
    "IAS": {
        "fixed_charge_per_kw_per_month": 30.0,
        "slabs": [(float('inf'), 5.50)] 
    }
}

INSTALLMENT_RATE = 250.0 
TOD_MULTIPLIERS = {"Peak": 1.20, "Off-Peak": 0.85, "Normal": 1.0}

# ==========================================
# 2. THE CALCULATION ENGINE
# ==========================================
def calculate_bihar_billing_v2(category: str, units: int, peak_units: int, off_peak_units: int, 
                               load_kw: float, billing_days: int, mode: str, 
                               current_balance: float, installments: int, 
                               dps: float = 0.0, subsidy: float = 0.0, arrears: float = 0.0, arrears_days: int = 0, **kwargs) -> dict:
    
    if category not in TARIFF_RATES:
        category = "DS-II"
    rates = TARIFF_RATES[category]

    # Ensure total units matches the sum of ToD units (fallback safety)
    total_units = max(units, peak_units + off_peak_units)
    normal_units = max(0, total_units - peak_units - off_peak_units)

    # 1. Calculate Base Effective Rate (Using Slabs)
    base_ec = 0.0
    remaining_units = total_units
    for slab_limit, rate in rates["slabs"]:
        if remaining_units > 0:
            units_in_slab = min(remaining_units, slab_limit)
            base_ec += units_in_slab * rate
            remaining_units -= units_in_slab
            
    effective_rate = (base_ec / total_units) if total_units > 0 else 0.0

    # 2. Apply ToD Logic (Mandatory for Prepaid)
    if mode.upper() == "PREPAID":
        ec_normal = normal_units * (effective_rate * TOD_MULTIPLIERS["Normal"])
        ec_peak = peak_units * (effective_rate * TOD_MULTIPLIERS["Peak"])
        ec_off_peak = off_peak_units * (effective_rate * TOD_MULTIPLIERS["Off-Peak"])
    else:
        # If Postpaid without smart meter, standard EC applies
        ec_normal = base_ec
        ec_peak = 0.0
        ec_off_peak = 0.0

    total_energy_charges = ec_normal + ec_peak + ec_off_peak

    # 3. Calculate Fixed Charges (Pro-Rata)
    pro_rata_fixed = (rates["fixed_charge_per_kw_per_month"] * load_kw / 30.0) * billing_days

    
    # 4. Total Installments
    total_installments = installments * INSTALLMENT_RATE
    
    # Auto-Calculate DPS (1.25% per month on Arrears)
    calculated_dps = 0.0
    if arrears > 0 and arrears_days > 0:
        calculated_dps = arrears * 0.0125 * (arrears_days / 30.0)
        
    # Combine any manually stated DPS with the auto-calculated DPS
    final_dps = dps + calculated_dps

    # Auto-Subsidy Logic (From our previous step)
    auto_subsidy = total_units * rates.get("subsidy_per_unit", 0.0)
    final_subsidy_amount = auto_subsidy + subsidy

    # 5. Grand Totals 
    # FIX: We now add `final_dps` and `arrears` to the total!
    total_payable = total_energy_charges + pro_rata_fixed + total_installments + final_dps + arrears - final_subsidy_amount
    total_payable = max(0, total_payable) # Prevent negative bills
    
    # 6. Wallet Deduction Logic
    closing_balance = current_balance
    if mode.upper() == "PREPAID":
        closing_balance = current_balance - total_payable

    return {
        "breakdown": {
            "energy_charges": round(total_energy_charges, 2),
            "tod_breakdown": {
                "normal": round(ec_normal, 2),
                "peak": round(ec_peak, 2),
                "off_peak": round(ec_off_peak, 2)
            },
            "fixed_charges": round(pro_rata_fixed, 2),
            "installments": round(total_installments, 2),
            "dps": round(final_dps, 2), # FIX: Return the final_dps here!
            "subsidy": round(final_subsidy_amount, 2),
            "total_payable": round(total_payable, 2)
        },
        "balance_sheet": {
            "closing": round(closing_balance, 2)
        }
    }