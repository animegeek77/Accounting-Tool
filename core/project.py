"""
Project management module for the accounting system.

## Wireframe Phase: Phase 6 (Advanced Features - PLANNED)

This module is reserved for Phase 6 implementation. Projects will be first-class
accounting entities that allow allocation of income and expenses, with:

- Project creation and lifecycle management
- Budget tracking (budgeted income/expenses)
- Actual income/expense aggregation from linked journal entries
- Project profitability reports
- Multi-project allocation (split percentages for payroll, expenses)

As of now, this module is a placeholder. Basic data structures and constraints
are documented below for reference; implementation will follow Phase 5 (Persistence).

## Design Notes (from accounting_scope.md)

Projects are first-class entities. Transactions may optionally be linked to:
- A project
- A client

A project may contain:
- Budgeted income
- Budgeted expenses
- Actual income and expenses

Project profitability is derived from linked transactions only.

## Implementation Status

- Status: NOT STARTED (Phase 6 planned)
- Dependencies: Phase 5 (Persistence) must complete first
- Related: core/journal_entry.py includes project_id field on JournalLine (ready)
"""

# Placeholder for Phase 6: Project tracking
__all__ = []
