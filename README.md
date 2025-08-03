# 💰 Expense Tracker Agent

Your Personal Finance Assistant that tracks daily spending, provides intelligent insights, and delivers automated summaries.

## 🌟 Features

- **📝 Smart Expense Tracking**: Easy expense entry with categorization and tagging
- **📊 Intelligent Analysis**: AI-powered spending insights and improvement suggestions
- **📅 Automated Summaries**: Daily reports delivered at 11 PM automatically
- **💳 Budget Management**: Set and monitor budgets with real-time alerts
- **📈 Comprehensive Reports**: Weekly, monthly, and custom period reports
- **🔍 Advanced Search**: Find expenses by description, category, or tags
- **📤 Data Export**: Export your data in CSV or JSON format
- **🎯 Personalized Insights**: Get tailored advice based on your spending patterns

## 🚀 Quick Start

### Installation

1. **Clone or download the expense tracker:**
   ```bash
   # If you have git
   git clone <repository-url>
   cd expense-tracker
   
   # Or download and extract the files
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Make the script executable (Linux/Mac):**
   ```bash
   chmod +x expense_tracker.py
   ```

4. **Optional: Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your OpenAI API key (optional)
   ```

### First Run

```bash
# Run without arguments to see welcome message
python expense_tracker.py

# Or get help
python expense_tracker.py --help
```

## 📖 Usage Guide

### Adding Expenses

```bash
# Quick add with prompts
python expense_tracker.py add 15.50

# Add with all details
python expense_tracker.py add 25.00 --category "Food & Dining" --description "Lunch at cafe" --tags "work,lunch"

# Add expense for a specific date
python expense_tracker.py add 50.00 --category "Transportation" --date "2024-01-15"
```

### Viewing Your Data

```bash
# Show today's summary
python expense_tracker.py summary

# Show summary for specific date
python expense_tracker.py summary --date "2024-01-15"

# List recent expenses
python expense_tracker.py list

# List expenses from last 30 days
python expense_tracker.py list --days 30

# Filter by category
python expense_tracker.py list --category "Food & Dining"
```

### Reports and Analysis

```bash
# Weekly report
python expense_tracker.py report

# Monthly report
python expense_tracker.py report --days 30

# Category-specific report
python expense_tracker.py report --category "Shopping" --days 14

# Get AI-powered insights
python expense_tracker.py insights

# View statistics
python expense_tracker.py stats
```

### Budget Management

```bash
# View current budgets
python expense_tracker.py budget --show

# Set a budget
python expense_tracker.py budget --category "Food & Dining" --amount 500

# Interactive budget setting
python expense_tracker.py budget
```

### Automated Summaries

```bash
# Start the daily summary scheduler (11 PM summaries)
python expense_tracker.py start

# Test the summary feature
python expense_tracker.py test-summary

# Stop the scheduler
python expense_tracker.py stop
```

### Data Management

```bash
# Search expenses
python expense_tracker.py search "coffee"
python expense_tracker.py search "uber" --days 7

# Export data
python expense_tracker.py export --format csv --days 30
python expense_tracker.py export --format json --output my_expenses.json

# Delete an expense (use ID from list command)
python expense_tracker.py delete 5
```

## 📂 Available Categories

- Food & Dining
- Transportation  
- Shopping
- Entertainment
- Bills & Utilities
- Healthcare
- Education
- Travel
- Groceries
- Subscriptions
- Investment
- Emergency
- Other

## 🤖 AI-Powered Features

The expense tracker includes intelligent analysis that:

- **Detects spending patterns** and unusual activity
- **Provides budget warnings** when approaching limits
- **Suggests improvements** based on your habits
- **Compares spending** across different time periods
- **Identifies trends** in your financial behavior

### Sample Insights

- "Your average dining expense is $28.50. Try cooking more meals at home."
- "You made 8 small purchases totaling $45.20. Consider bundling purchases."
- "High shopping expenses detected. Consider a 24-hour rule for non-essential purchases."

## 📊 Daily Summary Example

```
============================================================
📊 DAILY SPENDING SUMMARY - 2024-01-15
============================================================
💰 Total Spent     $85.50
📝 Transactions    6
🏆 Top Category    Food & Dining ($42.00)
📊 vs Yesterday    📈 +15.2%

💳 BUDGET STATUS
Category          Spent      Budget     Progress               Status
Food & Dining     $180.50    $500.00    ████████░░░░░░░░░░ 36.1%   ✅ OK
Transportation    $45.00     $200.00    ████░░░░░░░░░░░░░░ 22.5%   ✅ OK

💡 INSIGHTS & SUGGESTIONS
⚠️ Multiple dining expenses today
Consider meal planning or cooking at home to reduce dining costs.

🎯 IMPROVEMENT SUGGESTIONS
1. Your daily average spending is high. Set a daily spending limit.
2. Consider meal prepping on weekends to reduce dining expenses.
============================================================
```

## ⚙️ Configuration

### Default Budgets

The system comes with sensible default budgets that you can customize:

- Food & Dining: $500/month
- Transportation: $200/month  
- Shopping: $300/month
- Entertainment: $200/month
- Bills & Utilities: $400/month
- Healthcare: $150/month
- Education: $100/month
- Travel: $300/month
- Groceries: $400/month
- Subscriptions: $100/month
- Investment: $500/month
- Emergency: $200/month
- Other: $200/month

### Environment Variables

Create a `.env` file (copy from `.env.example`) to customize:

```bash
# Optional: OpenAI API key for enhanced insights
OPENAI_API_KEY=your_api_key_here

# Database location (default: expenses.db)
DATABASE_PATH=expenses.db

# Daily summary time (default: 23:00)
DAILY_SUMMARY_TIME=23:00
```

## 📁 File Structure

```
expense-tracker/
├── expense_tracker.py    # Main CLI application
├── database.py          # Database models and operations
├── analyzer.py          # Spending analysis engine
├── scheduler.py         # Daily summary scheduler
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── README.md          # This file
└── expenses.db        # SQLite database (created automatically)
```

## 🔧 Advanced Usage

### Running as a Service (Linux)

To run the scheduler as a background service:

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/expense-tracker.service
   ```

2. Add the service configuration:
   ```ini
   [Unit]
   Description=Expense Tracker Agent
   After=network.target

   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/path/to/expense-tracker
   ExecStart=/usr/bin/python3 /path/to/expense-tracker/expense_tracker.py start
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable expense-tracker
   sudo systemctl start expense-tracker
   ```

### Backup Your Data

Your expense data is stored in `expenses.db`. To backup:

```bash
# Copy the database file
cp expenses.db expenses_backup_$(date +%Y%m%d).db

# Or export to CSV
python expense_tracker.py export --format csv --days 365 --output full_backup.csv
```

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission denied (Linux/Mac)**
   ```bash
   chmod +x expense_tracker.py
   ```

3. **Database locked errors**
   - Close any other instances of the application
   - Check if the database file has proper permissions

4. **Scheduler not working**
   - Make sure to keep the terminal open when running `start`
   - Check system time and timezone settings

### Getting Help

```bash
# General help
python expense_tracker.py --help

# Command-specific help
python expense_tracker.py add --help
python expense_tracker.py report --help
```

## 📈 Tips for Better Expense Tracking

1. **Be Consistent**: Add expenses daily for better insights
2. **Use Descriptions**: Detailed descriptions help with searching and analysis
3. **Tag Smartly**: Use tags for additional categorization (work, personal, etc.)
4. **Review Regularly**: Check your summaries and adjust budgets as needed
5. **Set Realistic Budgets**: Start with your actual spending and gradually optimize
6. **Use Categories Consistently**: Stick to the same categorization for better analysis

## 🔒 Privacy & Security

- All data is stored locally in SQLite database
- No data is sent to external servers (except optional OpenAI API for insights)
- OpenAI API integration is optional and can be disabled
- Regular backups are recommended

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

---

**Happy tracking! 💰📊**

*Your financial wellness journey starts with awareness. This tool helps you understand your spending patterns and make informed decisions about your money.*