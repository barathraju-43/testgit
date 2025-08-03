#!/usr/bin/env python3
"""
Expense Tracker Agent - Your Personal Finance Assistant

A comprehensive expense tracking system that monitors daily spending,
provides intelligent insights, and delivers automated daily summaries.
"""

import typer
from typing import Optional, List
from datetime import date, datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
import sys
import os

# Import our modules
from database import ExpenseDatabase, Expense
from analyzer import SpendingAnalyzer
from scheduler import ExpenseScheduler
import config

# Initialize Rich console
console = Console()
app = typer.Typer(help="💰 Expense Tracker Agent - Your Personal Finance Assistant")

# Global instances
db = ExpenseDatabase()
analyzer = SpendingAnalyzer(db)
scheduler = ExpenseScheduler(db, analyzer)

@app.command("add")
def add_expense(
    amount: float = typer.Argument(..., help="Amount spent"),
    category: str = typer.Option(None, "--category", "-c", help="Expense category"),
    description: str = typer.Option("", "--description", "-d", help="Description of the expense"),
    date_str: str = typer.Option(None, "--date", help="Date (YYYY-MM-DD), defaults to today"),
    tags: str = typer.Option("", "--tags", "-t", help="Comma-separated tags")
):
    """💸 Add a new expense"""
    
    # Validate amount
    if amount <= 0:
        console.print("❌ Amount must be positive", style="red")
        raise typer.Exit(1)
    
    # Handle category selection
    if not category:
        console.print("\n📂 Available Categories:", style="bold blue")
        for i, cat in enumerate(config.EXPENSE_CATEGORIES, 1):
            console.print(f"{i:2d}. {cat}")
        
        while True:
            try:
                choice = Prompt.ask("\nSelect category (number or name)", default="13")
                if choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(config.EXPENSE_CATEGORIES):
                        category = config.EXPENSE_CATEGORIES[choice_idx]
                        break
                else:
                    if choice in config.EXPENSE_CATEGORIES:
                        category = choice
                        break
                console.print("❌ Invalid choice. Please try again.", style="red")
            except KeyboardInterrupt:
                console.print("\n👋 Cancelled")
                raise typer.Exit()
    
    # Handle date
    expense_date = date.today()
    if date_str:
        try:
            expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            console.print("❌ Invalid date format. Use YYYY-MM-DD", style="red")
            raise typer.Exit(1)
    
    # Handle description
    if not description:
        description = Prompt.ask("Description (optional)", default="")
    
    # Handle tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    try:
        # Add expense to database
        expense_id = db.add_expense(amount, category, description, expense_date, tag_list)
        
        # Show confirmation
        console.print(f"\n✅ Expense added successfully!", style="green")
        console.print(f"💰 Amount: ${amount:.2f}")
        console.print(f"📂 Category: {category}")
        console.print(f"📅 Date: {expense_date}")
        if description:
            console.print(f"📝 Description: {description}")
        if tag_list:
            console.print(f"🏷️ Tags: {', '.join(tag_list)}")
        
        # Show quick daily summary
        daily_total = db.get_daily_total(expense_date)
        console.print(f"\n📊 Today's total: ${daily_total:.2f}")
        
        # Check for budget warnings
        budgets = db.get_budgets(expense_date.year, expense_date.month)
        monthly_totals = db.get_monthly_total(expense_date.year, expense_date.month)
        
        if category in budgets:
            spent = monthly_totals.get(category, 0)
            budget = budgets[category]
            percentage = (spent / budget) * 100 if budget > 0 else 0
            
            if percentage >= 100:
                console.print(f"🚨 Warning: You've exceeded your {category} budget!", style="red")
            elif percentage >= 80:
                console.print(f"⚠️ Warning: You've used {percentage:.1f}% of your {category} budget", style="yellow")
        
    except Exception as e:
        console.print(f"❌ Error adding expense: {e}", style="red")
        raise typer.Exit(1)

@app.command("list")
def list_expenses(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to show"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of expenses to show")
):
    """📋 List recent expenses"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    expenses = db.get_expenses(start_date=start_date, end_date=end_date, category=category)
    
    if not expenses:
        console.print("📭 No expenses found for the specified period", style="yellow")
        return
    
    # Limit results
    expenses = expenses[:limit]
    
    # Create table
    table = Table(title=f"💸 Recent Expenses ({start_date} to {end_date})")
    table.add_column("Date", style="cyan")
    table.add_column("Amount", style="green")
    table.add_column("Category", style="blue")
    table.add_column("Description", style="white")
    table.add_column("Tags", style="magenta")
    
    total = 0
    for expense in expenses:
        tags_str = ", ".join(expense.tags) if expense.tags else ""
        table.add_row(
            str(expense.date),
            f"${expense.amount:.2f}",
            expense.category,
            expense.description[:30] + "..." if len(expense.description) > 30 else expense.description,
            tags_str
        )
        total += expense.amount
    
    console.print(table)
    console.print(f"\n💰 Total: ${total:.2f} | 📊 Average: ${total/len(expenses):.2f}")

@app.command("summary")
def show_summary(
    target_date: str = typer.Option(None, "--date", help="Date for summary (YYYY-MM-DD), defaults to today")
):
    """📊 Show detailed spending summary for a specific date"""
    
    summary_date = date.today()
    if target_date:
        try:
            summary_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            console.print("❌ Invalid date format. Use YYYY-MM-DD", style="red")
            raise typer.Exit(1)
    
    summary = analyzer.analyze_daily_spending(summary_date)
    scheduler._display_daily_summary(summary)

@app.command("report")
def show_report(
    days: int = typer.Option(7, "--days", "-d", help="Number of days for the report"),
    category: str = typer.Option(None, "--category", "-c", help="Focus on specific category")
):
    """📈 Generate spending report"""
    
    if category:
        # Category-specific report
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        expenses = db.get_expenses(start_date=start_date, end_date=end_date, category=category)
        
        if not expenses:
            console.print(f"📭 No {category} expenses found", style="yellow")
            return
        
        total = sum(expense.amount for expense in expenses)
        avg_daily = total / days
        avg_per_transaction = total / len(expenses)
        
        console.print(f"\n📊 {category.upper()} REPORT ({start_date} to {end_date})", style="bold blue")
        console.print(f"💰 Total Spent: ${total:.2f}")
        console.print(f"📊 Daily Average: ${avg_daily:.2f}")
        console.print(f"💳 Average per Transaction: ${avg_per_transaction:.2f}")
        console.print(f"📝 Number of Transactions: {len(expenses)}")
        
        # Show recent transactions
        console.print(f"\n📋 Recent {category} Expenses:")
        for expense in expenses[:10]:
            console.print(f"  • {expense.date}: ${expense.amount:.2f} - {expense.description}")
    
    else:
        # General report
        report = analyzer.get_spending_report(days)
        scheduler._display_weekly_report(report)

@app.command("budget")
def manage_budget(
    category: str = typer.Option(None, "--category", "-c", help="Category to set budget for"),
    amount: float = typer.Option(None, "--amount", "-a", help="Budget amount"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current budgets")
):
    """💳 Manage budgets"""
    
    if show or (not category and not amount):
        # Show current budgets
        today = date.today()
        budgets = db.get_budgets(today.year, today.month)
        monthly_totals = db.get_monthly_total(today.year, today.month)
        
        console.print(f"\n💳 BUDGET STATUS - {today.strftime('%B %Y')}", style="bold blue")
        
        table = Table()
        table.add_column("Category", style="cyan")
        table.add_column("Budget", style="green")
        table.add_column("Spent", style="white")
        table.add_column("Remaining", style="yellow")
        table.add_column("Progress", style="white")
        table.add_column("Status", style="white")
        
        total_budget = 0
        total_spent = 0
        
        for cat, budget in budgets.items():
            spent = monthly_totals.get(cat, 0)
            remaining = budget - spent
            percentage = (spent / budget) * 100 if budget > 0 else 0
            
            # Progress bar
            progress_bar = scheduler._create_progress_bar(percentage)
            
            # Status
            if percentage >= 100:
                status = Text("🚨 OVER", style="red")
            elif percentage >= 80:
                status = Text("⚠️ HIGH", style="yellow")
            else:
                status = Text("✅ OK", style="green")
            
            table.add_row(
                cat,
                f"${budget:.2f}",
                f"${spent:.2f}",
                f"${remaining:.2f}",
                progress_bar,
                status
            )
            
            total_budget += budget
            total_spent += spent
        
        console.print(table)
        
        overall_percentage = (total_spent / total_budget) * 100 if total_budget > 0 else 0
        console.print(f"\n💰 Overall: ${total_spent:.2f} / ${total_budget:.2f} ({overall_percentage:.1f}%)")
        
        return
    
    if not category:
        console.print("📂 Available Categories:", style="bold blue")
        for i, cat in enumerate(config.EXPENSE_CATEGORIES, 1):
            console.print(f"{i:2d}. {cat}")
        
        choice = Prompt.ask("\nSelect category (number or name)")
        if choice.isdigit():
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(config.EXPENSE_CATEGORIES):
                category = config.EXPENSE_CATEGORIES[choice_idx]
        else:
            category = choice
    
    if not amount:
        current_budget = db.get_budgets().get(category, 0)
        amount = float(Prompt.ask(f"Budget amount for {category}", default=str(current_budget)))
    
    if amount <= 0:
        console.print("❌ Budget amount must be positive", style="red")
        raise typer.Exit(1)
    
    try:
        db.set_budget(category, amount)
        console.print(f"✅ Budget set: {category} = ${amount:.2f}", style="green")
    except Exception as e:
        console.print(f"❌ Error setting budget: {e}", style="red")
        raise typer.Exit(1)

@app.command("insights")
def show_insights():
    """💡 Get AI-powered spending insights and suggestions"""
    
    suggestions = analyzer.generate_improvement_suggestions()
    
    if suggestions:
        console.print("\n🎯 PERSONALIZED SPENDING INSIGHTS", style="bold magenta")
        console.print("Based on your last 30 days of spending patterns:\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            panel = Panel(
                suggestion,
                title=f"💡 Insight #{i}",
                border_style="blue"
            )
            console.print(panel)
    else:
        console.print("📊 Not enough data for insights. Add more expenses to get personalized suggestions!", style="yellow")

@app.command("start")
def start_scheduler():
    """🚀 Start the daily summary scheduler"""
    
    scheduler.start_scheduler()
    
    console.print("✅ Expense tracker agent is now running!", style="green")
    console.print("📅 You'll receive daily summaries at 11 PM")
    console.print("📊 Weekly reports every Sunday at 9 AM")
    console.print("💳 Monthly budget checks on the 1st of each month")
    console.print("\n⏰ Next summary:", scheduler.get_next_summary_time())
    console.print("\n💡 Tip: Keep this terminal open or run in background for automatic summaries")

@app.command("stop")
def stop_scheduler():
    """⏹️ Stop the daily summary scheduler"""
    
    scheduler.stop_scheduler()
    console.print("⏹️ Scheduler stopped", style="yellow")

@app.command("test-summary")
def test_summary():
    """🧪 Test daily summary (for demonstration)"""
    
    console.print("🧪 Generating test daily summary...\n")
    scheduler.force_daily_summary()

@app.command("delete")
def delete_expense(
    expense_id: int = typer.Argument(..., help="ID of the expense to delete")
):
    """🗑️ Delete an expense"""
    
    # First, show the expense details
    expenses = db.get_expenses()
    target_expense = None
    
    for expense in expenses:
        if expense.id == expense_id:
            target_expense = expense
            break
    
    if not target_expense:
        console.print(f"❌ Expense with ID {expense_id} not found", style="red")
        raise typer.Exit(1)
    
    # Show expense details
    console.print(f"\n🗑️ Delete this expense?")
    console.print(f"💰 Amount: ${target_expense.amount:.2f}")
    console.print(f"📂 Category: {target_expense.category}")
    console.print(f"📅 Date: {target_expense.date}")
    console.print(f"📝 Description: {target_expense.description}")
    
    if Confirm.ask("Are you sure?"):
        if db.delete_expense(expense_id):
            console.print("✅ Expense deleted successfully", style="green")
        else:
            console.print("❌ Failed to delete expense", style="red")
    else:
        console.print("👋 Cancelled")

@app.command("search")
def search_expenses(
    query: str = typer.Argument(..., help="Search term"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to search")
):
    """🔍 Search expenses by description or category"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    all_expenses = db.get_expenses(start_date=start_date, end_date=end_date)
    
    # Filter expenses that match the query
    matching_expenses = []
    query_lower = query.lower()
    
    for expense in all_expenses:
        if (query_lower in expense.description.lower() or 
            query_lower in expense.category.lower() or
            any(query_lower in tag.lower() for tag in expense.tags)):
            matching_expenses.append(expense)
    
    if not matching_expenses:
        console.print(f"🔍 No expenses found matching '{query}'", style="yellow")
        return
    
    # Display results
    table = Table(title=f"🔍 Search Results for '{query}'")
    table.add_column("ID", style="dim")
    table.add_column("Date", style="cyan")
    table.add_column("Amount", style="green")
    table.add_column("Category", style="blue")
    table.add_column("Description", style="white")
    
    total = 0
    for expense in matching_expenses:
        table.add_row(
            str(expense.id),
            str(expense.date),
            f"${expense.amount:.2f}",
            expense.category,
            expense.description
        )
        total += expense.amount
    
    console.print(table)
    console.print(f"\n💰 Total: ${total:.2f} | 📊 Count: {len(matching_expenses)}")

@app.command("export")
def export_data(
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or json"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to export"),
    output: str = typer.Option(None, "--output", "-o", help="Output filename")
):
    """📤 Export expense data"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    expenses = db.get_expenses(start_date=start_date, end_date=end_date)
    
    if not expenses:
        console.print("📭 No expenses to export", style="yellow")
        return
    
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"expenses_{timestamp}.{format}"
    
    try:
        if format.lower() == "csv":
            import csv
            with open(output, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Date', 'Amount', 'Category', 'Description', 'Tags'])
                for expense in expenses:
                    writer.writerow([
                        expense.id,
                        expense.date,
                        expense.amount,
                        expense.category,
                        expense.description,
                        ','.join(expense.tags) if expense.tags else ''
                    ])
        
        elif format.lower() == "json":
            import json
            with open(output, 'w', encoding='utf-8') as jsonfile:
                data = [expense.to_dict() for expense in expenses]
                json.dump(data, jsonfile, indent=2, default=str)
        
        else:
            console.print("❌ Unsupported format. Use 'csv' or 'json'", style="red")
            raise typer.Exit(1)
        
        console.print(f"✅ Exported {len(expenses)} expenses to {output}", style="green")
    
    except Exception as e:
        console.print(f"❌ Export failed: {e}", style="red")
        raise typer.Exit(1)

@app.command("stats")
def show_statistics():
    """📊 Show comprehensive spending statistics"""
    
    console.print("\n📊 EXPENSE TRACKER STATISTICS", style="bold blue")
    
    # Get data for different periods
    today = date.today()
    
    # Today
    today_total = db.get_daily_total(today)
    
    # This week
    week_start = today - timedelta(days=today.weekday())
    week_expenses = db.get_expenses(start_date=week_start, end_date=today)
    week_total = sum(e.amount for e in week_expenses)
    
    # This month
    month_start = today.replace(day=1)
    month_expenses = db.get_expenses(start_date=month_start, end_date=today)
    month_total = sum(e.amount for e in month_expenses)
    
    # All time
    all_expenses = db.get_expenses()
    all_total = sum(e.amount for e in all_expenses)
    
    # Create stats table
    stats_table = Table()
    stats_table.add_column("Period", style="cyan")
    stats_table.add_column("Total Spent", style="green")
    stats_table.add_column("Transactions", style="yellow")
    stats_table.add_column("Average", style="white")
    
    stats_table.add_row("Today", f"${today_total:.2f}", "1" if today_total > 0 else "0", f"${today_total:.2f}")
    stats_table.add_row("This Week", f"${week_total:.2f}", str(len(week_expenses)), f"${week_total/max(len(week_expenses), 1):.2f}")
    stats_table.add_row("This Month", f"${month_total:.2f}", str(len(month_expenses)), f"${month_total/max(len(month_expenses), 1):.2f}")
    stats_table.add_row("All Time", f"${all_total:.2f}", str(len(all_expenses)), f"${all_total/max(len(all_expenses), 1):.2f}")
    
    console.print(stats_table)
    
    # Top categories
    if all_expenses:
        category_totals = {}
        for expense in all_expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = 0
            category_totals[expense.category] += expense.amount
        
        console.print("\n🏆 TOP SPENDING CATEGORIES (All Time)", style="bold yellow")
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        for i, (category, total) in enumerate(sorted_categories[:5], 1):
            percentage = (total / all_total) * 100
            console.print(f"{i}. {category}: ${total:.2f} ({percentage:.1f}%)")

def main():
    """Main entry point"""
    
    # Show welcome message on first run
    if len(sys.argv) == 1:
        console.print("""
💰 Welcome to Expense Tracker Agent!

Your personal finance assistant that helps you:
• 📝 Track daily expenses with smart categorization
• 📊 Get intelligent spending insights and suggestions  
• 📅 Receive automated daily summaries at 11 PM
• 💳 Monitor budgets and spending patterns
• 🎯 Improve your financial habits

Quick start:
  expense-tracker add 15.50 --category "Food & Dining" --description "Lunch"
  expense-tracker summary
  expense-tracker start    # Begin daily summaries
  
Type 'expense-tracker --help' for all commands.
        """, style="bold blue")
        return
    
    app()

if __name__ == "__main__":
    main()