
from fastapi import FastAPI
from pydantic import BaseModel, Field
from uuid import uuid4

app = FastAPI(title="Mock Banking Loan API")


class LoanApplication(BaseModel):
    customer_id: str
    loan_amount: float = Field(gt=0)
    tenure_years: int = Field(gt=0)
    monthly_emi: float = Field(gt=0)
    customer_confirmed: bool


@app.post("/loan-applications")
def submit_loan_application(application: LoanApplication):
    """Create a mock loan application."""
    if not application.customer_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Customer confirmation is required.",
        )
    return {
        "success": True,
        "application_id": f"LOAN-{uuid4().hex[:8].upper()}",
        "status": "SUBMITTED_FOR_REVIEW",
        "message": "Application submitted successfully for review.",
        "loan_amount": application.loan_amount,
        "tenure_years": application.tenure_years,
        "monthly_emi": application.monthly_emi,
    }
