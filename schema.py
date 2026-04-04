from pydantic import BaseModel, Field, field_validator

class BillingParameters(BaseModel):
    category: str = Field(default="DS-II", description="Tariff category: DS-II, NDS-II, HTS-I, or IAS")
    units: int = Field(default=0, description="Total energy units consumed")
    peak_units: int = Field(default=0, description="Units consumed during Peak hours (ToD)")
    off_peak_units: int = Field(default=0, description="Units consumed during Off-Peak hours (ToD)")
    load_kw: float = Field(default=1.0, description="Sanctioned load in kW")
    billing_days: int = Field(default=30, description="Number of days for the bill")
    mode: str = Field(default="Prepaid", description="Prepaid or Postpaid")
    current_balance: float = Field(default=0.0, description="User's existing wallet balance")
    installments: int = Field(default=0, description="Number of pending installments")
    dps: float = Field(default=0.0, description="Delayed Payment Surcharge (Penalty)")
    subsidy: float = Field(default=0.0, description="Government Subsidy Amount")
    arrears: float = Field(default=0.0, description="Previous unpaid bill amount")
    arrears_days: int = Field(default=0, description="Number of days the previous bill is overdue")

    # DEFENSIVE LOGIC: Automatically fix human mistakes
    @field_validator('units', 'peak_units', 'off_peak_units', 'load_kw', 'billing_days', 'installments', 'dps', 'subsidy')
    def prevent_negatives(cls, v):
        if v < 0:
            return 0 
        return v

    @field_validator('category')
    def enforce_valid_categories(cls, v):
        valid = ["DS-II", "NDS-II", "HTS-I", "IAS"]
        if v.upper() not in valid:
            return "DS-II"
        return v.upper()