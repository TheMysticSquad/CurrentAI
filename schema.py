from pydantic import BaseModel, Field, field_validator
from typing import Optional

class BillingParameters(BaseModel):
    category: str = Field(default="DS-II", description="Tariff category: DS-II, NDS-II, HTS-I, or IAS")
    units: int = Field(default=0, description="Total energy units consumed")
    load_kw: float = Field(default=1.0, description="Sanctioned load in kW")
    billing_days: int = Field(default=30, description="Number of days for the bill")
    mode: str = Field(default="Prepaid", description="Prepaid or Postpaid")
    current_balance: float = Field(default=0.0, description="User's existing wallet balance")
    installments: int = Field(default=0, description="Number of pending installments")

    # DEFENSIVE LOGIC: Automatically fix human mistakes
    @field_validator('units', 'load_kw', 'billing_days', 'installments')
    def prevent_negatives(cls, v):
        if v < 0:
            return 0  # Silently fix negative inputs to 0
        return v

    @field_validator('category')
    def enforce_valid_categories(cls, v):
        valid = ["DS-II", "NDS-II", "HTS-I", "IAS"]
        # If the LLM hallucinates "Shop Category", default back to DS-II
        if v.upper() not in valid:
            return "DS-II"
        return v.upper()