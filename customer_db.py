import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "smartbank.db"

INITIAL_CUSTOMERS = [
    {
        "customer_id": "CUST001",
        "name": "Arun Kumar",
        "phone": "9000000001",
        "account_number": "XXXXXX1234",
        "account_type": "Savings",
        "balance": 85000.00,
        "monthly_salary": 60000.00,
        "address": "Madurai, Tamil Nadu",
    }
]


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                account_number TEXT NOT NULL UNIQUE,
                account_type TEXT NOT NULL
                    CHECK (account_type IN ('Savings', 'Current')),
                balance REAL NOT NULL DEFAULT 0,
                monthly_salary REAL NOT NULL CHECK (monthly_salary >= 0),
                address TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for customer in INITIAL_CUSTOMERS:
            connection.execute("""
                INSERT OR IGNORE INTO customers
                (customer_id, name, phone, account_number, account_type,
                 balance, monthly_salary, address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer["customer_id"], customer["name"], customer["phone"],
                customer["account_number"], customer["account_type"],
                customer["balance"], customer["monthly_salary"],
                customer["address"]
            ))


def get_all_customers():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM customers ORDER BY customer_id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_customer(customer_id):
    if not customer_id:
        return None
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (customer_id.strip().upper(),)
        ).fetchone()
    return dict(row) if row else None


def create_customer(name, phone, account_type, monthly_salary, address):
    name = str(name).strip()
    phone = str(phone).strip()
    address = str(address).strip()
    account_type = str(account_type).strip()

    if not name or not phone or not address:
        raise ValueError("Please complete all required fields.")
    if not phone.isdigit() or len(phone) != 10:
        raise ValueError("Enter a valid 10-digit phone number.")
    if account_type not in ("Savings", "Current"):
        raise ValueError("Choose Savings or Current account.")
    try:
        monthly_salary = float(monthly_salary)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid monthly salary.")
    if monthly_salary < 0:
        raise ValueError("Monthly salary cannot be negative.")

    with get_connection() as connection:
        # Use the largest existing CUST number to avoid overwriting CUST001.
        rows = connection.execute(
            "SELECT customer_id FROM customers"
        ).fetchall()
        numbers = []
        for row in rows:
            cid = row["customer_id"]
            if cid.startswith("CUST") and cid[4:].isdigit():
                numbers.append(int(cid[4:]))
        next_number = max(numbers, default=0) + 1
        customer_id = f"CUST{next_number:03d}"
        account_number = f"XXXXXX{next_number:04d}"

        connection.execute("""
            INSERT INTO customers
            (customer_id, name, phone, account_number, account_type,
             balance, monthly_salary, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id, name, phone, account_number, account_type,
            0.0, monthly_salary, address
        ))

    return get_customer(customer_id)


initialize_database()
