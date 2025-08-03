import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_PATH = "expenses.db"
BACKUP_DIR = "backups"

# OpenAI configuration (optional - for AI-powered insights)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Expense categories
EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Education",
    "Travel",
    "Groceries",
    "Subscriptions",
    "Investment",
    "Emergency",
    "Other"
]

# Budget limits (monthly defaults - can be customized)
DEFAULT_MONTHLY_BUDGETS = {
    "Food & Dining": 500,
    "Transportation": 200,
    "Shopping": 300,
    "Entertainment": 200,
    "Bills & Utilities": 400,
    "Healthcare": 150,
    "Education": 100,
    "Travel": 300,
    "Groceries": 400,
    "Subscriptions": 100,
    "Investment": 500,
    "Emergency": 200,
    "Other": 200
}

# Notification settings
DAILY_SUMMARY_TIME = "23:00"  # 11 PM
NOTIFICATION_ENABLED = True

# Analysis settings
SPENDING_TREND_DAYS = 30
WARNING_THRESHOLD = 0.8  # 80% of budget
CRITICAL_THRESHOLD = 1.0  # 100% of budget