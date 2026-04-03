import streamlit as st
from brain import process_user_input
from billing_engine import calculate_bihar_billing_v2

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="CurrentAI", page_icon="⚡", layout="wide")

# --- 2. PRODUCTION SIDEBAR ---
with st.sidebar:
    st.title("⚡ CurrentAI")
    st.caption("Intelligent Billing Assistant")
    st.divider()
    
    # Critical for production: Let users clear the AI's memory to start fresh
    if st.button("🔄 Start New Bill", use_container_width=True, type="primary"):
        st.session_state.memory = {
            "category": "DS-II", "units": 0, "load_kw": 1.0, 
            "billing_days": 30, "mode": "Prepaid", 
            "current_balance": 0.0, "installments": 0
        }
        st.session_state.history = []
        st.rerun() # Refreshes the page instantly
        
    st.divider()
    st.subheader("💡 Try these scenarios")
    st.markdown("Click a button below to test the AI:")
    
    # We capture button clicks into a variable to act as chat input
    sidebar_prompt = None
    if st.button("🏢 1. Commercial Shop", help="Tests NDS-II category and load updates"):
        sidebar_prompt = "I run a small shop with a 5kw load. We consumed 450 units over the last 30 days."
        
    if st.button("🏠 2. Domestic Arrears", help="Tests DS-II and installment math"):
        sidebar_prompt = "Calculate my home bill. I used 120 units and have 2 pending installments."
        
    if st.button("💳 3. Wallet Payment", help="Tests balance adjustments"):
        sidebar_prompt = "I just paid 1500 rupees into my wallet. Update my balance."
        
    if st.button("🏭 4. Factory Postpaid", help="Tests HTS-I and mode change"):
        sidebar_prompt = "Change my category to HTS-I, mode to Postpaid, and units to 5000."
        
    st.divider()
    st.caption("Powered by Llama-3.1 & Fluentgrid")

# --- 3. SESSION MEMORY INITIALIZATION ---
if "memory" not in st.session_state:
    st.session_state.memory = {
        "category": "DS-II", "units": 0, "load_kw": 1.0,
        "billing_days": 30, "mode": "Prepaid",
        "current_balance": 0.0, "installments": 0
    }

if "history" not in st.session_state:
    st.session_state.history = []

# --- 4. MAIN LAYOUT ---
st.title("🤖 Chat with CurrentAI")
st.caption("Enter your billing details in natural language, and the AI will extract the parameters.")

# --- 5. DISPLAY CHAT HISTORY ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. HANDLE USER INPUT ---
# The prompt can come from either the chat input bar OR a sidebar button
chat_prompt = st.chat_input("Ex: 'I have a shop, used 450 units...'")
prompt = chat_prompt or sidebar_prompt

if prompt:
    # Show user message
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing through AI Engine..."):
        # STEP A: The Brain (Validates and Updates Memory)
        new_memory = process_user_input(prompt, st.session_state.memory)
        st.session_state.memory = new_memory

        # STEP B: The Engine (Calculates the Math)
        # We wrap this in a try/except so if the math engine fails, the UI doesn't crash
        try:
            result = calculate_bihar_billing_v2(**st.session_state.memory)
            
            # STEP C: Format the Response
            response_text = f"**Category:** {st.session_state.memory['category']} | **Days:** {st.session_state.memory['billing_days']} | **Mode:** {st.session_state.memory['mode']}"
            
            with st.chat_message("assistant"):
                st.markdown(response_text)
                
                # Display the bill beautifully using columns
                col1, col2, col3 = st.columns(3)
                col1.metric("Energy Charges", f"₹{result['breakdown']['energy_charges']}")
                col2.metric("Fixed Charges", f"₹{result['breakdown']['fixed_charges']}")
                col3.metric("Installments", f"₹{result['breakdown']['installments']}")
                
                st.success(f"### 💰 Total Payable: ₹{result['breakdown']['total_payable']}")
                st.info(f"💳 **Wallet Status:** After applying your credit of ₹{st.session_state.memory['current_balance']}, your new balance is **₹{result['balance_sheet']['closing']}**.")

                # Developer view: See the exact JSON the LangChain agent generated
                with st.expander("🔍 View AI Memory State (JSON)"):
                    st.json(st.session_state.memory)

            # Save assistant response to history
            st.session_state.history.append({
                "role": "assistant", 
                "content": f"Calculated Bill: **₹{result['breakdown']['total_payable']}** (New Balance: **₹{result['balance_sheet']['closing']}**)"
            })
            
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"Billing Engine Error: {e}\nPlease check your mathematical logic in billing_engine.py.")