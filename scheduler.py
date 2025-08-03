import schedule
import time
import threading
from datetime import datetime, date
from typing import Callable, Optional
import logging
from database import ExpenseDatabase
from analyzer import SpendingAnalyzer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExpenseScheduler:
    def __init__(self, db: ExpenseDatabase, analyzer: SpendingAnalyzer):
        self.db = db
        self.analyzer = analyzer
        self.console = Console()
        self.is_running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.info("Scheduler is already running")
            return
        
        # Schedule daily summary at 11 PM
        schedule.every().day.at(config.DAILY_SUMMARY_TIME).do(self.send_daily_summary)
        
        # Schedule weekly report every Sunday at 9 AM
        schedule.every().sunday.at("09:00").do(self.send_weekly_report)
        
        # Schedule monthly budget check on the 1st of each month
        schedule.every().month.do(self.monthly_budget_check)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Expense tracker scheduler started")
        print("📅 Daily summary scheduler started - you'll receive reports at 11 PM every day")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Expense tracker scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def send_daily_summary(self):
        """Generate and display daily spending summary"""
        try:
            summary = self.analyzer.analyze_daily_spending()
            self._display_daily_summary(summary)
            
            # Log the summary
            logger.info(f"Daily summary generated - Total spent: ${summary.total_spent:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
    
    def send_weekly_report(self):
        """Generate and display weekly spending report"""
        try:
            report = self.analyzer.get_spending_report(days=7)
            self._display_weekly_report(report)
            
            logger.info(f"Weekly report generated - Total spent: ${report['total_spent']:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
    
    def monthly_budget_check(self):
        """Check monthly budget status and send alerts"""
        try:
            today = date.today()
            budgets = self.db.get_budgets(today.year, today.month)
            monthly_totals = self.db.get_monthly_total(today.year, today.month)
            
            self._display_monthly_budget_status(budgets, monthly_totals)
            
            logger.info("Monthly budget check completed")
            
        except Exception as e:
            logger.error(f"Error in monthly budget check: {e}")
    
    def _display_daily_summary(self, summary):
        """Display formatted daily summary"""
        self.console.print("\n" + "="*60)
        self.console.print(f"📊 DAILY SPENDING SUMMARY - {summary.date}", style="bold blue")
        self.console.print("="*60)
        
        # Basic stats
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")
        
        stats_table.add_row("💰 Total Spent", f"${summary.total_spent:.2f}")
        stats_table.add_row("📝 Transactions", str(summary.expenses_count))
        stats_table.add_row("🏆 Top Category", f"{summary.top_category} (${summary.top_category_amount:.2f})")
        
        # Trends
        if summary.trends.get('daily_change', 0) != 0:
            change = summary.trends['daily_change']
            trend_icon = "📈" if change > 0 else "📉"
            trend_color = "red" if change > 0 else "green"
            stats_table.add_row("📊 vs Yesterday", f"{trend_icon} {change:+.1f}%", style=trend_color)
        
        if summary.trends.get('weekly_change', 0) != 0:
            change = summary.trends['weekly_change']
            trend_icon = "📈" if change > 0 else "📉"
            trend_color = "red" if change > 0 else "green"
            stats_table.add_row("📅 vs Last Week", f"{trend_icon} {change:+.1f}%", style=trend_color)
        
        self.console.print(stats_table)
        
        # Budget status
        if summary.budget_status:
            self.console.print("\n💳 BUDGET STATUS", style="bold yellow")
            budget_table = Table()
            budget_table.add_column("Category", style="cyan")
            budget_table.add_column("Spent", style="white")
            budget_table.add_column("Budget", style="white")
            budget_table.add_column("Progress", style="white")
            budget_table.add_column("Status", style="white")
            
            for category, status in summary.budget_status.items():
                if status['spent'] > 0 or status['percentage'] > 50:  # Only show relevant categories
                    percentage = status['percentage']
                    progress_bar = self._create_progress_bar(percentage)
                    
                    if percentage >= 100:
                        status_text = "🚨 OVER"
                        status_style = "red"
                    elif percentage >= 80:
                        status_text = "⚠️ HIGH"
                        status_style = "yellow"
                    else:
                        status_text = "✅ OK"
                        status_style = "green"
                    
                    budget_table.add_row(
                        category,
                        f"${status['spent']:.2f}",
                        f"${status['budget']:.2f}",
                        progress_bar,
                        Text(status_text, style=status_style)
                    )
            
            self.console.print(budget_table)
        
        # Insights
        if summary.insights:
            self.console.print("\n💡 INSIGHTS & SUGGESTIONS", style="bold green")
            for insight in summary.insights:
                icon = {"critical": "🚨", "warning": "⚠️", "info": "💡"}[insight.severity]
                color = {"critical": "red", "warning": "yellow", "info": "blue"}[insight.severity]
                
                panel = Panel(
                    f"{insight.message}\n\n💡 {insight.suggestion}",
                    title=f"{icon} {insight.category}",
                    border_style=color
                )
                self.console.print(panel)
        
        # Improvement suggestions
        suggestions = self.analyzer.generate_improvement_suggestions()
        if suggestions:
            self.console.print("\n🎯 IMPROVEMENT SUGGESTIONS", style="bold magenta")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"{i}. {suggestion}", style="white")
        
        self.console.print("\n" + "="*60 + "\n")
    
    def _display_weekly_report(self, report):
        """Display formatted weekly report"""
        self.console.print("\n" + "="*60)
        self.console.print("📈 WEEKLY SPENDING REPORT", style="bold blue")
        self.console.print(f"📅 Period: {report['period']}")
        self.console.print("="*60)
        
        # Summary stats
        self.console.print(f"💰 Total Spent: ${report['total_spent']:.2f}")
        self.console.print(f"📊 Daily Average: ${report['average_daily']:.2f}")
        self.console.print(f"📝 Total Transactions: {report['expenses_count']}")
        
        if report['top_expense']:
            self.console.print(f"🏆 Largest Expense: ${report['top_expense'].amount:.2f} ({report['top_expense'].category})")
        
        # Category breakdown
        if report['category_breakdown']:
            self.console.print("\n📊 CATEGORY BREAKDOWN", style="bold yellow")
            category_table = Table()
            category_table.add_column("Category", style="cyan")
            category_table.add_column("Amount", style="white")
            category_table.add_column("Percentage", style="white")
            
            sorted_categories = sorted(report['category_breakdown'].items(), 
                                     key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_categories:
                percentage = (amount / report['total_spent']) * 100 if report['total_spent'] > 0 else 0
                category_table.add_row(
                    category,
                    f"${amount:.2f}",
                    f"{percentage:.1f}%"
                )
            
            self.console.print(category_table)
        
        self.console.print("\n" + "="*60 + "\n")
    
    def _display_monthly_budget_status(self, budgets, monthly_totals):
        """Display monthly budget status"""
        self.console.print("\n" + "="*60)
        self.console.print("📊 MONTHLY BUDGET CHECK", style="bold blue")
        self.console.print("="*60)
        
        budget_table = Table()
        budget_table.add_column("Category", style="cyan")
        budget_table.add_column("Spent", style="white")
        budget_table.add_column("Budget", style="white")
        budget_table.add_column("Remaining", style="white")
        budget_table.add_column("Status", style="white")
        
        total_spent = sum(monthly_totals.values())
        total_budget = sum(budgets.values())
        
        for category, budget in budgets.items():
            spent = monthly_totals.get(category, 0)
            remaining = budget - spent
            percentage = (spent / budget) * 100 if budget > 0 else 0
            
            if percentage >= 100:
                status_text = "🚨 OVER BUDGET"
                status_style = "red"
            elif percentage >= 80:
                status_text = "⚠️ CLOSE TO LIMIT"
                status_style = "yellow"
            else:
                status_text = "✅ ON TRACK"
                status_style = "green"
            
            budget_table.add_row(
                category,
                f"${spent:.2f}",
                f"${budget:.2f}",
                f"${remaining:.2f}",
                Text(status_text, style=status_style)
            )
        
        self.console.print(budget_table)
        
        # Overall summary
        overall_percentage = (total_spent / total_budget) * 100 if total_budget > 0 else 0
        self.console.print(f"\n💰 Total Spent: ${total_spent:.2f} / ${total_budget:.2f} ({overall_percentage:.1f}%)")
        
        self.console.print("\n" + "="*60 + "\n")
    
    def _create_progress_bar(self, percentage, width=20):
        """Create a text-based progress bar"""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percentage:.1f}%"
    
    def force_daily_summary(self):
        """Manually trigger daily summary (for testing)"""
        self.send_daily_summary()
    
    def force_weekly_report(self):
        """Manually trigger weekly report (for testing)"""
        self.send_weekly_report()
    
    def get_next_summary_time(self):
        """Get the next scheduled summary time"""
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "No scheduled runs"