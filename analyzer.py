import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import statistics
from database import ExpenseDatabase, Expense
import config

@dataclass
class SpendingInsight:
    category: str
    message: str
    severity: str  # 'info', 'warning', 'critical'
    suggestion: str
    amount: float = 0.0

@dataclass
class DailySummary:
    date: date
    total_spent: float
    expenses_count: int
    top_category: str
    top_category_amount: float
    budget_status: Dict[str, Dict[str, float]]  # category -> {spent, budget, percentage}
    insights: List[SpendingInsight]
    trends: Dict[str, float]  # comparison with previous periods

class SpendingAnalyzer:
    def __init__(self, db: ExpenseDatabase):
        self.db = db
    
    def analyze_daily_spending(self, target_date: date = None) -> DailySummary:
        """Generate comprehensive daily spending analysis"""
        if target_date is None:
            target_date = date.today()
        
        # Get today's expenses
        expenses = self.db.get_expenses(start_date=target_date, end_date=target_date)
        total_spent = sum(expense.amount for expense in expenses)
        
        # Category breakdown
        category_totals = {}
        for expense in expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = 0
            category_totals[expense.category] += expense.amount
        
        # Find top spending category
        top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else ("None", 0)
        
        # Budget analysis
        budgets = self.db.get_budgets(target_date.year, target_date.month)
        monthly_totals = self.db.get_monthly_total(target_date.year, target_date.month)
        
        budget_status = {}
        for category, budget_limit in budgets.items():
            spent = monthly_totals.get(category, 0)
            percentage = (spent / budget_limit) * 100 if budget_limit > 0 else 0
            budget_status[category] = {
                'spent': spent,
                'budget': budget_limit,
                'percentage': percentage
            }
        
        # Generate insights
        insights = self._generate_insights(expenses, budget_status, target_date)
        
        # Calculate trends
        trends = self._calculate_trends(target_date)
        
        return DailySummary(
            date=target_date,
            total_spent=total_spent,
            expenses_count=len(expenses),
            top_category=top_category[0],
            top_category_amount=top_category[1],
            budget_status=budget_status,
            insights=insights,
            trends=trends
        )
    
    def _generate_insights(self, expenses: List[Expense], budget_status: Dict, 
                          target_date: date) -> List[SpendingInsight]:
        """Generate AI-powered spending insights and suggestions"""
        insights = []
        
        # Budget warnings
        for category, status in budget_status.items():
            percentage = status['percentage']
            
            if percentage >= config.CRITICAL_THRESHOLD * 100:
                insights.append(SpendingInsight(
                    category=category,
                    message=f"Budget exceeded for {category}",
                    severity="critical",
                    suggestion=f"You've spent ${status['spent']:.2f} out of ${status['budget']:.2f} budget. Consider reducing {category.lower()} expenses or increasing the budget.",
                    amount=status['spent'] - status['budget']
                ))
            elif percentage >= config.WARNING_THRESHOLD * 100:
                insights.append(SpendingInsight(
                    category=category,
                    message=f"Approaching budget limit for {category}",
                    severity="warning",
                    suggestion=f"You've used {percentage:.1f}% of your {category.lower()} budget. Be cautious with remaining expenses.",
                    amount=status['spent']
                ))
        
        # Daily spending patterns
        daily_total = sum(expense.amount for expense in expenses)
        if daily_total > 0:
            # Compare with average daily spending
            avg_daily = self._get_average_daily_spending(target_date)
            if daily_total > avg_daily * 1.5:
                insights.append(SpendingInsight(
                    category="Overall",
                    message="High spending day detected",
                    severity="warning",
                    suggestion=f"Today's spending (${daily_total:.2f}) is significantly higher than your average (${avg_daily:.2f}). Review if these were necessary expenses.",
                    amount=daily_total - avg_daily
                ))
        
        # Frequent small expenses
        small_expenses = [e for e in expenses if e.amount < 20]
        if len(small_expenses) >= 5:
            total_small = sum(e.amount for e in small_expenses)
            insights.append(SpendingInsight(
                category="Small Purchases",
                message="Multiple small expenses detected",
                severity="info",
                suggestion=f"You made {len(small_expenses)} small purchases totaling ${total_small:.2f}. Consider bundling purchases or using a spending limit for small items.",
                amount=total_small
            ))
        
        # Category-specific insights
        insights.extend(self._generate_category_insights(expenses, target_date))
        
        return insights
    
    def _generate_category_insights(self, expenses: List[Expense], 
                                  target_date: date) -> List[SpendingInsight]:
        """Generate category-specific insights"""
        insights = []
        category_totals = {}
        
        for expense in expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = []
            category_totals[expense.category].append(expense.amount)
        
        for category, amounts in category_totals.items():
            total = sum(amounts)
            count = len(amounts)
            avg_amount = total / count if count > 0 else 0
            
            # Food & Dining insights
            if category == "Food & Dining" and total > 50:
                if count >= 3:
                    insights.append(SpendingInsight(
                        category=category,
                        message="Multiple dining expenses today",
                        severity="info",
                        suggestion="Consider meal planning or cooking at home to reduce dining costs. Batch cooking can save both time and money.",
                        amount=total
                    ))
            
            # Transportation insights
            elif category == "Transportation" and count >= 4:
                insights.append(SpendingInsight(
                    category=category,
                    message="Frequent transportation expenses",
                    severity="info",
                    suggestion="Consider using public transport passes, carpooling, or combining trips to reduce transportation costs.",
                    amount=total
                ))
            
            # Shopping insights
            elif category == "Shopping" and total > 100:
                insights.append(SpendingInsight(
                    category=category,
                    message="High shopping expenses",
                    severity="warning",
                    suggestion="Review if all purchases were necessary. Consider implementing a 24-hour waiting period for non-essential purchases.",
                    amount=total
                ))
        
        return insights
    
    def _calculate_trends(self, target_date: date) -> Dict[str, float]:
        """Calculate spending trends compared to previous periods"""
        trends = {}
        
        # Compare with yesterday
        yesterday = target_date - timedelta(days=1)
        today_total = self.db.get_daily_total(target_date)
        yesterday_total = self.db.get_daily_total(yesterday)
        
        if yesterday_total > 0:
            daily_change = ((today_total - yesterday_total) / yesterday_total) * 100
            trends['daily_change'] = daily_change
        else:
            trends['daily_change'] = 0
        
        # Compare with same day last week
        last_week = target_date - timedelta(days=7)
        last_week_total = self.db.get_daily_total(last_week)
        
        if last_week_total > 0:
            weekly_change = ((today_total - last_week_total) / last_week_total) * 100
            trends['weekly_change'] = weekly_change
        else:
            trends['weekly_change'] = 0
        
        # Monthly progress
        month_start = target_date.replace(day=1)
        monthly_expenses = self.db.get_expenses(start_date=month_start, end_date=target_date)
        monthly_total = sum(expense.amount for expense in monthly_expenses)
        
        # Calculate daily average for the month so far
        days_passed = target_date.day
        monthly_daily_avg = monthly_total / days_passed if days_passed > 0 else 0
        trends['monthly_daily_avg'] = monthly_daily_avg
        
        return trends
    
    def _get_average_daily_spending(self, target_date: date, days: int = 30) -> float:
        """Calculate average daily spending over the last N days"""
        trends = self.db.get_spending_trends(days)
        if not trends:
            return 0
        
        daily_totals = [total for _, total in trends]
        return statistics.mean(daily_totals) if daily_totals else 0
    
    def generate_improvement_suggestions(self, target_date: date = None) -> List[str]:
        """Generate personalized improvement suggestions based on spending patterns"""
        if target_date is None:
            target_date = date.today()
        
        suggestions = []
        
        # Analyze last 30 days of spending
        month_ago = target_date - timedelta(days=30)
        expenses = self.db.get_expenses(start_date=month_ago, end_date=target_date)
        
        # Category analysis
        category_totals = {}
        category_counts = {}
        
        for expense in expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = 0
                category_counts[expense.category] = 0
            category_totals[expense.category] += expense.amount
            category_counts[expense.category] += 1
        
        # Sort categories by spending
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Generate suggestions based on top spending categories
        for category, total in sorted_categories[:3]:  # Top 3 categories
            count = category_counts[category]
            avg_per_transaction = total / count if count > 0 else 0
            
            if category == "Food & Dining":
                if avg_per_transaction > 25:
                    suggestions.append(f"Your average dining expense is ${avg_per_transaction:.2f}. Try cooking more meals at home or choosing less expensive restaurants.")
                if count > 45:  # More than 1.5 times per day
                    suggestions.append("You're dining out frequently. Consider meal prepping on weekends to reduce dining expenses.")
            
            elif category == "Shopping":
                if total > 800:  # High monthly shopping
                    suggestions.append("High shopping expenses detected. Create a shopping list before going out and stick to it. Consider a 24-hour rule for non-essential purchases.")
            
            elif category == "Transportation":
                if count > 60:  # Frequent transportation
                    suggestions.append("Frequent transportation expenses. Consider getting a monthly pass, carpooling, or combining errands into single trips.")
            
            elif category == "Subscriptions":
                suggestions.append("Review your subscriptions regularly. Cancel unused services and look for annual payment discounts.")
        
        # General suggestions based on spending patterns
        total_30_days = sum(category_totals.values())
        daily_avg = total_30_days / 30
        
        if daily_avg > 100:
            suggestions.append("Your daily average spending is high. Set a daily spending limit and track expenses in real-time.")
        
        # Budget-based suggestions
        budgets = self.db.get_budgets(target_date.year, target_date.month)
        monthly_totals = self.db.get_monthly_total(target_date.year, target_date.month)
        
        over_budget_categories = []
        for category, budget in budgets.items():
            spent = monthly_totals.get(category, 0)
            if spent > budget:
                over_budget_categories.append((category, spent - budget))
        
        if over_budget_categories:
            suggestions.append("You're over budget in some categories. Consider reallocating funds or finding ways to reduce expenses in these areas.")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_spending_report(self, days: int = 7) -> Dict:
        """Generate comprehensive spending report"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        expenses = self.db.get_expenses(start_date=start_date, end_date=end_date)
        
        # Basic statistics
        total_spent = sum(expense.amount for expense in expenses)
        avg_daily = total_spent / days
        
        # Category breakdown
        category_totals = {}
        for expense in expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = 0
            category_totals[expense.category] += expense.amount
        
        # Daily breakdown
        daily_totals = {}
        for expense in expenses:
            expense_date = expense.date
            if expense_date not in daily_totals:
                daily_totals[expense_date] = 0
            daily_totals[expense_date] += expense.amount
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_spent': total_spent,
            'average_daily': avg_daily,
            'expenses_count': len(expenses),
            'category_breakdown': category_totals,
            'daily_breakdown': daily_totals,
            'top_expense': max(expenses, key=lambda x: x.amount) if expenses else None
        }