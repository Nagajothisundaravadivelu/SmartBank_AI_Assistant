from customer_db import get_customer


ANNUAL_INTEREST_RATE = 12.0


def calculate_emi(loan_amount, tenure_years, annual_interest_rate=ANNUAL_INTEREST_RATE):
    loan_amount = float(loan_amount)
    tenure_years = int(tenure_years)
    annual_interest_rate = float(annual_interest_rate)

    if loan_amount <= 0:
        raise ValueError("Loan amount must be greater than zero.")
    if tenure_years <= 0:
        raise ValueError("Tenure must be greater than zero.")

    months = tenure_years * 12
    monthly_rate = annual_interest_rate / 12 / 100

    if monthly_rate == 0:
        monthly_emi = loan_amount / months
    else:
        factor = (1 + monthly_rate) ** months
        monthly_emi = loan_amount * monthly_rate * factor / (factor - 1)

    total_payment = monthly_emi * months
    total_interest = total_payment - loan_amount

    return {
        "loan_amount": loan_amount,
        "tenure_years": tenure_years,
        "annual_interest_rate": annual_interest_rate,
        "monthly_emi": monthly_emi,
        "total_interest": total_interest,
        "total_payment": total_payment,
    }


def check_loan_eligibility(monthly_salary, existing_emi, proposed_emi):
    monthly_salary = float(monthly_salary)
    existing_emi = float(existing_emi)
    proposed_emi = float(proposed_emi)

    if monthly_salary <= 0:
        raise ValueError("Monthly salary must be greater than zero.")
    if existing_emi < 0 or proposed_emi < 0:
        raise ValueError("EMI values cannot be negative.")

    total_monthly_emi = existing_emi + proposed_emi
    ratio = (total_monthly_emi / monthly_salary) * 100
    eligible = ratio <= 50

    return {
        "eligible": eligible,
        "reason": (
            "Combined EMIs are within 50% of monthly salary."
            if eligible else
            "Combined EMIs exceed 50% of monthly salary."
        ),
        "total_monthly_emi": total_monthly_emi,
        "emi_to_income_ratio": ratio,
        "monthly_salary": monthly_salary,
        "existing_emi": existing_emi,
        "proposed_emi": proposed_emi,
    }


def get_account_details(customer_id):
    customer = get_customer(customer_id)
    if not customer:
        return {
            "found": False,
            "customer_id": str(customer_id).strip().upper(),
            "message": "Customer not found. Check the customer ID or add the customer first.",
        }

    return {
        "found": True,
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "phone": customer["phone"],
        "account_number": customer["account_number"],
        "account_type": customer["account_type"],
        "balance": float(customer["balance"]),
        "monthly_salary": float(customer["monthly_salary"]),
        "address": customer["address"],
    }
