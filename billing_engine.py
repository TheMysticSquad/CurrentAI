# ==========================================
# 1. TARIFF CONFIGURATION (MULTI-STATE & HT)
# ==========================================
TARIFF_MASTER = {
    "Bihar": {
        "Domestic": {"fc_per_unit": 40.0, "unit_type": "kW", "slabs": [(100, 6.10), (float('inf'), 6.40)], "subsidy_per_unit": 1.83},
        "Commercial": {"fc_per_unit": 150.0, "unit_type": "kW", "slabs": [(float('inf'), 7.40)], "subsidy_per_unit": 0.0},
        "Industrial": {"fc_per_unit": 300.0, "unit_type": "kVA", "slabs": [(float('inf'), 7.00)], "subsidy_per_unit": 0.0, 
                       "billing_demand_factor": 0.85, "pf_threshold": 0.90, "pf_rebate_threshold": 0.95}
    },
    "Maharashtra": {
        "Domestic": {"fc_per_unit": 115.0, "unit_type": "kW", "slabs": [(100, 5.56), (300, 10.55), (float('inf'), 13.83)], "subsidy_per_unit": 0.0},
        "Commercial": {"fc_per_unit": 450.0, "unit_type": "kW", "slabs": [(float('inf'), 13.60)], "subsidy_per_unit": 0.0},
        "Industrial": {"fc_per_unit": 500.0, "unit_type": "kVA", "slabs": [(float('inf'), 8.50)], "subsidy_per_unit": 0.0, 
                       "billing_demand_factor": 1.0, "pf_threshold": 0.90, "pf_rebate_threshold": 0.95}
    },
    "Delhi": {
        "Domestic": {"fc_per_unit": 40.0, "unit_type": "kW", "slabs": [(200, 3.00), (400, 4.50), (float('inf'), 6.50)], "subsidy_per_unit": 0.0},
        "Commercial": {"fc_per_unit": 250.0, "unit_type": "kW", "slabs": [(float('inf'), 8.50)], "subsidy_per_unit": 0.0},
        "Industrial": {"fc_per_unit": 250.0, "unit_type": "kVA", "slabs": [(float('inf'), 8.00)], "subsidy_per_unit": 0.0, 
                       "billing_demand_factor": 0.85, "pf_threshold": 0.90, "pf_rebate_threshold": 0.95}
    }
}

INSTALLMENT_RATE = 250.0 
TOD_MULTIPLIERS = {"Peak": 1.20, "Off-Peak": 0.80, "Normal": 1.0}
TOD_HOURS = {"Peak": 6.0, "Off-Peak": 8.0, "Normal": 10.0}

# ==========================================
# 2. THE CALCULATION ENGINE
# ==========================================
def calculate_bihar_billing_v2(category: str, units: int, peak_units: int, off_peak_units: int, 
                               load_kw: float, billing_days: int, mode: str, 
                               current_balance: float, installments: int, 
                               dps: float = 0.0, subsidy: float = 0.0, arrears: float = 0.0, arrears_days: int = 0, 
                               state: str = "Bihar", solar_exported_units: int = 0, **kwargs) -> dict:
    
    # 1. Fetch State & Standardize Category
    state_tariffs = TARIFF_MASTER.get(state, TARIFF_MASTER["Bihar"])
    
    if category in ["DS-II", "Domestic"]: category = "Domestic"
    elif category in ["NDS-II", "Commercial"]: category = "Commercial"
    elif category in ["HTS-I", "Industrial", "HT"]: category = "Industrial"
    else: category = "Domestic" 
    
    rates = state_tariffs.get(category, state_tariffs["Domestic"])

    # 🛡️ SAFETY NET & INITIALIZATION
    units = units if units is not None else 0
    solar_exported_units = solar_exported_units if solar_exported_units is not None else 0
    peak_units = peak_units if peak_units is not None else 0
    off_peak_units = off_peak_units if off_peak_units is not None else 0
    load_kw = load_kw if load_kw is not None else 1.0
    billing_days = billing_days if billing_days is not None else 30
    current_balance = current_balance if current_balance is not None else 0.0

    # 🔌 APPLIANCE ESTIMATOR MATH
    if units == 0 and kwargs.get('appliances'):
        calculated_total = 0.0
        for app in kwargs['appliances']:
            qty = app.get('quantity', 1)
            monthly_app_units = (app['watts'] * app['hours_per_day'] * qty * billing_days) / 1000.0
            calculated_total += monthly_app_units
        units = int(calculated_total)

    # ☀️ SOLAR NET METERING GATE
    # Calculate Total Import first (Grid + Solar offset target)
    total_import_units = max(units, peak_units + off_peak_units)
    net_billed_units = max(0, total_import_units - solar_exported_units)
    banked_units = max(0, solar_exported_units - total_import_units)

    # Calculate ToD Split based on Net Billed Units
    reduction_ratio = (net_billed_units / total_import_units) if total_import_units > 0 else 0
    
    # If using appliance estimator, we distribute across slots
    if peak_units == 0 and off_peak_units == 0 and mode.upper() == "PREPAID":
        final_peak = (net_billed_units * (TOD_HOURS["Peak"] / 24.0))
        final_off_peak = (net_billed_units * (TOD_HOURS["Off-Peak"] / 24.0))
    else:
        # If user gave exact ToD, we reduce them proportionally
        final_peak = peak_units * reduction_ratio
        final_off_peak = off_peak_units * reduction_ratio
    
    final_normal = max(0, net_billed_units - final_peak - final_off_peak)

    # ⚡ ENERGY CHARGES (On Net Billed Units Only)
    base_ec = 0.0
    remaining_units = net_billed_units
    for slab_limit, rate in rates["slabs"]:
        if remaining_units > 0:
            units_in_slab = min(remaining_units, slab_limit)
            base_ec += units_in_slab * rate
            remaining_units -= units_in_slab
            
    effective_rate = (base_ec / net_billed_units) if net_billed_units > 0 else 0.0

    if mode.upper() == "PREPAID":
        ec_normal = final_normal * (effective_rate * TOD_MULTIPLIERS["Normal"])
        ec_peak = final_peak * (effective_rate * TOD_MULTIPLIERS["Peak"])
        ec_off_peak = final_off_peak * (effective_rate * TOD_MULTIPLIERS["Off-Peak"])
    else:
        ec_normal = base_ec
        ec_peak = 0.0
        ec_off_peak = 0.0

    total_energy_charges = ec_normal + ec_peak + ec_off_peak

    # 🏭 FIXED CHARGES (LT vs HT)
    pro_rata_fixed = 0.0
    if rates.get("unit_type") == "kVA":
        contract_demand = kwargs.get('contract_demand_kva') or load_kw
        max_demand = kwargs.get('maximum_demand_kva') or load_kw
        chargeable_demand = max(max_demand, contract_demand * rates.get("billing_demand_factor", 0.85))
        pro_rata_fixed = (rates["fc_per_unit"] * chargeable_demand / 30.0) * billing_days
    else:
        pro_rata_fixed = (rates["fc_per_unit"] * load_kw / 30.0) * billing_days

    # 📉 POWER FACTOR PENALTY (HT Only)
    pf_adjustment = 0.0
    if rates.get("unit_type") == "kVA" and kwargs.get('power_factor'):
        pf = kwargs['power_factor']
        if pf < rates["pf_threshold"]:
            pf_adjustment = total_energy_charges * (int(round((rates["pf_threshold"] - pf) / 0.01)) * 0.01)
        elif pf >= rates["pf_rebate_threshold"]:
            pf_adjustment = -(total_energy_charges * (int(round((pf - rates["pf_rebate_threshold"]) / 0.01)) * 0.005))

    # ⚖️ ARREARS, DPS, SUBSIDY & TOTALS
    calculated_dps = (arrears * 0.0125 * (arrears_days / 30.0)) if arrears > 0 else 0
    final_subsidy_amount = (net_billed_units * rates.get("subsidy_per_unit", 0.0)) + subsidy

    total_payable = total_energy_charges + pro_rata_fixed + (installments * INSTALLMENT_RATE) + dps + calculated_dps + arrears + pf_adjustment - final_subsidy_amount
    total_payable = max(0, total_payable) 

    return {
        "breakdown": {
            "solar_offset": round(banked_units, 2),
            "net_billed_units": round(net_billed_units, 2),
            "billed_units": round(total_import_units, 2),
            "billed_peak_units": round(final_peak, 2),
            "billed_off_peak_units": round(final_off_peak, 2),
            "energy_charges": round(total_energy_charges, 2),
            "tod_breakdown": {"normal": round(ec_normal, 2), "peak": round(ec_peak, 2), "off_peak": round(ec_off_peak, 2)},
            "fixed_charges": round(pro_rata_fixed, 2),
            "installments": round(installments * INSTALLMENT_RATE, 2),
            "dps": round(dps + calculated_dps, 2),
            "pf_adjustment": round(pf_adjustment, 2), 
            "subsidy": round(final_subsidy_amount, 2),
            "total_payable": round(total_payable, 2)
        },
        "balance_sheet": {
            "closing": round(current_balance - total_payable, 2)
        }
    }