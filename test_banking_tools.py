
# test_banking_tools.py

from banking_tools import (
    calculate_emi,
    check_loan_eligibility,
    get_account_details,
)

# 1. Calculate EMI
emi_result = calculate_emi(
    loan_amount=500000,
    tenure_years=3,
)

print("\n--- EMI CALCULATION ---")
print(emi_result)

# 2. Check loan eligibility
eligibility_result = check_loan_eligibility(
    monthly_salary=60000,
    existing_emi=5000,
    proposed_emi=emi_result["monthly_emi"],
)

print("\n--- LOAN ELIGIBILITY ---")
print(eligibility_result)

# 3. Retrieve account details
account_result = get_account_details("CUST001")

print("\n--- ACCOUNT DETAILS ---")
print(account_result)
