# expense_tracker_fixed.py
# Personal Expense Tracker GUI (With File Storage + Email & SMS Alerts)

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os
import smtplib
from email.mime.text import MIMEText

try:
    from twilio.rest import Client as TwilioClient
except Exception:
    TwilioClient = None

from dotenv import load_dotenv
load_dotenv()

# ---------------- Configuration ----------------
DATA_FILE = os.getenv("DATA_FILE", "expenses_data.json")

try:
    LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", "100.00"))
except ValueError:
    LOW_BALANCE_THRESHOLD = 100.00

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
USER_PHONE = os.getenv("USER_PHONE")

if USER_PHONE:
    USER_PHONE = USER_PHONE.strip()
    if USER_PHONE.isdigit() and len(USER_PHONE) == 10:
        USER_PHONE = "+91" + USER_PHONE

# ---------------- Notification ----------------
def send_email(subject, message):
    if not all([GMAIL_USER, GMAIL_PASS, RECEIVER_EMAIL]):
        return
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = RECEIVER_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
    except:
        pass

def send_sms(message):
    if TwilioClient is None or not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, USER_PHONE]):
        return
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=message, from_=TWILIO_FROM, to=USER_PHONE)
    except:
        pass

# ---------------- File Handling ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("incomes", []), data.get("expenses", [])
    return [], []

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"incomes": incomes, "expenses": expenses}, f, indent=4)

# ---------------- Helpers ----------------
def get_balance():
    return sum(i["amount"] for i in incomes) - sum(e["amount"] for e in expenses)

def check_low_balance():
    balance = get_balance()
    if balance <= LOW_BALANCE_THRESHOLD:
        alert = f"⚠ Low Balance Alert! Your balance is ₹{balance:.2f}"
        send_email("Low Balance Alert", alert)
        send_sms(alert)
        messagebox.showwarning("Low Balance", alert)

# ---------------- Core Functions ----------------
def add_income():
    try:
        amount = float(income_amount.get())
    except:
        messagebox.showerror("Error", "Invalid income amount")
        return

    incomes.append({
        "amount": amount,
        "category": income_category.get() or "Salary",
        "desc": income_desc.get() or "No description",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data()
    update_summary()
    show_incomes()
    check_low_balance()

def add_expense():
    try:
        amount = float(expense_amount.get())
    except:
        messagebox.showerror("Error", "Invalid expense amount")
        return

    expenses.append({
        "amount": amount,
        "category": expense_category.get() or "General",
        "desc": expense_desc.get() or "No description",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data()
    update_summary()
    show_expenses()
    check_low_balance()

# -------- CLEAR FUNCTIONS --------
def clear_recent_income():
    if incomes:
        incomes.pop()
        save_data()
        show_incomes()
        update_summary()

def clear_all_income():
    if messagebox.askyesno("Confirm", "Clear all income records?"):
        incomes.clear()
        save_data()
        show_incomes()
        update_summary()

        msg = "All income records have been cleared.\nTotal Income is now ₹0.00"
        send_email("Income Cleared Alert", msg)
        send_sms(msg)

def clear_recent_expense():
    if expenses:
        expenses.pop()
        save_data()
        show_expenses()
        update_summary()

def clear_all_expense():
    if messagebox.askyesno("Confirm", "Clear all expense records?"):
        expenses.clear()
        save_data()
        show_expenses()
        update_summary()

def show_incomes():
    income_list.delete(*income_list.get_children())
    for i, inc in enumerate(incomes, 1):
        income_list.insert("", "end",
            values=(i, inc["date"], inc["category"], inc["desc"], f"₹{inc['amount']:.2f}"))

def show_expenses():
    expense_list.delete(*expense_list.get_children())
    for i, exp in enumerate(expenses, 1):
        expense_list.insert("", "end",
            values=(i, exp["date"], exp["category"], exp["desc"], f"₹{exp['amount']:.2f}"))

def update_summary():
    label_income_val.config(text=f"₹{sum(i['amount'] for i in incomes):.2f}")
    label_expense_val.config(text=f"₹{sum(e['amount'] for e in expenses):.2f}")
    label_balance_val.config(text=f"₹{get_balance():.2f}")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Personal Expense Tracker with Notifications")
root.geometry("900x680")

# -------- Income Section --------
frame_income = tk.LabelFrame(root, text="➕ Add Income", padx=10, pady=10)
frame_income.pack(fill="x", padx=10, pady=5)

income_amount = tk.StringVar()
income_category = tk.StringVar(value="Salary")
income_desc = tk.StringVar()

tk.Label(frame_income, text="Amount (₹)").grid(row=0, column=0)
tk.Entry(frame_income, textvariable=income_amount).grid(row=0, column=1)

tk.Label(frame_income, text="Category").grid(row=0, column=2)
ttk.Combobox(
    frame_income,
    textvariable=income_category,
    values=["Salary", "Side Income", "Other"],
    state="readonly",
    width=15
).grid(row=0, column=3)

tk.Label(frame_income, text="Description").grid(row=0, column=4)
tk.Entry(frame_income, textvariable=income_desc, width=20).grid(row=0, column=5)

tk.Button(frame_income, text="Add Income", bg="green", fg="white",
          command=add_income).grid(row=0, column=6, padx=5)

tk.Button(frame_income, text="Clear Recent Income",
          command=clear_recent_income).grid(row=1, column=3, pady=5)

tk.Button(frame_income, text="Clear All Income",
          command=clear_all_income).grid(row=1, column=4, pady=5)

# -------- Expense Section --------
frame_expense = tk.LabelFrame(root, text="➖ Add Expense", padx=10, pady=10)
frame_expense.pack(fill="x", padx=10, pady=5)

expense_amount = tk.StringVar()
expense_category = tk.StringVar()
expense_desc = tk.StringVar()

tk.Label(frame_expense, text="Amount (₹)").grid(row=0, column=0)
tk.Entry(frame_expense, textvariable=expense_amount).grid(row=0, column=1)

tk.Label(frame_expense, text="Category").grid(row=0, column=2)
tk.Entry(frame_expense, textvariable=expense_category).grid(row=0, column=3)

tk.Label(frame_expense, text="Description").grid(row=0, column=4)
tk.Entry(frame_expense, textvariable=expense_desc, width=20).grid(row=0, column=5)

tk.Button(frame_expense, text="Add Expense", bg="red", fg="white",
          command=add_expense).grid(row=0, column=6, padx=5)

tk.Button(frame_expense, text="Clear Recent Expense",
          command=clear_recent_expense).grid(row=1, column=3, pady=5)

tk.Button(frame_expense, text="Clear All Expense",
          command=clear_all_expense).grid(row=1, column=4, pady=5)

# -------- Tables --------
income_list = ttk.Treeview(root, columns=("S.No","Date","Category","Desc","Amount"), show="headings", height=6)
for c in income_list["columns"]:
    income_list.heading(c, text=c)
income_list.pack(fill="x", padx=10)

expense_list = ttk.Treeview(root, columns=("S.No","Date","Category","Desc","Amount"), show="headings", height=6)
for c in expense_list["columns"]:
    expense_list.heading(c, text=c)
expense_list.pack(fill="x", padx=10)

# -------- Summary --------
frame_summary = tk.LabelFrame(root, text="Summary", padx=10, pady=10)
frame_summary.pack(fill="x", padx=10, pady=10)

label_income_val = tk.Label(frame_summary, text="₹0.00")
label_income_val.grid(row=0, column=1)
label_expense_val = tk.Label(frame_summary, text="₹0.00")
label_expense_val.grid(row=0, column=3)
label_balance_val = tk.Label(frame_summary, text="₹0.00")
label_balance_val.grid(row=0, column=5)

tk.Label(frame_summary, text="Total Income").grid(row=0, column=0)
tk.Label(frame_summary, text="Total Expense").grid(row=0, column=2)
tk.Label(frame_summary, text="Balance").grid(row=0, column=4)

# ---------------- Main ----------------
incomes, expenses = load_data()
show_incomes()
show_expenses()
update_summary()

root.mainloop()
