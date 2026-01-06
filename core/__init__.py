"""
Core accounting module - implements Phases 1 and 2 of the project wireframe.

## Phase 1: Accounting Foundation (COMPLETE)

- `account.py`: Chart of Accounts with immutable codes, hierarchical structure,
  and project/tax tagging capability
- `journal_entry.py`: Double-entry enforcement; JournalEntry is the ONLY mechanism
  for creating/modifying account balances

## Phase 2: Derived Truth (COMPLETE)

- `posting_engine.py`: Converts validated JournalEntry objects into ledger postings;
  maintains in-memory ledger for testing/local use
- `ledger.py`: READ-ONLY view that aggregates journal lines by account and derives
  balances respecting account NormalBalance; produces trial balance reports

## Phase 6: Advanced Features (PLANNED)

- `project.py`: Project tracking (reserved for Phase 6; not yet implemented)

## Not Included in Core

- Database persistence (Phase 5: reserved for db/ folder)
- Posting mutation endpoints (Phase 4: reserved for app/routes)
- Tax calculation logic (Phase 6)
- Payroll processing (Phase 6)

All core modules are read-only in terms of balance persistence. Mutations occur
only through validated JournalEntry objects.
"""

from .account import Account, AccountType, NormalBalance, ChartOfAccounts
from .journal_entry import JournalEntry, JournalLine, Journal, EntrySide, ReferenceType
from .posting_engine import PostingEngine, LedgerEntry
from .ledger import Ledger, AccountBalance, TrialBalanceRow

__all__ = [
    "Account",
    "AccountType",
    "NormalBalance",
    "ChartOfAccounts",
    "JournalEntry",
    "JournalLine",
    "Journal",
    "EntrySide",
    "ReferenceType",
    "PostingEngine",
    "LedgerEntry",
    "Ledger",
    "AccountBalance",
    "TrialBalanceRow",
]
