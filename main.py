
# main.py

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_agent

from banking_tools import (
    calculate_emi,
    check_loan_eligibility,
    get_account_details,
)

load_dotenv()

# 1. Initialize the Groq language model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
)


# 2. Expose EMI calculation as an agent tool
@tool
def calculate_loan_emi(
    loan_amount: float,
    tenure_years: int,
) -> dict:
    """Calculate the monthly EMI for a loan using the
    project's configured annual interest rate."""
    return calculate_emi(loan_amount, tenure_years)


# 3. Expose eligibility checking as an agent tool
@tool
def verify_loan_eligibility(
    monthly_salary: float,
    existing_emi: float,
    proposed_emi: float,
) -> dict:
    """Check mock loan eligibility using salary, existing EMI,
    and proposed EMI."""
    return check_loan_eligibility(
        monthly_salary,
        existing_emi,
        proposed_emi,
    )


# 4. Expose account retrieval as an agent tool
@tool
def retrieve_account(customer_id: str) -> dict:
    """Retrieve mock banking account details for a customer ID."""
    return get_account_details(customer_id)


# 5. Create ONE agent with three tools
agent = create_agent(
    model=llm,
    tools=[
        calculate_loan_emi,
        verify_loan_eligibility,
        retrieve_account,
    ],
    system_prompt="""
    You are a Smart Banking Support Agent using mock data.

    Your responsibilities:
    1. Understand the customer's banking request.
    2. Call the appropriate tools to calculate EMI,
       check eligibility, and retrieve account details.
    3. Use tool results when preparing your response.
    4. The configured annual interest rate is 12%.
    5. The mock eligibility policy allows total monthly EMIs
       up to 50% of monthly salary.
    6. Never invent tool results or claim a loan is approved.
    7. If the customer ID is missing, ask for it before
       retrieving account details.
    8. Do not claim that an application has been submitted.
       Application submission will be handled separately.
    """
)


# 6. Chat with the agent
print("Smart Banking Support Agent")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("Customer: ").strip()

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if not user_input:
        continue

    try:
        result = agent.invoke({
            "messages": [
                {"role": "user", "content": user_input}
            ]
        })

        final_message = result["messages"][-1]
        print("\nBanking Agent:", final_message.content, "\n")

    except Exception as error:
        print("An error occurred:", error)
