import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import config

@dataclass
class Expense:
    id: Optional[int]
    amount: float
    category: str
    description: str
    date: date
    created_at: datetime
    tags: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'tags': self.tags or []
        }

@dataclass
class Budget:
    id: Optional[int]
    category: str
    monthly_limit: float
    year: int
    month: int
    created_at: datetime

class ExpenseDatabase:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Expenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT  -- JSON array of tags
                )
            ''')
            
            # Budgets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    monthly_limit REAL NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, year, month)
                )
            ''')
            
            # Settings table for user preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_expense(self, amount: float, category: str, description: str, 
                   expense_date: date = None, tags: List[str] = None) -> int:
        """Add a new expense record"""
        if expense_date is None:
            expense_date = date.today()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO expenses (amount, category, description, date, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (amount, category, description, expense_date, json.dumps(tags or [])))
            
            expense_id = cursor.lastrowid
            conn.commit()
            return expense_id
    
    def get_expenses(self, start_date: date = None, end_date: date = None, 
                    category: str = None) -> List[Expense]:
        """Retrieve expenses with optional filters"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, amount, category, description, date, created_at, tags FROM expenses WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY date DESC, created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            expenses = []
            for row in rows:
                tags = json.loads(row[6]) if row[6] else []
                expense = Expense(
                    id=row[0],
                    amount=row[1],
                    category=row[2],
                    description=row[3],
                    date=datetime.fromisoformat(row[4]).date(),
                    created_at=datetime.fromisoformat(row[5]),
                    tags=tags
                )
                expenses.append(expense)
            
            return expenses
    
    def get_daily_total(self, target_date: date = None) -> float:
        """Get total spending for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        expenses = self.get_expenses(start_date=target_date, end_date=target_date)
        return sum(expense.amount for expense in expenses)
    
    def get_monthly_total(self, year: int = None, month: int = None) -> Dict[str, float]:
        """Get monthly spending totals by category"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        expenses = self.get_expenses(start_date=start_date, end_date=end_date)
        
        totals = {}
        for expense in expenses:
            if expense.category not in totals:
                totals[expense.category] = 0
            totals[expense.category] += expense.amount
        
        return totals
    
    def set_budget(self, category: str, monthly_limit: float, 
                   year: int = None, month: int = None) -> int:
        """Set or update budget for a category"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets (category, monthly_limit, year, month)
                VALUES (?, ?, ?, ?)
            ''', (category, monthly_limit, year, month))
            
            budget_id = cursor.lastrowid
            conn.commit()
            return budget_id
    
    def get_budgets(self, year: int = None, month: int = None) -> Dict[str, float]:
        """Get budget limits for a specific month"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, monthly_limit FROM budgets 
                WHERE year = ? AND month = ?
            ''', (year, month))
            
            rows = cursor.fetchall()
            budgets = {row[0]: row[1] for row in rows}
            
            # Fill in default budgets for missing categories
            for category, default_limit in config.DEFAULT_MONTHLY_BUDGETS.items():
                if category not in budgets:
                    budgets[category] = default_limit
            
            return budgets
    
    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_spending_trends(self, days: int = 30) -> List[Tuple[date, float]]:
        """Get daily spending totals for the last N days"""
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, SUM(amount) as daily_total
                FROM expenses 
                WHERE date >= ? AND date <= ?
                GROUP BY date
                ORDER BY date
            ''', (start_date, end_date))
            
            rows = cursor.fetchall()
            return [(datetime.fromisoformat(row[0]).date(), row[1]) for row in rows]