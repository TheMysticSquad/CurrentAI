# ⚡ VoltAssist AI (V2.0 PRO)

**The Universal, AI-Powered Utility Auditing & Solar Net Metering Engine**

VoltAssist (formerly CurrentAI) is a high-performance utility billing assistant that transforms messy, natural language inputs into precise, deterministic financial audits. Engineered with a "Human-in-the-Loop" agentic workflow, it supports everything from residential flats to massive 500kVA industrial plants across multiple Indian states.

## 🚀 New in V2.0

* **☀️ Solar Net Metering:** Full support for prosumer "Banking" and "Net Billing" logic. Subtracts solar exports from grid imports before applying slab rates.
* **🏭 Industrial (HT) Auditor:** Implements the strict **85% Billing Demand** rule and automated **Power Factor (PF) Penalties/Rebates** (1% surcharge per 0.01 PF drop).
* **🌍 Multi-State Tariff Master:** One-click switching between tariff structures for **Bihar, Maharashtra, Delhi, UP, and Karnataka**.
* **🔌 Smart Appliance Estimator:** Converts appliance lists (e.g., "2 ACs for 8 hours") into kWh and statistically distributes them across **Peak (1.2x)** and **Off-Peak (0.80x)** slots.
* **📸 Multimodal Vision AI:** Upload a photo of your smart meter or a PDF bill; the system uses `Llama-3.2-Vision` to extract parameters automatically.

## ✨ Core Features

* **🗣️ Agentic NLP Parsing:** Powered by Llama-3.1 & LangChain to extract units, load, category, and arrears from conversational text.
* **🛡️ Validation Gate:** An intelligent follow-up system that pauses calculations if critical data (like load or category) is missing.
* **📄 Enterprise PDF Invoicing:** Generates professional, A4-ready billing estimates including state subsidies and ToD breakdowns.
* **📊 Prosumer Dashboard:** A responsive Streamlit UI that adapts its metrics (Solar, PF, ToD) based on the user's specific connection type.

## 🛠️ Tech Stack

* **Frontend UI:** [Streamlit](https://streamlit.io/)
* **AI/NLP Pipeline:** [LangChain](https://www.langchain.com/) & Pydantic
* **LLM Provider:** [Groq](https://groq.com/) (Llama-3.1-70b & Llama-3.2-Vision)
* **PDF Engine:** FPDF
* **Language:** Python 3.12+

## 📁 Project Structure

```text
VoltAssist/
├── app.py              # Streamlit frontend, State management & UI
├── brain.py            # LangChain NLP extraction & Vision logic
├── billing_engine.py    # Universal Multi-state math & HT/Solar rules
├── pdf_generator.py     # Enterprise PDF invoice generation
├── schema.py            # Pydantic models for Industrial/Solar data
├── requirements.txt     # Python dependencies (V2 optimized)
└── .env                 # API Keys (Groq/OpenAI)
```

## 🚥 Getting Started

1.  **Clone the repo** and install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set your API Key** in a `.env` file:
    ```text
    GROQ_API_KEY=your_key_here
    ```
3.  **Run the app**:
    ```bash
    streamlit run app.py
    ```

---
