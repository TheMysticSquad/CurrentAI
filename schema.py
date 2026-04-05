from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class ApplianceItem(BaseModel):
    name: str = Field(description="Name of the appliance (e.g., AC, Fan, Fridge)")
    watts: float = Field(description="Estimated wattage (e.g., 1.5 ton AC = 1500W, Ceiling Fan = 75W, Fridge = 400W)")
    hours_per_day: float = Field(description="How many hours per day it is used")
    quantity: int = Field(default=1, description="Number of these specific appliances")

class BillingParameters(BaseModel):
    state: str = Field(default="Bihar", description="The Indian State where the user lives")
    category: Optional[str] = Field(default=None, description="Tariff category: 'Domestic', 'Commercial', or 'Industrial'")
    units: Optional[int] = Field(default=None, description="Total energy units consumed")
    load_kw: Optional[float] = Field(default=None, description="Sanctioned load in kW")
    
    appliances: Optional[List[ApplianceItem]] = Field(default=None, description="List of appliances. Extract this ONLY if the user describes appliances instead of explicit units.")
    
    # ==========================================
    # 🏭 NEW: HT INDUSTRIAL PARAMETERS
    # ==========================================
    contract_demand_kva: Optional[float] = Field(default=None, description="Contract demand in kVA for Industrial users")
    maximum_demand_kva: Optional[float] = Field(default=None, description="Maximum demand recorded in kVA for Industrial users")
    power_factor: Optional[float] = Field(default=None, description="Power factor (e.g., 0.88, 0.95) for Industrial users")
    # ==========================================

    peak_units: int = Field(default=0, description="Units consumed during Peak hours")
    off_peak_units: int = Field(default=0, description="Units consumed during Off-Peak hours")
    billing_days: int = Field(default=30, description="Number of days for the bill")
    mode: str = Field(default="Prepaid", description="Prepaid or Postpaid")
    current_balance: float = Field(default=0.0, description="User's existing wallet balance")
    installments: int = Field(default=0, description="Number of pending installments")
    dps: float = Field(default=0.0, description="Delayed Payment Surcharge")
    subsidy: float = Field(default=0.0, description="Government Subsidy Amount")
    arrears: float = Field(default=0.0, description="Previous unpaid bill amount")
    arrears_days: int = Field(default=0, description="Number of days the previous bill is overdue")
    
    is_complete: bool = Field(default=False, description="Set to False if (units OR appliances), load/demand, or category are missing.")
    follow_up_message: str = Field(default="", description="Question asking for missing data.")
    # ==========================================
    # ☀️ NEW: SOLAR NET METERING PARAMETERS
    # ==========================================
    solar_exported_units: Optional[int] = Field(default=0, description="Units sent back to the grid from solar panels")

    @field_validator('units', 'peak_units', 'off_peak_units', 'load_kw', 'billing_days', 'installments', 'dps', 'subsidy', 'arrears', 'arrears_days')
    def prevent_negatives(cls, v):
        if v is None: return v
        if v < 0: return 0 
        return v

    @field_validator('category')
    def enforce_valid_categories(cls, v):
        if v is None: return v
        valid = ["DOMESTIC", "COMMERCIAL", "INDUSTRIAL", "AGRICULTURE"]
        if v.upper() not in valid:
            return "Domestic"
        return v.title()