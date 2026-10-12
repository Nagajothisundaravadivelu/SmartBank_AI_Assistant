import os
import sqlite3
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_agent

from banking_tools import calculate_emi, check_loan_eligibility, get_account_details
from customer_db import create_customer, get_all_customers

load_dotenv()
API_URL = "http://127.0.0.1:8081/loan-applications"

st.set_page_config(
    page_title="SmartBank AI",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# AI agent and tools
# ----------------------------
@tool
def calculate_loan_emi(loan_amount: float, tenure_years: int) -> dict:
    """Calculate loan EMI using the demo's 12 percent annual interest rate."""
    return calculate_emi(loan_amount, tenure_years)


@tool
def verify_loan_eligibility(
    monthly_salary: float, existing_emi: float, proposed_emi: float
) -> dict:
    """Check demo loan eligibility using combined EMI as a share of salary."""
    return check_loan_eligibility(monthly_salary, existing_emi, proposed_emi)


@tool
def retrieve_account(customer_id: str) -> dict:
    """Retrieve account information by customer ID from the local SQLite database."""
    return get_account_details(customer_id)


@st.cache_resource
def build_agent():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from your .env file.")
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    return create_agent(
        model=llm,
        tools=[calculate_loan_emi, verify_loan_eligibility, retrieve_account],
        system_prompt="""
        You are SmartBank AI, a banking support assistant using fictional demo data.
        Use tools for EMI calculations, mock eligibility checks, and customer lookup.
        The configured annual interest rate is 12%. The demo eligibility rule permits
        combined monthly EMIs up to 50% of monthly salary.
        Explain results clearly. Do not claim a loan is approved.
        Never ask for passwords, PINs, or OTPs. Application submission is controlled
        separately by the app and requires explicit confirmation.
        """,
    )


# ----------------------------
# Session state and navigation
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "assessment" not in st.session_state:
    st.session_state.assessment = None
if "application_result" not in st.session_state:
    st.session_state.application_result = None
if "emi_result" not in st.session_state:
    st.session_state.emi_result = None


def open_page(page_name):
    st.session_state.page = page_name


def go_home():
    st.session_state.page = "Home"


# ----------------------------
# Styling
# ----------------------------
st.markdown("""
<style>
.block-container { padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1150px; }
.hero {
    padding: 2rem; border-radius: 18px;
    background: linear-gradient(120deg, #102a43, #176b87);
    color: white; margin-bottom: 1.5rem;
}
.hero h1 { color: white; margin-bottom: .5rem; }
.hero p { color: #e1edf5; font-size: 1rem; }
div.stButton > button { border-radius: 10px; min-height: 2.8rem; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header and sidebar navigation
# ----------------------------
with st.sidebar:
    st.markdown("## 🏦 SmartBank AI")
    st.caption("Demo banking assistant")
    st.divider()
    pages = [
        "Home", "Add Customer", "Account Details",
        "EMI Calculator", "Loan Eligibility", "AI Chat"
    ]
    for page_name in pages:
        if st.button(
            page_name,
            key=f"nav_{page_name.lower().replace(' ', '_')}",
            use_container_width=True,
            type="primary" if st.session_state.page == page_name else "secondary",
        ):
            open_page(page_name)
            st.rerun()
    st.divider()
    st.caption("Training demo only • Fictional customer data")

header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown("## 🏦 SmartBank AI")
with header_right:
    if st.session_state.page != "Home":
        st.button("← Home", on_click=go_home, use_container_width=True)
st.caption("Your intelligent banking support assistant")
st.divider()

# ----------------------------
# HOME DASHBOARD
# ----------------------------
if st.session_state.page == "Home":
    st.markdown("""
    <div class="hero">
        <h1>Welcome to SmartBank AI</h1>
        <p>Your virtual assistant for loan calculations, eligibility checks,
        customer information, and banking questions.</p>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("How can we help you today?")
    st.write("Choose a service to get started.")

    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### 🧮 EMI Calculator")
            st.write("Estimate monthly payments, total interest, and total repayment.")
            st.button("Open EMI Calculator →", key="home_emi", use_container_width=True,
                      on_click=open_page, args=("EMI Calculator",))
        with st.container(border=True):
            st.markdown("### 💳 Account Details")
            st.write("Look up a customer account using the customer ID.")
            st.button("View Account →", key="home_account", use_container_width=True,
                      on_click=open_page, args=("Account Details",))
        with st.container(border=True):
            st.markdown("### 👤 Add Customer")
            st.write("Register a customer and save their information in SQLite.")
            st.button("Add Customer →", key="home_add_customer", use_container_width=True,
                      on_click=open_page, args=("Add Customer",))
    with right:
        with st.container(border=True):
            st.markdown("### 🛡️ Loan Eligibility")
            st.write("Assess a proposed loan against the demo EMI-to-income rule.")
            st.button("Check Eligibility →", key="home_eligibility", use_container_width=True,
                      on_click=open_page, args=("Loan Eligibility",))
        with st.container(border=True):
            st.markdown("### 💬 Ask Banking AI")
            st.write("Ask questions about EMI, loans, and banking concepts.")
            st.button("Start Chat →", key="home_chat", use_container_width=True,
                      on_click=open_page, args=("AI Chat",))
    st.divider()
    customers = get_all_customers()
    c1, c2 = st.columns(2)
    c1.metric("Registered demo customers", len(customers))
    c2.metric("Database", "SQLite • persistent")
    st.caption("This is a training demo. It does not connect to a real bank.")

# ----------------------------
# ADD CUSTOMER
# ----------------------------
elif st.session_state.page == "Add Customer":
    st.title("👤 Add Customer")
    st.write("Enter the customer's details. The record will be saved in the local SQLite database.")
    with st.form("add_customer_form", clear_on_submit=True):
        name = st.text_input("Customer name", placeholder="Enter full name")
        phone = st.text_input("Phone number", placeholder="10-digit phone number", max_chars=10)
        account_type = st.selectbox("Account type", ["Savings", "Current"])
        monthly_salary = st.number_input(
            "Monthly salary (₹)", min_value=0.0, value=0.0, step=1000.0
        )
        address = st.text_area("Address", placeholder="Enter full address")
        submitted = st.form_submit_button("Save Customer", type="primary", use_container_width=True)

    if submitted:
        try:
            customer = create_customer(name, phone, account_type, monthly_salary, address)
            st.success("Customer added successfully!")
            a, b, c = st.columns(3)
            a.metric("Customer ID", customer["customer_id"])
            b.metric("Account type", customer["account_type"])
            c.metric("Monthly salary", f"₹{customer['monthly_salary']:,.2f}")
            st.write("**Name:**", customer["name"])
            st.write("**Phone:**", customer["phone"])
            st.write("**Address:**", customer["address"])
            st.info("Use this customer ID in Account Details and Loan Eligibility.")
        except ValueError as exc:
            st.error(str(exc))
        except sqlite3.IntegrityError:
            st.error("This phone number is already registered. Use a different number.")

    st.divider()
    st.subheader("Registered customers")
    customers = get_all_customers()
    if customers:
        st.dataframe(
            [
                {
                    "Customer ID": c["customer_id"],
                    "Name": c["name"],
                    "Phone": c["phone"],
                    "Account type": c["account_type"],
                    "Monthly salary": c["monthly_salary"],
                }
                for c in customers
            ],
            use_container_width=True,
            hide_index=True,
        )

# ----------------------------
# ACCOUNT DETAILS
# ----------------------------
elif st.session_state.page == "Account Details":
    st.title("💳 Account Details")
    customers = get_all_customers()
    customer_ids = [c["customer_id"] for c in customers]
    default_index = customer_ids.index("CUST001") if "CUST001" in customer_ids else 0
    with st.form("account_lookup_form"):
        customer_id = st.selectbox("Select customer ID", customer_ids, index=default_index)
        lookup = st.form_submit_button("View Account", type="primary", use_container_width=True)
    if lookup:
        account = get_account_details(customer_id)
        if account.get("found"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Customer ID", account["customer_id"])
            c2.metric("Account type", account["account_type"])
            c3.metric("Mock balance", f"₹{account['balance']:,.2f}")
            st.subheader(account["name"])
            left, right = st.columns(2)
            with left:
                st.write("**Account number:**", account["account_number"])
                st.write("**Phone:**", account["phone"])
                st.write("**Monthly salary:**", f"₹{account['monthly_salary']:,.2f}")
            with right:
                st.write("**Address:**", account["address"])
        else:
            st.warning(account["message"])
    st.caption("All account data shown here is fictional demo data.")

# ----------------------------
# EMI CALCULATOR
# ----------------------------
elif st.session_state.page == "EMI Calculator":
    st.title("🧮 EMI Calculator")
    st.write("Enter the loan amount and repayment period.")
    with st.form("emi_form"):
        loan_amount = st.number_input("Loan amount (₹)", min_value=10000.0,
                                      max_value=5000000.0, value=500000.0, step=10000.0)
        tenure_years = st.selectbox("Loan tenure", [1, 2, 3, 4, 5], index=2,
                                    format_func=lambda n: f"{n} year(s)")
        st.text_input("Annual interest rate", value="12% (mock rate)", disabled=True)
        calculate_clicked = st.form_submit_button("Calculate EMI", type="primary",
                                                   use_container_width=True)
    if calculate_clicked:
        st.session_state.emi_result = calculate_emi(loan_amount, tenure_years, 12)
    if st.session_state.emi_result:
        result = st.session_state.emi_result
        st.divider()
        st.subheader("Your estimated repayment")
        c1, c2, c3 = st.columns(3)
        c1.metric("Monthly EMI", f"₹{result['monthly_emi']:,.2f}")
        c2.metric("Total interest", f"₹{result['total_interest']:,.2f}")
        c3.metric("Total payment", f"₹{result['total_payment']:,.2f}")
        st.info("This estimate uses a fixed 12% annual interest rate and is for demonstration only.")

# ----------------------------
# LOAN ELIGIBILITY AND APPLICATION
# ----------------------------
elif st.session_state.page == "Loan Eligibility":
    st.title("🛡️ Loan Eligibility")
    st.write("Select a registered customer and enter the proposed loan details.")
    customers = get_all_customers()
    if not customers:
        st.warning("Add a customer before checking eligibility.")
    else:
        ids = [c["customer_id"] for c in customers]
        default_index = ids.index("CUST001") if "CUST001" in ids else 0
        selected_customer_id = st.selectbox("Customer ID", ids, index=default_index)
        selected_customer = get_account_details(selected_customer_id)
        salary_default = float(selected_customer.get("monthly_salary", 60000))
        with st.form("eligibility_form"):
            loan_amount = st.number_input("Loan amount (₹)", min_value=10000.0,
                                          max_value=5000000.0, value=500000.0, step=10000.0)
            tenure_years = st.selectbox("Loan tenure", [1, 2, 3, 4, 5], index=2,
                                        format_func=lambda n: f"{n} year(s)")
            monthly_salary = st.number_input("Monthly salary (₹)", min_value=1.0,
                                             value=max(1.0, salary_default), step=1000.0)
            existing_emi = st.number_input("Existing monthly EMI (₹)", min_value=0.0,
                                           value=5000.0, step=500.0)
            assess_clicked = st.form_submit_button("Calculate & Check Eligibility",
                                                   type="primary", use_container_width=True)
        if assess_clicked:
            emi_result = calculate_emi(loan_amount, tenure_years, 12)
            eligibility = check_loan_eligibility(monthly_salary, existing_emi, emi_result["monthly_emi"])
            st.session_state.assessment = {
                "customer_id": selected_customer_id,
                "loan_amount": loan_amount,
                "tenure_years": tenure_years,
                "monthly_salary": monthly_salary,
                "existing_emi": existing_emi,
                "emi": emi_result,
                "eligibility": eligibility,
                "account": get_account_details(selected_customer_id),
            }
            st.session_state.application_result = None

        assessment = st.session_state.assessment
        if assessment:
            # Show only if the assessment belongs to the currently selected customer.
            if assessment["customer_id"] == selected_customer_id:
                emi = assessment["emi"]
                eligibility = assessment["eligibility"]
                account = assessment["account"]
                st.divider()
                st.subheader("Assessment results")
                c1, c2, c3 = st.columns(3)
                c1.metric("Monthly EMI", f"₹{emi['monthly_emi']:,.2f}")
                c2.metric("Combined monthly EMIs", f"₹{eligibility['total_monthly_emi']:,.2f}")
                c3.metric("EMI-to-income ratio", f"{eligibility['emi_to_income_ratio']:.2f}%")
                if eligibility["eligible"]:
                    st.success("Passes the project's mock eligibility rule.")
                else:
                    st.error("Does not pass the project's mock eligibility rule.")
                st.caption("The mock rule allows combined monthly EMIs up to 50% of salary. This is not a real loan approval.")
                with st.expander("View mock account details"):
                    st.write("**Customer:**", account["name"])
                    st.write("**Customer ID:**", account["customer_id"])
                    st.write("**Account number:**", account["account_number"])
                    st.write("**Account type:**", account["account_type"])
                    st.write("**Mock balance:**", f"₹{account['balance']:,.2f}")

                st.divider()
                st.subheader("Application submission")
                if not eligibility["eligible"]:
                    st.warning("Submission is disabled because this assessment does not pass the mock eligibility rule.")
                elif st.session_state.application_result:
                    result = st.session_state.application_result
                    st.success("Application submitted for review.")
                    c1, c2 = st.columns(2)
                    c1.metric("Application ID", result.get("application_id", "N/A"))
                    c2.metric("Monthly EMI", f"₹{result.get('monthly_emi', 0):,.2f}")
                    st.write("**Status:**", result.get("status", "SUBMITTED_FOR_REVIEW"))
                    st.info("Submission does not mean your loan has been approved.")
                else:
                    st.write("Review these details before submitting:")
                    st.write(f"- Customer ID: {assessment['customer_id']}")
                    st.write(f"- Loan amount: ₹{assessment['loan_amount']:,.2f}")
                    st.write(f"- Tenure: {assessment['tenure_years']} years")
                    st.write(f"- Monthly EMI: ₹{emi['monthly_emi']:,.2f}")
                    with st.form("confirm_application_form"):
                        confirmed = st.checkbox("I have reviewed these details and confirm submission of this mock loan application.")
                        submit_application = st.form_submit_button("Submit Application for Review",
                                                                    type="primary", use_container_width=True)
                    if submit_application:
                        if not confirmed:
                            st.error("Please confirm the details before submitting.")
                        else:
                            payload = {
                                "customer_id": assessment["customer_id"],
                                "loan_amount": float(assessment["loan_amount"]),
                                "tenure_years": int(assessment["tenure_years"]),
                                "monthly_emi": float(emi["monthly_emi"]),
                                "customer_confirmed": True,
                            }
                            try:
                                response = requests.post(API_URL, json=payload, timeout=10)
                                if response.ok:
                                    st.session_state.application_result = response.json()
                                    st.success("Application submitted to the mock API.")
                                    st.rerun()
                                else:
                                    try:
                                        detail = response.json().get("detail", response.text)
                                    except ValueError:
                                        detail = response.text
                                    st.error(f"API error ({response.status_code}): {detail}")
                            except requests.RequestException as exc:
                                st.error("Could not connect to the loan API. Make sure FastAPI is running on port 8081.")
                                st.caption(str(exc))

# ----------------------------
# AI CHAT
# ----------------------------
elif st.session_state.page == "AI Chat":
    st.title("💬 Ask Banking AI")
    st.write("Ask about EMI, loan eligibility, or a registered demo account.")
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Example: Find account details for CUST001")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    agent = build_agent()
                    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
                    messages = result.get("messages", [])
                    answer = messages[-1].content if messages else "Sorry, I couldn't produce an answer."
                    if isinstance(answer, list):
                        answer = "\n".join(
                            part.get("text", str(part)) if isinstance(part, dict) else str(part)
                            for part in answer
                        )
                    st.markdown(answer)
                except Exception as exc:
                    answer = "I couldn't connect to the AI service. Check your GROQ_API_KEY in .env and internet connection."
                    st.error(answer)
                    st.caption(str(exc))
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
