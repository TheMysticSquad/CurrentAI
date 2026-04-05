from fpdf import FPDF
import datetime
from billing_engine import TARIFF_MASTER 

def create_bill_pdf(memory: dict, result: dict) -> bytes:
    pdf = FPDF(unit='mm', format='A4')
    pdf.add_page()
    
    # ---------------------------------------------------------
    # DATA EXTRACTION & SAFETY NET
    # ---------------------------------------------------------
    b = result['breakdown']
    
    # Get units from Math Engine (Corrected to handle Solar)
    total_import = b.get('billed_units', 0)
    solar_export = memory.get('solar_exported_units', 0)
    net_units = b.get('net_billed_units', total_import)
    
    peak_units = b.get('billed_peak_units', 0)
    off_peak_units = b.get('billed_off_peak_units', 0)
    
    load = memory.get('load_kw') or memory.get('contract_demand_kva') or 1.0
    category = memory.get('category') or "Domestic"
    state = memory.get('state') or "Bihar"
    days = memory.get('billing_days') or 30
    mode = memory.get('mode', 'Prepaid')
    arrears = memory.get('arrears') or 0.0
    
    state_tariffs = TARIFF_MASTER.get(state, TARIFF_MASTER["Bihar"])
    mapped_cat = category
    if mapped_cat in ["DS-II", "Domestic"]: mapped_cat = "Domestic"
    elif mapped_cat in ["NDS-II", "Commercial"]: mapped_cat = "Commercial"
    elif mapped_cat in ["HTS-I", "Industrial", "HT"]: mapped_cat = "Industrial"
    else: mapped_cat = "Domestic"
    
    rates = state_tariffs.get(mapped_cat, state_tariffs["Domestic"])

    # ---------------------------------------------------------
    # 1. HEADER SECTION
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(0, 10, "VOLTASSIST UTILITY SERVICES", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(100, 100, 100) 
    pdf.cell(0, 6, "ESTIMATED ELECTRICITY BILL INVOICE", ln=True, align='C')
    pdf.ln(5)
    pdf.line(10, 30, 200, 30)
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)

    # ---------------------------------------------------------
    # 2. ACCOUNT & CONSUMER INFORMATION BOX
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, " 1. ACCOUNT DETAILS", border=1, ln=True, fill=True)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, " Bill Issue Date:", border='L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(55, 8, datetime.date.today().strftime('%d %b %Y'))
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, " State:", border='L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(55, 8, state, border='R', ln=True)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, " Tariff Category:", border='L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(55, 8, mapped_cat)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, f" Load/Demand ({rates.get('unit_type', 'kW')}):", border='L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(55, 8, f"{load} {rates.get('unit_type', 'kW')}", border='R', ln=True)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, " Meter Mode:", border='L,B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(55, 8, mode, border='B')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, " Billing Days:", border='L,B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(55, 8, str(days), border='R,B', ln=True)
    pdf.ln(5)

    # ---------------------------------------------------------
    # 3. CONSUMPTION & SOLAR DETAILS BOX
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 2. CONSUMPTION & SOLAR DETAILS", border=1, ln=True, fill=True)

    # Main Unit Row
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 8, " Total Import (Grid Consumption):", border='L')
    pdf.cell(95, 8, f"{total_import} Units", border='R', align='R', ln=True)

    # --- SOLAR CONDITIONAL SECTION ---
    if solar_export > 0:
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(0, 102, 0) # Green for Solar
        pdf.cell(95, 6, " (-) Solar Export (Units Generated):", border='L')
        pdf.cell(95, 6, f"{solar_export} Units", border='R', align='R', ln=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 8, " NET BILLED UNITS:", border='L,B')
        pdf.cell(95, 8, f"{net_units} Units", border='R,B', align='R', ln=True)
    else:
        pdf.cell(190, 0, "", border='T', ln=True)
    # ----------------------------------

    # ToD Breakdown
    if mode.upper() == "PREPAID":
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, " Time of Day (ToD) Breakdown (Net):", border='L,R', ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 6, "   - Peak Hours (1.2x Rate):", border='L')
        pdf.cell(95, 6, f"{peak_units} Units", border='R', align='R', ln=True) 
        pdf.cell(95, 6, "   - Off-Peak Hours (0.80x Rate):", border='L,B')
        pdf.cell(95, 6, f"{off_peak_units} Units", border='R,B', align='R', ln=True)
    pdf.ln(5)

    # ---------------------------------------------------------
    # 4. FINANCIAL BREAKDOWN
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 3. BILLING CALCULATION", border=1, ln=True, fill=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 8, " Description", border=1)
    pdf.cell(50, 8, " Amount (INR)", border=1, align='C', ln=True)

    pdf.set_font("Arial", '', 10)
    def add_row(desc, amount):
        pdf.cell(140, 8, f" {desc}", border='L,R')
        pdf.cell(50, 8, f"{amount:.2f}", border='L,R', align='R', ln=True)

    add_row("Energy Charges (Net EC)", b['energy_charges'])
    add_row(f"Fixed Charges (FC) [{rates.get('unit_type', 'kW')}]", b['fixed_charges'])
    
    pf_adj = b.get('pf_adjustment', 0.0)
    if pf_adj != 0:
        label = "Power Factor Penalty" if pf_adj > 0 else "Power Factor Rebate"
        add_row(label, pf_adj)
    
    if b.get('installments', 0) > 0: add_row("Pending Installments", b['installments'])
    if arrears > 0: add_row("Previous Arrears", arrears)
    if b.get('dps', 0) > 0: add_row("DPS (Penalty)", b['dps'])

    pdf.cell(140, 8, " Government Subsidy", border='L,R')
    pdf.set_text_color(0, 128, 0) if b['subsidy'] > 0 else pdf.set_text_color(0,0,0)
    pdf.cell(50, 8, f"-{b['subsidy']:.2f}" if b['subsidy'] > 0 else "0.00", border='L,R', align='R', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 0, "", border='T', ln=True) 

    # ---------------------------------------------------------
    # 5. TOTALS
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(240, 248, 255)
    pdf.cell(140, 12, " NET AMOUNT PAYABLE", border=1, fill=True)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(50, 12, f"Rs. {b['total_payable']:.2f}", border=1, align='R', fill=True, ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"* Solar Units Carry Forward (Banked): {b.get('solar_offset', 0)} Units", ln=True)
    pdf.cell(0, 5, f"* Current Wallet Balance: Rs. {memory.get('current_balance', 0.0):.2f}", ln=True)
    pdf.cell(0, 5, f"* Projected Closing Balance: Rs. {result['balance_sheet']['closing']:.2f}", ln=True)
    pdf.cell(0, 5, "This is an AI-generated estimate and not a legal tax invoice.", ln=True)

    output = pdf.output(dest='S')
    return output.encode('latin-1') if isinstance(output, str) else bytes(output)