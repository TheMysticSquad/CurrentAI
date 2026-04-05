import streamlit as st
from brain import process_user_input, extract_text_from_pdf, analyze_image_with_vision
from billing_engine import calculate_bihar_billing_v2
from pdf_generator import create_bill_pdf  

st.set_page_config(page_title="VoltAssist AI", page_icon="⚡", layout="wide")

# ==========================================
# 1. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.title("⚡ VoltAssist")
    st.caption("Intelligent Billing Assistant")
    
    # State Selector
    selected_state = st.selectbox("🌍 Select Your State", ["Bihar", "Maharashtra", "Delhi", "Uttar Pradesh", "Karnataka"])
    if "memory" in st.session_state:
        st.session_state.memory["state"] = selected_state

    st.divider()
    
    if st.button("🔄 Start New Chat", use_container_width=True, type="primary"):
        st.session_state.memory = {
            "state": selected_state, "category": None, "units": None, "peak_units": 0, "off_peak_units": 0, 
            "load_kw": None, "billing_days": 30, "mode": "Prepaid", 
            "current_balance": 0.0, "installments": 0, "dps": 0.0, "subsidy": 0.0,
            "arrears": 0.0, "arrears_days": 0, "solar_exported_units": 0,
            "appliances": [], 
            "contract_demand_kva": None, "maximum_demand_kva": None, "power_factor": None,
            "is_complete": False, "follow_up_message": "" 
        }
        st.session_state.history = []
        st.rerun()
        
    st.divider()
    st.subheader("💡 Master Test Scenarios")
    
    sidebar_prompt = None
    
    # --- Grid Layout for Scenarios ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏢 1. Shop (NDS)"):
            sidebar_prompt = "I run a small shop with a 5kw load. We consumed 450 units over the last 30 days."
        if st.button("🏭 3. HT Factory"):
            sidebar_prompt = "Industrial factory in Maharashtra. Contract demand 500kVA, max demand 300kVA. 10,000 units. PF 0.85."
        if st.button("☀️ 5. Solar Net"):
            sidebar_prompt = "I have a 3kW solar setup. I imported 500 units from the grid but exported 200 units back. Domestic Bihar."
        if st.button("💳 7. Installments"):
            sidebar_prompt = "Commercial user in Delhi, 5kW load. 600 units. 4 installments of ₹250 each. Wallet balance is ₹1,200."
        if st.button("🚨 9. HT Overload"):
            sidebar_prompt = "Industrial connection. Contract Demand is 100kVA, but we hit 150kVA Max Demand. 5000 units, PF 0.88. Show penalty."

    with c2:
        if st.button("⏱️ 2. Smart ToD"):
            sidebar_prompt = "I am on Prepaid. I used 500 units total. 100 were peak and 50 were off-peak."
        if st.button("🔌 4. Appliances"):
            sidebar_prompt = "2kw domestic. I don't know my units, but I run two 1.5-ton ACs for 8 hours a day, and 4 ceiling fans for 12 hours a day."
        if st.button("⚖️ 6. DPS Penalty"):
            sidebar_prompt = "Domestic in Bihar, 2kW load. Used 250 units. I have an old unpaid bill (arrears) of ₹4,500 which is 60 days overdue."
        if st.button("🔋 8. Epic Combo"):
            sidebar_prompt = "Bihar Domestic, 3kW. 2 ACs for 8 hours/day. Solar export 150 units. 2 pending installments and an arrear of ₹1,000."
        if st.button("🏆 10. Zero Bill"):
            sidebar_prompt = "Domestic solar user. 5kW load. I imported 300 units but my solar panels exported 450 units. What happens to my bill?"

    st.divider()
    st.subheader("📸 Upload Bill or Meter")
    uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "png", "jpeg"], label_visibility="collapsed")
    
    file_prompt = None
    if uploaded_file is not None:
        if st.button("Extract Data from File", type="primary", use_container_width=True):
            with st.spinner("Analyzing document..."):
                if uploaded_file.name.lower().endswith('.pdf'):
                    extracted_text = extract_text_from_pdf(uploaded_file)
                    file_prompt = f"I uploaded a PDF bill. Here is the raw text extracted from it. Please parse my billing details: {extracted_text}"
                else:
                    vision_text = analyze_image_with_vision(uploaded_file)
                    file_prompt = f"I uploaded a photo of my meter/bill. The Vision AI saw this: {vision_text}. Please parse my billing details from this."
    st.caption("Powered by Llama-3.1")

# ==========================================
# 2. SESSION INITIALIZATION
# ==========================================
if "memory" not in st.session_state:
    st.session_state.memory = {
        "state": "Bihar", "category": None, "units": None, "peak_units": 0, "off_peak_units": 0, 
        "load_kw": None, "billing_days": 30, "mode": "Prepaid", 
        "current_balance": 0.0, "installments": 0, "dps": 0.0, "subsidy": 0.0,
        "arrears": 0.0, "arrears_days": 0, "solar_exported_units": 0,
        "appliances": [], 
        "contract_demand_kva": None, "maximum_demand_kva": None, "power_factor": None,
        "is_complete": False, "follow_up_message": "" 
    }

if "history" not in st.session_state:
    st.session_state.history = []

# ==========================================
# 3. CHAT INTERFACE
# ==========================================
st.title("🤖 Chat with VoltAssist")
st.caption("Enter your billing details in natural language, and the AI will extract the parameters.")

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

chat_input = st.chat_input("Ex: 'I have a shop, used 450 units...'")
prompt = chat_input or sidebar_prompt or file_prompt

if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing through AI Engine..."):
        # STEP A: AI Extraction
        new_memory = process_user_input(prompt, st.session_state.memory)
        st.session_state.memory = new_memory

        # STEP B: The Agentic Check (Safety First)
        mem = st.session_state.memory
        safe_units = mem.get('units') or 0
        safe_appliances = mem.get('appliances') or []
        
        has_energy_data = (safe_units > 0) or (len(safe_appliances) > 0)
        has_load_data = (mem.get('load_kw') is not None) or (mem.get('contract_demand_kva') is not None)
        
        if not mem.get('is_complete') or mem.get('category') is None or not has_load_data or not has_energy_data:
            follow_up = mem.get('follow_up_message') or "Could you please specify your category, load/demand, and units or appliances?"
            with st.chat_message("assistant"):
                st.markdown(f"🤖 **Wait!** {follow_up}")
            st.session_state.history.append({"role": "assistant", "content": f"🤖 **Wait!** {follow_up}"})

        # STEP C: Math Engine & Dashboard
        else:
            try:
                result = calculate_bihar_billing_v2(**st.session_state.memory)
                b = result['breakdown']
                
                with st.chat_message("assistant"):
                    st.markdown(f"**State:** {mem.get('state')} | **Category:** {mem['category']} | **Mode:** {mem['mode']}")
                    
                    # Dashboard Layout
                    solar_val = mem.get('solar_exported_units', 0)
                    cols = st.columns(6 if solar_val > 0 else 5)
                    
                    cols[0].metric("Energy Charges", f"₹{b['energy_charges']}")
                    cols[1].metric("Fixed Charges", f"₹{b['fixed_charges']}")
                    cols[2].metric("DPS (Penalty)", f"₹{b['dps']}", delta_color="inverse")
                    cols[3].metric("Subsidy", f"-₹{b['subsidy']}", delta_color="normal")
                    cols[4].metric("Installments", f"₹{b['installments']}")
                    if solar_val > 0:
                        cols[5].metric("Solar Export", f"{solar_val} Units", delta="Offset Applied")

                    # Industrial PF Alerts
                    pf_adj = b.get('pf_adjustment', 0.0)
                    if pf_adj > 0: st.warning(f"⚠️ **Power Factor Penalty:** ₹{pf_adj}")
                    elif pf_adj < 0: st.success(f"🌱 **Power Factor Rebate:** -₹{abs(pf_adj)}")

                    # Expanders
                    if mem['mode'].upper() == "PREPAID":
                        with st.expander("⏱️ View Time of Day (ToD) Breakdown"):
                            tod = b['tod_breakdown']
                            st.write(f"- **Normal:** ₹{tod['normal']} | **Peak:** ₹{tod['peak']} | **Off-Peak:** ₹{tod['off_peak']}")
                            
                    if mem.get('appliances'):
                        with st.expander("🔌 View Appliance Breakdown"):
                            for app in mem['appliances']:
                                q = app.get('quantity', 1)
                                u = (app['watts'] * app['hours_per_day'] * q * mem['billing_days']) / 1000
                                st.write(f"- **{q}x {app['name']}**: ~{int(u)} Units/month")
                                        
                    st.success(f"### 💰 Total Payable: ₹{b['total_payable']}")
                    
                    if solar_val > 0:
                        st.info(f"☀️ **Net Metering:** Consumed {b['billed_units']} units, Solar offset {solar_val} units. Billed for **{b['net_billed_units']} units**.")
                    
                    st.info(f"💳 **New Balance:** ₹{result['balance_sheet']['closing']}")
                    
                    # PDF Export
                    pdf_bytes = create_bill_pdf(st.session_state.memory, result)
                    st.download_button("📥 Download PDF Bill", pdf_bytes, "VoltAssist_Bill.pdf", "application/pdf")

                st.session_state.history.append({"role": "assistant", "content": f"Bill: **₹{b['total_payable']}** (Balance: **₹{result['balance_sheet']['closing']}**)"})
                
            except Exception as e:
                st.error(f"System Error: {e}")
