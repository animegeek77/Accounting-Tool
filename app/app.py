"""
Minimal Flask app wired to in-memory core objects.

Design notes (accountant perspective):
  `PostingEngine` (in-memory totals), and `Ledger` (read-only views).
  for accountants to inspect system state. No business logic, persistence,
  or seeded transactional data is added here.
"""
## Wireframe Phase
# Implements Phase 3: Read-only Visibility
#
# - Provides web UI for inspection of core accounting objects
# - Routes expose Chart of Accounts, Journal, and Ledger/Trial Balance
# - All endpoints read from in-memory data (no persistence)
# - No mutation endpoints yet (Phase 4: Controlled Mutation - planned)
# - No database integration yet (Phase 5: Persistence - planned)

import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from core.account import ChartOfAccounts
from core.journal_entry import Journal, JournalEntry, JournalLine, EntrySide, ReferenceType
from core.posting_engine import PostingEngine
from core.ledger import Ledger
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


def make_in_memory_services():
    """Create and return the core in-memory services."""
    chart = ChartOfAccounts()
    journal = Journal()
    posting_engine = PostingEngine(chart)
    ledger = Ledger(chart, posting_engine)

    # Add sample journal entries for demonstration
    _seed_sample_transactions(chart, journal, posting_engine)

    return chart, journal, posting_engine, ledger


def _seed_sample_transactions(chart, journal, posting_engine):
    """Add sample journal entries for demonstration purposes."""
    logger.info("Seeding sample transactions for demonstration")

    try:
        # Transaction 1: Client project revenue
        entry1 = JournalEntry(
            description="Project Alpha - Milestone 1 payment received",
            date=datetime(2026, 1, 15),
            source_ref="INV-2026-001",
            reference_type=ReferenceType.INVOICE
        )
        entry1.add_line(JournalLine(
            account_code=1010,
            amount=Decimal("15000.00"),
            side=EntrySide.DEBIT,
            description="Client payment received"
        ))
        entry1.add_line(JournalLine(
            account_code=4010,
            amount=Decimal("15000.00"),
            side=EntrySide.CREDIT,
            project_id="PROJ-001",
            description="Project Alpha Milestone 1"
        ))
        journal.add_entry(entry1, chart)
        posting_engine.post(entry1)

        # Transaction 2: Freelancer payment
        entry2 = JournalEntry(
            description="Freelancer payment for Project Alpha",
            date=datetime(2026, 1, 20),
            source_ref="FREELANCE-2026-001",
            reference_type=ReferenceType.INVOICE
        )
        entry2.add_line(JournalLine(
            account_code=5010,
            amount=Decimal("5000.00"),
            side=EntrySide.DEBIT,
            project_id="PROJ-001",
            description="Design work - John Doe"
        ))
        entry2.add_line(JournalLine(
            account_code=1010,
            amount=Decimal("5000.00"),
            side=EntrySide.CREDIT,
            description="Bank transfer"
        ))
        journal.add_entry(entry2, chart)
        posting_engine.post(entry2)

        # Transaction 3: Office rent payment
        entry3 = JournalEntry(
            description="January 2026 office rent",
            date=datetime(2026, 1, 31),
            source_ref="RENT-2026-01",
            reference_type=ReferenceType.OTHER
        )
        entry3.add_line(JournalLine(
            account_code=6110,
            amount=Decimal("3500.00"),
            side=EntrySide.DEBIT,
            description="Monthly office rent"
        ))
        entry3.add_line(JournalLine(
            account_code=1010,
            amount=Decimal("3500.00"),
            side=EntrySide.CREDIT,
            description="Rent payment"
        ))
        journal.add_entry(entry3, chart)
        posting_engine.post(entry3)

        # Transaction 4: Software subscription
        entry4 = JournalEntry(
            description="Annual software subscriptions",
            date=datetime(2026, 2, 1),
            source_ref="SOFTWARE-2026",
            reference_type=ReferenceType.OTHER
        )
        entry4.add_line(JournalLine(
            account_code=6140,
            amount=Decimal("1200.00"),
            side=EntrySide.DEBIT,
            description="Annual tools subscription"
        ))
        entry4.add_line(JournalLine(
            account_code=1010,
            amount=Decimal("1200.00"),
            side=EntrySide.CREDIT,
            description="Credit card payment"
        ))
        journal.add_entry(entry4, chart)
        posting_engine.post(entry4)

        # Transaction 5: Equipment purchase on credit
        entry5 = JournalEntry(
            description="Computer equipment purchase",
            date=datetime(2026, 2, 10),
            source_ref="PO-2026-015",
            reference_type=ReferenceType.OTHER
        )
        entry5.add_line(JournalLine(
            account_code=1120,
            amount=Decimal("4500.00"),
            side=EntrySide.DEBIT,
            description="MacBook Pro for design team"
        ))
        entry5.add_line(JournalLine(
            account_code=2010,
            amount=Decimal("4500.00"),
            side=EntrySide.CREDIT,
            description="Vendor invoice - Tech Supplier"
        ))
        journal.add_entry(entry5, chart)
        posting_engine.post(entry5)

        # Transaction 6: Client invoice sent
        entry6 = JournalEntry(
            description="Project Beta - Invoice sent",
            date=datetime(2026, 2, 15),
            source_ref="INV-2026-002",
            reference_type=ReferenceType.INVOICE
        )
        entry6.add_line(JournalLine(
            account_code=1040,
            amount=Decimal("25000.00"),
            side=EntrySide.DEBIT,
            description="Invoice sent to client"
        ))
        entry6.add_line(JournalLine(
            account_code=4010,
            amount=Decimal("25000.00"),
            side=EntrySide.CREDIT,
            project_id="PROJ-002",
            description="Project Beta services rendered"
        ))
        journal.add_entry(entry6, chart)
        posting_engine.post(entry6)

        logger.info("Successfully seeded 6 sample journal entries")

    except Exception as e:
        logger.error(f"Error seeding sample transactions: {e}")


def create_app():
    """Application factory for the accounting app."""
    # Create Flask app
    app = Flask(__name__, static_folder='static', template_folder='templates')

    # Configure logging
    log_level = logging.DEBUG if os.environ.get('FLASK_DEBUG') == 'true' else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure app settings
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['ENV'] = os.environ.get('FLASK_ENV', 'development')

    # Create isolated in-memory services and register read-only routes.
    logger.info("Initializing accounting services...")
    chart, journal, posting_engine, ledger_view = make_in_memory_services()

    # Import routes after services are created
    from app.routes import register_routes
    register_routes(app, chart, journal, posting_engine, ledger_view)

    logger.info("Flask app initialized successfully")
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
