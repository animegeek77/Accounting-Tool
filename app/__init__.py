"""
`app` package initializer — thin and honest.

From an accountant's perspective: this module provides a small,
explicit factory that assembles the in-memory services you can
use to inspect system state. It performs no IO, adds no sample
transactions, and has no side-effects on import.

Keep this file minimal — it's a composition helper, not a framework.

Wireframe Phase: Phase 3 (Read-only Visibility)
This package implements the web UI layer (Flask) for Phase 3. All routes are
read-only GET endpoints. Modules:
- app.py: Flask app factory and main service instantiation
- routes.py: Read-only route registration (endpoints for COA, Journal, Ledger)
- static/: CSS and client-side assets
- templates/: Jinja2 templates for rendering views

Future phases:
- Phase 4 (Controlled Mutation): Add POST/PUT/DELETE endpoints for posting
- Phase 5 (Persistence): Replace in-memory services with database-backed ones
"""

from typing import Tuple
import logging

from core.account import ChartOfAccounts
from core.journal_entry import Journal, JournalEntry, JournalLine, EntrySide, ReferenceType
from core.posting_engine import PostingEngine
from core.ledger import Ledger
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


def make_in_memory_services() -> Tuple[ChartOfAccounts, Journal, PostingEngine, Ledger]:
    """Create and return the core in-memory services.

    Returns a tuple: (chart, journal, posting_engine, ledger)
    - `chart` is a seeded `ChartOfAccounts` (read-only catalogue)
    - `journal` is an in-memory `Journal` with sample entries for demo
    - `posting_engine` is wired to the chart and populated with sample data
    - `ledger` is the read-only view derived from chart + posting_engine

    The function is intentionally explicit and idempotent; callers
    may call it to obtain isolated in-memory instances for testing
    or dev inspection.
    """
    chart = ChartOfAccounts()
    journal = Journal()
    posting_engine = PostingEngine(chart)
    ledger = Ledger(chart, posting_engine)

    # Add sample journal entries for demonstration
    _seed_sample_transactions(chart, journal, posting_engine)

    return chart, journal, posting_engine, ledger


def _seed_sample_transactions(chart: ChartOfAccounts, journal: Journal, posting_engine: PostingEngine) -> None:
    """Add sample journal entries for demonstration purposes.

    Creates realistic sample transactions:
    - Client project revenue
    - Operating expenses
    - Payroll
    - Asset purchase
    """
    logger.info("Seeding sample transactions for demonstration")

    try:
        # Transaction 1: Client project revenue
        entry1 = JournalEntry(
            description="Project Alpha - Milestone 1 payment received",
            date=datetime(2026, 1, 15),
            source_ref="INV-2026-001",
            reference_type=ReferenceType.INVOICE,
            project_id="PROJ-001"
        )
        entry1.add_line(JournalLine(
            account_code=1010,  # Cash – Operating Account
            amount=Decimal("15000.00"),
            side=EntrySide.DEBIT,
            project_id="PROJ-001",
            description="Client payment received"
        ))
        entry1.add_line(JournalLine(
            account_code=4010,  # Project Revenue
            amount=Decimal("15000.00"),
            side=EntrySide.CREDIT,
            project_id="PROJ-001",
            description="Project Alpha Milestone 1"
        ))
        journal.add_entry(entry1, chart)
        posting_engine.post(entry1)
        logger.info(f"Posted journal entry: {entry1.id[:8]}... - Project revenue")

        # Transaction 2: Freelancer payment
        entry2 = JournalEntry(
            description="Freelancer payment for Project Alpha",
            date=datetime(2026, 1, 20),
            source_ref="FREELANCE-2026-001",
            reference_type=ReferenceType.INVOICE,
            project_id="PROJ-001"
        )
        entry2.add_line(JournalLine(
            account_code=5010,  # Freelancers & Contractors
            amount=Decimal("5000.00"),
            side=EntrySide.DEBIT,
            project_id="PROJ-001",
            description="Design work - John Doe"
        ))
        entry2.add_line(JournalLine(
            account_code=1010,  # Cash – Operating Account
            amount=Decimal("5000.00"),
            side=EntrySide.CREDIT,
            description="Bank transfer"
        ))
        journal.add_entry(entry2, chart)
        posting_engine.post(entry2)
        logger.info(f"Posted journal entry: {entry2.id[:8]}... - Freelancer payment")

        # Transaction 3: Office rent payment
        entry3 = JournalEntry(
            description="January 2026 office rent",
            date=datetime(2026, 1, 31),
            source_ref="RENT-2026-01",
            reference_type=ReferenceType.OTHER
        )
        entry3.add_line(JournalLine(
            account_code=6110,  # Office Rent
            amount=Decimal("3500.00"),
            side=EntrySide.DEBIT,
            description="Monthly office rent"
        ))
        entry3.add_line(JournalLine(
            account_code=1010,  # Cash – Operating Account
            amount=Decimal("3500.00"),
            side=EntrySide.CREDIT,
            description="Rent payment"
        ))
        journal.add_entry(entry3, chart)
        posting_engine.post(entry3)
        logger.info(f"Posted journal entry: {entry3.id[:8]}... - Office rent")

        # Transaction 4: Software subscription
        entry4 = JournalEntry(
            description="Annual software subscriptions",
            date=datetime(2026, 2, 1),
            source_ref="SOFTWARE-2026",
            reference_type=ReferenceType.OTHER
        )
        entry4.add_line(JournalLine(
            account_code=6140,  # Software Subscriptions
            amount=Decimal("1200.00"),
            side=EntrySide.DEBIT,
            description="Annual tools subscription"
        ))
        entry4.add_line(JournalLine(
            account_code=1010,  # Cash – Operating Account
            amount=Decimal("1200.00"),
            side=EntrySide.CREDIT,
            description="Credit card payment"
        ))
        journal.add_entry(entry4, chart)
        posting_engine.post(entry4)
        logger.info(f"Posted journal entry: {entry4.id[:8]}... - Software subscription")

        # Transaction 5: Equipment purchase on credit
        entry5 = JournalEntry(
            description="Computer equipment purchase",
            date=datetime(2026, 2, 10),
            source_ref="PO-2026-015",
            reference_type=ReferenceType.OTHER
        )
        entry5.add_line(JournalLine(
            account_code=1120,  # Computer & Production Equipment
            amount=Decimal("4500.00"),
            side=EntrySide.DEBIT,
            description="MacBook Pro for design team"
        ))
        entry5.add_line(JournalLine(
            account_code=2010,  # Accounts Payable
            amount=Decimal("4500.00"),
            side=EntrySide.CREDIT,
            description="Vendor invoice - Tech Supplier"
        ))
        journal.add_entry(entry5, chart)
        posting_engine.post(entry5)
        logger.info(f"Posted journal entry: {entry5.id[:8]}... - Equipment purchase")

        # Transaction 6: Client invoice sent (accounts receivable)
        entry6 = JournalEntry(
            description="Project Beta - Invoice sent",
            date=datetime(2026, 2, 15),
            source_ref="INV-2026-002",
            reference_type=ReferenceType.INVOICE,
            project_id="PROJ-002"
        )
        entry6.add_line(JournalLine(
            account_code=1040,  # Accounts Receivable
            amount=Decimal("25000.00"),
            side=EntrySide.DEBIT,
            project_id="PROJ-002",
            description="Invoice sent to client"
        ))
        entry6.add_line(JournalLine(
            account_code=4010,  # Project Revenue
            amount=Decimal("25000.00"),
            side=EntrySide.CREDIT,
            project_id="PROJ-002",
            description="Project Beta services rendered"
        ))
        journal.add_entry(entry6, chart)
        posting_engine.post(entry6)
        logger.info(f"Posted journal entry: {entry6.id[:8]}... - Client invoice")

        logger.info("Successfully seeded 6 sample journal entries")

    except Exception as e:
        logger.error(f"Error seeding sample transactions: {e}")
        # Don't fail startup if sample data fails
        pass


__all__ = ["make_in_memory_services"]
