# ⚡ CurrentAI (VoltAssist V1)

**An Enterprise-Grade, NLP-Powered Utility Billing Engine**

CurrentAI (VoltAssist) is an intelligent utility billing assistant that allows users to input their electricity usage in natural language. Powered by Llama-3.1 and LangChain, the AI acts as an extraction pipeline to securely parse billing parameters and feed them into a deterministic, rule-based mathematical engine modeled after DISCOM (Bihar RMS) tariff structures.

## ✨ Key Features

* **🗣️ Natural Language Parsing:** Extracts complex billing parameters (units, load, category, arrears) from conversational text using Groq's blazing-fast inference API.
* **⏱️ Time of Day (ToD) Billing:** Automatically calculates 1.2x Peak and 0.85x Off-Peak surcharges/rebates for smart-metered prepaid users.
* **🏛️ Auto-Subsidy Engine:** Automatically detects domestic (DS-II) users and applies state government per-unit subsidies without requiring manual input.
* **⚖️ DPS & Arrears Calculation:** Intelligently calculates Delayed Payment Surcharges (1.25% per month) on past-due balances.
* **📊 Component-Wise Dashboard:** A clean, responsive Streamlit UI that breaks down the final bill into Energy Charges (EC), Pro-Rata Fixed Charges (FC), Penalties, and Installments.

## 🛠️ Tech Stack

* **Frontend UI:** [Streamlit](https://streamlit.io/)
* **AI/NLP Pipeline:** [LangChain](https://www.langchain.com/) & Pydantic
* **LLM Provider:** [Groq](https://groq.com/) (Llama-3.1-8b-instant)
* **Language:** Python 3.9+

## 📁 Project Structure

```text
CurrentAI/
├── app.py               # The Streamlit frontend and UI layout
├── brain.py             # The LangChain NLP extraction pipeline
├── billing_engine.py    # The deterministic math and tariff rules
├── schema.py            # Pydantic data models and validation
├── requirements.txt     # Python dependencies
└── .gitignore           # Git security rules
