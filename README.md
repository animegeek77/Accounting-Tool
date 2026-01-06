# Minimal Flask Accounting UI (placeholder)

This workspace provides a minimal Flask web UI with read-only views for inspecting accounting data: Chart of Accounts, Journal Entries, and the Ledger. The project is organized into phased milestones.

How to run (Windows PowerShell):

`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app\app.py
`

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in a browser.

Notes:

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
