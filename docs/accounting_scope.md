# Accounting Scope

**Status:** FROZEN (v1.0)

1. Accounting Basis

Line Media Solutions uses accrual accounting.

Revenue is recognized when services are delivered or contract milestones are met.

Expenses are recognized when incurred, not when paid.

Cash movements are recorded separately but never override accrual records.

1. Functional Currency & Periods

Functional currency: ZMW (or company default currency).

Financial year: Calendar year unless explicitly changed.

Accounting periods are monthly.

Once a period is closed, entries within it are immutable.

1. Core Accounting Model

All financial activity is recorded using double-entry accounting.

Every transaction must have:

- At least one debit.
- At least one credit.
- Total debits must equal total credits.

Account balances are derived from transactions only. (Direct balance edits are prohibited.)

1. Chart of Accounts Principles

Accounts follow a hierarchical structure.

Each account has:

- Account code.
- Name.
- Type (Asset, Liability, Equity, Income, Expense).

New accounts may be added, but account types are immutable once created.

1. Project-Based Accounting

Projects are first-class entities.

Transactions may optionally be linked to:

- A project.
- A client.

A project may contain:

- Budgeted income.
- Budgeted expenses.
- Actual income and expenses.

Project profitability is derived from linked transactions only.

1. Payroll & Staff Costs (Foundational Rules Only)

Employees and contractors are treated as cost sources.

Payroll expenses may be allocated:

- Fully to one project.
- Split across multiple projects by percentage.

Payroll logic generates accounting transactions but does not bypass them.

1. Tax Awareness (Not Tax Calculation)

Accounts may be tagged as tax-relevant.

Transactions may carry tax metadata:

- Tax type.
- Tax rate.
- Tax jurisdiction.

Tax reports read accounting data; they do not modify it.

1. Audit & Integrity Rules

All transactions have:

- Unique, immutable IDs.
- Timestamps.
- Source references (invoice, payroll run, adjustment, etc.).

Corrections are made using reversing entries.

Deletions of posted transactions are prohibited.

1. Reporting Authority

The following reports are considered authoritative:

- Trial Balance.
- General Ledger.
- Project Ledger.

All other reports are derived views.
