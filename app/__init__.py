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

from core.account import ChartOfAccounts
from core.journal_entry import Journal
from core.posting_engine import PostingEngine
from core.ledger import Ledger


def make_in_memory_services() -> Tuple[ChartOfAccounts, Journal, PostingEngine, Ledger]:
    """Create and return the core in-memory services.

    Returns a tuple: (chart, journal, posting_engine, ledger)
    - `chart` is a seeded `ChartOfAccounts` (read-only catalogue)
    - `journal` is an empty in-memory `Journal`
    - `posting_engine` is wired to the chart
    - `ledger` is the read-only view derived from chart + posting_engine

    The function is intentionally explicit and idempotent; callers
    may call it to obtain isolated in-memory instances for testing
    or dev inspection.
    """
    chart = ChartOfAccounts()
    journal = Journal()
    posting_engine = PostingEngine(chart)
    ledger = Ledger(chart, posting_engine)
    return chart, journal, posting_engine, ledger


__all__ = ["make_in_memory_services"]
