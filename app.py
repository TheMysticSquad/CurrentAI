import streamlit as st
from brain import process_user_input
from billing_engine import calculate_bihar_billing_v2

st.set_page_config(page_title="VoltAssist AI", page_icon="⚡", layout="wide")

with st.sidebar:
    st.title("⚡ VoltAssist")
    st.caption("Intelligent Billing Assistant")
    st.divider()
    
    if st.button("🔄 Start New Chat", use_container_width=True, type="primary"):
        st.session_state.memory = {
        "category": "DS-II", "units": 0, "peak_units": 0, "off_peak_units": 0, 
        "load_kw": 1.0, "billing_days": 30, "mode": "Prepaid", 
        "current_balance": 0.0, "installments": 0, "dps": 0.0, "subsidy": 0.0,
        "arrears": 0.0, "arrears_days": 0 # <--- ADD THESE HERE
        }
        st.session_state.history = []
        st.rerun()
        
    st.divider()
    st.subheader("💡 Try these scenarios")
    
    sidebar_prompt = None
    if st.button("🏢 1. Commercial Shop", help="Tests NDS-II category and load updates"):
        sidebar_prompt = "I run a small shop with a 5kw load. We consumed 450 units over the last 30 days."
        
    if st.button("⏱️ 2. Smart Meter ToD", help="Tests Peak/Off-Peak breakdown"):
        sidebar_prompt = "I am on Prepaid. I used 500 units total. 100 were peak and 50 were off-peak."
        
    if st.button("⚖️ 3. Penalty & Subsidy", help="Tests DPS and Govt Subsidy"):
        sidebar_prompt = "Add a 150 rupee DPS penalty, but apply my 300 rupee government subsidy."
        
    st.divider()
    st.caption("Powered by Llama-3.1 & Fluentgrid")

if "memory" not in st.session_state:
    st.session_state.memory = {
        "category": "DS-II", "units": 0, "peak_units": 0, "off_peak_units": 0, 
        "load_kw": 1.0, "billing_days": 30, "mode": "Prepaid", 
        "current_balance": 0.0, "installments": 0, "dps": 0.0, "subsidy": 0.0
    }

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🤖 Chat with VoltAssist")
st.caption("Enter your billing details in natural language, and the AI will extract the parameters.")

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

chat_prompt = st.chat_input("Ex: 'I have a shop, used 450 units...'")
prompt = chat_prompt or sidebar_prompt

if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing through AI Engine..."):
        new_memory = process_user_input(prompt, st.session_state.memory)
        st.session_state.memory = new_memory

        try:
            result = calculate_bihar_billing_v2(**st.session_state.memory)
            
            response_text = f"**Category:** {st.session_state.memory['category']} | **Days:** {st.session_state.memory['billing_days']} | **Mode:** {st.session_state.memory['mode']}"
            
            with st.chat_message("assistant"):
                st.markdown(response_text)
                
                # Component-Wise Dashboard
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Energy Charges (EC)", f"₹{result['breakdown']['energy_charges']}")
                col2.metric("Fixed Charges (FC)", f"₹{result['breakdown']['fixed_charges']}")
                col3.metric("DPS (Penalty)", f"₹{result['breakdown']['dps']}", delta_color="inverse")
                col4.metric("Subsidy", f"-₹{result['breakdown']['subsidy']}", delta_color="normal")
                col5.metric("Installments", f"₹{result['breakdown']['installments']}")
                
                # ToD Expandable Section
                if st.session_state.memory['mode'].upper() == "PREPAID":
                    with st.expander("⏱️ View Time of Day (ToD) Breakdown"):
                        tod = result['breakdown']['tod_breakdown']
                        st.write(f"- **Normal EC:** ₹{tod['normal']}")
                        st.write(f"- **Peak EC (1.2x):** ₹{tod['peak']}")
                        st.write(f"- **Off-Peak EC (0.85x):** ₹{tod['off_peak']}")
                
                st.success(f"### 💰 Total Payable: ₹{result['breakdown']['total_payable']}")
                st.info(f"💳 **Wallet Status:** After applying your credit of ₹{st.session_state.memory['current_balance']}, your new balance is **₹{result['balance_sheet']['closing']}**.")

                with st.expander("🔍 View AI Memory State (JSON)"):
                    st.json(st.session_state.memory)

            st.session_state.history.append({
                "role": "assistant", 
                "content": f"Calculated Bill: **₹{result['breakdown']['total_payable']}** (New Balance: **₹{result['balance_sheet']['closing']}**)"
            })
            
        except Exception as e:
            with st.chat_message("assistant"):
                error_msg = str(e).lower()
                if "rate_limit" in error_msg or "429" in error_msg:
                    st.warning("⏳ The AI is currently processing a high volume of requests. Please wait 10 seconds and try again!")
                else:
                    st.error(f"System Error: {e}")