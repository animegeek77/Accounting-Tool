# Flask Accounting System

A professional double-entry accounting system built with Flask, featuring a modern UI for managing Chart of Accounts, Journal Entries, and Trial Balance reports.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app/app.py

# Or use npm
npm start
```

The app will be available at **http://localhost:5000**

## Features

### Phase 1-2: Core Accounting Engine (Complete)
- **Chart of Accounts**: 47 accounts across Assets, Liabilities, Equity, Income, and Expenses
- **Double-Entry Bookkeeping**: Enforced balance validation (debits = credits)
- **Project Tagging**: Track transactions by project
- **Tax Awareness**: Mark tax-relevant accounts for reporting

### Phase 3: Read-Only Web UI (Complete)
- **Home Dashboard**: System overview and navigation
- **Chart of Accounts**: Browse all 47 accounts with type color-coding
- **Journal Entries**: View 6 sample transactions with full details
- **Trial Balance**: Balanced report showing account balances
- **Account Ledger**: Detailed transaction history per account

### Sample Data
The app comes pre-loaded with 6 realistic transactions:
1. Project revenue recognition (Invoice payment)
2. Freelancer contractor payment
3. Office rent expense
4. Software subscriptions
5. Equipment purchase on credit
6. Client invoice (Accounts Receivable)

## Current Status

**Trial Balance**: Balanced at $44,500 (debits = credits)
**Total Accounts**: 47 accounts
**Journal Entries**: 6 sample entries

## Project Structure

```
project/
├── app/
│   ├── app.py              # Flask application factory
│   ├── routes.py           # Read-only route handlers
│   ├── static/
│   │   └── style.css       # Modern responsive styling
│   └── templates/
│       ├── base.html       # Base template with navigation
│       ├── index.html      # Home dashboard
│       ├── chart_of_accounts.html
│       ├── journal_entries.html
│       ├── ledger.html     # Trial balance
│       ├── ledger_account.html  # Account detail
│       └── error.html      # Error pages
├── core/
│   ├── account.py          # Chart of Accounts model
│   ├── journal_entry.py    # Double-entry validation
│   ├── posting_engine.py   # Posting to ledger
│   ├── ledger.py           # Balance calculations
│   └── project.py          # Project tracking (reserved)
├── docs/
│   ├── accounting_scope.md
│   └── chart_of_accounts.md
└── requirements.txt
```

## Development

The application includes:
- Comprehensive error handling with try-catch blocks
- Structured logging for debugging
- Modern UI with responsive design
- Color-coded account types
- Running balance calculations in ledgers

## Future Phases

### Phase 4: Controlled Mutation (Planned)
- POST endpoints for creating journal entries
- Reversing entries for corrections
- Period locks for closing books

### Phase 5: Persistence (Planned)
- Database integration (Supabase ready)
- Data durability and recovery
- Migration tools

## Project Phases (Wireframe)

### Phase 1: Accounting Foundation

- **Status:** COMPLETE
- Chart of Accounts (core/account.py) with immutable codes and types
- Double-entry enforcement in core/journal_entry.py
- Project-tagging and tax-awareness support defined at the model layer

### Phase 2: Derived Truth

- **Status:** COMPLETE
- Ledger (core/ledger.py)  read-only aggregation from PostingEngine
- Trial balance reports
- Account balance calculations respecting NormalBalance

### Phase 3: Read-only Visibility

- **Status:** IN PROGRESS
- Web UI (Flask app in pp/) with templates for inspection
- Endpoints: /, /chart-of-accounts, /journal-entries, /ledger
- Currently serves placeholder data (no persistence yet)

### Phase 4: Controlled Mutation (Planned)

- **Status:** NOT STARTED
- Posting routes (API endpoints to create journal entries)
- Reversing entries
- Period locks

### Phase 5: Persistence (Planned)

- **Status:** NOT STARTED
- Database integration (db/ folder reserved)
- Data durability and recovery
- Migration tools

### Phase 6: Advanced Features (Planned)

- **Status:** NOT STARTED
- Enhanced project tracking (core/project.py reserved)
- Tax calculation and reporting
- Payroll integration
